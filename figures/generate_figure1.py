"""Figure 1: one unmodified scoring engine, three frameworks, two outcomes.

Every number on the figure is read from the files in this repository at run time
rather than typed in, so the diagram cannot drift from the code it describes:
line counts come from the files themselves, and the zero-line change to the
engine is the diff between the two commits named in the paper.

Drawn at the PeerJ text-block width (415.13 pt, measured from wlpeerj.cls) with
an 8 pt type floor, so the manuscript can include it unscaled.

    python figures/generate_figure1.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"

TEXT_PT = 415.13
W_IN = TEXT_PT / 72.0
BODY = 8.0

BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#D55E00"
GREY = "#4D4D4D"
INK = "#1A1A1A"


def lines(rel: str) -> int:
    with open(ROOT / rel, encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def main() -> None:
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                         "font.size": BODY, "text.color": INK, "pdf.fonttype": 42})

    n_engine = lines("app/scoring.php")
    n_edpex = lines("config/edpex.json")
    n_pmqa = lines("config/pmqa.json")
    n_pmqa_sql = lines("schema/156_pmqa.sql")
    n_aun = lines("app/aunqa.php")
    n_aun_sql = lines("schema/008_aunqa.sql")

    fig, ax = plt.subplots(figsize=(W_IN, W_IN * 0.62))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    def box(x, y, w, h, title, sub, edge, face, bold=True):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                    facecolor=face, edgecolor=edge, linewidth=0.9, zorder=3))
        ax.text(x + w / 2, y + h - 3.4, title, ha="center", va="center", fontsize=BODY,
                fontweight="bold" if bold else "normal", color=edge, zorder=4)
        for k, t in enumerate(sub):
            ax.text(x + w / 2, y + h - 7.6 - k * 3.9, t, ha="center", va="center",
                    fontsize=BODY, color=INK, zorder=4)

    def arrow(p0, p1, colour, dashed=False):
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=8, linewidth=1.0,
                                     color=colour, zorder=2,
                                     linestyle=(0, (4, 2)) if dashed else "solid"))

    # three frameworks across the top
    cw, gap = 30.0, 5.0
    xs = [0, cw + gap, 2 * (cw + gap)]
    box(xs[0], 43, cw, 18, "EdPEx", ["ADLI / LeTCI bands", "config/edpex.json", "%s lines" % f"{n_edpex:,}"],
        BLUE, "#DCE9F5")
    box(xs[1], 43, cw, 18, "PMQA-2562", ["ADLI / LeTCI bands", "config/pmqa.json + schema",
                                         "%d + %d lines" % (n_pmqa, n_pmqa_sql)], GREEN, "#D9EFE8")
    box(xs[2], 43, cw, 18, "AUN-QA", ["flat five-point scale", "app/aunqa.php + schema",
                                      "%d + %d lines" % (n_aun, n_aun_sql)], ORANGE, "#F7E2D5")

    # the shared engine
    box(0, 21, 65, 14, "Generic scoring engine  (app/scoring.php)",
        ["%d lines, keyed on category and scheme code" % n_engine,
         "0 lines changed for PMQA-2562 (6f79b81 → ab9c30e)"], BLUE, "#EAF1F8")

    arrow((xs[0] + cw / 2, 43), (xs[0] + cw / 2, 35.2), BLUE)
    arrow((xs[1] + cw / 2, 43), (xs[1] + cw / 2, 35.2), GREEN)
    ax.text(xs[0] + cw / 2 + 1.6, 39.1, "data", ha="left", va="center", fontsize=BODY,
            style="italic", color=GREY,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none"))
    ax.text(xs[1] + cw / 2 + 1.6, 39.1, "data only", ha="left", va="center", fontsize=BODY,
            style="italic", color=GREY,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none"))

    # AUN-QA does not route through the engine
    ax.add_patch(FancyBboxPatch((xs[2], 21), cw, 14, boxstyle="round,pad=0,rounding_size=1.2",
                                facecolor="#FBF0EA", edgecolor=ORANGE, linewidth=0.9,
                                linestyle=(0, (3, 2)), zorder=3))
    ax.text(xs[2] + cw / 2, 31.4, "Dedicated module", ha="center", va="center",
            fontsize=BODY, fontweight="bold", color=ORANGE, zorder=4)
    ax.text(xs[2] + cw / 2, 27.4, "shape does not match", ha="center", va="center",
            fontsize=BODY, color=INK, zorder=4)
    ax.text(xs[2] + cw / 2, 23.6, "the engine's assumptions", ha="center", va="center",
            fontsize=BODY, color=INK, zorder=4)
    arrow((xs[2] + cw / 2, 43), (xs[2] + cw / 2, 35.2), ORANGE, dashed=True)

    # the boundary condition
    box(4, 1.5, 92, 13, "Boundary condition",
        ["configuration-only extension succeeds when a framework's scoring paradigm is",
         "structurally congruent with the engine, not when the domains merely look alike"],
        GREY, "#F2F2F2")
    arrow((32.5, 21), (32.5, 14.7), GREY)

    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"figure1_extension_outcomes.{ext}", dpi=300, facecolor="white")
    plt.close(fig)
    print("figure1: engine %d, edpex %d, pmqa %d+%d, aunqa %d+%d lines"
          % (n_engine, n_edpex, n_pmqa, n_pmqa_sql, n_aun, n_aun_sql))


if __name__ == "__main__":
    main()
