"""Pipeline offline de cenarios 2026, backtests e reconciliacao hierarquica."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"/"historico"
H=pd.read_parquet(OUT/"escola_harmonizada.parquet")
ACTIVE=H[H.SITUACAO.eq("Em atividade")].copy()

METRICS={
 "MATRICULAS":("QT_MAT_BAS","sum",False),
 "ALUNOS_DOCENTE":("ALUNOS_DOCENTE","ratio_doc",False),
 "ALUNOS_TURMA":("ALUNOS_TURMA","ratio_tur",False),
 "MATRICULAS_SALA":("MATRICULAS_SALA","ratio_sala",False),
 "IMDE":("IMDE_HISTORICO_COMPATIVEL","weighted",True),
 "ACESSIBILIDADE":("INDICE_ACESSIBILIDADE_HIST","weighted",True),
 "INTERNET_PCT":("IN_INTERNET","percent",True),
 "BANDA_LARGA_PCT":("IN_BANDA_LARGA","percent",True),
}

def aggregate(data, metric):
    col,method,_=METRICS[metric]
    if method=="sum": return float(data[col].sum(min_count=1))
    if method=="ratio_doc": return float(data.QT_MAT_BAS.sum()/data.QT_DOC_BAS.sum())
    if method=="ratio_tur": return float(data.QT_MAT_BAS.sum()/data.QT_TUR_BAS.sum())
    if method=="ratio_sala": return float(data.QT_MAT_BAS.sum()/data.QT_SALAS_UTILIZADAS.sum())
    if method=="percent": return float(100*data[col].mean())
    x=data[[col,"QT_MAT_BAS"]].dropna()
    return float(np.average(x[col],weights=x.QT_MAT_BAS)) if len(x) and x.QT_MAT_BAS.sum() else np.nan

def series(metric,data=ACTIVE):
    return pd.Series({y:aggregate(g,metric) for y,g in data.groupby("ANO")},name=metric).sort_index()

def predict(method, train, target_year):
    train=train.dropna().astype(float)
    if method=="Persistencia": return float(train.iloc[-1])
    growth=train.pct_change().dropna().tail(2)
    if method=="Crescimento recente": return float(train.iloc[-1]*(1+growth.mean()))
    if method=="Tendencia robusta":
        slopes=[(train.iloc[j]-train.iloc[i])/(train.index[j]-train.index[i]) for i in range(len(train)) for j in range(i+1,len(train))]
        return float(train.iloc[-1]+np.median(slopes)*(target_year-train.index[-1]))
    raise ValueError(method)

def evaluate(metric):
    s=series(metric); methods=["Persistencia","Crescimento recente","Tendencia robusta"]
    rows=[]
    for method in methods:
        errors=[]
        for target in [2024,2025]:
            train=s[s.index<target]; pred=predict(method,train,target); actual=float(s.loc[target]); errors.append(abs(pred-actual))
            rows.append({"INDICADOR":metric,"MODELO":method,"BACKTEST_ANO":target,"REAL":actual,"PREVISTO":pred,
                         "ERRO_ABSOLUTO":abs(pred-actual),"ERRO_PCT":100*abs(pred-actual)/abs(actual) if actual else np.nan})
    summary=pd.DataFrame(rows).groupby("MODELO").ERRO_ABSOLUTO.mean()
    baseline=float(summary["Persistencia"]); candidates=summary.drop("Persistencia")
    best=candidates.idxmin(); best_error=float(candidates.min())
    forecast=predict(best,s,2026); last=float(s.loc[2025]); bounded=METRICS[metric][2]
    sanity=[]
    if forecast<0: sanity.append("NEGATIVO")
    if bounded and not 0<=forecast<=100: sanity.append("FORA_0_100")
    changes=s.pct_change().dropna()*100; forecast_change=100*(forecast/last-1) if last else np.nan
    max_observed=float(changes.abs().max())
    if np.isfinite(forecast_change) and abs(forecast_change)>max(5,1.5*max_observed): sanity.append("EXTRAPOLACAO_FORTE")
    approved=best_error<baseline and not sanity
    status="APROVADO" if approved else ("REPROVADO" if best_error>=baseline else "EXPERIMENTAL")
    residuals=pd.DataFrame(rows).query("MODELO==@best").ERRO_ABSOLUTO
    margin=float(max(residuals.max(),abs(forecast-last)*.25))
    lo=max(0,forecast-margin); hi=min(100,forecast+margin) if bounded else forecast+margin
    meta={"INDICADOR":metric,"MODELO":best,"BACKTEST_2024":float(pd.DataFrame(rows).query("MODELO==@best and BACKTEST_ANO==2024").ERRO_ABSOLUTO.iloc[0]),
          "BACKTEST_2025":float(pd.DataFrame(rows).query("MODELO==@best and BACKTEST_ANO==2025").ERRO_ABSOLUTO.iloc[0]),
          "BASELINE":"Persistencia","ERRO_MEDIO_MODELO":best_error,"ERRO_MEDIO_BASELINE":baseline,
          "SUPEROU_BASELINE":bool(best_error<baseline),"SANITY_CHECK":"OK" if not sanity else " | ".join(sanity),
          "STATUS":status,"PUBLICAR_2026":bool(approved),"REAL_2025":last,"CENARIO_2026":forecast,
          "VARIACAO_2026_PCT":forecast_change,"LIMITE_INFERIOR":lo,"LIMITE_SUPERIOR":hi,
          "MAIOR_VARIACAO_HISTORICA_ABS_PCT":max_observed}
    return pd.DataFrame(rows),meta

def territorial_scenario(national):
    """Bottom-up robusto nos grupos, seguido de scaling para reconciliar ao Brasil."""
    rows=[]; y25=ACTIVE[ACTIVE.ANO.eq(2025)]; total=float(y25.QT_MAT_BAS.sum()); national26=national["CENARIO_2026"]
    for level,col in [("REGIAO","NO_REGIAO"),("UF","SG_UF"),("REDE","DEPENDENCIA"),("LOCALIZACAO","LOCALIZACAO")]:
        values=[]
        for name,data in ACTIVE.groupby(col,dropna=False):
            s=data.groupby("ANO").QT_MAT_BAS.sum().sort_index(); real=float(s.loc[2025])
            raw=predict("Tendencia robusta",s,2026); hist=s.pct_change().dropna()
            low=max(-.15,float(hist.quantile(.05))-0.02); high=min(.15,float(hist.quantile(.95))+0.02)
            scenario=real*(1+np.clip(raw/real-1,low,high))
            values.append({"LOCALIDADE":name,"REAL_2025":real,"RAW":scenario})
        g=pd.DataFrame(values); scale=national26/g.RAW.sum(); g["CENARIO_2026"]=g.RAW*scale
        g["DELTA_ABS"]=g.CENARIO_2026-g.REAL_2025; g["DELTA_PCT"]=100*g.DELTA_ABS/g.REAL_2025
        g["LIMITE_INFERIOR"]=national["LIMITE_INFERIOR"]*g.REAL_2025/total
        g["LIMITE_SUPERIOR"]=national["LIMITE_SUPERIOR"]*g.REAL_2025/total
        g["NIVEL"]=level; g=g.drop(columns="RAW")
        g["CONFIANCA"]=national["STATUS"]; g["ALERTA"]=national["SANITY_CHECK"]
        rows.append(g)
    return pd.concat(rows,ignore_index=True)

def risk_table():
    data=ACTIVE.sort_values(["CO_ENTIDADE","ANO"]); g=data.groupby("CO_ENTIDADE")
    latest=data[data.ANO.eq(2025)][["CO_ENTIDADE","NO_ENTIDADE","NO_MUNICIPIO","SG_UF","QT_MAT_BAS","ALUNOS_DOCENTE","ALUNOS_TURMA","IMDE_HISTORICO_COMPATIVEL"]].copy()
    latest["VAR_MAT_1A"]=g.QT_MAT_BAS.pct_change(fill_method=None).loc[latest.index]
    latest["VAR_PRESSAO_1A"]=g.ALUNOS_TURMA.diff().loc[latest.index]
    latest["VAR_IMDE_1A"]=g.IMDE_HISTORICO_COMPATIVEL.diff().loc[latest.index]
    counts=g.ANO.nunique(); latest["ANOS_HISTORICO"]=latest.CO_ENTIDADE.map(counts)
    latest["ANOMALIA_TEMPORAL"]=latest.CO_ENTIDADE.isin(set(pd.read_parquet(OUT/"trajetorias_escolas.parquet").query("VARIACAO_ATIPICA_INVESTIGAR").CO_ENTIDADE))
    latest["RISCO_2026"]=(latest.VAR_MAT_1A.lt(-.10).astype(int)+latest.VAR_PRESSAO_1A.gt(2).astype(int)+latest.VAR_IMDE_1A.lt(-5).astype(int)+latest.ANOMALIA_TEMPORAL.astype(int))
    latest["SINAIS"]=""
    latest.loc[latest.VAR_MAT_1A.lt(-.10),"SINAIS"]+="queda de matriculas; "
    latest.loc[latest.VAR_PRESSAO_1A.gt(2),"SINAIS"]+="pressao crescente; "
    latest.loc[latest.VAR_IMDE_1A.lt(-5),"SINAIS"]+="queda de IMDE; "
    latest.loc[latest.ANOMALIA_TEMPORAL,"SINAIS"]+="mudanca atipica; "
    return latest.sort_values(["RISCO_2026","QT_MAT_BAS"],ascending=False)

def main():
    backtests=[]; registry=[]
    for metric in METRICS:
        bt,meta=evaluate(metric); backtests.append(bt); registry.append(meta)
    reg=pd.DataFrame(registry); bt=pd.concat(backtests,ignore_index=True)
    reg.to_csv(OUT/"registro_modelos.csv",index=False,encoding="utf-8-sig")
    bt.to_csv(OUT/"backtests_modelos.csv",index=False,encoding="utf-8-sig")
    national=reg[reg.INDICADOR.eq("MATRICULAS")].iloc[0].to_dict()
    territorial_scenario(national).to_parquet(OUT/"cenario_matriculas_2026_reconciliado.parquet",index=False)
    risk_table().to_parquet(OUT/"riscos_2026.parquet",index=False)
    audit={"gerado_em_utc":datetime.now(timezone.utc).isoformat(),"universo_real_2025":int(ACTIVE[ACTIVE.ANO.eq(2025)].QT_MAT_BAS.sum()),
           "coorte_backtest_2025":int(pd.read_parquet(OUT/"previsoes_matriculas.parquet").query("ANO_PREVISTO==2025").REALIZADO.sum()),
           "nota":"Cenarios territoriais top-down reconciliam exatamente com Brasil; cenario nao e previsao aprovada."}
    (OUT/"auditoria_preditiva.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
    print(reg[["INDICADOR","MODELO","STATUS","PUBLICAR_2026","SANITY_CHECK"]].to_string(index=False))

if __name__=="__main__": main()
