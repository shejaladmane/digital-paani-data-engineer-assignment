# In-scope design data fields

*The target schema for DP-DE-TH-01. These are the live survey registry definitions for
the plant-baseline, water-balance and collection-tank questions. Field ids are the
canonical names used by the digital survey application and the MongoDB data store —
your ingestion output should key on them.*

Notation: **R** = the survey app marks the answer required. `unit` is informational —
values are stored unconverted in the unit shown.

## Plant baseline (`QuestionGroup.PLANT`)

| Field id | Question text | Type | Unit | Bounds | R |
|---|---|---|---|---|---|
| `client_name` | What is the name of the client who owns this site? | STRING |  |  | ● |
| `sector` | What sector does this plant operate in? | ENUM |  |  | ● |
| `location_type` | Where is the plant located? | ENUM |  |  | ● |
| `start_of_operation` | What is the start date of plant operation? | STRING |  |  |  |
| `design_flow_kld` | What is the plant's design capacity in kL/d? | FLOAT | KLD | ≥ 0 | ● |
| `mean_flow_kld` | What is the plant's average treatment volume in kL/d? | FLOAT | KLD | ≥ 0 | ● |
| `peak_flow_kld` | What is the observed peak inlet flow? | FLOAT | KLD | ≥ 0 | ● |
| `peak_flow_timing` | When do/does the peak flow period(s) typically happen? | LIST_OF_RANGES |  |  |  |
| `unit_processes` | What unit processes does this plant have? | ENUM |  |  | ● |
| `pfd_pfd_displayed` | Is a process flow diagram displayed on-site? | BOOLEAN |  |  | ● |
| `inlet_cod_mg_l` | What is the inlet COD concentration? | FLOAT | mg/L | 300–1000 |  |
| `inlet_bod_mg_l` | What is the inlet BOD concentration (mg/L)? | FLOAT | mg/L | 100–600 |  |
| `inlet_n_mg_l` | What is the inlet's Total Nitrogen concentration (mg/L)? | FLOAT | mg/L | 10–100 |  |
| `inlet_tss_mg_l` | What is the inlet TSS concentration? | FLOAT | mg/L | 100–500 |  |
| `inlet_ph` | What is the inlet pH? | FLOAT |  | 1–14 |  |
| `outlet_cod_mg_l` | What is the treated water outlet COD concentration? | FLOAT | mg/L | 22.5–82.5 |  |
| `outlet_bod_mg_l` | What is the treated water outlet BOD concentration? | FLOAT | mg/L | 4.5–22 |  |
| `outlet_n_mg_l` | What is the treated water outlet Total N concentration? | FLOAT | mg/L | 0.9–11 |  |
| `outlet_tss_mg_l` | What is the treated water outlet TSS concentration? | FLOAT | mg/L | 9–33 |  |
| `outlet_color_observed` | What is the visible colour of the treated water at the outlet? | STRING |  |  |  |
| `outlet_odor_observed` | Was an objectionable odour observed at the treated water outlet? | BOOLEAN |  |  |  |
| `outlet_photo` | Take a photo of the treated water outlet | STRING |  |  |  |
| `sludge_wasting_frequency` | How frequently is waste sludge removed (x per day)? | FLOAT |  |  |  |

**Permitted values**

- `sector`: `municipal`, `industrial`, `buildings: commercial`, `buildings: residential`
- `location_type`: `Basement`, `Ground level`
- `unit_processes` *(multi-select)*: `ACTIVATED_SLUDGE`, `ANOXIC_TREATMENT`, `BELT_FILTER_PRESS_DEWATERING`, `BRINE_CONCENTRATION`, `CARTRIDGE_FILTRATION`, `CASCADE_AERATION`, `CASS`, `CENTRIFUGE_DEWATERING`, `CENTRIFUGE_THICKENING`, `CHLORINATION`, `CLARIFICATION`, `COLLECTION`, `COOLING`, `CRYSTALLIZATION`, `DAF_THICKENING`, `DECHLORINATION`, `DISSOLVED_AIR_FLOTATION`, `DISTRIBUTION`, `EQUALIZATION`, `FILTER_FEED`, `FINE_SCREENING`, `GRAVITY_BELT_THICKENING`, `GRAVITY_THICKENING`, `GRIT_REMOVAL`, `IRRIGATION`, `MBBR`, `MBR`, `MEDIA_FILTRATION`, `MICROFILTRATION`, `NANOFILTRATION`, `OIL_GREASE_REMOVAL`, `OZONATION`, `PLATE_FRAME_FILTRATION`, `RO_DESALINATION`, `ROTARY_DRUM_SCREENING`, `ROTARY_DRUM_THICKENING`, `SABRE`, `SBR`, `SCREENING`, `SCREW_PRESS_DEWATERING`, `SLUDGE_DIGESTION`, `SLUDGE_HOLDING`, `SLUDGE_TRANSFER`, `SOFTENING`, `SOLAR_DRYING`, `SUMP`, `THERMAL_DRYING`, `TREATED_WATER`, `TUBE_SETTLING`, `ULTRAFILTRATION`, `UV_DISINFECTION`

## Water balance (`QuestionGroup.WATER_BALANCE`)

