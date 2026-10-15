"""PyPI metadata, risk signals and the 0-100 health score.

Owner: Sohan. Fills `pypi`, `signals`, `health_score`, `at_risk` on each DepRecord.
Every signal must come from something observed (PyPI JSON, the code, or the baseline TestRun).

HOW THE SCORE WORKS
    health_score = clamp(100 + sum(points of all signals), 0, 100)
    at_risk      = health_score < 70

    id                   points  fires when                                           source
    fails_in_baseline      -30   a failing baseline test's error names this package    baseline_tests
                                 (or one of its dependencies, from PyPI metadata)
    major_behind           -25   pinned major version < latest major version           pypi
    old_pin                -20   the pinned release is older than 3 years              pypi
    inactive               -20   no release for 2+ years, or an "Inactive" classifier  pypi
    deprecation_warning    -15   a baseline pytest warning mentions this package        baseline_tests
    spec_mismatch          -15   requirements.txt and pyproject.toml disagree          repo_files
    private_api            -10   code imports a _private name from it                  code_scan
    undeclared / unused    -10   imported but not declared / declared but never used   code_scan
    unpinned                -5   no version constraint in any file                     repo_files

A signal is only added when its evidence exists, so a failed PyPI lookup or a skipped
baseline run (--no-tests) simply produces fewer signals; nothing is guessed.
"""
import re
from datetime import date, datetime, timezone

import requests

PYPI_URL = "https://pypi.org/pypi/{}/json"
PYPI_VERSION_URL = "https://pypi.org/pypi/{}/{}/json"
AT_RISK_BELOW = 70
OLD_PIN_DAYS = 3 * 365
INACTIVE_DAYS = 2 * 365

_cache = {}  # url -> parsed JSON, or None if the lookup failed


def get_json(url):
    if url not in _cache:
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "depexit/0.1"})
            resp.raise_for_status()
            _cache[url] = resp.json()
        except (requests.RequestException, ValueError):
            _cache[url] = None
    return _cache[url]


def parse_date(upload_time):
    return datetime.strptime(upload_time[:10], "%Y-%m-%d").date() if upload_time else None


def major(version):
    match = re.match(r"\d+", version or "")
    return int(match.group()) if match else None


def release_date(files):
    """Upload date of a release = its earliest file."""
    dates = [parse_date(f.get("upload_time")) for f in files or []]
    dates = [d for d in dates if d]
    return min(dates) if dates else None


def fetch_pypi(record, today):
    """Return the `pypi` block for one record (or {"error": ...} if PyPI can't be reached)."""
    data = get_json(PYPI_URL.format(record["name"]))
    if not data:
        return {"error": "PyPI lookup failed"}
    info = data["info"]
    releases = data.get("releases", {})
    latest = info["version"]
    latest_date = release_date(releases.get(latest))
    pinned = record.get("pinned_version")
    pinned_date = release_date(releases.get(pinned)) if pinned else None
    inactive = any("Inactive" in c for c in info.get("classifiers", [])) or \
        bool(latest_date and (today - latest_date).days > INACTIVE_DAYS)
    return {
        "latest": latest,
        "latest_date": latest_date.isoformat() if latest_date else None,
        "pinned_date": pinned_date.isoformat() if pinned_date else None,
        "inactive": inactive,
        "requires_python": info.get("requires_python"),
    }


def names_of(record):
    """Words that identify this package in an error message or warning."""
    return {record["name"].lower(), *(n.lower() for n in record["import_names"])}


def mentions(text, names):
    return any(re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w])", text, re.I) for n in names)


def dependency_names(record):
    """Packages that the pinned version depends on (PyPI requires_dist, extras ignored)."""
    if not record.get("pinned_version"):
        return set()
    data = get_json(PYPI_VERSION_URL.format(record["name"], record["pinned_version"]))
    requires = (data or {}).get("info", {}).get("requires_dist") or []
    return {re.match(r"[A-Za-z0-9._-]+", r).group().lower() for r in requires if "extra ==" not in r}


def signal(id, detail, points, source):
    return {"id": id, "detail": detail, "points": points, "source": source}


def baseline_signals(record, baseline):
    out = []
    if not baseline:
        return out
    names = names_of(record)
    failures = baseline.get("failing_tests") or {}
    # A failing test blames this package if its error names it directly...
    hits = [msg for msg in failures.values() if mentions(msg, names)]
    if not hits and failures:
        # ...or names something it depends on (Jinja2 2.11.3 breaks on MarkupSafe).
        related = dependency_names(record)
        hits = [msg for msg in failures.values() if related and mentions(msg, related)]
    if hits:
        out.append(signal("fails_in_baseline", hits[0], -30, "baseline_tests"))
    for warning in baseline.get("warnings") or []:
        if mentions(warning, names):
            out.append(signal("deprecation_warning", warning, -15, "baseline_tests"))
            break
    return out


def score_signals(record, today, baseline):
    pypi = record["pypi"]
    sigs = baseline_signals(record, baseline)

    pinned, latest = record.get("pinned_version"), pypi.get("latest")
    if major(pinned) is not None and major(latest) is not None and major(pinned) < major(latest):
        sigs.append(signal("major_behind", f"pinned {pinned}, latest {latest}", -25, "pypi"))
    if pypi.get("pinned_date"):
        age = (today - date.fromisoformat(pypi["pinned_date"])).days
        if age > OLD_PIN_DAYS:
            sigs.append(signal("old_pin", f"{pinned} released {pypi['pinned_date']} ({age // 365} years ago)",
                               -20, "pypi"))
    if pypi.get("inactive"):
        sigs.append(signal("inactive", f"last release {pypi.get('latest_date')}, or marked Inactive",
                           -20, "pypi"))
    if record["spec_mismatch"]:
        detail = ", ".join(f"{f}: {s or 'any'}" for f, s in record["specs"].items())
        sigs.append(signal("spec_mismatch", detail, -15, "repo_files"))
    private = [u for u in record["usages"] if u["private"]]
    if private:
        sigs.append(signal("private_api", f"{private[0]['file']}:{private[0]['line']} {private[0]['code']}",
                           -10, "code_scan"))
    if record["status"] in ("undeclared", "unused"):
        detail = "imported but not declared anywhere" if record["status"] == "undeclared" \
            else "declared but never imported"
        sigs.append(signal(record["status"], detail, -10, "code_scan"))
    if record["specs"] and not any(record["specs"].values()):
        sigs.append(signal("unpinned", "no version constraint in any file", -5, "repo_files"))
    return sigs


def enrich_and_score(records, baseline=None):
    """Return records with pypi info, signals, health_score and at_risk (health_score < 70)."""
    today = datetime.now(timezone.utc).date()
    for record in records:
        record["pypi"] = fetch_pypi(record, today)
        record["signals"] = score_signals(record, today, baseline)
        score = 100 + sum(s["points"] for s in record["signals"])
        record["health_score"] = max(0, min(100, score))
        record["at_risk"] = record["health_score"] < AT_RISK_BELOW
    return records


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    from . import deps, scan

    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    baseline = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))["baseline"] if len(sys.argv) > 2 else None
    for r in enrich_and_score(scan.attach_usages(deps.collect(target), target), baseline):
        print(f"{r['name']:16} {r['health_score']:3} {'AT RISK' if r['at_risk'] else '       '} "
              f"{[s['id'] for s in r['signals']]}")
