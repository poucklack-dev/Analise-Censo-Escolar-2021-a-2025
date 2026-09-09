"""Aplicação web local do Censo Escolar 2025 — Flask + frontend próprio."""
from io import BytesIO
from pathlib import Path
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file, Response
from plotly.offline import get_plotlyjs

ROOT=Path(__file__).resolve().parent
app=Flask(__name__,template_folder="templates",static_folder="static")
DF=pd.read_parquet(ROOT/"output/escola_analytics.parquet")
COURSE=pd.read_parquet(ROOT/"output/f_curso_tecnico.parquet")
AUDIT=pd.read_csv(ROOT/"output/auditoria.csv").replace({np.nan:None})
DF["MUNICIPIO_UF"]=(DF.NO_MUNICIPIO.astype("string").str.strip()+" — "+DF.SG_UF.astype("string").str.strip()).where(DF.NO_MUNICIPIO.notna() & DF.SG_UF.notna())
DF["ESCOLA_ROTULO"]=DF.NO_ENTIDADE.fillna("Sem nome")+" — "+DF.CO_ENTIDADE.astype("Int64").astype(str)

INVALID_LABELS={"", "nan", "none", "null", "na", "n/a", "ni", "não informado"}
def valid_label_mask(s):
    text=s.astype("string").str.strip()
    return s.notna() & ~text.str.casefold().isin(INVALID_LABELS)
def valid_values(s):
    return sorted(s.loc[valid_label_mask(s)].astype(str).unique().tolist())

def clean(v): return None if pd.isna(v) or np.isinf(v) else round(float(v),3)
def total(s): return s.sum(min_count=1)
def ratio(a,b,mult=1): return clean(mult*a/b) if b else None
def weighted(d,col):
    x=d[[col,"QT_MAT_BAS"]].dropna()
    return clean(np.average(x[col],weights=x.QT_MAT_BAS)) if len(x) and x.QT_MAT_BAS.sum() else None
def args(): return {k:request.args.get(k,"").strip() for k in ["region","uf","municipio","dep","loc","status","q"]}
def filtered(params=None):
    p=params or args(); d=DF
    maps={"region":"NO_REGIAO","uf":"SG_UF","municipio":"MUNICIPIO_UF","dep":"DEPENDENCIA","loc":"LOCALIZACAO","status":"SITUACAO"}
    for key,col in maps.items():
        if p.get(key): d=d[d[col].eq(p[key])]
    if p.get("q"):
        q=p["q"].casefold(); d=d[d.ESCOLA_ROTULO.str.casefold().str.contains(q,na=False)|d.MUNICIPIO_UF.str.casefold().str.contains(q,na=False)]
    return d
def grouped(d,key):
    d=d.loc[valid_label_mask(d[key])]
    rows=[]
    for name,g in d.groupby(key):
        mat=total(g.QT_MAT_BAS); doc=total(g.QT_DOC_BAS); tur=total(g.QT_TUR_BAS)
        rows.append({"label":str(name),"matriculas":clean(mat),"escolas":int(g.CO_ENTIDADE.nunique()),
          "docentes":clean(doc),"turmas":clean(tur),"alunos_docente":ratio(mat,doc),"alunos_turma":ratio(mat,tur),
          "imde":weighted(g,"IMDE"),"acessibilidade":weighted(g,"INDICE_ACESSIBILIDADE"),"ipi":weighted(g,"IPI"),
          "diversidade":weighted(g,"DIVERSIDADE_RACIAL"),"tempo_integral":ratio(total(g.QT_MAT_BAS_INT),mat,100),
          "dispositivos":ratio(total(g.DISPOSITIVOS),mat,100),"formacao":ratio(total(g.QT_DOC_BAS_ESCO_SUP_GRAD),doc,100)})
    return rows

@app.get("/")
def index(): return render_template("index.html")
@app.get("/vendor/plotly.js")
def plotly_js(): return Response(get_plotlyjs(),mimetype="application/javascript")

