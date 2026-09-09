"""ETL e camada analítica do Censo Escolar 2025 (Python puro)."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
YEAR = 2025
DATA = ROOT / "dados" / str(YEAR)
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
ENC = "cp1252"
ID = "CO_ENTIDADE"

FILES = {
    "escola": "Tabela_Escola_2025_V2.csv",
    "matricula": "Tabela_Matricula_2025_V2.csv",
    "docente": "Tabela_Docente_2025_V2.csv",
    "turma": "Tabela_Turma_2025_V2.csv",
    "gestor": "Tabela_Gestor_Escolar_2025_v2.csv",
    "curso": "Tabela_Curso_Tecnico_2025_V2.csv",
}

GEO = ["NU_ANO_CENSO", "NO_REGIAO", "CO_REGIAO", "NO_UF", "SG_UF", "CO_UF",
       "NO_MUNICIPIO", "CO_MUNICIPIO", "NO_ENTIDADE", ID, "TP_DEPENDENCIA", "TP_LOCALIZACAO"]
MAT = ["QT_MAT_BAS", "QT_MAT_BAS_FEM", "QT_MAT_BAS_MASC", "QT_MAT_BAS_ND",
       "QT_MAT_BAS_BRANCA", "QT_MAT_BAS_PRETA", "QT_MAT_BAS_PARDA", "QT_MAT_BAS_AMARELA",
       "QT_MAT_BAS_INDIGENA", "QT_MAT_BAS_0_3", "QT_MAT_BAS_4_5", "QT_MAT_BAS_6_10",
       "QT_MAT_BAS_11_14", "QT_MAT_BAS_15_17", "QT_MAT_BAS_18_MAIS", "QT_MAT_BAS_INT",
       "QT_MAT_EJA", "QT_MAT_ESP", "QT_MAT_PROF", "QT_MAT_PROF_TEC", "QT_TRANSP_PUBLICO",
       "QT_MAT_INF_CRE", "QT_MAT_INF_PRE", "QT_MAT_FUND_AI", "QT_MAT_FUND_AF", "QT_MAT_MED",
       "QT_MAT_EJA_FUND", "QT_MAT_EJA_MED"]
DOC = ["QT_DOC_BAS", "QT_DOC_BAS_FEM", "QT_DOC_BAS_MASC", "QT_DOC_BAS_ND",
       "QT_DOC_BAS_BRANCA", "QT_DOC_BAS_PRETA", "QT_DOC_BAS_PARDA", "QT_DOC_BAS_AMARELA",
       "QT_DOC_BAS_INDIGENA", "QT_DOC_BAS_PCD", "QT_DOC_BAS_ESCO_SUP_GRAD",
       "QT_DOC_BAS_ESCO_SUP_GRAD_LICEN", "QT_DOC_BAS_ESCO_SUP_POS_ESPEC",
       "QT_DOC_BAS_ESCO_SUP_POS_MESTRA", "QT_DOC_BAS_ESCO_SUP_POS_DOUTO",
       "QT_DOC_BAS_VINCULO_CONCUR", "QT_DOC_BAS_VINCULO_CONTRA", "QT_DOC_BAS_VINCULO_TERCEIR",
       "QT_DOC_BAS_VINCULO_CLT", "QT_DOC_BAS_0_24", "QT_DOC_BAS_25_29", "QT_DOC_BAS_30_39",
       "QT_DOC_BAS_40_49", "QT_DOC_BAS_50_54", "QT_DOC_BAS_55_59", "QT_DOC_BAS_60_MAIS",
       "QT_DOC_BAS_TRADUTOR_LIBRAS", "QT_DOC_BAS_DISC_LINGUA_PORT", "QT_DOC_BAS_DISC_MATEMATICA",
       "QT_DOC_BAS_DISC_FISICA", "QT_DOC_BAS_DISC_QUIMICA", "QT_DOC_BAS_DISC_HISTORIA",
       "QT_DOC_BAS_DISC_GEOGRAFIA", "QT_DOC_BAS_DISC_CIENCIAS", "QT_DOC_BAS_DISC_INFO_COMPUTACAO"]
TUR = ["QT_TUR_BAS", "QT_TUR_BAS_DISC_LINGUA_PORT", "QT_TUR_BAS_DISC_MATEMATICA",
       "QT_TUR_BAS_DISC_FISICA", "QT_TUR_BAS_DISC_QUIMICA", "QT_TUR_BAS_DISC_HISTORIA",
       "QT_TUR_BAS_DISC_GEOGRAFIA", "QT_TUR_BAS_DISC_CIENCIAS", "QT_TUR_BAS_DISC_INFO_COMPUTACAO"]
GES = ["QT_GEST_BAS", "QT_GEST_BAS_FEM", "QT_GEST_BAS_MASC", "QT_GEST_BAS_ND",
       "QT_GEST_BAS_BRANCA", "QT_GEST_BAS_PRETA", "QT_GEST_BAS_PARDA", "QT_GEST_BAS_AMARELA",
       "QT_GEST_BAS_INDIGENA", "QT_GEST_BAS_ESCO_SUP_GRAD", "QT_GEST_BAS_ESCO_SUP_POS_ESPEC",
       "QT_GEST_BAS_ESCO_SUP_POS_MESTRA", "QT_GEST_BAS_ESCO_SUP_POS_DOUTO",
       "QT_GEST_BAS_VINCULO_CONCUR", "QT_GEST_BAS_VINCULO_CONTRA", "QT_GEST_BAS_VINCULO_TERCEIR",
       "QT_GEST_BAS_VINCULO_CLT", "QT_GEST_BAS_ACESSO_CARGO_PROP", "QT_GEST_BAS_ACESSO_CARGO_INDIC",
       "QT_GEST_BAS_ACESSO_CARGO_SEL", "QT_GEST_BAS_ACESSO_CARGO_CONC",
       "QT_GEST_BAS_ACESSO_CARGO_ELEIC", "QT_GEST_BAS_ACESSO_CARGO_P_SEL",
       "QT_GEST_BAS_ACESSO_CARGO_OUTRO"]
ESC = ["TP_SITUACAO_FUNCIONAMENTO", "IN_INTERNET", "IN_BANDA_LARGA", "IN_INTERNET_ALUNOS",
       "IN_INTERNET_APRENDIZAGEM", "IN_LABORATORIO_INFORMATICA", "QT_DESKTOP_ALUNO",
       "QT_COMP_PORTATIL_ALUNO", "QT_TABLET_ALUNO", "QT_SALAS_UTILIZADAS",
       "QT_SALAS_UTILIZA_CLIMATIZADAS", "QT_SALAS_UTILIZADAS_ACESSIVEIS", "IN_BIBLIOTECA",
       "IN_BIBLIOTECA_SALA_LEITURA", "IN_LABORATORIO_CIENCIAS", "IN_QUADRA_ESPORTES",
       "IN_REFEITORIO", "IN_ACESSIBILIDADE_CORRIMAO", "IN_ACESSIBILIDADE_ELEVADOR",
       "IN_ACESSIBILIDADE_PISOS_TATEIS", "IN_ACESSIBILIDADE_VAO_LIVRE",
       "IN_ACESSIBILIDADE_RAMPAS", "IN_ACESSIBILIDADE_SINAL_SONORO",
       "IN_ACESSIBILIDADE_SINAL_TATIL", "IN_ACESSIBILIDADE_SINAL_VISUAL", "IN_AGUA_POTAVEL",
       "IN_AGUA_REDE_PUBLICA", "IN_AGUA_INEXISTENTE", "IN_ENERGIA_REDE_PUBLICA",
       "IN_ENERGIA_RENOVAVEL", "IN_ENERGIA_INEXISTENTE", "IN_ESGOTO_REDE_PUBLICA",
       "IN_ESGOTO_FOSSA_SEPTICA", "IN_ESGOTO_INEXISTENTE", "IN_LIXO_SERVICO_COLETA",
       "IN_LIXO_QUEIMA", "IN_TRATAMENTO_LIXO_SEPARACAO", "IN_TRATAMENTO_LIXO_REUTILIZA",
       "IN_TRATAMENTO_LIXO_RECICLAGEM", "IN_BANHEIRO", "IN_COZINHA", "IN_AREA_VERDE",
       "IN_AREA_PLANTIO", "IN_EDUC_AMBIENTAL", "IN_SALA_ATENDIMENTO_ESPECIAL",
       "QT_PROF_TRAD_LIBRAS", "QT_PROF_REVISOR_BRAILLE", "QT_PROF_MONITORES",
       "IN_ORGAO_CONSELHO_ESCOLAR", "IN_ORGAO_GREMIO_ESTUDANTIL", "IN_ORGAO_ASS_PAIS",
       "IN_ORGAO_ASS_PAIS_MESTRES"]
COURSE = ["NO_AREA_CURSO_PROFISSIONAL", "ID_AREA_CURSO_PROFISSIONAL", "NO_CURSO_EDUC_PROFISSIONAL",
          "CO_CURSO_EDUC_PROFISSIONAL", "QT_CURSO_TEC", "QT_MAT_CURSO_TEC",
          "QT_MAT_CURSO_TEC_IFTP_CT", "QT_MAT_CURSO_TEC_CONC", "QT_MAT_CURSO_TEC_SUBS", "QT_MAT_CURSO_TEC_EJA"]

def read(name, cols):
    available = pd.read_csv(DATA / FILES[name], sep=";", encoding=ENC, nrows=0).columns
    use = list(dict.fromkeys([c for c in cols if c in available]))
    return pd.read_csv(DATA / FILES[name], sep=";", encoding=ENC, usecols=use, low_memory=False)

def ratio(a, b):
    return a.div(b.where(b.ne(0)))

def weighted_score(frame, specs):
    values, weights = [], []
    for col, weight in specs.items():
        values.append(frame[col].astype(float) * weight)
        weights.append(frame[col].notna().astype(float) * weight)
    den = sum(weights)
    return sum(values).div(den.where(den.ne(0))) * 100

def winsor01(s):
    valid = s.dropna()
    if valid.empty or valid.nunique() == 1:
        return pd.Series(np.nan, index=s.index)
    lo, hi = valid.quantile([.05, .95])
    x = s.clip(lo, hi)
    return (x - lo) / (hi - lo) if hi > lo else pd.Series(0.0, index=s.index)

def audit_file(name):
    rows = duplicates = null_keys = negatives = 0
    keys = set()
    quantitative = None
    for chunk in pd.read_csv(DATA / FILES[name], sep=";", encoding=ENC, chunksize=20000, low_memory=False):
        rows += len(chunk)
        null_keys += int(chunk[ID].isna().sum())
        if name == "curso":
            valid = chunk[[ID, "CO_CURSO_EDUC_PROFISSIONAL"]].dropna().astype(str).agg("|".join, axis=1)
            school_keys = chunk[ID].dropna()
        else:
            valid = chunk[ID].dropna().astype(str)
            school_keys = chunk[ID].dropna()
        duplicates += int(valid.isin(keys).sum() + valid.duplicated().sum())
        keys.update(valid.unique().tolist())
        if quantitative is None:
            quantitative = [c for c in chunk if c.startswith("QT_")]
        negatives += int((chunk[quantitative].apply(pd.to_numeric, errors="coerce") < 0).sum().sum())
    return {"tabela": name, "registros": rows, "chaves_unicas_no_grao": len(keys), "chaves_nulas": null_keys,
            "duplicidades_chave": duplicates, "valores_quantitativos_negativos": negatives}

def main():
    escola = read("escola", GEO + ESC)
    mat = read("matricula", [ID] + MAT)
    doc = read("docente", [ID] + DOC)
    tur = read("turma", [ID] + TUR)
    ges = read("gestor", [ID] + GES)
    curso = read("curso", GEO + COURSE)

    dep = {1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}
    loc = {1: "Urbana", 2: "Rural"}
    sit = {1: "Em atividade", 2: "Paralisada", 3: "Extinta", 4: "Extinta em anos anteriores"}
    escola["DEPENDENCIA"] = escola.TP_DEPENDENCIA.map(dep).fillna("Não informado")
    escola["LOCALIZACAO"] = escola.TP_LOCALIZACAO.map(loc).fillna("Não informado")
    escola["SITUACAO"] = escola.TP_SITUACAO_FUNCIONAMENTO.map(sit).fillna("Não informado")

    facts = {"matricula": mat, "docente": doc, "turma": tur, "gestor": ges}
    base = escola.copy()
    for name, fact in facts.items():
        fact = fact.drop_duplicates(ID)
        fact[f"TEM_{name.upper()}"] = True
        base = base.merge(fact, on=ID, how="left", validate="one_to_one")
    for name in facts:
        base[f"TEM_{name.upper()}"] = base[f"TEM_{name.upper()}"].fillna(False)

    base["DISPOSITIVOS"] = base[["QT_DESKTOP_ALUNO", "QT_COMP_PORTATIL_ALUNO", "QT_TABLET_ALUNO"]].sum(axis=1, min_count=1)
    base["DISPOSITIVOS_100_ALUNOS"] = ratio(base.DISPOSITIVOS * 100, base.QT_MAT_BAS)
    base["ALUNOS_DOCENTE"] = ratio(base.QT_MAT_BAS, base.QT_DOC_BAS)
    base["ALUNOS_TURMA"] = ratio(base.QT_MAT_BAS, base.QT_TUR_BAS)
    base["ALUNOS_ESCOLA"] = base.QT_MAT_BAS
    base["MATRICULAS_SALA"] = ratio(base.QT_MAT_BAS, base.QT_SALAS_UTILIZADAS)
    base["PCT_TEMPO_INTEGRAL"] = ratio(base.QT_MAT_BAS_INT * 100, base.QT_MAT_BAS)
    base["PCT_EJA"] = ratio(base.QT_MAT_EJA * 100, base.QT_MAT_BAS)
    base["PCT_ED_ESPECIAL"] = ratio(base.QT_MAT_ESP * 100, base.QT_MAT_BAS)
    base["PCT_ED_PROFISSIONAL"] = ratio(base.QT_MAT_PROF * 100, base.QT_MAT_BAS)
    base["PCT_FEMININA"] = ratio(base.QT_MAT_BAS_FEM * 100, base.QT_MAT_BAS_FEM + base.QT_MAT_BAS_MASC)
    base["GAP_GENERO_PP"] = (ratio(base.QT_MAT_BAS_FEM, base.QT_MAT_BAS_FEM + base.QT_MAT_BAS_MASC) - .5).abs() * 200
    race_cols = ["QT_MAT_BAS_BRANCA", "QT_MAT_BAS_PRETA", "QT_MAT_BAS_PARDA", "QT_MAT_BAS_AMARELA", "QT_MAT_BAS_INDIGENA"]
    race_total = base[race_cols].sum(axis=1, min_count=1)
    base["DIVERSIDADE_RACIAL"] = (1 - base[race_cols].div(race_total, axis=0).pow(2).sum(axis=1)) * 100
    base["TAXA_DOC_SUPERIOR"] = ratio(base.QT_DOC_BAS_ESCO_SUP_GRAD * 100, base.QT_DOC_BAS)
    base["TAXA_LICENCIATURA"] = ratio(base.QT_DOC_BAS_ESCO_SUP_GRAD_LICEN * 100, base.QT_DOC_BAS)
    base["PCT_DOC_CONCURSADO"] = ratio(base.QT_DOC_BAS_VINCULO_CONCUR * 100, base.QT_DOC_BAS)
    base["TAXA_GEST_SUPERIOR"] = ratio(base.QT_GEST_BAS_ESCO_SUP_GRAD * 100, base.QT_GEST_BAS)
    base["PCT_TRANSPORTE_PUBLICO"] = ratio(base.QT_TRANSP_PUBLICO * 100, base.QT_MAT_BAS)
    base["SEM_AGUA_POTAVEL"] = (1 - base.IN_AGUA_POTAVEL).where(base.IN_AGUA_POTAVEL.notna())
    esgoto_adequado = base[["IN_ESGOTO_REDE_PUBLICA", "IN_ESGOTO_FOSSA_SEPTICA"]].max(axis=1, skipna=True).where(base[["IN_ESGOTO_REDE_PUBLICA", "IN_ESGOTO_FOSSA_SEPTICA"]].notna().any(axis=1))
    base["SEM_ESGOTO_ADEQUADO"] = (1 - esgoto_adequado).where(esgoto_adequado.notna())
    base["SEM_ENERGIA"] = base.IN_ENERGIA_INEXISTENTE.where(base.IN_ENERGIA_INEXISTENTE.notna())
    base["SEM_COLETA_LIXO"] = (1 - base.IN_LIXO_SERVICO_COLETA).where(base.IN_LIXO_SERVICO_COLETA.notna())
    lacks = base[["SEM_AGUA_POTAVEL", "SEM_ESGOTO_ADEQUADO", "SEM_ENERGIA", "SEM_COLETA_LIXO"]]
    base["QT_CARENCIAS_ESSENCIAIS"] = lacks.sum(axis=1, min_count=1)
    base["TRES_MAIS_CARENCIAS"] = base.QT_CARENCIAS_ESSENCIAIS.ge(3).astype(float).where(lacks.notna().sum(axis=1).ge(3))
    env = ["IN_ENERGIA_RENOVAVEL", "IN_AREA_VERDE", "IN_AREA_PLANTIO", "IN_TRATAMENTO_LIXO_SEPARACAO", "IN_TRATAMENTO_LIXO_REUTILIZA", "IN_TRATAMENTO_LIXO_RECICLAGEM", "IN_EDUC_AMBIENTAL"]
    base["INDICE_PRATICAS_AMBIENTAIS"] = base[env].mean(axis=1, skipna=True).where(base[env].notna().any(axis=1)) * 100
    support_access = base[["IN_ACESSIBILIDADE_CORRIMAO", "IN_ACESSIBILIDADE_ELEVADOR", "IN_ACESSIBILIDADE_PISOS_TATEIS", "IN_ACESSIBILIDADE_VAO_LIVRE", "IN_ACESSIBILIDADE_RAMPAS", "IN_ACESSIBILIDADE_SINAL_SONORO", "IN_ACESSIBILIDADE_SINAL_TATIL", "IN_ACESSIBILIDADE_SINAL_VISUAL"]].mean(axis=1, skipna=True)
    support = pd.concat([base.IN_SALA_ATENDIMENTO_ESPECIAL, support_access,
                         base.QT_PROF_TRAD_LIBRAS.gt(0).astype(float).where(base.QT_PROF_TRAD_LIBRAS.notna()),
                         base.QT_PROF_REVISOR_BRAILLE.gt(0).astype(float).where(base.QT_PROF_REVISOR_BRAILLE.notna()),
                         base.QT_PROF_MONITORES.gt(0).astype(float).where(base.QT_PROF_MONITORES.notna())], axis=1)
    base["ESTRUTURA_INCLUSAO"] = support.mean(axis=1, skipna=True).where(support.notna().any(axis=1)) * 100
    for suffix in ["LINGUA_PORT", "MATEMATICA", "FISICA", "QUIMICA", "HISTORIA", "GEOGRAFIA", "CIENCIAS", "INFO_COMPUTACAO"]:
        base[f"TURMAS_DOCENTE_{suffix}"] = ratio(base[f"QT_TUR_BAS_DISC_{suffix}"], base[f"QT_DOC_BAS_DISC_{suffix}"])

    digital = {"IN_INTERNET": .20, "IN_BANDA_LARGA": .25, "IN_INTERNET_ALUNOS": .20,
               "IN_INTERNET_APRENDIZAGEM": .20, "EQUIP_NORM": .15}
    base["EQUIP_NORM"] = (base.DISPOSITIVOS_100_ALUNOS.clip(0, 20) / 20).where(base.DISPOSITIVOS_100_ALUNOS.notna())
    base["IMDE"] = weighted_score(base, digital)
    access = {c: 1/8 for c in ["IN_ACESSIBILIDADE_CORRIMAO", "IN_ACESSIBILIDADE_ELEVADOR",
              "IN_ACESSIBILIDADE_PISOS_TATEIS", "IN_ACESSIBILIDADE_VAO_LIVRE", "IN_ACESSIBILIDADE_RAMPAS",
              "IN_ACESSIBILIDADE_SINAL_SONORO", "IN_ACESSIBILIDADE_SINAL_TATIL", "IN_ACESSIBILIDADE_SINAL_VISUAL"]}
    base["INDICE_ACESSIBILIDADE"] = weighted_score(base, access)
    pressure = pd.concat([winsor01(base[c]) for c in ["ALUNOS_DOCENTE", "ALUNOS_TURMA", "MATRICULAS_SALA"]], axis=1).mean(axis=1)
    lack = pd.concat([1-base.IMDE/100, 1-base.INDICE_ACESSIBILIDADE/100,
                      1-winsor01(base.DISPOSITIVOS_100_ALUNOS)], axis=1).mean(axis=1)
    volume = winsor01(np.log1p(base.QT_MAT_BAS))
    base["IPI"] = (100 * (.45*lack + .35*pressure + .20*volume)).clip(0, 100)
    base["PRESSAO_OUTLIER"] = False
    for c in ["ALUNOS_DOCENTE", "ALUNOS_TURMA", "MATRICULAS_SALA"]:
        q1, q3 = base[c].quantile([.25, .75]); lim = q3 + 1.5*(q3-q1)
        base["PRESSAO_OUTLIER"] |= base[c].gt(lim)

    # Testes de consistência sem forçar igualdade.
    base["DIF_SEXO"] = base.QT_MAT_BAS - base[["QT_MAT_BAS_FEM", "QT_MAT_BAS_MASC", "QT_MAT_BAS_ND"]].sum(axis=1, min_count=3)
    base["DIF_RACA"] = base.QT_MAT_BAS - base[race_cols].sum(axis=1, min_count=len(race_cols))

    course_key = [ID, "CO_CURSO_EDUC_PROFISSIONAL"]
    curso["DEPENDENCIA"] = curso.TP_DEPENDENCIA.map(dep).fillna("Não informado")
    curso["LOCALIZACAO"] = curso.TP_LOCALIZACAO.map(loc).fillna("Não informado")
    curso.to_parquet(OUT / "f_curso_tecnico.parquet", index=False)
    escola[GEO + [c for c in ["DEPENDENCIA", "LOCALIZACAO", "SITUACAO"] if c in escola]].to_parquet(OUT / "d_escola.parquet", index=False)
    for name, fact in facts.items(): fact.to_parquet(OUT / f"f_{name}.parquet", index=False)
    base.to_parquet(OUT / "escola_analytics.parquet", index=False)

    # Tabelas longas separadas: nunca cruza sexo, raça e idade.
    long_defs = {
      "matricula_sexo": {"Feminino":"QT_MAT_BAS_FEM", "Masculino":"QT_MAT_BAS_MASC", "Não declarado":"QT_MAT_BAS_ND"},
      "matricula_raca": {"Branca":"QT_MAT_BAS_BRANCA", "Preta":"QT_MAT_BAS_PRETA", "Parda":"QT_MAT_BAS_PARDA", "Amarela":"QT_MAT_BAS_AMARELA", "Indígena":"QT_MAT_BAS_INDIGENA"},
      "matricula_idade": {"0–3":"QT_MAT_BAS_0_3", "4–5":"QT_MAT_BAS_4_5", "6–10":"QT_MAT_BAS_6_10", "11–14":"QT_MAT_BAS_11_14", "15–17":"QT_MAT_BAS_15_17", "18+":"QT_MAT_BAS_18_MAIS"}}
    for filename, mapping in long_defs.items():
        x = base[[ID] + list(mapping.values())].rename(columns={v:k for k,v in mapping.items()})
        x.melt(ID, var_name="CATEGORIA", value_name="MATRICULAS").to_parquet(OUT / f"{filename}.parquet", index=False)

    audits = [audit_file(n) for n in FILES]
    active = set(escola.loc[escola.SITUACAO.eq("Em atividade"), ID].dropna())
    for row in audits:
        if row["tabela"] != "escola":
            keys = set(read(row["tabela"], [ID])[ID].dropna())
            row["escolas_ativas_com_correspondencia"] = len(active & keys)
            row["pct_correspondencia_ativas"] = round(100*len(active & keys)/len(active), 3) if active else None
            row["chaves_sem_dimensao_escola"] = len(keys - set(escola[ID].dropna()))
    pd.DataFrame(audits).to_csv(OUT / "auditoria.csv", index=False, encoding="utf-8-sig")
    consistency = {
        "escolas_com_diferenca_sexo": int(base.DIF_SEXO.fillna(0).ne(0).sum()),
        "diferenca_absoluta_sexo": float(base.DIF_SEXO.abs().sum()),
        "escolas_com_diferenca_raca": int(base.DIF_RACA.fillna(0).ne(0).sum()),
        "diferenca_absoluta_raca": float(base.DIF_RACA.abs().sum()),
        "nota_raca": "A diferença representa categorias não declaradas/não disponíveis; não foi imputada."
    }
    (OUT / "consistencia.json").write_text(json.dumps(consistency, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Concluído: {len(base):,} escolas; {len(curso):,} registros escola-curso.")

if __name__ == "__main__":
    main()
