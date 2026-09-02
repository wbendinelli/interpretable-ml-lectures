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

### Por que `UTI` e `SUPORT_VEN` não entram — a justificativa (2026-09-01)

**O que o campo é.** São os dois campos clinicamente mais fortes da
ficha, e a pergunta "se predizem tanto, por que ficam fora?" é legítima.
A Ficha SRAG Hospitalizado pergunta, no campo 50, "O paciente fez uso de
suporte ventilatório?" — três valores (1 invasivo, 2 não invasivo, 3
não), **nenhuma data**, logo depois de "Data da entrada/saída na UTI" na
ficha: a ausência de data é escolha do formulário, não esquecimento. O
[`DICTIONARY.md`](DICTIONARY.md) carrega a mesma definição e mede o
preenchimento: `UTI` em 85–97% dos registros contra 25–35% de
`DT_ENTUTI` — na maioria dos casos sabe-se **que** houve UTI, não
**quando**. E o Guia do SIVEP-Gripe fecha: "A ficha só é considerada
encerrada no sistema após a inserção da evolução do caso"; sobre a
evolução, "idealmente esse campo deve ser preenchido logo após alta ou
óbito ou transferência" (§3.2). O campo é resumo do episódio, digitado
no mesmo ato que digita o rótulo.

**O que a medição mostra** ([internals do modelo
§6](notebooks/srag_model_internals.ipynb), amostra commitada, parâmetros
adotados). No treino, a letalidade por nível de `SUPORT_VEN` é 76,4% no
invasivo (18,0% dos pacientes), 21,9% no não invasivo (55,9%) e 12,5% no
"não" (14,8%); em `UTI`, 55,3% no "sim" (33,3%) contra 17,8% no "não"
(57,4%). Somando as colunas, a AUC de teste sai de 0,7644 (as 40) para
0,8052 (+`UTI`), 0,8479 (+`SUPORT_VEN`) e 0,8514 (as duas), com o Brier
de 0,1308 para 0,1084 — Δ +0,0868 no bootstrap pareado do teste (200
reamostras, semente 42; EP 0,0038, 22,6 erros-padrão). No modelo de 42
features, `suport_ven` leva 49,5% do ganho, mais que o dobro de
`idade_anos` (23,3%). Nenhum fator de risco de admissão se comporta
assim; o desfecho, sim. E o nível "não" mistura o paciente leve que
nunca precisou de ventilação com o grave a quem ela não foi oferecida —
prognósticos opostos no mesmo código.

**O critério não é o tamanho do ganho, é o instante da predição.** A
questão 2.3 do PROBAST — "todos os preditores estão disponíveis no
momento em que o modelo pretende ser usado?" — diz que incluir preditores
indisponíveis nesse instante torna o modelo inutilizável *e* infla o
desempenho aparente, "porque tais preditores são medidos mais perto no
tempo da avaliação do desfecho". O item 9b do TRIPOD+AI repete a regra
("predictors should be measured before or at the time the model is
intended to be used"), e Wynants et al. (2020) atribuíram a essa causa
parte do alto risco de viés dos modelos de COVID que revisaram — o
placar acima é a demonstração local desse achado.

**O confundimento por capacidade instalada torna a leitura causal
impossível.** Ranzani et al. (2021) mediram, nas primeiras 250 mil
internações por COVID no Brasil, 80% de letalidade entre os ventilados
mecanicamente (36.046 de 45.205), com o Sudeste tendo cerca do dobro de
leitos de UTI por habitante do Norte e, entre ventilados com menos de 60
anos, 77% de óbitos no Nordeste contra 55% no Sul. Um CP ou ICE que mova
`suport_ven` de "não" para "invasivo" não mostraria efeito de
tratamento: mostraria triagem, gravidade não medida e oferta de leito.
van Geloven et al. (2020) dão o nome certo — tratamento pós-baseline é
evento intercorrente, tratado pela escolha do estimando, não jogado como
covariável.

**A literatura brasileira está dividida, e a divisão é informativa.**
Silva & Silva Neto (2022) mantêm as duas colunas — `SUPORT_VEN` com
importância 0,46 (≈3× a idade), `UTI` com 0,27, AUC 0,75 —, reconhecendo
a circularidade em texto e seguindo com elas; de Souza et al. (2021)
usam ventilação invasiva (HR 3,88) e UTI (HR 1,25) num estudo de
**fatores de risco**, não de predição na admissão (C-index 0,74). Do
outro lado, Baqui et al. (2021) treinam XGBoost no mesmo banco só com
variáveis de admissão, sem as duas, e chegam a AUC 0,813; e o ABC2-SPH
(Marcolino et al., 2021) as exclui **por desenho**, pondo no lugar
SpO2/FiO2 na apresentação — AUROC 0,844 na derivação, 0,859 na
validação. Fisiologia da admissão no lugar do desfecho; nosso
equivalente grosseiro é o checkbox `saturacao` ("Saturação O2 < 95%"),
que já é feature.

**O modelo do curso está na faixa certa da pergunta certa.** O 4C
Mortality Score (Knight et al., 2020), só com preditores de admissão,
valida em AUROC 0,767 — e o XGBoost comparativo do mesmo trabalho, em
0,779. As nossas 40 features dão 0,7644 no teste
([`MODEL.md`](MODEL.md)): mesma pergunta, mesma ordem de grandeza. Os
0,8514 não são um modelo melhor da mesma pergunta; são um modelo de
outra pergunta.

**Há enquadramentos legítimos em que ventilação É preditor — e o
SIVEP-Gripe não sustenta nenhum.** O SAPS 3 usa variáveis da primeira
hora após a admissão em UTI, ventilação incluída, porque ali o instante
da predição é a entrada na UTI, não a entrada no hospital; modelos de
landmark predizem a partir do dia *t* condicionando na sobrevida até
*t*. Ambos exigem saber **quando** cada coisa aconteceu — e `SUPORT_VEN`
não tem data nenhuma, `DT_ENTUTI` está numa minoria dos registros.

**Decisão.** O modelo do curso mantém os 40 preditores; `UTI` e
`SUPORT_VEN` seguem na classe `leakage`. Um modelo com essas colunas
responderia "quem morreu?", não "quem vai morrer?".

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

A ferramenta existe: [`tools/srag_40_gold.py`](../../tools/srag_40_gold.py)
recebe **cada decisão como flag obrigatória** (rodar sem flags imprime
este cardápio e sai), constrói `gold_covid_obito.parquet`
(1.282.970 × 50: 40 features + escrituração + diagnósticos) e escreve o
[`gold/MANIFEST.md`](gold/MANIFEST.md) — função pura de `counts.json` +
decisões, verificada por hook, com o funil na ordem, os NA absorvidos por
cada fill e as decisões que este cardápio não previu (§2.8 de lá:
NOSOCOMIAL vazio, as 772+3 idades, as RAs do DF, sem pesos de classe,
semana ordinal).
