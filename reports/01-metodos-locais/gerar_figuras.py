#!/usr/bin/env python3
"""Regenera as 7 figuras do relatório numa escala de texto legível a 170 mm.

`recortar_figuras.py` corta o cabeçalho das figuras já commitadas em
modules/NN-slug/figures/: certas para o caderno (9,6 a 12 pol.), pequenas
demais depois que o Typst as encolhe para a coluna do artigo (170 mm), onde um
rótulo de tick de 7,5 pt sai a 4,2 a 5,2 pt impressos. Este script roda os 5
walkthroughs de novo, FORA da árvore (nunca --inplace), com
SAPIANS_ESCALA_TEXTO=1.5 (1.35 onde 1.5 não cabe; ver ESCALA_POR_CADERNO), a
mesma figura com letra maior, e corta com a MESMA função de
recortar_figuras.py. Uma figura fica na escala 1,0 (ver SEM_ESCALA). Os cadernos e modules/*/figures/ não mudam:
figures_generated/ de cada caderno é git-ignored e só este script lê de lá.

NÃO rode recortar_figuras.py depois deste script: ele lê modules/*/figures/
(escala 1,0) e reescreveria por cima os PNGs legíveis com os pequenos.

    python3 reports/01-metodos-locais/gerar_figuras.py
    python3 reports/01-metodos-locais/gerar_figuras.py --sem-executar
    python3 reports/01-metodos-locais/gerar_figuras.py --escala 1.35 --so lime
"""

import argparse
import os
import pathlib
import subprocess
import sys
import tempfile
import time

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from recortar_figuras import altura_do_cabecalho  # a MESMA detecção de corte

REPO = pathlib.Path(__file__).resolve().parents[2]
JUPYTER = REPO / ".venv" / "bin" / "jupyter"
SAIDA = REPO / "reports" / "01-metodos-locais" / "figuras"
ESCALA_PADRAO = "1.5"
# Por caderno, quando 1,5 não cabe: a banda do título e os rótulos com
# `fontsize=` fixo não escalam, e a 1,5 o corte levava o tick de cima do
# cp_passo_4 e o rótulo da barra de cor do shap_passo_5 saía do canvas.
ESCALA_POR_CADERNO = {"cp": "1.35", "shap": "1.35"}
# Figuras que ficam na escala 1,0, recortadas da figura commitada do módulo:
# o rótulo vertical da barra de cor do shap_passo_5 não cabe no canvas em
# nenhuma escala acima de 1,0 (medido 2026-09-04: cortado nas duas pontas).
SEM_ESCALA = {
    "shap_passo_5_dependencia": "modules/05-shap/figures/shap_passo_5_dependencia.png",
}
TIMEOUT_CELULA = 1200  # s por célula, o mesmo valor de .github/workflows/ci.yml
# medido 2026-09-04: 68s nesta máquina (lime 22 + shap 22 + cf 9 + cp 8 + ice 7)

CADERNOS = {
    "cp": (
        "modules/01-ceteris-paribus/notebooks/cp_walkthrough.ipynb",
        ["cp_passo_1b_modelos", "cp_passo_4_restrito"],
    ),
    "ice": ("modules/02-ice/notebooks/ice_walkthrough.ipynb", ["ice_passo_1_feixe"]),
    "lime": (
        "modules/03-lime/notebooks/lime_walkthrough.ipynb",
        ["lime_passo_a_passo"],
    ),
    "cf": (
        "modules/04-counterfactual/notebooks/cf_walkthrough.ipynb",
        ["cf_passo_3_painel"],
    ),
    "shap": (
        "modules/05-shap/notebooks/shap_walkthrough.ipynb",
        ["shap_passo_1_waterfall", "shap_passo_5_dependencia"],
    ),
}


def executar(nb_rel: str, escala: str, scratch: str) -> None:
    """Roda `nb_rel` FORA da árvore, com o texto na escala `escala`.

    Sem `--ExecutePreprocessor.cwd`: o cwd do kernel precisa ser a própria
    pasta do caderno (o default do nbconvert), senão a célula de setup não
    acha `tools/` pelo sentinela de caminho e cai no `git clone` do Colab.
    """
    ambiente = os.environ | {
        "SAPIANS_ESCALA_TEXTO": escala,
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    }
    subprocess.run(
        [
            str(JUPYTER),
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            f"--ExecutePreprocessor.timeout={TIMEOUT_CELULA}",
            "--output-dir",
            scratch,
            nb_rel,
        ],
        cwd=REPO,
        check=True,
        env=ambiente,
    )


def cortar(origem: pathlib.Path, destino: pathlib.Path) -> None:
    """Recorta o cabeçalho de `origem` com a MESMA função de recortar_figuras.py."""
    if not origem.exists():
        raise SystemExit(f"AUSENTE  {origem}")
    im = Image.open(origem)
    corte = altura_do_cabecalho(im)
    if not 0 < corte < im.height * 0.30:
        raise SystemExit(f"SUSPEITO {origem.name}: corte em {corte} de {im.height}")
    im.crop((0, corte, im.width, im.height)).save(destino)
    print(
        f"{origem.name:<32} cabeçalho de {corte}px "
        f"({100 * corte / im.height:.0f}%) removido"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--escala",
        default=None,
        help="força este fator de SAPIANS_ESCALA_TEXTO em todos os cadernos "
        "(default: 1,5, ou o valor de ESCALA_POR_CADERNO)",
    )
    ap.add_argument(
        "--sem-executar",
        action="store_true",
        help="pula o nbconvert; reusa o figures_generated/ já no lugar",
    )
    ap.add_argument(
        "--so",
        action="append",
        choices=list(CADERNOS),
        metavar="CADERNO",
        help="roda/recorta só este caderno (repetível); default: os 5",
    )
    args = ap.parse_args()
    chaves = [c for c in CADERNOS if not args.so or c in args.so]

    SAIDA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sapians-relatorio-") as scratch:
        for chave in chaves:
            nb_rel, nomes_base = CADERNOS[chave]
            escala = args.escala or ESCALA_POR_CADERNO.get(chave, ESCALA_PADRAO)
            if not args.sem_executar:
                msg = f"[{chave}] executando {nb_rel} (escala {escala})..."
                print(msg, file=sys.stderr)
                inicio = time.monotonic()
                executar(nb_rel, escala, scratch)
                print(f"[{chave}] {time.monotonic() - inicio:.0f}s", file=sys.stderr)
            pasta = REPO / pathlib.Path(nb_rel).parent / "figures_generated"
            for nome_base in nomes_base:
                if nome_base in SEM_ESCALA:
                    origem = (
                        REPO / SEM_ESCALA[nome_base]
                    )  # figura do módulo, escala 1,0
                else:
                    origem = pasta / f"{nome_base}.png"
                cortar(origem, SAIDA / f"{nome_base}.png")

    # Escopado a notebooks/ e figures/, não a modules/ inteiro: o resto de
    # modules/ (READMEs, outlines) pode mudar por trabalho concorrente de
    # outro agente no mesmo worktree, sem relação nenhuma com este script.
    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "modules/*/notebooks",
            "modules/*/figures",
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if status.strip():
        print(
            f"modules/*/notebooks ou modules/*/figures sujo:\n{status}", file=sys.stderr
        )
        return 1
    print("modules/*/notebooks e modules/*/figures intocados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
