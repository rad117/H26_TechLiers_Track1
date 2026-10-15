"""Gemma 4 analysis: risk explanation, replacement, migration steps and code edits.

Owner: Sohan. Output shape: AIResult in team/CONTRACT.md. Never raise on model/JSON errors:
return {"source": "gemma", "ok": False, "error": ..., "raw": ...} instead.
Model id comes from $env:GEMMA_MODEL, the API key from $env:GEMINI_API_KEY (both may also be
set in a gitignored .env file at the project root).

WHAT GEMMA IS TRUSTED FOR: suggesting a replacement, the requirement changes, the edited files and
a prediction. All of that is AI-suggested. Nothing here is believed until runner.py has installed
the change and run the real tests; compare.py then grades the prediction ("Gemma vs Reality").
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path

from .deps import normalise, parse_requirement

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_TYPES = {"bump", "swap", "remove"}
REQUIREMENT_ACTIONS = {"set", "remove", "add"}

_client = None  # one long-lived client; a temporary one gets closed while still in use


def load_env():
    """Copy KEY=VALUE lines from .env into os.environ (real environment variables win)."""
    path = PROJECT_ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def model_name():
    load_env()
    return os.environ.get("GEMMA_MODEL", "<set GEMMA_MODEL>")


def get_client():
    global _client
    if _client is None:
        from google import genai
        from google.genai import types

        load_env()
        _client = genai.Client(http_options=types.HttpOptions(timeout=180_000))  # milliseconds
    return _client


# ---------- prompt ----------

INSTRUCTIONS = """You are helping a maintainer migrate away from a risky Python dependency.
Below are VERIFIED FACTS about one dependency of the project (JSON), plus the full text of the
project's dependency files and of every source file that uses it. Python 3.12 is used. The project's
tests are run with `pip install -r requirements.txt pytest` followed by `pytest`.

Reply with ONLY one JSON object (no markdown fences, no commentary) with exactly these keys:
{
  "risk_explanation": "2-4 sentences: why this dependency is risky, based on the facts",
  "replacement": "what to use instead, e.g. 'Jinja2>=3.1' or 'platformdirs (stdlib alternative: ...)'",
  "migration_type": "bump" | "swap" | "remove",
  "requirement_changes": [{"action": "set" | "remove" | "add", "name": "<package>", "line": "<requirements.txt line>"}],
  "file_edits": [{"path": "<repo-relative path>", "new_content": "<the COMPLETE new text of the file>"}],
  "steps": ["human-readable migration step", "..."],
  "suggested_tests": ["a test worth adding or running", "..."],
  "predicted_outcome": "pass" | "fail",
  "confidence": 0.0-1.0
}

Rules:
- bump: only the version changes. Use requirement_changes, and leave file_edits empty unless the new
  version needs code changes.
- swap: a different library. Remove the old requirement, add the new one, and give file_edits with the
  COMPLETE new content of every file that must change. Only edit files shown below.
- remove: the dependency is unused or replaceable by the standard library. Remove the requirement and
  edit files if needed.
- "set" replaces the requirements.txt line of an existing package, "add" appends a line, "remove"
  deletes the package's line. "line" is needed for set and add.
- Keep the program's behaviour identical. Prefer the smallest change that works. Do not touch tests.
- predicted_outcome: "pass" if, after your change, the dependencies install cleanly AND no test that passes
  today starts failing. Tests that already fail today (see the facts) do not count against you.
  "fail" if you expect the install to break or any currently passing test to break. Be honest.
"""


def read_text(repo, rel):
    try:
        return (Path(repo) / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def build_prompt(record, repo):
    files = sorted({u["file"] for u in record["usages"]})
    parts = []  # the repo files Gemma is shown
    for name in ("requirements.txt", "pyproject.toml"):
        text = read_text(repo, name)
        if text is not None:
            parts.append(f"## {name}\n```\n{text}\n```")
    for rel in files:
        text = read_text(repo, rel)
        if text is not None:
            parts.append(f"## {rel}\n```python\n{text}\n```")
    facts = "## Verified facts (JSON)\n" + json.dumps(record, indent=2)
    inputs = record["name"] + "\n\n" + "\n\n".join(parts)  # what the cache key depends on
    return "\n\n".join([INSTRUCTIONS, facts, *parts]), files, inputs


def prompt_key(prompt_inputs):
    """Fingerprint of what Gemma is asked: the instructions plus the files it is shown.
    Cached answers are reused only when this matches, so changing the prompt invalidates them."""
    return hashlib.sha256((INSTRUCTIONS + prompt_inputs).encode("utf-8")).hexdigest()[:16]


# ---------- parsing and validation ----------

def extract_json(text):
    """Pull the JSON object out of a model reply, tolerating ```json fences and chatter."""
    text = re.sub(r"```(?:json)?", "", text or "")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in the reply")
    return json.loads(text[start:end + 1])


