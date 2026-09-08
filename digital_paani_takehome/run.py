from __future__ import annotations

import argparse
from pathlib import Path

from src.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Digital Paani legacy survey ingestion")
    parser.add_argument("--input-dir", default="data/input")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
    parser.add_argument("--database", default="digital_paani")
    parser.add_argument(
        "--skip-mongo",
        action="store_true",
        help="Create cleaned artifacts without writing to MongoDB (development convenience only).",
    )
    args = parser.parse_args()

    plants, tanks = run_pipeline(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        mongo_uri=args.mongo_uri,
        database_name=args.database,
        skip_mongo=args.skip_mongo,
    )

    plant_review = sum(p["_validation"]["status"] == "needs_review" for p in plants)
    tank_review = sum(t["_validation"]["status"] == "needs_review" for t in tanks)

    print(f"Processed plant records: {len(plants)}")
    print(f"Processed collection tank records: {len(tanks)}")
    print(f"Plant records needing review: {plant_review}")
    print(f"Tank records needing review: {tank_review}")
    print("Artifacts written to:", Path(args.output_dir).resolve())
    if args.skip_mongo:
        print("MongoDB write skipped.")
    else:
        print(f"MongoDB write complete: {args.database}")


if __name__ == "__main__":
    main()
