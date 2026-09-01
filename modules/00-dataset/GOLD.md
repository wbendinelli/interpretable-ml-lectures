# GOLD.md — o cardápio de decisões

O Prata afirma fatos; o Ouro faz escolhas de tarefa. Este arquivo é o
cardápio dessas escolhas — cada uma com a evidência medida, uma
recomendação e um dono. **Nenhuma é tomada aqui.** Enquanto não forem,
nenhum módulo treina modelo sobre a base — e é essa abstenção que permite
~20 módulos compartilharem um único Prata.

Todo número abaixo é impresso por célula de notebook commitada: a tabela
por ano vive no [internals §7](notebooks/srag_silver_internals.ipynb), o
perfil da população no internals §1, e as classes de vazamento no
[`COLUMNS.md`](COLUMNS.md), que é gerado e verificado no build.

## Decisão 1 — o alvo
> **Decidido 2026-09-01 — William.** Óbito nos casos fechados. Os
> registros que nunca fecham saem do Ouro, contados no funil do
> [`gold/MANIFEST.md`](gold/MANIFEST.md).

Dono: **William + o curso**. Três candidatos, com as taxas dentro da
coorte hospitalizada (internals §7):

| Candidato | Definição | Taxa 2020 → 2024 | O que vigiar |
|---|---|---|---|
| Óbito | `EVOLUCAO == 2` nos casos fechados | 27,2% → 6,7% | 7–11% dos registros nunca fecham (`EVOLUCAO` vazio/9): "casos fechados" já é uma escolha de coorte, e censura diferente por ano |
| Admissão em UTI | `UTI == 1` | 29,6% → 27,6% | a taxa mais estável entre regimes; mas `UTI` vazio é 4–15% e `DT_ENTUTI` é gated nela |
| Ventilação invasiva | `SUPORT_VEN == 1` | 14,9% → 9,6% | campo de três valores (invasiva/não invasiva/não); colapsá-lo já é decisão de modelagem |

Recomendação: **óbito nos casos fechados** — é o desfecho que o produto
oficial conta (toda variante `_obito` existe para ser comparada), e a
deriva de regime (27,2% → 6,7%) é material de aula, não incômodo. Seja
qual for a escolha: `EVOLUCAO` é o rótulo e **nunca** feature — encabeça a
classe de vazamento.

## Decisão 2 — a coorte
> **Decidido 2026-09-01 — William.** `coorte_hospitalizado` ∧ `covid_caso`
> amplo, com `rt_pcr_confirmado` de flag para o recorte estrito; janela a
> partir de 2020-02-26 (não existe corte oficial — o script do MS não
> filtra por data; o evento InfoGripe de abril/2020 é referência, não
> filtro); todas as idades; nosocomiais mantidos como feature.

Dono: **William + o curso**.

| Opção | Tamanho (6 anos) | A favor | Contra |
|---|---|---|---|
| `coorte_hospitalizado` | 2.428.696 (59,1% dos registros) | a definição de caso do MS sem a circularidade de desfecho (o `caso_srag_ms` admite 24.475 linhas só porque o paciente morreu) | descarta notificações não hospitalizadas |
| SRAG inteira | 4.109.567 | nada descartado | mistura vias de notificação |
| só `covid_caso` | 723.677 em 2020 → 31.986 em 2024 | a pergunta pandêmica | a etiologia da base é mais ampla, e a decisão do curso (registrada em 2026-08-31) foi manter a base inteira e tratar a atipicidade da COVID como contexto |

Recomendação: **`coorte_hospitalizado`**, com o ano mantido como coluna
explícita — regime se modela ou se estratifica, nunca se esconde.

## Decisão 3 — a exclusão por vazamento
> **Decidido 2026-09-01 — William** (default proposto aceito). Lista
> gerada da classe `leakage`; imagem fora com célula-armadilha no
> notebook do modelo.

Dono: **convenção — default proposto, gerado, não digitado.**

