# Caminhos dos notebooks históricos

A curadoria move os cadernos abaixo para `notebooks/archive/` em seus próprios
módulos. Os links de leitura e Colab usam os novos caminhos. Campos históricos
como `source_notebook` e `source_procedure` preservam o endereço registrado na
produção da evidência; esta tabela permite encontrar o caderno atual sem
reescrever sua proveniência.

| Caminho anterior, relativo à raiz | Local atual | Estado |
|---|---|---|
| `modules/00-dataset/notebooks/srag_balance_comparison.ipynb` | [Balance comparison](00-dataset/notebooks/archive/srag_balance_comparison.ipynb) | Concluído; parâmetros fixos. |
| `modules/00-dataset/notebooks/srag_pfi_ranking.ipynb` | [PFI ranking](00-dataset/notebooks/archive/srag_pfi_ranking.ipynb) | Concluído; histórico por Brier e complementos. |
| `modules/00-dataset/notebooks/srag_course_study_walkthrough.ipynb` | [Course study walkthrough](00-dataset/notebooks/archive/srag_course_study_walkthrough.ipynb) | Interrompido antes da seleção final. |
| `modules/00-dataset/notebooks/srag_course_study_internals.ipynb` | [Course study internals](00-dataset/notebooks/archive/srag_course_study_internals.ipynb) | Auditoria do registro interrompido. |
| `modules/10-pfi/notebooks/srag_course_pfi_walkthrough.ipynb` | [Course PFI walkthrough](10-pfi/notebooks/archive/srag_course_pfi_walkthrough.ipynb) | Pendente; agregado adicional ausente. |
| `modules/10-pfi/notebooks/srag_course_pfi_internals.ipynb` | [Course PFI internals](10-pfi/notebooks/archive/srag_course_pfi_internals.ipynb) | Pendente; auditoria adicional não concluída. |

[Índice do arquivo da base](00-dataset/notebooks/archive/README.md) ·
[Índice do arquivo PFI](10-pfi/notebooks/archive/README.md).

Os verificadores e os fluxos de execução percorrem `notebooks/` recursivamente.
O arquivamento mantém as categorias de execução: arquivos terminados em
`_walkthrough.ipynb` e `_internals.ipynb` continuam automáticos; InfoGripe,
Balance comparison e PFI ranking continuam manuais. Arquivar não exclui células,
resultados, figuras publicadas ou fontes dos estudos.
