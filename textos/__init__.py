"""Text in Brazilian Portuguese from this dataset's tables, by rules: the "about" paragraph and equipment of
a version, its FIPE price history, a FAQ and its JSON-LD.

    pip install "git+https://github.com/CaiqueDourado/fipe-ficha-tecnica-veiculos"
    python -m textos <folder with the dataset files> 003268-9 2012

>>> from textos import Vehicle, history
"""

from .jsonld import faq_page
from .prices import by_model_year, history, ipva
from .text import join, lower_item, money, month_year, number, percent, sentence
from .vehicle import ITEMS, SECTIONS, Vehicle, fuel, measures

__all__ = ["ITEMS", "SECTIONS", "Vehicle", "by_model_year", "faq_page", "fuel", "history", "ipva", "join",
           "lower_item", "measures", "money", "month_year", "number", "percent", "sentence"]
__version__ = "0.1.0"
