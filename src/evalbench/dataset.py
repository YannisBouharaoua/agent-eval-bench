"""Lecture et validation d'un jeu de cas au format JSONL."""

from __future__ import annotations

import json
from pathlib import Path

from .models import CATEGORIES, Case

_ALLOWED = {
    "id", "category", "question", "expected_status", "expected_refs", "refs_mode",
    "must_contain", "must_not_contain",
}  # fmt: skip


class DatasetError(ValueError):
    pass


def _as_tuple(value: object, field: str, where: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return tuple(value)
    raise DatasetError(f"{where} : « {field} » doit être une chaîne ou une liste de chaînes.")


def parse_case(data: dict, where: str) -> Case:
    unknown = set(data) - _ALLOWED
    if unknown:
        # Une faute de frappe dans un nom de champ désactiverait un contrôle sans bruit.
        raise DatasetError(f"{where} : champs inconnus {sorted(unknown)}.")
    for required in ("id", "category", "question"):
        if not isinstance(data.get(required), str) or not data[required].strip():
            raise DatasetError(f"{where} : « {required} » est obligatoire.")
    if data["category"] not in CATEGORIES:
        raise DatasetError(f"{where} : catégorie « {data['category']} » inconnue ({CATEGORIES}).")
    mode = data.get("refs_mode", "all")
    if mode not in ("all", "any"):
        raise DatasetError(f"{where} : « refs_mode » vaut « all » ou « any ».")
    case = Case(
        id=data["id"],
        category=data["category"],
        question=data["question"],
        expected_status=_as_tuple(data.get("expected_status"), "expected_status", where),
        expected_refs=_as_tuple(data.get("expected_refs"), "expected_refs", where),
        refs_mode=mode,
        must_contain=_as_tuple(data.get("must_contain"), "must_contain", where),
        must_not_contain=_as_tuple(data.get("must_not_contain"), "must_not_contain", where),
    )
    if not (
        case.expected_status or case.expected_refs or case.must_contain or case.must_not_contain
    ):
        raise DatasetError(f"{where} : le cas ne vérifie rien.")
    return case


def load_dataset(path: Path) -> list[Case]:
    cases: list[Case] = []
    seen: set[str] = set()
    with Path(path).open(encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            if not line.strip():
                continue
            where = f"{path}:{n}"
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise DatasetError(f"{where} : JSON invalide ({e.msg}).") from None
            if not isinstance(data, dict):
                raise DatasetError(f"{where} : un objet JSON est attendu.")
            case = parse_case(data, where)
            if case.id in seen:
                raise DatasetError(f"{where} : identifiant « {case.id} » en double.")
            seen.add(case.id)
            cases.append(case)
    if not cases:
        raise DatasetError(f"{path} : aucun cas.")
    return cases