@app.get("/api/options")
def options():
    p=args(); d=DF
    if p["region"]: d=d[d.NO_REGIAO.eq(p["region"])]
    if p["uf"]: d=d[d.SG_UF.eq(p["uf"])]
    if p["dep"]: d=d[d.DEPENDENCIA.eq(p["dep"])]
    if p["loc"]: d=d[d.LOCALIZACAO.eq(p["loc"])]
    return jsonify({"regions":valid_values(DF.NO_REGIAO),"ufs":valid_values(d.SG_UF),
      "municipios":valid_values(d.MUNICIPIO_UF),"deps":valid_values(DF.DEPENDENCIA),
      "locs":valid_values(DF.LOCALIZACAO),"statuses":valid_values(DF.SITUACAO)})

@app.get("/api/dashboard")
def dashboard():
    p=args(); d=filtered(p); mat=total(d.QT_MAT_BAS); doc=total(d.QT_DOC_BAS); tur=total(d.QT_TUR_BAS)
    ids=set(d.CO_ENTIDADE); c=COURSE[COURSE.CO_ENTIDADE.isin(ids)]
    race={"Branca":total(d.QT_MAT_BAS_BRANCA),"Preta":total(d.QT_MAT_BAS_PRETA),"Parda":total(d.QT_MAT_BAS_PARDA),"Amarela":total(d.QT_MAT_BAS_AMARELA),"Indígena":total(d.QT_MAT_BAS_INDIGENA)}
    sex={"Feminino":total(d.QT_MAT_BAS_FEM),"Masculino":total(d.QT_MAT_BAS_MASC),"Não declarado":total(d.QT_MAT_BAS_ND)}
    priority=d.nlargest(30,"IPI")[["ESCOLA_ROTULO","MUNICIPIO_UF","QT_MAT_BAS","IMDE","INDICE_ACESSIBILIDADE","ALUNOS_DOCENTE","IPI"]]
    topc=c.groupby("NO_CURSO_EDUC_PROFISSIONAL",as_index=False).QT_MAT_CURSO_TEC.sum().nlargest(15,"QT_MAT_CURSO_TEC") if len(c) else pd.DataFrame(columns=["NO_CURSO_EDUC_PROFISSIONAL","QT_MAT_CURSO_TEC"])
    return jsonify({"count":len(d),"kpis":{"matriculas":clean(mat),"escolas":int(d.CO_ENTIDADE.nunique()),"docentes":clean(doc),"turmas":clean(tur),
      "alunos_docente":ratio(mat,doc),"alunos_turma":ratio(mat,tur),"integral":ratio(total(d.QT_MAT_BAS_INT),mat,100),"banda":clean(100*d.IN_BANDA_LARGA.mean()),
      "imde":weighted(d,"IMDE"),"acessibilidade":weighted(d,"INDICE_ACESSIBILIDADE"),"dispositivos":ratio(total(d.DISPOSITIVOS),mat,100),"ipi":weighted(d,"IPI"),
      "doc_superior":ratio(total(d.QT_DOC_BAS_ESCO_SUP_GRAD),doc,100),"licenciatura":ratio(total(d.QT_DOC_BAS_ESCO_SUP_GRAD_LICEN),doc,100),"concursados":ratio(total(d.QT_DOC_BAS_VINCULO_CONCUR),doc,100),"gestores":clean(total(d.QT_GEST_BAS)),
      "mat_tec":clean(total(c.QT_MAT_CURSO_TEC)),"ofertantes":int(c.CO_ENTIDADE.nunique()),"cursos":int(c.CO_CURSO_EDUC_PROFISSIONAL.nunique())},
      "regions":grouped(d,"NO_REGIAO"),"dependencies":grouped(d,"DEPENDENCIA"),"ufs":grouped(d,"SG_UF"),"municipios":grouped(d,"MUNICIPIO_UF") if p.get("uf") or p.get("municipio") else [],
      "sex":{k:clean(v) for k,v in sex.items()},"race":{k:clean(v) for k,v in race.items()},
      "courses":[{"label":r.NO_CURSO_EDUC_PROFISSIONAL,"value":clean(r.QT_MAT_CURSO_TEC)} for r in topc.itertuples()],
      "priority":[{"escola":r.ESCOLA_ROTULO,"municipio":r.MUNICIPIO_UF,"matriculas":clean(r.QT_MAT_BAS),"imde":clean(r.IMDE),"acessibilidade":clean(r.INDICE_ACESSIBILIDADE),"alunos_docente":clean(r.ALUNOS_DOCENTE),"ipi":clean(r.IPI)} for r in priority.itertuples()],
      "quality":AUDIT.to_dict("records")})

