# Aula — SHAP no modelo COVID (forma viva)

Forma editável da aula. As figuras estão em `../figures/`; as medições,
nos dois notebooks. Começar pela identidade da amostra, partições temporais
e escala da explicação, impressas no walkthrough.

**Objetivos.** Definir o jogo de atribuição, verificar sua soma e ler os
gráficos com seus limites. Distinguir caminhos e marginalização; investigar
interações sem inferir causalidade da cor, do sinal ou das taxas observadas.

## 1. Do jogo à floresta (8 min)

Apresentar coalizão, ganho e valor base. O `pred_contribs` usa o jogo de caminhos
do XGBoost. Eficiência é conferida contra a margem, não contra a probabilidade.
O internals §2 mostra por que valor base, margem média e frequência observada
não são sinônimos. Refits iguais com entradas fixas não resolvem a escolha do jogo.

## 2. Waterfall e force (10 min)

`shap_passo_1_waterfall.png` e `shap_passo_2_force.png`: seguir as contribuições
até a margem do exemplar e só então aplicar a sigmoide. O sinal reparte a predição
em relação à referência declarada; não estima o efeito de alterar a entrada.

## 3. SHAP × LIME, e a interpretação correta (8 min)

`shap_passo_3_vs_lime.png`: painéis separados, mesmo exemplar. As escalas e os
objetos são próprios. A concordância de sinais é descritiva; uma divergência
não identifica ruído e não torna um método incorreto. Consultar a auditoria
do ajuste no módulo 03 antes de discutir os coeficientes.

## 4. O global como soma de locais (8 min)

`shap_passo_4_global.png`: média absoluta e distribuição das contribuições no
teste histórico. Comparar o critério com gain, indicando os conjuntos envolvidos.
A diferença de postos não identifica a causa da mudança temporal.

## 5. Dependence plots — a interação em cor (12 min)

`shap_passo_5_dependencia.png` usa a amostra inteira, incluindo treino. A cor
mostra o calendário; não certifica interação funcional. O internals §3 mede
interações nas mesmas posições sorteadas e confere suas somas e simetria.
O controle aditivo com entradas dependentes demonstra por que dispersão visual
não basta; seu jogo condicional não é o algoritmo de caminhos.

Discutir o φ de doses sem lhe atribuir um mecanismo causal. A tabela observada
usa intervalos de idade explícitos e imprime as contagens, mas não controla
todos os confundidores. Nem o sinal nem essa tabela identificam o efeito de
administrar uma dose.

## 6. Caminho × intervenção, e o fechamento do curso (9 min)

`shap_passo_6_interventional.png`: comparar os jogos na mesma escala de margem.
Variação de Monte Carlo e diferença de jogo são questões distintas. As
combinações do estimador que violam o contrato são contadas na §7; as demais
não recebem, por isso, um certificado de viabilidade clínica.

Fechar com a sequência de leitura: modelo, conjunto, escala, jogo e verificação.

## Números citados nesta aula

Consultar as saídas e a síntese do README. O registro preserva a correção do
posto de `meses` por gain, de 16º para 19º (walkthrough §4). A revisão também
corrige as antigas inferências de interação pela dispersão, causalidade vacinal
e ruído pela divergência com LIME, sem mudar os valores SHAP do preditor histórico.
