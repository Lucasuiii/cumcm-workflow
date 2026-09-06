from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "skills" / "cumcm-workflow" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_workflow_core import build_valid_project, envelope, review, write_json  # noqa: E402
from init_latex_paper import initialize as initialize_latex  # noqa: E402
from build_handoff import build as build_handoff  # noqa: E402
from provenance import digest_records, tree_snapshot  # noqa: E402
from workflow_checks import check_project, sha256, stage_scope_paths  # noqa: E402


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_decisions(root: Path, stages: tuple[str, ...]) -> None:
    events = []
    for index, stage in enumerate(stages, 1):
        scope = [{"path": rel, "sha256": sha256(root / rel)} for rel in stage_scope_paths(root, stage)]
        event = {
            "decision_id": f"DEC-{index:03d}", "stage": stage, "decision": "accepted", "scope": scope,
            "reviewer": "fixture-reviewer", "task_turn_ref": f"fixture-turn-{index}",
            "user_visible_summary": f"Accepted fixture stage {stage}", "decided_at": "2026-08-30T12:00:00Z",
        }
        events.append(event)
        snapshot = {
            "snapshot_version": "0.6.0", "project_id": "SYNTHETIC-2024-B", "stage": stage,
            "decision_id": event["decision_id"], "decision": "accepted", "created_at": event["decided_at"],
            "artifacts": scope, "snapshot_digest": digest_records(scope),
        }
        write_json(root, f".cumcm/snapshots/{stage}.json", snapshot)
    decision_path = root / ".cumcm" / "decisions.jsonl"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text("".join(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n" for event in events), encoding="utf-8")


def build_paper_ready_project(root: Path, *, decisions: tuple[str, ...] | None = None) -> None:
    build_valid_project(root)
    paper_path = root / "paper" / "paper.pdf"
    paper_artifact = {"path": "paper/paper.pdf", "sha256": digest_file(paper_path)}

    included_layer = {
        "status": "included",
        "summary": "The paper records this part of the argument chain.",
        "evidence_ids": ["CLM-Q1-001"],
        "rationale": None,
    }
    plan = envelope("paper_plan")
    plan.update(
        {
            "authoring_task_ref": "fixture-paper-task",
            "claim_selection": [
                {"claim_id": "CLM-Q1-001", "subproblem_id": "Q1", "purpose": "answer Q1 directly"}
            ],
            "representation_plan": [
                {"item_id": "REP-Q1-001", "claim_ids": ["CLM-Q1-001"], "result_ids": ["RES-Q1-001"], "medium": "figure", "purpose": "show the restricted-policy comparison", "artifact_id": "FIG-Q1-001"}
            ],
            "paper_structure": [
                {"section_id": "SEC-Q1", "title": "Q1 solution", "purpose": "complete Q1 reasoning", "subproblem_ids": ["Q1"], "claim_ids": ["CLM-Q1-001"]}
            ],
            "reference_reviews": [
                {
                    "reference_id": "REF-001",
                    "source": "reviewed high-quality contest paper",
                    "quality_reasons": ["complete derivation and verification chain"],
                    "transferable_lessons": ["connect each conclusion to evidence"],
                    "non_transferable_limits": ["different problem and data"],
                }
            ],
            "reader_narrative": {
                "one_sentence_contribution": "The paper solves the declared restricted policy problem and explains the scope.",
                "judge_reading_path": ["problem", "mechanism", "model", "result", "meaning", "validation", "boundary"],
                "internal_metadata_policy": "sidecar_only",
            },
            "claims_evidence_matrix": [
                {
                    "claim_id": "CLM-Q1-001",
                    "subproblem_id": "Q1",
                    "planned_sections": ["Results"],
                    "evidence_ids": ["RES-Q1-001", "FIG-Q1-001"],
                    "status": "included",
                }
            ],
            "question_argument_chains": [
                {
                    "subproblem_id": "Q1",
                    "layers": {
                        name: dict(included_layer)
                        for name in (
                            "problem_interpretation",
                            "assumptions_boundaries",
                            "variables_parameters",
                            "objective_constraints",
                            "derivation",
                            "algorithm",
                            "results",
                            "validation",
                            "limitations",
                        )
                    },
                }
            ],
            "figure_plan": [
                {
                    "figure_id": "FIG-Q1-001",
                    "kind": "quantitative",
                    "purpose": "Explain the restricted-policy comparison.",
                    "claim_ids": ["CLM-Q1-001"],
                    "result_ids": ["RES-Q1-001"],
                    "required": True,
                    "decision_support": "Makes the policy comparison inspectable.",
                }
            ],
            "page_budget": [
                {"section": "Q1", "purpose": "Complete argument", "target_pages": 1.0}
            ],
        }
    )
    write_json(root, "paper/PAPER_PLAN.json", plan)

    initialize_latex(root, "Synthetic CUMCM Paper", 2026, "synthetic; evidence")
    for source in (root / "paper").rglob("*.tex"):
        text = source.read_text(encoding="utf-8")
        text = text.replace("CUMCM-TODO", "已完成").replace("\\placeholder{", "\\textbf{")
        source.write_text(text, encoding="utf-8")
    manifest_path = root / "paper" / "LATEX_TEMPLATE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["official_compliance"] = "verified_against_current_rules"
    manifest["official_template_source"] = "fixture://current-rules"
    manifest["review"] = review()
    write_json(root, "paper/LATEX_TEMPLATE_MANIFEST.json", manifest)

    dimension = {"status": "pass", "notes": "Checked against linked evidence.", "evidence_ids": ["CLM-Q1-001"]}
    quality = envelope("paper_quality_report")
    quality.update(
        {
            "paper_status": "final",
            "paper_artifact": paper_artifact,
            "content_review": {
                "decision": "accepted",
                "reviewer": "fixture-reviewer",
                "reviewed_at": "2026-08-30T12:00:00Z",
                "reviewer_kind": "external_reviewer",
                "artifact": paper_artifact,
                "summary": "Content is coherent and evidence-bounded.",
                "abstract_synthesis": dict(dimension),
                "conclusion_directness": dict(dimension),
                "internal_metadata_separation": dict(dimension),
                "reference_style_transfer": dict(dimension),
                "questions": [
                    {
                        "subproblem_id": "Q1",
                        "status": "pass",
                        "notes": "Q1 directly answers the task and explains the result.",
                        "argument_chain": dict(dimension),
                        "mechanism_explanation": dict(dimension),
                        "derivation": dict(dimension),
                        "result_interpretation": dict(dimension),
                        "reader_facing_language": dict(dimension),
                        "numerical_presentation": dict(dimension),
                        "validation_strength": dict(dimension),
                        "limitations": dict(dimension),
                    }
                ],
            },
            "layout_review": {
                "decision": "accepted",
                "reviewer": "fixture-reviewer",
                "reviewed_at": "2026-08-30T12:00:00Z",
                "reviewer_kind": "human_user",
                "artifact": paper_artifact,
                "page_count": 1,
                "rendered_pages": [1],
                "checks": [
                    {"check_id": "LAYOUT-001", "category": "cross_page", "status": "pass", "notes": "All rendered pages inspected."}
                ],
            },
            "final_qa": {
                "decision": "accepted",
                "reviewer": "fixture-reviewer",
                "reviewed_at": "2026-08-30T12:00:00Z",
                "reviewer_kind": "human_user",
                "artifact": paper_artifact,
                "notes": "Final bytes match the reviewed artifact.",
            },
            "open_issues": [],
        }
    )
    write_json(root, "paper/PAPER_QUALITY_REPORT.json", quality)

    revisions = envelope("paper_revision_log")
    revisions.update({"initial_snapshot": paper_artifact, "revisions": []})
    write_json(root, "paper/PAPER_REVISION_LOG.json", revisions)

    visible_text = envelope("paper_visible_text_report")
    visible_text.update(
        {
            "paper_artifact": paper_artifact,
            "status": "pass",
            "blocking_matches": [],
            "review_flags": [],
        }
    )
    write_json(root, "paper/PAPER_VISIBLE_TEXT_REPORT.json", visible_text)

    receipt = envelope("compile_receipt")
    receipt.update(
        {
            "source_snapshot": tree_snapshot(
                root,
                json.loads((root / "paper" / "LATEX_TEMPLATE_MANIFEST.json").read_text(encoding="utf-8"))["required_files"],
                entrypoint="paper/main.tex",
            ),
            "selected_attempt_id": "COMPILE-001",
            "attempts": [
                {
                    "attempt_id": "COMPILE-001",
                    "argv": ["xelatex", "paper.tex"],
                    "engine": "XeLaTeX",
                    "engine_version": "synthetic",
                    "exit_code": 0,
                    "log_path": "paper/compile.log",
                    "warnings": [],
                    "page_count": 1,
                    "pdf_path": "paper/paper.pdf",
                    "pdf_sha256": paper_artifact["sha256"],
                    "font_check": "pass",
                    "glyph_check": "pass",
                    "diagnostic_summary": "Synthetic compile succeeded.",
                    "completed_at": "2026-08-30T12:00:00Z",
                }
            ],
            "layout_review_binding": {
                "quality_report_path": "paper/PAPER_QUALITY_REPORT.json",
                "pdf_sha256": paper_artifact["sha256"],
            },
        }
    )
    write_json(root, "delivery/COMPILE_RECEIPT.json", receipt)
    delivery_path = root / "delivery" / "DELIVERY_MANIFEST.json"
    delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
    delivery["compile_receipt_path"] = "delivery/COMPILE_RECEIPT.json"
    write_json(root, "delivery/DELIVERY_MANIFEST.json", delivery)

    state_path = root / ".cumcm" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["mode"] = "finalizing"
    state["current_stage"] = "delivery"
    state["stages"] = {stage: "passed" for stage in (
        "intake", "problem-analysis", "model-design", "computation", "validation", "paper", "delivery"
    )}
    write_json(root, ".cumcm/state.json", state)

    # Distinct refs on the two cut transitions: the reviewer is not the task that
    # produced the evidence, and the paper is not written by the task that reviewed it.
    producing_task_refs = {
        "computation-validation": "fixture-modeling-task",
        "validation-paper": "fixture-independent-task",
    }
    for transition in ("modeling-computation", "computation-validation", "validation-paper", "paper-delivery"):
        build_handoff(root, transition, producing_task_refs.get(transition))

    record_decisions(
        root,
        decisions
        if decisions is not None
        else ("intake", "problem-analysis", "model-design", "computation", "validation", "paper", "delivery"),
    )


def set_state(root: Path, current: str, paper_status: str, delivery_status: str) -> None:
    path = root / ".cumcm" / "state.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["current_stage"] = current
    data["stages"]["paper"] = paper_status
    data["stages"]["delivery"] = delivery_status
    write_json(root, ".cumcm/state.json", data)


class PaperPipelineTests(unittest.TestCase):
    def test_complete_paper_ready_project_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            findings, summary = check_project(root, "delivery")
            self.assertEqual([item for item in findings if item.severity == "error"], [])
            self.assertEqual(summary["workflow_version"], "0.6.0")
            self.assertEqual(summary["gate_status"], "passed")

    def test_no_planned_visual_is_warning_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            path = root / "paper" / "PAPER_PLAN.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["representation_plan"] = []
            write_json(root, "paper/PAPER_PLAN.json", data)
            state = json.loads((root / ".cumcm/state.json").read_text(encoding="utf-8"))
            state["mode"] = "working"
            write_json(root, ".cumcm/state.json", state)
            findings, _ = check_project(root, "paper")
            warning = next(item for item in findings if item.rule_id == "PPLAN-W001")
            self.assertEqual(warning.severity, "warning")
            self.assertEqual([item for item in findings if item.severity == "error"], [])

    def test_representation_plan_requires_known_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            path = root / "paper" / "PAPER_PLAN.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["representation_plan"][0]["result_ids"] = ["RES-UNKNOWN"]
            write_json(root, "paper/PAPER_PLAN.json", data)
            findings, _ = check_project(root, "paper")
            self.assertIn("PPLAN-E014", {item.rule_id for item in findings})

    def test_review_only_failure_is_preflight_zero_and_enforce_nonzero(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root, decisions=("intake", "problem-analysis", "model-design", "computation", "validation"))
            set_state(root, "paper", "in_progress", "not_started")
            path = root / "paper" / "PAPER_QUALITY_REPORT.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["content_review"]["decision"] = "unreviewed"
            write_json(root, "paper/PAPER_QUALITY_REPORT.json", data)
            preflight_findings, preflight = check_project(root, "paper", "preflight")
            _, enforce = check_project(root, "paper", "enforce")
            self.assertIn("PQUALITY-E010", {item.rule_id for item in preflight_findings})
            self.assertEqual(preflight["blocking_error_count"], 0)
            self.assertEqual(preflight["gate_status"], "awaiting_review")
            self.assertGreater(enforce["blocking_error_count"], 0)
            preflight_cli = subprocess.run(
                [sys.executable, str(SCRIPTS / "cumcm_check.py"), "--project", str(root), "--stage", "paper", "--gate-mode", "preflight", "--no-write-report"],
                check=False,
                capture_output=True,
                text=True,
            )
            enforce_cli = subprocess.run(
                [sys.executable, str(SCRIPTS / "cumcm_check.py"), "--project", str(root), "--stage", "paper", "--gate-mode", "enforce", "--no-write-report"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(preflight_cli.returncode, 0, preflight_cli.stdout + preflight_cli.stderr)
            self.assertEqual(enforce_cli.returncode, 1)

    def test_strict_layout_review_must_cover_all_pages(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            path = root / "paper" / "PAPER_QUALITY_REPORT.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["layout_review"]["page_count"] = 2
            write_json(root, "paper/PAPER_QUALITY_REPORT.json", data)
            findings, _ = check_project(root, "paper")
            self.assertIn("PQUALITY-E008", {item.rule_id for item in findings})

    def test_final_paper_cannot_have_open_p0_issue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            path = root / "paper" / "PAPER_QUALITY_REPORT.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["open_issues"] = [{"issue_id": "ISSUE-001", "severity": "P0", "category": "content", "status": "open", "description": "Missing derivation", "location": "Q1", "resolution": None, "verified_by": None}]
            write_json(root, "paper/PAPER_QUALITY_REPORT.json", data)
            findings, _ = check_project(root, "paper")
            self.assertIn("PQUALITY-E011", {item.rule_id for item in findings})

    def test_revision_snapshot_hash_drift_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            path = root / "paper" / "PAPER_REVISION_LOG.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["initial_snapshot"]["sha256"] = "0" * 64
            write_json(root, "paper/PAPER_REVISION_LOG.json", data)
            findings, _ = check_project(root, "paper")
            self.assertIn("PREVISION-E003", {item.rule_id for item in findings})

    def test_closed_issue_requires_verified_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            path = root / "paper" / "PAPER_QUALITY_REPORT.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["open_issues"] = [{"issue_id": "ISSUE-001", "severity": "P1", "category": "content", "status": "closed", "description": "Clarify result scope", "location": "Q1", "resolution": "Edited prose", "verified_by": "fixture-reviewer"}]
            write_json(root, "paper/PAPER_QUALITY_REPORT.json", data)
            findings, _ = check_project(root, "paper")
            self.assertIn("PREVISION-E005", {item.rule_id for item in findings})

    def test_compile_receipt_page_count_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            path = root / "delivery" / "COMPILE_RECEIPT.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["attempts"][0]["page_count"] = 2
            write_json(root, "delivery/COMPILE_RECEIPT.json", data)
            findings, _ = check_project(root, "delivery")
            self.assertIn("COMPILE-E010", {item.rule_id for item in findings})

    def test_decision_log_does_not_add_event_hash_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            path = root / ".cumcm" / "decisions.jsonl"
            lines = path.read_text(encoding="utf-8").splitlines()
            events = [json.loads(line) for line in lines]
            self.assertTrue(events)
            self.assertTrue(all("event_hash" not in event and "previous_event_hash" not in event for event in events))

    def test_stale_decision_scope_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            path = root / "paper" / "PAPER_PLAN.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["updated_at"] = "2026-08-30T13:00:00Z"
            write_json(root, "paper/PAPER_PLAN.json", data)
            findings, _ = check_project(root, "paper")
            self.assertIn("DECISION-E010", {item.rule_id for item in findings})

    def test_record_decision_rejects_duplicate_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "record_decision.py"),
                    "--project",
                    str(root),
                    "--stage",
                    "delivery",
                    "--decision",
                    "accepted",
                    "--decision-id",
                    "DEC-007",
                    "--reviewer",
                    "fixture-reviewer",
                    "--task-turn-ref",
                    "duplicate-test",
                    "--summary",
                    "Must not append.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("already exists", completed.stderr)

    def test_missing_stage_decision_is_review_only_in_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root, decisions=("intake", "problem-analysis", "model-design", "computation", "validation"))
            set_state(root, "paper", "passed", "not_started")
            findings, summary = check_project(root, "paper", "preflight")
            self.assertIn("DECISION-E008", {item.rule_id for item in findings})
            self.assertEqual(summary["gate_status"], "awaiting_review")
            self.assertEqual(summary["blocking_error_count"], 0)

    def test_skill_and_docs_use_python3_entrypoint(self):
        targets = [
            ROOT / ".agents" / "skills" / "cumcm-workflow" / "SKILL.md",
            ROOT / "README.md",
        ]
        for path in targets:
            self.assertNotIn("python scripts/cumcm_check.py", path.read_text(encoding="utf-8"))


class TaskSeparationTests(unittest.TestCase):
    """The two cut transitions must be crossed in a fresh task.

    The refs are self-reported, so these checks are a paste guard, not proof. What they
    catch is the case the workflow actually cares about: one task producing the evidence
    and also reviewing it, or one task reviewing the work and also writing it up.
    """

    HANDOFFS = {
        "computation-validation": "handoffs/computation-validation/HANDOFF.json",
        "validation-paper": "handoffs/validation-paper/HANDOFF.json",
    }

    def set_producing_ref(self, root: Path, transition: str, value: object) -> None:
        rel = self.HANDOFFS[transition]
        data = json.loads((root / rel).read_text(encoding="utf-8"))
        data["producing_task_ref"] = value
        write_json(root, rel, data)

    def test_reviewer_running_in_the_producing_task_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            self.assertNotIn("HANDOFF-E010", {item.rule_id for item in check_project(root, "delivery")[0]})
            result = json.loads((root / "validation" / "INDEPENDENT_REVIEW_RESULT.json").read_text(encoding="utf-8"))
            collision = result["reviewer_context"]["task_ref"]
            self.set_producing_ref(root, "computation-validation", collision)
            findings, _ = check_project(root, "delivery")
            hit = [item for item in findings if item.rule_id == "HANDOFF-E010"]
            self.assertEqual(len(hit), 1)
            self.assertEqual(hit[0].severity, "error")
            self.assertIn(collision, hit[0].message)

    def test_paper_written_in_the_reviewing_task_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            plan = json.loads((root / "paper" / "PAPER_PLAN.json").read_text(encoding="utf-8"))
            self.set_producing_ref(root, "validation-paper", plan["authoring_task_ref"])
            findings, _ = check_project(root, "delivery")
            hit = [item for item in findings if item.rule_id == "HANDOFF-E010"]
            self.assertEqual(len(hit), 1)
            self.assertEqual(hit[0].owning_stage, "paper")

    def test_a_handoff_without_a_producing_ref_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            self.set_producing_ref(root, "computation-validation", None)
            hit = [item for item in check_project(root, "delivery")[0] if item.rule_id == "HANDOFF-E009"]
            self.assertEqual([item.severity for item in hit], ["error"])
            self.assertIn("--task-ref", hit[0].message)

    def test_review_package_no_longer_waits_on_a_user_confirmation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_paper_ready_project(root)
            rel = "validation/independent-review-package/REVIEW_PACKAGE_MANIFEST.json"
            package = json.loads((root / rel).read_text(encoding="utf-8"))
            self.assertEqual(package["reviewer_selection"]["status"], "recorded")
            self.assertNotIn("selected_by", package["reviewer_selection"])
            result = json.loads((root / "validation" / "INDEPENDENT_REVIEW_RESULT.json").read_text(encoding="utf-8"))
            self.assertNotIn("selected_by_user", result["reviewer_context"])
            findings, summary = check_project(root, "delivery", "enforce")
            codes = {item.rule_id for item in findings}
            self.assertNotIn("IREVIEW-E005", codes)
            self.assertNotIn("IREVIEW-E008", codes)
            self.assertEqual(summary["blocking_error_count"], 0)


if __name__ == "__main__":
    unittest.main()
