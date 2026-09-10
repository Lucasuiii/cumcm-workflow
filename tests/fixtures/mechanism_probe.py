"""Synthetic dry-run examples, not a general mathematical validator.

Each deliberately weak check passes a wrong answer. The discriminating check
uses the problem definition and the exported answer, with an explicit scope.
All numbers here define toy problems, not contest defaults or tolerances.
"""
import json
import sys
from pathlib import Path

mechanism, variant = sys.argv[1:]
if mechanism == "event":
    # Exact binary fractions: this polynomial's minimum occurs at its vertex.
    times = [0.0, 1.0] if variant != "good" else [0.0, 0.5, 1.0]
    gap = lambda t: (t - 0.5) ** 2
    candidates = [t for t in times if gap(t) <= 0]
    answer = {"first_contact": min(candidates) if candidates else None}
    discrete_only = variant == "not_applicable"
    expected = None if discrete_only else 0.5
    weak_pass = all(gap(t) >= 0 for t in (0, 1))
    details = {"scope": "observation times only" if discrete_only else "continuous closed interval",
               "reference_first_contact": expected}
elif mechanism == "rounding":
    # Units are indivisible only in the discrete variants; budget is 6/5.
    relaxation = [0.6, 0.6]
    values = [1, 0] if variant == "good" else [round(x) for x in relaxation]
    if variant == "not_applicable":
        values = relaxation
    answer = {"allocation": values}
    weak_pass = sum(relaxation) <= 1.2
    details = {"scope": "divisible" if variant == "not_applicable" else "integer allocation",
               "capacity": 1.2}
else:
    assert mechanism == "groups"
    rows = [{"row": i, "object": i // 2, "time": i % 2} for i in range(4)]
    train = rows[:2] if variant == "good" else rows[::2]
    test = rows[2:] if variant == "good" else rows[1::2]
    answer = {"train": train, "test": test}
    weak_pass = not ({r["row"] for r in train} & {r["row"] for r in test})
    details = {"scope": "future records of known objects" if variant == "not_applicable" else "unseen objects"}

# Replay the actual serialized deliverable, never the optimizer's internal state.
Path("results/answer.json").write_text(json.dumps(answer))
exported = json.loads(Path("results/answer.json").read_text())
if mechanism == "event":
    passed = exported["first_contact"] == expected
elif mechanism == "rounding":
    values = exported["allocation"]
    passed = all(x >= 0 for x in values) and sum(values) <= details["capacity"]
    if variant != "not_applicable":
        passed = passed and all(float(x).is_integer() for x in values)
    details["observed_load"] = sum(values)
else:
    train, test = exported["train"], exported["test"]
    overlap = {r["object"] for r in train} & {r["object"] for r in test}
    passed = not overlap
    if variant == "not_applicable":
        # Toy deployment explicitly observes an earlier record of each object.
        passed = all(any(a["object"] == b["object"] and a["time"] < b["time"]
                         for a in train) for b in test)
    details["shared_objects"] = sorted(overlap)
Path("results/diagnostics.json").write_text(json.dumps(details))
Path("results/assertions.json").write_text(json.dumps({"assertions": [
    {"name": "weak check", "passed": weak_pass},
    {"name": "answer matches scoped definition", "passed": passed},
]}))
