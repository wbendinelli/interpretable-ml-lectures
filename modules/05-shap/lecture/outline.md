# Aula — SHAP no modelo COVID (forma viva)

> Módulo novo (2026-09-01), direto sobre o modelo do curso — não há deck
> histórico; esta é a única forma da aula. Figuras em `../figures/`;
> todo número abaixo é impresso por `shap_walkthrough.ipynb` ou
> `shap_internals.ipynb`.

**Objetivos.** Ao final, a turma deve saber enunciar o jogo, o ganho e
os quatro axiomas (com a eficiência verificada, não assumida); ler os
cinco gráficos clássicos apontando o que é axioma e o que é estimativa;
dar a interpretação correta de um φ e desarmar as três leituras erradas;
e distinguir caminho × intervenção com o custo medido.

---

## 1. Do jogo à floresta (8 min)

Shapley (1953) em uma frase: a média do efeito marginal do jogador sobre
todas as ordens de chegada. Molnar (cap. 17): o jogo é a predição desta
instância, o ganho é f(x) menos a média, os jogadores são os valores das
features. Escrever a fórmula, apontar o fatorial, e dizer o preço: 2⁴⁰
coalizões — impraticável — e por isso TreeSHAP (exato em árvores,
`pred_contribs`) e estimadores por amostragem.

Os 4 axiomas com as citações do cap. 17; a eficiência já verificada:
desvio 1,05×10⁻⁵ em 16.142 pacientes; refits bit-idênticos; dummy testado
(vácuo honesto — as 40 features aparecem em divisão; internals §1).

*Configuração declarada:* margem, não probabilidade (é onde somar 800
árvores faz sentido); sem a lib `shap` (pin — a decisão e o critério de
falsificação estão no PR); os gráficos refeitos na mão.

## 2. Waterfall e force (10 min)

`shap_passo_1_waterfall.png`: partir da base (−0,79; sigmoide 0,31 ≈
prevalência do treino, internals §2) e somar até f(x). Para o
paciente-regra (p = 0,5000) é um cabo de guerra que empata: idade +0,92,
vacinação −0,36, calendário −0,32, zona desconhecida +0,16. **Apontar:
as barras somam exatamente — axioma, não ajuste.**

`shap_passo_2_force.png`: o mesmo objeto deitado — +1,86 contra −1,07,
encontro em f(x). É o formato que empilha para o global.

*Objeção que vem:* "0,50 é o modelo em dúvida — a explicação vale?"
Resposta: a atribuição explica a MARGEM, e o empate é informação: quais
forças se cancelam neste paciente (é o que o painel mostra).

## 3. SHAP × LIME, e a interpretação correta (8 min)

`shap_passo_3_vs_lime.png`: mesmo paciente do módulo 03; 7/8 sinais
concordam; a divergência (meses) é a feature que o 03 mediu como plano
no CP/ruído. **A frase do cap. 17 para levar:** φ é "a contribuição
deste valor de feature em relação à predição média" — não é
contrafactual, não é causal, não é "aumentar a feature aumenta p".

## 4. O global como soma de locais (8 min)

`shap_passo_4_global.png` (bar + beeswarm): "os φ são o átomo das
interpretações globais" (cap. 18). Apontar: idade com gradiente limpo;
vacina em dois grumos (declarada = φ negativo); e **meses 3º por
média|SHAP| contra 19º por gain** — importância para prever 2024 ≠
importância para construir árvores em 2020–22 (a deriva do módulo 02).

## 5. Dependence plots — a interação em cor (12 min)

`shap_passo_5_dependencia.png` (amostra inteira, 2020–2024 — o teste só
cobre 2024 e a interação é entre eras, dito no título):

- φ(idade): a curva abre em duas bandas nos idosos — na faixa 78–90
  anos que a célula imprime, mesma idade, +0,90 antes de mar/2022 vs
  +0,69 depois. A dispersão vertical É a interação (idade × meses, o
  par mais forte por `pred_interactions`, internals §3).
- **O painel-armadilha**: φ(doses) positivo nos vacinados (+0,08 em 3+
  doses). Deixar a sala reagir; então desarmar: o crédito protetor mora
  na declaração colinear (grumo do passo 4); doses sobra marcando os
  grupos priorizados. φ>0 ≠ "aumentar aumenta p" — e o módulo 04 MEDIU o
  contrafactual dessa pergunta (subir doses quase não move p).
- O que não há no painel: azul-escuro (pré-campanha) fora de doses = 0 —
  o dado real respeita a cerca que os vizinhos do módulo 03 violavam.

*Prompt de discussão:* qual dos cinco gráficos você mostraria ao comitê
de ética — e qual NUNCA mostraria sem este slide junto?

## 6. Caminho × intervenção, e o fechamento do curso (9 min)

`shap_passo_6_interventional.png`: o cap. 18 registra que o default do
pacote virou interventional; o nosso `pred_contribs` é path-dependent.
Na mão (Štrumbelj & Kononenko 2014): direções batem, magnitudes divergem
onde há correlação (idade +0,92 → +1,03), e o Monte Carlo centra em
OUTRA resposta (internals §4) — condicionais diferentes, não erro.

O preço do interventional, contado: 23,1% das 2.460 linhas híbridas são
pacientes impossíveis pela mesma `gate_impossible` (portão 15,4%). O
curso fecha na pergunta em que abriu — quem são as linhas — e na tabela
dos cinco métodos (walkthrough, fechamento).

A frase final é a da casa: explicar um modelo é, antes de tudo, saber o
que você acabou de dar de comer a ele.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo; os de base
cheia, pelo internals do modelo (módulo 00).

Todos foram remedidos no modelo do curso adotado em 2026-09-01 (800
árvores, profundidade 4, lr 0,05 — módulo 00, `SELECTION.md`); a versão
anterior desta aula os media no modelo de 400 árvores / profundidade 5,
e o paciente-regra era outro (gold_id 1269214). Deslocamento de
condicionamento, não falsificação — exceto a linha abaixo.

**Corrigidos nesta revisão:**

- posto de `meses` por gain — dizia 16º, mede 19º (shap_walkthrough §4).
