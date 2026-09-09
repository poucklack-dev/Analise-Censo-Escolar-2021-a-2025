# Diagnóstico da Educação Básica Brasileira — Censo Escolar 2021–2025

Plataforma analítica em Python para explorar o Censo Escolar de 2021 a 2025 e avaliar perspectivas para 2026. O projeto combina auditoria, harmonização de layouts anuais, indicadores educacionais, validação temporal e dashboard interativo.

## Demonstração local

```powershell
git clone URL_DO_SEU_REPOSITORIO
cd NOME_DO_REPOSITORIO
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

O dashboard abre em `http://localhost:8501`. Os artefatos processados necessários para a demonstração acompanham o repositório; não é necessário baixar os microdados para apenas visualizar o projeto.

## Execução

```powershell
python -m pip install -r requirements.txt
python pipeline.py
python historical_pipeline.py
python predictive_pipeline.py
python generate_reports.py
streamlit run app.py
```

O pipeline lê os arquivos de 2025 em `dados/2025/`, usando codificação `cp1252`, mantém as fontes intactas e grava a camada curada em `output/`. Os demais anos ficam organizados em `dados/<ano>/`. A pasta `dados/` é ignorada pelo Git devido ao tamanho; somente os resultados processados necessários para a demonstração são versionados.

## Estrutura do repositório

```text
app.py                    Dashboard Streamlit
pipeline.py               Tratamento do layout de 2025
historical_pipeline.py    Auditoria e harmonização de 2021–2025
predictive_pipeline.py    Validação e cenários para 2026
generate_reports.py       Relatórios e tabelas auxiliares
output/                   Dados processados usados pelo dashboard
docs/                     Documentação metodológica
static/ e templates/      Interface Flask alternativa
```

## Reprocessamento completo

Os microdados brutos não são publicados neste repositório. Para reconstruir todos os resultados, obtenha as bases no portal do Inep e organize os arquivos localmente em `dados/2021/` até `dados/2025/`. Depois execute:

## Arquitetura e ETL

- `pipeline.py`: seleção/tipagem, dimensões e fatos Parquet, auditoria em chunks, testes e métricas escolares.
- `historical_pipeline.py`: auditoria recursiva, leitura dos dicionários, harmonização 2021–2025, dimensão de ano, painel longitudinal, transições, trajetórias e validação preditiva temporal.
- `app.py`: filtros Região → UF → rede → urbano/rural, rankings selecionáveis, benchmark, quadrantes e simulador de priorização.
- `generate_reports.py`: relatório executivo, ranking de UFs e dicionário de métricas.
- [Modelo de dados](MODELO_DADOS.md): cardinalidades e direção lógica dos filtros.

As tabelas operacionais são agregadas por escola. Curso técnico permanece no grão escola–curso, evitando multiplicação de matrículas. Dependência, localização e situação são traduzidas. Escolas não ativas permanecem auditáveis, mas os indicadores principais usam somente escolas em atividade.

## Qualidade e semântica

`0` é ocorrência informada como inexistente; `null` é ausente/não aplicável/não disponível. O pipeline não imputa nulos como zero. A auditoria cobre registros, chaves únicas/nulas/duplicadas, negativos, correspondência com escolas ativas e fatos sem dimensão. Sexo e raça têm diferenças calculadas e expostas sem ajuste artificial.

## Métodos

- Diversidade racial: índice de Simpson, `(1 − Σp²) × 100`, apenas entre categorias informadas.
- IMDE: internet 20%, banda larga 25%, acesso do aluno 20%, uso em aprendizagem 20%, equipamentos 15%. Equipamentos saturam em 20 por 100 alunos para evitar distorção em escolas pequenas.
- Acessibilidade: média de oito recursos observados. Pesos são renormalizados quando há nulos.
- HHI: soma dos quadrados das participações dos cursos, escala 0–10.000.
- Pressão: sinal acima de `Q3 + 1,5 × IQR` em alunos/docente, alunos/turma ou matrículas/sala.
- IPI: 45% carência de infraestrutura, 35% pressão e 20% volume; variáveis contínuas são winsorizadas nos percentis 5 e 95.

Os pesos do IPI são escolhas normativas transparentes. O simulador seleciona a quantidade de escolas a investigar; o score não é verdade absoluta nem diagnóstico causal.

## Entregáveis

- Dashboard: `app.py`
- Camada estrela/analítica: `output/*.parquet`
- Auditoria: `output/auditoria.csv` e `output/consistencia.json`
- Métricas: `output/dicionario_metricas.csv`
- Relatório: `output/relatorio_executivo.md`
- Ranking: `output/ranking_uf.csv`

## Limitações

As bases são agregadas; não há IDEB/notas nem custos; não se infere causalidade; docentes/gestores podem ser vínculos, não indivíduos únicos; não declarados afetam denominadores. Curso técnico só possui série de 2023 a 2025, e perfis detalhados de docente/gestor permanecem restritos a 2025.

## Arquitetura histórica

Os layouts anuais são tratados antes da camada semântica. O crosswalk usa códigos, descrições dos dicionários, granularidade e notas oficiais, preservando `null` como indisponível. A camada harmonizada mantém nomes constantes e a coluna `ANO`; regras específicas não chegam ao frontend. Consulte [harmonização dos dados](docs/harmonizacao_dados.md) e o [relatório de auditoria](docs/relatorio_auditoria_multianual.md).

A modelagem temporal usa painel escola×ano, lags sem informação futura, teste 2024→2025 e comparação obrigatória com baseline. Modelos e resultados são persistidos pelo pipeline offline e nunca retreinados ao abrir a aplicação. Como o modelo experimental atual não superou o baseline, a estimativa de 2025 e a projeção indicativa de 2026 são exibidas com alerta explícito de baixa confiabilidade.
