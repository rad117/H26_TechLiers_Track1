"""Write the Dependency Exit Capsule: summary.json, per-dependency capsule.json/.md, patch.diff,
report.html (Blast Radius) and replay.ps1.

Owner: Radhesh. Develop against team/sample_data/results.sample.json (DEV ONLY, never ship it as output):
    python -m depexit.capsule team/sample_data/results.sample.json capsule_dev
"""
import json
import sys
from pathlib import Path


def write_all(out, meta, records, results, baseline, card):
    """Write every capsule file into out/. Return {"report": path_to_report_html, ...}."""
    raise NotImplementedError("Radhesh: see team/RADHESH.md, tasks 1-3")


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(write_all(Path(sys.argv[2] if len(sys.argv) > 2 else "capsule_dev"),
                    data["meta"], data["records"], data["results"], data["baseline"], data["scorecard"]))