@app.get("/api/report")
def report():
    d=filtered(); cols=["ESCOLA_ROTULO","MUNICIPIO_UF","NO_REGIAO","DEPENDENCIA","LOCALIZACAO","SITUACAO","QT_MAT_BAS","QT_DOC_BAS","QT_TUR_BAS","ALUNOS_DOCENTE","ALUNOS_TURMA","IMDE","INDICE_ACESSIBILIDADE","IPI"]
    page=max(1,request.args.get("page",1,type=int)); size=min(250,max(10,request.args.get("size",50,type=int))); start=(page-1)*size
    return jsonify({"total":len(d),"page":page,"size":size,"rows":d[cols].iloc[start:start+size].replace({np.nan:None}).to_dict("records")})
@app.get("/api/priority")
def priority_report():
    d=filtered(); metric=request.args.get("metric","IPI"); order=request.args.get("order","desc")
    allowed={"IPI":"IPI","IMDE":"IMDE","INDICE_ACESSIBILIDADE":"INDICE_ACESSIBILIDADE","ALUNOS_DOCENTE":"ALUNOS_DOCENTE","QT_MAT_BAS":"QT_MAT_BAS"}
    metric=allowed.get(metric,"IPI"); page=max(1,request.args.get("page",1,type=int)); size=min(100,max(10,request.args.get("size",20,type=int)))
    d=d.sort_values(metric,ascending=order=="asc",na_position="last"); start=(page-1)*size
    cols=["ESCOLA_ROTULO","MUNICIPIO_UF","QT_MAT_BAS","ALUNOS_DOCENTE","IMDE","INDICE_ACESSIBILIDADE","IPI"]
    return jsonify({"total":len(d),"page":page,"size":size,"metric":metric,
      "rows":d[cols].iloc[start:start+size].replace({np.nan:None}).to_dict("records")})
