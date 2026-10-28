"""Screenshot-style images of the example records in JSON (docs/img/vehicle-json.png, product-json.png), for the README and Kaggle.

    python scripts/make_json.py --fipe 003367-7 --ano 2012 --out docs/example-vehicle.json
    python scripts/make_json_image.py

Trims docs/example-vehicle.json to the fields worth showing, highlights it and screenshots it with Playwright.
Needs pygments and playwright (with Chromium: python -m playwright install chromium).
"""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

ROOT = Path(__file__).resolve().parents[1]
VERSION = 37057  # the version with equipment, out of the two Mobiauto pages of this code


def trim(rec: dict) -> dict:
    b = rec["marcas"][0]
    m = b["modelos"][0]
    y = m["anos"][0]
    f = next(v for v in y["fichas"] if v["id_versao"] == VERSION)
    p = y["precos"]
    peak = max(p, key=lambda r: r["valor"])
    keep = lambda d, ks: {k: d[k] for k in ks}  # noqa: E731
    return {"marcas": [{**keep(b, ("codigo_marca", "marca", "tipo_veiculo")), "modelos": [{
        **keep(m, ("codigo_modelo", "codigo_fipe", "modelo", "modelo_curto", "fonte")),
        "anos": [{"ano_modelo": y["ano_modelo"], "zero_km": y["zero_km"],
                  "precos": [p[0], peak, *[r for r in p if r["referencia"] == "2023-02"], p[-1]],
                  "fichas": [{**keep(f, ("id_versao", "versao", "preco_mobiauto", "data_coleta")),
                              "motor": keep(f["motor"], ("combustivel", "motorizacao", "potencia_cv", "tracao")),
                              "medidas": f["medidas"],
                              "itens": keep(f["itens"], ("airbag_motorista", "airbag_passageiro", "freios_abs",
                                                         "ar_condicionado", "teto_solar")),
                              "caracteristicas": {k: v for k, v in f["caracteristicas"].items()
                                                  if k in ("Conforto / Ar condicionado", "Dimensões / Comprimento (mm)",
                                                           "Mecânica / Potência (cv)")}}]}],
        "produtos": {**keep(m["produtos"], ("pares", "por_confianca")), "exemplos": m["produtos"]["exemplos"][:2]}}]}]}


def fmt(o, ind: int = 0) -> str:
    """JSON with small flat objects on one line, like a person would write it."""
    sp = "  " * ind
    if isinstance(o, dict):
        flat = json.dumps(o, ensure_ascii=False)
        if all(not isinstance(v, (dict, list)) for v in o.values()) and len(o) <= 4 and len(flat) <= 115:
            return flat
        return "{\n" + ",\n".join(f'{sp}  "{k}": {fmt(v, ind + 1)}' for k, v in o.items()) + f"\n{sp}}}"
    if isinstance(o, list):
        return "[\n" + ",\n".join(f"{sp}  {fmt(v, ind + 1)}" for v in o) + f"\n{sp}]"
    return json.dumps(o, ensure_ascii=False)


CSS = """
body { margin: 0; background: #fdfdfc; font-family: Inter, 'DejaVu Sans', sans-serif; }
.win { margin: 28px; border-radius: 12px; overflow: hidden; display: inline-block;
       box-shadow: 0 10px 30px rgba(17,17,17,.12), 0 0 0 1px #d9dde3; background: #ffffff; }
.bar { height: 38px; background: #f3f4f6; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center;
       padding: 0 14px; gap: 8px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.title { margin-left: 14px; font: 13px 'DejaVu Sans Mono', monospace; color: #555555; }
.code { padding: 16px 26px 20px 0; display: flex; }
.ln { color: #b8bec7; text-align: right; padding: 0 16px 0 18px; user-select: none; }
pre { margin: 0; font: 14px/1.5 'DejaVu Sans Mono', monospace; }
.highlight { background: transparent; }
.highlight .nt { color: #2a78d6; }               /* keys */
.highlight .s2 { color: #b4531f; }               /* strings */
.highlight .mi, .highlight .mf { color: #12895f; } /* numbers */
.highlight .kc { color: #8250df; font-weight: bold; } /* true false null */
.highlight .p { color: #555555; }
"""


def trim_product(rec: dict, per_key: int = 3, keys: int = 4) -> dict:
    v = rec["veiculos"]
    g = {k: rec["grupo"][k] for k in ("group_id", "nome", "nome_longo", "ofertas", "lojas", "group_flag")}
    out = []
    for k in v["por_chave"][:keys]:
        models = [{c: m[c] for c in ("codigo_fipe", "marca", "modelo")} for m in k["modelos"][:per_key]]
        out.append({**{c: k[c] for c in ("chave", "nivel", "confianca", "produtos_da_chave", "modelos_da_chave")},
                    "modelos": models})
    return {"grupo": g, "veiculos": {"pares": v["pares"], "por_confianca": v["por_confianca"], "por_chave": out}}


def render(text: str, title: str, out: Path) -> None:
    json.loads(text)  # still valid JSON
    code = highlight(text, JsonLexer(), HtmlFormatter(nowrap=True))
    lines = "\n".join(str(i) for i in range(1, text.count("\n") + 2))
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="win" id="win"><div class="bar"><span class="dot" style="background:#ff5f57"></span>
<span class="dot" style="background:#febc2e"></span><span class="dot" style="background:#28c840"></span>
<span class="title">{title}</span></div>
<div class="code"><pre class="ln">{lines}</pre><pre class="highlight">{code}</pre></div></div></body></html>"""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=2, viewport={"width": 1100, "height": 800})
        page.set_content(html)
        page.locator("#win").screenshot(path=str(out))
        browser.close()
    print(out)


def main() -> None:
    docs = ROOT / "docs"
    rec = json.loads((docs / "example-vehicle.json").read_text(encoding="utf-8"))
    render(fmt(trim(rec)), "docs/example-vehicle.json · Ford EcoSport Freestyle 1.6 16V Flex 2012 (trimmed)",
           docs / "img" / "vehicle-json.png")
    product = docs / "example-product.json"
    if product.exists():
        rec = json.loads(product.read_text(encoding="utf-8"))
        render(fmt(trim_product(rec)), f"docs/example-product.json · group {rec['grupo']['group_id']} (trimmed)",
               docs / "img" / "product-json.png")


if __name__ == "__main__":
    main()
