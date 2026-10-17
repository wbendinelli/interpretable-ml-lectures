# ROADMAP — todos os métodos do Molnar, sobre uma base só

O curso aplica os métodos do *Interpretable Machine Learning* do Molnar
(3ª edição — capítulos verificados contra o livro vivo; os módulos 01–03
já citam os capítulos 12–14) a um único dataset: a base SRAG /
SIVEP-Gripe que o módulo 00 trata, documenta e contrata.

## A tese organizadora

O módulo 00 mediu a estrutura que faz desta base um **argumento**, não só
um caso: a ficha desliga campos condicionalmente (34 portões confirmados;
o funil de comorbidade segura 0,00% de contradição nos seis anos), então
as features são **conjuntamente restritas**. Um método que perturba,
varre ou permuta features *de forma independente* — ceteris paribus, ICE,
LIME, PDP, Shapley marginal, permutation importance, anchors — pode
produzir combinações que contradizem o formulário ou o recorte da coorte:
uma comorbidade marcada com `FATOR_RISC` dizendo que não há nenhuma, um
subtipo sem triagem positiva. A restrição violada precisa ser nomeada;
estar fora da coorte não significa ser biologicamente impossível. ALE e
explicações condicionais fazem parte do plano de estudo, mas não são
apresentados como solução automática para todas essas restrições.

A base ainda carrega três armadilhas nomeadas que os módulos vão reusar:

- **Redundância na representação da idade**: `COD_IDADE` pode ser
  reconstruído de `TP_IDADE` e `NU_IDADE_N`; as exceções ficam na
  checagem `conf-comp-cod-idade` do módulo 00. Esses códigos brutos não
  fazem parte das entradas do modelo explicado na aula PFI; não devem
  aparecer como se seu experimento já tivesse sido realizado.
- **Calendários disfarçados**: campos disponíveis em alguns anos e
  inteiramente vazios em outros podem informar o período pela revisão do
  formulário (módulo 00, internals do Prata §2).
- **Deriva de regime como sinal**: letalidade 29,0% → 8,6% entre
  2020–2024 nos registros brutos (módulo 00, internals do Prata §1).
  Uma explicação que destaque o tempo pode refletir essa associação;
  não demonstra um efeito causal do calendário.

## O mapa

Status: ✅ disponível (sobre a referência registrada — ver bandeira 2) ·
🔜 planejado · ⛔ não se aplica a esta base.
Os materiais disponíveis continuam condicionados à referência amostrada.
A ampliação do treino completo está em execução no módulo da base; não
significa que as medições de todos os métodos já tenham sido migradas.

