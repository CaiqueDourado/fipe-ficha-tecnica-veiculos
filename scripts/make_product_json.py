"""The vehicle × product matches seen from the product side: one product group of the e-commerce catalog and the
FIPE vehicles matched to it, grouped by the key that matched.

    # 1. product groups with trustworthy matches, to choose one (also writes docs/produtos_candidatos.json)
    python scripts/make_product_json.py --data D:\\fipe_out\\kaggle --catalog D:\\catalogo --list
    # 2. one group as JSON
    python scripts/make_product_json.py --data D:\\fipe_out\\kaggle --catalog D:\\catalogo --group 12711411

--data has this dataset's Parquet files (veiculo_produto, modelos, marcas); --catalog has grupos.parquet from
https://www.kaggle.com/datasets/caiquedourado/catalogo-produtos-ecommerce-brasil. Needs duckdb.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
LEVELS = "CASE confianca WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--group", type=int)
    ap.add_argument("--list", action="store_true", help="print candidate groups and stop")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "example-product.json")
    a = ap.parse_args()

    con = duckdb.connect()
    con.execute(f"CREATE VIEW vp AS SELECT * FROM read_parquet('{(a.data / 'veiculo_produto.parquet').as_posix()}')")
    con.execute(f"CREATE VIEW modelos AS SELECT * FROM read_parquet('{(a.data / 'modelos.parquet').as_posix()}')")
    con.execute(f"CREATE VIEW marcas AS SELECT * FROM read_parquet('{(a.data / 'marcas.parquet').as_posix()}')")
    con.execute(f"CREATE VIEW grupos AS SELECT * FROM read_parquet('{(a.catalog / 'grupos.parquet').as_posix()}')")

    if a.list:
        cand = con.execute("""
            SELECT g.id group_id, g.short_name, g.offers, g.stores,
                   count(*) FILTER (WHERE vp.confianca = 'alta') alta,
                   count(*) FILTER (WHERE vp.confianca = 'media') media,
                   count(*) FILTER (WHERE vp.confianca = 'baixa') baixa
            FROM vp JOIN grupos g ON g.id = vp.group_id
            WHERE g.group_flag = 'ok'
            GROUP BY ALL HAVING alta >= 2 AND alta + media + baixa <= 40
            ORDER BY g.offers DESC LIMIT 40""").df()
        print(cand.to_string(index=False, max_colwidth=70))
        out = a.out.with_name("produtos_candidatos.json")
        out.write_text(json.dumps([record(con, int(i)) for i in cand.group_id], ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
        print(f"{len(cand)} candidates -> {out}")
        return

    rec = record(con, a.group)
    a.out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{rec['veiculos']['pares']} pairs, {len(rec['veiculos']['por_chave'])} keys -> {a.out}")


def record(con, group: int) -> dict:
    g = con.execute("SELECT id, short_name, long_name, offers, stores, brands, group_flag FROM grupos WHERE id = ?",
                    [group]).fetchone()
    if not g:
        raise SystemExit(f"group {group} not in grupos.parquet")
    rows = con.execute(f"""
        SELECT vp.chave, vp.nivel, vp.confianca, vp.produtos_da_chave, vp.modelos_da_chave,
               m.codigo_modelo, m.codigo_fipe, b.marca, m.modelo, m.tipo_veiculo
        FROM vp JOIN modelos m USING (codigo_modelo) JOIN marcas b USING (codigo_marca)
        WHERE vp.group_id = ?
        ORDER BY {LEVELS}, vp.produtos_da_chave, vp.chave, m.modelo""", [group]).fetchall()

    keys: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for chave, nivel, conf, n_prod, n_mod, cod, fipe, marca, modelo, tipo in rows:
        counts[conf] = counts.get(conf, 0) + 1
        k = keys.setdefault(chave, {"chave": chave, "nivel": nivel, "confianca": conf,
                                    "produtos_da_chave": n_prod, "modelos_da_chave": n_mod, "modelos": []})
        k["modelos"].append({"codigo_modelo": cod, "codigo_fipe": fipe, "marca": marca, "modelo": modelo,
                             "tipo_veiculo": tipo})
    return {"grupo": {"group_id": g[0], "nome": g[1], "nome_longo": g[2], "ofertas": g[3], "lojas": g[4],
                     "marcas": g[5], "group_flag": g[6]},
            "veiculos": {"pares": len(rows), "por_confianca": counts, "por_chave": list(keys.values())}}


if __name__ == "__main__":
    main()
