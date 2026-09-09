# Diagnóstico e refatoração da camada preditiva

## Problemas encontrados

- `46.018.380` é o total do universo de escolas ativas em 2025.
- `45.523.573` é o realizado somente na coorte com pares válidos no backtest 2024→2025.
- A estimativa retrospectiva de 2025 (`≈50,62 milhões`) vinha de um Ridge escolar em `log1p` e era somada após a transformação inversa, acumulando viés positivo.
- A antiga projeção 2026 (`≈51,12 milhões`) era a soma sem reconciliação das previsões de 180.540 escolas.
- Crescimentos extremos por UF eram derivados dessa agregação micro sem controle macro.
- Pressão e infraestrutura usavam tendência sobre cinco pontos, com somente um backtest explícito.

## Nova decisão metodológica

O pipeline `predictive_pipeline.py` testa persistência, crescimento recente e tendência robusta em dois cortes fora da amostra: 2024 e 2025. O status é `APROVADO` somente quando o candidato supera persistência em erro médio e passa pelos testes de sanidade. Resultados reprovados são cenários indicativos, nunca previsões executivas.

Matrículas, IMDE e banda larga foram reprovados. Alunos/docente, alunos/turma, matrículas/sala, acessibilidade e internet foram aprovados. O cenário indicativo nacional de matrículas para 2026 é aproximadamente 45,39 milhões (-1,36%), reconciliado em todos os níveis. Regiões, UFs, redes e localização somam exatamente ao Brasil.

As projeções territoriais usam tendências robustas limitadas ao comportamento histórico e depois são reconciliadas ao cenário macro. Séries escolares anômalas não alimentam diretamente um total executivo. A camada de riscos usa anomalia, queda de matrículas, crescimento de pressão e queda de IMDE apenas como sinais para investigação.

## Separação da interface

As páginas executivas exibem 2025 somente como realizado e 2026 como previsão aprovada ou cenário indicativo. Estimativas retrospectivas, coortes, erros e baselines ficam exclusivamente em `Modelos & Validação`, organizado em abas de Performance, Backtests, Compatibilidade e Qualidade multianual.
