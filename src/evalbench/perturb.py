"""Variantes d'une question, pour mesurer la robustesse.

Un utilisateur réel oublie les accents, écrit tout en minuscules et fait des fautes de
frappe. Un agent robuste répond de la même façon. Les variantes sont reproductibles :
la même question donne toujours la même faute de frappe.
"""

from __future__ import annotations

import hashlib
import random
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import replace

from .models import Case


def sans_accents(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    return "".join(c for c in t if not unicodedata.combining(c))


def minuscules(text: str) -> str:
    return text.lower()


def fautes(text: str) -> str:
    """Inverse deux lettres voisines dans un mot long sur trois environ."""
    seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    words = text.split(" ")
    long_words = [i for i, w in enumerate(words) if len(w) >= 6 and w.isalpha()]
    if not long_words:
        return text
    for i in rng.sample(long_words, k=max(1, len(long_words) // 3)):
        w = words[i]
        j = rng.randrange(1, len(w) - 2)
        words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2 :]
    return " ".join(words)


PERTURBATIONS: dict[str, Callable[[str], str]] = {
    "sans_accents": sans_accents,
    "minuscules": minuscules,
    "fautes": fautes,
}


def make_variants(cases: Iterable[Case], names: Iterable[str]) -> list[Case]:
    """Variantes des cas de qualité. Une variante identique à l'original est ignorée."""
    names = list(names)
    unknown = [n for n in names if n not in PERTURBATIONS]
    if unknown:
        raise ValueError(f"Perturbations inconnues : {unknown}. Choix : {sorted(PERTURBATIONS)}.")
    variants: list[Case] = []
    for case in cases:
        if case.category != "quality":
            continue
        for name in names:
            question = PERTURBATIONS[name](case.question)
            if question == case.question:
                continue
            variants.append(
                replace(
                    case,
                    id=f"{case.id}~{name}",
                    question=question,
                    variant_of=case.id,
                    perturbation=name,
                )
            )
    return variants
