# Harmonização dos dados — Censo Escolar 2021–2025

## Arquitetura

`dados/<ano>` (raw, imutável) → ETL específico do layout → crosswalk → `output/historico` (Parquet/CSV) → indicadores/API/dashboard.

O processamento histórico é executado por `historical_pipeline.py`. A aplicação consulta artefatos persistidos e não lê CSV/XLSX nem treina modelos durante a abertura.

## Evidência e decisões

- 2021–2024: um arquivo consolidado, com uma linha por `CO_ENTIDADE`, contém cadastro, infraestrutura e totais escolares de matrícula, docente e turma.
- 2025: seis tabelas escolares agregadas separadas. Escola, matrícula, docente, turma e gestor têm `CO_ENTIDADE` como chave; curso técnico usa escola–curso.
- Cursos técnicos: entidade própria disponível somente em 2023–2025. Não há série técnica para 2021–2022 neste conjunto.
- Gestores e perfil detalhado docente: os totais/categorias usados pela aplicação 2025 não estão no layout escolar consolidado anterior. As páginas detalhadas permanecem 2025.
- Geografia: junções usam códigos (`CO_ENTIDADE`, `CO_MUNICIPIO`, `CO_UF`), nunca nomes como chave primária.
- Ausência: coluna ausente, valor nulo, não coletado ou não aplicável permanece `null`; nunca vira zero.

## Variáveis históricas centrais

| Variável padrão | 2021–2024 | 2025 | Compatibilidade/transformação |
|---|---|---|---|
| Matrículas | `QT_MAT_BAS` | `QT_MAT_BAS` (tabela matrícula) | Compatível segundo os dicionários |
| Docentes | `QT_DOC_BAS` | `QT_DOC_BAS` (tabela docente) | Compatível no agregado escolar; vínculos, não pessoas únicas |
| Turmas | `QT_TUR_BAS` | `QT_TUR_BAS` (tabela turma) | Compatível no agregado escolar |
| Tempo integral | soma `QT_MAT_INF_INT + QT_MAT_FUND_INT + QT_MAT_MED_INT` | `QT_MAT_BAS_INT` | Equivalência parcial; reconstrução documentada |
| Internet/banda larga | mesmos códigos | mesmos códigos | Compatível onde a descrição oficial coincide |
| Acessibilidade | oito indicadores `IN_ACESSIBILIDADE_*` | mesmos indicadores | Comparável por componente observado; nulos não entram no denominador |
| IMDE Histórico Compatível | cinco componentes e pesos fixos | cinco componentes e pesos fixos | Nome distinto do IMDE 2025 para explicitar a série harmonizada |
| IPI Histórico Relativo | fórmula 45/35/20 recalculada por ano | idem | Comparável como prioridade relativa dentro do ano, não como nível absoluto entre anos |
| Cursos técnicos | ausente em 2021–2022; suplemento em 2023–2024 | tabela própria | Série disponível em 2023–2025 |

O crosswalk completo, com variável original, descrição oficial, status e observação por ano, está em `output/historico/crosswalk_variaveis.csv`. O catálogo extraído das planilhas oficiais está em `catalogo_dicionarios.csv`.

## Indicadores e agregação

Taxas operacionais territoriais usam razão de totais: `SUM(matrículas) / SUM(docentes|turmas|salas)`. Índices escolares são ponderados por matrículas quando agregados. Nenhuma média de médias é usada quando o denominador original está disponível.

As faixas das matrizes de transição são tercis anuais (`Baixa`, `Média`, `Alta`) calculados entre escolas ativas. Como são posições relativas, medem mobilidade distributiva e não mudança absoluta.

Trajetórias exigem ao menos três observações. “Melhora/queda consistente” exige variações anuais sempre acima/abaixo de 2%; “recuperação/queda recente” exige mudança final superior a 10% em direção oposta à média anterior; “volátil” exige desvio-padrão das variações acima de 20%; demais casos são “estáveis”. “Variação atípica — investigar” compara a última variação à mediana e MAD, com piso de 50%.

## Modelagem temporal

Pergunta: é possível prever `QT_MAT_BAS` da escola em `t+1` usando apenas dados disponíveis em `t`? O painel usa transições 2021→2022 a 2024→2025, lags, totais operacionais, razões, rede, localização e conectividade. O teste é estritamente temporal: treino com alvos até 2024 e teste em 2025. O baseline é persistência (`matrículas_t+1 = matrículas_t`).

O Ridge não superou o baseline (MAE 110,99 contra 27,41; RMSE 464,76 contra 88,85). A estimativa retrospectiva de 2025 e a projeção indicativa de 2026 são exibidas para avaliação de portfólio, sempre marcadas como experimentais e de baixa confiabilidade. Os coeficientes são associações preditivas, não efeitos causais. Quatro transições anuais não justificam ARIMA, ETS ou Prophet agregados.

## Auditoria

Inventário, qualidade, transições, trajetórias e metadados do modelo ficam em `output/historico/`. O índice de compatibilidade mede cobertura da camada analítica, com peso 1 para compatível/renomeada e 0,5 para equivalência parcial; não representa qualidade oficial do Censo.
