"""The text of one version of the dataset: about, equipment, FIPE price, FAQ.

    python -m textos <folder with the dataset> 003268-9 2012

The folder can be the dataset's sample/ (CSV) or the Kaggle download (Parquet). Needs pandas.
"""

import sys
from pathlib import Path

import pandas as pd

from . import Vehicle, by_model_year, faq_page, history


def load(folder: Path, name: str) -> pd.DataFrame:
    parquet = folder / f"{name}.parquet"
    if parquet.exists():
        return pd.read_parquet(parquet)
    return pd.read_csv(folder / f"{name}_sample.csv", dtype={"codigo_fipe": str})


def main() -> None:
    folder, code, year = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    fichas, precos = load(folder, "fichas"), load(folder, "precos")
    precos["zero_km"] = precos.zero_km.astype(str).str.lower() == "true"
    versions = fichas[(fichas.codigo_fipe == code) & (fichas.ano_modelo == year)]
    if versions.empty:
        sys.exit("no specification for this FIPE code and year")
    v = Vehicle(versions.iloc[0].to_dict())
    print(f"# {v.title}\n\n{v.about()}\n")
    for title, text in v.equipment().items():
        print(f"## {title}\n\n{text}\n")
    serie = precos[(precos.codigo_fipe == code) & (precos.ano_modelo == year)]
    print("## Preço\n\n" + history(zip(serie.referencia, serie.valor), v.title))
    last = precos[(precos.codigo_fipe == code) & (precos.referencia == precos.referencia.max())]
    print(by_model_year(zip(last.ano_modelo.where(~last.zero_km, None), last.valor), v.title.rsplit(" ", 1)[0],
                        last.referencia.max()) + "\n")
    print('<script type="application/ld+json">\n' + faq_page(v.faq(include_no=False), indent=1) + "\n</script>")


if __name__ == "__main__":
    main()
