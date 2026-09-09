# Relatório técnico da auditoria multianual

## Arquivos e estruturas encontradas

Foram auditados recursivamente 16 arquivos brutos: cinco dicionários XLSX, quatro microdados escolares consolidados (2021–2024), dois suplementos de cursos técnicos (2023–2024) e seis tabelas agregadas de 2025. O inventário completo registra arquivo, tabela, granularidade, chave, registros, colunas, nulos e duplicidades em `output/historico/inventario_arquivos.csv`.

| Ano | Estrutura escolar | Registros | Colunas | Curso técnico |
|---:|---|---:|---:|---|
| 2021 | consolidada, escola | 221.140 | 370 | não disponível |
| 2022 | consolidada, escola | 224.649 | 385 | não disponível |
| 2023 | consolidada, escola | 217.625 | 408 | suplemento, 23.224 linhas |
| 2024 | consolidada, escola | 215.545 | 426 | suplemento, 27.516 linhas |
| 2025 | seis tabelas separadas | escola: 214.192 | escola: 290 | tabela própria, 32.136 linhas |

As tabelas escolares e fatos 2025 não têm duplicidade em `CO_ENTIDADE`. As tabelas de curso não têm duplicidade na chave composta escola–curso. Repetição de escola em curso é esperada e não foi tratada como erro.

## Comparabilidade

Comparáveis em 2021–2025: matrículas totais e por grandes etapas, docentes totais, turmas totais, salas, rede, localização, situação, conectividade, principais instalações e oito componentes de acessibilidade. Tempo integral é parcial em 2021–2024 porque foi reconstruído por etapas. IMDE recebeu uma versão histórica explicitamente nomeada. IPI é apenas relativo dentro de cada ano.

Parciais: granularidade lógica de docente/turma anterior (agregado dentro da escola consolidada), tempo integral reconstruído e componentes cujas notas oficiais indicam alterações. Não comparáveis/ausentes: perfil detalhado docente e gestor antes de 2025; cursos técnicos antes de 2023; indicadores 2025 sem equivalente documentado.

## Totais validados

| Ano | Escolas ativas | Matrículas | Docentes | Turmas |
|---:|---:|---:|---:|---:|
| 2021 | 180.057 | 46.668.401 | 2.846.169 | 2.128.776 |
| 2022 | 184.332 | 47.382.074 | 2.924.306 | 2.190.502 |
| 2023 | 180.230 | 47.304.632 | 2.934.558 | 2.212.677 |
| 2024 | 181.065 | 47.088.922 | 2.939.002 | 2.224.054 |
| 2025 | 180.540 | 46.018.380 | 2.992.045 | 2.233.976 |

Há 198.819 códigos escolares presentes nos cinco arquivos; presença não equivale a atividade. Continuidade e situação oficial são analisadas separadamente.

## Viabilidade preditiva

Viáveis: painel longitudinal escola×ano, teste temporal de previsão de matrículas, trajetórias, transições por faixas, anomalias para investigação e tendências territoriais descritivas.

Não recomendadas: ARIMA/ETS/Prophet sobre apenas cinco totais anuais; inferência causal; previsão de gestor/perfil docente sem histórico; previsão técnica para 2021–2022; classificação de pressão futura sem ganho validado. O Ridge longitudinal testado perdeu para a persistência e foi corretamente reprovado.

## Alterações realizadas

- ETL: novo pipeline offline anual, leitura dos dicionários, crosswalk, camada harmonizada, dimensão `dAno`, curso técnico 2023–2025 e validações.
- Modelo: fato escola–ano, lags sem vazamento, split temporal, baseline, métricas, incerteza residual, persistência de metadados e previsões não aprovadas.
- Frontend: filtro global de ano, bloqueio explícito de páginas incompatíveis, seção “Análises Preditivas”, evolução, pressão, infraestrutura, trajetórias, matriz de compatibilidade e página de modelos.
- Desempenho: CSV/XLSX e treino ficam fora do runtime; a interface lê Parquet/CSV/JSON persistidos com cache.
