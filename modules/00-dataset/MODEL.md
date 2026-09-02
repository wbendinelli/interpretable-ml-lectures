# MODEL.md — o modelo do curso

Gerado por `tools/srag_60_model.py --card` de `gold/model_metrics.json`.
Não editar à mão. Os cinco módulos de método explicam ESTE modelo:
todos refazem o fit da amostra commitada (determinística), então
"um modelo, um paciente" é garantia de código, não de disciplina.

## O que é

- **XGBoost** 800 árvores,
  profundidade 4, lr 0.05, min_child_weight 100, reg_lambda 5.0,
  `hist`, categóricas nativas, semente 42 — o modelo que os
  métodos explicam. A escolha destes parâmetros está em
  [`SELECTION.md`](SELECTION.md): protocolo pré-registrado,
  seis candidatos, seleção na validação, teste lido uma vez.
- **Regressão logística** (imputação mediana + padronização +
  one-hot; semana como seno/cosseno) — o baseline interpretável.
- **40 features** do Ouro (manifesto §2.5); alvo `y_obito`;
  split temporal treino ≤2022 / val 2023 / teste 2024.
- Treinado na **amostra commitada** (val e teste inteiros; treino 200.000 de 1.242.680).

## Métricas

| modelo | split | n | AUC | Brier | previsto médio | observado |
|---|---|---:|---:|---:|---:|---:|
| xgb | val | 24.148 | 0.7564 | 0.1356 | 0.2209 | 0.1893 |
| xgb | test | 16.142 | 0.7644 | 0.1308 | 0.2154 | 0.1824 |
| logit | val | 24.148 | 0.7206 | 0.155 | 0.2764 | 0.1893 |
| logit | test | 16.142 | 0.7246 | 0.1452 | 0.2419 | 0.1824 |

O gap de calibração no teste (previsto acima do observado) é o
**achado da deriva de regime**, não um defeito a esconder: o modelo
aprendeu letalidades de 2020–22 e o mundo de 2024 é outro — é
exatamente o que os módulos de método vão explicar.

## O paciente-exemplo

Regra: |p − 0,5| mínimo no teste, empate por `gold_id` — aplicada ao
modelo-da-amostra, o que os módulos usam.

- `gold_id` = 1276776, p(óbito) = 0.500
- 90 anos, masculino, SE, início em 2024 (semana 34), 1 dose(s) antes do sintoma, comorbidades: cardiopati
- Segundo paciente (mesma regra em 2021): `gold_id` = 834192, p = 0.500

## As quatro impossibilidades (gate_impossible)

| restrição | fração da amostra em estado vulnerável |
|---|---:|
| critério-2 por um fio (só tosse OU só garganta) | 79.6% |
| critério-3 por um fio | 24.67% |
| portão do funil (sem fator de risco declarado) | 37.27% |
| pré-campanha (nenhuma dose pode existir) | 29.67% |

Perturbar uma linha através de uma dessas fronteiras fabrica um
paciente que não pode existir — a conta que os módulos 01–05 fazem,
todos pela MESMA função, para imprimirem números idênticos por
construção.

## Limites declarados

- Imagem (RAIOX/TOMO) fora das features; a célula-armadilha do
  walkthrough mede o que o modelo teria aprendido (a AUSÊNCIA do
  registro prediz óbito — qualidade de documentação vazando).
- `UTI`/`SUPORT_VEN` fora — campos do episódio inteiro, preenchidos
  no encerramento; a justificativa medida e referenciada está no
  [`GOLD.md`](GOLD.md) (decisão 3).
- Sem pesos de classe (manifesto §2.7).
- O delta amostra→cheio está no internals do modelo.
