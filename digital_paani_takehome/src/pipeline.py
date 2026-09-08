"""End-to-end legacy survey ingestion pipeline."""

from __future__ import annotations

import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pandas as pd
from pymongo import MongoClient

from .config import EXPECTED_ROWS_PER_SHEET, SHEET_CONFIG
from .normalizers import (
    FRESHWATER_ALIASES,
    WASTEWATER_DEST_ALIASES,
    WASTEWATER_SOURCE_ALIASES,
    clean_text,
    is_blank,
    normalize_client_name,
    normalize_location,
    normalize_multiselect,
    normalize_sector,
    normalize_simple_enum,
    normalize_unit_processes,
    parse_arrangement,
    parse_boolean_yes_no,
    parse_fraction,
    parse_int,
    parse_number,
    parse_peak_flow_timing,
)
from .validation import make_issue, validate_plant, validate_tank


def read_source_workbook(path: Path) -> dict[str, pd.DataFrame]:
    """Read all five sheets using the known non-A1 header offsets from Appendix A."""
    sheets: dict[str, pd.DataFrame] = {}
    for sheet_name, cfg in SHEET_CONFIG.items():
        df = pd.read_excel(
            path,
            sheet_name=sheet_name,
            header=cfg["header"],
            usecols=cfg["usecols"],
            engine="openpyxl",
        )
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all").reset_index(drop=True)
        if len(df) != EXPECTED_ROWS_PER_SHEET:
            raise ValueError(
                f"{path.name} / {sheet_name}: expected {EXPECTED_ROWS_PER_SHEET} data rows, found {len(df)}"
            )
        sheets[sheet_name] = df
    return sheets