| Cap. Molnar | Método | Status | O estudo na base SRAG | Restrições em 4,1 M × 420 |
|---:|---|---|---|---|
| `6` | Regressão linear | 🔜 | baseline na coorte; a multicolinearidade das comorbidades desestabiliza coeficientes — medido, não afirmado. Prévia medida no estudo de seleção do módulo 00 (o LPM e sua patologia fora de [0,1]) | trivial |
| `7` | Regressão logística | 🔜 | o primeiro modelo do alvo; coeficientes vs o funil. Prévia medida no estudo de seleção do módulo 00 (C tunado na validação temporal) | trivial |
| `8` | GLM / GAM | 🔜 | efeito não linear da idade no óbito — o U que os regimes movem. Fora do estudo de seleção do módulo 00, de propósito: vira módulo próprio | seleção de termos exige cuidado |
| `9` | Árvore de decisão | 🔜 | tratamento nativo do vazio vs os três estados. Prévia medida no estudo de seleção do módulo 00 (profundidade/poda tunadas) | ok |
| `10` | Regras de decisão | 🔜 | regras sobre checkboxes; a tentação do vazamento de ano. Fora do estudo de seleção do módulo 00, de propósito: vira módulo próprio | pré-seleção de features |
| `11` | RuleFit | 🔜 | geração de regras em subamostra. Fora do estudo de seleção do módulo 00, de propósito: vira módulo próprio | subamostrar |
| `12` | Ceteris paribus | ✅ reescrito (2026-09-01) | variar uma entrada com as demais fixas; verificar as restrições do formulário e da coorte | barato |
| `13` | ICE | ✅ reescrito (2026-09-01) | heterogeneidade por regime — curvas coloridas por ano | subamostrar pacientes |
| `14` | LIME | ✅ reescrito (2026-09-01) | verificar a vizinhança perturbada contra as restrições declaradas do formulário e da coorte | explicar uma amostra |
| `15` | Contrafactuais | ✅ (módulo 04, 2026-09-01) | "o que teria de mudar" sob as restrições dos portões — imutáveis (idade, ano) declarados | por instância |
| `16` | Anchors | 🔜 | SE-ENTÃO sobre checkboxes; o mesmo risco de amostragem do LIME | subamostrar |
| `17` | Valores de Shapley | ✅ (módulo 05, com o cap. 18) | distinguir a definição por coalizões da implementação TreeSHAP e explicitar o jogo de referência | enumeração genérica cresce exponencialmente; árvores têm algoritmo específico |
| `18` | SHAP | ✅ (módulo 05, 2026-09-01) | TreeSHAP no modelo do curso; interventional vs path-dependent sobre o funil | eficiente |
| `19` | PDP | 🔜 | efeito médio vs as pontas fora da variedade | subamostra de fundo |
| `20` | ALE | 🔜 | acumula **diferenças** dentro de janelas que a base ocupa, o que corrige a extrapolação do PDP — mas não a cerca, porque a diferença ainda é tomada com o resto da ficha parado; checkboxes sem ordem exigem uma escolha de ordenação | bins por quantil, ok |
| `21` | Interação (H) | 🔜 | idade × ano, vacina × regime | restringir os pares de interesse + subamostrar |
| `22` | Decomposição funcional | teoria | ler junto de PDP, ALE e interação | — |
| `23` | Permutation Feature Importance (PFI) | ✅ (módulo 06) | erro original vs permutado no XGBoost fixo; ranking, repetição e comparação entre permutação individual, conjunta e dentro de subgrupos | teste temporal completo; modelo fixo |
| `24` | LOFO | 🔜 | p re-treinos — o capítulo mais caro; features agrupadas (as famílias!) como saída | pesado: agrupar + subamostrar |
| `25` | Surrogates globais | 🔜 | fidelidade (R²) lida com o ceticismo do próprio módulo 03 | subamostrar |
| `26` | Protótipos e críticas | 🔜 | quem é o paciente típico de 2021; distância de Gower para tipos mistos | O(N²) — coresets |
| `27–30` | Features aprendidas / saliência / TCAV / adversarial | ⛔ | específicos de imagem e rede neural | — |
| `31` | Instâncias influentes | 🔜 | as sete linhas da quarentena vs as realmente influentes | diagnóstico de deleção: amostrar |
| `32` | Avaliação de interpretabilidade | teoria | a barra de evidência do próprio repositório, formalizada | — |

Os métodos disponíveis têm uma entrada própria em
[`modules/`](modules/README.md); os demais permanecem planejados nesta tabela.
Os capítulos excluídos conservam o motivo declarado.

Chegar ao **cap. 23** com o módulo PFI não significa implementar todos os
capítulos anteriores nem criar módulos intermediários para preencher a
numeração. As prévias de modelos interpretáveis no estudo de seleção não
equivalem a módulos completos desses métodos. O
[relatório vivo dos registros à importância global](reports/02-modelo-global-pfi/README.md)
sintetiza somente os métodos efetivamente estudados e preserva o
[relatório local entregue](reports/01-metodos-locais/README.md).

## Estado do percurso e próxima execução

O módulo da base já documenta aquisição, Silver, escolhas Gold, estudo de
seleção e referência amostrada. Os módulos de método disponíveis estão
listados acima; as próximas aulas continuam planejadas, sem resultados
atribuídos a métodos ainda não executados. A unidade da série é o contrato
de dados e modelo, não a obrigação de usar um único registro em qualquer
pergunta: contrafactuais declaram seu exemplar e PFI avalia o conjunto.

