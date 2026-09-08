# AI assistant disclosure

## Context file
See `context.md` at the repository root.

## Important prompts

1. "Read the take-home brief, schema and validation rules, then propose a focused Python batch pipeline that reads the five Excel layouts, maps them to the canonical fields, validates them and writes idempotently to local MongoDB."
   - Why it mattered: established the overall implementation shape and kept the work scoped to Part A.

2. "Inspect the supplied Excel layouts and build explicit mappings for the different header offsets and messy representations such as percentages, unit-bearing numbers, Yes/No variants, multi-selects and tank dimensions."
   - Why it mattered: focused the implementation on the actual source inconsistencies instead of a generic ETL example.

3. "Implement the prose domain checks, including peaking factor, collection-tank sizing, tank count versus arrangement, and reported volume versus dimensions, while retaining questionable observations with review flags."
   - Why it mattered: converted the most important domain rules into executable checks and made the invalid-data policy explicit.

## Example where the assistant was wrong / needed correction

The first proposed normalization could have treated all abbreviations as unambiguous. During review, `MF` was recognized as potentially ambiguous, so the final implementation makes the mapping assumption explicit and emits a warning for domain confirmation instead of silently treating it as certain.

If you personally observe a different AI error while finishing the assignment, replace this example with the real one. Do not claim an error you did not actually observe.
