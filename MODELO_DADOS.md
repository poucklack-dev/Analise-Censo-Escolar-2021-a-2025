# Modelo analítico

```mermaid
erDiagram
  dEscola ||--o| fMatricula : CO_ENTIDADE
  dEscola ||--o| fDocente : CO_ENTIDADE
  dEscola ||--o| fTurma : CO_ENTIDADE
  dEscola ||--o| fGestor : CO_ENTIDADE
  dEscola ||--o{ fCursoTecnico : CO_ENTIDADE
  dCursoTecnico ||--o{ fCursoTecnico : CO_CURSO_EDUC_PROFISSIONAL
```

Os filtros fluem das dimensões para os fatos. Escola, matrícula, docente, turma e gestor têm um registro agregado por escola. Curso técnico tem um registro por escola–curso; por isso jamais é unido diretamente aos demais fatos para somar matrículas gerais.

As tabelas `matricula_sexo`, `matricula_raca` e `matricula_idade` são fatos auxiliares separados. Essa separação impede produto cartesiano entre quebras demográficas.
