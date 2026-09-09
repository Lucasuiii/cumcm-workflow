#!/usr/bin/env python3
"""Answer the only question that matters after a change: what must be redone?

The expensive work in a contest is re-running computation, re-doing an independent
review and re-writing paper sections -- not re-reading JSON. So this walks the
existing ID graph

    official source -> fact -> capability -> model
    source file     -> official run -> result -> claim -> paper section -> PDF

backwards from the changed files and names the specific runs, findings and
sections that are actually affected. It never suppresses a check; cumcm_check.py
still validates everything.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

STAGE_ORDER = ["intake", "problem-analysis", "model-design", "computation", "validation", "paper", "delivery"]


def read(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def live_path_of(frozen: str) -> str | None:
    """runs/<id>/source/code/solve.py -> code/solve.py (None if not a frozen path)."""
    parts = frozen.split("/")
    if len(parts) > 3 and parts[0] == "runs" and parts[2] in {"source", "outputs", "inputs"}:
        return "/".join(parts[3:])
    return None


def build_plan(root: Path, changed: list[str]) -> dict[str, Any]:
    root = root.resolve()
    changed_set = {path.strip() for path in changed if path.strip()}
    sources = read(root, "problem/SOURCE_MANIFEST.json")
    facts = read(root, "analysis/PROBLEM_FACTS.json")
    results_index = read(root, "results/RESULTS_INDEX.json")
    claims = read(root, "validation/CLAIM_LEDGER.json")
    review = read(root, "validation/INDEPENDENT_REVIEW_RESULT.json")
    plan = read(root, "paper/PAPER_PLAN.json")
    latex = read(root, "paper/LATEX_TEMPLATE_MANIFEST.json")
    receipt = read(root, "delivery/COMPILE_RECEIPT.json")

    actions: dict[str, list[str]] = {stage: [] for stage in STAGE_ORDER}
    unaffected: dict[str, list[str]] = {stage: [] for stage in STAGE_ORDER}

    # --- official sources -------------------------------------------------
    touched_sources = [
        str(item.get("source_id"))
        for item in as_list(sources.get("sources"))
        if isinstance(item, dict) and str(item.get("path")) in changed_set
    ]
    if touched_sources:
        actions["intake"].append(f"re-verify official inventory for {', '.join(sorted(touched_sources))}")
        dependent_facts = [
            str(item.get("fact_id") or item.get("id"))
            for item in as_list(facts.get("facts"))
            if isinstance(item, dict) and str(item.get("source_id")) in set(touched_sources)
        ]
        if dependent_facts:
            actions["problem-analysis"].append(f"re-extract facts: {', '.join(sorted(dependent_facts))}")

    # --- runs whose recorded source tree or formal inputs moved -----------
    stale_runs: set[str] = set()
    official_runs: dict[str, dict[str, Any]] = {}
    manifests: list[dict[str, Any]] = []
    for manifest_path in sorted((root / "runs").glob("*/RUN_MANIFEST.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(manifest, dict):
            manifests.append(manifest)
    # A superseded run is history. Never propose re-running it.
    superseded = {
        str(m.get("parent_run_id")) for m in manifests
        if str(m.get("parent_run_id", "")).strip() and str(m.get("parent_run_id")) != str(m.get("run_id"))
        and m.get("official_run") is True and m.get("status") == "completed" and m.get("exit_code") == 0
    }
    for manifest in manifests:
        if manifest.get("official_run") is not True or str(manifest.get("run_id")) in superseded:
            continue
        run_id = str(manifest.get("run_id"))
        official_runs[run_id] = manifest
        snapshot = manifest.get("implementation", {}).get("source_snapshot", {})
        # Source is frozen inside the run directory, so watch the live counterpart:
        # runs/<id>/source/code/solve.py is evidence for code/solve.py.
        watched = set()
        for value in as_list(snapshot.get("files")):
            watched.add(str(value))
            live = live_path_of(str(value))
            if live:
                watched.add(live)
        for entry in as_list(manifest.get("inputs")):
            if not isinstance(entry, dict) or entry.get("evidence_role") != "formal_input":
                continue
            watched.add(str(entry.get("path")))
            live = live_path_of(str(entry.get("path")))
            if live:
                watched.add(live)
        if watched & changed_set:
            stale_runs.add(run_id)
    # Propagate along declared output -> formal input edges, including frozen
    # copies. A historical input requires an explicit binding decision, not a
    # blind rerun with the old arguments.
    def aliases(path: str) -> set[str]:
        result = {path}
        while live := live_path_of(path):
            result.add(live)
            path = live
        return result

    inputs = {
        rid: set().union(*(aliases(str(e.get("path"))) for e in as_list(m.get("inputs"))
                          if isinstance(e, dict) and e.get("evidence_role") == "formal_input"), set())
        for rid, m in official_runs.items()
    }
    outputs = {
        rid: set().union(*(aliases(str(e.get("path"))) for e in as_list(m.get("outputs"))
                          if isinstance(e, dict)), set())
        for rid, m in official_runs.items()
    }
    dependent_runs: set[str] = set()
    while True:
        affected_outputs = set().union(*(outputs[rid] for rid in stale_runs), set())
        newly_stale = {rid for rid in official_runs if rid not in stale_runs and inputs[rid] & affected_outputs}
        if not newly_stale:
            break
        dependent_runs.update(newly_stale)
        stale_runs.update(newly_stale)
    for run_id in sorted(dependent_runs):
        actions["computation"].append(
            f"refresh input bindings for {run_id} after upstream successors exist; "
            "review intentional historical inputs and do not blindly reuse frozen parent inputs"
        )
    for run_id in sorted(stale_runs):
        actions["computation"].append(f"re-run {run_id}: record_run.py --rerun {run_id} --official (appends a successor)")
    for run_id in sorted(set(official_runs) - stale_runs):
        unaffected["computation"].append(run_id)

    # --- results, claims, sections ---------------------------------------
    stale_results = {
        str(item.get("result_id"))
        for item in as_list(results_index.get("results"))
        if isinstance(item, dict) and str(item.get("run_id")) in stale_runs
    }
    if stale_results:
        actions["computation"].append(
            f"re-point results to the successor: index_result.py --follow-lineage ({', '.join(sorted(stale_results))})"
        )

    stale_claims: set[str] = set()
    for claim in as_list(claims.get("claims")):
        if not isinstance(claim, dict):
            continue
        evidence = claim.get("evidence") if isinstance(claim.get("evidence"), dict) else {}
        touched = {str(value) for value in as_list(evidence.get("result_ids"))} & stale_results
        touched |= {str(value) for value in as_list(evidence.get("run_ids"))} & stale_runs
        if touched:
            stale_claims.add(str(claim.get("claim_id")))
    if stale_claims:
        actions["validation"].append(f"re-establish evidence for claims: {', '.join(sorted(stale_claims))}")

    findings = [item for item in as_list(review.get("findings")) if isinstance(item, dict)]
    targeted = sorted(
        str(item.get("finding_id"))
        for item in findings
        if (stale_results | stale_runs | stale_claims)
        & {token.strip(" ,;()") for token in str(item.get("location", "")).replace("#", " ").split()}
    )
    if stale_runs or stale_claims:
        if targeted:
            actions["validation"].append(f"targeted re-review covers: {', '.join(targeted)}")
        actions["validation"].append("rebuild the package: build_independent_review_package.py --review-mode auto --refresh")
        untouched = sorted({str(item.get("finding_id")) for item in findings} - set(targeted))
        if untouched:
            unaffected["validation"].extend(untouched)

    section_files: dict[str, set[str]] = {}
    for item in as_list(latex.get("subproblem_sections")):
        if isinstance(item, dict):
            section_files.setdefault(str(item.get("subproblem_id")), set()).add(str(item.get("path")))
    stale_sections: set[str] = set()
    for section in as_list(plan.get("paper_structure")):
        if not isinstance(section, dict):
            continue
        if {str(value) for value in as_list(section.get("claim_ids"))} & stale_claims:
            for subproblem in as_list(section.get("subproblem_ids")):
                if str(subproblem) in section_files:
                    stale_sections.update(section_files[str(subproblem)])
    changed_tex = sorted(path for path in changed_set if path.endswith((".tex", ".bib")))
    for path in changed_tex:
        stale_sections.add(path)
    if stale_sections:
        actions["paper"].append(f"rewrite or re-review: {', '.join(sorted(stale_sections))}")
    untouched_sections = sorted(set().union(*section_files.values(), set()) - stale_sections)
    if untouched_sections:
        unaffected["paper"].extend(untouched_sections)

    compile_inputs = set(as_list(receipt.get("source_snapshot", {}).get("files")))
    if stale_sections or stale_runs or changed_tex or compile_inputs & changed_set:
        actions["delivery"].append("recompile and rebind: record_compile.py --update-quality")
        if receipt:
            actions["delivery"].append("the previous PDF/source binding is void until the recompile succeeds")

    return {
        "changed_paths": sorted(changed_set),
        "stale_official_runs": sorted(stale_runs),
        "stale_results": sorted(stale_results),
        "stale_claims": sorted(stale_claims),
        "stale_sections": sorted(stale_sections),
        "actions": {stage: actions[stage] for stage in STAGE_ORDER if actions[stage]},
        "unaffected": {stage: sorted(set(unaffected[stage])) for stage in STAGE_ORDER if unaffected[stage]},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="List the work a change actually invalidates")
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--changed", action="append", default=[], required=True, help="project-relative changed path; repeat as needed")
    parser.add_argument("--json", action="store_true", help="print the machine-readable plan only")
    args = parser.parse_args()
    root = args.project.resolve()
    if not root.is_dir():
        parser.error(f"project is not a directory: {root}")
    plan = build_plan(root, args.changed)
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    print("changed: " + ", ".join(plan["changed_paths"]))
    if not plan["actions"]:
        print("nothing downstream is invalidated by these paths")
    for stage, items in plan["actions"].items():
        print(f"\n{stage}")
        for item in items:
            print(f"  - {item}")
    if plan["unaffected"]:
        print("\nnot affected (do not redo):")
        for stage, items in plan["unaffected"].items():
            print(f"  {stage}: {', '.join(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
