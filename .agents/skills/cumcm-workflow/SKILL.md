---
name: cumcm-workflow
description: Build or resume a contest-ready CUMCM project from official files through modeling, one selected computation backend, bounded independent validation, fresh-context paper writing, and final delivery. Use for real CUMCM work; do not use for ordinary paper polishing or unsupported one-shot answers.
---

# CUMCM Workflow

Keep the claims that matter traceable to official sources and to real execution, without turning every draft into an audit package.

Two rules shape everything below:

1. **Tooling records machine facts; you write judgement.** Never type a hash, a page count, an exit code, a source snapshot, or a result value. `record_run.py`, `index_result.py`, `record_compile.py` and `refresh_evidence.py` observe those. You write problem facts, the model, claims, and the paper.
2. **The model is chosen late, and the choice is earned.** Working mode accepts a draft model contract. You name candidate models, say what evidence would tell them apart, evaluate them with cheap exploratory runs, and only then select one and freeze the contract.

## Start or resume

1. Locate `.cumcm/state.json`. Resume an exact `0.6.0` project. Older workspaces are not supported; start a new project from the official files.
2. If no state exists and the user supplies official files, read [01-intake.md](references/01-intake.md), choose a safe target, and run `scripts/init_project.py` for them. Do not make the user assemble the command.
3. Read only the active stage guide plus [handoffs.md](references/handoffs.md) when crossing stages. A fresh task reads its handoff first, not the whole workspace.
4. Keep the six responsibilities distinct: orchestrator, modeling, computation, validation, paper, delivery. Do not simulate separation by inventing many small Skills.

## The two knobs

`mode` (in state) decides what must be complete. `--gate-mode` decides whether human gates count.

- `working`: fast modeling, exploratory computation, debugging. Official-input protection, real execution, exact result locators and non-fabrication are enforced. A draft model contract is enough; `CROSS_QUESTION_LEDGER.json` is optional; stage ordering is advisory. `enforce` here reports `working_ready`, never a formal approval.
- `finalizing`: freeze claim-bearing results. The model contract must be complete and its verification plan must map to assertions an official run recorded. Requires current stage decisions and snapshots, fresh handoffs, bounded independent review, paper/PDF QA and delivery binding. `enforce` cannot pass unless every stage through the requested one is `passed` with a current accepted decision.

Switch with `scripts/set_mode.py`. There is no `strict`/`sprint` profile in v0.6; a single rule set applies.

## Where a person is asked

Three checkpoints, one per block, and each records what was put in front of the person, not only what they decided. A decision with nothing presented is not evidence that anyone looked. They sit in front of the three cost steps: rejecting a model choice costs a conversation, rejecting a conclusion costs a recomputation, rejecting a finished paper costs a rewrite.

- **`MODEL_CONTRACT.selection_check`**, before a candidate becomes `selected`: the judgement criterion, each candidate's `discriminating_evidence`, and the `scope` the winner will claim. `presented_candidate_ids` must cover every candidate (`MODEL-E018`) — showing only the winner is not a comparison.
- **`CLAIM_LEDGER.conclusion_check`**, before `validation-paper`: the conclusions themselves — claim text, `scope`, evidence state, open P0/P1. No run ids, no hashes. `presented_claim_ids` must cover every declared claim (`CLAIM-E023`). This is the cheap place to hear no; the same objection at delivery costs a rewritten paper.
- **`DELIVERY_MANIFEST.final_check`**, before submission: the finished object — rendered pages, the answer to each subproblem, open findings. `presented_pages` must cover every rendered page (`DELIVERY-E020`), and `human_user` is not claimable with nothing presented (`DELIVERY-E019`).

The paper report carries no approvals of its own: `content_report` and `layout_report` are reports. Reviewer selection is recorded, not confirmed — separation comes from the two cut transitions instead (`references/handoffs.md`).

Stage statuses are `not_started`, `in_progress`, `passed`, `needs_revision`.

## Roles and handoffs

| Responsibility | Main reference | Outgoing handoff |
|---|---|---|
| Modeling | [02-problem-analysis.md](references/02-problem-analysis.md), [03-model-design.md](references/03-model-design.md) | `modeling-computation` |
| Computation | [04-computation.md](references/04-computation.md) | `computation-validation` |
| Validation | [05-validation.md](references/05-validation.md) | `validation-paper` |
| Paper | [06-paper-writing.md](references/06-paper-writing.md), [latex-template.md](references/latex-template.md) | `paper-delivery` |
| Delivery | [07-compile-delivery.md](references/07-compile-delivery.md) | final package |

