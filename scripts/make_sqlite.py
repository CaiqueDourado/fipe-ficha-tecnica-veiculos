"""The dataset as one SQLite file, for apps and quick SQL: makes, models, prices, specifications and the
vehicle × product pairs you can trust.

    python scripts/make_sqlite.py --data D:\\fipe_out\\kaggle --out D:\\fipe_out\\veiculos.sqlite
    python scripts/make_sqlite.py --data sample --out veiculos_sample.sqlite        # from the CSV sample

By default `veiculo_produto` keeps only the pairs with confianca alta or media (1.8 million of 25.5 million):
the 23.7 million `baixa` pairs would make the file several times larger and are mostly wrong. Use
--confianca alta,media,baixa to keep them all. Needs pandas and pyarrow.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

TABLES = ["marcas", "modelos", "precos", "fichas", "ficha_caracteristicas", "ficha_titulos", "veiculo_produto"]
INDEXES = [
    "CREATE INDEX modelos_marca ON modelos (codigo_marca)",
    "CREATE INDEX modelos_fipe ON modelos (codigo_fipe)",
    "CREATE INDEX precos_modelo ON precos (codigo_modelo, ano_modelo, referencia)",
    "CREATE INDEX precos_fipe ON precos (codigo_fipe, ano_modelo)",
    "CREATE INDEX fichas_fipe ON fichas (codigo_fipe, ano_modelo)",
    "CREATE INDEX caracteristicas_versao ON ficha_caracteristicas (id_versao)",
    "CREATE INDEX vp_modelo ON veiculo_produto (codigo_modelo, confianca)",
    "CREATE INDEX vp_grupo ON veiculo_produto (group_id)",
]


def batches(folder: Path, table: str, size: int = 200_000):
    parquet = folder / f"{table}.parquet"
    if parquet.exists():
        for b in pq.ParquetFile(parquet).iter_batches(batch_size=size):
            yield b.to_pandas()
    elif (folder / f"{table}_sample.csv").exists():
        yield from pd.read_csv(folder / f"{table}_sample.csv", dtype={"codigo_fipe": str}, chunksize=size)
    else:
        raise SystemExit(f"{table}.parquet not found in {folder}: download the Kaggle files there first "
                         "(kaggle datasets download caiquedourado/fipe-ficha-tecnica-veiculos -p <folder> --unzip)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--confianca", default="alta,media", help="veiculo_produto levels to keep")
    a = ap.parse_args()
    keep = set(a.confianca.split(","))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.unlink(missing_ok=True)
    con = sqlite3.connect(a.out)
    con.execute("PRAGMA journal_mode = OFF")
    con.execute("PRAGMA synchronous = OFF")
    for t in TABLES:
        n = 0
        for df in batches(a.data, t):
            if t == "veiculo_produto":
                df = df[df.confianca.isin(keep)]
            for c in df.columns:                       # dates and booleans as SQLite understands them
                if str(df[c].dtype).startswith(("datetime", "date")):
                    df[c] = df[c].astype(str).str[:10]
                elif str(df[c].dtype) in ("bool", "boolean"):
                    df[c] = df[c].astype("Int64")
            df.to_sql(t, con, if_exists="append", index=False)
            n += len(df)
        print(f"{t:<22} {n:>12,}")
    for sql in INDEXES:
        con.execute(sql)
    con.execute("CREATE TABLE sobre (chave TEXT, valor TEXT)")
    con.executemany("INSERT INTO sobre VALUES (?, ?)", [
        ("fonte", "https://github.com/CaiqueDourado/fipe-ficha-tecnica-veiculos"),
        ("licenca", "CC BY 4.0; preços: FIPE"),
        ("veiculo_produto", f"somente confianca em {sorted(keep)}"),
    ])
    con.commit()
    con.execute("VACUUM")
    con.close()
    print(f"{a.out} {a.out.stat().st_size / 1e6:,.0f} MB")


if __name__ == "__main__":
    main()
