# Deployment notes

## Local execution

Requirements:
- Python 3.11+ recommended
- MongoDB 7 locally, or Docker Desktop
- Small local disk footprint for the five supplied workbooks and JSON output

Commands:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d
python run.py
pytest -q
```

## Compute requirement

The supplied workload is tiny: five Excel workbooks with six rows per worksheet. I would deploy this onto existing low-utilization application / batch capacity rather than request a dedicated EC2 instance. The important requirements are reliable network access to MongoDB, enough memory for Python plus Excel parsing, and a scheduler or job runner.

If isolation required a new instance, a small general-purpose burstable instance such as `t3.small` / `t4g.small` (where the Python/native dependency stack is compatible with ARM for t4g) would be more than sufficient. The workload is latency-insensitive and neither CPU- nor memory-intensive at the supplied scale.

## CI/CD proposal

1. Pull request triggers linting / formatting and `pytest`.
2. Run an integration test against an ephemeral MongoDB container.
3. Run the pipeline against a small fixture workbook and assert deterministic document counts and selected validation outcomes.
4. Build a versioned application artifact/container.
5. Deploy first to a non-production environment and run the batch in dry-run / artifact-only mode.
6. Review validation issue counts and a sample of documents.
7. Promote the same artifact to production.
8. Because writes are deterministic upserts, rollback is primarily application rollback; data changes should additionally be protected with collection backups/snapshots before a production backfill.

## Operational observability I would add next

- Structured logs with source file, plant ID and rule code
- Run-level summary metrics
- Counts read / transformed / written / needing review
- Failure notification and a run identifier
- Persisted audit metadata / source checksum for stronger replay tracking
