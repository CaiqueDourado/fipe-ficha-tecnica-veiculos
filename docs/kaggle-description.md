**Tabela FIPE e ficha técnica de veículos**: preços FIPE de carros, motos e caminhões desde 2020, ficha técnica de 37.794 versões e casamento veículo × produto. **FIPE vehicle prices and specifications (Brazil)**.

![FIPE prices and vehicle specifications](https://raw.githubusercontent.com/CaiqueDourado/fipe-ficha-tecnica-veiculos/main/docs/img/cover.png)

The FIPE table is Brazil's monthly reference of used and new vehicle prices (insurance, taxes, car sales). This dataset has three parts:

- **FIPE prices**: 1.65 million prices per month, FIPE code, model year and fuel, January 2020 to February 2023 (the author's collection for his vehicle sites) plus October 2026 from the official FIPE API.
- **Specifications** of 37,794 car and motorcycle versions (Mobiauto, September 2022): engine, power, consumption, dimensions and 58 yes/no items.
- **Vehicle × product matches**: 25.5 million candidate pairs between FIPE models and the product groups of the [catalog of Brazilian e-commerce products](https://www.kaggle.com/datasets/caiquedourado/catalogo-produtos-ecommerce-brasil), each with a warning level (`confianca`). **Most pairs are wrong**: use `confianca = 'alta'`.

![Used vehicle prices, January 2020 = 100](https://raw.githubusercontent.com/CaiqueDourado/fipe-ficha-tecnica-veiculos/main/docs/img/used-prices.png)

How much of the zero km price a car keeps, by age, in October 2026 (median of 917 cars):

![Share of the zero km price by age](https://raw.githubusercontent.com/CaiqueDourado/fipe-ficha-tecnica-veiculos/main/docs/img/depreciation.png)

## Files

- `marcas.parquet`: FIPE brands and vehicle type.
- `modelos.parquet`: FIPE models (versions), FIPE code, short names used for matching.
- `precos.parquet`: price per reference month, FIPE code, model year and fuel; `zero_km` flags the zero km price.
- `fichas.parquet`: one row per version, 81 specification columns (58 booleans).
- `ficha_caracteristicas.parquet`: the same specifications in long form (section, key, value).
- `ficha_titulos.parquet`: section titles and FAQ questions for writing text from the specifications.
- `veiculo_produto.parquet`: vehicle model × product group, with how many products the key matched and the warning level.

## How it was collected

![Sources and tables](https://raw.githubusercontent.com/CaiqueDourado/fipe-ficha-tecnica-veiculos/main/docs/img/flow.png)

To bring the FIPE series up to date in 2026 the project tried the g1 (Globo) FIPE JSON files (stopped around 2022, no reference month), then BrasilAPI (its price endpoint failing on FIPE's side), and settled on the official FIPE site's JSON API, with a resumable collector that slows down when the site answers HTTP 429. The specifications came from a 2022 crawler that read yes/no items from the SVG path of each icon on the page. Zero km prices are flagged instead of carrying an invented model year; the data quality report lists every fix and every known limit.

## How each vehicle is structured

The tables nest into one tree: brand → model (FIPE code) → model year → monthly prices and specification versions, plus the model's product pairs. `scripts/make_json.py` in the repository writes it from these files. One car, trimmed (the whole record: https://github.com/CaiqueDourado/fipe-ficha-tecnica-veiculos/blob/main/docs/example-vehicle.json):

```json
{"marca": "Ford", "tipo_veiculo": "carro",
 "modelos": [{"codigo_modelo": 6157, "codigo_fipe": "003367-7", "modelo": "EcoSport FREESTYLE 1.6 16V Flex 5p",
   "anos": [{"ano_modelo": 2012, "zero_km": false,
     "precos": [{"referencia": "2020-01", "valor": 33276, "combustivel": "Gasolina", "fonte": "dump"}, …,
                {"referencia": "2026-10", "valor": 41862, "combustivel": "Flex", "fonte": "fipe_api"}],
     "fichas": [{"id_versao": 37057, "versao": "Freestyle 1.6 16V (Flex)",
                 "motor": {"potencia_cv": "115 (Etanol) / 110 (Gasolina)", …},
                 "medidas": {"comprimento_mm": 4239, "porta_malas_l": 296, …},
                 "itens": {"airbag_motorista": true, "freios_abs": true, …},
                 "caracteristicas": {"Conforto / Ar condicionado": "Sim", …}}]}],
   "produtos": {"pares": 15, "por_confianca": {"baixa": 15}, "exemplos": […]}}]}
```

## The FIPE sources, with real answers

g1's static JSON had no reference month and was stale; BrasilAPI answered HTTP 500 for every price; the official FIPE site's API (five POST calls: reference months, brands, models, model years, price) was used. Each request and its real answer: https://github.com/CaiqueDourado/fipe-ficha-tecnica-veiculos/blob/main/docs/apis.md

The repository also has `textos/`, which writes the "about" paragraph, equipment, price history and FAQ of a version from these tables, by rules (the notebook shows it).

Methodology, data quality report, data dictionary (EN and PT), scripts and a sample: **https://github.com/CaiqueDourado/fipe-ficha-tecnica-veiculos**

## Related

- [Catálogo de produtos do e-commerce brasileiro](https://www.kaggle.com/datasets/caiquedourado/catalogo-produtos-ecommerce-brasil) (`group_id` → `grupos.id`)
- [Municípios e estados do Brasil](https://www.kaggle.com/datasets/caiquedourado/municipios-e-estados-do-brasil)
- [DedupKit](https://github.com/CaiqueDourado/DedupKit): matching product names in Portuguese

License: CC BY 4.0 for the compilation and derived columns; prices by FIPE. Version 1.0.0. Author: Caique Dourado.
