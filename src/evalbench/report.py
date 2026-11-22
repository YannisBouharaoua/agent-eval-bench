"""Rapports : JSON pour les machines, Markdown pour la CI, HTML pour les humains."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from . import __version__
from .metrics import MetricResult
from .models import CaseResult

VERDICT_LABELS = {
    "poursuivre": "Poursuivre",
    "corriger": "Corriger avant de poursuivre",
    "arreter": "Arrêter ou revoir la conception",
}
STATE_LABELS = {
    "atteint": "Atteint",
    "a_corriger": "À corriger",
    "bloquant": "Bloquant",
    "non_mesure": "Non mesuré",
    "sans_seuil": "Sans seuil",
}


def fmt(value: float | None, unit: str) -> str:
    if value is None:
        return "—"
    if unit == "ratio":
        return f"{value * 100:.0f} %"
    if unit == "ms":
        return f"{value:,.0f} ms".replace(",", " ")
    return f"{value:.4f} €".replace(".", ",")


def build_run(
    name: str,
    target_name: str,
    results: list[CaseResult],
    metrics: list[MetricResult],
    verdict: str,
    reasons: list[str],
    judge_name: str | None = None,
) -> dict[str, Any]:
    judged = [r.faithfulness for r in results if r.faithfulness is not None]
    return {
        "name": name,
        "target": target_name,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "evalbench_version": __version__,
        "verdict": verdict,
        "reasons": reasons,
        "metrics": [m.to_dict() for m in metrics],
        "faithfulness": {
            "judge": judge_name,
            "mean": sum(judged) / len(judged) if judged else None,
            "n": len(judged),
        },
        "cases": [r.to_dict() for r in results],
    }


def to_markdown(run: dict[str, Any]) -> str:
    lines = [
        f"## {run['name']} — {VERDICT_LABELS[run['verdict']]}",
        "",
        *[f"- {r}" for r in run["reasons"]],
        "",
        "| Critère | Mesure | Cible | Seuil bloquant | Cas | État |",
        "|---|---|---|---|---|---|",
    ]
    for m in run["metrics"]:
        state = STATE_LABELS[m["state"]] + (f" ({m['note']})" if m["note"] else "")
        lines.append(
            f"| {m['label']} | {fmt(m['value'], m['unit'])} | {fmt(m['target'], m['unit'])} | "
            f"{fmt(m['blocking'], m['unit'])} | {m['n']} | {state} |"
        )
    failed = [c for c in run["cases"] if not c["passed"]]
    lines += ["", f"{len(run['cases']) - len(failed)} cas réussis sur {len(run['cases'])}."]
    return "\n".join(lines) + "\n"


_CSS = """
:root{--ok:#1a7f4b;--warn:#b26a00;--bad:#c0392b;--mute:#667085;--line:#e4e7ec;--bg:#f8f9fb}
*{box-sizing:border-box}body{font:15px/1.5 system-ui,sans-serif;color:#1d2433;margin:0;
background:var(--bg)}main{max-width:980px;margin:0 auto;padding:32px 20px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 12px}
.meta{color:var(--mute);font-size:13px}
.verdict{border-radius:10px;padding:18px 20px;margin:20px 0;background:#fff;
border:1px solid var(--line);border-left:6px solid var(--mute)}
.verdict.poursuivre{border-left-color:var(--ok)}.verdict.corriger{border-left-color:var(--warn)}
.verdict.arreter{border-left-color:var(--bad)}.verdict strong{font-size:19px}
.verdict ul{margin:8px 0 0;padding-left:20px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);
border-radius:10px;overflow:hidden}th,td{padding:9px 12px;text-align:left;
border-bottom:1px solid var(--line);vertical-align:top}th{font-size:12px;
text-transform:uppercase;letter-spacing:.04em;color:var(--mute);background:#fcfcfd}
tr:last-child td{border-bottom:0}td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.tag{display:inline-block;padding:1px 9px;border-radius:99px;font-size:12px;font-weight:600;
border:1px solid}.atteint,.pass{color:var(--ok)}.a_corriger{color:var(--warn)}
.bloquant,.fail{color:var(--bad)}.non_mesure,.sans_seuil{color:var(--mute)}
.small{font-size:13px;color:var(--mute)}details{background:#fff;border:1px solid var(--line);
border-radius:10px;margin:8px 0;padding:10px 14px}summary{cursor:pointer;font-weight:600}
pre{white-space:pre-wrap;word-break:break-word;background:var(--bg);padding:10px;
border-radius:6px;font-size:13px;margin:8px 0}
"""


def to_html(run: dict[str, Any]) -> str:
    e = escape
    rows = []
    for m in run["metrics"]:
        note = f'<div class="small">{e(m["note"])}</div>' if m["note"] else ""
        rows.append(
            f"<tr><td><strong>{e(m['label'])}</strong></td>"
            f'<td class="num">{fmt(m["value"], m["unit"])}</td>'
            f'<td class="num">{fmt(m["target"], m["unit"])}</td>'
            f'<td class="num">{fmt(m["blocking"], m["unit"])}</td>'
            f'<td class="num">{m["n"]}</td>'
            f'<td><span class="tag {m["state"]}">{STATE_LABELS[m["state"]]}</span>{note}</td></tr>'
        )
    failed = [c for c in run["cases"] if not c["passed"]]
    blocks = []
    for c in failed:
        checks = "".join(
            f'<li class="{"pass" if k["passed"] else "fail"}">{e(k["name"])}'
            f"{' — ' + e(k['detail']) if k['detail'] else ''}</li>"
            for k in c["checks"]
        )
        origin = f" · variante « {e(c['perturbation'])} »" if c["perturbation"] else ""
        blocks.append(
            f"<details><summary>{e(c['id'])} <span class='small'>{e(c['category'])}{origin}"
            f"</span></summary><div class='small'>Question</div><pre>{e(c['question'])}</pre>"
            f"<div class='small'>Réponse ({e(c['status'])})</div>"
            f"<pre>{e(c['answer'] or c['error'] or '—')}</pre><ul>{checks}</ul></details>"
        )
    faith = run["faithfulness"]
    faith_html = ""
    if faith["judge"]:
        faith_html = (
            f"<h2>Fidélité aux sources (indicatif)</h2><p>Note moyenne : "
            f"<strong>{fmt(faith['mean'], 'ratio')}</strong> sur {faith['n']} réponses, "
            f"jugées par {e(faith['judge'])}. Cette note n'entre pas dans le verdict.</p>"
        )
    reasons = "".join(f"<li>{e(r)}</li>" for r in run["reasons"])
    passed = len(run["cases"]) - len(failed)
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(run["name"])} — rapport d'évaluation</title><style>{_CSS}</style></head>
<body><main>
<h1>{e(run["name"])}</h1>
<div class="meta">Cible : {e(run["target"])} · {e(run["generated_at"])} ·
evalbench {e(run["evalbench_version"])}</div>
<div class="verdict {run["verdict"]}"><strong>{VERDICT_LABELS[run["verdict"]]}</strong>
<ul>{reasons}</ul></div>
<h2>Critères</h2>
<table><thead><tr><th>Critère</th><th>Mesure</th><th>Cible</th><th>Seuil bloquant</th>
<th>Cas</th><th>État</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
{faith_html}
<h2>Cas en échec ({len(failed)} sur {len(run["cases"])})</h2>
{"".join(blocks) or f"<p>Les {passed} cas sont réussis.</p>"}
</main></body></html>
"""


def write_reports(run: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / "run.json",
        "markdown": out_dir / "summary.md",
        "html": out_dir / "report.html",
    }
    paths["json"].write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["markdown"].write_text(to_markdown(run), encoding="utf-8")
    paths["html"].write_text(to_html(run), encoding="utf-8")
    return paths
