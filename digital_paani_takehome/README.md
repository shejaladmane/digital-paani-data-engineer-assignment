# Digital Paani – Data Engineer Take-Home Assignment

## Overview

This project implements Part A of the Digital Paani Data Engineer take-home assignment.

The pipeline ingests legacy Excel survey data, normalizes it into a canonical structure, performs data-quality and domain validation, generates JSON artifacts, and loads the processed records into MongoDB.

## Technologies

- Python
- Pandas / OpenPyXL
- MongoDB / PyMongo
- Pytest
- Docker / Docker Compose
- Git / GitHub
- AI-assisted development using ChatGPT

## Submission Contents

- `src/` – ingestion, normalization, pipeline and validation code
- `tests/` – automated tests
- `data/input/` – supplied Excel input files
- `data/reference/` – canonical fields and validation rules
- `output/` – generated JSON artifacts
  - `plants.json`
  - `collection_tanks.json`
  - `validation_issues.json`
- `docs/ADR.md` – architecture/design decisions
- `docs/DEPLOYMENT.md` – deployment notes
- `docs/AI_ASSISTANT.md` – AI assistance disclosure
- `run.py` – pipeline entry point
- `requirements.txt` – dependencies
- `docker-compose.yml` – MongoDB setup
- `README.md` – project documentation

## Setup & Execution

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d
python run.py
pytest -q

##Final Execution Result
Processed plant records: 30
Processed collection tank records: 30
Plant records needing review: 26
Tank records needing review: 15
MongoDB write complete: digital_paani

Data Quality

The pipeline follows a retain-and-flag approach. Records with validation issues are retained and flagged for review instead of being silently discarded.

Validation includes required fields, numeric ranges, enums, flow checks, tank sizing, tank arrangement, and cross-field consistency.

Key Challenges
1. Inconsistent Legacy Data

The Excel files contained variations in headers, formats, units, and value representations.

Approach: Implemented normalization logic to convert legacy values into the canonical schema.

2. Data Validation

Some records contained missing, inconsistent, or out-of-range values.

Approach: Added validation rules and retained problematic records with validation issues for review.

3. Tank and Flow Calculations

Some validations required comparing multiple fields and calculated values.

Approach: Implemented domain-specific validation for peaking factor, tank sizing, tank count, arrangement, and dimensions.

4. Idempotent MongoDB Writes

Repeated pipeline execution should not create duplicate records.

Approach: Used deterministic identifiers and MongoDB upsert operations.

AI Assistance

ChatGPT was used as a development assistant for:

Understanding assignment requirements
Reviewing the provided schema and validation rules
Discussing ETL and validation approaches
Identifying edge cases in legacy data
Reviewing code and documentation
Improving README and project documentation

The implementation and final outputs were reviewed and tested by the developer.

Detailed AI usage is documented in:

docs/AI_ASSISTANT.md

MongoDB

Database:

digital_paani

Collections:

plants
collection_tanks 