@app.get("/api/advanced")
def advanced():
    d=filtered(); rows=[]
    for name,g in d.loc[valid_label_mask(d.SG_UF)].groupby("SG_UF"):
        row={"label":str(name)}
        for col in ["SEM_AGUA_POTAVEL","SEM_ESGOTO_ADEQUADO","SEM_ENERGIA","SEM_COLETA_LIXO","TRES_MAIS_CARENCIAS"]:
            row[col]=clean(100*g[col].mean())
        row["especial"]=clean(total(g.QT_MAT_ESP)); row["especial_pct"]=ratio(total(g.QT_MAT_ESP),total(g.QT_MAT_BAS),100); row["inclusao"]=weighted(g,"ESTRUTURA_INCLUSAO")
        row["ambiental"]=weighted(g,"INDICE_PRATICAS_AMBIENTAIS"); row["transporte"]=ratio(total(g.QT_TRANSP_PUBLICO),total(g.QT_MAT_BAS),100)
        row["alunos_docente"]=ratio(total(g.QT_MAT_BAS),total(g.QT_DOC_BAS)); row["alunos_turma"]=ratio(total(g.QT_MAT_BAS),total(g.QT_TUR_BAS)); row["matriculas_sala"]=ratio(total(g.QT_MAT_BAS),total(g.QT_SALAS_UTILIZADAS)); row["matriculas"]=clean(total(g.QT_MAT_BAS))
        rows.append(row)
    gaps=[]
    for name,g in d.loc[valid_label_mask(d.SG_UF)].groupby("SG_UF"):
        u=g[g.LOCALIZACAO.eq("Urbana")]; r=g[g.LOCALIZACAO.eq("Rural")]
        if u.empty or r.empty: continue
        def mean_gap(col): return clean(100*(r[col].mean()-u[col].mean()))
        gaps.append({"label":str(name),"Banda larga":mean_gap("IN_BANDA_LARGA"),"Internet alunos":mean_gap("IN_INTERNET_ALUNOS"),
          "Acessibilidade":clean(weighted(r,"INDICE_ACESSIBILIDADE")-weighted(u,"INDICE_ACESSIBILIDADE")) if weighted(r,"INDICE_ACESSIBILIDADE") is not None and weighted(u,"INDICE_ACESSIBILIDADE") is not None else None,
          "Água potável":mean_gap("IN_AGUA_POTAVEL"),"Esgoto adequado":clean(100*((1-r.SEM_ESGOTO_ADEQUADO).mean()-(1-u.SEM_ESGOTO_ADEQUADO).mean())),
          "Dispositivos":clean(r.DISPOSITIVOS_100_ALUNOS.mean()-u.DISPOSITIVOS_100_ALUNOS.mean()),"Tempo integral":clean(r.PCT_TEMPO_INTEGRAL.mean()-u.PCT_TEMPO_INTEGRAL.mean()),
          "Formação docente":clean(r.TAXA_DOC_SUPERIOR.mean()-u.TAXA_DOC_SUPERIOR.mean())})
    stages=[]
    for name,g in d.groupby("DEPENDENCIA",dropna=False):
        vals={"Creche":total(g.QT_MAT_INF_CRE),"Pré-escola":total(g.QT_MAT_INF_PRE),"Fundamental iniciais":total(g.QT_MAT_FUND_AI),"Fundamental finais":total(g.QT_MAT_FUND_AF),"Ensino médio":total(g.QT_MAT_MED),"EJA":total(g.QT_MAT_EJA),"Profissional":total(g.QT_MAT_PROF)}
        den=sum(v for v in vals.values() if pd.notna(v))
        stages.append({"label":str(name),**{k:clean(100*v/den) if den and pd.notna(v) else None for k,v in vals.items()}})
    disciplines=[]
    names={"LINGUA_PORT":"Português","MATEMATICA":"Matemática","FISICA":"Física","QUIMICA":"Química","HISTORIA":"História","GEOGRAFIA":"Geografia","CIENCIAS":"Ciências","INFO_COMPUTACAO":"Computação"}
    for suf,label in names.items(): disciplines.append({"label":label,"value":ratio(total(d[f"QT_TUR_BAS_DISC_{suf}"]),total(d[f"QT_DOC_BAS_DISC_{suf}"]))})
    governance=[]
    for name,g in d.groupby("DEPENDENCIA",dropna=False): governance.append({"label":str(name),"Conselho escolar":clean(100*g.IN_ORGAO_CONSELHO_ESCOLAR.mean()),"Grêmio estudantil":clean(100*g.IN_ORGAO_GREMIO_ESTUDANTIL.mean()),"Associação de pais":clean(100*g.IN_ORGAO_ASS_PAIS.mean()),"Associação pais e mestres":clean(100*g.IN_ORGAO_ASS_PAIS_MESTRES.mean())})
    doc={"Licenciatura":ratio(total(d.QT_DOC_BAS_ESCO_SUP_GRAD_LICEN),total(d.QT_DOC_BAS),100),"Especialização":ratio(total(d.QT_DOC_BAS_ESCO_SUP_POS_ESPEC),total(d.QT_DOC_BAS),100),"Mestrado":ratio(total(d.QT_DOC_BAS_ESCO_SUP_POS_MESTRA),total(d.QT_DOC_BAS),100),"Doutorado":ratio(total(d.QT_DOC_BAS_ESCO_SUP_POS_DOUTO),total(d.QT_DOC_BAS),100),"Concursado":ratio(total(d.QT_DOC_BAS_VINCULO_CONCUR),total(d.QT_DOC_BAS),100),"Contratado":ratio(total(d.QT_DOC_BAS_VINCULO_CONTRA),total(d.QT_DOC_BAS),100),"Terceirizado":ratio(total(d.QT_DOC_BAS_VINCULO_TERCEIR),total(d.QT_DOC_BAS),100),"CLT":ratio(total(d.QT_DOC_BAS_VINCULO_CLT),total(d.QT_DOC_BAS),100)}
    ids=set(d.CO_ENTIDADE); tc=COURSE[COURSE.CO_ENTIDADE.isin(ids)]
    hhi=[]
    for name,g in tc.loc[valid_label_mask(tc.SG_UF)].groupby("SG_UF"):
        s=g.groupby("CO_CURSO_EDUC_PROFISSIONAL").QT_MAT_CURSO_TEC.sum(min_count=1); den=s.sum(min_count=1)
        hhi.append({"label":str(name),"value":clean(((s/den)**2).sum()*10000) if den else None})
    mode_cols={"Integrada":"QT_MAT_CURSO_TEC_IFTP_CT","Concomitante":"QT_MAT_CURSO_TEC_CONC","Subsequente":"QT_MAT_CURSO_TEC_SUBS","EJA":"QT_MAT_CURSO_TEC_EJA"}
    modes=[{"label":k,"value":clean(total(tc[v]))} for k,v in mode_cols.items()]
    profiles=[]
    try:
        cols=["IMDE","INDICE_ACESSIBILIDADE","ALUNOS_DOCENTE","ALUNOS_TURMA","DISPOSITIVOS_100_ALUNOS","QT_CARENCIAS_ESSENCIAIS"]
        z=d[["CO_ENTIDADE"]+cols].dropna()
        if len(z)>=20:
            if len(z)>10000: z=z.sample(10000,random_state=42)
            values=z[cols].to_numpy(float); values=(values-values.mean(0))/values.std(0).clip(min=1e-9)
            rng=np.random.default_rng(42); centers=values[rng.choice(len(values),4,replace=False)]
            for _ in range(25):
                labels=((values[:,None,:]-centers[None,:,:])**2).sum(2).argmin(1)
                updated=np.array([values[labels==i].mean(0) if np.any(labels==i) else centers[i] for i in range(4)])
                if np.allclose(updated,centers,atol=1e-4): break
                centers=updated
            z=z.copy(); z["cluster"]=labels
            for n,g in z.groupby("cluster"):
                profiles.append({"label":f"Perfil {int(n)+1}","escolas":len(g),"imde":clean(g.IMDE.mean()),"acessibilidade":clean(g.INDICE_ACESSIBILIDADE.mean()),"pressao":clean(g.ALUNOS_DOCENTE.mean()),"carencias":clean(g.QT_CARENCIAS_ESSENCIAIS.mean())})
    except Exception: pass
    return jsonify({"essentials":rows,"gaps":gaps,"stages":stages,"disciplines":disciplines,"governance":governance,"doc_profile":doc,"tech_hhi":hhi,"tech_modes":modes,"profiles":profiles})
@app.get("/api/export")
def export():
    d=filtered(); cols=["CO_ENTIDADE","NO_ENTIDADE","NO_MUNICIPIO","SG_UF","NO_REGIAO","DEPENDENCIA","LOCALIZACAO","SITUACAO","QT_MAT_BAS","QT_DOC_BAS","QT_TUR_BAS","IMDE","INDICE_ACESSIBILIDADE","IPI"]
    b=BytesIO(); b.write(d[cols].to_csv(index=False).encode("utf-8-sig")); b.seek(0)
    return send_file(b,mimetype="text/csv",as_attachment=True,download_name="censo_escolar_2025.csv")

if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=False)
