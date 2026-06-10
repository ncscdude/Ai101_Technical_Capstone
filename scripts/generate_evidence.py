from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from canonicalizer import canonicalize  # noqa: E402


TODAY = date(2026, 6, 9)


def main() -> int:
    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)

    test_run = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    samples = {
        "PASS": (
            "Q1 2026 Quarterly Report\nDate: 15 March 2026\nPrepared by: Finance Team\n",
            "Q1_Report.docx",
        ),
        "WARN": (
            "Meeting Summary - Q2 Report\nDate: 2026-04-10\nThis document summarizes the Q2 planning session.\n",
            "Mixed.docx",
        ),
        "FAIL": (
            "Q2 Sales Presentation\nDate: 2026-06-09\nSlide 1: Revenue Overview\n",
            "Slides.pptx",
        ),
    }

    lines = [
        "FILE CANONICALIZER v0.5 - TEST EVIDENCE",
        "Generated: 2026-06-10",
        "Runner: python -m unittest discover -s tests -v",
        "",
        "TEST OUTPUT",
        "-----------",
        test_run.stdout.strip(),
        test_run.stderr.strip(),
        "",
        "SAMPLE OUTPUTS",
        "--------------",
    ]

    for label, (text, filename) in samples.items():
        lines.append(f"{label}:")
        lines.append(json.dumps(canonicalize(text, filename, TODAY), indent=2))
        lines.append("")

    output = "\n".join(line for line in lines if line is not None)
    (evidence_dir / "test_results.txt").write_text(output, encoding="utf-8")
    print(output)
    return test_run.returncode


if __name__ == "__main__":
    raise SystemExit(main())

