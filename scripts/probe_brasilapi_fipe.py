"""Look at BrasilAPI's FIPE endpoints before writing the collector.

    python probe_brasilapi_fipe.py --out D:\\fipe_raw\\_brasilapi_probe

About 20 requests, one every 2 seconds. Saves every answer as it comes and a report of the structure.
Also asks the official FIPE site (veiculos.fipe.org.br), the source BrasilAPI mirrors, for the years and
the FIPE code of one model, because BrasilAPI's model list has the model id but not the FIPE code.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://brasilapi.com.br/api/fipe"


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-fipe-probe/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode()


FIPE = "https://veiculos.fipe.org.br/api/veiculos"


def post(path: str, form: dict):
    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(FIPE + path, data=data, headers={
        "User-Agent": "Mozilla/5.0 portfolio-fipe-probe/0.1", "Referer": "https://veiculos.fipe.org.br/",
        "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode()


def shape(obj) -> str:
    if isinstance(obj, list):
        return f"list with {len(obj)} items; first: {json.dumps(obj[0], ensure_ascii=False)[:300] if obj else '-'}"
    return json.dumps(obj, ensure_ascii=False)[:400]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    report = []

    def call(name: str, path: str):
        status, body = get(BASE + path)
        (a.out / f"{name}.json").write_bytes(body)
        try:
            obj = json.loads(body)
        except ValueError:
            obj = body[:200].decode(errors="replace")
        report.append(f"{status}  {path}\n    {shape(obj)}")
        time.sleep(2)
        return obj if status == 200 else None

    tabelas = call("tabelas", "/tabelas/v1")
    first = last = None
    if isinstance(tabelas, list) and tabelas:
        last, first = tabelas[0], tabelas[-1]
        report.append(f"    {len(tabelas)} reference tables, from {first} to {last}")
    marcas = {}
    for tipo in ("carros", "motos", "caminhoes"):
        marcas[tipo] = call(f"marcas_{tipo}", f"/marcas/v1/{tipo}")
    if isinstance(marcas.get("carros"), list) and marcas["carros"]:
        code = next((m.get("valor") or m.get("codigo") for m in marcas["carros"] if "nissan" in str(m).lower()),
                    None) or marcas["carros"][0].get("valor")
        call("veiculos_carros_marca", f"/veiculos/v1/carros/{code}")
    call("preco_atual_023067-7", "/preco/v1/023067-7")
    if isinstance(tabelas, list) and len(tabelas) > 40:
        old = tabelas[40].get("codigo")
        call(f"preco_tabela_{old}_023067-7", f"/preco/v1/023067-7?tabela_referencia={old}")
    call("preco_atual_840015-6", "/preco/v1/840015-6")
    call("preco_atual_501034-9", "/preco/v1/501034-9")
    call("preco_codigo_invalido", "/preco/v1/000000-0")
    def fipe(name: str, path: str, form: dict):
        status, body = post(path, form)
        (a.out / f"fipe_{name}.json").write_bytes(body)
        try:
            obj = json.loads(body)
        except ValueError:
            obj = body[:200].decode(errors="replace")
        report.append(f"{status}  FIPE {path} {form}\n    {shape(obj)}")
        time.sleep(2)
        return obj if status == 200 else None

    refs = fipe("tabelas", "/ConsultarTabelaDeReferencia", {})
    ref = refs[0]["Codigo"] if isinstance(refs, list) and refs and "Codigo" in refs[0] else None
    if ref:
        base = {"codigoTabelaReferencia": ref, "codigoTipoVeiculo": 1, "codigoMarca": 43, "codigoModelo": 4406}
        anos = fipe("anos_tiida", "/ConsultarAnoModelo", base)
        if isinstance(anos, list) and anos:
            ano, comb = str(anos[0]["Value"]).split("-")
            fipe("valor_tiida", "/ConsultarValorComTodosParametros",
                 {**base, "anoModelo": ano, "codigoTipoCombustivel": comb, "tipoVeiculo": "carro",
                  "tipoConsulta": "tradicional"})
    text = "\n".join(report)
    (a.out / "relatorio.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"\n-> {a.out}  (compacte a pasta e me envie)")


if __name__ == "__main__":
    main()
