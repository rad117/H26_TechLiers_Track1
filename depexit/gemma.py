"""Gemma 4 analysis: risk explanation, replacement, migration steps and code edits.

Owner: Sohan. Output shape: AIResult in team/CONTRACT.md. Never raise on model/JSON errors:
return {"source": "gemma", "ok": False, "error": ..., "raw": ...} instead.
Model id comes from $env:GEMMA_MODEL, the API key from $env:GEMINI_API_KEY.
"""
import os


def model_name():
    return os.environ.get("GEMMA_MODEL", "<set GEMMA_MODEL>")


def analyze(record, repo, out):
    """Ask Gemma about one at-risk DepRecord. Cache the answer in out/ai/<name>.json."""
    raise NotImplementedError("Sohan: see team/SOHAN.md, task 4")
