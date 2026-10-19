# `reports/01-metodos-locais/figuras/`

**Figuras de uma entrega histórica.** Preserve estes arquivos. O gerador e os
cadernos compatíveis pertencem à
[revisão `509a33a`](https://github.com/wbendinelli/interpretable-ml-lectures/tree/509a33af8b629bcc9369a1e2653b4c4fa5d9f814/reports/01-metodos-locais).
Estude sua reprodução somente em um checkout separado dessa revisão; os
notebooks atuais não usam os caminhos esperados pelo gerador histórico.
O [índice dos relatórios](../../README.md) identifica a edição viva e as
correções posteriores. A descrição abaixo registra o processo da entrega.

As sete figuras do relatório, geradas por
`reports/01-metodos-locais/gerar_figuras.py`. O script roda os 5 walkthroughs
de novo, fora da árvore do git, com `SAPIANS_ESCALA_TEXTO=1.5` (a mesma
figura do caderno, com toda fonte 50% maior; 1.35 nos cadernos 01 e 05, onde a
1.5 o corte levava um tick e um rótulo saía do canvas) e então recorta o
cabeçalho com a mesma função de `recortar_figuras.py`, `altura_do_cabecalho`.
Uma figura fica na escala do caderno: `shap_passo_5_dependencia`, cujo rótulo
vertical da barra de cor não cabe no canvas em nenhuma escala acima de 1,0; ela
é o recorte da figura commitada do módulo 05, como antes. As escalas vivem em
`ESCALA_POR_CADERNO` e a exceção em `SEM_ESCALA`, no próprio script.

Por que a escala maior: as figuras de módulo (`modules/NN-slug/figures/`)
são desenhadas para o caderno, 9,6 a 12 polegadas de largura. O Typst do
relatório as encolhe para os 170 mm da coluna do artigo, e um rótulo de eixo
de 7,5 pt sai impresso a 4,2-5,2 pt, ilegível. Gerar a mesma figura maior faz
o encolhimento chegar num tamanho que ainda se lê.

Por que o corte: as figuras de módulo trazem, dentro da imagem, um kicker
(`§1 · O FEIXE`) e uma manchete com o achado, a convenção certa para um
caderno, onde a figura precisa se explicar sozinha, e a errada para um
artigo, onde a legenda faz esse trabalho e a manchete vira repetição.
Rótulos de painel (`A · o modelo caixa-preta`) ficam, porque esses um artigo
usa.

**Na revisão entregue, os cadernos e `modules/*/figures/` não eram alterados.**
`gerar_figuras.py` lia o `figures_generated/` de cada caderno, então não
escrevia de volta em `modules/`. Nos notebooks atuais, as saídas ficam em
diretórios externos. Apagar esta pasta e executar o gerador atual não é uma
receita válida de recuperação da entrega.

**Não rode `recortar_figuras.py` depois deste script.** Ele lê
`modules/*/figures/` na escala 1,0 e reescreveria por cima estas figuras
legíveis com as pequenas.
