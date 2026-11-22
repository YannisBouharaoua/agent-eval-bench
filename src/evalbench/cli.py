"""Ligne de commande : ``evalbench run`` et ``evalbench validate``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .dataset import DatasetError, load_dataset
from .metrics import VERDICTS, decide, evaluate
from .perturb import make_variants
from .report import build_run, to_markdown, write_reports
from .runner import run_cases
from .targets import build_target


def cmd_validate(args: argparse.Namespace) -> int:
    cases = load_dataset(Path(args.dataset))
    by_category: dict[str, int] = {}
    for c in cases:
        by_category[c.category] = by_category.get(c.category, 0) + 1
    print(f"{len(cases)} cas valides : " + ", ".join(f"{k} {v}" for k, v in by_category.items()))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config))
    cases = load_dataset(config.dataset_path)
    cases += make_variants(cases, config.perturbations)
    target = build_target(config.target)

    judge = None
    if config.judge_model and not args.no_judge:
        from .judge import AnthropicJudge

        judge = AnthropicJudge(config.judge_model)

    def progress(result) -> None:
        if not args.quiet:
            print("." if result.passed else "F", end="", flush=True)

    results = run_cases(target, cases, judge=judge, on_result=progress)
    if not args.quiet:
        print()
    metrics = evaluate(results, config.thresholds, config.pricing)
    verdict, reasons = decide(metrics)
    run = build_run(
        args.name or config.name, target.name, results, metrics, verdict, reasons,
        judge_name=judge.name if judge else None,
    )  # fmt: skip
    paths = write_reports(run, Path(args.out))
    print(to_markdown(run))
    print(f"Rapport : {paths['html']}")

    if args.fail_on == "never":
        return 0
    return 1 if VERDICTS.index(verdict) >= VERDICTS.index(args.fail_on) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evalbench", description="Évaluer un agent IA")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run", help="lancer une évaluation")
    p.add_argument("-c", "--config", required=True)
    p.add_argument("-o", "--out", default="reports/dernier")
    p.add_argument(
        "--fail-on",
        choices=["corriger", "arreter", "never"],
        default="arreter",
        help="verdict à partir duquel la commande sort en erreur (défaut : arreter)",
    )
    p.add_argument("--name", help="titre du rapport (défaut : celui de la configuration)")
    p.add_argument("--no-judge", action="store_true", help="ne pas appeler le juge")
    p.add_argument("-q", "--quiet", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("validate", help="vérifier un jeu de cas")
    p.add_argument("dataset")
    p.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (DatasetError, ValueError, FileNotFoundError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
