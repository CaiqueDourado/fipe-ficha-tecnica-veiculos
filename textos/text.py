"""Small pieces of Brazilian Portuguese used by every template: lists, money, numbers, months, case."""

from __future__ import annotations

import math
import re

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]
# words that keep their case inside a sentence
ACRONYMS = {"abs", "usb", "gps", "cd", "mp3", "fm", "am", "gnv", "tv", "led", "4x4", "cvt", "suv", "ebd", "esp",
            "ohc", "dohc", "v6", "v8", "tdi", "tsi", "gm", "vw", "bmw"}


def join(items, conjunction: str = "e") -> str:
    """['a', 'b', 'c'] -> 'a, b e c' (no serial comma, as in Portuguese)."""
    items = [str(i) for i in items if i not in (None, "")]
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} {conjunction} {items[-1]}"


def number(value: float, decimals: int = 0) -> str:
    """1234.5 -> '1.234,5' whatever the machine locale."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def money(value: float, cents: bool = False) -> str:
    """38640 -> 'R$ 38.640'; with cents -> 'R$ 38.640,00'."""
    return "R$ " + number(value, 2 if cents else 0)


def percent(fraction: float, decimals: int = 0) -> str:
    """0.234 -> '23%'."""
    return number(fraction * 100, decimals) + "%"


def month_year(year: int, month: int) -> str:
    """2026, 10 -> 'outubro de 2026'."""
    return f"{MESES[month - 1]} de {year}"


def lower_item(text: str) -> str:
    """'Airbag motorista' -> 'airbag motorista', 'Freios abs' -> 'freios ABS', 'Cd player com mp3' -> 'CD player com MP3'."""
    words = []
    for w in str(text).split():
        bare = w.lower().strip(".,;:")
        words.append(w.upper() if bare in ACRONYMS else w.lower())
    return " ".join(words)


def sentence(text: str) -> str:
    """Capital first letter, one space between words, no space before punctuation, a final period."""
    text = re.sub(r"\s+", " ", str(text)).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    if not text:
        return text
    text = text[0].upper() + text[1:]
    return text if text[-1] in ".!?" else text + "."


def is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or str(value).strip() in ("", "nan", "None")