A ampliação autorizada estuda o treino elegível completo. Seu percurso é:

1. **Reafirmar a tarefa no módulo da base.** Delimitar a coorte, o
   desfecho admitido e as exclusões. A expressão “casos fechados” precisa
   identificar também a exclusão de óbitos por outras causas.
2. **Separar população, partições e amostra.** Explicitar que a amostra
   usada pela referência foi retirada apenas do período de treino;
   validação e teste permaneceram completos. O novo ajuste completo não
   altera automaticamente esses períodos.
3. **Executar a seleção e a comparação declaradas.** Produzir a evidência
   com o treino completo, respeitando o papel da validação e identificando
   como exploratórias as análises do teste já observado. Ainda não há
   vencedor novo adotado por este mapa. O
   [novo protocolo](modules/00-dataset/COURSE_STUDY.md) usa log loss de
   validação como critério principal; a seleção histórica usou AUC.
   Pesos, redução e SMOTENC restrito são comparados somente nas famílias
   logística e XGBoost, com as listas de configurações correspondentes;
   árvore e floresta entram sem balanceamento.
4. **Decidir sobre a referência e reconciliar as explicações.** Se o
   modelo adotado mudar, recalcular os experimentos afetados e registrar
   as diferenças. Desempenho próximo entre modelos não garante previsões
   ou explicações equivalentes.
5. **Consolidar a nova edição do relatório e a aula PFI.** Vincular cada
   resultado ao notebook responsável e manter intacto o PDF entregue dos
   métodos locais. A nova edição viva está em preparação; não foi
   exportado um novo PDF.

O PFI já tem sua [aula no módulo 06](modules/06-pfi/README.md), construída
sobre o modelo do curso. Ela preserva os experimentos anteriores do módulo 00
como histórico e mede a dependência preditiva global. O exemplo final usa
cardiopatia e diabetes, com permutação conjunta e dentro dos estados de diabetes;
o par de códigos brutos de idade do plano inicial não é entrada desse modelo e
não é apresentado como resultado realizado.

## Convenções de módulo (restrições já em vigor)

Numeração sequencial própria deste repositório; cada módulo nomeia seu
capítulo no README. Estrutura do `modules/_template/`: README com a ordem
fixa de seções, `lecture/outline.md`, dois notebooks
(`<slug>_walkthrough`, `<slug>_internals`), `RANDOM_STATE = 42`, figuras
promovidas por cópia explícita, outputs commitados após rodada de kernel
limpo, e linha adicionada à mão na tabela do README raiz. Todo número em
prosa é impresso por célula commitada no mesmo módulo.

## Duas bandeiras, registradas para não se resolverem em silêncio

1. **A exigência de COVID nunca foi confirmada com o professor.** O
   William preferiria estudar saúde mental; nada no repositório força
   COVID. A base mantém todas as etiologias de SRAG; o recorte COVID é
   uma escolha explícita da receita Gold adotada. Isso não significa que
   alterar uma flag baste para executar outra tarefa: os valores
   suportados precisam corresponder aos filtros e ao alvo efetivamente
   implementados. Uma nova pergunta exige uma receita validada, não uma
   troca silenciosa do nome no manifesto.
2. **Resolvida em 2026-09-01: os módulos 01–03 rodavam sobre o Breast
   Cancer Wisconsin.** O modelo do curso existe (módulo 00), os três
   módulos foram reescritos sobre ele e os módulos 04 (contrafactuais) e
   05 (SHAP) nasceram direto no caso COVID. A versão BCW de 01–03 vive no
   histórico do git. Segunda rodada, em 2026-09-02: o estudo de
   seleção trocou os hiperparâmetros do modelo (`PR #29`) e os cinco módulos
   foram re-sincronizados número a número sobre o modelo adotado — os
   deslocamentos de condicionamento registrados numa nota por módulo, as
   afirmações falsificadas corrigidas uma a uma no texto.
