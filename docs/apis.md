# The FIPE sources, with real answers

To bring the FIPE series to 2026 the project asked three public sources, in this order. Every answer below
was saved by the scripts on 22/10/2026 and is shown as it came, cut where marked with `…`. The scripts:
[`probe_globo_fipe.py`](../scripts/probe_globo_fipe.py), [`probe_brasilapi_fipe.py`](../scripts/probe_brasilapi_fipe.py)
and [`coletor_fipe.py`](../scripts/coletor_fipe.py).

| Source | Lists | Prices | Reference month | Used |
|---|---|---|---|---|
| g1 (Globo) static JSON | yes | yes | no, and stale | no |
| BrasilAPI | yes | HTTP 500 | HTTP 500 | no |
| Official FIPE site | yes | yes | yes | **yes** |

## 1. g1: the JSON files behind g1's FIPE page

Plain GET, no key. One list per vehicle type (`carro`, `moto`, `caminhao`; the plural names give 404) and
one file per FIPE code.

```text
GET https://g1.globo.com/static/fipe/json/carro.json          200, 565,332 bytes, 6,195 items
```
```json
[{"modelo": "Integra GS 1.8", "marca": "Acura", "cod_fipe": "038003-2"},
 {"modelo": "Legend 3.2/3.5", "marca": "Acura", "cod_fipe": "038002-4"}, …]
```
```text
GET https://g1.globo.com/static/fipe/json/carro/023067-7.json  200, 270 bytes
```
```json
[{"tipo": "2008 gasolina", "valor": "21165"}, {"tipo": "2009 gasolina", "valor": "22429"},
 {"tipo": "2010 gasolina", "valor": "23162"}, {"tipo": "2011 gasolina", "valor": "25108"},
 {"tipo": "2012 gasolina", "valor": "26317"}, {"tipo": "2013 gasolina", "valor": "29732"}]
```

Why it was dropped:

- **No reference month.** A price says "2013 gasolina", not which FIPE table it came from.
- **Stale.** The same Nissan Tiida 2013 (`023067-7`) is R$ 29,732 here and R$ 39,647 in the official
  October 2026 table below. No car launched after 2022 is in the list, and all of its 6,195 car codes were
  already in the February 2023 dump.
- Model year and fuel come in one string (`"Zero km gasolina"` for zero km), and prices are strings.

## 2. BrasilAPI

Plain GET, no key. Brands and models answered; everything with a price or a reference month answered
HTTP 500, in two rounds on 22/10/2026.

```text
GET https://brasilapi.com.br/api/fipe/marcas/v1/carros         200, 108 brands
```
```json
[{"nome": "Acura", "valor": "1"}, {"nome": "Agrale", "valor": "2"}, {"nome": "Alfa Romeo", "valor": "3"}, …]
```
```text
GET https://brasilapi.com.br/api/fipe/veiculos/v1/carros/43    200, 200 models of brand 43 (Nissan)
```
```json
[{"modelo": "350Z 3.5 V6 280cv/ 312cv 2p", "valor": "1781"},
 {"modelo": "ALTIMA SL 2.5 16V 4p Aut.", "valor": "6644"}, …]
```

`valor` is FIPE's own brand or model code, not a price, and the model list has no FIPE code.

```text
GET https://brasilapi.com.br/api/fipe/preco/v1/023067-7        500
GET https://brasilapi.com.br/api/fipe/tabelas/v1               500
```
```json
{"message": "Fonte de dados FIPE temporariamente indisponível. Tente novamente mais tarde.",
 "type": "internal", "name": "InternalError"}
```

Even an invalid code (`000000-0`) got the same 500: the failure was in BrasilAPI's call to FIPE, not in
the request.

## 3. The official FIPE site (used)

