"""Dashboard interativo em Streamlit — substitui integralmente a camada Power BI/DAX."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
st.set_page_config(page_title="Atlas da Escola Brasileira · 2025", page_icon="▰", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{--bg:#f5f6fa;--card:#fff;--text:#202331;--muted:#687083;--line:#e5e8ef;--primary:#625df5;--soft:#efefff;--green:#28a96b;--red:#dc5960;--amber:#e59b35;}
html,body,[class*="css"],.stApp{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--text)}
.stApp{background:var(--bg)}
.block-container{padding:2.25rem 2rem 3rem;max-width:1600px}
[data-testid="stHeader"]{background:transparent}
[data-testid="stMainBlockContainer"]{padding-top:2.25rem!important}
[data-testid="stHorizontalBlock"]{gap:1rem!important;align-items:stretch}
[data-testid="stVerticalBlock"]>div{margin-bottom:.35rem}
[data-testid="stSidebar"]{background:#111426;border-right:1px solid #282d4c;min-width:252px;max-width:252px;position:relative}
[data-testid="stSidebar"]:before{content:"";position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(rgba(113,108,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(113,108,255,.035) 1px,transparent 1px);background-size:24px 24px}
[data-testid="stSidebar"] *{color:#d8dbea}
[data-testid="stSidebar"] h2{color:#fff!important;letter-spacing:.12em;font-size:18px!important}
[data-testid="stSidebar"] h4{color:#777f9d!important;font-size:10px!important;letter-spacing:.13em;text-transform:uppercase}
[data-testid="stSidebar"] hr{border-color:#2a2f4b;margin:.8rem 0}
[data-testid="stSidebar"] [role="radiogroup"] label{min-height:39px;padding:7px 10px;border-radius:8px;border:1px solid transparent;transition:all 160ms ease}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#1b1f37;border-color:#2c3151}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#25294a;border-color:#454a82;color:#a9a6ff;box-shadow:inset 3px 0 #7772ff}
[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#191d34!important;border-color:#303654!important}
[data-testid="stSidebar"] .stButton button{background:#1c2038;color:#aaa7ff;border:1px solid #3a4067;border-radius:7px;font-size:12px;font-weight:600;width:100%;height:34px}
h1,h2,h3{font-family:Inter,sans-serif!important;color:var(--text)!important;letter-spacing:-.015em}
.saas-top{height:52px;background:#fff;border:1px solid var(--line);border-radius:8px;padding:0 16px;display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.saas-brand{display:flex;align-items:center;gap:10px;font-size:13px;color:var(--muted)}
.saas-dot{width:9px;height:9px;background:var(--green);border-radius:50%;box-shadow:0 0 0 3px #e7f8ee}
.saas-tools{display:flex;gap:10px;align-items:center;color:var(--muted);font-size:12px}.avatar{width:30px;height:30px;background:var(--soft);color:var(--primary);border-radius:8px;display:grid;place-items:center;font-weight:700}
.atlas-head{padding:.35rem 0 1rem;margin:0 0 1.25rem;border-bottom:1px solid var(--line)}
.atlas-kicker{text-transform:uppercase;letter-spacing:.10em;font-size:.65rem;font-weight:600;color:var(--primary)}
.atlas-title{font-size:1.65rem;line-height:1.25;margin:.3rem 0 .45rem;color:var(--text);font-weight:650}
.atlas-deck{font-size:.82rem;color:var(--muted);max-width:850px}
.folio{background:#fff;border:1px solid var(--line);border-radius:10px;padding:17px 18px;min-height:108px;margin:0 0 .9rem;box-shadow:0 2px 8px rgba(37,39,53,.035);transition:border-color 160ms ease,box-shadow 160ms ease}
.folio:hover{border-color:#d7d9ff;box-shadow:0 3px 10px rgba(37,39,53,.05)}
.folio-label{font-size:.72rem;color:var(--muted);font-weight:500}
.folio-value{font-size:1.55rem;color:var(--text);font-weight:600;margin-top:.45rem}
.folio-context{font-size:.66rem;color:var(--primary);margin-top:.25rem}
.filter-note{background:#1b1f37;border:1px solid #303654;border-radius:8px;padding:.65rem;font-size:.72rem;color:#aaa7ff!important;margin:.6rem 0 1rem}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:10px;overflow:hidden}
.stPlotlyChart{background:#fff!important;border:1px solid var(--line);border-radius:10px;padding:.85rem;margin:.6rem 0 1.25rem;box-shadow:0 2px 8px rgba(37,39,53,.035);color:var(--text)!important}
[data-testid="stDataFrame"]{margin:.6rem 0 1.25rem}
[data-testid="stAlert"]{margin:.65rem 0 1.15rem}
.stCaptionContainer{margin:.25rem 0 .7rem}
div[data-baseweb="select"]>div,input{border-radius:7px!important;background:#fafbfe!important;border-color:var(--line)!important;font-size:12px!important}
.stTabs [data-baseweb="tab-list"]{gap:6px}.stTabs [data-baseweb="tab"]{height:36px;border-radius:7px;padding:0 12px;background:#fff}
.stTabs [aria-selected="true"]{background:var(--soft)!important;color:var(--primary)!important}
@media(max-width:900px){.block-container{padding:1.5rem .9rem 2rem}.folio{min-height:92px}.atlas-title{font-size:1.35rem}}
</style>
""", unsafe_allow_html=True)
px.defaults.template="plotly_white"
px.defaults.color_discrete_sequence=["#696cff","#03c3ec","#28c76f","#ff9f43","#ea5455","#8a8fa3"]

@st.cache_data
def load():
    hist=OUT/"historico"
    return (pd.read_parquet(OUT/"escola_analytics.parquet"),
            pd.read_parquet(OUT/"f_curso_tecnico.parquet"), pd.read_csv(OUT/"auditoria.csv"),
            pd.read_parquet(hist/"escola_harmonizada.parquet"),
            pd.read_parquet(hist/"curso_tecnico_harmonizado.parquet"),
            pd.read_csv(hist/"qualidade_multianual.csv"), pd.read_csv(hist/"crosswalk_variaveis.csv"),
            pd.read_parquet(hist/"trajetorias_escolas.parquet"),
            pd.read_parquet(hist/"previsoes_matriculas.parquet"),
            json.loads((hist/"modelo_matriculas.json").read_text(encoding="utf-8")),
            pd.read_csv(hist/"registro_modelos.csv"), pd.read_csv(hist/"backtests_modelos.csv"),
            pd.read_parquet(hist/"cenario_matriculas_2026_reconciliado.parquet"),
            pd.read_parquet(hist/"riscos_2026.parquet"),
            json.loads((hist/"auditoria_preditiva.json").read_text(encoding="utf-8")))

def div(a, b): return a / b if b else np.nan
def fmt(v, kind="n"):
    if pd.isna(v): return "—"
    if kind == "%": return f"{v:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    if kind == "d": return f"{v:,.0f}".replace(",", ".")
    return f"{v:,.0f}".replace(",", ".")
def fmt_signed(v, kind="d"):
    if pd.isna(v): return "—"
    return f"{'+' if v>0 else '−' if v<0 else ''}{fmt(abs(v),kind)}"
def friendly_table(frame, names=None, integer_columns=None, percent_columns=None):
    out=frame.rename(columns=names or {}).copy()
    for source in integer_columns or []:
        col=(names or {}).get(source,source)
        if col in out: out[col]=out[col].map(lambda value:fmt(value,"n"))
    for source in percent_columns or []:
        col=(names or {}).get(source,source)
        if col in out: out[col]=out[col].map(lambda value:fmt(value,"%"))
    return out
INDICATOR_LABELS={"MATRICULAS":"Matrículas","ALUNOS_DOCENTE":"Alunos por docente","ALUNOS_TURMA":"Alunos por turma",
 "MATRICULAS_SALA":"Matrículas por sala","IMDE":"Estrutura digital das escolas","ACESSIBILIDADE":"Acessibilidade",
 "INTERNET_PCT":"Escolas com internet","BANDA_LARGA_PCT":"Escolas com banda larga"}
MODEL_LABELS={"Ridge":"Modelo estatístico (Ridge)","Persistencia":"Modelo simples (repete o ano anterior)",
 "Crescimento recente":"Modelo baseado no crescimento recente","Tendencia robusta":"Modelo baseado na tendência histórica"}
