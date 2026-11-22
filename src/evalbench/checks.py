"""Contrôles déterministes appliqués à chaque réponse.

Aucun de ces contrôles n'appelle un modèle : deux passages sur la même réponse donnent
le même résultat, et chaque échec s'explique par une règle lisible.
"""

from __future__ import annotations

import re
import unicodedata

from .models import Case, Check, Response


def fold(text: str) -> str:
    """Minuscules, sans accents, espaces normalisés (y compris insécables)."""
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def run_checks(case: Case, response: Response) -> list[Check]:
    checks: list[Check] = []
    if response.error:
        return [Check("reponse_obtenue", False, response.error)]

    if case.expected_status:
        ok = response.status in case.expected_status
        checks.append(
            Check(
                "statut",
                ok,
                ""
                if ok
                else f"attendu {' ou '.join(case.expected_status)}, reçu {response.status}",
            )
        )

    if case.expected_refs:
        cited = {fold(c) for c in response.citations}
        found = [r for r in case.expected_refs if fold(r) in cited]
        ok = bool(found) if case.refs_mode == "any" else len(found) == len(case.expected_refs)
        missing = [r for r in case.expected_refs if r not in found]
        checks.append(
            Check(
                "references_attendues",
                ok,
                ""
                if ok
                else f"non citées : {', '.join(missing)} ; citées : "
                f"{', '.join(response.citations) or 'aucune'}",
            )
        )

    # Une référence citée doit figurer dans les sources que la cible déclare avoir lues.
    if response.source_refs is not None and response.citations:
        sources = {fold(s) for s in response.source_refs}
        orphans = [c for c in response.citations if fold(c) not in sources]
        checks.append(
            Check(
                "citations_appuyees",
                not orphans,
                "" if not orphans else f"citées sans source : {', '.join(orphans)}",
            )
        )

    answer = fold(response.answer)
    for needle in case.must_contain:
        ok = fold(needle) in answer
        checks.append(Check("contient", ok, "" if ok else f"absent : « {needle} »"))
    for needle in case.must_not_contain:
        ok = fold(needle) not in answer
        checks.append(Check("ne_contient_pas", ok, "" if ok else f"présent : « {needle} »"))
    return checks
