"""Look at the FIPE JSON files that g1 (Globo) serves, before writing the collector.

    python probe_globo_fipe.py --out D:\\fipe_raw\\_globo_probe

Downloads the vehicle lists (carro, moto, caminhao) and two vehicles' price files, saves them as they
come, and prints the structure. Only a few requests, one per second.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://g1.globo.com/static/fipe/json"
LISTS = ["carro", "moto", "caminhao", "carros", "motos", "caminhoes"]


def get(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (portfolio data probe)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def shape(obj, depth=0, limit=3) -> str:
    pad = "  " * depth
    if isinstance(obj, dict):
        lines = [f"{pad}dict with {len(obj)} keys"]
        for k in list(obj)[:12]:
            lines.append(f"{pad}  {k!r}: " + shape(obj[k], depth + 2, limit).lstrip())
        return "\n".join(lines)
    if isinstance(obj, list):
        head = f"{pad}list with {len(obj)} items"
        return head + ("\n" + shape(obj[0], depth + 1, limit) if obj else "")
    return f"{pad}{type(obj).__name__}: {str(obj)[:80]!r}"


def first_code(obj) -> str | None:
    """Find something that looks like a FIPE code (000000-0) anywhere in the list file."""
    text = json.dumps(obj, ensure_ascii=False)
    import re
    m = re.search(r"\b\d{6}-\d\b", text)
    return m.group(0) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    report = []
    codes = {"carro": "023067-7"}
    for name in LISTS:
        url = f"{BASE}/{name}.json"
        status, body = get(url)
        report.append(f"{status}  {url}  {len(body):,} bytes")
        if status == 200 and body:
            (a.out / f"{name}.json").write_bytes(body)
            obj = json.loads(body)
            report.append(shape(obj))
            code = first_code(obj)
            if code:
                codes.setdefault(name, code)
        time.sleep(1)
    for name, code in codes.items():
        url = f"{BASE}/{name}/{code}.json"
        status, body = get(url)
        report.append(f"{status}  {url}  {len(body):,} bytes")
        if status == 200 and body:
            (a.out / f"{name}_{code}.json").write_bytes(body)
            report.append(shape(json.loads(body)))
        time.sleep(1)
    text = "\n".join(report)
    (a.out / "relatorio.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"\n-> {a.out}  (compacte a pasta e me envie)")


if __name__ == "__main__":
    main()
