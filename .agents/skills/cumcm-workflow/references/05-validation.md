# Validation responsibility

## First review: full and context-separated

Build the current computation handoff, then run:

```bash
python3 scripts/build_independent_review_package.py --project <project>
```

The package binds only canonical evidence for formal results: official inputs, problem/model contracts, `RESULTS_INDEX.json`, cited successful `official_run: true` manifests, matching source snapshots, formal inputs, claim-bearing outputs, and review instructions. It records `context_excluded` — the prior reasoning it physically left out — rather than asserting that the reviewer holds no conclusions. Failed/exploratory runs, stdout/stderr, full logs, and debug history are excluded; package/upstream freshness digests cover this same canonical set. Stop and let the user route it to a separate task or human. Record both originating and reviewer task references; they must differ. The result template ships with every independence field `null`, so the reviewer or the user has to assert them; a null fails `IREVIEW-E027`. Differing task references are a paste guard, not proof of independence. Same-model fresh-context review remains correlated. Task references and user confirmation improve context-separation evidence but cannot cryptographically prove reviewer independence.

## Findings and verdicts

The P0/P1 boundary is not severity, it is kind. P0 findings are consistency failures: the work claims more than it verified, or two records of the same thing disagree. They can be settled by reading, without the reviewer's taste. P1 findings are judgements made inside the range the work actually verified. A finding that could be resolved by narrowing a scope statement is P0, not P1.

- `P0`
  - wrong data or computation
  - task mismatch: the answer does not address what was asked
  - **declared scope exceeds verified range**: a rule, threshold, strategy, selected model, or fitted relation checked only at the point where it was derived — one parameter set, a boundary value, in sample — while its `scope` claims a range. Two ways out, both acceptable: verify across the claimed range, or narrow the scope to what was verified.
  - disagreement between code, model, results, and paper, including a paper that contradicts its own tables or figures
  - an assumption that contradicts a condition the problem states
  - serious provenance failure
- `P1`, all inside the verified range: model choice, strength of assumptions, weak baseline, thinner validation or sensitivity than ideal, limited fit.
- `P2`: optional presentation or additional experiment suggestion.

For a claim that prescribes an action — a decision rule, a threshold, a selected strategy — verifying the range means reporting how it behaves away from the nominal point, not only that it is optimal at it. A rule that is correct at the design point and inert everywhere else is a P0 finding, not a presentation concern.

Verdicts are `accepted`, `accepted_with_concerns`, `revision_required`, and `inconclusive`. Only an open P0 permits `revision_required`. Open P1/P2 items remain visible as warnings or suggestions and do not block paper work.

After a full review returns open P0 findings, rerunning the package builder in auto mode defaults to a targeted re-review. It archives the prior review/package and targets every prior open P0. The new package embeds `TARGETED_FINDINGS.json` with only `finding_id`, `category`, `location`, `evidence`, and `recommendation`, so a fresh reviewer can work from the package alone without receiving the full old review. Do not turn unrelated newly noticed P1/P2 items into new blockers. A genuinely new P0 may still require revision.

## Claims

Create `CLAIM_LEDGER.json` from the reviewed evidence. Each paper-bearing claim records its exact text, scope, evidence IDs, evidence state, and limitations. Strong claims—global optimality, equivalence, causality, robustness, significance, or reproducibility—still need claim-specific support. `reproduced` requires an isolated rerun and comparison; an original successful run is only `supported_not_reproduced` unless stronger evidence exists.

Before paper writing, build `validation-paper`. For a targeted result, the builder follows only the structured `previous_review_path` lineage and applies the latest status per finding ID: open/accepted P1 concerns remain, while resolved findings drop out. Its limitations come from supported paper-eligible claim limitations, those current P1 concerns, and explicit model applicability, assumptions, and known limitations—not contradicted/unsupported claims or model `scope`. Its `representation_candidates` proactively identify trend, multi-group comparison, distribution, sensitivity, model-performance, and spatial/network/clustering evidence. A fresh paper task reads this compact handoff first, chooses prose/equation/table/figure, and does not scan full run/debug history.
