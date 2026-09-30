"""Draw the cost–quality frontier of the thesis from the committed router report.

    python -m scripts.thesis.figures

Mermaid charts space categories evenly, which would misplace the points of a
frontier, so this figure is plotted with matplotlib from
``benchmarks/router/v1/report.json`` and written as PNG (for Word) and SVG.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPORT = Path("benchmarks/router/v1/report.json")
OUT = Path("docs/tfc/tesis/figuras/frontera")
CURVE, MARK, INK = "#1f4e79", "#b03a2e", "#1a1a1a"
# (baseline key, label, text offset in points)
BASELINES = (
    ("all_local", "todo local", (-6, 10)),
    ("heuristic_premium_frontier", "heurística de dos reglas", (8, 14)),
    ("all_economy", "todo económico", (-8, 10)),
    ("all_frontier", "todo frontier", (-8, 10)),
)


def frontier_figure(report: dict):
    pareto = sorted(report["learned"]["pareto"], key=lambda p: (p["quality"], p["cost"]))
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
    ax.plot([p["quality"] for p in pareto], [p["cost"] * 1000 for p in pareto],
            color=CURVE, linewidth=2, label="router aprendido (frontera fuera de fold)")
    for key, label, offset in BASELINES:
        b = report["baselines"][key]
        ax.scatter([b["quality"]], [b["cost"] * 1000], marker="s", s=36, color=INK, zorder=3)
        ax.annotate(label, (b["quality"], b["cost"] * 1000), textcoords="offset points",
                    xytext=offset, ha="left" if offset[0] > 0 else "right", fontsize=9)
    n = report["nested"]["0.95"]
    ax.scatter([n["quality"]], [n["cost"] * 1000], s=60, color=MARK, zorder=4)
    ax.annotate(f"objetivo 0.95, estimación anidada: USD {n['cost'] * 1000:.2f}",
                (n["quality"], n["cost"] * 1000), textcoords="offset points", xytext=(-12, 2),
                ha="right", va="bottom", fontsize=9, color=MARK)
    ax.set_xlabel("Calidad (proporción de respuestas sustituibles)")
    ax.set_ylabel("Costo (USD cada 1000 prompts)")
    ax.set_xlim(0.74, 1.01)
    ax.set_ylim(0, 2.7)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def write_frontier(report: dict, stem: Path) -> list[Path]:
    fig = frontier_figure(report)
    paths = [stem.with_suffix(".png"), stem.with_suffix(".svg")]
    fig.savefig(paths[0], metadata={"Software": None})
    fig.savefig(paths[1], metadata={"Date": None})
    plt.close(fig)
    return paths


def main() -> int:
    for path in write_frontier(json.loads(REPORT.read_text(encoding="utf-8")), OUT):
        print(f"figure → {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