def weighted(df, col, weight="QT_MAT_BAS"):
    x=df[[col,weight]].dropna(); return np.average(x[col],weights=x[weight]) if len(x) and x[weight].sum()>0 else np.nan
def trend_projection(series):
    """Tendência linear curta com backtest 2025; resultado sempre experimental."""
    s=series.dropna().astype(float).sort_index()
    if len(s)<4: return {"projection":np.nan,"estimate_2025":np.nan,"mae":np.nan,"baseline_mae":np.nan}
    train=s[s.index<2025]
    b=np.polyfit(train.index.to_numpy(float),train.to_numpy(float),1)
    estimate_2025=float(np.polyval(b,2025)); actual_2025=float(s.loc[2025]) if 2025 in s.index else np.nan
    full=np.polyfit(s.index.to_numpy(float),s.to_numpy(float),1)
    return {"projection":float(np.polyval(full,2026)),"estimate_2025":estimate_2025,
            "mae":abs(estimate_2025-actual_2025),"baseline_mae":abs(float(train.iloc[-1])-actual_2025),
            "approved":abs(estimate_2025-actual_2025)<abs(float(train.iloc[-1])-actual_2025)}
def cards(items):
    for col,(label,value,kind) in zip(st.columns(len(items)),items):
        col.markdown(f'<div class="folio"><div class="folio-label">{label}</div><div class="folio-value">{fmt(value,kind)}</div><div class="folio-context">Base selecionada · {selected_year}</div></div>',unsafe_allow_html=True)
def predictive_cards(items):
    for col,(label,value,kind,context) in zip(st.columns(len(items)),items):
        shown=value if isinstance(value,str) else fmt(value,kind)
        col.markdown(f'<div class="folio"><div class="folio-label">{label}</div><div class="folio-value">{shown}</div><div class="folio-context">{context}</div></div>',unsafe_allow_html=True)
def heading(kicker,title,deck):
    st.markdown(f'<div class="atlas-head"><div class="atlas-kicker">{kicker}</div><div class="atlas-title">{title}</div><div class="atlas-deck">{deck}</div></div>',unsafe_allow_html=True)
def polish(fig):
    fig.update_layout(font_family="Inter",paper_bgcolor="#ffffff",plot_bgcolor="#ffffff",title_font_family="Inter",title_font_size=15,
                      margin=dict(l=24,r=20,t=60,b=28),legend_title_text="")
    fig.update_xaxes(showgrid=True,gridcolor="#f0f1f5",zeroline=False)
    fig.update_yaxes(showgrid=False,zeroline=False)
    return fig
def clear_filters(*keys):
    for key in keys: st.session_state[key]=[]
def grouped(df, level="SG_UF"):
    sums=[c for c in df if c.startswith("QT_") or c in ["DISPOSITIVOS"]]
    groups=df.groupby(level,dropna=False)
    g=groups[sums].sum(min_count=1).reset_index()
    schools=groups["CO_ENTIDADE"].nunique().rename("ESCOLAS").reset_index()
    g=g.merge(schools,on=level,how="left",validate="one_to_one")
    for c in ["IMDE","INDICE_ACESSIBILIDADE","IPI","DIVERSIDADE_RACIAL","TAXA_DOC_SUPERIOR","TAXA_LICENCIATURA"]:
        scores=groups.apply(lambda x: weighted(x,c),include_groups=False).rename(c).reset_index()
        g=g.merge(scores,on=level,how="left",validate="one_to_one")
    g["ALUNOS_DOCENTE"]=g.QT_MAT_BAS/g.QT_DOC_BAS.replace(0,np.nan)
    g["ALUNOS_TURMA"]=g.QT_MAT_BAS/g.QT_TUR_BAS.replace(0,np.nan)
    g["DISPOSITIVOS_100_ALUNOS"]=100*g.DISPOSITIVOS/g.QT_MAT_BAS.replace(0,np.nan)
    g["PCT_TEMPO_INTEGRAL"]=100*g.QT_MAT_BAS_INT/g.QT_MAT_BAS.replace(0,np.nan)
    return g

df2025, course2025, audit2025, history, course_history, audit_history, crosswalk, trajectories, predictions, model_meta, model_registry, model_backtests, reconciled, risks, predictive_audit = load()
predictive_pages=["Visão Geral 2026","Matrículas 2026","Pressão Operacional 2026",
                  "Infraestrutura 2026","Tendências & Riscos","Modelos & Validação"]
df=df2025; course=course2025; audit=audit2025
st.sidebar.markdown("## ATLAS 25")
st.sidebar.caption("Caderno de evidências da educação básica")
area=st.sidebar.radio("ÁREA",["Leituras","Análises Preditivas"],horizontal=True,key="nav_area")
if area=="Leituras":
    page=st.sidebar.radio("LEITURAS",["Visão Executiva","Infraestrutura & Inclusão","Estudantes & Equidade",
     "Docentes & Gestão","Educação Profissional","Priorização","Ranking e comparação","Relatórios","Qualidade dos dados","Principais Descobertas"],key="nav_main")
