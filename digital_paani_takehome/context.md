# AI working context

Task: build Part A of Digital Paani DP-DE-TH-01.

Requirements used:
- Read all supplied legacy Excel batches.
- Each workbook has five named worksheets with non-A1 header offsets.
- Normalize the heterogeneous layouts into canonical plant-baseline, water-balance and collection-tank fields.
- Apply the supplied field schema and prose validation rules.
- Do not silently discard invalid data.
- Write to local MongoDB.
- Make reruns safe / idempotent.
- Produce cleaned data artifacts, ADR, deployment notes and AI-assistant disclosure.
- Part B is not part of the pre-interview submission.

Implementation choices:
- Python + pandas + openpyxl + pymongo.
- Two MongoDB collections: plants and collection_tanks.
- Flag-and-retain invalid records.
- Deterministic IDs with replace/upsert.
- Site-characteristics location overrides plant_design when they conflict, with a warning.
- Numeric text is parsed but surfaced as a warning.
