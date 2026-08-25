#!/usr/bin/env python3
"""
APACHE II (Acute Physiology and Chronic Health Evaluation II) Calculator.

Implements the scoring system published by Knaus et al. (1985):
  - 12 acute physiology variables, each scored 0-4
  - GCS component = 15 - actual GCS
  - Creatinine points doubled when acute renal failure (ARF) is present
  - Age points (0-6)
  - Chronic health points (0 or 2 or 5)
  - Total score range: 0-71

Predicted hospital mortality uses the Knaus logistic equation:
  ln(R/(1-R)) = -3.517 + (APACHE II x 0.146)
                + 0.603 (if emergency surgery)
                + diagnostic_category_weight

Reference:
  Knaus WA, Draper EA, Wagner DP, Zimmerman JE.
  APACHE II: a severity of disease classification system.
  Crit Care Med. 1985;13(10):818-829.

Stdlib only. No external dependencies.
"""

import math
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Scoring bands
#
# Each band list is ordered from HIGHEST threshold downward.
# _band() returns the points for the first threshold the value meets.
# ---------------------------------------------------------------------------

TEMPERATURE_BANDS = [
    (41.0, 4),   # >= 41
    (39.0, 3),   # 39.0 - 40.9
    (38.5, 1),   # 38.5 - 38.9
    (36.0, 0),   # 36.0 - 38.4
    (34.0, 1),   # 34.0 - 35.9
    (32.0, 2),   # 32.0 - 33.9
    (30.0, 3),   # 30.0 - 31.9
    (-999.0, 4), # <= 29.9
]

MAP_BANDS = [
    (160.0, 4),  # >= 160
    (130.0, 3),  # 130 - 159
    (110.0, 2),  # 110 - 129
    (70.0, 0),   # 70 - 109
    (50.0, 2),   # 50 - 69
    (-999.0, 4), # <= 49
]

HEART_RATE_BANDS = [
    (180.0, 4),  # >= 180
    (140.0, 3),  # 140 - 179
    (110.0, 2),  # 110 - 139
    (70.0, 0),   # 70 - 109
    (55.0, 2),   # 55 - 69
    (40.0, 3),   # 40 - 54
    (-999.0, 4), # <= 39
]

RESPIRATORY_RATE_BANDS = [
    (50.0, 4),   # >= 50
    (35.0, 3),   # 35 - 49
    (25.0, 1),   # 25 - 34
    (12.0, 0),   # 12 - 24
    (10.0, 1),   # 10 - 11
    (6.0, 2),    # 6 - 9
    (-999.0, 4), # <= 5
]

# A-aDO2 bands (used when FiO2 >= 0.5)
A_ADO2_BANDS = [
    (500.0, 4),  # >= 500
    (350.0, 3),  # 350 - 499
    (200.0, 2),  # 200 - 349
    (-999.0, 0), # < 200
]

# PaO2 bands (used when FiO2 < 0.5)
PAO2_BANDS = [
    (71.0, 0),   # > 70
    (61.0, 1),   # 61 - 70
    (55.0, 3),   # 55 - 60
    (-999.0, 4), # < 55
]

ARTERIAL_PH_BANDS = [
    (7.70, 4),   # >= 7.70
    (7.60, 3),   # 7.60 - 7.69
    (7.50, 1),   # 7.50 - 7.59
    (7.33, 0),   # 7.33 - 7.49
    (7.25, 2),   # 7.25 - 7.32
    (7.15, 3),   # 7.15 - 7.24
    (-999.0, 4), # < 7.15
]

SODIUM_BANDS = [
    (180.0, 4),  # >= 180
    (160.0, 3),  # 160 - 179
    (155.0, 2),  # 155 - 159
    (150.0, 1),  # 150 - 154
    (130.0, 0),  # 130 - 149
    (120.0, 2),  # 120 - 129
    (111.0, 3),  # 111 - 119
    (-999.0, 4), # <= 110
]

POTASSIUM_BANDS = [
    (7.0, 4),    # >= 7.0
    (6.0, 3),    # 6.0 - 6.9
    (5.5, 1),    # 5.5 - 5.9
    (3.5, 0),    # 3.5 - 5.4
    (3.0, 1),    # 3.0 - 3.4
    (2.5, 2),    # 2.5 - 2.9
    (-999.0, 4), # < 2.5
]

