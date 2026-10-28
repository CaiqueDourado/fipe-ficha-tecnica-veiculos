"""Cover image for README and Kaggle (EN and PT): the three parts of the dataset, each shown with a real record.

    python scripts/make_json.py --fipe 003367-7 --ano 2012 --out docs/example-vehicle.json
    python scripts/make_cover.py

Prices and specifications come from docs/example-vehicle.json (Ford EcoSport Freestyle 2012), the product
matches from docs/example-product.json (wheel caps for the Mercedes GLC 250), the totals from stats.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INK, MUTED, LINE, BG, CARD = "#111111", "#5c5c5c", "#d9dde3", "#fdfdfc", "#ffffff"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
LEVEL = {"alta": AQUA, "media": "#c99a06", "baixa": ORANGE}
VERSION = 37057
TEXT = {
    "en": {"suffix": "", "title": "FIPE prices, specifications and auto parts of Brazilian vehicles",
           "sub": "{precos} FIPE prices 2020–2026 · {fichas} specification versions · {pares} vehicle × product pairs",
           "p1": "FIPE prices", "p1s": "per month, code, model year and fuel",
           "p2": "Specifications", "p2s": "{cols} columns per version (Mobiauto)",
           "p3": "Vehicle × product", "p3s": "catalog product groups, with a warning level",
           "power": "power", "trunk": "trunk", "weight": "weight", "size": "length",
           "items": ["driver airbag", "ABS", "air conditioning", "sunroof"],
           "product": "Wheel center caps, Mercedes GLC 250", "all": "all pairs: ", "models": "{n} models", "gap": "not collected",
           "foot": "Ford EcoSport Freestyle 1.6 16V Flex 2012 · FIPE 003367-7  |  real records from the dataset"},
    "pt": {"suffix": ".pt-BR", "title": "Preços FIPE, ficha técnica e autopeças de veículos do Brasil",
           "sub": "{precos} preços FIPE 2020–2026 · {fichas} versões com ficha técnica · {pares} pares veículo × produto",
           "p1": "Preços FIPE", "p1s": "por mês, código, ano-modelo e combustível",
           "p2": "Ficha técnica", "p2s": "{cols} colunas por versão (Mobiauto)",
           "p3": "Veículo × produto", "p3s": "grupos de produto do catálogo, com nível de alerta",
           "power": "potência", "trunk": "porta-malas", "weight": "peso", "size": "comprimento",
           "items": ["airbag do motorista", "freios ABS", "ar-condicionado", "teto solar"],
           "product": "Calotas de centro de roda, Mercedes GLC 250", "all": "todos os pares: ", "models": "{n} modelos", "gap": "não coletado",
           "foot": "Ford EcoSport Freestyle 1.6 16V Flex 2012 · FIPE 003367-7  |  registros reais do dataset"},
}
ITEMS = ["airbag_motorista", "freios_abs", "ar_condicionado", "teto_solar"]
for family in ("Inter", "DejaVu Sans"):
    try:
        matplotlib.font_manager.findfont(family, fallback_to_default=False)
        plt.rcParams["font.family"] = family
        break
    except ValueError:
        continue


def num(n: float, pt: bool, digits: int = 0) -> str:
    s = f"{n:,.{digits}f}"
    return s.translate(str.maketrans(",.", ".,")) if pt else s


def panel(ax, x, w, color, title, sub):
    ax.add_patch(FancyBboxPatch((x, 6), w, 52, boxstyle="round,pad=0,rounding_size=1.4", fc=CARD, ec=LINE, lw=1.1))
    ax.add_patch(FancyBboxPatch((x, 57.2), w, 0.8, boxstyle="square,pad=0", fc=color, ec="none"))
    ax.text(x + 2, 53, title, fontsize=13, weight="bold", color=INK, va="center")
    ax.text(x + 2, 49.2, sub, fontsize=8.6, color=MUTED, va="center")


def main() -> None:
    stats = json.loads((ROOT / "stats.json").read_text(encoding="utf-8"))
    veh = json.loads((ROOT / "docs" / "example-vehicle.json").read_text(encoding="utf-8"))
    prod = json.loads((ROOT / "docs" / "example-product.json").read_text(encoding="utf-8"))
    year = veh["marcas"][0]["modelos"][0]["anos"][0]
    prices = year["precos"]
    ficha = next(f for f in year["fichas"] if f["id_versao"] == VERSION)

    for lang, t in TEXT.items():
        pt = lang == "pt"
        fig = plt.figure(figsize=(12, 6.2), dpi=100)
        fig.patch.set_facecolor(BG)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 120)
        ax.axis("off")
        ax.text(3, 69, t["title"], fontsize=19, weight="bold", color=INK, va="center")
        sub = t["sub"].format(precos=num(stats["precos"] / 1e6, pt, 2) + (" mi" if pt else "M"),
                              fichas=num(stats["fichas"], pt),
                              pares=num(stats["veiculo_produto"] / 1e6, pt, 1) + (" mi" if pt else "M"))
        ax.text(3, 63.6, sub, fontsize=10.5, color=MUTED, va="center")
        ax.set_ylim(0, 74)

        # 1. prices
        x1, w = 3, 36
        panel(ax, x1, w, BLUE, t["p1"], t["p1s"])
        cax = fig.add_axes([(x1 + 2) / 120, 11 / 74, (w - 4) / 120, 31 / 74])
        cax.set_facecolor(CARD)
        idx = [int(p["referencia"][:4]) * 12 + int(p["referencia"][5:7]) for p in prices]
        vals = [p["valor"] / 1000 for p in prices]
        cut = next(i for i in range(1, len(idx)) if idx[i] - idx[i - 1] > 2)
        cax.plot(idx[:cut], vals[:cut], color=BLUE, lw=2.2)
        cax.plot(idx[cut - 1:cut + 1], vals[cut - 1:cut + 1], color=BLUE, lw=1.3, ls=(0, (2, 3)))
        for i in (0, max(range(len(vals)), key=vals.__getitem__), len(vals) - 1):
            cax.plot(idx[i], vals[i], "o", color=BLUE, ms=6, mec=CARD, mew=1.8)
            cax.annotate(f"R$ {num(prices[i]['valor'], pt)}\n{prices[i]['referencia']}", (idx[i], vals[i]),
                         xytext=(0, 8), textcoords="offset points", ha="center", fontsize=7.6, color=INK)
        cax.text((idx[cut - 1] + idx[cut]) / 2, vals[cut] - 2.4, t["gap"], ha="center", fontsize=7.4,
                 color=MUTED, style="italic")
        cax.set_ylim(min(vals) - 2, max(vals) + 5.5)
        cax.set_xlim(idx[0] - 4, idx[-1] + 4)
        cax.set_xticks([y * 12 + 1 for y in (2020, 2022, 2024, 2026)])
        cax.set_xticklabels(["2020", "2022", "2024", "2026"])
        cax.set_yticks([])
        for s in ("top", "right", "left"):
            cax.spines[s].set_visible(False)
        cax.spines["bottom"].set_color(LINE)
        cax.tick_params(colors=MUTED, labelsize=8, length=0)

        # 2. specifications
        x2 = x1 + w + 2.5
        panel(ax, x2, w, AQUA, t["p2"], t["p2s"].format(cols=stats.get("fichas_colunas", 81)))
        m, md = ficha["motor"], ficha["medidas"]
        cv = m["potencia_cv"].replace(" (Etanol) / ", " / ").replace(" (Gasolina)", "") + " cv"
        rows = [(t["power"], cv), (t["size"], f"{num(md['comprimento_mm'], pt)} mm"),
                (t["weight"], f"{num(md['peso_kg'], pt)} kg"), (t["trunk"], f"{md['porta_malas_l']} l")]
        for i, (k, v) in enumerate(rows):
            y = 42 - i * 4.6
            ax.text(x2 + 2, y, k, fontsize=9.2, color=MUTED, va="center")
            ax.text(x2 + w - 2, y, v, fontsize=9.6, color=INK, va="center", ha="right", weight="bold")
            ax.plot([x2 + 2, x2 + w - 2], [y - 2.5, y - 2.5], color="#eef0f3", lw=0.8)
        for i, (lab, key) in enumerate(zip(t["items"], ITEMS)):
            ok = ficha["itens"].get(key) is True
            ax.text(x2 + 2, 23 - i * 3.4, ("✓  " if ok else "✗  ") + lab, fontsize=9.2,
                    color=AQUA if ok else ORANGE, va="center")
        ax.text(x2 + 2, 8.6, f"versao: {ficha['versao']}", fontsize=7.6, color=MUTED, family="monospace")

        # 3. vehicle x product
        x3 = x2 + w + 2.5
        w3 = 117 - x3
        panel(ax, x3, w3, ORANGE, t["p3"], t["p3s"])
        ax.text(x3 + 2, 43, t["product"], fontsize=9.6, color=INK, weight="bold", va="center")
        ax.text(x3 + 2, 39.6, f"group_id {prod['grupo']['group_id']}", fontsize=7.8, color=MUTED,
                family="monospace", va="center")
        y = 33.5
        for k in prod["veiculos"]["por_chave"]:
            c = LEVEL[k["confianca"]]
            ax.add_patch(FancyBboxPatch((x3 + 2, y - 1.6), 7.6, 3.2, boxstyle="round,pad=0,rounding_size=0.8",
                                        fc=c, ec="none"))
            ax.text(x3 + 5.8, y, k["confianca"], fontsize=8, color="white", weight="bold", ha="center", va="center")
            ax.text(x3 + 11, y + 0.9, k["chave"], fontsize=9, color=INK, family="monospace", va="center")
            sample = k["modelos"][0]["modelo"]
            sample = sample if len(sample) <= 26 else sample[:25] + "…"
            ax.text(x3 + 11, y - 2.3, f"{t['models'].format(n=len(k['modelos']))} · {sample}", fontsize=7.8,
                    color=MUTED, va="center")
            y -= 7.6

        tot = stats["veiculo_produto_confianca"]
        share = " · ".join(f"{k} {num(100 * tot[k] / stats['veiculo_produto'], pt, 1)}%" for k in ("alta", "media", "baixa"))
        ax.text(x3 + 2, 9.6, t["all"] + share, fontsize=7.8, color=MUTED)
        ax.text(3, 2.6, t["foot"], fontsize=8.4, color=MUTED)
        ax.text(117, 2.6, "github.com/CaiqueDourado", fontsize=8.4, color=MUTED, ha="right")
        out = ROOT / "docs" / "img" / f"cover{t['suffix']}.png"
        fig.savefig(out, facecolor=BG)
        plt.close(fig)
        print(out)


if __name__ == "__main__":
    main()
