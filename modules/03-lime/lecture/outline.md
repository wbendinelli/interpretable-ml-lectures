# Aula — LIME no modelo COVID (forma viva)

> Reescrita 2026-09-01 sobre o modelo do curso. Figuras referenciadas por
> nome em `../figures/`. Todo número abaixo é impresso por
> `lime_walkthrough.ipynb` ou `lime_internals.ipynb`; os marcadores
> `(walkthrough §N)` / `(internals §N)` apontam para dentro deles. Os
> decks PDF desta pasta são o registro do seminário da era BCW
> (2026-08-24) e não são retro-editados.

**Objetivos.** Ao final, a turma deve saber enunciar o que o LIME otimiza
e nomear cada termo; seguir o mecanismo de ponta a ponta na figura A–F;
contar as duas contaminações da vizinhança (gramática vs biologia) e
dizer qual delas `categorical_features` conserta; e dizer que parte da
explicação merece confiança, em que escala, citando a medição.

---

## 1. Motivação — falada, não projetada

Noventa segundos antes do método. O modelo do curso acerta AUC 0,7644 no
teste da amostra deste módulo (walkthrough, célula de setup) e 0,7680 na
base cheia (módulo 00, internals do modelo §1) — mas foi treinado em
2020–2022, e o AUC por ano cai de 0,7890 (2020) para 0,7680 (2024) com a
probabilidade média derivando junto (módulo 00, internals do modelo §2).
O agregado não diz **em quem** o modelo ainda acerta.
Métodos locais existem para essa pergunta; o LIME é o primeiro do curso
que responde com uma atribuição por feature.

*Pergunta para a sala:* se o comitê de ética pergunta "por que o modelo
previu óbito para este paciente?", o que conta como resposta — e o que
conta como consolo?

## 2. O objetivo, termo a termo

$$\xi(x) = \operatorname*{arg\,min}_{g \in G} \; \mathcal{L}(f, g, \pi_x) + \Omega(g)$$

- **f** — o XGBoost de 800 árvores (módulo 00).
- **g** — a Ridge local.
- **π_x** — o kernel: $\sqrt{\exp(-d^2/\nu^2)}$, ν = 0,75√40 ≈ 4,74,
  distâncias no espaço padronizado.
- **𝓛** — erro quadrático ponderado.
- **Ω** — 10 features mantidas + L2 (α = 1).

Dizer com todas as letras: **g nunca passa por cima de f** — a predição
continua vindo do XGBoost; a reta só o resume.

Sinalizar as duas configurações (walkthrough, célula do objetivo):
`discretize_continuous=False` (o default fraseia como intervalos de
quartis — a forma das figuras do Molnar; contínuo deixa o gerador nu) e
`categorical_features`, que é a própria tese da aula.

## 3. A figura A–F — o que apontar

`lime_passo_a_passo.png` (walkthrough §0). O plano é idade × meses, corte
ceteris paribus do modelo real com as outras 38 congeladas no paciente.
Antes do primeiro painel, responder a pergunta que sempre vem: o paciente
é o mesmo |p−0,5| dos módulos 01–02 **porque precisa ser** — para um
paciente confiante, o contorno 0,5 do ajuste é empurrado para longe
(distância = |g(x)−0,5|/‖w‖) e a figura degenera.

| painel | mostra | apontar |
|---|---|---|
| A | a fronteira do modelo no corte | escadaria com tiras verticais — floresta divide uma feature por vez (módulo 01); não ler precisão na posição |
| B | o anel de meia-altura do kernel | ±16 anos × ±5,7 meses: "local" tem esse tamanho |
| C | a perturbação | **a nuvem não está no ✕** — quadrados ainda sem cor de classe, centro na média do treino, paciente a 6,7 desvios: um forasteiro na própria vizinhança |
| D | f nos vizinhos | único momento em que f é consultada — e o único em que os quadrados ganham cor; eles não separam ao longo da fronteira tracejada |
| E | o peso | **0,1% dos vizinhos com peso > 0,1** — sorteio na média, peso no paciente |
| F | a reta ponderada | *isto é a explicação*: R² 0,399 e pesos quase nulos, ajustada no deserto do painel E |

Deixar armada a pergunta: *os quadradinhos são pacientes?* — o resto da
aula são contagens respondendo.

## 4. As duas rodadas — gramática vs biologia

O coração da aula (walkthrough §§2–4, `lime_passo_2_lado_a_lado.png` e
`lime_passo_3_cercas.png`).

**Ingênua:** 4.999/5.000 vizinhos com código fabricado; a única linha
válida é o próprio paciente; doses negativas em 34,3%. Apontar que nada
quebrou — o wrapper arredonda em silêncio, R² 0,50, ranking entregue.
**O defeito não avisa; tem que contar.**

