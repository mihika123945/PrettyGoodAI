import json

from voice_tester.analyzer import compile_bug_report


def test_report_orders_issues_by_severity(tmp_path):
    for run_id, severity in (("run-low", "low"), ("run-high", "high")):
        run_dir = tmp_path / run_id
        run_dir.mkdir()
        (run_dir / "analysis.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "scenario_id": "scenario",
                    "issues": [
                        {
                            "title": severity,
                            "severity": severity,
                            "evidence": "evidence",
                            "explanation": "explanation",
                            "expected_behavior": "expected",
                            "timestamp": None,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    output = compile_bug_report(tmp_path, tmp_path / "report.md")
    report = output.read_text(encoding="utf-8")
    assert report.index("## 1. high") < report.index("## 2. low")
