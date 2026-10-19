# GOLD.md — o cardápio de decisões

Este arquivo registra as escolhas de tarefa que produziram o Ouro, com
seu contexto e as alternativas consideradas. **As decisões já foram aplicadas.**
Os blocos datados preservam a adoção histórica; o
[`gold/MANIFEST.md`](gold/MANIFEST.md) documenta a receita efetivamente executada.
O Prata reúne o tratamento dos registros; o Ouro define o alvo, a coorte,
as entradas e a divisão dos dados para esta tarefa.

Todo número abaixo é impresso por célula de notebook commitada: a tabela
por ano vive no [internals §7](notebooks/srag_silver_internals.ipynb), o
perfil da população no internals §1, e as classes de vazamento no
[`COLUMNS.md`](COLUMNS.md), que é gerado e verificado no build.

## Decisão 1 — o alvo
> **Decidido 2026-09-01 — William.** Alvo `y_obito`, com óbito no código 2
> e cura no código 1 de `EVOLUCAO`. Os demais códigos, ignorados e vazios
> são excluídos, com contagens no [`gold/MANIFEST.md`](gold/MANIFEST.md).

“Casos fechados” é a denominação histórica desse recorte. Ela não inclui
qualquer evolução conhecida: óbito por outras causas fica fora, e não entra
como sobrevivência. A tarefa não estima mortalidade por todas as causas.

Dono: **William + o curso**. Três candidatos, com as taxas dentro da
coorte hospitalizada (internals §7):

| Candidato | Definição | Taxa 2020 → 2024 | O que vigiar |
|---|---|---|---|
| Óbito | `EVOLUCAO == 2` nos casos fechados | 27,2% → 6,7% | 7–11% dos registros nunca fecham (`EVOLUCAO` vazio/9): "casos fechados" já é uma escolha de coorte, e censura diferente por ano |
| Admissão em UTI | `UTI == 1` | 29,6% → 27,6% | a taxa mais estável entre regimes; mas `UTI` vazio é 4–15% e `DT_ENTUTI` é gated nela |
| Ventilação invasiva | `SUPORT_VEN == 1` | 14,9% → 9,6% | campo de três valores (invasiva/não invasiva/não); colapsá-lo já é decisão de modelagem |

**Escolha aplicada:** óbito nos casos fechados conforme os códigos acima.
A mudança da taxa observada (27,2% → 6,7%) integra o contexto temporal do
estudo. `EVOLUCAO` fornece o rótulo e fica excluído das entradas do modelo.

## Decisão 2 — a coorte
> **Decidido 2026-09-01 — William.** `coorte_hospitalizado` ∧ `covid_caso`
> amplo, com `rt_pcr_confirmado` de flag para o recorte estrito; janela a
> partir de 2020-02-26 (corte do estudo; o script do MS usado como referência
> não filtra por data, e o evento InfoGripe de abril/2020 não foi usado como
> filtro); todas as idades, com os limites do manifesto; nosocomiais mantidos
> como feature.

Dono: **William + o curso**.

| Opção | Tamanho (6 anos) | A favor | Contra |
|---|---|---|---|
| `coorte_hospitalizado` | 2.428.696 (59,1% dos registros) | a definição de caso do MS sem a circularidade de desfecho (o `caso_srag_ms` admite 24.475 linhas só porque o paciente morreu) | descarta notificações não hospitalizadas |
| SRAG inteira | 4.109.567 | nada descartado | mistura vias de notificação |
| só `covid_caso` | 723.677 em 2020 → 31.986 em 2024 | a pergunta pandêmica | a etiologia da base é mais ampla, e a decisão do curso (registrada em 2026-08-31) foi manter a base inteira e tratar a atipicidade da COVID como contexto |

A tabela registra as alternativas e contagens consideradas no Bronze,
antes da quarentena. A escolha aplicada combina **`coorte_hospitalizado` e
`covid_caso` amplo**, seguida dos filtros do manifesto. Manter toda a série
na origem não implica incluir todas as suas notificações na tarefa.
O ano acompanha os registros para identificar as partições e estudar a
mudança de população.

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
casos fecham *depois* da digitação, em todos os anos. Essa ordem temporal
não comprova a disponibilidade do campo no instante de uso, nem exclui
associação com o desfecho. Estar fora da classe `leakage` também não
transforma uma coluna automaticamente em entrada da Gold.

