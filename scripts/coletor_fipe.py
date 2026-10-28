"""Collect one month of the FIPE table (cars, motorcycles, trucks) from the official site's JSON API.

    python coletor_fipe.py --out D:\\fipe_raw\\api --limit 20      # quick test: 20 prices
    python coletor_fipe.py --out D:\\fipe_raw\\api                 # latest month, resumable
    python coletor_fipe.py --out D:\\fipe_raw\\api --referencia 300 # an older month (codes: tabelas.json)

Source: veiculos.fipe.org.br/api/veiculos, the API behind the FIPE price page and the source BrasilAPI
mirrors (BrasilAPI's price endpoint returned "Fonte de dados FIPE temporariamente indisponível" on
22/10/2026, while its brand and model lists worked). The site's terms ask for no abuse, so the default
is one request every 1.5 s, slowing down by itself when the site answers 429; a month is about
55 thousand requests (one to two days) and every answer is
appended to disk at once, so the run can stop and resume at any time.

Output, per reference month: <out>/<codigo>/marcas.jsonl, modelos.jsonl, anos.jsonl, precos.jsonl
(one JSON per line, as the API returned it, plus the request that produced it).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://veiculos.fipe.org.br/api/veiculos"
TIPOS = {1: "carro", 2: "moto", 3: "caminhao"}
HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio dataset; one request per second)",
           "Referer": "https://veiculos.fipe.org.br/", "Content-Type": "application/x-www-form-urlencoded"}


class Api:
    """POST with a polite pace. A 429 (Too Many Requests) is the site asking to slow down: the pause between
    requests grows by half (up to --max-delay) and the request waits Retry-After, or 60 s. After 500 answers
    in a row without a 429 the pause shrinks a little, never below --delay."""

    def __init__(self, delay: float, max_delay: float):
        self.min_delay, self.delay, self.max_delay = delay, delay, max_delay
        self.last, self.calls, self.ok_streak = 0.0, 0, 0

    def post(self, path: str, form: dict):
        for attempt in range(8):
            wait = self.delay - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            self.calls += 1
            req = urllib.request.Request(API + path, data=urllib.parse.urlencode(form).encode(), headers=HEADERS)
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = json.loads(r.read())
                self.ok_streak += 1
                if self.ok_streak >= 500 and self.delay > self.min_delay:
                    self.delay, self.ok_streak = max(self.min_delay, self.delay * 0.9), 0
                if isinstance(body, dict) and body.get("codigo") == "2" and "erro" in body:
                    return None  # FIPE's way of saying "no data for these parameters"
                return body
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    self.ok_streak = 0
                    self.delay = min(self.max_delay, self.delay * 1.5)
                    pause = int(e.headers.get("Retry-After") or 60) if str(e.headers.get("Retry-After", "")).isdigit() else 60
                    print(f"   429: pausing {pause}s, then one request every {self.delay:.1f}s", flush=True)
                    time.sleep(pause)
                    continue
                pause = min(300, 10 * 2 ** attempt)
                print(f"   {path} failed ({e}); trying again in {pause}s", flush=True)
                time.sleep(pause)
            except (urllib.error.URLError, TimeoutError, ValueError, ConnectionError) as e:
                pause = min(300, 10 * 2 ** attempt)
                print(f"   {path} failed ({e}); trying again in {pause}s", flush=True)
                time.sleep(pause)
        raise RuntimeError(f"{path} {form} failed 8 times")


class Store:
    """Append-only JSONL files, loaded once; the keys already written are skipped on resume."""

    def __init__(self, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        self.folder, self.data = folder, {}

    def table(self, name: str) -> dict:
        if name not in self.data:
            self.data[name] = {}
            path = self.folder / f"{name}.jsonl"
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        row = json.loads(line)
                        self.data[name][row["chave"]] = row["resposta"]
        return self.data[name]

    def get(self, name: str, key: str, fetch):
        """The stored answer for key, or fetch it, store it and return it."""
        t = self.table(name)
        if key not in t:
            request, response = fetch()
            with open(self.folder / f"{name}.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"chave": key, "pedido": request, "resposta": response}, ensure_ascii=False) + "\n")
            t[key] = response
        return t[key]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--referencia", type=int, help="FIPE reference table code; default: the latest")
    ap.add_argument("--tipos", type=int, nargs="*", default=[1, 2, 3], help="1 cars, 2 motorcycles, 3 trucks")
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between requests (keep it >= 1)")
    ap.add_argument("--max-delay", type=float, default=8.0, help="ceiling for the pause after 429 answers")
    ap.add_argument("--limit", type=int, help="stop after this many prices (for a test)")
    a = ap.parse_args()
    api = Api(max(a.delay, 1.0), a.max_delay)
    a.out.mkdir(parents=True, exist_ok=True)
    tabelas = api.post("/ConsultarTabelaDeReferencia", {})
    (a.out / "tabelas.json").write_text(json.dumps(tabelas, ensure_ascii=False, indent=1), encoding="utf-8")
    ref = a.referencia or tabelas[0]["Codigo"]
    mes = next((t["Mes"].strip() for t in tabelas if t["Codigo"] == ref), "?")
    st = Store(a.out / str(ref))
    print(f"Reference {ref} ({mes}) -> {st.folder}")
    prices = 0
    try:
        for tipo in a.tipos:
            base = {"codigoTabelaReferencia": ref, "codigoTipoVeiculo": tipo}
            marcas = st.get("marcas", str(tipo), lambda: (base, api.post("/ConsultarMarcas", base) or []))
            for marca in marcas:
                mform = {**base, "codigoMarca": marca["Value"]}
                mkey = f"{tipo}/{marca['Value']}"
                modelos = st.get("modelos", mkey, lambda: (mform, api.post("/ConsultarModelos", mform) or {}))
                for modelo in modelos.get("Modelos") or []:
                    yform = {**mform, "codigoModelo": modelo["Value"]}
                    ykey = f"{mkey}/{modelo['Value']}"
                    anos = st.get("anos", ykey, lambda: (yform, api.post("/ConsultarAnoModelo", yform) or []))
                    for ano in anos:
                        pkey = f"{ykey}/{ano['Value']}"
                        if pkey in st.table("precos"):
                            continue
                        ano_modelo, combustivel = str(ano["Value"]).split("-")
                        pform = {**yform, "anoModelo": ano_modelo, "codigoTipoCombustivel": combustivel,
                                 "tipoVeiculo": TIPOS[tipo], "tipoConsulta": "tradicional"}
                        st.get("precos", pkey, lambda: (pform, api.post("/ConsultarValorComTodosParametros", pform)))
                        prices += 1
                        if prices % 200 == 0:
                            print(f"   {len(st.table('precos')):,} prices ({api.calls:,} requests this run)", flush=True)
                        if a.limit and prices >= a.limit:
                            print(f"Stopped at --limit {a.limit}.")
                            return
                print(f"   tipo {tipo} marca {marca['Label']}: {len(st.table('precos')):,} prices so far", flush=True)
        print(f"Done: {len(st.table('precos')):,} prices for {mes}.")
    except KeyboardInterrupt:
        print("\nStopped. Run the same command again to resume.", file=sys.stderr)


if __name__ == "__main__":
    main()