else:
    st.sidebar.markdown("#### ANÁLISES PREDITIVAS")
    page=st.sidebar.radio("Modelagem temporal",predictive_pages,key="nav_predictive",label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown("#### RECORTE TERRITORIAL")
if area=="Leituras":
    year_choice=st.sidebar.selectbox("Ano",["Todos os anos",2021,2022,2023,2024,2025],index=5,key="f_year")
    selected_year=year_choice
else:
    year_choice="Todos os anos"; selected_year="Histórico 2021–2025 · Horizonte 2026"
    st.sidebar.caption("Histórico: 2021–2025\n\nHorizonte: 2026")
if area=="Análises Preditivas":
    df=df2025; course=course2025; audit=audit_history
elif year_choice=="Todos os anos":
    df=history.copy(); course=course_history.copy(); audit=audit_history.copy()
elif year_choice != 2025:
    df=history[history.ANO.eq(year_choice)].copy(); course=course_history[course_history.ANO.eq(year_choice)].copy()
    audit=audit_history[audit_history.ANO.eq(year_choice)].copy()
    df["IMDE"]=df.IMDE_HISTORICO_COMPATIVEL; df["INDICE_ACESSIBILIDADE"]=df.INDICE_ACESSIBILIDADE_HIST
    df["IPI"]=df.IPI_HISTORICO_RELATIVO
    for col in ["DIVERSIDADE_RACIAL","TAXA_DOC_SUPERIOR","TAXA_LICENCIATURA","QT_GEST_BAS",
                "QT_DOC_BAS_ESCO_SUP_GRAD","QT_DOC_BAS_ESCO_SUP_GRAD_LICEN","QT_DOC_BAS_VINCULO_CONCUR",
                "QT_GEST_BAS_ESCO_SUP_GRAD","PRESSAO_OUTLIER","DIF_SEXO","DIF_RACA"]: df[col]=np.nan
    df["TEM_MATRICULA"]=df.QT_MAT_BAS.notna()
if "IMDE" not in df and "IMDE_HISTORICO_COMPATIVEL" in df:
    df["IMDE"]=df.IMDE_HISTORICO_COMPATIVEL; df["INDICE_ACESSIBILIDADE"]=df.INDICE_ACESSIBILIDADE_HIST
    df["IPI"]=df.IPI_HISTORICO_RELATIVO
for col in ["DIVERSIDADE_RACIAL","TAXA_DOC_SUPERIOR","TAXA_LICENCIATURA","QT_GEST_BAS",
            "QT_DOC_BAS_ESCO_SUP_GRAD","QT_DOC_BAS_ESCO_SUP_GRAD_LICEN","QT_DOC_BAS_VINCULO_CONCUR",
            "QT_GEST_BAS_ESCO_SUP_GRAD","PRESSAO_OUTLIER","DIF_SEXO","DIF_RACA"]:
    if col not in df: df[col]=np.nan
if "TEM_MATRICULA" not in df: df["TEM_MATRICULA"]=df.QT_MAT_BAS.notna()
df["MUNICIPIO_UF"] = df["NO_MUNICIPIO"].fillna("Não informado") + " — " + df["SG_UF"].fillna("NI")
df["ESCOLA_ROTULO"] = df["NO_ENTIDADE"].fillna("Sem nome") + " — " + df["CO_ENTIDADE"].astype("Int64").astype(str)
if st.sidebar.button("Limpar todos os filtros"):
    for k in ["f_region","f_uf","f_dep","f_loc","f_status","f_municipio","f_escola"]:
        st.session_state[k]=[]
    st.rerun()
region=st.sidebar.multiselect("Região",sorted(df.NO_REGIAO.dropna().unique()),key="f_region",on_change=clear_filters,args=("f_uf","f_municipio","f_escola"))
x=df[df.NO_REGIAO.isin(region)] if region else df
uf=st.sidebar.multiselect("Estado (UF)",sorted(x.SG_UF.dropna().unique()),key="f_uf",on_change=clear_filters,args=("f_municipio","f_escola"))
x=x[x.SG_UF.isin(uf)] if uf else x
dep=st.sidebar.multiselect("Rede administrativa",sorted(x.DEPENDENCIA.dropna().unique()),key="f_dep",on_change=clear_filters,args=("f_municipio","f_escola"))
x=x[x.DEPENDENCIA.isin(dep)] if dep else x
loc=st.sidebar.multiselect("Localização",sorted(x.LOCALIZACAO.dropna().unique()),key="f_loc",on_change=clear_filters,args=("f_municipio","f_escola"))
x=x[x.LOCALIZACAO.isin(loc)] if loc else x
status=st.sidebar.multiselect("Situação da escola",sorted(x.SITUACAO.dropna().unique()),default=["Em atividade"],key="f_status",on_change=clear_filters,args=("f_municipio","f_escola"))
x=x[x.SITUACAO.isin(status)] if status else x
municipio=st.sidebar.multiselect("Município",sorted(x.MUNICIPIO_UF.dropna().unique()),max_selections=20,key="f_municipio",on_change=clear_filters,args=("f_escola",))
x=x[x.MUNICIPIO_UF.isin(municipio)] if municipio else x
if municipio:
    escola_sel=st.sidebar.multiselect("Escola",sorted(x.ESCOLA_ROTULO.dropna().unique()),max_selections=20,key="f_escola")
    x=x[x.ESCOLA_ROTULO.isin(escola_sel)] if escola_sel else x
active=x
filter_count=sum(bool(v) for v in [region,uf,dep,loc,status,municipio])
st.sidebar.markdown(f'<div class="filter-note"><b>{len(active):,.0f}</b> escolas no recorte<br>{filter_count} filtro(s) ativo(s)</div>'.replace(",","."),unsafe_allow_html=True)
if active.empty:
    st.warning("Nenhuma escola ativa corresponde à combinação de filtros.")
    st.stop()

historical_allowed={"Visão Executiva","Infraestrutura & Inclusão","Relatórios","Qualidade dos dados"}
incompatible=(year_choice!="Todos os anos" and year_choice!=2025 and page not in historical_allowed and page not in predictive_pages
              and not (page=="Educação Profissional" and year_choice in [2023,2024]))
if year_choice=="Todos os anos" and page not in predictive_pages and page!="Qualidade dos dados":
    heading("Série histórica","Selecione um ano para esta leitura","A opção Todos os anos é reservada às páginas temporais para evitar somas repetidas da mesma escola.")
    st.info("Escolha 2021, 2022, 2023, 2024 ou 2025 no filtro lateral.")
elif incompatible:
    heading("Disponibilidade histórica","Indicador não disponível para este ano","O layout selecionado não contém equivalentes oficiais para todos os componentes desta página.")
    st.warning("Dados ausentes não foram convertidos em zero. Consulte a matriz de compatibilidade em Modelos & Validação.")
elif page=="Visão Geral 2026":
    heading("ANÁLISES PREDITIVAS","Perspectivas para 2026","Modelos construídos a partir do histórico harmonizado de 2021–2025.")
    hh=history[history.SITUACAO.eq("Em atividade")]
    annual=hh.groupby("ANO").agg(MATRICULAS=("QT_MAT_BAS","sum"),ESCOLAS=("CO_ENTIDADE","nunique")).reset_index()
    m=model_registry[model_registry.INDICADOR.eq("MATRICULAS")].iloc[0]
    recent=100*(annual.iloc[-1].MATRICULAS/annual.iloc[-2].MATRICULAS-1)
    predictive_cards([("MATRÍCULAS 2026","Sem previsão aprovada","s","O método testado errou mais que repetir 2024"),
      ("ÚLTIMO REALIZADO",annual.iloc[-1].MATRICULAS,"n","2025 · universo total de escolas ativas"),
      ("TENDÊNCIA RECENTE",recent,"%","Variação observada de 2024 para 2025"),
      ("STATUS","Em revisão","s","Resultado disponível apenas para exploração")])
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=annual.ANO,y=annual.MATRICULAS,name="Realizado",mode="lines+markers",line=dict(color="#625df5",width=3)))
    fig.add_trace(go.Scatter(x=[2025,2026],y=[m.REAL_2025,m.CENARIO_2026],name="Cenário indicativo",mode="lines+markers",
                  line=dict(color="#e59b35",width=3,dash="dash"),marker_symbol="circle-open"))
    fig.add_trace(go.Scatter(x=[2026,2026],y=[m.LIMITE_INFERIOR,m.LIMITE_SUPERIOR],name="Intervalo estimado",mode="lines",line=dict(color="#e59b35",width=10)))
    fig.update_layout(title="Histórico de matrículas e cenário indicativo para 2026",xaxis=dict(dtick=1),height=390,hovermode="x unified")
    st.plotly_chart(fig,use_container_width=True,theme=None)
    st.info(f"As matrículas diminuíram {fmt(abs(recent),'%')} entre 2024 e 2025. O método testado errou mais do que simplesmente repetir o resultado de 2024. Por isso, não há previsão nacional aprovada para 2026.")
    ufview=reconciled[reconciled.NIVEL.eq("UF")]
    c1,c2=st.columns(2)
    c1.plotly_chart(px.bar(ufview.nlargest(10,"DELTA_PCT"),x="LOCALIDADE",y="DELTA_PCT",title="Estados com maior alta possível",
      labels={"LOCALIDADE":"Estado","DELTA_PCT":"Variação (%)"}),use_container_width=True,theme=None)
    c2.plotly_chart(px.bar(ufview.nsmallest(10,"DELTA_PCT"),x="LOCALIDADE",y="DELTA_PCT",title="Estados com maior redução possível",
      labels={"LOCALIDADE":"Estado","DELTA_PCT":"Variação (%)"}),use_container_width=True,theme=None)

elif page=="Matrículas 2026":
    heading("ANÁLISES PREDITIVAS","Matrículas em 2026","Os totais de regiões, estados, redes e localização foram conferidos para coincidir com o Brasil.")
    m=model_registry[model_registry.INDICADOR.eq("MATRICULAS")].iloc[0]
    predictive_cards([("PREVISÃO BRASIL 2026","Sem previsão aprovada","s","O método testado errou mais que repetir 2024"),
      ("POSSÍVEL CENÁRIO",m.CENARIO_2026,"n","Resultado exploratório · baixa confiança"),
      ("VARIAÇÃO VS 2025",m.VARIACAO_2026_PCT,"%","Dentro do comportamento histórico"),
      ("INTERVALO ESTIMADO",f"{fmt(m.LIMITE_INFERIOR)} – {fmt(m.LIMITE_SUPERIOR)}","s","Intervalo de previsão, não de certeza")])
    level=st.radio("Detalhamento",["REGIAO","UF","REDE","LOCALIZACAO"],horizontal=True,format_func=lambda x:{"REGIAO":"Região","UF":"UF","REDE":"Rede","LOCALIZACAO":"Urbano/rural"}[x])
    table=reconciled[reconciled.NIVEL.eq(level)].copy()
    table=table[["LOCALIDADE","REAL_2025","CENARIO_2026","DELTA_ABS","DELTA_PCT","LIMITE_INFERIOR","LIMITE_SUPERIOR","CONFIANCA","ALERTA"]]
    st.plotly_chart(px.bar(table.sort_values("DELTA_PCT"),x="LOCALIDADE",y="DELTA_PCT",color="DELTA_PCT",
      color_continuous_scale="RdYlGn",title=f"Mudança indicada para 2026 — {level.title()}",
      labels={"LOCALIDADE":"Localidade","DELTA_PCT":"Variação prevista (%)"}),use_container_width=True,theme=None)
    display_table=friendly_table(table,{"LOCALIDADE":"Localidade","REAL_2025":"Realizado em 2025","CENARIO_2026":"Cenário para 2026",
      "DELTA_ABS":"Variação absoluta","DELTA_PCT":"Variação (%)","LIMITE_INFERIOR":"Limite inferior",
      "LIMITE_SUPERIOR":"Limite superior","CONFIANCA":"Status","ALERTA":"Verificação"},
      ["REAL_2025","CENARIO_2026","DELTA_ABS","LIMITE_INFERIOR","LIMITE_SUPERIOR"],["DELTA_PCT"])
    display_table["Status"]=display_table["Status"].replace({"REPROVADO":"Não aprovado","APROVADO":"Aprovado","EXPERIMENTAL":"Em avaliação"})
    c1,c2=st.columns(2)
    c1.markdown("#### Maiores crescimentos indicados"); c1.dataframe(display_table.loc[table.nlargest(10,"DELTA_PCT").index],hide_index=True,use_container_width=True)
    c2.markdown("#### Maiores reduções indicadas"); c2.dataframe(display_table.loc[table.nsmallest(10,"DELTA_PCT").index],hide_index=True,use_container_width=True)
    st.warning("Possível cenário — baixa confiança. O método usado para matrículas não passou nos testes. Os valores servem apenas para explorar uma possibilidade para 2026.")

