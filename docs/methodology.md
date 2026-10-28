# Methodology

How the three parts of this dataset were collected, what was changed to publish them, and how to rebuild
everything. Counts come from `stats.json`.

![Sources and tables](img/flow.png)

## 1. FIPE prices (tables `marcas`, `modelos`, `precos`)

The FIPE table (Fundação Instituto de Pesquisas Econômicas) is the monthly reference of average used and
new vehicle prices in Brazil, used for insurance, taxes and car sales. Each row is a price for one
**FIPE code** (a version, such as `023067-7`, Nissan Tiida SL 1.8 Flex), one **model year** and one
**fuel**, in one **reference month**. FIPE calls the zero km price "year 32000".

### Three sources, in order

| When | Source | What happened |
|---|---|---|
| 2020–2023 | Monthly dumps of the FIPE table (MySQL files from a data provider), loaded into the author's SQL Server | The 38 months from January 2020 to February 2023 in this dataset. |
| 2026, first try | `g1.globo.com/static/fipe/json/` (the JSON files behind g1's FIPE page) | Three lists (`carro.json`, `moto.json`, `caminhao.json`: brand, model, FIPE code) and one file per code (`carro/023067-7.json`: model year + fuel, price). Dropped: the files stopped around 2022 (no car launched after that, such as BYD Dolphin or VW Tera, and every one of its 6,195 car codes was already in the February 2023 dump), and prices carry no reference month. |
| 2026, second try | BrasilAPI (`brasilapi.com.br/api/fipe`) | Brands and models answered (the model `valor` is FIPE's model code), but prices and the list of reference months returned HTTP 500, "Fonte de dados FIPE temporariamente indisponível", in two rounds on 22/10/2026. |
| October 2026 on | The official FIPE site's JSON API (`veiculos.fipe.org.br/api/veiculos`), the source BrasilAPI itself relays | `scripts/coletor_fipe.py` walks type → brand → model → model year and asks for each price. |

The collector sends one request every 1.5 seconds. When the site answers 429 (Too Many Requests) it
waits what the site asks and slows down by half, up to one request every 8 seconds; after 500 answers
without a 429 it speeds up a little. Every answer is appended to a JSON Lines file as it arrives, with the
request that produced it, so a run can stop and resume. A month is about 55 thousand requests.

Requests and real answers of the three sources: [apis.md](apis.md).

### From the sources to the tables

- `marcas` and `modelos` come from the dump; brands and models that exist only in the API (launched after
  February 2023) are added with `fonte = fipe_api`. `codigo_modelo` is the same number in both.
- `precos` joins the dump and the API. The dump had replaced the zero km year (32000) by the model's
  latest year plus one, and empty years the same way, marking those rows in `_temp_alterado`; then a fixed
  patch turned 2025 into 2023. Those rows are published as `zero_km = true` with no model year. In the API
  rows, year 32000 becomes `zero_km = true`.
- 1,732 dump rows are dropped because they repeat a key (same month, code, year and fuel; 1,661
  keys appear two or more times); the last loaded row is kept. No dump price is zero.
- "Ãlcool", a UTF-8 text read as Latin-1, is fixed to "Álcool".
- The modelo short names (`modelo_curto`, `primeiro_nome`, `primeiro_segundo_nome`, `primeiro_nome_marca`)
  were computed by the author in 2022 to match vehicles with products (section 3): the name up to the
  first number, its first word, its first two words, and brand + first word.

## 2. Vehicle specifications (tables `fichas`, `ficha_caracteristicas`, `ficha_titulos`)

Collected from 6 to 8 September 2022 from the FIPE pages of Mobiauto (`mobiauto.com.br/tabela-fipe`), a
Brazilian car marketplace, starting from 98 car brands and 107 motorcycle brands. The crawler walked the
tree brand → model → year → version and, on each version page, read the price, the FIPE code and the
specifications. Yes/no items are drawn as icons on the page: the crawler decoded the SVG path of each icon
(`M16.672 8.26a1` = Sim, `M16.707 8.707a1` = Não).

| | |
|---|---:|
| versions | 37,794 (31,650 cars, 6,144 motorcycles) |
| specifications | 2,704,962 values; 81 keys per car version, 23 per motorcycle version |
| sections | Mecânica, Dimensões, Segurança, Conforto, Janelas, Bancos, Som, Outros |

Changes for the release:

- Versions are the leaves of the tree (`tipo = Carro` in the source, which is the tree level, not the
  vehicle type: motorcycles were also "Carro"). The vehicle type and the model year come from the URL.
- 72 versions collected twice (same URL) are kept once.
- Empty values stay empty; mojibake ("Ã  disco") is fixed; the section `som` becomes `Som` and its title
  "Audio e Multimídia" gets its accent.
- A price of zero on the page (7,523 versions) becomes empty.
- `fichas` pivots the 81 keys into columns: 58 yes/no items become booleans, 23 measures stay as text
  because many carry the fuel ("122 (Etanol) / 115 (Gasolina)").
- `ficha_titulos` keeps the section titles, the sentence that opens each section's list ("Itens de
  segurança ativa e passiva disponíveis:") and 81 FAQ questions ("Possui Teto solar?"). The author's sites
  used them to write a text and a FAQ for each version (section 4).

## 3. Vehicle × product matches (table `veiculo_produto`)

For the auto parts pages of the author's sites ("Tapete para Gol", "Palheta para Onix"), each FIPE model
was searched by name inside the names of the product groups of the
[e-commerce catalog dataset](https://github.com/CaiqueDourado/catalogo-produtos-ecommerce-brasil):

1. brand + first word (`VW Gol`), with the brand rewritten for GM, VW, Mercedes and Harley-Davidson;
2. first word alone (`Gol`), as a whole word;
3. first two words (`Gol G5`).

Around 560 ambiguous names (Uno, Gol, Polo and other everyday words) were excluded and some redundant
pairs deleted. Even so, a name like "Palio" also matches "Palio Weekend" accessories and the word "palio"
in unrelated products, and the result is **noisy**: 25,456,723 pairs between 8,910 models and 848,018
product groups, and 627 models matched more than 10,000 product groups each.

Nothing was removed from it for the release. Instead every pair carries how many product groups its key
matched (`produtos_da_chave`) and a warning level:

| `confianca` | rule | pairs |
|---|---|---:|
| alta | key matched fewer than 100 product groups | 127,322 |
| media | 100 to 999 | 1,643,114 |
| baixa | 1,000 or more | 23,686,287 |

Every `group_id` exists in the catalog dataset (checked against its `grupos` table).

## 4. Text from the data

In 2022 the author's vehicle sites had one page per FIPE model, "Tudo sobre <marca> <modelo>": a paragraph
about the car, the equipment by section, the specification table, the FIPE price today and month by
month, the IPVA per state and a FAQ, all written from these tables by a C# page generator. `textos/` is
that generator rewritten in Python:

| 2022 page generator | `textos/` |
|---|---|
| Unmapped specification keys reached public pages as `<p>ABC…</p>` (debug text) | Only known fields produce text; empty fields produce nothing |
| Consumption written as `7.5Km/l (Etanol)` | `7,5 km/l com etanol`, numbers in Brazilian format |
| The fuel of each measure lost or repeated | Kept per value: "107 cv com etanol e 101 cv com gasolina"; "Flex" not repeated |
| IPVA with the car rate for motorcycles, and the price of the last version in a loop | `ipva()` takes the rate and the price you pass; no rates are shipped |
| FAQ questions copied from the source ("Possui Teto solar?") | Questions written for the version: "O … tem teto solar?" |
| Item names as stored ("Desemb. traseiro", "Freios abs") | Expanded and cased: "desembaçador traseiro", "freios ABS" |

**Why rules and not a language model.** A page that states a car's power or price has to say exactly what
the data says. A template can't invent an airbag or round a price, and when a field is empty the sentence
is not written. It is also free to run on every version, and the same input always gives the same text.
The cost is variety: every page has the same shape.

`textos/` has no dependencies; `python -m textos <folder> <FIPE code> <year>` prints the whole page of a
version from `sample/` or the Kaggle files. Its tests run in CI with the data checks.

## Rebuilding

```bash
pip install pyodbc pyarrow duckdb pandas
python scripts/exportar_fipe.py --out D:/fipe_raw                       # SQL Server -> Parquet (resumable)
python scripts/coletor_fipe.py --out D:/fipe_raw/api                    # one FIPE month (resumable)
python scripts/perfil_fipe.py --raw D:/fipe_raw --grupos <catalog grupos.parquet>
python scripts/build_veiculos.py --raw D:/fipe_raw --out D:/fipe_out    # Kaggle files, sample, stats.json
python scripts/validate.py --full D:/fipe_out/kaggle
python scripts/make_figures.py --data D:/fipe_out/kaggle
python scripts/docs.py                                                  # data dictionaries, Kaggle metadata
```

`probe_globo_fipe.py` and `probe_brasilapi_fipe.py` are the two probes that led to the official API; they
are kept to show what each source returns.