Build handoffs with `scripts/build_handoff.py`. They carry canonical paths, a compact downstream payload, and an upstream digest. Never copy full logs, failed runs, debug history, or old review conversations. A stale digest requires rebuilding.

## Choosing the model

Model design does not pick a model. It proposes candidates and says how the choice will be settled:

```json
"candidates": [
  {"candidate_id": "CAND-ENUM", "method": "complete enumeration",
   "why_considered": "the declared policy class is finite and small",
   "discriminating_evidence": ["whether the greedy pick equals the enumerated minimum"],
   "status": "under_evaluation"},
  {"candidate_id": "CAND-GREEDY", "method": "greedy first-fit",
   "why_considered": "constant time, adequate if the set is already ordered by cost",
   "discriminating_evidence": ["whether the greedy pick equals the enumerated minimum"],
   "status": "under_evaluation"}
]
```

Then settle it with evidence rather than with an opinion:

```bash
python3 scripts/record_run.py --project <p> --candidate CAND-ENUM   -- python3 code/enum.py
python3 scripts/record_run.py --project <p> --candidate CAND-GREEDY -- python3 code/greedy.py
```

Set the winner to `status: "selected"`, the others to `"rejected"`, give each a `decision_rationale` that refers to what those runs showed, and list the runs in `evaluation_run_ids`. Only then does the selected model get an official run.

The checker holds you to it: exactly one candidate may end up `selected` (`MODEL-E013`), a selection must cite a run that evaluated it (`MODEL-W014`), a selected or rejected candidate needs a recorded reason (`MODEL-E014`), and a candidate with nothing to tell it apart is flagged (`MODEL-W012`). In `working` these are warnings; freezing turns them into errors. `cumcm_check.py` prints the comparison under `model_candidates`.

Two things this deliberately does not do: it does not require more than one candidate when one is obviously right (that is `MODEL-W007`, a warning), and it does not judge which candidate is better — it only insists that the choice was made against recorded evidence.

## Recording computation

```bash
# exploration costs nothing to record
python3 scripts/record_run.py --project <p> -- python3 code/try.py

# freezing a run for formal results costs a few declarations
python3 scripts/record_run.py --project <p> --official \
  --capability CAP-Q1-001 --source code/solve.py \
  --input data/q1.csv:formal --output results/q1.json:claim \
  --assert "feasibility=pass" -- python3 code/solve.py

# the value is read out of the output, never transcribed
python3 scripts/index_result.py --project <p> --result-id RES-Q1-001 \
  --run RUN-Q1-001 --locator results/q1.json#/minimum_cost \
  --name "Minimum cost" --unit CNY --scope "declared candidates only"

# a rerun appends a successor; the parent and its evidence stay untouched
python3 scripts/record_run.py --project <p> --rerun RUN-Q1-001 --official
python3 scripts/index_result.py --project <p> --follow-lineage
```

Exploratory runs are recorded, never trusted, and never block: a failed assertion or a non-zero exit inside one is a fact about the experiment, not about the formal chain. Only a successful `official_run: true` run may support a formal result.

Runs are append-only. `--rerun` appends `RUN-Q1-002` with `parent_run_id: RUN-Q1-001`; it never overwrites, because the parent is the only record of what the superseded run executed and produced. Each run freezes its declared source and outputs into `runs/<id>/source/…` and `runs/<id>/outputs/…`, mirroring the original layout, and hashes those copies — so a preserved run stays verifiable however the workspace changes, and `output_locator` names an immutable file.

A run may only claim what it produced and what it verified: the recorder compares every declared output's timestamp across the execution and refuses to record a leftover file as this run's claim-bearing evidence, and a rerun never inherits its parent's assertion verdicts. Only a successful official rerun supersedes its parent, and every formal consumer resolves the current run through the same code.

That does not weaken drift detection, it sharpens it. `RUN-E020` now compares the frozen copy with the live file and says the working tree has moved on from the run backing your results; superseded runs are exempt, and altering a frozen copy is `RUN-E021`. Supersession is derived from the parent chain and never written back — stamping the old manifest would change its hash and stale every decision bound to it. `RESULT-E017` catches a result still citing a superseded run; `index_result.py --follow-lineage` re-points it, explicitly, because which run backs a claim is judgement rather than a machine fact.

