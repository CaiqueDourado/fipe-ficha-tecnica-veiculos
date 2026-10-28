"""Figures for README and Kaggle (EN and PT).

    python scripts/make_figures.py                          # from sample/
    python scripts/make_figures.py --data D:\\fipe_out\\kaggle # from the full files (what the README shows)

1. used-vehicle prices month by month, relative to January 2020, for the same FIPE code and model year;
2. how much of the zero km price a car keeps, by age, in the latest month of the series.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "img"
INK, MUTED, LINE, BG = "#111111", "#555555", "#e6e6e6", "#fdfdfc"
SERIES = {"carro": "#2a78d6", "moto": "#eb6834", "caminhao": "#1baf7a"}
for family in ("Inter", "DejaVu Sans"):
    try:
        matplotlib.font_manager.findfont(family, fallback_to_default=False)
        plt.rcParams["font.family"] = family
        break
    except ValueError:
        continue
TEXT = {
    "en": {"suffix": "", "names": {"carro": "Cars", "moto": "Motorcycles", "caminhao": "Trucks"},
           "t1": "Used vehicles got more expensive, not cheaper, from 2020 to 2022",
           "s1": "Median FIPE price of the same code and model year, January 2020 = 100 · {n} price series",
           "t2": "How much of the zero km price a car keeps",
           "s2": "Median FIPE price by age as a share of the same code's zero km price · {ref} · {n} cars",
           "age": "Age (years)", "src": "Source: FIPE table, dataset fipe-ficha-tecnica-veiculos"},
    "pt": {"suffix": ".pt-BR", "names": {"carro": "Carros", "moto": "Motos", "caminhao": "Caminhões"},
           "t1": "Os usados ficaram mais caros, não mais baratos, de 2020 a 2022",
           "s1": "Mediana do preço FIPE do mesmo código e ano-modelo, janeiro de 2020 = 100 · {n} séries de preço",
           "t2": "Quanto do preço de zero km um carro mantém",
           "s2": "Mediana do preço FIPE por idade como fração do zero km do mesmo código · {ref} · {n} carros",
           "age": "Idade (anos)", "src": "Fonte: tabela FIPE, base fipe-ficha-tecnica-veiculos"},
}


def load(data: Path | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    if data:
        p, m = pd.read_parquet(data / "precos.parquet"), pd.read_parquet(data / "modelos.parquet")
    else:
        p = pd.read_csv(ROOT / "sample" / "precos_sample.csv", dtype={"codigo_fipe": str})
        m = pd.read_csv(ROOT / "sample" / "modelos_sample.csv", dtype={"codigo_fipe": str})
    p["referencia"] = pd.to_datetime(p.referencia)
    p["zero_km"] = p.zero_km.astype(str).str.lower() == "true"
    return p.merge(m[["codigo_modelo", "tipo_veiculo"]], on="codigo_modelo"), m


def index_by_month(p: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    d = p[(p.fonte == "dump") & ~p.zero_km].copy()
    d["k"] = d.codigo_fipe + "/" + d.ano_modelo.astype("Int64").astype(str) + "/" + d.combustivel
    base = d[d.referencia == d.referencia.min()].drop_duplicates("k").set_index("k").valor
    d = d[d.k.isin(base.index)]
    d["idx"] = 100 * d.valor / d.k.map(base)
    return d.groupby(["tipo_veiculo", "referencia"]).idx.median().unstack(0), d.k.nunique()


def depreciation(p: pd.DataFrame):
    last = p[p.tipo_veiculo == "carro"]
    ref = last.referencia.max()
    last = last[last.referencia == ref]
    zk = last[last.zero_km].drop_duplicates("codigo_fipe").set_index("codigo_fipe").valor
    u = last[~last.zero_km & last.codigo_fipe.isin(zk.index)].copy()
    u["age"] = ref.year - u.ano_modelo
    u["share"] = 100 * u.valor / u.codigo_fipe.map(zk)
    u = u[u.age.between(0, 15)]
    return u.groupby("age").share.median(), ref, u.codigo_fipe.nunique()


def frame(fig, t: str, s: str, src: str) -> None:
    fig.patch.set_facecolor(BG)
    fig.text(0.02, 0.93, t, fontsize=15, weight="bold", color=INK)
    fig.text(0.02, 0.87, s, fontsize=10, color=MUTED)
    fig.text(0.02, 0.025, src, fontsize=8, color=MUTED)


def style(ax) -> None:
    ax.set_facecolor(BG)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(axis="y", color=LINE, linewidth=0.8)
    ax.set_axisbelow(True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    p, _ = load(a.data)
    idx, n_series = index_by_month(p)
    dep, ref, n_cars = depreciation(p)
    figures = {"n_series": int(n_series), "index_last": {k: round(float(v), 1) for k, v in idx.iloc[-1].items()},
               "index_peak": {k: round(float(v), 1) for k, v in idx.max().items()},
               "depreciation": {int(k): round(float(v), 1) for k, v in dep.items()}, "ref": str(ref.date())}
    for lang, t in TEXT.items():
        fmt = (lambda n: f"{n:,}".replace(",", ".")) if lang == "pt" else (lambda n: f"{n:,}")
        fig, ax = plt.subplots(figsize=(10, 4.8), dpi=110)
        fig.subplots_adjust(left=0.07, right=0.86, top=0.8, bottom=0.12)
        frame(fig, t["t1"], t["s1"].format(n=fmt(int(n_series))), t["src"])
        style(ax)
        ends = []
        for tipo in ("carro", "moto", "caminhao"):
            if tipo in idx:
                s = idx[tipo].dropna()
                ax.plot(s.index, s.values, color=SERIES[tipo], linewidth=2, label=t["names"][tipo])
                ends.append([s.iloc[-1], s.iloc[-1], tipo, s.index[-1]])
        ends.sort()
        gap = (idx.max().max() - idx.min().min()) * 0.06
        for i in range(1, len(ends)):  # keep the end labels apart
            ends[i][1] = max(ends[i][1], ends[i - 1][1] + gap)
        for value, y, tipo, x in ends:
            ax.annotate(f"{t['names'][tipo]} {value:.0f}", (x, value), xytext=(x, y), textcoords="data",
                        va="center", fontsize=9, color=INK, annotation_clip=False,
                        xycoords="data").set_x(x)
            ax.texts[-1].set_position((x + pd.Timedelta(days=12), y))
        ax.axhline(100, color=MUTED, linewidth=0.8, linestyle=(0, (2, 2)))
        ax.legend(frameon=False, fontsize=9, loc="upper left", labelcolor=INK)
        ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=(1, 7)))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m'))
        fig.savefig(OUT / f"used-prices{t['suffix']}.png", facecolor=BG)
        plt.close(fig)

        if n_cars < 20:
            print(f"depreciation: only {n_cars} cars with a zero km price; run with --data on the full files")
            continue
        fig, ax = plt.subplots(figsize=(10, 4.6), dpi=110)
        fig.subplots_adjust(left=0.07, right=0.97, top=0.8, bottom=0.14)
        months = {"en": ref.strftime("%B %Y"), "pt": f"{ref.month:02d}/{ref.year}"}
        frame(fig, t["t2"], t["s2"].format(ref=months[lang], n=fmt(int(n_cars))), t["src"])
        style(ax)
        ax.bar(dep.index, dep.values, color=SERIES["carro"], width=0.7)
        for x, y in dep.items():
            if x in (0, 1, 3, 5, 10, 15):
                ax.annotate(f"{y:.0f}%", (x, y), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=9, color=INK)
        ax.set_xlabel(t["age"], color=MUTED, fontsize=9)
        ax.set_xticks(range(0, 16))
        ax.set_ylim(0, 110)
        fig.savefig(OUT / f"depreciation{t['suffix']}.png", facecolor=BG)
        plt.close(fig)
    (ROOT / "docs" / "figures.json").write_text(json.dumps(figures, indent=1), encoding="utf-8")
    print(json.dumps(figures, indent=1))


if __name__ == "__main__":
    main()
