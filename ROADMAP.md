# ROADMAP — todos os métodos do Molnar, sobre uma base só

O curso aplica os métodos do *Interpretable Machine Learning* do Molnar
(3ª edição — capítulos verificados contra o livro vivo; os módulos 01–03
já citam os capítulos 12–14) a um único dataset: a base SRAG /
SIVEP-Gripe que o módulo 00 trata, documenta e contrata.

## A tese organizadora

O módulo 00 mediu a estrutura que faz desta base um **argumento**, não só
um caso: a ficha desliga campos condicionalmente (34 portões confirmados;
o funil de comorbidade segura 0,00% de contradição nos seis anos), então
as features são **conjuntamente restritas**. Todo método que perturba,
varre ou permuta features *de forma independente* — ceteris paribus, ICE,
LIME, PDP, Shapley marginal, permutation importance, anchors — fabrica
pacientes que não podem existir: uma comorbidade marcada com `FATOR_RISC`
dizendo que não há nenhuma, um subtipo sem triagem positiva. Os capítulos
construídos para escapar dessa suposição — ALE, e SHAP na forma
condicional — são onde o curso aterrissa.

A base ainda carrega três armadilhas nomeadas que os módulos vão reusar:

- **Uma redundância exata**: `COD_IDADE` = `TP_IDADE` +
  `zfill(NU_IDADE_N, 3)` em 100,00% — a importância se divide
  arbitrariamente entre as duas, por construção (as 20 exceções em 4,1 M,
  todas idades negativas, são impressas pela checagem
  `conf-comp-cod-idade` do QUALITY.md).
- **Calendários disfarçados**: 21 colunas são 100% vazias em algum ano;
  um modelo que não recebe o tempo ainda lê o ano na revisão do
  formulário.
- **Deriva de regime como sinal**: letalidade 29,0% → 8,6% entre
  2020–2024 — uma explicação que revela "ano" está *correta*, e os
  módulos vão poder dizer isso.

## O mapa

Status: ✅ disponível (sobre o modelo do curso — ver bandeira 2) ·
🔜 planejado · ⛔ não se aplica a esta base.

| Cap. Molnar | Método | Status | O estudo na base SRAG | Restrições em 4,1 M × 420 |
|---:|---|---|---|---|
| 6 | Regressão linear | 🔜 | baseline na coorte; a multicolinearidade das comorbidades desestabiliza coeficientes — medido, não afirmado. Prévia medida no estudo de seleção do módulo 00 (o LPM e sua patologia fora de [0,1]) | trivial |
| 7 | Regressão logística | 🔜 | o primeiro modelo do alvo; coeficientes vs o funil. Prévia medida no estudo de seleção do módulo 00 (C tunado na validação temporal) | trivial |
| 8 | GLM / GAM | 🔜 | efeito não linear da idade no óbito — o U que os regimes movem. Fora do estudo de seleção do módulo 00, de propósito: vira módulo próprio | seleção de termos exige cuidado |
| 9 | Árvore de decisão | 🔜 | tratamento nativo do vazio vs os três estados. Prévia medida no estudo de seleção do módulo 00 (profundidade/poda tunadas) | ok |
| 10 | Regras de decisão | 🔜 | regras sobre checkboxes; a tentação do vazamento de ano. Fora do estudo de seleção do módulo 00, de propósito: vira módulo próprio | pré-seleção de features |
| 11 | RuleFit | 🔜 | geração de regras em subamostra. Fora do estudo de seleção do módulo 00, de propósito: vira módulo próprio | subamostrar |
| 12 | Ceteris paribus | ✅ reescrito (2026-09-01) | varrer uma comorbidade com 140 congeladas: contar pacientes impossíveis pelos portões | barato |
| 13 | ICE | ✅ reescrito (2026-09-01) | heterogeneidade por regime — curvas coloridas por ano | subamostrar pacientes |
| 14 | LIME | ✅ reescrito (2026-09-01) | perturbação vs o funil (o módulo BCW já mediu ~75% de sintéticos impossíveis no mesmo esquema) | explicar uma amostra |
| 15 | Contrafactuais | ✅ (módulo 04, 2026-09-01) | "o que teria de mudar" sob as restrições dos portões — imutáveis (idade, ano) declarados | por instância |
| 16 | Anchors | 🔜 | SE-ENTÃO sobre checkboxes; o mesmo risco de amostragem do LIME | subamostrar |
| 17 | Valores de Shapley | ✅ (módulo 05, com o 18) | exato é 2^420; a escolha da aproximação É a lição | só aproximado |
| 18 | SHAP | ✅ (módulo 05, 2026-09-01) | TreeSHAP no modelo do curso; interventional vs path-dependent sobre o funil | eficiente |
| 19 | PDP | 🔜 | efeito médio vs as pontas fora da variedade | subamostra de fundo |
| 20 | ALE | 🔜 | **o capítulo-remédio** — condicionamento local respeita o funil; checkboxes sem ordem exigem uma escolha de ordenação | bins por quantil, ok |
| 21 | Interação (H) | 🔜 | idade × ano, vacina × regime | ~87 mil pares — restringir + subamostrar |
| 22 | Decomposição funcional | teoria | ler junto de 19–21 | — |
| 23 | Permutation importance | 🔜 | permutar um membro do par exato (`COD_IDADE`) — a arbitrariedade, exibida | subamostra de holdout |
| 24 | LOFO | 🔜 | p re-treinos — o capítulo mais caro; features agrupadas (as famílias!) como saída | pesado: agrupar + subamostrar |
| 25 | Surrogates globais | 🔜 | fidelidade (R²) lida com o ceticismo do próprio módulo 03 | subamostrar |
| 26 | Protótipos e críticas | 🔜 | quem é o paciente típico de 2021; distância de Gower para tipos mistos | O(N²) — coresets |
| 27–30 | Features aprendidas / saliência / TCAV / adversarial | ⛔ | específicos de imagem e rede neural | — |
| 31 | Instâncias influentes | 🔜 | as sete linhas da quarentena vs as realmente influentes | diagnóstico de deleção: amostrar |
| 32 | Avaliação de interpretabilidade | teoria | a barra de evidência do próprio repositório, formalizada | — |

