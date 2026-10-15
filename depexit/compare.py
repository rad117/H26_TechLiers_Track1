"""Compare baseline vs candidate test runs, and grade Gemma's predictions ("Gemma vs Reality").

Owner: Sheersh. Output shapes: Comparison and Scorecard in team/CONTRACT.md.
"""


def compare(baseline, run, ai):
    """Return a Comparison dict for one dependency."""
    raise NotImplementedError("Sheersh: see team/SHEERSH.md, task 3")


def scorecard(results):
    """Return a Scorecard dict over all DepResults that have both an AI prediction and a test run."""
    raise NotImplementedError("Sheersh: see team/SHEERSH.md, task 4")
