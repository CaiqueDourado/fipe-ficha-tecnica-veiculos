# Data quality report

What is reliable, what was fixed, and what is still wrong. Counts are in `stats.json`.

## Know before using

- **`veiculo_produto` is mostly noise.** 93% of its 25.5 million pairs have `confianca = baixa`: the key
  matched 1,000 or more product groups ("PALIO" alone matched 46,722). A first name like "Palio", "Strada"
  or "Kombi" appears in accessories for that car, but also in unrelated products and in other cars' names.
  Use `confianca = 'alta'` (127,322 pairs) for anything shown to people, or treat the table as candidate
  pairs to be checked. It is published, with this warning, because it is what the author's auto parts
  pages ran on, and because filtering it well is an open problem.
- **The zero km year was lost in 2020–2023.** The source writes the zero km price as model year 32000. The
  author's 2022 import replaced 32000 (and empty years) by the model's latest year plus one, then turned
  2025 into 2023. Those rows are published as `zero_km = true` with no model year (42,598 prices), so a
  zero km price is never mistaken for a used one; the two cases (32000 and empty) cannot be told apart.
- **Gap between February 2023 and October 2026.** The months in between were not collected. A model that
  existed only in that gap has no price.
- **The fuel name changed between sources.** In the 2020–2023 dumps FIPE had no "Flex": flex cars are
  "Gasolina". The official FIPE API in October 2026 writes "Flex", "Híbrido" and "Elétrico". In the sample,
  151 of 1,099 code and model year pairs went from "Gasolina" in February 2023 to "Flex" in October 2026.
  To follow one car across both periods, join by `codigo_fipe`, `ano_modelo` and `zero_km`, not by fuel.
  `fichas.combustivel` (Mobiauto) uses its own names ("Etanol / Gasolina", "Flex").
- **Brand names differ by vehicle type.** FIPE writes the same maker differently in each type: "GM -
  Chevrolet" for cars and "CHEVROLET" for trucks, "VW - VolksWagen" and "VOLKSWAGEN". `codigo_marca` is
  different too. Group by name only after normalizing it.
- **A FIPE code is not a version name.** The same code can belong to more than one `codigo_modelo` when FIPE
  renamed the version (353 codes: "Stilo Dualogic" and "Stilo Duologic"). In `fichas`, 5,753 FIPE codes
  are shared by 33,940 versions, because Mobiauto splits versions that FIPE prices together.

## Fixed in this release

| # | Problem in the source | Rows | Fix |
|---|---|---:|---|
| 1 | Same month, code, year and fuel loaded more than once | 1,732 | Last loaded row kept |
| 2 | "Ãlcool", "Ã  disco": UTF-8 read as Latin-1 | fuel of 16,769 prices; 48 values | Fixed |
| 3 | Zero km written as an invented year | 42,598 | `zero_km = true`, no model year |
| 4 | Specification nodes typed "Carro" for every version, motorcycles included | 6,144 | Type and model year from the URL |
| 5 | The same version page collected twice | 72 | Kept once |
| 6 | Mobiauto price shown as zero | 7,523 | Empty |
| 7 | Yes/no items stored as text "Sim"/"Não" | 58 keys | Booleans in `fichas`; text kept in `ficha_caracteristicas` |
| 8 | Section `som` in lower case, title "Audio e Multimídia" | 1 | `Som`, "Áudio e Multimídia" |
| 9 | FIPE code without the hyphen in Mobiauto (`0015059`) | 6 | `001505-9` |

## Known limitations (kept as they are)

- **Specifications are from September 2022**, for the versions on Mobiauto then. Only 4,608 of the 9,629
  FIPE models of that time had a specification page; there are no trucks.
- **Empty specifications.** 383,857 values are empty in the source (14% of the specifications).
- **Measures are text.** Power, torque and 0-100 times carry the fuel, sometimes two values: "122 (Etanol)
  / 115 (Gasolina)". Parse them for your use; the raw text is kept.
- **Values from the page's HTML.** A few values were read with the HTML around them; none were found in the
  release checks, but they can't be ruled out.
- **Ambiguous names in the matching.** About 560 everyday names (Uno, Gol, Polo...) were excluded from the
  first-name match in 2022, which also hides correct pairs for those cars.
- **Prices are FIPE's averages**, not transaction prices; FIPE publishes its own method.

## Sources and terms

FIPE prices are public on the FIPE site. The specifications were collected from Mobiauto's public pages;
the author decided to publish them as a research compilation with the source of every row (`url`). If you
own content in this dataset and want it removed, open an issue: it will be removed in the next version.
