# `report/figuras/` — as figuras dos módulos, preparadas para o relatório

Cópias derivadas dos PNG commitados em `modules/NN-slug/figures/`, com **a
faixa de cabeçalho removida**.

As figuras dos módulos trazem, dentro da imagem, um kicker (`§1 · O FEIXE`) e
uma manchete com o achado — convenção de caderno e de slide, onde a figura
precisa se explicar sozinha. Num artigo isso duplica a legenda: a manchete
"Aos 80 anos o feixe vale 0,481 em 2020 e 0,303 em 2024" repete, dentro da
imagem e com número, o que a `Figura 3:` diz logo abaixo. Periódicos pedem
figura sem título interno pelo mesmo motivo.

O corte é automático e mede ~13% da altura em todas: `report/recortar_figuras.py`
acha o maior vão branco no terço superior da imagem, que é sempre o espaço
entre a manchete e a área do gráfico, e corta ali. Rótulos de painel (`A · o
modelo caixa-preta`) ficam, porque esses um artigo usa.

**As figuras dos módulos não são tocadas.** Este diretório é derivado: apagá-lo
e rodar o script de novo reproduz tudo. Se uma figura de módulo for regerada,
rode o script outra vez.
