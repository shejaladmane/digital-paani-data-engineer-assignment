# ADR — Legacy survey ingestion decisions

## Status
Accepted for the take-home implementation.

## Context
The source consists of heterogeneous Excel worksheets with different header offsets, inconsistent human-entered representations, repeated identifiers, and prose validation rules. The target is the canonical survey field schema used by the digital application / MongoDB path.

## Decision 1 — Explicit sheet contracts rather than automatic header discovery
I use a small configuration table containing each sheet's header row and column range. This is intentionally explicit because Appendix A supplies those positions and the source format is small and known. Automatic header discovery would add complexity and risk incorrectly interpreting human commentary as data.

Rejected alternative: infer tables by searching for likely column names. That would be more flexible but is unnecessary for five known layouts and harder to reason about in a five-hour exercise.

## Decision 2 — Merge plant data by Plant ID; match process_design by normalized client name
Four sheets carry a plant identifier, so Plant ID is the join key there. `process_design` does not carry the plant code, so I match its client name using a conservative normalization and a guarded fuzzy fallback. Name differences are still surfaced as warnings rather than hidden.

Rejected alternative: join process_design by row number. Row position appears aligned in the supplied data, but relying on it would silently associate the wrong tank if someone inserted or sorted a row.

## Decision 3 — Site-characteristics location wins when the two location fields disagree
The site-characteristics worksheet explicitly states that its location was re-recorded from the site because the design sheet was filled from drawings. I therefore use the site value as canonical while emitting a cross-sheet disagreement warning.

Rejected alternative: always use plant_design. That would ignore the source-specific provenance note.

## Decision 4 — Retain questionable records with validation flags
I chose a "write with a flag" policy. Parseable values are kept, and records with rule failures are marked `needs_review`; the issue contains the field, rule and raw value when useful. Nothing is silently discarded.

This is preferable here to rejecting entire plant records because a single suspicious value should not make the rest of an expensive site survey disappear. It also preserves potentially genuine outliers such as high borewell TDS while making them reviewable.

Rejected alternatives:
- Reject the whole record: too destructive.
- Null every invalid value: loses potentially real measurements.
- Write without flags: hides known data-quality risk downstream.

## Decision 5 — Deterministic IDs and upsert for re-runs
Plants use the supplied plant ID as `_id`. Collection tanks use `<plant_id>:COLLECTION`. MongoDB writes are `replace_one(..., upsert=True)`.

This makes the batch idempotent: the same input can be run repeatedly, including after a partial failure, without creating duplicates.

Rejected alternative: insert-only writes with generated ObjectIds. They would duplicate records on the second run and complicate partial-failure recovery.

## Decision 6 — Normalize representation, but do not invent information
Examples include converting `61%` to `0.61`, numeric strings such as `300 KLD` to numbers, and `Y/FALSE/no` to the supplied `Yes`/`No` representation. These conversions are surfaced as data-quality warnings when the source type was inconsistent.

For fields that cannot be represented faithfully — for example half-hour peak-flow ranges when the target type stores integer-hour pairs — the canonical field is left null and the raw value is surfaced in a warning rather than rounded silently.

One explicit assumption is `MF -> MEDIA_FILTRATION`; it is flagged for domain confirmation because the abbreviation is potentially ambiguous.
