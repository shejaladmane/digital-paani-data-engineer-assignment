from src.normalizers import parse_arrangement, parse_fraction
from src.validation import validate_plant, validate_tank


def collector(items):
    def add(code, field, message, severity="error", raw_value=None):
        items.append(
            {
                "code": code,
                "field": field,
                "message": message,
                "severity": severity,
                "raw_value": raw_value,
            }
        )
    return add


def test_percentage_is_converted_to_fraction():
    issues = []
    value = parse_fraction("61%", "treated_water_reuse_fraction", collector(issues))
    assert value == 0.61
    assert any(i["code"] == "percent_to_fraction" for i in issues)


def test_tank_arrangement_parsing():
    issues = []
    assert parse_arrangement("2 x 1", "tank_arrangement", collector(issues)) == [2, 1]
    assert not issues


def test_peaking_factor_rule():
    plant = {
        "client_name": "Example",
        "sector": "industrial",
        "location_type": "Ground level",
        "design_flow_kld": 500.0,
        "mean_flow_kld": 100.0,
        "peak_flow_kld": 600.0,
        "unit_processes": ["MBBR"],
        "pfd_pfd_displayed": "Yes",
        "freshwater_source": ["Municipal"],
        "wastewater_source": ["Domestic sewage"],
        "wastewater_destination": ["On-site reuse"],
        "water_balance_displayed": "Yes",
    }
    issues = validate_plant(plant)
    assert any(i["code"] == "peaking_factor_out_of_range" for i in issues)


def test_tank_count_vs_arrangement_rule():
    plant = {"design_flow_kld": 300.0}
    tank = {
        "tank_count": 2,
        "tank_arrangement": [1, 1],
        "tank_shape": "Rectangular",
        "tank_volume_m3": 10.0,
        "tank_length_m": 2.0,
        "tank_width_m": 2.0,
        "tank_diameter_m": None,
        "tank_height_m": 2.5,
        "tank_sizing_groups": None,
        "tank_moc": "RCC",
        "covered": "Covered",
        "tank_condition": "Good",
        "tank_accessibility": "Easy",
        "sludge_observed_in_tank": "No",
        "wiring_distance_to_panel_m": 10.0,
    }
    issues = validate_tank(tank, plant)
    assert any(i["code"] == "tank_count_arrangement_mismatch" for i in issues)
