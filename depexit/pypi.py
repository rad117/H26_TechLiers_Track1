"""PyPI metadata, risk signals and the 0-100 health score.

Owner: Sohan. Fills `pypi`, `signals`, `health_score`, `at_risk` on each DepRecord.
Every signal must come from something observed (PyPI JSON, the code, or the baseline TestRun).
"""


def enrich_and_score(records, baseline=None):
    """Return records with pypi info, signals, health_score and at_risk (health_score < 70)."""
    raise NotImplementedError("Sohan: see team/SOHAN.md, task 3")
