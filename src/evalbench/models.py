"""Structures de données partagées."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CATEGORIES = ("quality", "scope", "oversight", "security")


@dataclass(frozen=True)
class Case:
    """Un cas de test : une question et ce qu'on attend de la réponse."""

    id: str
    category: str
    question: str
    expected_status: tuple[str, ...] = ()
    expected_refs: tuple[str, ...] = ()
    refs_mode: str = "all"  # "all" : toutes les références ; "any" : au moins une
    must_contain: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = ()
    variant_of: str | None = None  # identifiant du cas d'origine, pour un cas perturbé
    perturbation: str | None = None


@dataclass
class Response:
    """Ce que la cible a renvoyé, ramené à un format commun."""

    status: str
    answer: str = ""
    citations: list[str] = field(default_factory=list)
    source_refs: list[str] | None = None  # None : la cible n'expose pas ses sources
    source_texts: list[str] = field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float = 0.0
    error: str | None = None


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class CaseResult:
    case: Case
    response: Response
    checks: list[Check]
    faithfulness: float | None = None

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.case.id,
            "category": self.case.category,
            "variant_of": self.case.variant_of,
            "perturbation": self.case.perturbation,
            "question": self.case.question,
            "passed": self.passed,
            "status": self.response.status,
            "answer": self.response.answer,
            "citations": self.response.citations,
            "latency_ms": round(self.response.latency_ms, 1),
            "error": self.response.error,
            "faithfulness": self.faithfulness,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks
            ],
        }
