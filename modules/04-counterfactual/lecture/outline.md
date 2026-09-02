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

`cf_passo_1_busca_livre.png`. Apontar as cores e a ordem: a melhor
mudança do mundo é verde-sintoma — `saturacao → nao`, apagar do
prontuário a saturação baixa (0,793 → 0,571), que é consequência, não
alavanca; a segunda é laranja-demografia, `idade → 10`, dos 32 aos 10
anos; a terceira recua o calendário para o mês 6 e cai na cerca. E
`imunodepre → desconhecido` / `out_morbi → desconhecido` entre as dez:
apagar o registro vale quase tanto quanto curar — a armadilha da
documentação do módulo 00, de volta. Na contagem: 3,5% de inválidos,
contra 30,6% do LIME — mesma régua, métodos fabricam ficção em taxas
diferentes. E nenhuma mudança única cruza 0,5 sozinha.

## 3. A fronteira, e válido ≠ alcançável (10 min)

`cf_passo_2_fronteira.png` — dizer explicitamente: **isto é a perda de
Wachter vista por inteiro** (x = d, y = validade; cada ponto um
candidato; escolher λ escolheria um ponto; nós mostramos a nuvem).

Os melhores válidos: volte ao mês 6 da pandemia sem nenhuma dose;
apague a saturação e vire criança de 10 anos. Notar que recuar o
calendário **sozinho** é pré-campanha (§2) e recuá-lo com zero doses
passa — o par escapa da cerca de que o simples não escapava. A distinção
da aula: a `gate_impossible` responde "isso existe?"; ninguém a desenhou
para "dá para chegar lá daqui?".

*Objeção que vem:* "então a cerca falhou?" — Não: internals §3, o portão
é **unidirecional no dado real** (0,54% declaram fator sem nomear
comorbidade — o estado 'declarado sem detalhe' existe), então "curar"
uma comorbidade produz um paciente que existe. Quem barra a cura é a
lista de alavancas.

## 4. Rashomon: três histórias impressas (8 min)

Walkthrough §4: dos 68 válidos, três com features disjuntas — mês 6 com
zero doses (0,199); saturação apagada e 10 anos de idade (0,316);
imunodepressão e desconforto respiratório curados (0,452). Ler as três
tabelas em voz alta e perguntar à sala: *qual história você contaria ao
paciente?* — então
nomear: é o Rashomon do cap. 15 ("you will usually find multiple
counterfactual explanations"), e a diversidade-como-critério (DiCE) é
pedir o cardápio de uma vez.

## 5. As alavancas, e a resposta honesta (12 min)

`cf_passo_3_painel.png`. Primeiro o paciente: os dois candidatos
acionáveis que ele tem deixam a p em 0,793, onde ela já estava — não
cruzam e não movem a previsão na terceira casa; apontar o módulo 05 §5
(a atribuição de doses marca grupos priorizados; φ>0 não é causa).
Depois o teste inteiro: 30,3% do alto risco com contrafactual acionável,
69,7% sem — e o gradiente que dói: 35% → 15% → **0%** conforme o risco
sobe, com 19 pacientes na banda de cima e nenhuma saída para nenhum
deles. Quem mais precisa de saída é quem não tem.

Internals §4 para a objeção do limiar: 0,5 → 30,3%; 0,4 → 9,3%;
0,3 → 1,1%. O limiar é decisão de quem opera; a conta acompanha.

*Prompt de discussão:* o comitê pergunta "o que este paciente deveria
ter feito?" — o método respondeu "nada ao alcance dele mudava a previsão".
Isso é um fracasso da explicação ou a informação mais importante da
tarde?

## 6. Fechamento (5 min)

Walkthrough §6, as três tabelas: o mais próximo é o acionável que não
cruza (Gower 0,0042); o mais eficaz, oito vezes mais longe (0,0339) e
absurdo. *Existir, estar perto, estar ao alcance.* A citação do capítulo
— "no additional assumptions and no magic in the background" — com a
ressalva medida: a
ausência de mágica no método empurra as suposições para o desenho do
espaço, onde ficam visíveis. E o gancho para o 05: em vez de buscar a
mudança, atribuir a predição — exatamente.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo.

**Corrigidos nesta revisão:** a re-sincronização no modelo do curso
adotado em 2026-09-01 (módulo 00, SELECTION.md) mudou o paciente que a
regra "p mais próximo de 0,8" escolhe — gold_id 1267430, de 81 anos,
para 1266990, de 32 anos — e com ele estas afirmações:

- melhor mudança única — dizia `idade → 10`, "rejuvenesça 71 anos"
  (0,804 → 0,480); mede `saturacao → nao` (0,793 → 0,571)
  (cf_walkthrough §2)
- mudanças simples que cruzam 0,5 — dizia 1; mede 0 (cf_walkthrough §2)
- contrafactuais válidos — dizia 151; mede 68 (cf_walkthrough §4)
- as três histórias do Rashomon — dizia 0,18 / 0,34 / 0,40; mede
  0,199 / 0,316 / 0,452, e sobre outras features (cf_walkthrough §4)
- subir doses no paciente — dizia que **aumenta** a p (0,829); mede
  0,793 → 0,793, sem cruzar (cf_walkthrough §5)
- cobertura no alto risco — dizia 36% / 64% sobre 902 pacientes; mede
  30,3% / 69,7% sobre 624 (cf_walkthrough §5)
- gradiente por banda — dizia 43% → 25% → 3%; mede 35% → 15% → 0%
  (cf_walkthrough §5)
- sensibilidade do limiar — dizia 0,4 → 16,2% e 0,3 → 2,5%; mede 9,3% e
  1,1% (cf_internals §4)
- distância do mais eficaz — dizia dez vezes o acionável (0,0400); mede
  0,0339 contra 0,0042 (cf_walkthrough §6)
