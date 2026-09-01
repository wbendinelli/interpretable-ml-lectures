# Aula — LIME no modelo COVID (forma viva)

> Reescrita 2026-09-01 sobre o modelo do curso (XGBoost, óbito por COVID,
> módulo 00). A aula da era Breast Cancer vive no histórico do git; os
> decks PDF desta pasta são o registro dela e não são retro-editados.

## Arco (50 min)

1. **O método em uma frase** (5 min) — sorteie vizinhos, pese pela
   distância, ajuste uma reta. Contraste com o módulo 01: o CP move um
   fio; o LIME chacoalha as 40 colunas de uma vez. A pergunta da aula:
   quem são os vizinhos?

2. **A rodada ingênua** (10 min) — `lime_passo_1_gerador.png`: sem
   `categorical_features`, 4.999 dos 5.000 vizinhos têm código fabricado
   (a única linha válida é o próprio paciente); doses negativas em 34%.
   O wrapper arredonda em silêncio — e é por isso que "funciona".
   **Ponto da aula: o erro não avisa; tem que contar.**

3. **A rodada correta, e o que ela não conserta** (15 min) —
   `lime_passo_2_lado_a_lado.png`: pesos ganham nome de gente.
   `lime_passo_3_cercas.png`: a mesma `gate_impossible` dos módulos
   00–02 conta 30,6% de vizinhos impossíveis para o paciente-regra e
   79,2% para o vulnerável — e pré-campanha/fora-da-coorte dão idênticos
   nos dois, porque **a nuvem é a mesma**: a gaussiana é centrada na
   média do treino (internals §2), o sorteio é independente por coluna
   (correlação meses×doses: +0,61 no real, −0,00 na nuvem). A correção
   de codificação conserta a gramática; a biologia conjunta, não.

4. **R² não é fidelidade** (10 min) — `lime_passo_4_kernel.png`: kernel
   estreito → R² 0,00 com erro 0,00, a explicação vazia perfeita; kernel
   largo → R² 0,65 e erro 0,045 no próprio paciente. O `score` que a lib
   reporta mede a nuvem sintética, e a largura escolhe qual mentira
   contar.

5. **O que carregar** (10 min) — `lime_passo_5_sementes.png`: aqui a
   semente não assusta (Jaccard 0,83, zero trocas de sinal) porque o
   acaso mora só no gerador. A ponte com o módulo 01 (internals §6): não
   compare peso com degrau — a inclinação pontual da escadaria troca de
   sinal com o passo; compare por região (peso ≈ inclinação × desvio).
   Gancho para o módulo 04: parar de diagnosticar vizinhos impossíveis e
   buscar direto no espaço permitido.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo; os de base
cheia, pelo internals do modelo (módulo 00).
