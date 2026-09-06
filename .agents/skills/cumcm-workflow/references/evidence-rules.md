# Evidence rules

## Three levels

- Hard invariant / P0: affects truth, provenance, reproducibility, task coverage, or final submission identity. Block it.
- Warning / P1: affects model strength or reader confidence inside the range the claim actually covers, and does not show the result is false. Keep it visible. A claim that reaches past what was verified is not P1; that is a consistency failure and belongs in P0.
- Suggestion / P2: optional expression, layout, or extra analysis. Do not gate on it.

File existence proves existence. Schema validity proves structure. Successful execution proves a process ran. None proves that the model matches the task. Exact locators and hashes establish identity, not mathematical correctness.

Claims of global optimality, equivalence, causality, significance, robustness, or reproducibility require claim-specific evidence and scope. A solver success flag, non-rejection, or original run is insufficient by itself.

## Change impact

The deterministic check is cheap, so it always runs in full through the requested stage. What is expensive is re-running computation, re-doing an independent review and re-writing paper sections, and that is what gets scoped:

```bash
python3 scripts/plan_redo.py --project <p> --changed code/solve_q2.py
```

It walks `official source -> fact -> capability` and `source file -> official run -> result -> claim -> section -> PDF` and names the runs, findings and sections a change actually invalidates — plus the ones it does not, so you do not redo them. v0.5's `cosmetic/local/semantic/claim_changing/global` labels are gone; they classified a judgement instead of following the evidence graph.
