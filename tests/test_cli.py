import json
from pathlib import Path

from evalbench.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_demo_run_end_to_end(tmp_path, capsys):
    code = main(["run", "-c", str(ROOT / "bench.demo.toml"), "-o", str(tmp_path), "-q"])
    assert code == 1  # verdict « arreter » : la commande échoue par défaut

    run = json.loads((tmp_path / "run.json").read_text())
    assert run["verdict"] == "arreter"
    states = {m["key"]: m["state"] for m in run["metrics"]}
    assert states["quality"] == "atteint"
    assert states["oversight"] == states["security"] == "bloquant"
    assert states["cost_per_question_eur"] == "atteint"
    failed = {c["id"] for c in run["cases"] if not c["passed"]}
    assert {"o-recrutement", "x-repete"} <= failed
    assert any("~fautes" in i for i in failed)  # la faiblesse aux fautes de frappe est vue

    html = (tmp_path / "report.html").read_text()
    assert "Arrêter ou revoir la conception" in html and "CANARI-7431" in html
    assert "Contrôle humain" in (tmp_path / "summary.md").read_text()
    assert "Sous le seuil bloquant" in capsys.readouterr().out


def test_fail_on_controls_the_exit_code(tmp_path):
    base = ["run", "-c", str(ROOT / "bench.demo.toml"), "-o", str(tmp_path), "-q"]
    assert main([*base, "--fail-on", "never"]) == 0
    assert main([*base, "--fail-on", "corriger"]) == 1


def test_report_escapes_agent_output(tmp_path):
    from evalbench.metrics import decide, evaluate
    from evalbench.models import Case, CaseResult, Check, Response
    from evalbench.report import build_run, to_html

    payload = "<script>alert(1)</script>"
    r = CaseResult(
        case=Case(id="x", category="security", question=payload),
        response=Response(status="answered", answer=payload),
        checks=[Check("ne_contient_pas", False, payload)],
    )
    metrics = evaluate([r], {})
    html = to_html(build_run(payload, payload, [r], metrics, *decide(metrics)))
    assert payload not in html and "&lt;script&gt;" in html


def test_config_errors_exit_with_code_2(tmp_path, capsys):
    bad = tmp_path / "bench.toml"
    bad.write_text('[target]\ntype = "demo"\n')
    assert main(["run", "-c", str(bad)]) == 2
    assert "[dataset]" in capsys.readouterr().err

    bad.write_text(
        '[target]\ntype = "ftp"\n[dataset]\npath = "' + str(ROOT / "datasets/demo.jsonl") + '"\n'
    )
    assert main(["run", "-c", str(bad), "-o", str(tmp_path / "o")]) == 2
    assert main(["validate", str(tmp_path / "absent.jsonl")]) == 2


def test_validate_command(capsys):
    assert main(["validate", str(ROOT / "datasets/ai_act.jsonl")]) == 0
    assert "26 cas valides" in capsys.readouterr().out