def _row_dict_by_id(df: pd.DataFrame, id_column: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in df.to_dict(orient="records"):
        plant_id = clean_text(row.get(id_column))
        if plant_id is None:
            continue
        if plant_id in result:
            raise ValueError(f"Duplicate plant id {plant_id!r} in one worksheet")
        result[plant_id] = row
    return result


def _issue_collector(target: list[dict[str, Any]]):
    def add_issue(
        code: str,
        field: str | None,
        message: str,
        severity: str = "error",
        raw_value: Any = None,
    ) -> None:
        target.append(make_issue(code, field, message, severity, raw_value))

    return add_issue


def _check_client_name(
    canonical_name: str | None,
    other_name: Any,
    sheet_name: str,
    issues: list[dict[str, Any]],
) -> None:
    other = clean_text(other_name)
    if canonical_name is None or other is None:
        return
    if canonical_name != other:
        issues.append(
            make_issue(
                "cross_sheet_client_name_difference",
                "client_name",
                f"Client name differs on {sheet_name}: {other!r}; canonical plant_design value is {canonical_name!r}.",
                "warning",
                other,
            )
        )


def _find_process_row(
    client_name: str,
    process_rows: list[dict[str, Any]],
    used_indexes: set[int],
) -> tuple[dict[str, Any] | None, float]:
    target = normalize_client_name(client_name)

    # First prefer exact match on normalized names.
    for idx, row in enumerate(process_rows):
        if idx in used_indexes:
            continue
        if normalize_client_name(row.get("Client Name")) == target:
            used_indexes.add(idx)
            return row, 1.0

    # Conservative fuzzy fallback if harmless abbreviations differ.
    best_idx = None
    best_score = 0.0
    for idx, row in enumerate(process_rows):
        if idx in used_indexes:
            continue
        score = SequenceMatcher(
            None,
            target,
            normalize_client_name(row.get("Client Name")),
        ).ratio()
        if score > best_score:
            best_idx = idx
            best_score = score

    if best_idx is not None and best_score >= 0.75:
        used_indexes.add(best_idx)
        return process_rows[best_idx], best_score
    return None, best_score


def _string_or_none(value: Any) -> str | None:
    return clean_text(value)


def transform_workbook(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sheets = read_source_workbook(path)

    plant_design = _row_dict_by_id(sheets["plant_design"], "Plant ID")
    water_quality = _row_dict_by_id(sheets["water quality"], "Plant ID")
    water_balance = _row_dict_by_id(sheets["water_balance"], "Plant ID")
    site = _row_dict_by_id(sheets["site-characteristics"], "Plant_ID")
    process_rows = sheets["process_design"].to_dict(orient="records")
    used_process_indexes: set[int] = set()

    plants: list[dict[str, Any]] = []
    tanks: list[dict[str, Any]] = []

    for plant_id, base in plant_design.items():
        plant_issues: list[dict[str, Any]] = []
        tank_issues: list[dict[str, Any]] = []
        add_plant_issue = _issue_collector(plant_issues)
        add_tank_issue = _issue_collector(tank_issues)

        wq = water_quality.get(plant_id, {})
        wb = water_balance.get(plant_id, {})
        st = site.get(plant_id, {})

        client_name = _string_or_none(base.get("Client Name"))
        if client_name is None:
            client_name = ""

        _check_client_name(client_name, wq.get("Client Name"), "water quality", plant_issues)
        _check_client_name(client_name, wb.get("Client Name"), "water_balance", plant_issues)
        _check_client_name(client_name, st.get("Client Name"), "site-characteristics", plant_issues)

        process, process_score = _find_process_row(client_name, process_rows, used_process_indexes)
        if process is None:
            process = {}
            tank_issues.append(
                make_issue(
                    "process_row_not_matched",
                    "client_name",
                    f"Could not safely match process_design row to client {client_name!r}; best score={process_score:.3f}.",
                    "error",
                )
            )
        else:
            process_client = _string_or_none(process.get("Client Name"))
            if process_client and process_client != client_name:
                tank_issues.append(
                    make_issue(
                        "cross_sheet_client_name_difference",
                        "client_name",
                        (
                            f"process_design name {process_client!r} differs from plant_design "
                            f"name {client_name!r}; matched using normalized name."
                        ),
                        "warning",
                        process_client,
                    )
                )

        design_location = normalize_location(base.get("Plant Location"))
        site_location = normalize_location(st.get("Plant Location"))
        chosen_location = site_location or design_location
        if design_location and site_location and design_location != site_location:
            plant_issues.append(
                make_issue(
                    "cross_sheet_location_difference",
                    "location_type",
                    (
                        f"plant_design says {design_location!r} but site-characteristics says "
                        f"{site_location!r}; using site-characteristics because its sheet note says "
                        "the location was re-recorded from the site."
                    ),
                    "warning",
                    {"plant_design": design_location, "site_characteristics": site_location},
                )
            )

        plant = {
            "_id": plant_id,
            "plant_id": plant_id,
            "client_name": client_name or None,
            "sector": normalize_sector(base.get("Sector")),
            "location_type": chosen_location,
            "start_of_operation": _string_or_none(base.get("Start of operation")),
            "design_flow_kld": parse_number(base.get("Design Flow (KLD)"), "design_flow_kld", add_plant_issue),
            "mean_flow_kld": parse_number(base.get("Mean flow, kld"), "mean_flow_kld", add_plant_issue),
            "peak_flow_kld": parse_number(base.get("Peak Flow KLD"), "peak_flow_kld", add_plant_issue),
            "peak_flow_timing": parse_peak_flow_timing(base.get("Peak flow timing"), "peak_flow_timing", add_plant_issue),
            "unit_processes": normalize_unit_processes(base.get("Unit processes"), add_plant_issue),
            "pfd_pfd_displayed": parse_boolean_yes_no(base.get("PFD displayed?"), "pfd_pfd_displayed", add_plant_issue),
            "inlet_cod_mg_l": parse_number(wq.get("Inlet COD (mg/L)"), "inlet_cod_mg_l", add_plant_issue),
            "inlet_bod_mg_l": parse_number(wq.get("Inlet BOD (mg/L)"), "inlet_bod_mg_l", add_plant_issue),
            "inlet_n_mg_l": parse_number(wq.get("Inlet Total N (mg/L)"), "inlet_n_mg_l", add_plant_issue),
            "inlet_tss_mg_l": parse_number(wq.get("Inlet TSS (mg/L)"), "inlet_tss_mg_l", add_plant_issue),
            "inlet_ph": parse_number(wq.get("Inlet pH"), "inlet_ph", add_plant_issue),
            "outlet_cod_mg_l": parse_number(wq.get("Outlet COD (mg/L)"), "outlet_cod_mg_l", add_plant_issue),
            "outlet_bod_mg_l": parse_number(wq.get("Outlet BOD (mg/L)"), "outlet_bod_mg_l", add_plant_issue),
            "outlet_n_mg_l": parse_number(wq.get("Outlet Total N (mg/L)"), "outlet_n_mg_l", add_plant_issue),
            "outlet_tss_mg_l": parse_number(wq.get("Outlet TSS (mg/L)"), "outlet_tss_mg_l", add_plant_issue),
            "outlet_color_observed": _string_or_none(wq.get("Outlet colour")),
            "outlet_odor_observed": parse_boolean_yes_no(wq.get("Objectionable odour at outlet?"), "outlet_odor_observed", add_plant_issue),
            "outlet_photo": _string_or_none(wq.get("Outlet photo ref")),
            "sludge_wasting_frequency": parse_number(process.get("Sludge wasting (per day)"), "sludge_wasting_frequency", add_plant_issue),
            "freshwater_source": normalize_multiselect(
                wb.get("Freshwater source"), FRESHWATER_ALIASES, r"\s*[;,+/]\s*"
            ),
            "freshwater_cost_per_kl": parse_number(wb.get("Freshwater cost (Rs/KL)"), "freshwater_cost_per_kl", add_plant_issue),
            "consumption_domestic_kld": parse_number(wb.get("Domestic consumption (KL/day)"), "consumption_domestic_kld", add_plant_issue),
            "consumption_laundry_kld": parse_number(wb.get("Laundry consumption (KL/day)"), "consumption_laundry_kld", add_plant_issue),
            "consumption_kitchen_kld": parse_number(wb.get("Kitchen consumption (KL/day)"), "consumption_kitchen_kld", add_plant_issue),
            "freshwater_tds_mg_l": parse_number(wb.get("Freshwater TDS (mg/L)"), "freshwater_tds_mg_l", add_plant_issue),
            "freshwater_ph": parse_number(wb.get("Freshwater pH"), "freshwater_ph", add_plant_issue),
            "freshwater_hardness_mg_l": parse_number(wb.get("Freshwater hardness (mg/L as CaCO3)"), "freshwater_hardness_mg_l", add_plant_issue),
            "freshwater_fluoride_mg_l": parse_number(wb.get("Freshwater fluoride (mg/L)"), "freshwater_fluoride_mg_l", add_plant_issue),
            "wastewater_source": normalize_multiselect(
                wb.get("Wastewater source"), WASTEWATER_SOURCE_ALIASES, r"\s*[;,+]\s*"
            ),
            "wastewater_destination": normalize_multiselect(
                wb.get("Treated water destination"), WASTEWATER_DEST_ALIASES, r"\s*[;,+]\s*"
            ),
            "treated_water_reuse_fraction": parse_fraction(wb.get("Reuse fraction"), "treated_water_reuse_fraction", add_plant_issue),
            "reuse_flushing_kld": parse_number(wb.get("Reuse - flushing (KL/day)"), "reuse_flushing_kld", add_plant_issue),
            "reuse_gardening_kld": parse_number(wb.get("Reuse - gardening (KL/day)"), "reuse_gardening_kld", add_plant_issue),
            "reuse_cooling_tower_kld": parse_number(wb.get("Reuse - cooling tower (KL/day)"), "reuse_cooling_tower_kld", add_plant_issue),
            "reuse_water_quality_tds_mg_l": parse_number(wb.get("Reuse point TDS (mg/L)"), "reuse_water_quality_tds_mg_l", add_plant_issue),
            "water_balance_displayed": parse_boolean_yes_no(wb.get("Water balance displayed?"), "water_balance_displayed", add_plant_issue),
            "_source": {"file": path.name},
        }

        tank = {
            "_id": f"{plant_id}:COLLECTION",
            "plant_id": plant_id,
            "tank_type": "COLLECTION",
            "tank_count": parse_int(process.get("Tank count"), "tank_count", add_tank_issue),
            "tank_arrangement": parse_arrangement(process.get("Tank arrangement (rows x cols)"), "tank_arrangement", add_tank_issue),
            "tank_shape": normalize_simple_enum(
                process.get("Tank shape"),
                {"rectangular": "Rectangular", "cylindrical": "Cylindrical"},
            ),
            "tank_volume_m3": parse_number(process.get("Tank volume (m3)"), "tank_volume_m3", add_tank_issue),
            "tank_length_m": parse_number(process.get("Tank length (m)"), "tank_length_m", add_tank_issue),
            "tank_width_m": parse_number(process.get("Tank width (m)"), "tank_width_m", add_tank_issue),
            "tank_diameter_m": parse_number(process.get("Tank diameter (m)"), "tank_diameter_m", add_tank_issue),
            "tank_height_m": parse_number(process.get("Tank height (m)"), "tank_height_m", add_tank_issue),
            "tank_sizing_groups": None if is_blank(process.get("Same dimensions for all tanks?")) else process.get("Same dimensions for all tanks?"),
            "tank_moc": _string_or_none(st.get("Tank material of construction")),
            "covered": normalize_simple_enum(
                st.get("Open / covered / sealed"),
                {"open": "Open", "covered": "Covered", "sealed/closed": "Sealed/Closed"},
            ),
            "tank_condition": normalize_simple_enum(
                st.get("Tank condition"),
                {"good": "Good", "fair": "Fair", "poor": "Poor"},
            ),
            "tank_accessibility": normalize_simple_enum(
                st.get("Tank accessibility"),
                {"easy": "Easy", "restricted": "Restricted", "unsafe": "Unsafe"},
            ),
            "sludge_observed_in_tank": parse_boolean_yes_no(
                st.get("Sludge visible in tank?"), "sludge_observed_in_tank", add_tank_issue
            ),
            "wiring_distance_to_panel_m": parse_number(
                st.get("Cable run to panel (m)"), "wiring_distance_to_panel_m", add_tank_issue
            ),
            "_source": {"file": path.name},
        }

        plant_issues.extend(validate_plant(plant))
        tank_issues.extend(validate_tank(tank, plant))

        plant["_validation"] = {
            "status": "needs_review" if any(i["severity"] == "error" for i in plant_issues) else "valid",
            "issues": plant_issues,
        }
        tank["_validation"] = {
            "status": "needs_review" if any(i["severity"] == "error" for i in tank_issues) else "valid",
            "issues": tank_issues,
        }

        plants.append(plant)
        tanks.append(tank)

    return plants, tanks


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_artifacts(
    output_dir: Path,
    plants: list[dict[str, Any]],
    tanks: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "plants.json", plants)
    _write_json(output_dir / "collection_tanks.json", tanks)

    issues = []
    for record_type, records in [("plant", plants), ("collection_tank", tanks)]:
        for record in records:
            for issue in record["_validation"]["issues"]:
                issues.append(
                    {
                        "record_type": record_type,
                        "record_id": record["_id"],
                        **issue,
                    }
                )
    _write_json(output_dir / "validation_issues.json", issues)


def write_to_mongo(
    mongo_uri: str,
    database_name: str,
    plants: list[dict[str, Any]],
    tanks: list[dict[str, Any]],
) -> None:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[database_name]

    db.plants.create_index("plant_id", unique=True)
    db.collection_tanks.create_index([("plant_id", 1), ("tank_type", 1)], unique=True)

    # Idempotency: deterministic _id + replace_one(upsert=True).
    # Re-running the same input updates the same document rather than duplicating it.
    for plant in plants:
        db.plants.replace_one({"_id": plant["_id"]}, plant, upsert=True)
    for tank in tanks:
        db.collection_tanks.replace_one({"_id": tank["_id"]}, tank, upsert=True)

    client.close()


def run_pipeline(
    input_dir: Path,
    output_dir: Path,
    mongo_uri: str,
    database_name: str,
    skip_mongo: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    files = sorted(input_dir.glob("DP-DE-TH-01_legacy_surveys_batch_*.xlsx"))
    if not files:
        raise FileNotFoundError(
            f"No input workbooks found in {input_dir}. Expected DP-DE-TH-01_legacy_surveys_batch_*.xlsx"
        )

    all_plants: list[dict[str, Any]] = []
    all_tanks: list[dict[str, Any]] = []
    seen_plant_ids: set[str] = set()

    for path in files:
        plants, tanks = transform_workbook(path)
        for plant in plants:
            if plant["plant_id"] in seen_plant_ids:
                raise ValueError(f"Duplicate plant id across files: {plant['plant_id']}")
            seen_plant_ids.add(plant["plant_id"])
        all_plants.extend(plants)
        all_tanks.extend(tanks)

    all_plants.sort(key=lambda d: d["plant_id"])
    all_tanks.sort(key=lambda d: d["plant_id"])

    write_artifacts(output_dir, all_plants, all_tanks)
    if not skip_mongo:
        write_to_mongo(mongo_uri, database_name, all_plants, all_tanks)

    return all_plants, all_tanks