elif page=="Pressão Operacional 2026":
    heading("ANÁLISES PREDITIVAS","Pressão operacional em 2026","Como a relação entre matrículas, docentes, turmas e salas pode evoluir no próximo período.")
    hh=history[history.SITUACAO.eq("Em atividade")]
    annual=hh.groupby("ANO").agg(MATRICULAS=("QT_MAT_BAS","sum"),DOCENTES=("QT_DOC_BAS","sum"),TURMAS=("QT_TUR_BAS","sum"),SALAS=("QT_SALAS_UTILIZADAS","sum")).reset_index()
    annual["Alunos/docente"]=annual.MATRICULAS/annual.DOCENTES.replace(0,np.nan)
    annual["Alunos/turma"]=annual.MATRICULAS/annual.TURMAS.replace(0,np.nan)
    annual["Matrículas/sala"]=annual.MATRICULAS/annual.SALAS.replace(0,np.nan)
    pressure_cols=["Alunos/docente","Alunos/turma","Matrículas/sala"]
    metric_keys={"Alunos/docente":"ALUNOS_DOCENTE","Alunos/turma":"ALUNOS_TURMA","Matrículas/sala":"MATRICULAS_SALA"}
    projected={c:model_registry[model_registry.INDICADOR.eq(metric_keys[c])].iloc[0] for c in pressure_cols}
    future={"ANO":2026,**{c:projected[c].CENARIO_2026 for c in pressure_cols}}
    display=pd.concat([annual.assign(TIPO="Realizado"),pd.DataFrame([future]).assign(TIPO="Projeção indicativa")],ignore_index=True)
    long=display.melt(["ANO","TIPO"],value_vars=pressure_cols,var_name="Indicador",value_name="Valor")
    predictive_cards([(f"{c.upper()} 2026",projected[c].CENARIO_2026,"d",
      f"{fmt_signed(projected[c].CENARIO_2026-projected[c].REAL_2025)} em relação a 2025 · Resultado aprovado nos testes") for c in pressure_cols])
    st.plotly_chart(px.line(long,x="ANO",y="Valor",color="Indicador",line_dash="TIPO",markers=True,title="Evolução da pressão operacional — 2021 a 2026",
      labels={"ANO":"Ano","Valor":"Resultado","Indicador":"Medida analisada","TIPO":"Tipo de resultado"}),use_container_width=True,theme=None)
    st.caption("2021–2025: dados conhecidos • 2026: resultado calculado por métodos que passaram nos testes")
    ufpress=[]
    for name,g in history[history.SITUACAO.eq("Em atividade")].groupby("SG_UF"):
        s=g.groupby("ANO").apply(lambda z:z.QT_MAT_BAS.sum()/z.QT_DOC_BAS.sum(),include_groups=False)
        p=trend_projection(s); ufpress.append({"UF":name,"REAL_2025":s.loc[2025],"PREVISTO_2026":p["projection"],"DELTA":p["projection"]-s.loc[2025]})
    ufpress=pd.DataFrame(ufpress)
    st.plotly_chart(px.bar(ufpress.nlargest(12,"DELTA"),x="UF",y="DELTA",title="UFs com maior aumento indicado em alunos por docente",
      labels={"UF":"UF","DELTA":"Variação prevista"}),use_container_width=True,theme=None)

elif page=="Infraestrutura 2026":
    heading("ANÁLISES PREDITIVAS","Infraestrutura em 2026","Um resultado só é destacado quando foi mais preciso do que repetir o ano anterior e permaneceu entre 0 e 100.")
    hh=history[history.SITUACAO.eq("Em atividade")]
    def yearly_weighted(group,col): return weighted(group,col)
    rows=[]
    for year,g in hh.groupby("ANO"):
        rows.append({"ANO":year,"IMDE Histórico Compatível":yearly_weighted(g,"IMDE_HISTORICO_COMPATIVEL"),
                     "Acessibilidade":yearly_weighted(g,"INDICE_ACESSIBILIDADE_HIST"),
                     "Internet (%)":100*g.IN_INTERNET.mean(),"Banda larga (%)":100*g.IN_BANDA_LARGA.mean()})
    infra=pd.DataFrame(rows); infra_cols=[c for c in infra if c!="ANO"]
    metric_keys={"IMDE Histórico Compatível":"IMDE","Acessibilidade":"ACESSIBILIDADE","Internet (%)":"INTERNET_PCT","Banda larga (%)":"BANDA_LARGA_PCT"}
    projected={c:model_registry[model_registry.INDICADOR.eq(metric_keys[c])].iloc[0] for c in infra_cols}
    future={"ANO":2026,**{c:projected[c].CENARIO_2026 for c in infra_cols}}
    display=pd.concat([infra.assign(TIPO="Realizado"),pd.DataFrame([future]).assign(TIPO="Projeção indicativa")],ignore_index=True)
    long=display.melt(["ANO","TIPO"],value_vars=infra_cols,var_name="Indicador",value_name="Valor")
    predictive_cards([(f"{c.upper()} 2026",future[c] if projected[c].PUBLICAR_2026 else "Sem previsão aprovada","d" if projected[c].PUBLICAR_2026 else "s",
      f"{fmt_signed(future[c]-projected[c].REAL_2025)} em relação a 2025 · {'Aprovado nos testes' if projected[c].PUBLICAR_2026 else 'Não passou nos testes'}") for c in infra_cols])
    st.plotly_chart(px.line(long,x="ANO",y="Valor",color="Indicador",line_dash="TIPO",markers=True,range_y=[0,100],title="Infraestrutura das escolas — histórico e 2026",
      labels={"ANO":"Ano","Valor":"Resultado de 0 a 100","Indicador":"Condição analisada","TIPO":"Tipo de resultado"}),use_container_width=True,theme=None)
    st.caption("2021–2025: dados conhecidos • 2026: resultado futuro, exibido somente quando aprovado nos testes")
    rejected=[c for c in infra_cols if not projected[c].PUBLICAR_2026]
    if rejected: st.info("Não há previsão aprovada para "+", ".join(rejected)+": repetir o resultado do ano anterior foi igual ou mais preciso.")
    st.info("O IPI relativo é adequado para prioridade dentro de cada ano; sua escala percentílica impede interpretar queda absoluta como melhoria estrutural.")