## Choosing one backend

Project state defaults to `{"preferred":"matlab","fallback":"python","selection":"auto"}`. Use `scripts/backend_selection.py` or the same criteria: numerical methods, optimization, ODE/PDE, signal processing, data cleaning, Excel/CSV, machine learning, available toolboxes, existing code, complexity, runtime stability. MATLAB preference breaks ties only. An unavailable preferred backend may fall back; an unavailable task `required_backend` must fail. Implement and officially run one language. Do not build parity implementations unless the user asks.

## Evidence gates

- hard invariant / `P0`: wrong data or computation, task mismatch, a claim whose declared scope exceeds the range actually verified, code/result/paper disagreement, an assumption contradicting a stated condition, stale provenance, fabricated approval or review, simulated data presented as observed, final-version mismatch. These block.
- warning / `P1`, judged inside the verified range: strong assumptions, weak baseline, thinner validation or sensitivity than ideal, limited fit, thin section. Visible, never blocking.
- suggestion / `P2`: wording, layout, optional chart, extra experiment. Not in the gate.

Independent validation uses `accepted`, `accepted_with_concerns`, `revision_required`, `inconclusive`. Only an open P0 permits `revision_required`. After a full review finds P0 issues, the next package defaults to a targeted re-review of exactly those findings.

The review package copies only canonical evidence for formally indexed results and records `context_excluded` — the prior reasoning it physically left out. It does not claim the reviewer holds no opinion. The result template leaves every independence field `null`: the reviewer must assert them, and a null fails `IREVIEW-E027`. The user no longer confirms the reviewer; separation comes from the cut instead — `computation-validation` and `validation-paper` carry the task that built them, and a consuming task that matches is `HANDOFF-E010`. See `references/handoffs.md`.

## Iterating

Reopening an upstream stage is one command, not a hand-edit of `state.json`:

```bash
python3 scripts/record_decision.py --project <p> --stage model-design \
  --decision revision_requested --decision-id DEC-007 --reviewer <name> \
  --task-turn-ref <ref> --summary "Q2 model does not fit the observed regime"
```

That invalidates the stage and everything downstream. To find out what a change actually costs before you redo anything:

```bash
python3 scripts/plan_redo.py --project <p> --changed code/solve_q2.py
```

`plan_redo.py` walks `source -> official run -> result -> claim -> section -> PDF` and names the specific runs, findings and sections that are affected — and the ones that are not. It never suppresses a check; `cumcm_check.py` still validates everything through the requested stage, because that is cheap. The expensive work is re-running, re-reviewing and re-writing, and that is what the plan scopes.

## Contest invariants

- Preserve and byte-identify official sources. OCR routes attention; rendered pages decide formulas, tables and ambiguous notation.
- Never invent observed data, approvals, independent review, or successful execution. Label genuine simulations and record their generator and seed.
- Keep the mathematical model and result contracts language-neutral.
- Use SHA-256 only for evidence-critical identity: official sources, formal inputs, claim-bearing outputs, compact snapshots/handoffs, review packages, selected source trees, and the reviewed final PDF.
- Keep internal IDs, evidence states, local paths, run coverage and workflow language out of the visible paper.
- Paper handoff limitations come only from supported paper-eligible claim limitations, current P1 concerns, and explicit applicability/assumption/known-limitation fields — not contradicted claims or model scope.
- Bind the final PDF to its reviewed bytes and to the exact editable LaTeX source snapshot used for compilation.
- Missing current official rules or templates blocks delivery; it does not authorize autonomous search or submission.
- Final delivery contains the reviewed PDF, editable LaTeX, and computation source as separate roles.

Read [artifact-contracts.md](references/artifact-contracts.md) when creating machine-readable files and [evidence-rules.md](references/evidence-rules.md) before model selection, review, or paper claims.

## Validate

```bash
python3 scripts/cumcm_check.py --project <project> --stage <stage> --gate-mode enforce
```

Record a decision only after showing the exact artifact and receiving the decision:

```bash
python3 scripts/record_decision.py --project <project> --stage <stage> \
  --decision accepted --decision-id <id> --reviewer <name> \
  --task-turn-ref <ref> --summary <visible-summary>
```

Passing establishes current structure, provenance, successful execution and recorded review boundaries. It does not prove mathematical correctness or global optimality.
