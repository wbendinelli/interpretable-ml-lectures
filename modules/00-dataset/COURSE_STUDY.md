# Estudo global do modelo do curso

O modelo de referência será escolhido novamente usando todo o treino elegível,
com **log loss de validação como critério principal**. A amostra executável do
estudo anterior permanece identificada como referência histórica. A nova versão
só será adotada nas aulas depois de terminar a comparação e congelar um único
preditor com seu protocolo, pré-processamento e identificação verificável.

## Tarefa e população

O estudo é retrospectivo sobre registros de hospitalização da coorte COVID do
SIVEP-Gripe. O alvo distingue **óbito registrado no código 2 de cura registrada
no código 1 de `EVOLUCAO`**. Registros de óbito por outras causas, ignorados e
vazios não pertencem a esse alvo. O estudo não estima mortalidade por todas as
causas e não demonstra, por si só, utilidade clínica na admissão.

A receita da coorte permanece a do [manifesto Gold](gold/MANIFEST.md). A
ampliação do treino não redefine o alvo, inventa desfechos, corrige valores
clínicos desconhecidos nem transforma o estado `desconhecido` em `não`.
Notificações não são apresentadas como pessoas únicas; a separação por pessoa
não está demonstrada nesta extração.

## Divisão temporal e treinamento

O calendário separa os papéis dos dados antes de qualquer amostragem ou
balanceamento. O protocolo registra os limites exatos e as contagens lidas da
Gold. A referência sem balanceamento usa **todos os registros do período
de treino**. Os candidatos com pesos usam essas mesmas linhas; os candidatos
com redução ou síntese transformam apenas o treino, a partir desse conjunto
completo. A validação e a avaliação temporal preservam os registros reais e
sua distribuição observada.

A amostra de treino da versão anterior foi uma decisão operacional para
reprodução das aulas. Não era parte da PFI. Ela não é usada como limite de
volume desta nova seleção.

## Critério e comparação

Antes dos ajustes, `srag_51_course_study.py` grava um protocolo contendo o hash
da Gold, as variáveis, os limites temporais, as versões da pilha, a semente,
os candidatos e suas configurações. A busca é finita e declarada. O vencedor
é o candidato com menor log loss de validação; empates numéricos exatos são
resolvidos por ordem determinística dos identificadores. Essa regra não é um
teste de equivalência estatística nem uma garantia de melhor família universal.

A comparação inclui baseline de prevalência, modelo linear de probabilidade,
regressão logística, árvore, floresta e XGBoost. O modelo linear de
probabilidade é um contraste didático: suas previsões podem sair do intervalo
probabilístico e são limitadas explicitamente para o cálculo da perda.

Pesos de classe, redução da classe majoritária e SMOTENC restrito entram como
candidatos de regressão logística e XGBoost, com configurações próprias. O
SMOTENC restrito reconstitui o calendário e rejeita propostas que violem as
restrições declaradas; não é apresentado como o algoritmo sem modificações.
A preparação sintética é reutilizada, sem misturar validação ou teste, entre
os ajustes que usam a mesma estratégia e semente.

A referência sem balanceamento participa da seleção. **Reconhecer e estudar o
desbalanceamento não obriga a tornar as classes igualmente frequentes.** A
frequência artificial do treino pode alterar as probabilidades; por isso a
comparação usa log loss e avaliação na distribuição real.

## Pré-processamento e avaliação

O vocabulário das categorias, a imputação, a padronização e os amostradores
são ajustados somente com o treino. Categorias novas na avaliação têm uma
regra explícita. O pipeline salvo inclui essas transformações, evitando que
cada aula reconstrua uma versão diferente do preditor.

ROC-AUC, average precision, Brier e curvas de calibração complementam o critério
principal. Log loss e Brier avaliam previsões probabilísticas; não isolam a
calibração. Sensibilidade e especificidade em um limiar descritivo não são uma
escolha de política clínica.