CREATININE_BANDS = [
    (3.5, 4),    # >= 3.5
    (2.0, 3),    # 2.0 - 3.4
    (1.5, 2),    # 1.5 - 1.9
    (0.6, 0),    # 0.6 - 1.4
    (-999.0, 2), # < 0.6
]

HEMATOCRIT_BANDS = [
    (60.0, 4),   # >= 60
    (50.0, 2),   # 50 - 59.9
    (46.0, 1),   # 46 - 49.9
    (30.0, 0),   # 30 - 45.9
    (20.0, 2),   # 20 - 29.9
    (-999.0, 4), # < 20
]

WBC_BANDS = [
    (40.0, 4),   # >= 40
    (20.0, 2),   # 20 - 39.9
    (15.0, 1),   # 15 - 19.9
    (3.0, 0),    # 3 - 14.9
    (1.0, 2),    # 1 - 2.9
    (-999.0, 4), # < 1
]

AGE_BANDS = [
    (75, 6),     # >= 75
    (65, 5),     # 65 - 74
    (55, 3),     # 55 - 64
    (45, 2),     # 45 - 54
    (-999, 0),   # < 45
]

# Diagnostic category weights for the Knaus mortality equation.
# Only a representative subset is included; the original paper has ~50 categories.
DIAGNOSTIC_WEIGHTS = {
    "nonoperative_respiratory": -2.108,
    "postoperative_respiratory": -1.368,
    "nonoperative_cardiovascular": -1.227,
    "postoperative_cardiovascular": -0.797,
    "neurologic": -1.228,
    "drug_overdose": -3.353,
    "diabetic_ketoacidosis": -1.507,
    "nonoperative_gi": 0.334,
    "postoperative_gi": -0.236,
    "sepsis": 0.113,
    "cardiogenic_shock": 0.393,
    "head_trauma": -0.517,
    "asthma_allergy": -2.108,
    "metabolic_renal": -0.196,
    "respiratory_insufficiency_after_surgery": -1.368,
    "multiple_trauma": -1.684,
    "craniotomy_for_tumor": -1.288,
}


def _band_score(value: float, bands: list) -> int:
    """Return the APACHE II points for *value* given an ordered band table."""
    for threshold, points in bands:
        if value >= threshold:
            return points
    return 0  # fallback (should never reach with -999 sentinel)


def score_temperature(temp_c: float) -> int:
    """Score body temperature in degrees Celsius."""
    return _band_score(temp_c, TEMPERATURE_BANDS)


def score_map(map_mmhg: float) -> int:
    """Score mean arterial pressure in mmHg."""
    return _band_score(map_mmhg, MAP_BANDS)


def score_heart_rate(hr: float) -> int:
    """Score heart rate in beats per minute."""
    return _band_score(hr, HEART_RATE_BANDS)


def score_respiratory_rate(rr: float) -> int:
    """Score respiratory rate in breaths per minute."""
    return _band_score(rr, RESPIRATORY_RATE_BANDS)


def score_oxygenation(pao2: Optional[float] = None,
                      fio2: Optional[float] = None,
                      paco2: float = 40.0,
                      atmospheric_pressure: float = 760.0) -> dict:
    """
    Score oxygenation.

    When FiO2 >= 0.5, uses the A-aDO2 gradient:
        A-aDO2 = FiO2 * (Patm - 47) - PaCO2 / 0.8 - PaO2

    When FiO2 < 0.5, uses PaO2 directly.

    Returns dict with keys: variable, value, points.
    """
    if fio2 is not None and fio2 >= 0.5 and pao2 is not None:
        a_ado2 = fio2 * (atmospheric_pressure - 47.0) - (paco2 / 0.8) - pao2
        pts = _band_score(a_ado2, A_ADO2_BANDS)
        return {"variable": "A-aDO2", "value": round(a_ado2, 1), "points": pts}
    if pao2 is not None:
        pts = _band_score(pao2, PAO2_BANDS)
        return {"variable": "PaO2", "value": pao2, "points": pts}
    return {"variable": "oxygenation", "value": None, "points": 0}


