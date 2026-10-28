"""Checks on the sample (and, with --full, on the Kaggle Parquet files). Exits with 1 on any failure.

    python scripts/validate.py                       # sample/ (what CI runs)
    python scripts/validate.py --full D:\\fipe_out\\kaggle
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FAIL: list[str] = []


def check(ok: bool, message: str) -> None:
    print(("ok    " if ok else "FAIL  ") + message)
    if not ok:
        FAIL.append(message)


def load(folder: Path, full: bool) -> dict[str, pd.DataFrame]:
    tables = [t["name"] for t in json.loads((ROOT / "schema" / "dataset.json").read_text(encoding="utf-8"))["tables"]]
    if full:
        return {t: pd.read_parquet(folder / f"{t}.parquet") for t in tables}
    return {t: pd.read_csv(folder / f"{t}_sample.csv", dtype={"codigo_fipe": str}) for t in tables}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", type=Path)
    a = ap.parse_args()
    d = load(a.full or ROOT / "sample", bool(a.full))
    cols = json.loads((ROOT / "schema" / "columns.json").read_text(encoding="utf-8"))
    for t, df in d.items():
        check(list(df.columns) == [c["name"] for c in cols if c["table"] == t], f"{t}: columns match schema/columns.json")
    m, mo, p, f, fc, ft, vp = (d[k] for k in ("marcas", "modelos", "precos", "fichas", "ficha_caracteristicas",
                                               "ficha_titulos", "veiculo_produto"))
    check(m.codigo_marca.is_unique, "marcas: codigo_marca unique")
    check(set(m.tipo_veiculo) <= {"carro", "moto", "caminhao"}, "marcas: tipo_veiculo in carro/moto/caminhao")
    check(mo.codigo_modelo.is_unique, "modelos: codigo_modelo unique")
    check(mo.codigo_marca.isin(m.codigo_marca).all(), "modelos: every brand exists in marcas")
    fipe = r"^\d{6}-\d$"
    check(mo.codigo_fipe.dropna().str.match(fipe).all(), "modelos: codigo_fipe looks like 000000-0")
    check(p.codigo_modelo.isin(mo.codigo_modelo).all(), "precos: every model exists in modelos")
    key = ["referencia", "codigo_fipe", "ano_modelo", "zero_km", "combustivel", "codigo_modelo"]
    check(not p.duplicated(key).any(), "precos: one price per month, code, model, year and fuel")
    check((p.valor > 0).all(), "precos: valor > 0")
    zk = p.zero_km.astype(str).str.lower() == "true"
    check(p.loc[zk, "ano_modelo"].isna().all() and p.loc[~zk, "ano_modelo"].notna().all(),
          "precos: ano_modelo empty exactly for zero km")
    check(p.ano_modelo.dropna().between(1950, 2030).all(), "precos: model years between 1950 and 2030")
    check(pd.to_datetime(p.referencia).dt.day.eq(1).all(), "precos: referencia is the first day of a month")
    check(set(p.fonte) <= {"dump", "fipe_api"}, "precos: fonte is dump or fipe_api")
    check(not p.combustivel.str.contains("Ã", na=False).any(), "precos: no mojibake in combustivel")
    check(f.id_versao.is_unique, "fichas: id_versao unique")
    check(f.url.is_unique, "fichas: url unique")
    check(set(f.tipo_veiculo) <= {"carro", "moto"}, "fichas: tipo_veiculo carro or moto")
    check((f.preco_mobiauto.dropna() > 0).all(), "fichas: preco_mobiauto empty or > 0")
    check(f.codigo_fipe.dropna().str.match(fipe).all(), "fichas: codigo_fipe looks like 000000-0")
    booleans = [c["name"] for c in cols if c["table"] == "fichas" and c["type"] == "boolean"]
    check(len(booleans) == 58, f"fichas: 58 yes/no columns ({len(booleans)})")
    values = {str(v) for v in pd.unique(f[booleans].values.ravel()) if not pd.isna(v)}
    check(values <= {"True", "False"}, "fichas: yes/no columns only hold true/false/empty")
    check(fc.id_versao.isin(f.id_versao).all(), "ficha_caracteristicas: every version exists in fichas")
    check(not fc.duplicated(["id_versao", "secao", "chave"]).any(), "ficha_caracteristicas: one value per key")
    check(not fc.valor.str.contains("Ã", na=False).any(), "ficha_caracteristicas: no mojibake")
    check(set(ft.tipo) == {"secao", "faq"}, "ficha_titulos: secao and faq rows")
    expected = pd.cut(vp.produtos_da_chave, [0, 99, 999, float("inf")], labels=["alta", "media", "baixa"]).astype(str)
    check((expected == vp.confianca).all(), "veiculo_produto: confianca follows produtos_da_chave")
    check(vp.codigo_modelo.isin(mo.codigo_modelo).all(), "veiculo_produto: every model exists in modelos")
    if FAIL:
        sys.exit(f"{len(FAIL)} check(s) failed")
    print("all checks passed")


if __name__ == "__main__":
    main()
