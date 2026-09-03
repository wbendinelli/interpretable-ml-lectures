#!/usr/bin/env python3
"""Prepara as figuras dos módulos para o relatório, tirando o cabeçalho.

As figuras de módulo trazem dentro da imagem um kicker (`§1 · O FEIXE`) e uma
manchete com o achado. É a convenção certa para um caderno, onde a figura
precisa se explicar sozinha, e a errada para um artigo, onde a legenda faz
esse trabalho e a manchete vira repetição.

O corte acha o maior vão branco no terço superior da imagem — sempre o espaço
entre a manchete e a área do gráfico — e corta no meio dele. Rótulos de painel
(`A · o modelo caixa-preta`) ficam, porque esses um artigo usa.

As figuras dos módulos não são tocadas. Rode da raiz do repositório:

    python report/recortar_figuras.py
"""

import pathlib
import sys

from PIL import Image

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "report" / "figuras"

FIGURAS = [
    "modules/01-ceteris-paribus/figures/cp_passo_1b_modelos.png",
    "modules/01-ceteris-paribus/figures/cp_passo_4_restrito.png",
    "modules/02-ice/figures/ice_passo_1_feixe.png",
    "modules/03-lime/figures/lime_passo_a_passo.png",
    "modules/04-counterfactual/figures/cf_passo_3_painel.png",
    "modules/05-shap/figures/shap_passo_1_waterfall.png",
    "modules/05-shap/figures/shap_passo_5_dependencia.png",
]


def altura_do_cabecalho(im: Image.Image) -> int:
    """Onde termina o cabeçalho: o meio do maior vão branco no topo."""
    cinza = im.convert("L")
    largura, altura = cinza.size
    px = cinza.load()
    cheia = [
        min(px[x, y] for x in range(0, largura, 3)) < 245 for y in range(altura)
    ]
    limite, vaos, y = int(altura * 0.30), [], 0
    while y < limite:
        if cheia[y]:
            y += 1
            continue
        inicio = y
        while y < altura and not cheia[y]:
            y += 1
        if inicio > 0:  # a margem branca do topo não conta
            vaos.append((inicio, y - inicio))
    if not vaos:
        return 0
    inicio, alto = max(vaos, key=lambda v: v[1])
    return inicio + alto // 2


def main() -> int:
    SAIDA.mkdir(parents=True, exist_ok=True)
    for rel in FIGURAS:
        origem = RAIZ / rel
        if not origem.exists():
            print(f"AUSENTE  {rel}", file=sys.stderr)
            return 1
        im = Image.open(origem)
        corte = altura_do_cabecalho(im)
        if not 0 < corte < im.height * 0.30:
            print(f"SUSPEITO {origem.name}: corte em {corte} de {im.height}", file=sys.stderr)
            return 1
        im.crop((0, corte, im.width, im.height)).save(SAIDA / origem.name)
        print(f"{origem.name:<32} cabeçalho de {corte}px ({100 * corte / im.height:.0f}%) removido")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
