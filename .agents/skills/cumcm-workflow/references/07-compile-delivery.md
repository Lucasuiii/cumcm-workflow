# Delivery responsibility

Delivery is a `finalizing` responsibility. It uses only current user-supplied official rules/templates and the fresh `paper-delivery` handoff. That handoff must identify the reviewed PDF, the compile-bound editable LaTeX snapshot/entry point, every official computation source selected through `RESULTS_INDEX → successful official run → source snapshot`, and the official paper materials still requiring compliance review.

Produce the receipt with the recorder, not by hand:

```bash
python3 scripts/record_compile.py --project <p> --update-quality
```

## Hard checks

- the selected compile attempt exited successfully with the declared engine;
- font and missing-glyph checks pass (derived from the engine log, not asserted);
- the reviewed PDF path/hash, page count, layout report, compile receipt, and delivery manifest agree;
- the compile receipt contains a current `sha256-tree-v1` snapshot of every required editable LaTeX source file and its entry point;
- fonts/glyphs, overflow, clipping, unreadable figures/tables, and unresolved references are checked;
- current official-format compliance is verified from user-supplied material;
- final PDF, editable LaTeX source, and computation source are separately addressable and present.

The exact PDF hash and source-tree snapshot bind the final approved artifact to its editable source without requiring per-file hashes to be typed or reviewed manually. Ordinary logs, caches, temporary files, documentation, and debugging material stay outside the delivery package.

Missing current rules or a required template yields `blocked_missing_user_material`; it does not authorize web search. Submission remains user-controlled.

## The last checkpoint

`DELIVERY_MANIFEST.final_check` is the single approval before submission; the paper report carries none of its own. It replaced four separate ones, which in practice collapsed into a single typed sentence approving things nobody had looked at.

This one asks a narrower question than the conclusion check did. The model is settled by now: what is being judged is the finished object — whether the answers are stated correctly in the paper, whether the pages hold together, whether the deliverables are complete. Present the rendered pages `record_compile.py` wrote to `.cumcm/tmp/pages/`, the answer to each subproblem, the open findings, and anything still in `unresolved_errors`.

`presented_pages` records what was actually put in front of the reviewer. `DELIVERY-E020` rejects a check that skipped rendered pages, and `DELIVERY-E019` rejects `reviewer_kind: human_user` with nothing presented at all — if the pages were never shown, the record must not claim a person read them. A model that cannot see images has not done layout QA; say so in `notes` and record the kind honestly rather than upgrading a text transcription into a human reading.
