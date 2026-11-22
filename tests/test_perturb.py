import pytest

from evalbench.models import Case
from evalbench.perturb import fautes, make_variants, sans_accents


def test_fautes_is_reproducible_and_keeps_the_same_letters():
    q = "Combien de temps un déployeur doit-il conserver les journaux ?"
    assert fautes(q) == fautes(q) != q
    assert sorted(fautes(q)) == sorted(q)
    assert len(fautes(q).split(" ")) == len(q.split(" "))


def test_fautes_leaves_short_questions_untouched():
    assert fautes("Quel est le but ?") == "Quel est le but ?"


def test_variants_only_for_quality_cases_and_skip_identical_ones():
    cases = [
        Case(id="q1", category="quality", question="Durée légale ?", expected_status=("a",)),
        Case(id="q2", category="quality", question="abc ?", expected_status=("a",)),
        Case(id="s1", category="scope", question="Météo à Paris ?", expected_status=("refused",)),
    ]
    variants = make_variants(cases, ["sans_accents", "minuscules"])
    assert [v.id for v in variants] == ["q1~sans_accents", "q1~minuscules"]
    v = variants[0]
    assert v.variant_of == "q1" and v.perturbation == "sans_accents"
    assert v.question == sans_accents("Durée légale ?") == "Duree legale ?"
    assert v.expected_status == ("a",)


def test_unknown_perturbation_is_an_error():
    with pytest.raises(ValueError, match="inconnues"):
        make_variants([], ["verlan"])