elif page=="Tendências & Riscos":
    heading("ANÁLISES PREDITIVAS","Tendências e riscos para 2026","Sinais históricos orientados à investigação; não representam certeza futura nem relação causal.")
    counts=trajectories.TRAJETORIA.value_counts().rename_axis("TRAJETORIA").reset_index(name="ESCOLAS")
    c1,c2=st.columns(2)
    c1.plotly_chart(px.bar(counts,x="TRAJETORIA",y="ESCOLAS",title="Comportamento das matrículas ao longo dos anos",
      labels={"TRAJETORIA":"Comportamento observado","ESCOLAS":"Quantidade de escolas"}),use_container_width=True,theme=None)
    involved=risks[risks.RISCO_2026.gt(0)].groupby("RISCO_2026").agg(ESCOLAS=("CO_ENTIDADE","nunique"),MATRICULAS=("QT_MAT_BAS","sum")).reset_index()
    c2.plotly_chart(px.bar(involved,x="RISCO_2026",y="ESCOLAS",title="Escolas por quantidade de sinais de risco",
      labels={"RISCO_2026":"Quantidade de sinais","ESCOLAS":"Escolas"}),use_container_width=True,theme=None)
    risk_uf=risks[risks.RISCO_2026.gt(0)].groupby("SG_UF").agg(ESCOLAS=("CO_ENTIDADE","nunique"),MATRICULAS_ENVOLVIDAS=("QT_MAT_BAS","sum"),SINAIS=("RISCO_2026","sum")).reset_index()
    st.plotly_chart(px.bar(risk_uf.nlargest(15,"SINAIS"),x="SG_UF",y="SINAIS",color="MATRICULAS_ENVOLVIDAS",title="Territórios com mais sinais para investigação em 2026",
      labels={"SG_UF":"UF","SINAIS":"Quantidade de sinais","MATRICULAS_ENVOLVIDAS":"Matrículas envolvidas"}),use_container_width=True,theme=None)
    risk_display=risks[risks.RISCO_2026.gt(0)][["NO_ENTIDADE","NO_MUNICIPIO","SG_UF","QT_MAT_BAS","SINAIS","ANOS_HISTORICO"]].head(100)
    risk_display=friendly_table(risk_display,{"NO_ENTIDADE":"Escola","NO_MUNICIPIO":"Município","SG_UF":"UF","QT_MAT_BAS":"Matrículas em 2025","SINAIS":"Sinais para investigação","ANOS_HISTORICO":"Anos no histórico"},["QT_MAT_BAS","ANOS_HISTORICO"])
    st.dataframe(risk_display,use_container_width=True,hide_index=True)
    st.caption("Mudança atípica, queda persistente, pressão crescente e infraestrutura estagnada são sinais de investigação — não previsões determinísticas.")
    unusual=trajectories[trajectories.VARIACAO_ATIPICA_INVESTIGAR].sort_values("INCLINACAO_ANUAL",ascending=False).head(100)
    unusual=friendly_table(unusual,{"CO_ENTIDADE":"Código da escola","ANOS_OBSERVADOS":"Anos com dados","ANO_INICIAL":"Primeiro ano",
      "ANO_FINAL":"Último ano","MATRICULAS_INICIAL":"Matrículas no primeiro ano","MATRICULAS_FINAL":"Matrículas no último ano",
      "INCLINACAO_ANUAL":"Mudança média por ano","TRAJETORIA":"Comportamento observado","VARIACAO_ATIPICA_INVESTIGAR":"Mudança fora do padrão?"},
      ["CO_ENTIDADE","ANOS_OBSERVADOS","ANO_INICIAL","ANO_FINAL","MATRICULAS_INICIAL","MATRICULAS_FINAL","INCLINACAO_ANUAL"])
    unusual["Mudança fora do padrão?"]=unusual["Mudança fora do padrão?"].map({True:"Sim",False:"Não"})
    st.dataframe(unusual,use_container_width=True,hide_index=True)
    st.caption("Ausência cadastral não é interpretada como fechamento; a situação oficial deve ser verificada no ano correspondente.")

elif page=="Modelos & Validação":
    heading("ANÁLISES PREDITIVAS","Como as previsões foram avaliadas","Veja, em linguagem simples, quais métodos funcionaram melhor usando anos cujos resultados já conhecemos.")
    tab1,tab2,tab3,tab4=st.tabs(["Resumo dos resultados","Testes com anos conhecidos","Dados disponíveis","Qualidade dos dados"])
    with tab1:
        show=model_registry[["INDICADOR","MODELO","ERRO_MEDIO_MODELO","ERRO_MEDIO_BASELINE","SUPEROU_BASELINE","SANITY_CHECK","STATUS","PUBLICAR_2026"]]
        show=show.copy(); show["INDICADOR"]=show.INDICADOR.map(INDICATOR_LABELS).fillna(show.INDICADOR)
        show["MODELO"]=show.MODELO.map(MODEL_LABELS).fillna(show.MODELO)
        show["SUPEROU_BASELINE"]=show.SUPEROU_BASELINE.map({True:"Sim",False:"Não"})
        show["PUBLICAR_2026"]=show.PUBLICAR_2026.map({True:"Sim",False:"Não"})
        show["SANITY_CHECK"]=show.SANITY_CHECK.replace({"OK":"Aprovado","EXTRAPOLACAO_FORTE":"Extrapolação forte"})
        show["STATUS"]=show.STATUS.replace({"REPROVADO":"Não aprovado","APROVADO":"Aprovado","EXPERIMENTAL":"Em avaliação"})
        show=friendly_table(show,{"INDICADOR":"O que foi analisado","MODELO":"Método utilizado","ERRO_MEDIO_MODELO":"Erro médio do método",
          "ERRO_MEDIO_BASELINE":"Erro ao repetir o ano anterior","SUPEROU_BASELINE":"Foi mais preciso?","SANITY_CHECK":"Verificações básicas",
          "STATUS":"Resultado da avaliação","PUBLICAR_2026":"Pode aparecer como previsão?"},["ERRO_MEDIO_MODELO","ERRO_MEDIO_BASELINE"])
        st.dataframe(show,use_container_width=True,hide_index=True)
        st.caption("Aprovado: foi melhor que repetir o ano anterior e não produziu valores impossíveis. Reprovado: foi menos preciso ou apresentou resultado incoerente.")
    with tab2:
        selected=st.selectbox("Indicador",model_registry.INDICADOR.tolist(),format_func=lambda value:INDICATOR_LABELS.get(value,value),key="backtest_metric")
        bt=model_backtests[model_backtests.INDICADOR.eq(selected)]
        bt=bt.copy(); bt["INDICADOR"]=bt.INDICADOR.map(INDICATOR_LABELS).fillna(bt.INDICADOR); bt["MODELO"]=bt.MODELO.map(MODEL_LABELS).fillna(bt.MODELO)
        bt=friendly_table(bt,{"INDICADOR":"O que foi analisado","MODELO":"Método utilizado","BACKTEST_ANO":"Ano usado no teste","REAL":"Resultado conhecido",
          "PREVISTO":"Resultado calculado","ERRO_ABSOLUTO":"Quanto o método errou","ERRO_PCT":"Erro (%)"},["BACKTEST_ANO","REAL","PREVISTO","ERRO_ABSOLUTO"],["ERRO_PCT"])
        st.dataframe(bt,use_container_width=True,hide_index=True)
        if selected=="MATRICULAS":
            test2025=predictions[predictions.ANO_PREVISTO.eq(2025)]
            real=test2025.REALIZADO.sum(); model=test2025.PREVISAO.sum()
            test_ids=set(test2025.CO_ENTIDADE)
            baseline=history[history.ANO.eq(2024) & history.SITUACAO.eq("Em atividade") & history.CO_ENTIDADE.isin(test_ids)].QT_MAT_BAS.sum()
            predictive_cards([("RESULTADO CONHECIDO DE 2025",real,"n","Escolas com dados disponíveis em 2024 e 2025"),
              ("MODELO ESTATÍSTICO (RIDGE)",model,"n",f"Previsão baseada no histórico · errou {fmt(abs(model-real))}"),
              ("MODELO SIMPLES",baseline,"n",f"Repete o resultado anterior · errou {fmt(abs(baseline-real))}"),
              ("MODELO SIMPLES FOI MAIS PRECISO","Resultado do teste","s","O modelo estatístico apresentou erro maior")])
            st.warning("Este teste considera somente as escolas com dados disponíveis nos dois anos. Ele não representa o total nacional completo de 2025, que foi de 46.018.380 matrículas.")
    with tab3:
        availability=pd.DataFrame([
          ["Matrículas","Disponível","Disponível","Disponível","Disponível","Disponível"],
          ["Docentes e turmas — totais","Disponível","Disponível","Disponível","Disponível","Disponível"],
          ["Internet e banda larga","Disponível","Disponível","Disponível","Disponível","Disponível"],
          ["Acessibilidade","Disponível","Disponível","Disponível","Disponível","Disponível"],
          ["Cursos técnicos","Não disponível","Não disponível","Disponível","Disponível","Disponível"],
          ["Perfil detalhado de docentes e gestores","Não disponível","Não disponível","Não disponível","Não disponível","Disponível"],
        ],columns=["Informação","2021","2022","2023","2024","2025"])
        st.dataframe(availability,use_container_width=True,hide_index=True)
        st.caption("Quando uma informação não foi encontrada ou mudou de significado, ela não é tratada como zero e não é usada para inventar uma série histórica.")
    with tab4:
        quality=friendly_table(audit_history,{"ANO":"Ano","REGISTROS":"Registros","ESCOLAS":"Escolas","MUNICIPIOS":"Municípios",
          "CAMPOS_HARMONIZADOS":"Campos harmonizados","VALORES_NULOS":"Valores ausentes","CHAVES_DUPLICADAS":"Chaves duplicadas",
          "CAMPOS_COMPATIVEIS":"Campos compatíveis","CAMPOS_PARCIAIS":"Campos parcialmente compatíveis",
          "INDICE_COMPATIBILIDADE":"Compatibilidade (%)","NOTA":"Observação"},
          ["ANO","REGISTROS","ESCOLAS","MUNICIPIOS","CAMPOS_HARMONIZADOS","VALORES_NULOS","CHAVES_DUPLICADAS","CAMPOS_COMPATIVEIS","CAMPOS_PARCIAIS"],["INDICE_COMPATIBILIDADE"])
        st.dataframe(quality,use_container_width=True,hide_index=True)
        st.caption("Continuidade cadastral é usada como critério de confiabilidade, não como previsão.")

