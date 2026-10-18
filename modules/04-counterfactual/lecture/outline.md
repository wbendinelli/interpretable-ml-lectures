# Aula — Contrafactuais no preditor COVID

Forma viva do módulo 04. As seções dos cadernos conservam seus números;
figuras são geradas pelo walkthrough e promovidas após execução e inspeção.

**Objetivos.** Formular uma busca finita; distinguir critérios de saída,
distância, restrições e diversidade; interpretar candidatos hipotéticos e
ausência de cruzamento sem inferir intervenção causal ou impossibilidade clínica.

## 1. A pergunta e o contrato

Partir da síntese do setup: unidade notificação, alvo e períodos do modelo
retrospectivo. O teste já observado sustenta explicações exploratórias.
A regra do exemplar e o limiar permanecem declarados, sem nova seleção clínica.

Apresentar a perda de Wachter como referência conceitual. A aplicação enumera
uma grade de alterações e compara p e Gower; não executa a otimização original,
não calcula uma fronteira Pareto e não cobre o espaço contínuo inteiro.

No walkthrough §1, mostrar mês e semana congelados. Ambas as codificações
vêm da data de início dos sintomas; mover apenas uma quebrava o contrato.
A grade vigente tem 103 movimentos simples e 5.099 pares completos, conferidos
nos internals §1. A correção histórica não inventa semana a partir de mês.

## 2. Mudanças isoladas — walkthrough §2

Abrir `cf_passo_1_busca_livre.png`. A maior redução é `saturacao → nao`,
de p 0,793 para 0,571. Trocar esse código não descreve tratamento de hipoxemia.
Idade também muda a previsão, sem ser uma ação disponível.

Nenhum candidato simples cruza 0,5; 1,9% violam as restrições verificadas.
Não comparar essa fração com a do LIME como uma nota de qualidade: os
geradores respondem a perguntas diferentes.

## 3. Pares, probabilidade e distância — walkthrough §3

Abrir `cf_passo_2_fronteira.png`: círculo passa nas restrições, cruz viola
alguma delas, marcador do registro na origem de Gower. A nuvem contém o
recorte de pares dos 60 melhores movimentos simples.

São 1.688 pares; 65 cruzam o limiar e passam nas restrições. O menor p é
0,3157, também encontrado na enumeração completa dos internals §1. A
igualdade vale para este exemplar e grade; não prova exatidão geral do recorte.

Explicar a correção: o resultado antigo de p 0,1995 movia mês e zerava doses
com semana fixa. Os internals o recompõem como auditoria histórica, sem
usá-lo como solução vigente. As cercas disponíveis não detectavam todo o
problema de calendário; passar nelas não comprova plausibilidade clínica.

## 4. Diversidade — walkthrough §4

A regra gulosa ordena por menor p e pede features disjuntas, com um limite
de apresentação. Ela encontra 2 histórias no menu corrigido: saturação +
idade (0,316) e imunodepressão + desconforto respiratório (0,452).
O código não força uma terceira, nem afirma maximizar o total de histórias.

Pergunta de discussão: o que essas histórias revelam sobre a função preditiva,
e o que seria necessário para tratá-las como alternativas executáveis?

## 5. Históricos hipotéticos restritos — walkthrough §5

Abrir `cf_passo_3_painel.png`. A busca permite mais doses anteriores ao sintoma
e, quando aplicável, uma declaração diferente. Esses históricos não são ações
administráveis retroativamente a quem já está internado. As frações não medem
eficácia de vacina, benefício de tratamento ou recourse clínico.

O exemplar tem 2 candidatos restritos e ambos mantêm p em 0,793. No painel
de 624 notificações com p ≥ 0,5, há cruzamento em 189 (30,3%) e ausência
nessa lista em 435 (69,7%). O calendário já estava fixo no painel; por isso
as contagens permanecem iguais. As bandas têm frações de 35%, 15% e 0%;
a última contém 19 notificações e não autoriza concluir ausência de alternativa
clínica ou generalização à população.

Nos internals §4, o painel de origem permanece o mesmo e muda somente o alvo:
0,5 → 30,3%; 0,4 → 9,3%; 0,3 → 1,1%. Não são novas coortes de risco
selecionadas em cada limiar, nem avaliação de uma política clínica.

## 6. Fechamento — walkthrough §6

As tabelas separam a melhor mudança única, o melhor par que cruza passando
nas restrições e o melhor candidato restrito. O último está em Gower 0,0042
e não cruza; o melhor par que cruza está em 0,0297. Menor distância e menor
probabilidade não são critérios equivalentes.

Concluir com o alcance: a ausência vale para a grade, o limiar e o preditor;
as restrições verificam parte do contrato; candidatos são consultas hipotéticas
ao modelo. O capítulo de Dandl e Molnar já discute controle de entradas e
limites causais. A contribuição local é operacionalizar e auditar essas escolhas
no caso SRAG, sem reivindicar um sexto critério inédito.

## Correções desta revisão

O menu anterior tinha 113 movimentos, 6.129 pares completos e 1.691 pares
no recorte, com 68 cruzamentos e 3 histórias exibidas. A revisão congela as
duas codificações do calendário e produz os números vigentes acima. O mínimo
anterior de 0,1995 e Gower 0,0339 fica registrado na auditoria do internals §1.

A redação também chamava a nuvem de perda de Wachter inteira, os históricos
vacinais de alavancas reais e o resultado de ausência de saída ao alcance.
Essas interpretações foram limitadas à grade finita e ao preditor.

<details>
<summary>Registro anterior: adoção da referência histórica</summary>

Os valores e interpretações abaixo pertencem à etapa anterior, preservada
como memória; os números e o alcance vigentes são os da revisão acima.


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

</details>