Nesta rodada, as probabilidades são avaliadas **sem recalibração**. Uma
comparação futura de calibradores precisaria separar os dados usados para
ajustá-los dos dados usados para selecionar e avaliar, preservando a ordem
temporal.

O teste histórico já foi observado em estudos anteriores. O novo procedimento
não o usa para escolher o vencedor, mas sua reutilização continua sendo um
**backtest exploratório**, não uma confirmação independente. Novas decisões
baseadas nele exigem essa mesma identificação.

## Modelo único e adoção nas aulas

A seleção é congelada antes de calcular os resultados do teste. O artefato
canônico inclui o pipeline treinado, os hiperparâmetros e o hash do protocolo.
Modelos e caches ficam fora do repositório; as fontes, os resultados agregados
e a identificação da versão ficam versionados.

A PFI vem depois do treinamento e da seleção: altera as entradas de avaliação
com o preditor fixo. Trocar o modelo exige recalcular as explicações, o exemplar
quando aplicável, as figuras e os textos dependentes. Uma diferença pequena de
AUC entre modelos não autoriza transferir previsões ou importâncias.

A cobertura didática segue a numeração própria do repositório: a PFI está no
módulo 06 e corresponde ao capítulo 23 de Molnar. Isso não significa que todos
os capítulos intermediários já tenham sido implementados. A síntese ampliada
fica no [relatório do modelo global e PFI](../../reports/02-modelo-global-pfi/README.md).

### Critério para chamar uma aula de migrada

O [loader da referência](../../tools/srag_63_course_reference.py) consulta o
pipeline congelado diretamente nas entradas brutas. Os consumidores novos não
usam o helper histórico que distingue a codificação pela classe Python do
estimador: um wrapper genérico não é reconhecido por aquela heurística.

| Método | Conferência exigida antes da adoção |
|---|---|
| Ceteris paribus e ICE | Usar o preditor carregado, selecionar novamente exemplares e painéis declarados e recalcular curvas e conclusões. Experimentos de retreinamento ficam identificados como estudos separados. |
| LIME | Reconstruir as entradas brutas sem perda e consultar o mesmo pipeline; revisar as frequências da vizinhança. O ajuste do explicador local permanece, pois ele não é o preditor explicado. |
| Contrafactuais | Recalcular exemplar e candidatos, manter o calendário coerente ao alterar o tempo e tratar explicitamente a ausência de candidatos ou soluções. |
| SHAP | Escolher uma implementação compatível com a família vencedora e conferir a escala e a soma das atribuições. Rotinas nativas de XGBoost não são uma interface genérica para qualquer vencedor. |
| PFI | Recalcular perdas, ordens, ranking e janela didática; atualizar gráfico, probabilidades e metadados juntos. A igualdade com probabilidades históricas não é um requisito para um modelo novo. |

Cada caderno adotado deve imprimir a identificação do mesmo modelo e produzir
novamente seus próprios resultados. Compartilhar o preditor não obriga todos
os métodos a explicarem a mesma pessoa ou a usarem o mesmo conjunto de apoio.
Um background de explicação declarado também não reduz retroativamente os
dados com que o preditor foi treinado.

## Evidência e reprodução

O [walkthrough do estudo](notebooks/srag_course_study_walkthrough.ipynb) lê o
registro agregado e explica o protocolo. O [internals](notebooks/srag_course_study_internals.ipynb)
confere as guardas, a seleção e a integridade dos resultados. A execução
completa usa a Gold local, grava arquivos fora do repositório e não roda
silenciosamente ao abrir um notebook de aula.

Referências metodológicas: [métricas conforme o objetivo](https://scikit-learn.org/stable/modules/model_evaluation.html#which-scoring-function-should-i-use),
[calibração](https://scikit-learn.org/stable/modules/calibration.html) e
[reamostragem somente no treino](https://imbalanced-learn.org/stable/common_pitfalls.html).