elif page=="Visão Executiva":
    heading("Leitura 01 · panorama","O tamanho da rede — e onde ela tensiona","Uma abertura nacional que combina escala, capacidade operacional e sinais territoriais de prioridade.")
    cards([("Matrículas",active.QT_MAT_BAS.sum(),"n"),("Escolas no recorte",active.CO_ENTIDADE.nunique(),"n"),
      ("Docentes",active.QT_DOC_BAS.sum(),"n"),("Turmas",active.QT_TUR_BAS.sum(),"n"),
      ("Alunos/docente",div(active.QT_MAT_BAS.sum(),active.QT_DOC_BAS.sum()),"d"),
      ("Alunos/turma",div(active.QT_MAT_BAS.sum(),active.QT_TUR_BAS.sum()),"d"),
      ("Tempo integral",100*div(active.QT_MAT_BAS_INT.sum(),active.QT_MAT_BAS.sum()),"%"),
      ("Escolas c/ banda larga",100*active.IN_BANDA_LARGA.mean(),"%")])
    g=grouped(active,"SG_UF")
    c1,c2=st.columns(2)
    c1.plotly_chart(px.bar(active.groupby("NO_REGIAO",as_index=False).QT_MAT_BAS.sum(),x="NO_REGIAO",y="QT_MAT_BAS",title="Matrículas por região",
      labels={"NO_REGIAO":"Região","QT_MAT_BAS":"Matrículas"}),use_container_width=True,theme=None)
    c2.plotly_chart(px.bar(active.groupby("DEPENDENCIA",as_index=False).QT_MAT_BAS.sum(),x="DEPENDENCIA",y="QT_MAT_BAS",title="Matrículas por rede",
      labels={"DEPENDENCIA":"Rede administrativa","QT_MAT_BAS":"Matrículas"}),use_container_width=True,theme=None)
    st.plotly_chart(px.bar(g.sort_values("IPI",ascending=False),x="SG_UF",y="IPI",color="NO_REGIAO" if "NO_REGIAO" in g else None,
      title="Prioridade de infraestrutura por estado",labels={"SG_UF":"Estado (UF)","IPI":"Índice de Prioridade de Infraestrutura (IPI)","NO_REGIAO":"Região"}),use_container_width=True,theme=None)
    st.caption("IPI significa Índice de Prioridade de Infraestrutura. Valores maiores indicam mais sinais de carência e pressão, servindo como ponto de partida para investigação — não como nota de qualidade.")

elif page=="Infraestrutura & Inclusão":
    heading("Leitura 02 · condições de oferta","Infraestrutura que aproxima — ou afasta","Conectividade, recursos digitais e acessibilidade lidos lado a lado, sempre dentro do recorte selecionado.")
    cards([("Maturidade digital (IMDE)",weighted(active,"IMDE"),"d"),("Acessibilidade",weighted(active,"INDICE_ACESSIBILIDADE"),"d"),
           ("Dispositivos/100 alunos",div(active.DISPOSITIVOS.sum()*100,active.QT_MAT_BAS.sum()),"d"),
           ("Banda larga",100*active.IN_BANDA_LARGA.mean(),"%")])
    levels={"UF":"SG_UF","Município":"MUNICIPIO_UF","Escola":"ESCOLA_ROTULO"}
    level_label=st.radio("Detalhamento territorial",list(levels),horizontal=True,key="infra_level")
    level=levels[level_label]; g=grouped(active,level)
    order_label=st.selectbox("Ordenar por",["Menor IMDE","Menor acessibilidade","Menos dispositivos/100 alunos","Maior IPI"])
    order_map={"Menor IMDE":("IMDE",True),"Menor acessibilidade":("INDICE_ACESSIBILIDADE",True),
               "Menos dispositivos/100 alunos":("DISPOSITIVOS_100_ALUNOS",True),"Maior IPI":("IPI",False)}
    metric,ascending=order_map[order_label]
    limit=st.slider("Quantidade exibida",5,50,20,key="infra_limit")
    show=g.sort_values(metric,ascending=ascending).head(limit)
    long=show[[level,"IMDE","INDICE_ACESSIBILIDADE"]].melt(level,var_name="Indicador",value_name="Índice")
    long["Indicador"]=long.Indicador.replace({"IMDE":"Maturidade digital","INDICE_ACESSIBILIDADE":"Acessibilidade"})
    st.plotly_chart(px.bar(long,y=level,x="Índice",color="Indicador",barmode="group",orientation="h",
      range_x=[0,100],title=f"Maturidade digital e acessibilidade — {level_label}",
      labels={level:level_label,"Índice":"Resultado de 0 a 100","Indicador":"Indicador analisado"}),use_container_width=True,theme=None)
    c1,c2=st.columns(2)
    c1.plotly_chart(px.bar(show.sort_values("DISPOSITIVOS_100_ALUNOS"),y=level,x="DISPOSITIVOS_100_ALUNOS",orientation="h",title="Dispositivos disponíveis para cada 100 alunos",
      labels={level:level_label,"DISPOSITIVOS_100_ALUNOS":"Dispositivos por 100 alunos"}),use_container_width=True,theme=None)
    c2.plotly_chart(px.bar(show.sort_values("IPI"),y=level,x="IPI",orientation="h",range_x=[0,100],title="Prioridade de infraestrutura",
      labels={level:level_label,"IPI":"Índice de Prioridade de Infraestrutura (IPI)"}),use_container_width=True,theme=None)
    st.caption("Todos os gráficos respeitam os filtros laterais. Nulos não são convertidos em zero.")
    st.info("IMDE significa Índice de Maturidade Digital Escolar. Ele reúne conexão à internet, banda larga, acesso dos alunos, uso pedagógico e quantidade de equipamentos. IPI significa Índice de Prioridade de Infraestrutura e ajuda a localizar escolas que merecem investigação.")

elif page=="Estudantes & Equidade":
    heading("Leitura 03 · quem está na escola","Estudantes e equidade","Perfil demográfico, diversidade e modalidades de atendimento sem misturar populações estatísticas incompatíveis.")
    sex=pd.DataFrame({"Categoria":["Feminino","Masculino","Não declarado"],"Matrículas":[active.QT_MAT_BAS_FEM.sum(),active.QT_MAT_BAS_MASC.sum(),active.QT_MAT_BAS_ND.sum()]})
    race_cols={"Branca":"QT_MAT_BAS_BRANCA","Preta":"QT_MAT_BAS_PRETA","Parda":"QT_MAT_BAS_PARDA","Amarela":"QT_MAT_BAS_AMARELA","Indígena":"QT_MAT_BAS_INDIGENA"}
    race=pd.DataFrame({"Categoria":list(race_cols),"Matrículas":[active[c].sum() for c in race_cols.values()]})
    c1,c2=st.columns(2); c1.plotly_chart(px.pie(sex,names="Categoria",values="Matrículas",title="Sexo"),use_container_width=True,theme=None); c2.plotly_chart(px.bar(race,x="Categoria",y="Matrículas",title="Raça/cor informada"),use_container_width=True,theme=None)
    g=grouped(active,"SG_UF").sort_values("DIVERSIDADE_RACIAL")
    long=g[["SG_UF","DIVERSIDADE_RACIAL","PCT_TEMPO_INTEGRAL"]].melt("SG_UF",var_name="Indicador",value_name="Percentual")
    long["Indicador"]=long.Indicador.replace({"DIVERSIDADE_RACIAL":"Diversidade racial","PCT_TEMPO_INTEGRAL":"Tempo integral"})
    st.plotly_chart(px.bar(long,x="SG_UF",y="Percentual",color="Indicador",barmode="group",title="Diversidade racial e tempo integral por estado",
      labels={"SG_UF":"Estado (UF)","Percentual":"Resultado (%)","Indicador":"Indicador analisado"}),use_container_width=True,theme=None)

