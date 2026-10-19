# Aula — Feature Interaction

[README](../README.md) · [walkthrough](../notebooks/interaction_walkthrough.ipynb) · [internals](../notebooks/interaction_internals.ipynb)

**Pergunta da aula.** Depois dos efeitos principais, o capítulo 21 de Molnar pergunta onde a resposta do modelo deixa de ser aditiva. Calculamos a estatística H de Friedman–Popescu em pares declarados do mesmo caso SRAG/COVID e examinamos o resíduo, o denominador e a escala.

## Definir aditividade antes da razão

Escrever a soma de dependências parciais e o resíduo. Conferir que os termos são centralizados nos mesmos pontos observados.

**Abrir:** walkthrough §1–§2.

![Definir aditividade antes da razão](../figures/interaction-h.png)

## Ler o mapa do resíduo

Comparar a superfície conjunta e a resposta após retirar os efeitos simples. Distinguir magnitude em pontos percentuais e normalização pelo denominador.

**Abrir:** walkthrough §3.

![Ler o mapa do resíduo](../figures/interaction-residuo.png)

## Questionar estabilidade e escala

Ler a sensibilidade ao fundo. Abrir os controles conhecidos e a logística de um escore aditivo; concluir que H exige informar a escala e não mede importância.

**Abrir:** walkthrough §4; internals §2–§3.

![Questionar estabilidade e escala](../figures/interaction-escala.png)

## Conferir o parecer e seus limites

Abrir a síntese da base no walkthrough §5 e a auditoria do algoritmo no internals §4. Distinguir a definição do capítulo, a configuração adotada e o alcance das conclusões. O [parecer no README](../README.md#auditoria-frente-ao-livro-e-ao-código) registra adaptações e achados; a concordância de cálculo não certifica validade clínica.

## Perguntas para discussão

- Como um par pode ter H maior e resíduo absoluto menor? Conferir numerador e denominador antes de ordenar os pares.
- Por que transformar logisticamente um escore aditivo pode produzir H positivo sem retreinar o modelo?
- O que os sorteios de fundo e pontos avaliados mostram sobre a estabilidade da razão? Por que sua faixa não é um intervalo de confiança?

## Fechamento

Concluir lendo H junto do resíduo absoluto, do denominador e da escala. Uma razão indefinida não demonstra ausência de interação, e H não é um ranking de importância. Seguir para [Decomposição funcional](../../09-functional-decomposition/README.md), que exige declarar a função e os pesos usados para separar seus componentes.

As medições e seus condicionamentos estão no [README](../README.md) e nas seções de caderno indicadas. Este roteiro é o material vivo da aula; não foi produzido nem alterado um deck entregue.
