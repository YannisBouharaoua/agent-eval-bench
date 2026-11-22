from evalbench.checks import fold, run_checks
from evalbench.models import Case, Response


def case(**kw):
    return Case(id="c", category="quality", question="Q", **kw)


def failed(checks):
    return [c.name for c in checks if not c.passed]


def test_fold_ignores_case_accents_and_non_breaking_spaces():
    assert fold("35 000 000  EUR, Élevé") == "35 000 000 eur, eleve"


def test_error_response_fails_whatever_the_expectations():
    checks = run_checks(case(must_not_contain=("x",)), Response(status="error", error="HTTP 500"))
    assert failed(checks) == ["reponse_obtenue"] and checks[0].detail == "HTTP 500"


def test_status_accepts_any_listed_value():
    c = case(expected_status=("answered", "pending_review"))
    assert not failed(run_checks(c, Response(status="pending_review")))
    assert failed(run_checks(c, Response(status="refused"))) == ["statut"]


def test_expected_refs_all_versus_any():
    r = Response(status="answered", citations=["article 6"])
    both = ("Article 6", "Annexe III")
    assert failed(run_checks(case(expected_refs=both), r)) == ["references_attendues"]
    assert not failed(run_checks(case(expected_refs=both, refs_mode="any"), r))


def test_citation_without_matching_source_is_flagged():
    r = Response(status="answered", citations=["Article 5", "Article 71"],
                 source_refs=["Article 5"])  # fmt: skip
    checks = run_checks(case(expected_refs=("Article 5",)), r)
    assert failed(checks) == ["citations_appuyees"]
    assert "Article 71" in checks[-1].detail


def test_citation_support_is_skipped_when_target_exposes_no_sources():
    r = Response(status="answered", citations=["Article 71"], source_refs=None)
    names = [c.name for c in run_checks(case(must_not_contain=("zzz",)), r)]
    assert names == ["ne_contient_pas"]


def test_must_contain_and_must_not_contain_are_accent_insensitive():
    r = Response(status="answered", answer="Pratique INTERDITE, amende de 35 000 000 EUR")
    assert not failed(run_checks(case(must_contain=("interdite", "35 000 000")), r))
    assert failed(run_checks(case(must_not_contain=("Interdité",)), r)) == ["ne_contient_pas"]
    assert failed(run_checks(case(must_contain=("six mois",)), r)) == ["contient"]
