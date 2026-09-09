"""Validação rápida dos arquivos necessários para publicar e executar o dashboard."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "output/escola_analytics.parquet",
    "output/f_curso_tecnico.parquet",
    "output/auditoria.csv",
    "output/historico/escola_harmonizada.parquet",
    "output/historico/curso_tecnico_harmonizado.parquet",
    "output/historico/qualidade_multianual.csv",
    "output/historico/crosswalk_variaveis.csv",
    "output/historico/trajetorias_escolas.parquet",
    "output/historico/previsoes_matriculas.parquet",
    "output/historico/registro_modelos.csv",
    "output/historico/backtests_modelos.csv",
    "output/historico/cenario_matriculas_2026_reconciliado.parquet",
    "output/historico/riscos_2026.parquet",
    "output/historico/auditoria_preditiva.json",
]

missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
oversized = [str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file() and path.stat().st_size >= 100 * 1024 * 1024 and "dados" not in path.parts]

if missing or oversized:
    if missing:
        print("Arquivos necessários ausentes:", *missing, sep="\n- ")
    if oversized:
        print("Arquivos acima de 100 MB:", *oversized, sep="\n- ")
    sys.exit(1)

print(f"Repositório validado: {len(REQUIRED)} artefatos necessários encontrados e nenhum arquivo versionável acima de 100 MB.")
