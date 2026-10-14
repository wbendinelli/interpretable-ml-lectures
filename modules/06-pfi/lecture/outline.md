# Aula — PFI no modelo SRAG/COVID (forma viva)

Este é o roteiro editável da apresentação interativa em inglês. As notas
do professor e os cadernos são em português. Toda medição citada aqui é
impressa por [`pfi_walkthrough.ipynb`](../notebooks/pfi_walkthrough.ipynb);
as verificações independentes ficam em
[`pfi_internals.ipynb`](../notebooks/pfi_internals.ipynb).
Após esta primeira indicação, os ponteiros usam `walkthrough §N`.

## Arco

Partir da pergunta global, mostrar uma coluna se movendo e seguir o
erro. Depois repetir o experimento, ler o ranking e qualificar a
conclusão quando as entradas dependem umas das outras. Molnar,
capítulo 23, é a referência teórica; Raschka fornece a sequência visual.

## 1. Abrir com a pergunta e localizar o método

**Telas `cover` e `61`.** Dizer: “Queremos entender quanto este modelo
depende de uma entrada para manter seu desempenho.” Apontar a passagem
da visão geral de seleção de features para PFI. O mapa é contexto
didático: medir importância não é, por si só, selecionar e retreinar
um conjunto menor de entradas.

## 2. Uma coluna muda; o modelo permanece

**Tela `62`.** Apontar a coluna original e sua cópia. Os símbolos do
esquema público representam linhas; não são fichas individuais nem
valores usados para obter o gráfico. Mostrar a ordem dos passos:
copiar, embaralhar, prever com o mesmo modelo, avaliar.

Ao passar de idade para saturação baixa, apontar o retorno ao original:
as alterações não se acumulam. Os rótulos observados ficam fixos.
A operação real, com tipos preservados e ordens registradas, é conferida
no walkthrough §3.

## 3. Ler antes/depois antes de ler o ranking

**Tela `63`.** O erro de referência do teste é Brier **0,1308**
(walkthrough §2). Começar pelo significado: comparar probabilidade
prevista de óbito e desfecho observado, elevar a distância ao quadrado
e calcular a média. Erro de probabilidades não equivale à contagem
de classificações erradas num limiar.

Mostrar a diferença como aumento absoluto do mesmo erro; depois a razão
como comparação relativa com a referência. A idade tem diferença média
**0,0234**, com SD **0,0007**; saturação baixa, **0,0043**, com SD
**0,0003** (walkthrough §4–§5). Não transformar esses números em mudança
na mortalidade nem em efeito de aumentar a idade.

Apontar a haste de SD e explicar seu condicionamento. A barra resume
repetições; não é a perda de uma única ficha. Na razão, a linha da
referência marca erro igual ao original; uma permutação que melhora
o desempenho pode ficar abaixo dela (§5).

## 4. Importância não decide sozinha a seleção

**Tela `65`.** Dizer: “Este diagnóstico mantém o preditor fixo; um
estudo de seleção requer sua própria avaliação.” O slide distingue
importância por permutação na avaliação e um estudo de seleção que
retreina modelos com outro conjunto de entradas.
Apontar o papel da métrica e da população avaliadas.

## 5. De onde veio o modelo que estamos explicando?

**Telas `66` e `66-selection`.** Mostrar Bronze → Silver → Gold,
coorte e alvo. Usar o bloco de dados para explicar o contrato, sem
ler todas as regras de tratamento. O estado desconhecido de uma
categoria não deve ser apresentado como ausência da condição.

Apontar treino até 2022, validação em 2023 e teste histórico em 2024.
Explicar que a seleção registrada precede esta aula e que o modelo
de referência permaneceu sem balanceamento. A explicação é exploratória
porque esse teste já foi observado (walkthrough §1). Detalhes da busca
e do tratamento estão nos documentos do módulo 00; esta aula não os
executa novamente para escolher outro vencedor.

## 6. O algoritmo, lido no código que executa

**Telas `67` a `70`.** Apontar o predictor já ajustado, o erro original,
a cópia da matriz, a coluna permutada e as novas probabilidades. O
walkthrough §3 exibe o fonte compartilhado de `srag_70_explain` e
reproduz o trace de idade e saturação baixa. Atribuir o erro após
permutação ao diagnóstico, sem chamar isso de “modelo retreinado”.

**Tela `71`.** Seguir o `for`: gerar a ordem, construir a matriz da
repetição, prever e registrar o erro. O protocolo tem **50** ordens
com semente **42** (walkthrough §1). Pausar ou avançar uma repetição
para acompanhar o ponto, o resultado mais recente, a média acumulada
e o SD. O número de repetições é uma escolha registrada; não prova
convergência nem cobre incerteza do treino.

## 7. O que podemos concluir — e o que falta para outras perguntas

**Tela `73`.** Destacar a leitura global e a possibilidade de avaliar
um preditor fixo. Para cada limite, dizer a consequência: depende
da métrica e da avaliação; não mostra direção do efeito; combina
efeitos e dependências; o SD mostrado descreve os embaralhamentos.
Walkthrough §7 reúne a leitura do livro e sua aplicação neste estudo.

## 8. Um exemplo final de dependência

**Tela `dependence-results`.** Começar pela opção conjunta: a mesma
linha doadora fornece cardiopatia e diabetes, conservando o par.
Mostrar que outras relações podem se romper. O gráfico compara
diagnósticos diferentes; a barra conjunta não é evidência suficiente
de interação causal ou de redundância.

Na opção por subgrupos, mostrar cardiopatia sendo embaralhada dentro
dos estados originais de diabetes. Diabetes fica fixa, o modelo também.
Comparar o erro com o original de cada grupo e agregar pelo tamanho
dos grupos (walkthrough §6). Esse é o vínculo com a abordagem de
subgrupos de Molnar; condicionar somente em diabetes não implementa
PFI condicional dada toda a ficha.

## 9. Fechar com a pergunta correta

**Tela `thanks`.** Retomar: “De qual informação este modelo depende
para manter o desempenho nesta avaliação?” Encerrar com a escolha
da pergunta — global, individual ou dentro de grupos — e dar os
créditos a Molnar, Raschka e à base SRAG.

## Objeções para a discussão

- **“Você apagou a variável?”** Não. A coluna continua presente com os
  valores redistribuídos; o predictor não foi retreinado.
- **“Uma importância baixa permite remover a entrada?”** O diagnóstico
  não substitui uma comparação de modelos e sua avaliação temporal.
- **“Brier é só calibração?”** Ele avalia probabilidades; não é uma
  estatística exclusiva de calibração. Esta aula usa sua mudança como
  erro de referência.
- **“Os bigodes são um intervalo de confiança?”** A haste da apresentação
  mostra SD entre permutações. Os boxplots usam quartis e sua própria
  regra de bigodes. Nenhum dos dois incorpora automaticamente refits
  ou uma amostra futura.
- **“A permutação conjunta resolve toda dependência?”** Preserva o par
  escolhido; as relações com as demais entradas ainda podem mudar.
- **“A abordagem por subgrupos é a PFI condicional completa?”** Aqui,
  a restrição considera diabetes. O condicionamento não cobre todas
  as outras entradas.

## Referências da aula

As entradas completas estão no [README do módulo](../README.md#referências):
Molnar, capítulo 23; Raschka, aula de feature selection; e a documentação
oficial do algoritmo de permutation importance do scikit-learn.