**Correta:** 0 fabricados, pesos com nome (`vacina_covid_declarada=1`
−0,19) — e as cercas conjuntas ficam: 30,6% (paciente-regra) / 79,2%
(vulnerável) impossíveis pela mesma `gate_impossible` dos módulos 00–02.
Apontar os idênticos 27,94% / 3,60% nos dois pacientes: **a nuvem é a
mesma** — o gerador nem olhou o paciente; o que muda a conta é o contexto
herdado (o portão).

**Antecipar estas três — elas vêm:**

- *"Por que não `sample_around_instance=True`?"* — internals §3: salva o
  paciente-regra por **geografia** (30,6% → 3,6%) e **piora** o
  vulnerável (82,9%); o portão (~70%) não cede em variante nenhuma.
  Usamos o default porque é como o LIME é rodado na prática — e a
  pergunta rende um exercício.
- *"E o discretizador do livro?"* — internals §3: muda a marginal das
  numéricas (idade < 0 some), impossíveis 8,9% no paciente-regra, 73,5%
  no vulnerável. Apresentação, não conserto.
- *"79,6% no módulo 01 vs 3,6% aqui — qual está certo?"* — os dois:
  perguntas diferentes (flip forçado de um sintoma vs sorteio pela
  prevalência). A régua é a mesma; o método é que muda.

## 5. R², kernel e sementes — o que assinar embaixo

`lime_passo_4_kernel.png`: kernel estreito → R² 0,00 **com erro 0,00** —
a explicação vazia perfeita (todos os pesos zerados, intercepto certo);
largo → R² 0,68 e erro 0,028 no paciente, subindo juntos. O `score` da
lib mede a nuvem. Regra para levar: **não ranqueie explicações por R²**.
Se sobrar tempo, `lime_internals_kernel.png` (internals §4) tem as 21
larguras com as duas curvas no mesmo eixo — a versão fina do mesmo
achado.

`lime_passo_5_sementes.png`: Jaccard 1,00 no top-5 das dez sementes e
zero trocas de sinal no top-8 — topo firme. A cauda é a posição seguinte:
3 das 8 features do topo somem do top-10 em alguma semente; internals §5:
21 sementes, dobrar vizinhos compra estabilidade (0,89 → 1,00, com o
mínimo saindo de 0,43).

Ponte com o módulo 01 (internals §6), dita com cuidado: não compare o
peso com o degrau **no ponto** — a inclinação pontual troca de sinal com
o passo (doses: +0,022 em h=1, −0,015 em h=2; a escadaria do módulo 01
cobrando). Regional × dp contra o peso: bate nas três numéricas em que os
dois lados têm direção (3/3), por um fio no par mais fraco.

## 6. O que o livro diz, e o fechamento

Molnar (cap. 14) sobre fidelidade local — pôr na tela ao lado da nossa
medição do §5 e perguntar à sala qual leitura fica. Das limitações do
capítulo, três saíram medidas hoje: vizinhança (B/E), correlação
ignorada (C + as cercas), instabilidade (§5). Crédito dito: as
limitações são do livro; Slack et al. (2020) fizeram da segunda um
ataque; o nosso acréscimo é a contagem exata em cercas deriváveis.

Fechar com a conclusão do próprio capítulo, lida em voz alta:

> "… the method is still in the development phase and many problems need
> to be solved before it can be safely applied."
> — Molnar, *Interpretable Machine Learning*, cap. 14, "Conclusion".

E a frase da casa: o valor do LIME não é nunca errar — é que, uma vez
medido, dá para dizer com precisão *como* ele erra; essa é a diferença
entre uma explicação e um consolo.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo; os de base
cheia, pelo internals do modelo (módulo 00). Todos vêm do modelo do curso
adotado em 2026-09-01 (800 árvores, profundidade 4, lr 0,05 — módulo 00,
SELECTION.md); a versão anterior desta aula os media no modelo de 400
árvores / profundidade 5, com outro paciente-regra (gold_id 1269214).

**Corrigidos nesta revisão:**

- erro no paciente ao declarar as categóricas — dizia que subia (0,011 →
  0,083), mede que cai (0,046 → 0,008) (walkthrough §3)
- estabilidade do top-5 nas dez sementes — dizia Jaccard 0,83 (mín
  0,43), mede 1,00 (mín 1,00) (walkthrough §6)
- a ponte CP↔LIME em doses — dizia que divergia, mede concordância 3/3
  (internals §6)
- quem troca de sinal com o passo — dizia idade (−0,002 / +0,003), mede
  doses (+0,022 / −0,015) (internals §6)
