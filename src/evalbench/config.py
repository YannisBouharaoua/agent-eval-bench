"""Lecture du fichier de configuration (TOML)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .metrics import validate_thresholds


@dataclass
class BenchConfig:
    name: str
    target: dict[str, Any]
    dataset_path: Path
    perturbations: list[str] = field(default_factory=list)
    thresholds: dict[str, dict[str, float]] = field(default_factory=dict)
    pricing: dict[str, float] | None = None
    judge_model: str | None = None


def load_config(path: Path) -> BenchConfig:
    path = Path(path)
    with path.open("rb") as f:
        raw = tomllib.load(f)
    for section in ("target", "dataset"):
        if section not in raw:
            raise ValueError(f"{path} : section [{section}] manquante.")
    if "path" not in raw["dataset"]:
        raise ValueError(f"{path} : [dataset] doit indiquer « path ».")
    thresholds = raw.get("thresholds", {})
    validate_thresholds(thresholds)
    pricing = raw.get("pricing")
    if pricing is not None and set(pricing) != {"input_per_mtok_eur", "output_per_mtok_eur"}:
        raise ValueError(
            f"{path} : [pricing] attend « input_per_mtok_eur » et « output_per_mtok_eur »."
        )
    return BenchConfig(
        name=raw.get("name", path.stem),
        target=raw["target"],
        dataset_path=(path.parent / raw["dataset"]["path"]).resolve(),
        perturbations=list(raw["dataset"].get("perturbations", [])),
        thresholds=thresholds,
        pricing=pricing,
        judge_model=raw.get("judge", {}).get("model"),
    )