elif page=="Docentes & Gestão":
    heading("Leitura 04 · pessoas que sustentam a rede","Docência e gestão","Formação, vínculo e carga discente para observar a força de trabalho educacional.")
    cards([("Docentes",active.QT_DOC_BAS.sum(),"n"),("Gestores",active.QT_GEST_BAS.sum(),"n"),
      ("Formação superior docente",100*div(active.QT_DOC_BAS_ESCO_SUP_GRAD.sum(),active.QT_DOC_BAS.sum()),"%"),
      ("Licenciatura",100*div(active.QT_DOC_BAS_ESCO_SUP_GRAD_LICEN.sum(),active.QT_DOC_BAS.sum()),"%"),
      ("Docentes concursados",100*div(active.QT_DOC_BAS_VINCULO_CONCUR.sum(),active.QT_DOC_BAS.sum()),"%"),
      ("Gestores com superior",100*div(active.QT_GEST_BAS_ESCO_SUP_GRAD.sum(),active.QT_GEST_BAS.sum()),"%")])
    g=grouped(active,"SG_UF").sort_values("TAXA_DOC_SUPERIOR")
    c1,c2=st.columns(2)
    c1.plotly_chart(px.bar(g,x="SG_UF",y="TAXA_DOC_SUPERIOR",title="Docentes com formação superior por estado",range_y=[0,100],
      labels={"SG_UF":"Estado (UF)","TAXA_DOC_SUPERIOR":"Docentes com formação superior (%)"}),use_container_width=True,theme=None)
    c2.plotly_chart(px.bar(g.sort_values("ALUNOS_DOCENTE",ascending=False),x="SG_UF",y="ALUNOS_DOCENTE",title="Quantidade de alunos por docente em cada estado",
      labels={"SG_UF":"Estado (UF)","ALUNOS_DOCENTE":"Alunos por docente"}),use_container_width=True,theme=None)

elif page=="Educação Profissional":
    heading("Leitura 05 · caminhos para o trabalho","Educação profissional","Escala, variedade e concentração territorial dos cursos técnicos.")
    ids=set(active.CO_ENTIDADE); c=course[course.CO_ENTIDADE.isin(ids)]
    course_options=sorted(c.NO_CURSO_EDUC_PROFISSIONAL.dropna().unique())
    course_sel=st.multiselect("Refinar por curso técnico",course_options,max_selections=15,key="course_filter")
    c=c[c.NO_CURSO_EDUC_PROFISSIONAL.isin(course_sel)] if course_sel else c
    cards([("Matrículas técnicas",c.QT_MAT_CURSO_TEC.sum(),"n"),("Escolas ofertantes",c.CO_ENTIDADE.nunique(),"n"),
      ("Cursos distintos",c.CO_CURSO_EDUC_PROFISSIONAL.nunique(),"n"),("Cursos/escola",div(len(c),c.CO_ENTIDADE.nunique()),"d"),
      ("Matrículas/curso",div(c.QT_MAT_CURSO_TEC.sum(),len(c)),"d")])
    top=c.groupby("NO_CURSO_EDUC_PROFISSIONAL",as_index=False).QT_MAT_CURSO_TEC.sum().nlargest(15,"QT_MAT_CURSO_TEC")
    st.plotly_chart(px.bar(top.sort_values("QT_MAT_CURSO_TEC"),x="QT_MAT_CURSO_TEC",y="NO_CURSO_EDUC_PROFISSIONAL",orientation="h",title="Cursos técnicos com mais matrículas",
      labels={"QT_MAT_CURSO_TEC":"Matrículas","NO_CURSO_EDUC_PROFISSIONAL":"Curso técnico"}),use_container_width=True,theme=None)
    def hhi(z):
        s=z.groupby("CO_CURSO_EDUC_PROFISSIONAL").QT_MAT_CURSO_TEC.sum(); return ((s/s.sum())**2).sum()*10000 if s.sum() else np.nan
    h=c.groupby("SG_UF").apply(hhi,include_groups=False).rename("HHI").reset_index()
    st.plotly_chart(px.bar(h.sort_values("HHI",ascending=False),x="SG_UF",y="HHI",title="Concentração da oferta de cursos técnicos por estado",
      labels={"SG_UF":"Estado (UF)","HHI":"Índice de concentração da oferta (HHI)"}),use_container_width=True,theme=None)
    st.info("HHI significa Índice Herfindahl-Hirschman. Próximo de zero indica oferta distribuída entre vários cursos; próximo de 10.000 indica matrículas concentradas em poucos cursos.")

elif page=="Priorização":
    heading("Leitura 06 · decisão assistida","Onde olhar primeiro","Uma fila transparente de investigação — não um veredito sobre a qualidade das escolas.")
    level=st.selectbox("Unidade",["Escola","Município"])
    if level=="Escola":
        rank=active[["NO_ENTIDADE","NO_MUNICIPIO","SG_UF","QT_MAT_BAS","IMDE","INDICE_ACESSIBILIDADE","ALUNOS_DOCENTE","ALUNOS_TURMA","IPI"]].copy(); key="NO_ENTIDADE"
    else: rank=grouped(active,"MUNICIPIO_UF"); key="MUNICIPIO_UF"
    rank=rank.sort_values("IPI",ascending=False); rank["PERCENTIL_IPI"]=rank.IPI.rank(pct=True)*100
    rank_display=rank.head(st.slider("Quantidade priorizada (simulador)",10,200,30)).rename(columns={"NO_ENTIDADE":"Escola","NO_MUNICIPIO":"Município","SG_UF":"Estado (UF)",
      "QT_MAT_BAS":"Matrículas","IMDE":"Maturidade digital (IMDE)","INDICE_ACESSIBILIDADE":"Acessibilidade",
      "ALUNOS_DOCENTE":"Alunos por docente","ALUNOS_TURMA":"Alunos por turma","IPI":"Prioridade de infraestrutura (IPI)","PERCENTIL_IPI":"Posição relativa (%)"})
    for col in ["Matrículas","Maturidade digital (IMDE)","Acessibilidade","Alunos por docente","Alunos por turma","Prioridade de infraestrutura (IPI)"]:
        if col in rank_display: rank_display[col]=rank_display[col].map(lambda value:fmt(value,"n"))
    if "Posição relativa (%)" in rank_display: rank_display["Posição relativa (%)"]=rank_display["Posição relativa (%)"].map(lambda value:fmt(value,"%"))
    st.dataframe(rank_display,use_container_width=True,hide_index=True)
    st.info("IPI alto é sinal de atenção para investigação, não um juízo de qualidade. Componentes: carência digital/acessibilidade/equipamentos (45%), pressão operacional (35%) e volume discente (20%).")

