import pytest

from evalbench.metrics import decide, evaluate, percentile, validate_thresholds
from evalbench.models import Case, CaseResult, Check, Response


def result(id, category, passed, variant_of=None, latency=10.0, tokens=None, error=None):
    response = Response(status="error" if error else "answered", latency_ms=latency, error=error)
    if tokens:
        response.input_tokens, response.output_tokens = tokens
    return CaseResult(
        case=Case(id=id, category=category, question="Q", variant_of=variant_of),
        response=response,
        checks=[Check("c", passed)],
    )


def by_key(metrics):
    return {m.spec.key: m for m in metrics}


T = {
    "quality": {"target": 0.8, "blocking": 0.5},
    "security": {"target": 1.0, "blocking": 0.9},
    "latency_p95_ms": {"target": 100, "blocking": 500},
}


def test_percentile_uses_nearest_rank():
    values = [float(v) for v in range(1, 21)]
    assert percentile(values, 95) == 19.0 and percentile(values, 50) == 10.0
    assert percentile([7.0], 95) == 7.0


def test_category_ratios_ignore_variants():
    rs = [
        result("a", "quality", True),
        result("b", "quality", False),
        result("a~x", "quality", False, variant_of="a"),
    ]
    m = by_key(evaluate(rs, T))
    assert m["quality"].value == 0.5 and m["quality"].n == 2


def test_robustness_only_counts_variants_of_passing_originals():
    rs = [
        result("a", "quality", True),
        result("b", "quality", False),
        result("a~1", "quality", True, variant_of="a"),
        result("a~2", "quality", False, variant_of="a"),
        result("b~1", "quality", False, variant_of="b"),
    ]
    m = by_key(evaluate(rs, {}))["robustness"]
    assert m.value == 0.5 and m.n == 2


def test_robustness_is_unmeasured_when_no_original_passes():
    rs = [result("a", "quality", False), result("a~1", "quality", False, variant_of="a")]
    m = by_key(evaluate(rs, {}))["robustness"]
    assert m.value is None and m.state == "non_mesure" and "rien à comparer" in m.note


def test_states_for_higher_and_lower_is_better():
    rs = [result(f"q{i}", "quality", i < 6) for i in range(10)]
    rs += [result("x", "security", True, latency=600.0)]
    m = by_key(evaluate(rs, T))
    assert m["quality"].state == "a_corriger"  # 0.6 entre 0.5 et 0.8
    assert m["security"].state == "atteint"
    assert m["latency_p95_ms"].state == "bloquant"  # 600 ms au-delà de 500
    assert m["scope"].state == "non_mesure"


def test_boundaries_are_inclusive():
    rs = [result(f"q{i}", "quality", i < 8) for i in range(10)] + [
        result("l", "scope", True, latency=100.0)
    ]
    m = by_key(evaluate(rs, {**T, "latency_p95_ms": {"target": 100, "blocking": 100}}))
    assert m["quality"].state == "atteint"
    assert m["latency_p95_ms"].state == "atteint"


def test_cost_needs_pricing_and_usage():
    pricing = {"input_per_mtok_eur": 3.0, "output_per_mtok_eur": 15.0}
    with_usage = [result("a", "quality", True, tokens=(1000, 200))]
    m = by_key(evaluate(with_usage, {}, pricing))["cost_per_question_eur"]
    assert m.value == pytest.approx(0.006) and m.state == "sans_seuil"
    assert by_key(evaluate(with_usage, {}))["cost_per_question_eur"].value is None
    no_usage = [result("a", "quality", True)]
    m = by_key(evaluate(no_usage, {}, pricing))["cost_per_question_eur"]
    assert m.value is None and "jetons" in m.note


def test_errors_are_excluded_from_latency_but_fail_quality():
    rs = [result("a", "quality", False, error="HTTP 500", latency=9999.0),
          result("b", "quality", True, latency=20.0)]  # fmt: skip
    m = by_key(evaluate(rs, {}))
    assert m["latency_p95_ms"].value == 20.0 and m["quality"].value == 0.5


def test_verdict_follows_the_worst_criterion():
    ok = [result(f"q{i}", "quality", True) for i in range(5)] + [result("x", "security", True)]
    assert decide(evaluate(ok, T))[0] == "poursuivre"

    below_target = ok[:3] + [result("q8", "quality", False), result("x", "security", True)]
    verdict, reasons = decide(evaluate(below_target, T))
    assert verdict == "corriger" and "Qualité" in reasons[0]

    breach = ok[:5] + [result("x", "security", False)]
    verdict, reasons = decide(evaluate(breach, T))
    assert verdict == "arreter" and "Sécurité" in reasons[0]


def test_unmeasured_criterion_with_a_threshold_prevents_poursuivre():
    only_quality = [result(f"q{i}", "quality", True) for i in range(5)]
    verdict, reasons = decide(evaluate(only_quality, T))
    assert verdict == "corriger"
    assert "Non mesuré" in reasons[0] and "Sécurité" in reasons[0]


@pytest.mark.parametrize(
    "thresholds",
    [
        {"vitesse": {"target": 1, "blocking": 0}},
        {"quality": {"target": 0.5}},
        {"quality": {"target": 0.5, "blocking": 0.8}},
        {"latency_p95_ms": {"target": 500, "blocking": 100}},
    ],
)
def test_invalid_thresholds_are_rejected(thresholds):
    with pytest.raises(ValueError):
        validate_thresholds(thresholds)