Doze módulos de método planejados além dos cinco existentes; quatro
capítulos excluídos com o motivo declarado.

## Etapas

1. **Prata completo** — feito (PR #14): 194/194 colunas com regra,
   contrato verificado, três falsificações no registro.
2. **Validação externa + este mapa + o cardápio do Ouro** — este PR.
3. **Loader do Prata no Postgres/Metabase** — próximo PR, para o
   tratamento ser navegável.
4. **Decisões do Ouro** — William + professor escolhem alvo, coorte e
   split (o cardápio é o
   [`modules/00-dataset/GOLD.md`](modules/00-dataset/GOLD.md)); então
   `tools/srag_40_gold.py` materializa com manifesto.
5. **O módulo do modelo do curso** — um modelo, um split, um paciente,
   compartilhados por todos os módulos de método (o padrão RandomForest +
   paciente #67 da série BCW, agora sobre SRAG).
6. **Módulos de método**, na ordem de dependência da tabela: modelos
   interpretáveis primeiro (6–11), as reescritas (12–14), depois o arco
   agnóstico de modelo (19, 20, 23, 18, 17, 15, 16, 21, 24, 25, 26, 31).

## Convenções de módulo (restrições já em vigor)

Numeração sequencial própria deste repositório; cada módulo nomeia seu
capítulo no README. Estrutura do `modules/_template/`: README com a ordem
fixa de seções, `lecture/outline.md`, dois notebooks
(`<slug>_walkthrough`, `<slug>_internals`), `RANDOM_STATE = 42`, figuras
promovidas por cópia explícita, outputs commitados após rodada de kernel
limpo, e linha adicionada à mão na tabela do README raiz. Todo número em
prosa é impresso por célula commitada no mesmo módulo.

## Duas bandeiras, registradas para não se resolverem em silêncio

1. **A exigência de COVID nunca foi confirmada com o professor.** O
   William preferiria estudar saúde mental; nada no repositório força
   COVID (o recorte COVID dos módulos 00–05 é uma flag do
   `srag_40_gold.py`, não um compromisso da base). A base mantém todas as etiologias de SRAG exatamente para
   isso continuar sendo um recorte do Ouro, não um compromisso de
   fundação. Perguntar é mais barato que reescrever.
2. **Resolvida em 2026-09-01: os módulos 01–03 rodavam sobre o Breast
   Cancer Wisconsin.** O modelo do curso existe (módulo 00), os três
   módulos foram reescritos sobre ele e os módulos 04 (contrafactuais) e
   05 (SHAP) nasceram direto no caso COVID. A versão BCW de 01–03 vive no
   histórico do git. Segunda rodada, em 2026-09-02: o estudo de
   seleção trocou os hiperparâmetros do modelo (PR #29) e os cinco módulos
   foram re-sincronizados número a número sobre o modelo adotado — os
   deslocamentos de condicionamento registrados numa nota por módulo, as
   afirmações falsificadas corrigidas uma a uma no texto.
