# Aula — LIME no modelo COVID (forma viva)

> Reescrita 2026-09-01 sobre o modelo do curso. Figuras referenciadas por
> nome em `../figures/`. Todo número abaixo é impresso por
> `lime_walkthrough.ipynb` ou `lime_internals.ipynb`; os marcadores
> `(walkthrough §N)` / `(internals §N)` apontam para dentro deles. Os
> decks PDF desta pasta são o registro do seminário da era BCW
> (2026-08-24) e não são retro-editados.

**Objetivos.** Enunciar o objetivo; acompanhar uma chamada na figura A–F;
separar codificação, domínio e regras conjuntas; interpretar R² ponderado,
erro no exemplar e estabilidade na escala da explicação.

---

## 1. Motivação — falada, não projetada

O modelo tem AUC **0,7644** no teste da amostra deste módulo
(walkthrough, setup); a logística tem **0,7246**. Esses números descrevem
discriminação agregada, sem explicar uma previsão individual.

Mostrar a síntese do setup: SHA256, unidade de notificação, partições,
óbitos, proporções e anos de início. O treino é subamostrado; validação e
teste são mantidos. O estudo usa a amostra commitada, e a leitura do
teste já observado é exploratória.

*Pergunta para a sala:* que objeto o LIME aproxima e em quais registros
avaliamos a qualidade dessa aproximação?

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
quartis — a forma das figuras do Molnar) e `categorical_features`.
A segunda opção informa o tratamento das categorias; não garante o domínio
de todas as entradas ou a consistência da ficha.

## 3. A figura A–F — o que apontar

`lime_passo_a_passo.png` (walkthrough §0). O plano é idade × meses, corte
ceteris paribus do modelo real com as outras 38 congeladas no paciente.
Antes do primeiro painel, responder a pergunta que sempre vem: o paciente
segue a regra |p−0,5| dos módulos 01–02 para facilitar a leitura do corte.
A distância do contorno 0,5 ao exemplar depende de |g(x)−0,5|/‖w‖;
um contorno distante dificulta a composição visual, sem impedir aplicar LIME.

| painel | mostra | apontar |
|---|---|---|
| A | a fronteira do modelo no corte | escadaria com tiras verticais — floresta divide uma feature por vez (módulo 01); não ler precisão na posição |
| B | o anel de meia-altura do kernel | ler os semieixos impressos no §0; o contorno é conferido contra o kernel instalado |
| C | a perturbação | a nuvem é a enviada ao preditor na própria chamada de LIME; seu centro e a distância ao paciente são impressos |
| D | f nos vizinhos | a cor é a classe prevista no mesmo corte CP usado para desenhar a fronteira; demais entradas fixas no paciente |
| E | o peso | pesos efetivamente entregues à Ridge; ler a fração acima do limiar, calculada nessa nuvem |
| F | a reta ponderada | intercepto, coeficientes, predição local e R² vêm da mesma Explanation; equações normais independentes no internals §7 |

Perguntar quais amostras são decodificáveis e quais violam as regras
verificadas. A figura descreve consultas artificiais, não novos pacientes observados.

<a id="4-as-duas-rodadas--gramática-vs-biologia"></a>

## 4. As duas rodadas — codificação e regras conjuntas

Walkthrough §§2–4: `lime_passo_2_lado_a_lado.png` e `lime_passo_3_cercas.png`.

**Sem categóricas declaradas:** 4.999/5.000 vizinhos com código fabricado;
a linha original conserva os níveis categóricos testados. Há doses negativas
em 34,3%. O wrapper arredonda para consultar o preditor, e a biblioteca retorna
R² 0,50 e um ranking; esses retornos não certificam o domínio das entradas.

**Com categóricas declaradas:** 0 códigos fabricados na checagem das categorias;
o coeficiente `vacina_covid_declarada=1` é −0,19. As violações conjuntas
permanecem: 30,6% no exemplar de referência e 79,2% no vulnerável. Doses
tratadas como contínuas ainda podem ser fracionárias. Decodificar uma categoria
não valida integralidade, restrições conjuntas ou plausibilidade clínica.

Os 27,94% / 3,60% coincidem entre os dois exemplares nos experimentos registrados.
Essas igualdades são de contagens específicas, não prova de que qualquer
exemplar receba a mesma explicação ou de que sua vizinhança represente a conjunta.

