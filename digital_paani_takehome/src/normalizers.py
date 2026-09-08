"""Normalization helpers for messy spreadsheet values."""

from __future__ import annotations

import math
import re
from typing import Any, Callable

IssueSink = Callable[[str, str | None, str, str, Any], None]


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def clean_text(value: Any) -> str | None:
    if is_blank(value):
        return None
    return re.sub(r"\s+", " ", str(value).strip())


def normalize_client_name(value: Any) -> str:
    """Create a conservative matching key; this is not the stored client name."""
    text = clean_text(value) or ""
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    replacements = {
        "twp": "township",
        "centre": "center",
        "pvt": "private",
        "ltd": "limited",
    }
    tokens = [replacements.get(token, token) for token in text.split()]
    # Corporate suffixes are ignored only for matching, not for stored data.
    tokens = [t for t in tokens if t not in {"private", "limited"}]
    return " ".join(tokens)


def parse_number(value: Any, field: str, add_issue: IssueSink) -> float | None:
    if is_blank(value):
        return None
    if isinstance(value, bool):
        add_issue("parse_error", field, "Boolean found where a number was expected.", "error", value)
        return None
    if isinstance(value, (int, float)):
        return float(value)

    raw = clean_text(value)
    assert raw is not None

    fraction_match = re.fullmatch(r"\s*([+-]?\d+)\s*/\s*(\d+)\s*", raw)
    if fraction_match:
        denominator = int(fraction_match.group(2))
        if denominator == 0:
            add_issue("parse_error", field, "Fraction has a zero denominator.", "error", value)
            return None
        parsed = int(fraction_match.group(1)) / denominator
        add_issue("numeric_text", field, "Numeric value arrived as text and was parsed.", "warning", value)
        return float(parsed)

    cleaned = raw.replace(",", "")
    match = re.search(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", cleaned)
    if not match:
        add_issue("parse_error", field, "Could not parse numeric value.", "error", value)
        return None

    parsed = float(match.group(0))
    add_issue("numeric_text", field, "Numeric value arrived as text and was parsed.", "warning", value)
    return parsed


def parse_int(value: Any, field: str, add_issue: IssueSink) -> int | None:
    number = parse_number(value, field, add_issue)
    if number is None:
        return None
    if not float(number).is_integer():
        add_issue("type_error", field, "Expected an integer value.", "error", value)
        return None
    return int(number)


def parse_fraction(value: Any, field: str, add_issue: IssueSink) -> float | None:
    if is_blank(value):
        return None
    raw = clean_text(value)
    if raw and raw.endswith("%"):
        number = parse_number(raw[:-1], field, add_issue)
        if number is None:
            return None
        add_issue(
            "percent_to_fraction",
            field,
            "Percentage text was converted to a 0-1 fraction.",
            "warning",
            value,
        )
        return number / 100.0
    return parse_number(value, field, add_issue)


def parse_boolean_yes_no(value: Any, field: str, add_issue: IssueSink) -> str | None:
    if is_blank(value):
        return None
    text = clean_text(value)
    assert text is not None
    token = text.casefold()
    if token in {"yes", "y", "true", "1"}:
        return "Yes"
    if token in {"no", "n", "false", "0"}:
        return "No"
    add_issue("parse_error", field, "Unrecognized boolean representation.", "error", value)
    return None


def normalize_sector(value: Any) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    token = text.casefold()
    aliases = {
        "municipal": "municipal",
        "industrial": "industrial",
        "industrial effluent plant": "industrial",
        "commercial": "buildings: commercial",
        "commercial building": "buildings: commercial",
        "commercial - office": "buildings: commercial",
        "residential": "buildings: residential",
        "residential building": "buildings: residential",
    }
    return aliases.get(token, text)


def normalize_location(value: Any) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    aliases = {"basement": "Basement", "ground level": "Ground level"}
    return aliases.get(text.casefold(), text)


def normalize_simple_enum(value: Any, aliases: dict[str, str]) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    return aliases.get(text.casefold(), text)


def split_multiselect(value: Any, separators_regex: str) -> list[str] | None:
    text = clean_text(value)
    if text is None:
        return None
    return [part.strip() for part in re.split(separators_regex, text) if part.strip()]


def normalize_multiselect(
    value: Any,
    aliases: dict[str, str],
    separators_regex: str,
) -> list[str] | None:
    parts = split_multiselect(value, separators_regex)
    if parts is None:
        return None
    return [aliases.get(part.casefold(), part) for part in parts]


UNIT_PROCESS_ALIASES = {
    "screening": "SCREENING",
    "equalization": "EQUALIZATION",
    "eq": "EQUALIZATION",
    "mbbr": "MBBR",
    "clarification": "CLARIFICATION",
    "chlorination": "CHLORINATION",
    "asp": "ACTIVATED_SLUDGE",
    "activated sludge": "ACTIVATED_SLUDGE",
    "tube settling": "TUBE_SETTLING",
    "media filtration": "MEDIA_FILTRATION",
    "sbr": "SBR",
    "cass": "CASS",
    "mbr": "MBR",
    "ogt": "OIL_GREASE_REMOVAL",
    "oil grease removal": "OIL_GREASE_REMOVAL",
    "uv": "UV_DISINFECTION",
    "uv disinfection": "UV_DISINFECTION",
    "anoxic": "ANOXIC_TREATMENT",
    "anoxic treatment": "ANOXIC_TREATMENT",
}


def normalize_unit_processes(value: Any, add_issue: IssueSink) -> list[str] | None:
    parts = split_multiselect(value, r"\s*[;,+]\s*")
    if parts is None:
        return None
    result: list[str] = []
    for part in parts:
        key = part.casefold().strip()
        if key == "mf":
            # The source abbreviation is ambiguous. We make the assumption explicit.
            result.append("MEDIA_FILTRATION")
            add_issue(
                "mapping_assumption",
                "unit_processes",
                "Mapped source abbreviation 'MF' to MEDIA_FILTRATION; confirm with domain team.",
                "warning",
                part,
            )
        else:
            result.append(UNIT_PROCESS_ALIASES.get(key, part))
    return result


FRESHWATER_ALIASES = {
    "borewell": "Borewell",
    "municipal": "Municipal",
    "surface": "Surface",
    "tankers": "Tankers",
    "tanker": "Tankers",
    "other": "Other",
}

WASTEWATER_SOURCE_ALIASES = {
    "domestic sewage": "Domestic sewage",
    "kitchen/canteen": "Kitchen/canteen",
    "laundry": "Laundry",
    "municipal sewage": "Municipal sewage",
    "industrial effluent": "Industrial effluent",
    "combined effluent (cetp)": "Combined effluent (CETP)",
    "cooling tower blowdown": "Cooling tower blowdown",
    "boiler blowdown": "Boiler blowdown",
    "ro reject": "RO reject",
    "wash water": "Wash water",
    "stormwater": "Stormwater",
    "sump": "Sump",
    "other": "Other",
}

WASTEWATER_DEST_ALIASES = {
    "on-site reuse": "On-site reuse",
    "surface water discharge": "Surface water discharge",
    "sewer discharge": "Sewer discharge",
    "groundwater recharge": "Groundwater recharge",
    "land application/irrigation": "Land application/irrigation",
    "tanker removal": "Tanker removal",
    "zero liquid discharge (zld)": "Zero liquid discharge (ZLD)",
    "other": "Other",
}


def parse_arrangement(value: Any, field: str, add_issue: IssueSink) -> list[int] | None:
    if is_blank(value):
        return None
    text = clean_text(value)
    assert text is not None
    match = re.fullmatch(r"\s*(\d+)\s*[xX×]\s*(\d+)\s*", text)
    if not match:
        add_issue("parse_error", field, "Expected tank arrangement like '2 x 1'.", "error", value)
        return None
    return [int(match.group(1)), int(match.group(2))]


def _hour_to_24(hour: int, suffix: str | None) -> int:
    if suffix is None:
        return hour
    suffix = suffix.casefold()
    if suffix == "am":
        return 0 if hour == 12 else hour
    if suffix == "pm":
        return hour if hour == 12 else hour + 12
    return hour


def parse_peak_flow_timing(value: Any, field: str, add_issue: IssueSink) -> list[list[int]] | None:
    if is_blank(value):
        return None
    raw = clean_text(value)
    assert raw is not None
    text = raw.casefold()

    if text in {"continuous", "round the clock"}:
        add_issue(
            "mapping_assumption",
            field,
            "Mapped an all-day textual description to [0, 24].",
            "warning",
            value,
        )
        return [[0, 24]]

    # The target type only supports integer hours. Do not silently round half-hours.
    minute_matches = re.findall(r":(\d{2})", text)
    if any(minutes != "00" for minutes in minute_matches):
        add_issue(
            "unsupported_precision",
            field,
            "Source contains minute-level times but target schema stores integer-hour ranges; value left null.",
            "warning",
            value,
        )
        return None

    # Convert 0700, 1800, etc. to 7, 18 when minutes are exactly 00.
    def four_digit_to_hour(match: re.Match[str]) -> str:
        return str(int(match.group(1)))

    text = re.sub(r"\b([01]\d|2[0-3])00\b", four_digit_to_hour, text)
    text = text.replace(":00", "")

    pattern = re.compile(
        r"(?<!\d)(\d{1,2})\s*(am|pm)?\s*(?:-|to)\s*(\d{1,2})\s*(am|pm)?(?!\d)"
    )
    ranges: list[list[int]] = []
    for match in pattern.finditer(text):
        start = int(match.group(1))
        start_suffix = match.group(2)
        end = int(match.group(3))
        end_suffix = match.group(4)

        # In '6-8pm', pm applies to both ends.
        if start_suffix is None and end_suffix is not None:
            start_suffix = end_suffix
        if end_suffix is None and start_suffix is not None:
            end_suffix = start_suffix

        start24 = _hour_to_24(start, start_suffix)
        end24 = _hour_to_24(end, end_suffix)
        if not (0 <= start24 <= 23 and 0 <= end24 <= 24):
            add_issue("parse_error", field, "Peak-flow hour falls outside the 24-hour clock.", "error", value)
            return None
        ranges.append([start24, end24])

    if not ranges:
        add_issue("parse_error", field, "Could not parse peak-flow timing into hour ranges.", "warning", value)
        return None
    return ranges