elif page=="Ranking e comparação":
    heading("Mesa de comparação","Uma medida, diferentes referências","Ranking territorial e comparação da escola com sua UF, região e o Brasil.")
    opts={"Maturidade digital (IMDE)":"IMDE","Acessibilidade":"INDICE_ACESSIBILIDADE","Alunos por docente":"ALUNOS_DOCENTE","Alunos por turma":"ALUNOS_TURMA","Tempo integral":"PCT_TEMPO_INTEGRAL","Docentes com formação superior":"TAXA_DOC_SUPERIOR","Prioridade de infraestrutura (IPI)":"IPI"}
    label=st.selectbox("Indicador",opts); metric=opts[label]; g=grouped(active,"MUNICIPIO_UF"); g["RANK"]=g[metric].rank(ascending=False,method="min"); g["PERCENTIL"]=g[metric].rank(pct=True)*100
    ranking=g.sort_values(metric,ascending=False)[["MUNICIPIO_UF",metric,"RANK","PERCENTIL"]].head(100).rename(columns={"MUNICIPIO_UF":"Município e estado",metric:label,
      "RANK":"Posição no ranking","PERCENTIL":"Posição relativa (%)"})
    ranking[label]=ranking[label].map(lambda value:fmt(value,"n")); ranking["Posição no ranking"]=ranking["Posição no ranking"].map(lambda value:fmt(value,"n"))
    ranking["Posição relativa (%)"]=ranking["Posição relativa (%)"].map(lambda value:fmt(value,"%"))
    st.dataframe(ranking,use_container_width=True,hide_index=True)
    school=st.selectbox("Benchmark de escola",active.ESCOLA_ROTULO.sort_values().unique())
    row=active[active.ESCOLA_ROTULO.eq(school)].iloc[0]; val=row[metric]; ufm=weighted(active[active.SG_UF.eq(row.SG_UF)],metric); regm=weighted(active[active.NO_REGIAO.eq(row.NO_REGIAO)],metric); br=weighted(active,metric)
    cards([("Resultado",val,"d"),("Média do estado",ufm,"d"),("Média da região",regm,"d"),("Média do Brasil",br,"d"),("Diferença para o estado",val-ufm,"d"),("Diferença para o Brasil",val-br,"d")])

elif page=="Relatórios":
    heading("Central de dados","Relatórios e exportação","Monte uma tabela do recorte atual, escolha as colunas e exporte em CSV, um formato de planilha compatível com Excel e outros programas.")
    friendly={"ESCOLA_ROTULO":"Escola","MUNICIPIO_UF":"Município / UF","NO_REGIAO":"Região","DEPENDENCIA":"Rede",
      "LOCALIZACAO":"Localização","SITUACAO":"Situação","QT_MAT_BAS":"Matrículas","QT_DOC_BAS":"Docentes",
      "QT_TUR_BAS":"Turmas","ALUNOS_DOCENTE":"Alunos por docente","ALUNOS_TURMA":"Alunos por turma","IMDE":"Maturidade digital (IMDE)",
      "INDICE_ACESSIBILIDADE":"Acessibilidade","DISPOSITIVOS_100_ALUNOS":"Dispositivos por 100 alunos","IPI":"Prioridade de infraestrutura (IPI)",
      "PCT_TEMPO_INTEGRAL":"Tempo integral (%)","TAXA_DOC_SUPERIOR":"Docentes com superior (%)"}
    defaults=["ESCOLA_ROTULO","MUNICIPIO_UF","DEPENDENCIA","LOCALIZACAO","QT_MAT_BAS","IMDE","INDICE_ACESSIBILIDADE","IPI"]
    chosen=st.multiselect("Colunas do relatório",list(friendly),default=defaults,format_func=lambda z:friendly[z])
    if not chosen: st.info("Selecione pelo menos uma coluna para montar o relatório.")
    else:
        report=active[chosen].rename(columns=friendly)
        c1,c2,c3=st.columns([2,1,1])
        sort_label=c1.selectbox("Ordenar por",list(report.columns))
        direction=c2.selectbox("Ordem",["Decrescente","Crescente"])
        page_size=c3.selectbox("Linhas por página",[25,50,100,250],index=1)
        report=report.sort_values(sort_label,ascending=direction=="Crescente",na_position="last")
        pages=max(1,int(np.ceil(len(report)/page_size)))
        current=st.number_input("Página",1,pages,1)
        start=(current-1)*page_size
        report_display=report.iloc[start:start+page_size].copy()
        for col in report_display.select_dtypes(include=np.number):
            report_display[col]=report_display[col].map(lambda value:fmt(value,"%" if "%" in col else "n"))
        st.dataframe(report_display,use_container_width=True,hide_index=True)
        st.caption(f"Exibindo {start+1:,}–{min(start+page_size,len(report)):,} de {len(report):,} registros".replace(",","."))
        st.download_button("Baixar tabela em CSV",report.to_csv(index=False).encode("utf-8-sig"),f"relatorio_censo_{selected_year}.csv","text/csv",help="CSV é um formato de tabela que pode ser aberto no Excel, Google Planilhas e outros programas.")

elif page=="Qualidade dos dados":
    heading("Caderno técnico","Qualidade antes da conclusão","Completude, correspondência, duplicidade e consistência para tornar visível o limite da evidência.")
    if "tabela" in audit.columns:
        audit_display=friendly_table(audit,{"tabela":"Base analisada","registros":"Registros","chaves_unicas_no_grao":"Registros únicos",
          "chaves_nulas":"Identificadores ausentes","duplicidades_chave":"Identificadores repetidos","valores_quantitativos_negativos":"Valores negativos",
          "escolas_ativas_com_correspondencia":"Escolas ativas encontradas","pct_correspondencia_ativas":"Correspondência com escolas ativas (%)",
          "chaves_sem_dimensao_escola":"Registros sem escola correspondente"},
          ["registros","chaves_unicas_no_grao","chaves_nulas","duplicidades_chave","valores_quantitativos_negativos","escolas_ativas_com_correspondencia","chaves_sem_dimensao_escola"],["pct_correspondencia_ativas"])
    else:
        audit_display=friendly_table(audit,{"ANO":"Ano","REGISTROS":"Registros","ESCOLAS":"Escolas","MUNICIPIOS":"Municípios","CAMPOS_HARMONIZADOS":"Campos comparáveis",
          "VALORES_NULOS":"Valores ausentes","CHAVES_DUPLICADAS":"Identificadores repetidos","CAMPOS_COMPATIVEIS":"Campos compatíveis",
          "CAMPOS_PARCIAIS":"Campos parcialmente compatíveis","INDICE_COMPATIBILIDADE":"Compatibilidade (%)","NOTA":"Observação"},
          ["ANO","REGISTROS","ESCOLAS","MUNICIPIOS","CAMPOS_HARMONIZADOS","VALORES_NULOS","CHAVES_DUPLICADAS","CAMPOS_COMPATIVEIS","CAMPOS_PARCIAIS"],["INDICE_COMPATIBILIDADE"])
    st.dataframe(audit_display,use_container_width=True,hide_index=True)
    cards([("Diferenças no teste sexo",active.DIF_SEXO.fillna(0).ne(0).sum(),"n"),("Diferenças no teste raça",active.DIF_RACA.fillna(0).ne(0).sum(),"n"),
           ("Outliers de pressão",active.PRESSAO_OUTLIER.sum(),"n"),("Escolas sem matrícula",(~active.TEM_MATRICULA).sum(),"n")])
    st.warning("Zero significa ausência informada. Campo vazio significa dado não disponível ou não aplicável. O sistema preserva essa diferença e não transforma campos vazios em zero.")

else:
    heading("Síntese editorial","O que merece atenção","Fatos observados separados de hipóteses e possíveis caminhos de investigação.")
    g=grouped(active,"SG_UF"); rural=active[active.LOCALIZACAO.eq("Rural")]; urban=active[active.LOCALIZACAO.eq("Urbana")]
    insights=[
      ("Prioridade",g.loc[g.IPI.idxmax(),"SG_UF"],g.IPI.max(),"combinação de carências, pressão e volume; investigar componentes antes de decidir"),
      ("Maturidade digital",g.loc[g.IMDE.idxmin(),"SG_UF"],g.IMDE.min(),"menor Índice de Maturidade Digital Escolar, considerando o tamanho das escolas; priorizar diagnóstico de conexão e equipamentos"),
      ("Acessibilidade",g.loc[g.INDICE_ACESSIBILIDADE.idxmin(),"SG_UF"],g.INDICE_ACESSIBILIDADE.min(),"menor cobertura observada; validar registros nulos e barreiras físicas"),
      ("Gap territorial de banda larga","Rural × urbana",100*(rural.IN_BANDA_LARGA.mean()-urban.IN_BANDA_LARGA.mean()),"diferença em pontos percentuais; hipótese: infraestrutura territorial, sem inferência causal"),
      ("Pressão operacional","Brasil",100*active.PRESSAO_OUTLIER.mean(),"percentual de escolas com valores muito distantes do padrão observado; requer investigação local")]
    for title,where,value,note in insights:
        st.subheader(title); st.write(f"**Fato:** {where}: {fmt(value,'d')}.  **Hipótese/decisão:** {note}.")
    st.caption("Análise transversal de 2025: associação não implica causalidade; docentes/gestores podem representar vínculos, não pessoas únicas; não há desempenho escolar nem série temporal.")