### Por que `UTI` e `SUPORT_VEN` não entram — a justificativa (2026-09-01)

**O que os campos registram.** `UTI` e `SUPORT_VEN` descrevem eventos do
episódio de hospitalização. A Ficha SRAG Hospitalizado pergunta, no campo 50,
"O paciente fez uso de suporte ventilatório?" — três valores (1 invasivo, 2 não invasivo, 3
não), **nenhuma data**, logo depois de "Data da entrada/saída na UTI" na
ficha: a ausência de data é escolha do formulário, não esquecimento. O
[`DICTIONARY.md`](DICTIONARY.md) carrega a mesma definição e mede o
preenchimento: `UTI` em 85–97% dos registros contra 25–35% de
`DT_ENTUTI` — na maioria dos casos sabe-se **que** houve UTI, não
**quando**. E o Guia do SIVEP-Gripe fecha: "A ficha só é considerada
encerrada no sistema após a inserção da evolução do caso"; sobre a
evolução, "idealmente esse campo deve ser preenchido logo após alta ou
óbito ou transferência" (§3.2). Essas instruções descrevem o encerramento
da ficha, mas não demonstram que todos os campos tenham sido digitados no
mesmo ato ou que estivessem disponíveis na admissão.

**O que a medição mostra** ([internals do modelo
§6](notebooks/srag_model_internals.ipynb), amostra commitada, parâmetros
adotados). No treino, a letalidade por nível de `SUPORT_VEN` é 76,4% no
invasivo (18,0% dos registros), 21,9% no não invasivo (55,9%) e 12,5% no
"não" (14,8%); em `UTI`, 55,3% no "sim" (33,3%) contra 17,8% no "não"
(57,4%). Somando as colunas, a AUC de teste sai de 0,7644 (as 40) para
0,8052 (+`UTI`), 0,8479 (+`SUPORT_VEN`) e 0,8514 (as duas), com o Brier
de 0,1308 para 0,1084 — Δ +0,0868 no bootstrap pareado do teste (200
reamostras, semente 42; EP 0,0038, 22,6 erros-padrão). No modelo de 42
features, `suport_ven` leva 49,5% do ganho, mais que o dobro de
`idade_anos` (23,3%). O ganho de desempenho e essas associações, isoladamente,
não demonstram vazamento. A limitação decisiva é a ausência de uma medida
alinhada ao instante de predição pretendido. O nível "não" também não distingue
as razões para não usar ventilação; as tabelas não identificam a gravidade
ou o acesso ao tratamento dentro desse grupo.

**O instante da predição orienta a avaliação dos preditores.** A questão
2.3 do PROBAST pergunta se eles estão disponíveis quando o modelo pretende
ser usado. Medições feitas mais perto do desfecho podem elevar o desempenho
aparente sem permitir o uso no instante pretendido. O item 9b do TRIPOD+AI
pede que os preditores sejam medidos antes ou no momento de uso. Wynants
et al. (2020) discutem esse problema entre as fontes de alto risco de viés
nos modelos de COVID revisados. O placar local mostra a sensibilidade do
desempenho à inclusão dessas colunas; a classificação de vazamento depende
também de sua definição e temporalidade.

**Limites da leitura causal.** Ranzani et al. (2021) descrevem diferenças
regionais de acesso e desfechos em hospitalizações por COVID no Brasil.
Um CP ou ICE que mova `suport_ven` de "não" para "invasivo" descreve a resposta
do preditor à substituição da entrada; não identifica um efeito de tratamento
nem separa gravidade, triagem e oferta de leito. van Geloven et al. (2020)
discutem como o tratamento após o instante inicial afeta o objetivo preditivo.

**As perguntas dos estudos brasileiros diferem.** Silva & Silva Neto (2022)
e de Souza et al. (2021) incluem UTI e ventilação em análises com objetivos
próprios. Baqui et al. (2021) e o ABC2-SPH (Marcolino et al., 2021) adotam
preditores ligados à admissão. Essas escolhas exigem acompanhar população,
desfecho e momento de mensuração; os resultados não são um placar diretamente
transferível ao curso. Na Gold, `saturacao` ("Saturação O2 < 95%") é uma entrada,
mas o checkbox não equivale à medida contínua SpO2/FiO2 usada no ABC2-SPH.