def score_arterial_ph(ph: float) -> int:
    """Score arterial blood pH."""
    return _band_score(ph, ARTERIAL_PH_BANDS)


def score_sodium(na: float) -> int:
    """Score serum sodium in mEq/L."""
    return _band_score(na, SODIUM_BANDS)


def score_potassium(k: float) -> int:
    """Score serum potassium in mEq/L."""
    return _band_score(k, POTASSIUM_BANDS)


def score_creatinine(cr: float, acute_renal_failure: bool = False) -> int:
    """
    Score serum creatinine in mg/dL.

    If acute renal failure (ARF) is present, points are doubled
    per the original Knaus scoring rules.
    """
    pts = _band_score(cr, CREATININE_BANDS)
    if pts >= 2 and acute_renal_failure:
        pts *= 2
    return pts


def score_hematocrit(hct: float) -> int:
    """Score hematocrit as a percentage."""
    return _band_score(hct, HEMATOCRIT_BANDS)


def score_wbc(wbc: float) -> int:
    """Score white blood cell count in thousands per mm^3."""
    return _band_score(wbc, WBC_BANDS)


def score_gcs(gcs: int) -> int:
    """
    Score Glasgow Coma Scale.

    APACHE II GCS component = 15 - actual GCS.
    """
    gcs = max(3, min(15, gcs))
    return 15 - gcs


def score_age(age_years: int) -> int:
    """Score patient age in years."""
    return _band_score(age_years, AGE_BANDS)


def score_chronic_health(nonoperative_or_emergency: bool,
                         elective_surgery: bool,
                         chronic_health_present: bool) -> int:
    """
    Score chronic health status.

    - Nonoperative or emergency postoperative with severe organ insufficiency
      or immunocompromised: +5
    - Elective postoperative with severe organ insufficiency
      or immunocompromised: +2
    - No chronic health condition: 0
    """
    if not chronic_health_present:
        return 0
    if elective_surgery:
        return 2
    return 5


# ---------------------------------------------------------------------------
# Main result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ApacheIIResult:
    """Complete APACHE II scoring result."""
    # Individual physiology component scores
    temperature_points: int
    map_points: int
    heart_rate_points: int
    respiratory_rate_points: int
    oxygenation_points: int
    oxygenation_detail: dict
    ph_points: int
    sodium_points: int
    potassium_points: int
    creatinine_points: int
    hematocrit_points: int
    wbc_points: int
    gcs_points: int

    # Subtotals
    acute_physiology_score: int  # sum of 12 physiology variables
    age_points: int
    chronic_health_points: int
    total_score: int             # 0-71

    # Mortality prediction
    predicted_mortality_pct: float

    # Input echo for verification
    inputs: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Primary calculation function
# ---------------------------------------------------------------------------

