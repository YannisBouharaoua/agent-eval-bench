import pytest

from evalbench.judge import parse_verdict
from evalbench.models import Case, Response
from evalbench.runner import run_cases


def test_parse_verdict_counts_supported_claims():
    raw = (
        'Voici : {"affirmations": [{"texte": "a", "appuyee": true}, '
        '{"texte": "b", "appuyee": false}]}'
    )
    assert parse_verdict(raw) == 0.5


@pytest.mark.parametrize(
    "raw",
    ["pas de json", "{cassé}", '{"affirmations": []}', '{"affirmations": [{"appuyee": "oui"}]}',
     '{"autre": 1}', "[1, 2]"],
)  # fmt: skip
def test_unreadable_verdicts_give_none_not_a_score(raw):
    assert parse_verdict(raw) is None


class FixedTarget:
    name = "fixed"

    def __init__(self, response):
        self.response = response

    def ask(self, question):
        return self.response


class CountingJudge:
    name = "compteur"

    def __init__(self):
        self.calls = 0

    def faithfulness(self, answer, sources):
        self.calls += 1
        return 0.75


def test_judge_only_scores_original_answered_quality_cases_with_sources():
    answered = Response(status="answered", answer="R", source_texts=["S"])
    cases = [
        Case(id="q", category="quality", question="Q", expected_status=("answered",)),
        Case(id="q~v", category="quality", question="Q", variant_of="q"),
        Case(id="s", category="scope", question="Q", expected_status=("refused",)),
    ]
    judge = CountingJudge()
    results = run_cases(FixedTarget(answered), cases, judge=judge)
    assert judge.calls == 1
    assert [r.faithfulness for r in results] == [0.75, None, None]

    judge = CountingJudge()
    run_cases(FixedTarget(Response(status="answered", answer="R")), cases[:1], judge=judge)
    assert judge.calls == 0  # pas de sources : rien à comparer