**Comparar estudos exige suas populações e definições.** O 4C Mortality
Score (Knight et al., 2020), com preditores de admissão, valida em AUROC
0,767 — e o XGBoost comparativo do mesmo trabalho, em 0,779. As nossas
40 features dão 0,7644 no teste ([`MODEL.md`](MODEL.md)); a inclusão das
colunas do episódio dá 0,8514. Esses valores mantêm sua procedência própria.
Uma AUC próxima entre estudos não comprova equivalência de tarefa, ausência
de viés ou validade clínica do modelo do curso.

**Correção de interpretação:** a redação anterior dizia "mesma pergunta,
mesma ordem de grandeza" e usava essa aproximação como justificativa da
adequação do modelo. A comparação de AUCs entre coortes não sustenta essa
conclusão.

**Outros instantes de predição exigem outro alinhamento temporal.** O SAPS 3
e os modelos de landmark definem um instante de avaliação e exigem preditores
alinhados a ele. Nesta extração, `SUPORT_VEN` não tem data própria e `DT_ENTUTI`
está numa minoria dos registros. Não foi demonstrado aqui o alinhamento
necessário para esses enquadramentos; essa limitação se refere à aplicação
estudada, não a todo possível estudo no SIVEP-Gripe.

**Decisão.** O modelo do curso mantém os 40 preditores; `UTI` e
`SUPORT_VEN` seguem na classe `leakage`. A referência é retrospectiva, e a
disponibilidade dos demais preditores na admissão também exige avaliação.
A exclusão dessas colunas, sozinha, não valida uso prospectivo.

#### Referências

- Ministério da Saúde. *Dicionário de Dados — Ficha SRAG Hospitalizado*
  (31/03/2020), campo 50.
  <http://www.cosemssp.org.br/wp-content/uploads/2020/07/Dicionario-de-Dados-SRAG-Hospitalizado_31_03_2020.pdf>
- Ministério da Saúde. *Guia do SIVEP-Gripe (SRAG)*, §3.2.
  <https://saude.es.gov.br/media/Imuniza%C3%A7%C3%A3o/Guia%20do%20SIVEP-%20GRIPE%20%20-%20Vigil%C3%A2ncia%20de%20influenza%20(SRAG).pdf>
- Wolff RF et al. (2019). PROBAST: explanation and elaboration.
  *Ann Intern Med* 170:W1–W33.
  <https://www.probast.org/wp-content/uploads/2020/02/aime201901010-m181377.pdf>
- Collins GS et al. (2024). TRIPOD+AI statement. *BMJ* 385:e078378.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/>
- Wynants L et al. (2020). Prediction models for diagnosis and prognosis of
  covid-19: systematic review and critical appraisal. *BMJ* 369:m1328.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC7222643/>
- Knight SR et al. (2020). 4C Mortality Score. *BMJ* 370:m3339.
  <https://api.repository.cam.ac.uk/server/api/core/bitstreams/46708bd7-5816-4c02-9edd-1612e8cf5e28/content>
- Ranzani OT et al. (2021). Characterisation of the first 250 000 hospital
  admissions for COVID-19 in Brazil. *Lancet Respir Med* 9:407–418.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC7834889/>
- Silva & Silva Neto (2022). Predição sobre o SIVEP-Gripe com `SUPORT_VEN`
  e `UTI`. *Saúde em Debate* 46(spe8):118–129, doi 10.1590/0103-11042022E809.
  <https://www.scielo.br/j/sdeb/a/DwTh6QXxcQwX6MwJkztftvr/?format=html&lang=pt>
- de Souza et al. (2021). Fatores de risco sobre o SIVEP-Gripe. *PLOS ONE*
  e0248580, doi 10.1371/journal.pone.0248580.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC7971705/>
- Baqui P et al. (2021). XGBoost sobre o SIVEP-Gripe (2020) só com variáveis
  de admissão. *Sci Rep* 11:15591, doi 10.1038/s41598-021-95004-8.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC8329284/>
- Marcolino MS et al. (2021). Escore ABC2-SPH. *Int J Infect Dis*,
  doi 10.1016/j.ijid.2021.07.049. <https://pubmed.ncbi.nlm.nih.gov/34311100/>