def apache_ii(
    temp_c: float,
    map_mmhg: float,
    hr: float,
    rr: float,
    ph: float,
    sodium: float,
    potassium: float,
    creatinine: float,
    hematocrit: float,
    wbc: float,
    gcs: int,
    age_years: int,
    chronic_health_present: bool,
    emergency_surgery: bool = False,
    elective_surgery: bool = False,
    acute_renal_failure: bool = False,
    pao2: Optional[float] = None,
    fio2: Optional[float] = None,
    paco2: float = 40.0,
    diagnosis: Optional[str] = None,
) -> ApacheIIResult:
    """
    Calculate the APACHE II score and predicted mortality.

    Parameters
    ----------
    temp_c : float
        Core body temperature in degrees Celsius.
    map_mmhg : float
        Mean arterial pressure in mmHg.
    hr : float
        Heart rate in beats per minute.
    rr : float
        Respiratory rate in breaths per minute.
    ph : float
        Arterial blood pH.
    sodium : float
        Serum sodium in mEq/L.
    potassium : float
        Serum potassium in mEq/L.
    creatinine : float
        Serum creatinine in mg/dL.
    hematocrit : float
        Hematocrit as a percentage.
    wbc : float
        White blood cell count in thousands/mm^3.
    gcs : int
        Glasgow Coma Scale (3-15).
    age_years : int
        Patient age in years.
    chronic_health_present : bool
        Whether severe organ insufficiency or immunocompromised status exists.
    emergency_surgery : bool
        Whether this is an emergency postoperative admission.
    elective_surgery : bool
        Whether this is an elective postoperative admission.
    acute_renal_failure : bool
        Whether acute renal failure is present (doubles creatinine points).
    pao2 : float, optional
        Arterial oxygen pressure in mmHg.
    fio2 : float, optional
        Fraction of inspired oxygen (0.21 - 1.0).
    paco2 : float
        Arterial CO2 pressure in mmHg (default 40, used for A-aDO2 calc).
    diagnosis : str, optional
        Diagnostic category key for mortality weight lookup.

    Returns
    -------
    ApacheIIResult
        Complete scoring breakdown and predicted mortality.
    """
    # Score each of the 12 acute physiology variables
    temp_pts = score_temperature(temp_c)
    map_pts = score_map(map_mmhg)
    hr_pts = score_heart_rate(hr)
    rr_pts = score_respiratory_rate(rr)
    ox = score_oxygenation(pao2=pao2, fio2=fio2, paco2=paco2)
    ox_pts = ox["points"]
    ph_pts = score_arterial_ph(ph)
    na_pts = score_sodium(sodium)
    k_pts = score_potassium(potassium)
    cr_pts = score_creatinine(creatinine, acute_renal_failure=acute_renal_failure)
    hct_pts = score_hematocrit(hematocrit)
    wbc_pts = score_wbc(wbc)
    gcs_pts = score_gcs(gcs)

    # Acute Physiology Score (APS)
    aps = (temp_pts + map_pts + hr_pts + rr_pts + ox_pts +
           ph_pts + na_pts + k_pts + cr_pts + hct_pts + wbc_pts + gcs_pts)

    # Age points
    age_pts = score_age(age_years)

    # Chronic health points
    ch_pts = score_chronic_health(
        nonoperative_or_emergency=(not elective_surgery),
        elective_surgery=elective_surgery,
        chronic_health_present=chronic_health_present,
    )

    # Total APACHE II score
    total = aps + age_pts + ch_pts

    # Predicted mortality using Knaus logistic equation
    logit = -3.517 + (total * 0.146)
    if emergency_surgery:
        logit += 0.603
    if diagnosis:
        logit += DIAGNOSTIC_WEIGHTS.get(diagnosis, 0.0)
    mortality = 1.0 / (1.0 + math.exp(-logit))
    mortality_pct = round(mortality * 100.0, 1)

    return ApacheIIResult(
        temperature_points=temp_pts,
        map_points=map_pts,
        heart_rate_points=hr_pts,
        respiratory_rate_points=rr_pts,
        oxygenation_points=ox_pts,
        oxygenation_detail=ox,
        ph_points=ph_pts,
        sodium_points=na_pts,
        potassium_points=k_pts,
        creatinine_points=cr_pts,
        hematocrit_points=hct_pts,
        wbc_points=wbc_pts,
        gcs_points=gcs_pts,
        acute_physiology_score=aps,
        age_points=age_pts,
        chronic_health_points=ch_pts,
        total_score=total,
        predicted_mortality_pct=mortality_pct,
        inputs={
            "temp_c": temp_c, "map_mmhg": map_mmhg, "hr": hr, "rr": rr,
            "ph": ph, "sodium": sodium, "potassium": potassium,
            "creatinine": creatinine, "hematocrit": hematocrit, "wbc": wbc,
            "gcs": gcs, "age_years": age_years,
            "chronic_health_present": chronic_health_present,
            "emergency_surgery": emergency_surgery,
            "elective_surgery": elective_surgery,
            "acute_renal_failure": acute_renal_failure,
            "pao2": pao2, "fio2": fio2, "paco2": paco2,
            "diagnosis": diagnosis,
        },
    )


