"""Cover image for README and Kaggle (EN and PT): one car, its FIPE price over time and part of its specifications.

    python scripts/make_cover.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INK, MUTED, LINE, BG, BLUE = "#111111", "#555555", "#e6e6e6", "#fdfdfc", "#2a78d6"
CODE, YEAR = "003367-7", 2012
TEXT = {
    "en": {"suffix": "", "title": "FIPE prices and vehicle specifications",
           "sub": "Brazil · 1.65M prices, 2020–2026 · 37,794 versions · vehicle × product matches",
           "car": "Ford EcoSport Freestyle 1.6 16V Flex 2012 · FIPE {code}",
           "specs": ["115 cv (ethanol) / 110 cv (gasoline)", "Trunk: 296 l", "Driver and passenger airbags", "ABS: yes"],
           "price": "FIPE price, R$"},
    "pt": {"suffix": ".pt-BR", "title": "Tabela FIPE e ficha técnica de veículos",
           "sub": "Brasil · 1,65 mi de preços, 2020–2026 · 37.794 versões · casamento veículo × produto",
           "car": "Ford EcoSport Freestyle 1.6 16V Flex 2012 · FIPE {code}",
           "specs": ["115 cv (etanol) / 110 cv (gasolina)", "Porta-malas: 296 l", "Airbag do motorista e do passageiro", "ABS: sim"],
           "price": "Preço FIPE, R$"},
}
for family in ("Inter", "DejaVu Sans"):
    try:
        matplotlib.font_manager.findfont(family, fallback_to_default=False)
        plt.rcParams["font.family"] = family
        break
    except ValueError:
        continue


def main() -> None:
    p = pd.read_csv(ROOT / "sample" / "precos_sample.csv", dtype={"codigo_fipe": str}, parse_dates=["referencia"])
    s = p[(p.codigo_fipe == CODE) & (p.ano_modelo == YEAR)].sort_values("referencia").set_index("referencia").valor
    for lang, t in TEXT.items():
        fig = plt.figure(figsize=(11.2, 5.6), dpi=100)
        fig.patch.set_facecolor(BG)
        fig.text(0.04, 0.86, t["title"], fontsize=26, weight="bold", color=INK)
        fig.text(0.04, 0.78, t["sub"], fontsize=12.5, color=MUTED)
        fig.text(0.04, 0.66, t["car"].format(code=CODE), fontsize=13, weight="bold", color=INK)
        for i, line in enumerate(t["specs"]):
            fig.text(0.05, 0.57 - i * 0.075, "•  " + line, fontsize=12.5, color=INK)
        ax = fig.add_axes([0.52, 0.12, 0.44, 0.5])
        ax.set_facecolor(BG)
        gap = s.index.to_series().diff() > pd.Timedelta(days=62)   # February 2023 -> October 2026 was not collected
        part = gap.cumsum()
        for k in part.unique():
            seg = s[part.values == k]
            ax.plot(seg.index, seg.values / 1000, color=BLUE, linewidth=2.5)
        for d in s.index[gap.values]:
            prev = s.index[s.index.get_loc(d) - 1]
            ax.plot([prev, d], [s[prev] / 1000, s[d] / 1000], color=BLUE, linewidth=1.5, linestyle=(0, (2, 3)))
        for d in (s.index[0], s.idxmax(), s.index[-1]):
            ax.annotate(f"{s[d] / 1000:.1f} mil".replace(".", ",") if lang == "pt" else f"{s[d] / 1000:.1f}k", (d, s[d] / 1000),
                        xytext=(0, 8), textcoords="offset points", ha="center", fontsize=10, color=INK)
            ax.plot([d], [s[d] / 1000], "o", color=BLUE, markersize=7, markeredgecolor=BG, markeredgewidth=2)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(LINE)
        ax.tick_params(colors=MUTED, labelsize=9, length=0)
        ax.set_yticks([])
        ax.xaxis.set_major_locator(matplotlib.dates.YearLocator())
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y'))
        ax.set_title(t["price"], loc="left", fontsize=10, color=MUTED)
        ax.set_ylim(s.min() / 1000 * 0.9, s.max() / 1000 * 1.12)
        out = ROOT / "docs" / "img" / f"cover{t['suffix']}.png"
        fig.savefig(out, facecolor=BG)
        plt.close(fig)
        print(out)


if __name__ == "__main__":
    main()