**Perguntas de comparação:**

- `sample_around_instance=True`: as violações passam de 30,6% a 3,6% no
  exemplar de referência e chegam a 82,9% no vulnerável; o portão permanece
  próximo de 70% nas variantes testadas (internals §3). Geração e ponderação
  locais são escolhas distintas; a redução de um filtro não valida toda a nuvem.
- Discretizador: a idade negativa some na variante; as violações são 8,9%
  e 73,5% nos exemplares (internals §3). Compare representação e regras,
  sem chamar a mudança de uma correção universal.
- 79,6% no módulo 01 (CP) e 3,6% aqui: a primeira conta força uma troca de sintoma;
  a segunda sorteia níveis por frequências. Mesmo filtro, perturbações diferentes.

## 5. R², kernel e sementes — o que assinar embaixo

`lime_passo_4_kernel.png`: nas larguras estreitas testadas, R² 0,00 e erro
0,00 no exemplar podem acompanhar um ajuste quase constante. Na configuração
larga, R² 0,68 e erro 0,028. O score mede ajuste à nuvem ponderada; o erro
no exemplar é outra verificação. Conferir as 21 larguras no internals §4.

`lime_passo_5_sementes.png`: Jaccard 1,00 no top-5 das dez sementes e
zero trocas de sinal no top-8. Ainda assim, 3 das 8 entradas do topo saem do
top-10 em alguma semente. Nas 21 sementes do internals §5, aumentar os vizinhos
muda a estabilidade (0,89 → 1,00; mínimo anterior 0,43). São resultados das
configurações comparadas, sem garantia para qualquer exemplar.

A comparação CP↔LIME (internals §6) é empírica e regional. Em doses, a
diferença finita troca de sinal com o passo (+0,022 em h=1, −0,015 em h=2).
A reta do CP na região declarada, multiplicada pelo desvio padrão, concorda
em direção nas três numéricas comparáveis (3/3). Isso não torna o coeficiente
LIME uma inclinação CP: a regressão usa várias entradas, pesos e outra
referência de amostragem.

## 6. O que o livro diz, e o fechamento

Molnar define fidelidade local em relação às previsões do modelo numa
vizinhança. Relacionar essa definição à geração, aos pesos e ao ajuste que
acabamos de conferir. A evidência distingue códigos categóricos, regras
conjuntas, fidelidade e estabilidade. Slack et al. (2020) motivam a atenção
à amostragem detectável; não executamos esse ataque aqui.

Fechar retomando o contrato da explicação: preditor fixo, representação,
vizinhança e escala. Coeficientes e R² pertencem a esse contrato. Os filtros
não cobrem toda a validade da ficha ou sua plausibilidade clínica.

**Correção de interpretação.** As expressões anteriores “gramática vs biologia”,
“pacientes impossíveis” e “qual mentira contar” davam alcance maior às checagens.
As medidas foram preservadas como diagnóstico das configurações declaradas.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo. Todos vêm
do modelo do curso
adotado em 2026-09-01 (800 árvores, profundidade 4, lr 0,05 — módulo 00,
SELECTION.md); a versão anterior desta aula os media no modelo de 400
árvores / profundidade 5, com outro paciente-regra (gold_id 1269214).

**Corrigidos nesta revisão:**

- figura A–F: uma segunda nuvem e uma Ridge com kernel sem a raiz
  quadrada apareciam ao lado do R² da primeira explicação. Os registros
  antigos de meia-altura (±16 anos × ±5,7 meses), coeficientes
  (+0,0001/+0,0003) e fração acima do limiar (0,1%) ficam marcados como
  corrigidos. O §0 usa uma execução e o internals §7 reconstrói o ajuste.
- erro no paciente ao declarar as categóricas — dizia que subia (0,011 →
  0,083), mede que cai (0,046 → 0,008) (walkthrough §3)
- estabilidade do top-5 nas dez sementes — dizia Jaccard 0,83 (mín
  0,43), mede 1,00 (mín 1,00) (walkthrough §6)
- a ponte CP↔LIME em doses — dizia que divergia, mede concordância 3/3
  (internals §6)
- quem troca de sinal com o passo — dizia idade (−0,002 / +0,003), mede
  doses (+0,022 / −0,015) (internals §6)
