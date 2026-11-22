"""Exécution des cas contre une cible."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable

from .checks import run_checks
from .judge import Judge
from .models import Case, CaseResult
from .targets import Target


def run_cases(
    target: Target,
    cases: Iterable[Case],
    judge: Judge | None = None,
    on_result: Callable[[CaseResult], None] | None = None,
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in cases:
        start = time.perf_counter()
        response = target.ask(case.question)
        response.latency_ms = (time.perf_counter() - start) * 1000
        result = CaseResult(case=case, response=response, checks=run_checks(case, response))
        # Le juge ne note que les réponses d'origine, rédigées et accompagnées de sources.
        if (
            judge is not None
            and case.variant_of is None
            and case.category == "quality"
            and response.status == "answered"
            and response.source_texts
        ):
            result.faithfulness = judge.faithfulness(response.answer, response.source_texts)
        results.append(result)
        if on_result:
            on_result(result)
    return results
