"""Executable validation rules derived from validation_rules.md."""

from __future__ import annotations

import math
from typing import Any

from .config import (
    BOUNDS,
    ENUMS,
    NONNEGATIVE_FIELDS,
    PLANT_REQUIRED_FIELDS,
    STRICTLY_POSITIVE_FIELDS,
    TANK_REQUIRED_FIELDS,
)


def make_issue(
    code: str,
    field: str | None,
    message: str,
    severity: str = "error",
    raw_value: Any = None,
) -> dict[str, Any]:
    issue = {
        "code": code,
        "field": field,
        "severity": severity,
        "message": message,
    }
    if raw_value is not None:
        issue["raw_value"] = raw_value
    return issue


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == []


def _validate_required(record: dict[str, Any], required: set[str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for field in sorted(required):
        if _missing(record.get(field)):
            issues.append(make_issue("required_missing", field, "Required field is blank."))
    return issues


def _validate_enums(record: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for field, permitted in ENUMS.items():
        if field not in record or _missing(record.get(field)):
            continue
        value = record[field]
        values = value if isinstance(value, list) else [value]
        for item in values:
            if item not in permitted:
                issues.append(
                    make_issue(
                        "enum_not_permitted",
                        field,
                        f"Value {item!r} is not in the supplied permitted-value list.",
                        "error",
                        item,
                    )
                )
    return issues


def _validate_numeric_bounds(record: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    for field, (minimum, maximum) in BOUNDS.items():
        value = record.get(field)
        if value is None:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            issues.append(make_issue("type_error", field, "Expected numeric value."))
            continue
        if minimum is not None and value < minimum:
            issues.append(
                make_issue(
                    "below_plausibility_band",
                    field,
                    f"Value {value} is below the minimum {minimum}.",
                )
            )
        if maximum is not None and value > maximum:
            issues.append(
                make_issue(
                    "above_plausibility_band",
                    field,
                    f"Value {value} is above the maximum {maximum}.",
                )
            )

    for field in STRICTLY_POSITIVE_FIELDS:
        value = record.get(field)
        if value is None:
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value <= 0:
            issues.append(
                make_issue(
                    "non_positive_value",
                    field,
                    "Validation rules state that zero or negative is not plausible for this field.",
                )
            )

    for field in NONNEGATIVE_FIELDS:
        value = record.get(field)
        if value is None:
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value < 0:
            issues.append(make_issue("negative_value", field, "Value must be non-negative."))

    return issues


def validate_plant(plant: dict[str, Any]) -> list[dict[str, Any]]:
    issues = []
    issues.extend(_validate_required(plant, PLANT_REQUIRED_FIELDS))
    issues.extend(_validate_enums(plant))
    issues.extend(_validate_numeric_bounds(plant))

    mean_flow = plant.get("mean_flow_kld")
    peak_flow = plant.get("peak_flow_kld")
    if isinstance(mean_flow, (int, float)) and isinstance(peak_flow, (int, float)) and mean_flow > 0:
        peaking_factor = peak_flow / mean_flow
        # Base rule 2.0-4.5 with 10% design-adequacy margin -> 1.8-4.95.
        if not 1.8 <= peaking_factor <= 4.95:
            issues.append(
                make_issue(
                    "peaking_factor_out_of_range",
                    "peak_flow_kld",
                    f"Peak/mean flow ratio is {peaking_factor:.3f}; allowed band with margin is 1.8-4.95.",
                )
            )

    return issues


def validate_tank(tank: dict[str, Any], plant: dict[str, Any]) -> list[dict[str, Any]]:
    issues = []
    issues.extend(_validate_required(tank, TANK_REQUIRED_FIELDS))
    issues.extend(_validate_enums(tank))
    issues.extend(_validate_numeric_bounds(tank))

    count = tank.get("tank_count")
    arrangement = tank.get("tank_arrangement")
    if isinstance(count, int) and isinstance(arrangement, list) and len(arrangement) == 2:
        arrangement_count = arrangement[0] * arrangement[1]
        if arrangement_count != count:
            issues.append(
                make_issue(
                    "tank_count_arrangement_mismatch",
                    "tank_arrangement",
                    f"rows × columns = {arrangement_count}, but tank_count = {count}.",
                )
            )

    # Collection tank sizing: design_flow/20/6, with 10% shortfall tolerated.
    design_flow = plant.get("design_flow_kld")
    volume = tank.get("tank_volume_m3")
    if (
        isinstance(design_flow, (int, float))
        and design_flow > 0
        and isinstance(volume, (int, float))
        and volume >= 0
        and isinstance(count, int)
        and count > 0
    ):
        required_volume = design_flow / 20.0 / 6.0
        total_reported_volume = volume * count
        minimum_with_margin = required_volume * 0.90
        if total_reported_volume < minimum_with_margin:
            issues.append(
                make_issue(
                    "collection_tank_undersized",
                    "tank_volume_m3",
                    (
                        f"Total tank volume {total_reported_volume:.3f} m3 is below the "
                        f"10%-margin minimum {minimum_with_margin:.3f} m3 "
                        f"(nominal requirement {required_volume:.3f} m3)."
                    ),
                )
            )

    # Reported volume versus dimensions. Skip when a required dimension is missing or <= 0.
    shape = tank.get("tank_shape")
    reported_volume = tank.get("tank_volume_m3")
    calculated_volume = None

    if shape == "Rectangular":
        length = tank.get("tank_length_m")
        width = tank.get("tank_width_m")
        height = tank.get("tank_height_m")
        if all(isinstance(v, (int, float)) and v > 0 for v in [length, width, height]):
            calculated_volume = length * width * height
    elif shape == "Cylindrical":
        diameter = tank.get("tank_diameter_m")
        height = tank.get("tank_height_m")
        if all(isinstance(v, (int, float)) and v > 0 for v in [diameter, height]):
            calculated_volume = math.pi / 4.0 * diameter**2 * height

    if (
        calculated_volume is not None
        and isinstance(reported_volume, (int, float))
        and reported_volume > 0
    ):
        lower = reported_volume * 0.90
        upper = reported_volume * 1.10
        if not lower <= calculated_volume <= upper:
            issues.append(
                make_issue(
                    "tank_volume_dimension_mismatch",
                    "tank_volume_m3",
                    (
                        f"Dimensions imply {calculated_volume:.3f} m3 while reported volume is "
                        f"{reported_volume:.3f} m3; allowed range is {lower:.3f}-{upper:.3f} m3."
                    ),
                )
            )

    return issues