def apache_ii_from_dict(params: dict) -> ApacheIIResult:
    """
    Convenience wrapper that accepts a dict of parameters.

    Useful for CSV batch processing. Keys match the parameter names of
    apache_ii() (with underscores). Missing optional keys use defaults.
    """
    # Map common aliases
    alias_map = {
        "temperature": "temp_c",
        "map": "map_mmhg",
        "heart_rate": "hr",
        "respiratory_rate": "rr",
        "arterial_ph": "ph",
        "na": "sodium",
        "k": "potassium",
        "cr": "creatinine",
        "hct": "hematocrit",
        "white_blood_cells": "wbc",
        "gcs_score": "gcs",
        "age": "age_years",
        "arf": "acute_renal_failure",
        "emerg": "emergency_surgery",
        "elective": "elective_surgery",
        "chronic": "chronic_health_present",
    }
    mapped = {}
    for k, v in params.items():
        key = alias_map.get(k, k)
        mapped[key] = v

    # Coerce types
    bool_keys = [
        "chronic_health_present", "emergency_surgery",
        "elective_surgery", "acute_renal_failure",
    ]
    int_keys = ["gcs", "age_years"]
    float_keys = [
        "temp_c", "map_mmhg", "hr", "rr", "ph", "sodium",
        "potassium", "creatinine", "hematocrit", "wbc",
        "pao2", "fio2", "paco2",
    ]

    for bk in bool_keys:
        if bk in mapped:
            v = mapped[bk]
            if isinstance(v, str):
                mapped[bk] = v.lower() in ("1", "true", "yes", "y")
            else:
                mapped[bk] = bool(v)

    for ik in int_keys:
        if ik in mapped:
            mapped[ik] = int(float(mapped[ik]))

    for fk in float_keys:
        if fk in mapped and mapped[fk] is not None and mapped[fk] != "":
            mapped[fk] = float(mapped[fk])

    # Remove empty strings for optional params
    for k in list(mapped.keys()):
        if mapped[k] == "" or mapped[k] is None:
            if k in ("pao2", "fio2", "paco2", "diagnosis"):
                mapped.pop(k, None)

    return apache_ii(**mapped)


# ---------------------------------------------------------------------------
# Severity classification helper
# ---------------------------------------------------------------------------

def severity_tier(score: int) -> str:
    """
    Return a human-readable severity tier for an APACHE II total score.

    These are approximate clinical groupings, not from the original paper:
        0-4:   Minimal
        5-9:   Low
        10-14: Moderate
        15-19: Moderately severe
        20-24: Severe
        25-29: Very severe
        30-34: Critical
        35+:   Extreme
    """
    if score <= 4:
        return "Minimal"
    elif score <= 9:
        return "Low"
    elif score <= 14:
        return "Moderate"
    elif score <= 19:
        return "Moderately severe"
    elif score <= 24:
        return "Severe"
    elif score <= 29:
        return "Very severe"
    elif score <= 34:
        return "Critical"
    else:
        return "Extreme"


# ---------------------------------------------------------------------------
# Self-test / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example: 67-year-old with sepsis
    result = apache_ii(
        temp_c=39.2, map_mmhg=68, hr=128, rr=34,
        ph=7.22, sodium=134, potassium=5.6, creatinine=2.8,
        hematocrit=28.0, wbc=21.0, gcs=13, age_years=67,
        chronic_health_present=False, emergency_surgery=False,
        pao2=58, fio2=0.4, diagnosis="sepsis",
    )
    print(f"APACHE II Total Score: {result.total_score}")
    print(f"  Acute Physiology Score: {result.acute_physiology_score}")
    print(f"  Age Points: {result.age_points}")
    print(f"  Chronic Health Points: {result.chronic_health_points}")
    print(f"  Predicted Mortality: {result.predicted_mortality_pct}%")
    print(f"  Severity: {severity_tier(result.total_score)}")
    print()
    print("Component breakdown:")
    print(f"  Temperature:    {result.temperature_points}")
    print(f"  MAP:            {result.map_points}")
    print(f"  Heart Rate:     {result.heart_rate_points}")
    print(f"  Resp Rate:      {result.respiratory_rate_points}")
    print(f"  Oxygenation:    {result.oxygenation_points} ({result.oxygenation_detail})")
    print(f"  pH:             {result.ph_points}")
    print(f"  Sodium:         {result.sodium_points}")
    print(f"  Potassium:      {result.potassium_points}")
    print(f"  Creatinine:     {result.creatinine_points}")
    print(f"  Hematocrit:     {result.hematocrit_points}")
    print(f"  WBC:            {result.wbc_points}")
    print(f"  GCS:            {result.gcs_points}")
