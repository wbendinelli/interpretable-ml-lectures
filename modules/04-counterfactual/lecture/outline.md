# Aula — Contrafactuais no modelo COVID (forma viva)

> Módulo novo (2026-09-01), direto sobre o modelo do curso — não há deck
> histórico; esta é a única forma da aula. Figuras em `../figures/`;
> todo número abaixo é impresso por `cf_walkthrough.ipynb` ou
> `cf_internals.ipynb`.

**Objetivos.** Ao final, a turma deve saber formular a busca como
enumeração sobre movimentos declarados; nomear os cinco critérios do
cap. 15 e apontar a operacionalização de cada um; reconhecer o Rashomon
numa lista de válidos; e defender "não há X ao seu alcance" como
resposta do método.

---

## 1. A pergunta invertida (7 min)

Dos módulos 01–03 ("o que pesou?") para a definição do cap. 15 — a menor
mudança que muda a predição. Escrever a perda de Wachter no quadro e
apontar cada termo; então a virada didática: **o espaço deste problema
cabe na memória** (113 simples, 6.129 pares), logo não escolhemos λ —
enumeramos a nuvem inteira e mostramos a troca (passo 2). DiCE declarado
fora (pin); Dandl/NSGA-II citado como o plano B de quem não cabe.

A tabela dos cinco critérios → operacionalização (validade = cruzar 0,5;
proximidade = Gower; sparsidade = profundidade; plausibilidade =
`gate_impossible`; diversidade = §4) + o sexto da casa: acionabilidade.

*Por que este paciente:* p ≈ 0,8 por regra — contrafactual pede alguém
com o que perder; em p = 0,5 qualquer sopro cruza e a busca degenera.

## 2. O que a busca livre quer (8 min)

`cf_passo_1_busca_livre.png`. Apontar as cores: a melhor mudança do
mundo é laranja-demografia — `idade → 10`, "rejuvenesça 71 anos"
(0,804 → 0,480); verdes apagam sintomas (consequência, não alavanca);
e `cs_escol_n → desconhecido` derruba a p — a armadilha da documentação
do módulo 00, de volta. Quase nada é vermelho-cerca: 3,5% de inválidos,
contra 30,6% do LIME — mesma régua, métodos fabricam ficção em taxas
diferentes.

## 3. A fronteira, e válido ≠ alcançável (10 min)

`cf_passo_2_fronteira.png` — dizer explicitamente: **isto é a perda de
Wachter vista por inteiro** (x = d, y = validade; cada ponto um
candidato; escolher λ escolheria um ponto; nós mostramos a nuvem).

Os melhores válidos: criança sem imunodepressão, gestante de terceiro
trimestre. A distinção da aula: a `gate_impossible` responde "isso
existe?"; ninguém a desenhou para "dá para chegar lá daqui?".

*Objeção que vem:* "então a cerca falhou?" — Não: internals §3, o portão
é **unidirecional no dado real** (0,54% declaram fator sem nomear
comorbidade — o estado 'declarado sem detalhe' existe), então "curar"
uma comorbidade produz um paciente que existe. Quem barra a cura é a
lista de alavancas.

## 4. Rashomon: três histórias impressas (8 min)

Walkthrough §4: dos 151 válidos, três com features disjuntas — criança
sem imunodepressão (0,18); saturação + raça apagadas (0,34); gestante de
idade ignorada aos 81 (0,40). Ler as três tabelas em voz alta e
perguntar à sala: *qual história você contaria ao paciente?* — então
nomear: é o Rashomon do cap. 15 ("you will usually find multiple
counterfactual explanations"), e a diversidade-como-critério (DiCE) é
pedir o cardápio de uma vez.

## 5. As alavancas, e a resposta honesta (12 min)

`cf_passo_3_painel.png`. Primeiro o paciente: subir doses **aumenta** a
p (0,829) — segurar a reação e apontar o módulo 05 §5 (a atribuição de
doses marca grupos priorizados; φ>0 não é causa). Depois o teste
inteiro: 36% do alto risco com contrafactual acionável, 64% sem — e o
gradiente que dói: 43% → 25% → **3%** conforme o risco sobe. Quem mais
precisa de saída é quem não tem.

Internals §4 para a objeção do limiar: 0,5 → 36%; 0,4 → 16%; 0,3 → 2,5%.
O limiar é decisão de quem opera; a conta acompanha.

*Prompt de discussão:* o comitê pergunta "o que este senhor deveria ter
feito?" — o método respondeu "nada ao alcance dele mudava a previsão".
Isso é um fracasso da explicação ou a informação mais importante da
tarde?

## 6. Fechamento (5 min)

Walkthrough §6, as três tabelas: o mais próximo é o acionável que não
cruza (Gower 0,0042); o mais eficaz, 10× mais longe e absurdo. *Existir,
estar perto, estar ao alcance.* A citação do capítulo — "no additional
assumptions and no magic in the background" — com a ressalva medida: a
ausência de mágica no método empurra as suposições para o desenho do
espaço, onde ficam visíveis. E o gancho para o 05: em vez de buscar a
mudança, atribuir a predição — exatamente.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo.
