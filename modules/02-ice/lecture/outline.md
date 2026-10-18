# Aula — ICE no modelo COVID (forma viva)

**Objetivos.** Construir ICE/PDP no mesmo painel; comparar curvas centradas;
conferir violações de regras e interpretar diferenças finitas na escala de
probabilidade, com sensibilidade à grade.

## 1. Do CP ao feixe (7 min)

A regra do painel é **200 registros, 40 por ano, semente 42**. Conferir a tabela
da amostra e a unidade notificação no setup. A ponderação equilibra os anos para
comparação visual; não reproduz a distribuição anual da Gold.

<a id="2-o-feixe-e-o-teste-que-falha-de-propósito-12-min"></a>

## 2. O feixe e a média do painel (12 min)

Abrir `ice_passo_1_feixe.png`. Aos 80 anos: médias de 0,481 (2020), 0,317 (2023)
e 0,303 (2024), contra 0,400 no painel. A média tem outra referência; não
precisa coincidir com as curvas individuais. A cor por ano não controla as
outras entradas. Separação de nível não demonstra, sozinha, interação.

**Pergunta:** que comparação muda se ponderarmos os anos pelas frequências
originais? Não chamar o PDP de erro por resumir uma referência diferente.

## 3. Centrado: nível × forma (8 min)

Abrir `ice_passo_2_centrado.png`. A âncora comum remove o nível inicial de cada
curva. Ganho 0→100: p10 0,247 e p90 0,623; correlação mediana 0,983 com a média
(internals §2). Correlação alta não prova paralelismo ou ausência de interação.

## 4. Quem são as linhas, vezes 200 (10 min)

Na grade de idade, 0/10.200 violações dos filtros. Em doses, 252/1.400 (18%):
42 registros pré-campanha × 6 doses. Em tosse, 54% (internals §3). As regras
são de formulário, calendário e coorte; passar por elas não certifica toda a
plausibilidade clínica.

<a id="5-a-derivada-onde-o-efeito-mora-8-min"></a>

## 5. Diferenças finitas e suporte da grade (8 min)

Abrir `ice_passo_4_derivada.png`. O nome do arquivo foi preservado, mas a figura
mostra **Δp/Δidade em intervalos**, não uma derivada analítica suave.
Na grade principal, o máximo mediano é 0,0239/ano no intervalo iniciado aos
10 anos; no miolo 40–54 a mediana é 0,00326, e após 55 o máximo é 0,0133.

Conferir a tabela de passos **1, 2 e 5 anos**, com o mesmo modelo e painel.
Posição e altura do máximo dependem dos intervalos. A faixa interquartil
representa dispersão entre curvas; não é incerteza da média.

A proporção de óbitos registrada no treino vai de 3,49% (4–8 anos) a 13,89%
(16–20), com 292 a 720 registros por faixa. Isso descreve suporte e associação;
não explica causalmente o pico das diferenças de previsão.

**Correção de interpretação.** A aula dizia “Aqui, sim” para efeito biológico
e atribuía o máximo ao “braço adolescente da curva em U”. A coorte ser COVID
não isola esse mecanismo. As medidas continuam registradas, com o alcance
restrito ao modelo, painel e grade.

## 6. Fechamento (5 min)

Cada curva parte de uma notificação observada e avalia substituições artificiais.
A média resume esse painel; c-ICE remove a âncora e diferenças finitas localizam
mudanças entre pontos. O módulo 03 muda a referência para uma vizinhança sorteada,
que também precisa ser identificada e auditada.

<details>
<summary>Histórico de condicionamento das medidas</summary>

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo.

**Re-medidos em 2026-09-02**, no modelo do curso adotado em 2026-09-01
(800 árvores, profundidade 4, lr 0,05 — módulo 00, SELECTION.md), contra
o modelo de 400 árvores / profundidade 5 da versão anterior:
p(óbito) aos 80 anos 0,48 → 0,481 (2020), 0,32 → 0,317/0,303 (2023/2024),
PDP 0,407 → 0,400; ganho 0→100 p10 0,23 → 0,247 e p90 0,62 → 0,623;
correlação curva×média 0,965 → 0,983; derivada 0,023 → 0,0239 (aos 10),
0,003 → 0,00326 (miolo), 0,014 → 0,0133 (pós-55). Deslocamento de
condicionamento das medidas; a interpretação clínica foi corrigida nesta revisão. As contagens de cerca
não se mexeram (idade 0/10.200, doses 252/1.400 = 18%, tosse 54%) — a
cerca é da base, não do modelo.
</details>
