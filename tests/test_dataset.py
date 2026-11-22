import json

import pytest

from evalbench.dataset import DatasetError, load_dataset


def write(tmp_path, *rows):
    p = tmp_path / "d.jsonl"
    p.write_text("\n".join(r if isinstance(r, str) else json.dumps(r) for r in rows))
    return p


def test_loads_a_valid_case_and_normalizes_strings_to_tuples(tmp_path):
    p = write(tmp_path, {"id": "a", "category": "scope", "question": "Q ?",
                         "expected_status": "refused"})  # fmt: skip
    (case,) = load_dataset(p)
    assert case.expected_status == ("refused",) and case.refs_mode == "all"


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ({"id": "a", "category": "scope", "question": "Q", "expected_statut": "x"}, "inconnus"),
        ({"id": "a", "category": "vitesse", "question": "Q", "expected_status": "x"}, "catégorie"),
        ({"id": "a", "category": "scope", "question": "Q"}, "ne vérifie rien"),
        ({"category": "scope", "question": "Q", "expected_status": "x"}, "obligatoire"),
        ({"id": "a", "category": "scope", "question": "Q", "must_contain": [1]}, "liste"),
        ("{pas du json", "JSON invalide"),
    ],
)
def test_rejects_invalid_rows_with_file_and_line(tmp_path, row, message):
    with pytest.raises(DatasetError, match=message) as e:
        load_dataset(write(tmp_path, row))
    assert "d.jsonl:1" in str(e.value)


def test_rejects_duplicate_ids_and_empty_files(tmp_path):
    row = {"id": "a", "category": "scope", "question": "Q", "expected_status": "refused"}
    with pytest.raises(DatasetError, match="en double"):
        load_dataset(write(tmp_path, row, row))
    with pytest.raises(DatasetError, match="aucun cas"):
        load_dataset(write(tmp_path, ""))


def test_shipped_datasets_are_valid():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "datasets"
    assert len(load_dataset(root / "demo.jsonl")) == 9
    cases = load_dataset(root / "ai_act.jsonl")
    assert {c.category for c in cases} == {"quality", "scope", "oversight", "security"}