| Field id | Question text | Type | Unit | Bounds | R |
|---|---|---|---|---|---|
| `freshwater_source` | What are the site's freshwater sources? | ENUM |  |  | ● |
| `freshwater_cost_per_kl` | What is the cost/kL of freshwater at the site? | FLOAT | ₹/KL | ≥ 0 |  |
| `consumption_domestic_kld` | What is the total freshwater consumption at the site? | FLOAT | KL/day | ≥ 0 |  |
| `consumption_laundry_kld` | What is the freshwater consumption for laundry? | FLOAT | KL/day | ≥ 0 |  |
| `consumption_kitchen_kld` | What is the freshwater consumption for the kitchen? | FLOAT | KL/day | ≥ 0 |  |
| `freshwater_tds_mg_l` | What is the TDS of the freshwater source? | FLOAT | mg/L | 45–275 |  |
| `freshwater_ph` | What is the pH of the freshwater source? | FLOAT |  | 0–14 |  |
| `freshwater_hardness_mg_l` | What is the hardness of the freshwater source? | FLOAT | mg/L as CaCO3 | 9–198 |  |
| `freshwater_fluoride_mg_l` | What is the fluoride concentration in the freshwater source? | FLOAT | mg/L | 0.009–0.33 |  |
| `wastewater_source` | What are the plant's primary sources of wastewater? | ENUM |  |  | ● |
| `wastewater_destination` | How is treated wastewater disposed of? | ENUM |  |  | ● |
| `treated_water_reuse_fraction` | What fraction of treated water is reused on-site? | FLOAT |  | 0–1 |  |
| `reuse_flushing_kld` | How much treated water is reused for flushing? | FLOAT | KL/day | ≥ 0 |  |
| `reuse_gardening_kld` | How much treated water is reused for gardening? | FLOAT | KL/day | ≥ 0 |  |
| `reuse_cooling_tower_kld` | How much treated water is reused for the cooling tower? | FLOAT | KL/day | ≥ 0 |  |
| `reuse_water_quality_tds_mg_l` | What is the TDS of the treated water at the reuse points? | FLOAT | mg/L | 450–1100 |  |
| `water_balance_displayed` | Is a water balance diagram displayed on-site? | BOOLEAN |  |  | ● |

**Permitted values**

- `freshwater_source` *(multi-select)*: `Borewell`, `Municipal`, `Surface`, `Tankers`, `Other`
- `wastewater_source` *(multi-select)*: `Domestic sewage`, `Kitchen/canteen`, `Laundry`, `Municipal sewage`, `Industrial effluent`, `Combined effluent (CETP)`, `Cooling tower blowdown`, `Boiler blowdown`, `RO reject`, `Wash water`, `Stormwater`, `Sump`, `Other`
- `wastewater_destination` *(multi-select)*: `On-site reuse`, `Surface water discharge`, `Sewer discharge`, `Groundwater recharge`, `Land application/irrigation`, `Tanker removal`, `Zero liquid discharge (ZLD)`, `Other`

## Collection tank (`TankType.COLLECTION`)

| Field id | Question text | Type | Unit | Bounds | R |
|---|---|---|---|---|---|
| `tank_count` | How many tanks of this type are there? | INT |  | ≥ 0 | ● |
| `tank_arrangement` | How are the tanks arranged? | INTEGER_PAIR |  |  | ● |
| `tank_shape` | What is the tank's shape? | ENUM |  |  | ● |
| `tank_volume_m3` | What is the tank's volume (m3)? | FLOAT |  | ≥ 0 |  |
| `tank_length_m` | What is the tank's length (m)? | FLOAT |  | ≥ 0 |  |
| `tank_width_m` | What is the tank's width (m)? | FLOAT |  | ≥ 0 |  |
| `tank_diameter_m` | What is the tank's diameter (m)? | FLOAT |  | ≥ 0 |  |
| `tank_height_m` | What is the tank's height (m)? | FLOAT |  | ≥ 0 |  |
| `tank_sizing_groups` | Do all tanks have the same dimensions? | DIMENSION_COUNT |  |  |  |
| `tank_moc` | What is the tank's material of construction? | STRING |  |  |  |
| `covered` | Is the tank open, covered, or sealed? | ENUM |  |  | ● |
| `tank_condition` | What is the overall condition of the tank? | ENUM |  |  | ● |
| `tank_accessibility` | How accessible is the tank for maintenance? | ENUM |  |  | ● |
| `sludge_observed_in_tank` | Was visible sludge observed inside this tank during the visit? | BOOLEAN |  |  | ● |
| `wiring_distance_to_panel_m` | What is the cable run distance from this tank's equipment to the electrical panel? | FLOAT | m | ≥ 0 |  |

**Permitted values**

- `tank_shape`: `Rectangular`, `Cylindrical`
- `covered`: `Open`, `Covered`, `Sealed/Closed`
- `tank_condition`: `Good`, `Fair`, `Poor`
- `tank_accessibility`: `Easy`, `Restricted`, `Unsafe`

## Notes on the awkward types

- `peak_flow_timing` (`LIST_OF_RANGES`) is stored as a list of (start hour, end hour)
  integer pairs on a 24-hour clock: *morning 7–9 and evening 6–8* is `[(7,9),(18,20)]`.
- `tank_arrangement` (`INTEGER_PAIR`) is stored as `(rows, columns)`.
- `tank_sizing_groups` (`DIMENSION_COUNT`) is only populated when the tanks of a type
  have differing dimensions; an empty value means all tanks share the dimensions given
  in the other fields. Every tank in this dataset is uniform, so you can treat it as
  a pass-through.
- `tank_length_m` / `tank_width_m` apply to rectangular tanks and `tank_diameter_m` to
  cylindrical ones; the survey app hides the inapplicable fields, so a blank there is
  expected rather than missing.
- Booleans are stored as `Yes` / `No`.
- `outlet_photo` holds a reference to a photo captured during the survey. The legacy
  sheets carry the filename the domain team recorded; the image files themselves are
  out of scope for this assignment.

*55 fields in scope.*