The JSON API behind [veiculos.fipe.org.br](https://veiculos.fipe.org.br/), the source BrasilAPI relays.
Every call is a POST with a form body (`application/x-www-form-urlencoded`) to
`https://veiculos.fipe.org.br/api/veiculos/<method>`. Five calls lead to a price. Vehicle types: 1 car,
2 motorcycle, 3 truck.

**1. Reference months.** `ConsultarTabelaDeReferencia`, empty form. 310 months; 338 is October 2026.

```json
[{"Codigo": 338, "Mes": "outubro/2026 "}, {"Codigo": 337, "Mes": "setembro/2026 "}, …]
```

**2. Brands of a type.** `ConsultarMarcas`

```text
codigoTabelaReferencia=338&codigoTipoVeiculo=1
```
```json
[{"Label": "Acura", "Value": "1"}, {"Label": "Agrale", "Value": "2"}, …, {"Label": "BYD", "Value": "238"}, …]
```

**3. Models of a brand.** `ConsultarModelos` (it also returns every model year of the brand)

```text
codigoTabelaReferencia=338&codigoTipoVeiculo=1&codigoMarca=1
```
```json
{"Modelos": [{"Label": "Integra GS 1.8", "Value": 1}, {"Label": "Legend 3.2/3.5", "Value": 2},
             {"Label": "NSX 3.0", "Value": 3}],
 "Anos": [{"Label": "1998 Gasolina", "Value": "1998-1"}, …, {"Label": "1991 Gasolina", "Value": "1991-1"}]}
```

**4. Model years of a model.** `ConsultarAnoModelo`. `Value` is year and fuel code joined by a hyphen.

```text
codigoTabelaReferencia=338&codigoTipoVeiculo=1&codigoMarca=1&codigoModelo=1
```
```json
[{"Label": "1992 Gasolina", "Value": "1992-1"}, {"Label": "1991 Gasolina", "Value": "1991-1"}]
```

**5. Price.** `ConsultarValorComTodosParametros`. The EcoSport of the README, model 6157:

```text
codigoTabelaReferencia=338&codigoTipoVeiculo=1&codigoMarca=22&codigoModelo=6157
&anoModelo=2017&codigoTipoCombustivel=5&tipoVeiculo=carro&tipoConsulta=tradicional
```
```json
{"Valor": "R$ 57.839,00", "Marca": "Ford", "Modelo": "EcoSport FREESTYLE 1.6 16V Flex 5p",
 "AnoModelo": 2017, "Combustivel": "Flex", "CodigoFipe": "003367-7",
 "MesReferencia": "outubro de 2026 ", "Autenticacao": "06g5g3xd4n3k", "TipoVeiculo": 1,
 "SiglaCombustivel": "F", "DataConsulta": "quinta-feira, 22 de outubro de 2026 13:47"}
```

What the build does with it:

- `Valor` "R$ 57.839,00" becomes 57839.0; `MesReferencia` "outubro de 2026 " becomes `2026-10-01`
  (note the trailing space, in `Mes` too).
- `codigoModelo` (6157) is the same number as `codigo_modelo` in the 2020–2023 dumps, so the series joins.
- `Combustivel` says "Flex" here; the dumps said "Gasolina" for the same code
  ([data quality](data-quality.md)).
- Zero km comes as model year 32000.

The collector saves each answer with the request that produced it, one JSON line per call, so a run can
stop and resume:

```json
{"chave": "1/22/6157/2017-5",
 "pedido": {"codigoTabelaReferencia": 338, "codigoTipoVeiculo": 1, "codigoMarca": "22", "codigoModelo": 6157,
            "anoModelo": "2017", "codigoTipoCombustivel": "5", "tipoVeiculo": "carro", "tipoConsulta": "tradicional"},
 "resposta": {"Valor": "R$ 57.839,00", "CodigoFipe": "003367-7", "MesReferencia": "outubro de 2026 ", …}}
```

It sends one request every 1.5 s and slows down by itself when the site answers HTTP 429. A month is about
55 thousand requests. The site's terms ask for no abuse; keep the pace if you run it.
