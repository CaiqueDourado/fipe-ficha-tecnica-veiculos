# Changelog

Versions follow [Semantic Versioning](https://semver.org/): a new major version renames or removes columns.

## [1.1.0] - 2026-10-28

### Added
- `scripts/make_sqlite.py`: the whole dataset as one SQLite file with indexes (`veiculo_produto` with `alta` and `media` pairs by default); release asset `veiculos.sqlite.gz`.
- Release asset `veiculos.jsonl.gz`: one nested JSON record per model (`scripts/make_json.py`).
- README and Kaggle: the four vehicle sites these tables ran (Tudo Sobre Carros, Tudo para Seus Carros, Tudo Sobre Motos, Tudo Sobre Caminhões), with what each part of the sites became in the dataset.

## [1.0.0] - 2026-10-28

### Added
- FIPE brands, models and prices (January 2020 to February 2023 from the author's database, October 2026 from the official FIPE API), specifications of 37,794 versions (Mobiauto, September 2022) and 25,456,723 vehicle × product matches with a warning level (Parquet on Kaggle; a sample of 300 models in CSV here).
- `textos/`: the author's 2022 page generator rewritten in Python (about paragraph, equipment, FIPE price history, FAQ and JSON-LD), with tests.
- Export, FIPE collector, probes of g1 and BrasilAPI, profile and build scripts; validation of the sample in GitHub Actions.
- Data dictionary (EN, PT), methodology, data quality report, figures, exploratory notebook, Kaggle metadata.

### Changed (relative to the author's database)
- Zero km prices flagged (`zero_km`) instead of an invented model year; repeated prices removed; encoding fixed; vehicle type and model year of the specifications taken from the URL; yes/no items as booleans; Mobiauto prices of zero emptied; FIPE codes without the hyphen restored (6).
