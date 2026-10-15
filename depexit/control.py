"""Negative control: does our grader catch a migration that looks right but is wrong?

Owner: Radhesh. A perfect score ("Gemma was right about 7 of 7") only means something if the grader can also
say no. This feeds runner.py and compare.py a HUMAN-WRITTEN, DELIBERATELY WRONG migration (no AI involved) and
checks that it is caught:

    python -m depexit.control https://github.com/rishrek/LinkWatch --out control_output

The mistake is a realistic one: swap the abandoned `toml` package for the standard library's `tomllib`, but
open the file in text mode. tomllib needs binary mode ("rb"), so loading sites.toml raises a TypeError. It
installs fine and looks plausible in review; only running the tests reveals it.
"""
import argparse
import json
import shutil
from pathlib import Path

from . import compare, runner
from .__main__ import get_repo

BROKEN_CONFIG = '''from typing import List

import tomllib
from pydantic import BaseModel, validator


class Site(BaseModel):
    name: str
    url: str

    class Config:
        anystr_strip_whitespace = True

    @validator("name")
    def name_not_empty(cls, value):
        if not value:
            raise ValueError("site name can not be empty")
        return value

    @validator("url")
    def url_has_scheme(cls, value):
        if not value.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return value


class Settings(BaseModel):
    title: str = "linkwatch"
    output: str = "status.html"
    sites: List[Site] = []

    class Config:
        extra = "forbid"


def load_settings(path="sites.toml"):
    with open(path) as fh:  # THE DELIBERATE BUG: tomllib needs open(path, "rb")
        data = tomllib.load(fh)
    return Settings(**data)
'''

# Shaped like an AIResult so the real runner and grader treat it exactly as they treat Gemma's answers
CONTROL = {
    "source": "human-control", "model": "none (human-written, deliberately wrong)", "ok": True,
    "risk_explanation": "toml is unmaintained; Python 3.11+ ships tomllib.",
    "replacement": "tomllib (stdlib)", "migration_type": "remove",
    "requirement_changes": [{"action": "remove", "name": "toml"}],
    "file_edits": [{"path": "linkwatch/config.py", "new_content": BROKEN_CONFIG}],
    "steps": ["Remove toml from requirements.txt", "Load sites.toml with tomllib instead of toml"],
    "suggested_tests": [], "predicted_outcome": "pass", "confidence": 0.9,
}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="depexit.control", description=__doc__.splitlines()[0])
    parser.add_argument("target", help="git URL or folder of LinkWatch")
    parser.add_argument("--out", default="control_output")
    args = parser.parse_args(argv)

    out = Path(args.out).resolve()
    work = out / "_work"
    work.mkdir(parents=True, exist_ok=True)
    repo = get_repo(args.target, work)
    baseline = runner.run_tests(repo, "baseline", work)
    cand, patch = runner.apply_migration(repo, {"name": "toml-control"}, CONTROL, work)
    run = runner.run_tests(cand, "toml-control", work)
    result = compare.compare(baseline, run, CONTROL)

    (out / "patch.diff").write_bytes(patch.encode("utf-8"))
    (out / "logs").mkdir(exist_ok=True)
    for r in (baseline, run):
        shutil.copy(r["log_file"], out / "logs")
    (out / "control.json").write_text(json.dumps(
        {"control": CONTROL, "baseline": baseline, "run": run, "comparison": result}, indent=2), encoding="utf-8")

    caught = result["verdict"] == "regressed" and result["prediction_correct"] is False
    print(f"verdict={result['verdict']}  predicted={result['predicted_outcome']}  actual={result['actual_outcome']}")
    for gap in result["gaps"]:
        print(f"  gap: {gap}")
    print("CAUGHT: the grader rejected the wrong migration" if caught else "NOT CAUGHT: investigate!")
    return 0 if caught else 1


if __name__ == "__main__":
    raise SystemExit(main())
