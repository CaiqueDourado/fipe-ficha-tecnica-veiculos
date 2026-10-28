"""schema.org JSON-LD for the generated FAQ, the format search engines read."""

from __future__ import annotations

import json


def faq_page(pairs: list[tuple[str, str]], indent: int | None = None) -> str:
    """[(question, answer), ...] -> a FAQPage JSON-LD string (put it in <script type="application/ld+json">)."""
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for q, a in pairs]}
    return json.dumps(data, ensure_ascii=False, indent=indent)
