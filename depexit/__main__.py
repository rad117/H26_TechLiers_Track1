"""depexit CLI: python -m depexit analyze <repo-url-or-path> --out capsule_out

Owner: Sohan. Runs every stage in the order described in team/CONTRACT.md.
"""
import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, capsule, compare, deps, gemma, pypi, runner, scan


def log(msg):
    print(f"[depexit {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_repo(target, work):
    """Clone a URL (or copy a local folder) into work/target and return that path."""
    dest = work / "target"
    if dest.exists():
        shutil.rmtree(dest)
    if target.startswith(("http://", "https://", "git@")):
        subprocess.run(["git", "clone", "--depth", "1", "-q", target, str(dest)], check=True)
    else:
        shutil.copytree(target, dest, ignore=shutil.ignore_patterns(
            ".git", ".venv", "venv", "__pycache__", "capsule_out", "depexit", "team"))
    return dest


def git_commit(repo):
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def analyze(args):
    out = Path(args.out).resolve()
    work = out / "_work"
    work.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    log(f"getting target repo: {args.target}")
    repo = get_repo(args.target, work)

    baseline = None
    if not args.no_tests:
        log("running baseline tests on the ORIGINAL dependencies")
        baseline = runner.run_tests(repo, "baseline", work)
        log(f"baseline: stage={baseline['stage']} passed={baseline.get('passed')} failed={baseline.get('failed')}")

    log("collecting declared dependencies")
    records = deps.collect(repo)
    log("scanning imports")
    records = scan.attach_usages(records, repo, baseline["venv_python"] if baseline else None)
    log("fetching PyPI metadata and scoring")
    records = pypi.enrich_and_score(records, baseline)

    at_risk = [r for r in records if r.get("at_risk")]
    if args.only:
        wanted = {n.lower() for n in args.only}
        at_risk = [r for r in at_risk if r["name"].lower() in wanted]
    at_risk.sort(key=lambda r: r.get("health_score", 100))
    if args.max_deps:
        at_risk = at_risk[: args.max_deps]
    log(f"{len(at_risk)} at-risk dependencies: {', '.join(r['name'] for r in at_risk)}")

    results = []
    for record in at_risk:
        name = record["name"]
        result = {"dep": record, "ai": None, "patch": "", "run": None, "comparison": None}
        if not args.no_ai:
            log(f"[{name}] asking Gemma")
            result["ai"] = gemma.analyze(record, repo, out)
        if baseline and result["ai"] and result["ai"].get("ok"):
            log(f"[{name}] applying migration in a copy and running tests")
            candidate, result["patch"] = runner.apply_migration(repo, record, result["ai"], work)
            result["run"] = runner.run_tests(candidate, name, work)
            result["comparison"] = compare.compare(baseline, result["run"], result["ai"])
            log(f"[{name}] verdict={result['comparison']['verdict']}")
        results.append(result)

    card = compare.scorecard(results)
    meta = {
        "tool": "depexit", "version": __version__,
        "target": args.target, "target_commit": git_commit(repo),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host_python": platform.python_version(),
        "model": gemma.model_name() if not args.no_ai else None,
        "duration_s": round(time.monotonic() - started, 1),
    }
    log("writing capsule")
    paths = capsule.write_all(out, meta, records, results, baseline, card)
    log(f"done in {meta['duration_s']} s -> {paths.get('report') or out}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="depexit", description="Dependency Exit Capsule generator (Gemma 4)")
    parser.add_argument("--version", action="version", version=f"depexit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("analyze", help="analyse a repository and write a Dependency Exit Capsule")
    a.add_argument("target", help="git URL or local folder of the repository to analyse")
    a.add_argument("--out", default="capsule_out", help="output folder (default: capsule_out)")
    a.add_argument("--only", nargs="*", metavar="PKG", help="only migrate these dependencies")
    a.add_argument("--max-deps", type=int, help="migrate at most N riskiest dependencies")
    a.add_argument("--no-ai", action="store_true", help="skip Gemma (facts only)")
    a.add_argument("--no-tests", action="store_true", help="skip creating venvs and running tests")
    args = parser.parse_args(argv)
    if args.command == "analyze":
        analyze(args)


if __name__ == "__main__":
    sys.exit(main())
