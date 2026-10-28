"""Text from FIPE prices: the price of a version today, how it moved over the months, what each model
year is worth, and an IPVA estimate from a rate you supply.

Inputs are plain Python (dates as 'YYYY-MM-DD' strings or datetime.date, prices as numbers) so the
functions work with pandas rows, SQL results or JSON alike. Rewritten from the author's 2022 C# pages:
the "lançado com R$ X, ofertado por R$ Y" sentence, the price history and the IPVA block, which used the
car rate for motorcycles and took the price of whatever version came last in a loop.
"""

from __future__ import annotations

import datetime as dt
from typing import Iterable

from .text import join, money, month_year, percent, sentence


def _date(value) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value)[:10])


def _month(d: dt.date) -> str:
    return month_year(d.year, d.month)


def history(series: Iterable[tuple], name: str, min_change: float = 0.03) -> str:
    """series: (reference month, price) of ONE version and model year. Describes the latest price, the change
    since the first month, and the peak or the low when it is not at an end of the series.

    >>> history([("2020-01-01", 31989), ("2022-04-01", 41500), ("2023-02-01", 38640)], "Ford EcoSport XL 2012")
    'Em fevereiro de 2023, o Ford EcoSport XL 2012 valia R$ 38.640 na tabela FIPE, 21% a mais que em janeiro de 2020 (R$ 31.989). O maior valor foi R$ 41.500, em abril de 2022.'
    """
    pts = sorted((_date(d), float(v)) for d, v in series if v)
    if not pts:
        return ""
    (d0, v0), (d1, v1) = pts[0], pts[-1]
    out = [f"Em {_month(d1)}, o {name} valia {money(v1)} na tabela FIPE"]
    if len(pts) > 1:
        change = v1 / v0 - 1
        if abs(change) < min_change:
            out[0] += f", praticamente o mesmo que em {_month(d0)} ({money(v0)})"
        else:
            out[0] += f", {percent(abs(change))} a {'mais' if change > 0 else 'menos'} que em {_month(d0)} ({money(v0)})"
        peak = max(pts, key=lambda p: p[1])
        low = min(pts, key=lambda p: p[1])
        if peak[0] not in (d0, d1) and peak[1] > max(v0, v1) * (1 + min_change):
            out.append(f"O maior valor foi {money(peak[1])}, em {_month(peak[0])}")
        elif low[0] not in (d0, d1) and low[1] < min(v0, v1) * (1 - min_change):
            out.append(f"O menor valor foi {money(low[1])}, em {_month(low[0])}")
    return " ".join(sentence(s) for s in out)


def by_model_year(rows: Iterable[tuple], name: str, reference=None) -> str:
    """rows: (model year or None for zero km, price) of ONE FIPE code in one month. Lists the range of years
    and what the newest and oldest are worth; with a zero km price, how much the used ones keep of it.

    >>> by_model_year([(None, 120000), (2024, 98000), (2020, 70000)], "Exemplo 1.0", "2026-10-01")
    'Na tabela FIPE de outubro de 2026, há preços do Exemplo 1.0 de 2020 a 2024 e zero km. O zero km sai por R$ 120.000; o 2024, por R$ 98.000 (82% do zero km); o 2020, por R$ 70.000 (58% do zero km).'
    """
    rows = [(y, float(v)) for y, v in rows if v]
    zero = next((v for y, v in rows if y is None), None)
    used = sorted(((int(y), v) for y, v in rows if y is not None), reverse=True)
    if not used and zero is None:
        return ""
    when = f"Na tabela FIPE de {_month(_date(reference))}" if reference else "Na tabela FIPE"
    if len(used) == 1 and zero is None:
        return sentence(f"{when}, o {name} {used[0][0]} vale {money(used[0][1])}")
    years = f"de {used[-1][0]} a {used[0][0]}" if len(used) > 1 else (f"de {used[0][0]}" if used else "")
    first = f"{when}, há preços do {name} " + join([x for x in (years, "zero km" if zero else "") if x])
    parts = []
    if zero:
        parts.append(f"o zero km sai por {money(zero)}")
    for y, v in ([used[0], used[-1]] if len(used) > 1 else used):
        verb = ", por" if parts else " sai por"
        parts.append(f"o {y}{verb} {money(v)}" + (f" ({percent(v / zero)} do zero km)" if zero else ""))
    return sentence(first) + " " + sentence("; ".join(parts))


def ipva(value: float, rate: float, state: str | None = None, preposition: str = "em", year: int | None = None) -> str:
    """IPVA estimate = FIPE value x the state's rate (in %). Rates change by state, year and vehicle type
    (motorcycles usually pay less): pass the one that applies; none is shipped.

    >>> ipva(38640, 4, "São Paulo", "em", 2027)
    'Com alíquota de 4% em São Paulo, o IPVA 2027 fica em torno de R$ 1.546 (4% de R$ 38.640, o valor na tabela FIPE).'
    """
    where = f" {preposition} {state}" if state else ""
    rate_text = (f"{rate:g}".replace(".", ",")) + "%"
    label = f"IPVA {year}" if year else "IPVA"
    return sentence(f"Com alíquota de {rate_text}{where}, o {label} fica em torno de {money(value * rate / 100)} "
                    f"({rate_text} de {money(value)}, o valor na tabela FIPE)")
