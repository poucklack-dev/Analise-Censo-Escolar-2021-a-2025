"""Auditoria, harmonizacao e modelagem temporal do Censo Escolar 2021-2025.

Este pipeline e offline: le os arquivos brutos e dicionarios uma vez e persiste
artefatos Parquet/CSV consumidos pelas aplicacoes. Ausencia nunca e convertida em zero.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re
import unicodedata

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "dados"
OUT = ROOT / "output" / "historico"
OUT.mkdir(parents=True, exist_ok=True)
YEARS = list(range(2021, 2026))
ENC = "cp1252"
KEY = "CO_ENTIDADE"

BASE_COLUMNS = [
    "NU_ANO_CENSO", "NO_REGIAO", "CO_REGIAO", "NO_UF", "SG_UF", "CO_UF",
    "NO_MUNICIPIO", "CO_MUNICIPIO", "NO_ENTIDADE", KEY, "TP_DEPENDENCIA",
    "TP_LOCALIZACAO", "TP_SITUACAO_FUNCIONAMENTO", "QT_MAT_BAS", "QT_DOC_BAS",
    "QT_TUR_BAS", "QT_MAT_INF_CRE", "QT_MAT_INF_PRE", "QT_MAT_FUND_AI",
    "QT_MAT_FUND_AF", "QT_MAT_MED", "QT_MAT_EJA", "QT_MAT_PROF",
    "QT_MAT_PROF_TEC", "QT_SALAS_UTILIZADAS", "QT_SALAS_UTILIZA_CLIMATIZADAS",
    "QT_SALAS_UTILIZADAS_ACESSIVEIS", "QT_DESKTOP_ALUNO", "QT_COMP_PORTATIL_ALUNO",
    "QT_TABLET_ALUNO", "IN_INTERNET", "IN_BANDA_LARGA", "IN_INTERNET_ALUNOS",
    "IN_INTERNET_APRENDIZAGEM", "IN_LABORATORIO_INFORMATICA", "IN_BIBLIOTECA",
    "IN_BIBLIOTECA_SALA_LEITURA", "IN_LABORATORIO_CIENCIAS", "IN_QUADRA_ESPORTES",
    "IN_REFEITORIO", "IN_AGUA_POTAVEL", "IN_AGUA_REDE_PUBLICA",
    "IN_AGUA_INEXISTENTE", "IN_ENERGIA_REDE_PUBLICA", "IN_ENERGIA_RENOVAVEL",
    "IN_ENERGIA_INEXISTENTE", "IN_ESGOTO_REDE_PUBLICA", "IN_ESGOTO_FOSSA_SEPTICA",
    "IN_ESGOTO_INEXISTENTE", "IN_ACESSIBILIDADE_CORRIMAO", "IN_ACESSIBILIDADE_ELEVADOR",
    "IN_ACESSIBILIDADE_PISOS_TATEIS", "IN_ACESSIBILIDADE_VAO_LIVRE",
    "IN_ACESSIBILIDADE_RAMPAS", "IN_ACESSIBILIDADE_SINAL_SONORO",
    "IN_ACESSIBILIDADE_SINAL_TATIL", "IN_ACESSIBILIDADE_SINAL_VISUAL",
]
INTEGRAL_COMPONENTS = ["QT_MAT_INF_INT", "QT_MAT_FUND_INT", "QT_MAT_MED_INT"]
ACCESS = [c for c in BASE_COLUMNS if c.startswith("IN_ACESSIBILIDADE_")]
COURSE_COLUMNS = [
    "NU_ANO_CENSO", "NO_REGIAO", "SG_UF", "CO_UF", "NO_MUNICIPIO",
    "CO_MUNICIPIO", KEY, "NO_ENTIDADE", "TP_DEPENDENCIA", "TP_LOCALIZACAO",
    "NO_AREA_CURSO_PROFISSIONAL", "ID_AREA_CURSO_PROFISSIONAL",
    "NO_CURSO_EDUC_PROFISSIONAL", "CO_CURSO_EDUC_PROFISSIONAL",
    "QT_CURSO_TEC", "QT_MAT_CURSO_TEC",
]


def raw_files() -> list[Path]:
    return sorted(p for p in RAW.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".xls", ".parquet"})


def csv_columns(path: Path) -> list[str]:
    return list(pd.read_csv(path, sep=";", encoding=ENC, nrows=0).columns)


def dictionary_catalog() -> pd.DataFrame:
    rows = []
    for year in YEARS:
        path = next((RAW / str(year)).glob("dicion*.xlsx"))
        for sheet in pd.ExcelFile(path).sheet_names:
            raw = pd.read_excel(path, sheet_name=sheet, header=None)
            header_candidates = raw.index[raw.apply(lambda r: r.astype(str).str.contains("Nome da Vari", case=False, na=False).any(), axis=1)]
            if len(header_candidates) == 0:
                continue
            h = int(header_candidates[0])
            names = raw.iloc[h].tolist()
            name_idx = next(i for i, value in enumerate(names) if "Nome da Vari" in str(value))
            desc_idx = next(i for i, value in enumerate(names) if "Descri" in str(value))
            note_idx = next((i for i, value in enumerate(names) if "Nota" in str(value)), None)
            table = raw.iloc[h + 1 :]
            for _, row in table.iterrows():
                variable = row.iloc[name_idx]
                if pd.isna(variable) or not re.fullmatch(r"[A-Z][A-Z0-9_]+", str(variable).strip()):
                    continue
                rows.append({
                    "ANO": year, "TABELA_DICIONARIO": sheet.strip(), "VARIAVEL_ORIGINAL": str(variable).strip(),
                    "DESCRICAO_OFICIAL": None if pd.isna(row.iloc[desc_idx]) else str(row.iloc[desc_idx]).strip(),
                    "NOTA_OFICIAL": None if note_idx is None or pd.isna(row.iloc[note_idx]) else str(row.iloc[note_idx]).strip(),
                    "DICIONARIO": path.name,
                })
    return pd.DataFrame(rows).drop_duplicates(["ANO", "TABELA_DICIONARIO", "VARIAVEL_ORIGINAL"])


def inventory() -> pd.DataFrame:
    entity_names = {"microdados": "Escola consolidada", "Matricula": "Matricula", "Docente": "Docente",
                    "Turma": "Turma", "Gestor": "Gestor", "Curso": "Curso tecnico",
                    "suplemento": "Curso tecnico", "Escola": "Escola", "dicion": "Dicionario"}
    rows = []
    for path in raw_files():
        year = int(path.parent.name)
        label = next((v for k, v in entity_names.items() if k.lower() in path.name.lower()), "Auxiliar")
        if path.suffix.lower() == ".csv":
            cols = csv_columns(path)
            count = 0
            null_keys = duplicates = 0
            seen: set[str] = set()
            key = KEY if KEY in cols else None
            course_key = "CO_CURSO_EDUC_PROFISSIONAL" if label == "Curso tecnico" and "CO_CURSO_EDUC_PROFISSIONAL" in cols else None
            use = [c for c in [key, course_key] if c] or [cols[0]]
            for chunk in pd.read_csv(path, sep=";", encoding=ENC, usecols=use, chunksize=100_000, low_memory=False):
                count += len(chunk)
                if key:
                    s = chunk[key]
                    null_keys += int(s.isna().sum())
                    if course_key:
                        values = chunk[[key, course_key]].dropna().astype("Int64").astype(str).agg("|".join, axis=1)
                    else:
                        values = s.dropna().astype("Int64").astype(str)
                    duplicates += int(values.duplicated().sum() + values.isin(seen).sum())
                    seen.update(values.unique())
            course = label == "Curso tecnico"
            grain = "1 registro/escola-curso" if course else "1 registro/escola"
            if course and "CO_CURSO_EDUC_PROFISSIONAL" in cols:
                grain_key = f"{KEY}+CO_CURSO_EDUC_PROFISSIONAL"
            else:
                grain_key = key or "Nao identificada"
            rows.append({"ANO": year, "ARQUIVO": path.name, "TABELA": label, "GRANULARIDADE": grain,
                         "CHAVE": grain_key, "REGISTROS": count, "COLUNAS": len(cols),
                         "CHAVES_NULAS": null_keys, "DUPLICIDADES_CO_ENTIDADE": duplicates,
                         "DICIONARIO_ASSOCIADO": next((p.name for p in path.parent.glob("dicion*.xlsx")), None)})
        else:
            rows.append({"ANO": year, "ARQUIVO": path.name, "TABELA": label, "GRANULARIDADE": "metadados",
                         "CHAVE": "VARIAVEL", "REGISTROS": None, "COLUNAS": None, "CHAVES_NULAS": None,
                         "DUPLICIDADES_CO_ENTIDADE": None, "DICIONARIO_ASSOCIADO": path.name})
    return pd.DataFrame(rows)


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\W+", " ", text).strip()


def crosswalk(catalog: pd.DataFrame) -> pd.DataFrame:
    # Mapeamentos renomeados sao explicitamente declarados; os demais exigem nome e descricao oficiais coerentes.
    mapping = {c: {y: c for y in YEARS} for c in BASE_COLUMNS}
    mapping["QT_MAT_BAS_INT"] = {2021: "QT_MAT_INF_INT+QT_MAT_FUND_INT+QT_MAT_MED_INT",
                                 2022: "QT_MAT_INF_INT+QT_MAT_FUND_INT+QT_MAT_MED_INT",
                                 2023: "QT_MAT_INF_INT+QT_MAT_FUND_INT+QT_MAT_MED_INT",
                                 2024: "QT_MAT_INF_INT+QT_MAT_FUND_INT+QT_MAT_MED_INT", 2025: "QT_MAT_BAS_INT"}
    file_cols = {}
    for year in YEARS:
        if year < 2025:
            file_cols[year] = set(csv_columns(RAW / str(year) / f"microdados_ed_basica_{year}.csv"))
        else:
            file_cols[year] = set().union(*(set(csv_columns(p)) for p in (RAW / "2025").glob("Tabela_*.csv")))
    rows = []
    for standard, by_year in mapping.items():
        descriptions = {}
        for year, original in by_year.items():
            first = original.split("+")[0]
            match = catalog[(catalog.ANO == year) & (catalog.VARIAVEL_ORIGINAL == first)]
            descriptions[year] = None if match.empty else match.iloc[0].DESCRICAO_OFICIAL
        reference = normalize_text(descriptions.get(2025))
        for year in YEARS:
            original = by_year.get(year)
            exists = original is not None and all(c in file_cols[year] for c in original.split("+"))
            desc = descriptions.get(year)
            if not exists:
                status, note = "NAO EXISTENTE", "Variavel ou componentes ausentes no arquivo do ano."
            elif "+" in original:
                status, note = "EQUIVALENCIA PARCIAL", "Total reconstruido pela soma de etapas integrais; regra documentada."
            elif original != standard:
                status, note = "RENOMEADA", "Codigo mudou; descricao oficial foi conferida."
            elif reference and normalize_text(desc) == reference:
                status, note = "COMPATIVEL", "Mesmo codigo e descricao oficial equivalente ao ano de referencia."
            else:
                status, note = "EQUIVALENCIA PARCIAL", "Mesmo codigo; descricao/estrutura historica requer cautela."
            rows.append({"VARIAVEL_PADRAO": standard, "ANO": year, "VARIAVEL_ORIGINAL": original,
                         "STATUS_COMPATIBILIDADE": status, "DESCRICAO_OFICIAL": desc, "OBSERVACAO": note})
    return pd.DataFrame(rows)


def ratio(a: pd.Series, b: pd.Series) -> pd.Series:
    return a.div(b.where(b.ne(0)))


def winsor01(series: pd.Series) -> pd.Series:
    valid = series.dropna()
    if valid.nunique() < 2:
        return pd.Series(np.nan, index=series.index)
    lo, hi = valid.quantile([.05, .95])
    return (series.clip(lo, hi) - lo) / (hi - lo) if hi > lo else pd.Series(0.0, index=series.index)


def weighted_score(frame: pd.DataFrame, specs: dict[str, float]) -> pd.Series:
    numerator = sum(frame[c].astype(float) * w for c, w in specs.items())
    denominator = sum(frame[c].notna().astype(float) * w for c, w in specs.items())
    return numerator.div(denominator.where(denominator.ne(0))) * 100


def read_historical_year(year: int) -> pd.DataFrame:
    path = RAW / str(year) / f"microdados_ed_basica_{year}.csv"
    available = set(csv_columns(path))
    requested = [c for c in BASE_COLUMNS + INTEGRAL_COMPONENTS if c in available]
    data = pd.read_csv(path, sep=";", encoding=ENC, usecols=requested, low_memory=False)
    data["QT_MAT_BAS_INT"] = data[[c for c in INTEGRAL_COMPONENTS if c in data]].sum(axis=1, min_count=1)
    return data


def read_2025() -> pd.DataFrame:
    return pd.read_parquet(ROOT / "output" / "escola_analytics.parquet")


def harmonize() -> pd.DataFrame:
    frames = []
    for year in YEARS:
        data = read_historical_year(year) if year < 2025 else read_2025()
        data["ANO"] = year
        for col in BASE_COLUMNS + ["QT_MAT_BAS_INT"]:
            if col not in data:
                data[col] = np.nan
        data["DEPENDENCIA"] = data.get("DEPENDENCIA", data.TP_DEPENDENCIA.map({1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}))
        data["LOCALIZACAO"] = data.get("LOCALIZACAO", data.TP_LOCALIZACAO.map({1: "Urbana", 2: "Rural"}))
        data["SITUACAO"] = data.get("SITUACAO", data.TP_SITUACAO_FUNCIONAMENTO.map({1: "Em atividade", 2: "Paralisada", 3: "Extinta", 4: "Extinta no ano anterior"}))
        data["DISPOSITIVOS"] = data[["QT_DESKTOP_ALUNO", "QT_COMP_PORTATIL_ALUNO", "QT_TABLET_ALUNO"]].sum(axis=1, min_count=1)
        data["ALUNOS_DOCENTE"] = ratio(data.QT_MAT_BAS, data.QT_DOC_BAS)
        data["ALUNOS_TURMA"] = ratio(data.QT_MAT_BAS, data.QT_TUR_BAS)
        data["MATRICULAS_SALA"] = ratio(data.QT_MAT_BAS, data.QT_SALAS_UTILIZADAS)
        data["PCT_TEMPO_INTEGRAL"] = 100 * ratio(data.QT_MAT_BAS_INT, data.QT_MAT_BAS)
        equipment = (data.DISPOSITIVOS * 5 / data.QT_MAT_BAS.where(data.QT_MAT_BAS.ne(0))).clip(upper=1)
        data["IMDE_HISTORICO_COMPATIVEL"] = weighted_score(data.assign(_equip=equipment), {
            "IN_INTERNET": .20, "IN_BANDA_LARGA": .25, "IN_INTERNET_ALUNOS": .20,
            "IN_INTERNET_APRENDIZAGEM": .20, "_equip": .15})
        data["INDICE_ACESSIBILIDADE_HIST"] = data[ACCESS].mean(axis=1, skipna=True) * 100
        data.loc[data[ACCESS].notna().sum(axis=1).eq(0), "INDICE_ACESSIBILIDADE_HIST"] = np.nan
        frames.append(data)
    result = pd.concat(frames, ignore_index=True, sort=False)
    # IPI historico usa a mesma formula, mas percentis sao relativos a cada ano; nao se interpreta nivel absoluto entre anos.
    result["IPI_HISTORICO_RELATIVO"] = np.nan
    for year, idx in result.groupby("ANO").groups.items():
        block = result.loc[idx]
        lack = 1 - pd.concat([block.IMDE_HISTORICO_COMPATIVEL / 100,
                              block.INDICE_ACESSIBILIDADE_HIST / 100,
                              (block.DISPOSITIVOS * 5 / block.QT_MAT_BAS.where(block.QT_MAT_BAS.ne(0))).clip(upper=1)], axis=1).mean(axis=1)
        pressure = pd.concat([winsor01(block.ALUNOS_DOCENTE), winsor01(block.ALUNOS_TURMA), winsor01(block.MATRICULAS_SALA)], axis=1).mean(axis=1)
        result.loc[idx, "IPI_HISTORICO_RELATIVO"] = 100 * (.45 * lack + .35 * pressure + .20 * winsor01(block.QT_MAT_BAS))
    keep = list(dict.fromkeys(["ANO"] + BASE_COLUMNS + ["QT_MAT_BAS_INT", "DEPENDENCIA", "LOCALIZACAO", "SITUACAO",
        "DISPOSITIVOS", "ALUNOS_DOCENTE", "ALUNOS_TURMA", "MATRICULAS_SALA", "PCT_TEMPO_INTEGRAL",
        "IMDE_HISTORICO_COMPATIVEL", "INDICE_ACESSIBILIDADE_HIST", "IPI_HISTORICO_RELATIVO"]))
    return result[keep]


def harmonize_courses() -> pd.DataFrame:
    frames = []
    paths = {2023: RAW / "2023" / "suplemento_cursos_tecnicos_2023.csv",
             2024: RAW / "2024" / "suplemento_cursos_tecnicos_2024.csv",
             2025: RAW / "2025" / "Tabela_Curso_Tecnico_2025_V2.csv"}
    for year, path in paths.items():
        available = set(csv_columns(path)); use = [c for c in COURSE_COLUMNS if c in available]
        data = pd.read_csv(path, sep=";", encoding=ENC, usecols=use, low_memory=False)
        data["ANO"] = year
        frames.append(data)
    return pd.concat(frames, ignore_index=True, sort=False)


def quality(h: pd.DataFrame, cross: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, data in h.groupby("ANO"):
        cw = cross[cross.ANO.eq(year)]
        compatible = cw.STATUS_COMPATIBILIDADE.isin(["COMPATIVEL", "RENOMEADA"]).sum()
        partial = cw.STATUS_COMPATIBILIDADE.eq("EQUIVALENCIA PARCIAL").sum()
        score = 100 * (compatible + .5 * partial) / len(cw)
        rows.append({"ANO": year, "REGISTROS": len(data), "ESCOLAS": data.CO_ENTIDADE.nunique(),
                     "MUNICIPIOS": data.CO_MUNICIPIO.nunique(), "CAMPOS_HARMONIZADOS": len(h.columns),
                     "VALORES_NULOS": int(data.isna().sum().sum()), "CHAVES_DUPLICADAS": int(data.CO_ENTIDADE.duplicated().sum()),
                     "CAMPOS_COMPATIVEIS": int(compatible), "CAMPOS_PARCIAIS": int(partial),
                     "INDICE_COMPATIBILIDADE": round(score, 1),
                     "NOTA": "Compatibilidade com a camada analitica; nao e indice oficial de qualidade do Censo."})
    return pd.DataFrame(rows)


def temporal_summary(h: pd.DataFrame) -> pd.DataFrame:
    active = h[h.SITUACAO.eq("Em atividade")]
    keys = ["ANO", "NO_REGIAO", "SG_UF", "CO_MUNICIPIO", "NO_MUNICIPIO", "DEPENDENCIA", "LOCALIZACAO"]
    grouped = active.groupby(keys, dropna=False)
    out = grouped.agg(MATRICULAS=("QT_MAT_BAS", "sum"), DOCENTES=("QT_DOC_BAS", "sum"),
                      TURMAS=("QT_TUR_BAS", "sum"), SALAS=("QT_SALAS_UTILIZADAS", "sum"),
                      ESCOLAS=(KEY, "nunique")).reset_index()
    out["ALUNOS_DOCENTE"] = ratio(out.MATRICULAS, out.DOCENTES)
    out["ALUNOS_TURMA"] = ratio(out.MATRICULAS, out.TURMAS)
    out["MATRICULAS_SALA"] = ratio(out.MATRICULAS, out.SALAS)
    return out


def trajectories(h: pd.DataFrame) -> pd.DataFrame:
    active = h[h.SITUACAO.eq("Em atividade")][[KEY, "ANO", "QT_MAT_BAS"]].dropna()
    rows = []
    for school, data in active.groupby(KEY):
        data = data.sort_values("ANO"); values = data.QT_MAT_BAS.to_numpy(float); years = data.ANO.to_numpy(int)
        if len(data) < 3:
            continue
        changes = np.diff(values) / np.where(values[:-1] == 0, np.nan, values[:-1])
        slope = np.polyfit(years, values, 1)[0]
        prior_mean = np.nanmean(changes[:-1]) if len(changes) > 1 and np.isfinite(changes[:-1]).any() else np.nan
        if np.all(changes > .02): label = "Melhora consistente"
        elif np.all(changes < -.02): label = "Queda consistente"
        elif changes[-1] > .10 and np.isfinite(prior_mean) and prior_mean <= 0: label = "Recuperacao recente"
        elif changes[-1] < -.10 and np.isfinite(prior_mean) and prior_mean >= 0: label = "Queda recente"
        elif np.nanstd(changes) > .20: label = "Volatil"
        else: label = "Estavel"
        median = np.nanmedian(np.abs(changes - np.nanmedian(changes)))
        anomaly = bool(abs(changes[-1] - np.nanmedian(changes)) > max(.50, 3 * median)) if len(changes) > 1 else False
        rows.append({KEY: school, "ANOS_OBSERVADOS": len(data), "ANO_INICIAL": years[0], "ANO_FINAL": years[-1],
                     "MATRICULAS_INICIAL": values[0], "MATRICULAS_FINAL": values[-1], "INCLINACAO_ANUAL": slope,
                     "TRAJETORIA": label, "VARIACAO_ATIPICA_INVESTIGAR": anomaly})
    return pd.DataFrame(rows)


def transitions(h: pd.DataFrame) -> pd.DataFrame:
    rows = []
    active = h[h.SITUACAO.eq("Em atividade")].copy()
    for metric in ["IMDE_HISTORICO_COMPATIVEL", "ALUNOS_TURMA"]:
        parts = []
        for year, data in active.groupby("ANO"):
            valid = data[[KEY, metric]].dropna().copy()
            valid["FAIXA"] = pd.qcut(valid[metric].rank(method="first"), 3, labels=["Baixa", "Media", "Alta"])
            valid["ANO"] = year; parts.append(valid[[KEY, "ANO", "FAIXA"]])
        classified = pd.concat(parts)
        for year in YEARS[:-1]:
            left = classified[classified.ANO.eq(year)][[KEY, "FAIXA"]].rename(columns={"FAIXA": "ORIGEM"})
            right = classified[classified.ANO.eq(year + 1)][[KEY, "FAIXA"]].rename(columns={"FAIXA": "DESTINO"})
            matrix = left.merge(right, on=KEY).groupby(["ORIGEM", "DESTINO"], observed=True).size().reset_index(name="ESCOLAS")
            matrix["INDICADOR"] = metric; matrix["ANO_ORIGEM"] = year; matrix["ANO_DESTINO"] = year + 1
            rows.append(matrix)
    return pd.concat(rows, ignore_index=True)


def ridge_fit_predict(train: pd.DataFrame, test: pd.DataFrame, features: list[str], alpha: float) -> tuple[np.ndarray, dict[str, float]]:
    x = train[features].astype(float); y = np.log1p(train.TARGET.astype(float))
    means = x.mean(); scales = x.std().replace(0, 1); xz = ((x - means) / scales).fillna(0)
    xt = ((test[features].astype(float) - means) / scales).fillna(0)
    xz = xz.clip(-10, 10); xt = xt.clip(-10, 10)
    X = np.c_[np.ones(len(xz)), xz.to_numpy()]; T = np.c_[np.ones(len(xt)), xt.to_numpy()]
    penalty = np.eye(X.shape[1]) * alpha; penalty[0, 0] = 0
    beta = np.linalg.pinv(X.T @ X + penalty) @ X.T @ y.to_numpy()
    upper = float(np.log1p(max(1, train.TARGET.quantile(.999) * 3)))
    prediction = np.maximum(0, np.expm1(np.clip(T @ beta, 0, upper)))
    importance = dict(sorted(zip(features, np.abs(beta[1:])), key=lambda item: item[1], reverse=True))
    return prediction, importance


def predictive_model(h: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    cols = [KEY, "ANO", "QT_MAT_BAS", "QT_DOC_BAS", "QT_TUR_BAS", "QT_SALAS_UTILIZADAS",
            "IN_INTERNET", "IN_BANDA_LARGA", "TP_DEPENDENCIA", "TP_LOCALIZACAO"]
    panel = h[h.SITUACAO.eq("Em atividade")][cols].sort_values([KEY, "ANO"]).copy()
    panel["TARGET"] = panel.groupby(KEY).QT_MAT_BAS.shift(-1)
    panel["TARGET_ANO"] = panel.ANO + 1
    panel["LAG_MATRICULAS_2"] = panel.groupby(KEY).QT_MAT_BAS.shift(1)
    panel["VAR_MATRICULAS_1ANO"] = panel.groupby(KEY).QT_MAT_BAS.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    panel["ALUNOS_DOCENTE"] = ratio(panel.QT_MAT_BAS, panel.QT_DOC_BAS)
    panel["ALUNOS_TURMA"] = ratio(panel.QT_MAT_BAS, panel.QT_TUR_BAS)
    features = ["QT_MAT_BAS", "LAG_MATRICULAS_2", "QT_DOC_BAS", "QT_TUR_BAS", "QT_SALAS_UTILIZADAS",
                "ALUNOS_DOCENTE", "ALUNOS_TURMA", "VAR_MATRICULAS_1ANO", "IN_INTERNET", "IN_BANDA_LARGA",
                "TP_DEPENDENCIA", "TP_LOCALIZACAO"]
    samples = panel.dropna(subset=["TARGET", "QT_MAT_BAS"])
    test = samples[samples.TARGET_ANO.eq(2025)].copy(); train = samples[samples.TARGET_ANO.lt(2025)].copy()
    pred, importance = ridge_fit_predict(train, test, features, alpha=10.0)
    baseline = test.QT_MAT_BAS.to_numpy(float); actual = test.TARGET.to_numpy(float)
    def metrics(y, p):
        err = y - p
        return {"MAE": float(np.mean(np.abs(err))), "RMSE": float(np.sqrt(np.mean(err ** 2))),
                "MAPE": float(np.mean(np.abs(err[y != 0] / y[y != 0])) * 100),
                "R2": float(1 - np.sum(err ** 2) / np.sum((y - y.mean()) ** 2))}
    model_metrics, baseline_metrics = metrics(actual, pred), metrics(actual, baseline)
    residual = actual - pred; qlo, qhi = np.quantile(residual, [.10, .90])
    future = panel[panel.ANO.eq(2025)].copy()
    all_train = samples[samples.TARGET_ANO.le(2025)]
    future_pred, _ = ridge_fit_predict(all_train, future, features, alpha=10.0)
    retrospective = pd.DataFrame({KEY: test[KEY].to_numpy(), "ANO_ORIGEM": 2024, "ANO_PREVISTO": 2025,
        "PREVISAO": pred, "REALIZADO": actual, "LIMITE_INFERIOR": np.maximum(0, pred + qlo),
        "LIMITE_SUPERIOR": np.maximum(0, pred + qhi), "TIPO": "Estimativa retrospectiva",
        "CONFIABILIDADE": "Baixa — modelo inferior ao baseline"})
    prospective = pd.DataFrame({KEY: future[KEY].to_numpy(), "ANO_ORIGEM": 2025, "ANO_PREVISTO": 2026,
        "PREVISAO": future_pred, "REALIZADO": np.nan, "LIMITE_INFERIOR": np.maximum(0, future_pred + qlo),
        "LIMITE_SUPERIOR": np.maximum(0, future_pred + qhi), "TIPO": "Projecao indicativa",
        "CONFIABILIDADE": "Baixa — modelo inferior ao baseline"})
    predictions = pd.concat([retrospective, prospective], ignore_index=True)
    metadata = {"nome": "Ridge longitudinal de matriculas", "objetivo": "Prever matriculas da escola no proximo Censo",
                "target": "QT_MAT_BAS no ano t+1", "periodo_treino": "features 2021-2023 / targets 2022-2024",
                "periodo_teste": "features 2024 / target 2025", "observacoes_treino": len(train),
                "observacoes_teste": len(test), "features": features, "algoritmo": "Ridge em log1p(target), alpha=10",
                "baseline": "persistencia: matriculas_t+1 = matriculas_t", "metricas_modelo": model_metrics,
                "metricas_baseline": baseline_metrics, "superou_baseline_mae": model_metrics["MAE"] < baseline_metrics["MAE"],
                "importancia_coeficientes_padronizados": importance,
                "intervalo": "quantis 10% e 90% dos residuos do teste temporal de 2025",
                "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
                "limitacoes": "Quatro transicoes anuais; mudancas cadastrais e metodologicas podem afetar o painel. Importancias nao sao causais."}
    return predictions, metadata


def main() -> None:
    catalog = dictionary_catalog(); catalog.to_csv(OUT / "catalogo_dicionarios.csv", index=False, encoding="utf-8-sig")
    inv = inventory(); inv.to_csv(OUT / "inventario_arquivos.csv", index=False, encoding="utf-8-sig")
    cw = crosswalk(catalog); cw.to_csv(OUT / "crosswalk_variaveis.csv", index=False, encoding="utf-8-sig")
    h = harmonize(); h.to_parquet(OUT / "escola_harmonizada.parquet", index=False)
    pd.DataFrame({"ANO": YEARS}).to_parquet(OUT / "d_ano.parquet", index=False)
    courses = harmonize_courses(); courses.to_parquet(OUT / "curso_tecnico_harmonizado.parquet", index=False)
    quality(h, cw).to_csv(OUT / "qualidade_multianual.csv", index=False, encoding="utf-8-sig")
    temporal_summary(h).to_parquet(OUT / "resumo_temporal.parquet", index=False)
    trajectories(h).to_parquet(OUT / "trajetorias_escolas.parquet", index=False)
    transitions(h).to_csv(OUT / "matrizes_transicao.csv", index=False, encoding="utf-8-sig")
    predictions, metadata = predictive_model(h)
    predictions.to_parquet(OUT / "previsoes_matriculas.parquet", index=False)
    (OUT / "modelo_matriculas.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"escolas_ano": h.groupby("ANO").size().to_dict(), "cursos_ano": courses.groupby("ANO").size().to_dict(),
                      "modelo_superou_baseline": metadata["superou_baseline_mae"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