- van Geloven N et al. (2020). Prediction meets causal inference: the role of
  treatment in clinical prediction models. *Eur J Epidemiol* 35:619–630.
  <https://arxiv.org/pdf/2004.06998>
- Liu V et al. (2013). Variáveis do SAPS 3 (primeira hora após a admissão em
  UTI), material suplementar. *Crit Care Med*.
  <https://cdn-links.lww.com/permalink/ccm/a/ccm_41_1_2012_07_11_liu_204007_sdc1.pdf>

## Decisão 4 — anos e split
> **Decidido 2026-09-01 — William.** Holdout temporal: treino até
> 2022-12-31, validação 2023, teste 2024 — contagens no MANIFEST §2.4.

Dono: **William + o curso**.

A população não é estacionária: letalidade 29,0% → 8,6%, fração COVID
70,2% → 11,6%, idade mediana 5,8 → 60,7 → 8,0 entre os regimes (Silver
internals §1 e §6). As alternativas consideradas foram:

1. **Holdout temporal, adotado** — treino até 2022, validação 2023 e teste
   2024. Avalia períodos posteriores ao treino. A mudança de distribuição
   acompanha a interpretação dos resultados.
2. Split estratificado dentro do ano — responde a uma avaliação interna ao
   período; pode servir ao estudo da mecânica dos métodos.
3. Recorte de regime (ex.: só 2023–2024) — disponível para outra pergunta,
   com uma coorte e um protocolo próprios.

**Correção do registro:** a primeira opção dizia "treina ≤ 2023, testa 2024".
A receita aplicada reserva 2023 para validação e limita o treino a 2022,
como no bloco de decisão e no manifesto. O teste histórico já foi observado;
a separação temporal não o torna uma confirmação independente.

## Decisão 5 — codificação
> **Decidido 2026-09-01 — William** (construído variável a variável, com
> prós e contras — o registro completo das escolhas de features está no
> MANIFEST §2.5, incluindo o fold declarado dos três estados em
> `desconhecido` e as decisões que este cardápio não previu, §2.8).

Dono: **convenção adotada, com aplicação registrada no manifesto.**

A lista abaixo reúne os critérios do cardápio. A lista efetiva de entradas
e sua codificação são as do MANIFEST §2.5; pertencer a uma classe admitida
não implica que toda coluna dessa classe tenha entrado no modelo.

- O Prata distingue os três estados do vazio. No Ouro aplicado, eles são
  fundidos em `desconhecido`, com a compressão e seus diagnósticos declarados
  no manifesto. `nao_aplicavel` registra o funil, não uma resposta clínica negativa.
- Checkboxes entram como booleanos (`_marcado`); as flags `_caso` são
  fatos e podem entrar; as variantes `_unico` são para contagem de
  vigilância, não para feature.
- Colunas vazias em algum ano (`year_gated`, 21 no levantamento) podem
  carregar disponibilidade do formulário. O cardápio propunha excluí-las
  ou declarar seu uso junto do ano; a seleção aplicada está no manifesto.
- `code_pair`: fica o lado do código (joinável), sai o lado do nome.
- `free_text` e `identifier`: excluídos. `FAB_*` entra por
  `_fabricante` (vocabulário de 8 valores), nunca cru.
- Idade: `idade_anos` (derivada das datas). `NU_IDADE_N` sem `TP_IDADE`
  é armadilha conhecida; `COD_IDADE` normalmente repete a composição dos
  outros dois campos, com exceções auditadas no Silver internals §3.
  A redação anterior, “identidade exata”, generalizava essa relação sem
  ressalvas. Essa redundância não cria entradas adicionais na Gold aplicada.

## O que o Ouro materializou

A receita é executada por [`tools/srag_40_gold.py`](../../tools/srag_40_gold.py), que
recebe **cada decisão como flag obrigatória** (rodar sem flags imprime
este cardápio e sai), constrói `gold_covid_obito.parquet`
(1.282.970 × 50: 40 features + escrituração + diagnósticos) e escreve o
[`gold/MANIFEST.md`](gold/MANIFEST.md) — função pura de `counts.json` +
decisões, verificada por hook, com o funil na ordem, os NA absorvidos por
cada fill e as decisões que este cardápio não previu (§2.8 de lá:
NOSOCOMIAL vazio, as 772+3 idades, as RAs do DF, sem pesos de classe,
semana ordinal).