As classes tornam a lista *gerável*: 11 colunas cruas com
`classe = leakage` no `COLUMNS.md` (`EVOLUCAO`, `DT_EVOLUCA`,
`DT_ENCERRA`, `UTI`, `DT_ENTUTI`, `DT_SAIDUTI`, `SUPORT_VEN`,
`CLASSI_FIN`, `CLASSI_OUT`, `CRITERIO`, `VG_ENC`) e 39 derivadas que a
herdam (as 36 variantes `_obito*`, `dias_uti`, `dias_ate_internacao`,
`caso_srag_ms`). Se o alvo for UTI em vez de óbito, a lista **muda** —
`UTI` vira rótulo e tudo que decorre da admissão se move — e é exatamente
por isso que a exclusão tem de ser derivada da escolha do alvo, nunca
copiada.

Medido e deliberadamente **fora** da lista: `DT_DIGITA` — 63–69% dos
casos fecham *depois* da digitação, em todos os anos; a data de entrada
não codifica o desfecho.

## Decisão 4 — anos e split
> **Decidido 2026-09-01 — William.** Holdout temporal: treino até
> 2022-12-31, validação 2023, teste 2024 — contagens no MANIFEST §2.4.

Dono: **William + o curso**.

A população não é estacionária: letalidade 29,0% → 8,6%, fração COVID
70,2% → 11,6%, idade mediana 5,8 → 60,7 → 8,0 entre os regimes (README do
módulo; internals §1 e §6). Opções:

1. **Holdout temporal** — treina ≤ 2023, testa 2024. Analogia honesta com
   implantação; a deriva vira achado que os módulos de interpretabilidade
   mostram. *(Recomendado.)*
2. Split estratificado dentro do ano — ilusão i.i.d., mas útil para
   módulos de mecânica de método.
3. Recorte de regime (ex.: só 2023–2024) — já rejeitado uma vez para a
   base (decisão registrada: manter a base crua), mas disponível por
   módulo se a pergunta exigir.

## Decisão 5 — codificação
> **Decidido 2026-09-01 — William** (construído variável a variável, com
> prós e contras — o registro completo das escolhas de features está no
> MANIFEST §2.5, incluindo o fold declarado dos três estados em
> `desconhecido` e as decisões que este cardápio não previu, §2.8).

Dono: **convenção — defaults propostos.**

- Os três estados do vazio são **categorias**, nunca imputados em
  silêncio: `nao_aplicavel` é informação (o funil), não ausência.
- Checkboxes entram como booleanos (`_marcado`); as flags `_caso` são
  fatos e podem entrar; as variantes `_unico` são para contagem de
  vigilância, não para feature.
- Colunas `year_gated` são calendários disfarçados (21): excluídas por
  default, ou mantidas só com o ano explicitamente presente, para o
  modelo não usar disponibilidade de formulário como proxy.
- `code_pair`: fica o lado do código (joinável), sai o lado do nome.
- `free_text` e `identifier`: excluídos. `FAB_*` entra por
  `_fabricante` (vocabulário de 8 valores), nunca cru.
- Idade: `idade_anos` (derivada das datas). `NU_IDADE_N` sem `TP_IDADE`
  é armadilha conhecida; `COD_IDADE` é identidade exata dos outros dois —
  um dos pares redundantes que os módulos de importância vão exibir.

## O que o Ouro materializou

A ferramenta existe: [`tools/srag_gold.py`](../../tools/srag_gold.py)
recebe **cada decisão como flag obrigatória** (rodar sem flags imprime
este cardápio e sai), constrói `gold_covid_obito.parquet`
(1.282.970 × 50: 40 features + escrituração + diagnósticos) e escreve o
[`gold/MANIFEST.md`](gold/MANIFEST.md) — função pura de `counts.json` +
decisões, verificada por hook, com o funil na ordem, os NA absorvidos por
cada fill e as decisões que este cardápio não previu (§2.8 de lá:
NOSOCOMIAL vazio, as 772+3 idades, as RAs do DF, sem pesos de classe,
semana ordinal).