def clean(data, allowed_files, current_lines=frozenset()):
    """Check types and drop anything unsafe or malformed. Raise ValueError if unusable."""
    if data.get("migration_type") not in MIGRATION_TYPES:
        raise ValueError("migration_type must be bump, swap or remove")
    changes = []
    for item in data.get("requirement_changes") or []:
        if not isinstance(item, dict) or item.get("action") not in REQUIREMENT_ACTIONS or not item.get("name"):
            continue
        action, name, line = item["action"], str(item["name"]), str(item.get("line", "")).strip()
        if action != "remove":
            parsed = parse_requirement(line)  # must be a plain requirements.txt line for this package
            if not parsed or normalise(parsed[0]) != normalise(name) or line in current_lines:
                continue  # malformed, wrong package, or identical to what is already there
        changes.append({"action": action, "name": name, "line": line})
    edits = []
    for item in data.get("file_edits") or []:
        path = str(item.get("path", "")).replace("\\", "/") if isinstance(item, dict) else ""
        # Only files that Gemma was shown may be rewritten (blocks "../" and invented paths).
        if path in allowed_files and isinstance(item.get("new_content"), str) and item["new_content"].strip():
            edits.append({"path": path, "new_content": item["new_content"]})
    if not changes and not edits:
        raise ValueError("it proposed no effective change (requirement lines identical to the current "
                         "ones, or malformed); give real requirements.txt lines such as 'Jinja2>=3.1,<4'")
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
    except (TypeError, ValueError):
        confidence = 0.5
    as_list = lambda v: [str(x) for x in v] if isinstance(v, list) else []  # noqa: E731
    return {
        "risk_explanation": str(data.get("risk_explanation", "")),
        "replacement": str(data.get("replacement", "")),
        "migration_type": data["migration_type"],
        "requirement_changes": changes,
        "file_edits": edits,
        "steps": as_list(data.get("steps")),
        "suggested_tests": as_list(data.get("suggested_tests")),
        "predicted_outcome": "pass" if str(data.get("predicted_outcome")).lower() == "pass" else "fail",
        "confidence": confidence,
    }


# ---------- the public function ----------

def failure(error, raw=""):
    return {"source": "gemma", "model": model_name(), "ok": False, "error": str(error), "raw": raw}


def candidate_models():
    """The configured model first, then a fallback (the hosted 31B model often answers 500/503)."""
    load_env()
    fallback = os.environ.get("GEMMA_FALLBACK_MODEL", "gemma-4-26b-a4b-it")
    return [m for m in dict.fromkeys([model_name(), fallback]) if not m.startswith("<")]


def ask(prompt):
    """Return (reply text, model that answered). Retry transient server errors, then fall back."""
    import httpx
    from google.genai import errors

    last = None
    for model in candidate_models():
        for attempt in range(1):
            try:
                # No generation config: gemma-4-31b-it returned HTTP 500 whenever `temperature` was set.
                reply = get_client().models.generate_content(model=model, contents=prompt)
                return reply.text or "", model
            except (errors.ServerError, httpx.TransportError) as exc:  # 500/503 or timeout: next model
                last = exc
            except errors.ClientError as exc:
                if exc.code != 429:  # bad key / bad request: another attempt won't help
                    raise
                last = exc
                time.sleep(10)
    raise last


def analyze(record, repo, out):
    """Ask Gemma about one at-risk DepRecord. Cache the answer in out/ai/<name>.json."""
    prompt, shown_files, inputs = build_prompt(record, repo)
    key = prompt_key(inputs)
    ai_dir = Path(out) / "ai"
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", record["name"])
    cache = ai_dir / f"{safe}.json"
    if cache.exists():
        try:
            cached = json.loads(cache.read_text(encoding="utf-8"))
            if (cached.get("ok") and cached.get("model") in candidate_models()
                    and cached.get("prompt_key") == key):
                return cached
        except ValueError:
            pass  # unreadable cache: ask again

    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / f"{safe}.prompt.txt").write_text(prompt, encoding="utf-8")  # evidence trail

    req_text = read_text(repo, "requirements.txt") or ""
    current_lines = {line.strip() for line in req_text.splitlines()}
    raw, result = "", None
    try:
        for attempt in range(2):  # one retry if the reply isn't usable
            raw, used = ask(prompt if attempt == 0 else
                            prompt + "\n\nYour previous reply was rejected: "
                            f"{error}. Reply again with ONLY the corrected JSON object.")
            try:
                result = {"source": "gemma", "model": used, "ok": True, "prompt_key": key,
                          **clean(extract_json(raw), set(shown_files), current_lines), "raw": raw}
                break
            except ValueError as exc:  # also covers json.JSONDecodeError
                error = exc
        if result is None:
            return failure(f"unusable reply: {error}", raw)
    except Exception as exc:  # network, quota, auth: never crash the pipeline
        return failure(f"{type(exc).__name__}: {str(exc)[:300]}", raw)

    cache.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    import sys

    from . import deps, pypi, scan

    target, package = Path(sys.argv[1]), sys.argv[2]
    found = pypi.enrich_and_score(scan.attach_usages(deps.collect(target), target))
    rec = next(r for r in found if r["name"].lower() == package.lower())
    answer = analyze(rec, target, Path(sys.argv[3] if len(sys.argv) > 3 else "capsule_dev"))
    answer.pop("raw", None)
    print(json.dumps(answer, indent=2))
