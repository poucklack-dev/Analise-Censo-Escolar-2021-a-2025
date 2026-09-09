"""Gera relatório executivo, métricas e tabelas de apoio a partir da camada analítica."""
from pathlib import Path
import pandas as pd
import numpy as np

R=Path(__file__).resolve().parent; O=R/"output"
d=pd.read_parquet(O/"escola_analytics.parquet"); d=d[d.SITUACAO.eq("Em atividade")]
c=pd.read_parquet(O/"f_curso_tecnico.parquet"); c=c[c.CO_ENTIDADE.isin(set(d.CO_ENTIDADE))]
def div(a,b): return a/b if b else np.nan
def w(g,col):
    x=g[[col,"QT_MAT_BAS"]].dropna(); return np.average(x[col],weights=x.QT_MAT_BAS) if len(x) and x.QT_MAT_BAS.sum() else np.nan
def br(v): return f"{v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

uf=d.groupby("SG_UF").agg(MATRICULAS=("QT_MAT_BAS","sum"),ESCOLAS=("CO_ENTIDADE","nunique"),DOCENTES=("QT_DOC_BAS","sum"),TURMAS=("QT_TUR_BAS","sum"))
for m in ["IMDE","INDICE_ACESSIBILIDADE","IPI","DIVERSIDADE_RACIAL"]: uf[m]=d.groupby("SG_UF").apply(lambda x:w(x,m),include_groups=False)
uf["ALUNOS_DOCENTE"]=uf.MATRICULAS/uf.DOCENTES; uf["ALUNOS_TURMA"]=uf.MATRICULAS/uf.TURMAS
uf.sort_values("IPI",ascending=False).to_csv(O/"ranking_uf.csv",encoding="utf-8-sig")

metrics=[
("Escolas em atividade","Escolas com situação 1","COUNT DISTINCT CO_ENTIDADE onde situação = ativa","Escola","Extintas/paralisadas excluídas dos KPIs"),
("Matrículas","Matrículas da educação básica","Σ QT_MAT_BAS","Matrícula","Agregado escolar"),
("Docentes","Docentes/vínculos informados","Σ QT_DOC_BAS","Docente","Não necessariamente pessoas únicas entre escolas"),
("Alunos por docente","Carga discente relativa","Σ matrículas / Σ docentes","Matrícula + Docente","Razão de totais"),
("Alunos por turma","Tamanho operacional médio","Σ matrículas / Σ turmas","Matrícula + Turma","Razão de totais"),
("Tempo integral","Participação de matrículas integrais","Σ integral / Σ matrículas × 100","Matrícula","Denominador > 0"),
("Diversidade racial","Probabilidade de dois alunos informados pertencerem a grupos diferentes","(1 - Σ pᵢ²) × 100","Matrícula","Índice de Simpson; exclui não informados"),
("IMDE","Maturidade digital escolar","média ponderada observada: internet 20%; banda 25%; aluno 20%; aprendizagem 20%; equipamentos 15%","Escola + Matrícula","Equipamentos saturados em 20/100 alunos; pesos renormalizados ante nulos"),
("Índice de Acessibilidade","Cobertura de oito recursos","média dos itens observados × 100","Escola","Nulos não viram zero"),
("HHI técnico","Concentração de matrículas entre cursos","Σ participação² × 10.000","Curso Técnico","0 diversificado; 10.000 curso único"),
("IPI","Prioridade de infraestrutura","45% carência + 35% pressão + 20% volume","Todas","Indicadores winsorizados P5–P95; sinal para investigação"),
("Outlier de pressão","Sinal estatístico de carga elevada","> Q3 + 1,5×IQR em qualquer indicador","Escola","Não significa escola ruim")]
pd.DataFrame(metrics,columns=["Métrica","Definição","Fórmula conceitual","Fonte","Observações"]).to_csv(O/"dicionario_metricas.csv",index=False,encoding="utf-8-sig")

rural=d[d.LOCALIZACAO.eq("Rural")]; urban=d[d.LOCALIZACAO.eq("Urbana")]
worst=uf.sort_values("IPI",ascending=False).head(5)
report=f"""# Relatório executivo — Censo Escolar 2025

## Resposta ao case

As UFs com maior sinal composto de atenção são **{', '.join(worst.index)}**. Elas lideram o IPI nacional no recorte, combinando menor disponibilidade relativa de infraestrutura, pressão operacional e volume atendido. O ranking é uma triagem: a decisão de investimento deve validar os componentes e o contexto de cada escola.

## Panorama

- {d.CO_ENTIDADE.nunique():,.0f} escolas em atividade e {d.QT_MAT_BAS.sum():,.0f} matrículas.
- {d.QT_DOC_BAS.sum():,.0f} docentes/vínculos e {d.QT_TUR_BAS.sum():,.0f} turmas.
- {br(div(d.QT_MAT_BAS.sum(),d.QT_DOC_BAS.sum()))} alunos por docente e {br(div(d.QT_MAT_BAS.sum(),d.QT_TUR_BAS.sum()))} alunos por turma.
- Banda larga: {br(100*d.IN_BANDA_LARGA.mean())}% das escolas ativas com resposta observada; gap rural menos urbano: {br(100*(rural.IN_BANDA_LARGA.mean()-urban.IN_BANDA_LARGA.mean()))} p.p.
- {c.QT_MAT_CURSO_TEC.sum():,.0f} matrículas técnicas em {c.CO_ENTIDADE.nunique():,.0f} escolas ofertantes.
- {100*d.PRESSAO_OUTLIER.mean():.2f}% das escolas têm ao menos um sinal de pressão pelo critério IQR.

## Principais evidências

1. **Prioridade territorial:** {worst.index[0]} tem o maior IPI ponderado ({br(worst.iloc[0].IPI)}). Hipótese a investigar: combinação dos componentes, sem atribuição causal.
2. **Maturidade digital:** {uf.IMDE.idxmin()} apresenta o menor IMDE ({br(uf.IMDE.min())}). Verificar banda larga, uso pedagógico e equipamentos.
3. **Acessibilidade:** {uf.INDICE_ACESSIBILIDADE.idxmin()} registra o menor índice observado ({br(uf.INDICE_ACESSIBILIDADE.min())}). Confirmar completude cadastral antes de intervenção.
4. **Pressão docente:** {uf.ALUNOS_DOCENTE.idxmax()} tem a maior razão agregada alunos/docente ({br(uf.ALUNOS_DOCENTE.max())}). A razão não mede qualidade e pode refletir organização da oferta.
5. **Desigualdade territorial:** a diferença rural–urbana de banda larga é {br(100*(rural.IN_BANDA_LARGA.mean()-urban.IN_BANDA_LARGA.mean()))} p.p.; trata-se de associação descritiva.

## Limitações

Dados de um único ano; ausência de evolução temporal, IDEB/notas e variáveis de custo; agregados escolares não permitem inferência individual; docentes e gestores podem representar vínculos; categorias de pós-graduação podem se sobrepor; não declaração é preservada como nulo; índices compostos dependem de pesos normativos e não demonstram causalidade.
"""
(O/"relatorio_executivo.md").write_text(report,encoding="utf-8")
print("Relatórios gerados.")
