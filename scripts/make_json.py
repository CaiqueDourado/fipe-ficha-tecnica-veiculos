"""The dataset as nested JSON: brand > model (FIPE code) > model year > prices and specifications.

    python scripts/make_json.py                                         # sample/ -> sample/veiculos_sample.json
    python scripts/make_json.py --fipe 003367-7 --ano 2012 --out docs/example-vehicle.json
    python scripts/make_json.py --data D:\\fipe_out\\kaggle --out D:\\fipe_out\\veiculos.jsonl   # full: one model per line

--data is the sample/ folder (CSV) or the Kaggle download (Parquet). An output ending in .jsonl gets one model
per line, with its brand, which is the practical shape for the full dataset. Needs duckdb.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
TABLES = ["marcas", "modelos", "precos", "fichas", "ficha_caracteristicas", "veiculo_produto"]
ID = ["id_versao", "tipo_veiculo", "marca", "modelo", "ano_modelo", "ano_url", "versao", "codigo_fipe",
      "preco_mobiauto", "data_coleta", "url"]
ENGINE = ["combustivel", "motorizacao", "potencia_cv", "torque_kgf_m", "cambio", "tracao", "direcao",
          "velocidade_maxima_km_h", "tempo_0_100_s", "consumo_cidade_km_l", "consumo_estrada_km_l",
          "freios_dianteiros", "freios_traseiros", "suspensao_dianteira", "suspensao_traseira"]
SIZE = ["comprimento_mm", "largura_mm", "altura_mm", "entre_eixos_mm", "peso_kg", "porta_malas_l", "tanque_l",
        "ocupantes"]
EXAMPLES = 5  # product pairs listed per model, best warning level first


def source(folder: Path, name: str) -> str:
    parquet = folder / f"{name}.parquet"
    if parquet.exists():
        return f"read_parquet('{parquet.as_posix()}')"
    types = ", types={'codigo_fipe': 'VARCHAR'}" if name in ("modelos", "precos", "fichas") else ""
    return f"read_csv_auto('{(folder / f'{name}_sample.csv').as_posix()}'{types})"


def clean(value):
    if value is None or value == "":
        return None
    if isinstance(value, float):
        if value != value:
            return None
        return int(value) if value.is_integer() else value
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    return value


def rows(con, sql: str) -> list[dict]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [{c: clean(v) for c, v in zip(cols, r)} for r in cur.fetchall()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=ROOT / "sample")
    ap.add_argument("--out", type=Path, default=ROOT / "sample" / "veiculos_sample.json")
    ap.add_argument("--fipe", help="only this FIPE code")
    ap.add_argument("--ano", type=int, help="only this model year (with --fipe)")
    a = ap.parse_args()

    con = duckdb.connect()
    for t in TABLES:
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM {source(a.data, t)}")
    where_fipe = f"WHERE codigo_fipe = '{a.fipe}'" if a.fipe else ""
    where_year = f" AND (ano_modelo = {a.ano} OR ano_modelo IS NULL)" if a.ano and a.fipe else ""

    models = rows(con, f"SELECT * FROM modelos {where_fipe} ORDER BY codigo_marca, modelo, codigo_modelo")
    keep = {m["codigo_modelo"] for m in models}
    brands = {b["codigo_marca"]: b for b in rows(con, "SELECT * FROM marcas")}

    prices = defaultdict(list)
    for p in rows(con, f"""SELECT codigo_modelo, ano_modelo, zero_km, strftime(referencia, '%Y-%m') referencia,
                                   valor, combustivel, fonte
                            FROM precos {where_fipe}{where_year} ORDER BY referencia"""):
        if p["codigo_modelo"] in keep:
            prices[(p.pop("codigo_modelo"), p.pop("ano_modelo"), p.pop("zero_km"))].append(p)

    specs_long = defaultdict(dict)
    fipe_versions = f"WHERE id_versao IN (SELECT id_versao FROM fichas {where_fipe}{where_year})" if a.fipe else ""
    for r in rows(con, f"SELECT id_versao, secao, chave, valor FROM ficha_caracteristicas {fipe_versions} ORDER BY 1, 2, 3"):
        specs_long[r["id_versao"]][f"{r['secao']} / {r['chave']}"] = r["valor"]
    specs = defaultdict(list)
    for f in rows(con, f"SELECT * FROM fichas {where_fipe}{where_year} ORDER BY id_versao"):
        items = {k: v for k, v in f.items() if k not in ID + ENGINE + SIZE}
        specs[(f["codigo_fipe"], f["ano_modelo"])].append({
            **{k: f[k] for k in ("id_versao", "versao", "preco_mobiauto", "data_coleta", "url")},
            "motor": {k: f[k] for k in ENGINE},
            "medidas": {k: f[k] for k in SIZE},
            "itens": items,
            "caracteristicas": specs_long.get(f["id_versao"], {}),
        })

    model_list = ", ".join(str(k) for k in keep) or "NULL"
    products = defaultdict(lambda: {"pares": 0, "por_confianca": {}, "exemplos": []})
    for r in rows(con, f"""SELECT codigo_modelo, confianca, count(*) n FROM veiculo_produto
                            WHERE codigo_modelo IN ({model_list}) GROUP BY 1, 2"""):
        products[r["codigo_modelo"]]["pares"] += r["n"]
        products[r["codigo_modelo"]]["por_confianca"][r["confianca"]] = r["n"]
    for r in rows(con, f"""SELECT codigo_modelo, group_id, chave, confianca, produtos_da_chave FROM (
                              SELECT *, row_number() OVER (PARTITION BY codigo_modelo ORDER BY
                                     CASE confianca WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END,
                                     produtos_da_chave, group_id) rn
                              FROM veiculo_produto WHERE codigo_modelo IN ({model_list})) WHERE rn <= {EXAMPLES}
                            ORDER BY codigo_modelo, rn"""):
        products[r.pop("codigo_modelo")]["exemplos"].append(r)

    def model_node(m: dict) -> dict:
        years = sorted({(y, z) for (c, y, z) in prices if c == m["codigo_modelo"]},
                       key=lambda t: (t[1], t[0] or 0))
        return {
            **{k: m[k] for k in ("codigo_modelo", "codigo_fipe", "modelo", "modelo_curto", "slug", "fonte")},
            "anos": [{"ano_modelo": y, "zero_km": z,
                      "precos": prices[(m["codigo_modelo"], y, z)],
                      "fichas": [] if z else specs.get((m["codigo_fipe"], y), [])} for y, z in years],
            "produtos": products.get(m["codigo_modelo"], {"pares": 0, "por_confianca": {}, "exemplos": []}),
        }

    def brand_head(code: int) -> dict:
        b = brands[code]
        return {"codigo_marca": code, "marca": b["marca"], "tipo_veiculo": b["tipo_veiculo"]}

    a.out.parent.mkdir(parents=True, exist_ok=True)
    if a.out.suffix == ".jsonl":
        with open(a.out, "w", encoding="utf-8") as fh:
            for m in models:
                fh.write(json.dumps({**brand_head(m["codigo_marca"]), "modelo": model_node(m)}, ensure_ascii=False) + "\n")
    else:
        tree: dict[int, dict] = {}
        for m in models:
            tree.setdefault(m["codigo_marca"], {**brand_head(m["codigo_marca"]), "modelos": []})["modelos"].append(model_node(m))
        out = {"fonte": "https://github.com/CaiqueDourado/fipe-ficha-tecnica-veiculos", "marcas": list(tree.values())}
        a.out.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(models)} models -> {a.out}")


if __name__ == "__main__":
    main()
