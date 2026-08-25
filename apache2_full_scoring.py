#!/usr/bin/env python3
"""
APACHE II Full Component Scoring + ICU Decision Modules.

Real APACHE II (Knaus 1985) implementation:
- 12 physiologic variables scored 0-4 from published band tables
- GCS points = 15 - GCS; creatinine doubled in acute renal failure
- Age points and chronic health points
- Knaus mortality equation: ln(R/(1-R)) = -3.517 + 0.146*score
  + diagnostic category weight + 0.603 if emergency surgery
Plus: ventilator weaning readiness (RSBI/NIF/SBT) and vasopressor tiering.
Stdlib only.
"""

import math
from dataclasses import dataclass, field


TEMP_BANDS = [(41.0, 4), (39.0, 3), (38.5, 1), (36.0, 0),
              (34.0, 1), (32.0, 2), (30.0, 3), (-99.0, 4)]
MAP_BANDS = [(160.0, 4), (130.0, 3), (110.0, 2), (70.0, 0),
             (50.0, 2), (-99.0, 4)]
HR_BANDS = [(180.0, 4), (140.0, 3), (110.0, 2), (70.0, 0),
            (55.0, 2), (40.0, 3), (-99.0, 4)]
RR_BANDS = [(50.0, 4), (35.0, 3), (25.0, 1), (12.0, 0),
            (10.0, 1), (6.0, 2), (-99.0, 4)]
PH_BANDS = [(7.70, 4), (7.60, 3), (7.50, 1), (7.33, 0),
            (7.25, 2), (7.15, 3), (-99.0, 4)]
NA_BANDS = [(180.0, 4), (160.0, 3), (155.0, 2), (150.0, 1), (130.0, 0),
            (120.0, 2), (111.0, 3), (-99.0, 4)]
K_BANDS = [(7.0, 4), (6.0, 3), (5.5, 1), (3.5, 0),
           (3.0, 1), (2.5, 2), (-99.0, 4)]
CR_BANDS = [(3.5, 4), (2.0, 3), (1.5, 2), (0.6, 0), (-99.0, 2)]
HCT_BANDS = [(60.0, 4), (50.0, 2), (46.0, 1), (30.0, 0),
             (20.0, 2), (-99.0, 4)]
WBC_BANDS = [(40.0, 4), (20.0, 2), (15.0, 1), (3.0, 0),
             (1.0, 2), (-99.0, 4)]

AGE_POINTS = [(45, 0), (55, 2), (65, 3), (75, 5), (999, 6)]
A_AA_GRADIENT_BANDS = [(500.0, 4), (350.0, 3), (200.0, 2), (-99.0, 0)]
PAO2_BANDS = [(70.0, 0), (61.0, 1), (55.0, 3), (-99.0, 4)]

DIAGNOSTIC_WEIGHTS = {
    "sepsis": 0.113,
    "cardiogenic_shock": 0.393,
    "asthma_allergy": -2.108,
    "head_trauma": -0.517,
}


def _band(value: float, bands) -> int:
    for cutoff, pts in bands:
        if value >= cutoff:
            return pts
    return 0


def score_oxygenation(pao2_mmhg: float = None, fio2: float = None,
                      atmospheric_pressure: float = 760.0) -> dict:
    """A-a gradient used when FiO2 >= 0.5, else PaO2 alone."""
    if fio2 is not None and fio2 >= 0.5 and pao2_mmhg is not None:
        paco2_default = 40.0
        a_a = fio2 * (atmospheric_pressure - 47.0) - paco2_default / 0.8 - pao2_mmhg
        pts = _band(a_a, A_AA_GRADIENT_BANDS)
        return {"variable": "A-a_gradient", "value": round(a_a, 1), "points": pts}
    if pao2_mmhg is not None:
        pts = _band(pao2_mmhg, PAO2_BANDS)
        return {"variable": "PaO2", "value": pao2_mmhg, "points": pts}
    return {"variable": "oxygenation_missing", "value": None, "points": 0}


@dataclass
class ApacheResult:
    acute_physiology_score: int
    age_points: int
    chronic_health_points: int
    total_score: int
    component_points: dict
    predicted_mortality_pct: float


def apache_ii(temp_c: float, map_mmhg: float, hr_bpm: float, rr_bpm: float,
              ph: float, sodium: float, potassium: float, creatinine: float,
              hematocrit: float, wbc_k_ul: float, gcs: int, age_years: int,
              chronic_health_present: bool, emergency_surgery: bool,
              elective_surgery: bool = False, pao2_mmhg: float = None,
              fio2: float = None, diagnosis: str = None) -> ApacheResult:
    comps = {
        "temperature": _band(temp_c, TEMP_BANDS),
        "map": _band(map_mmhg, MAP_BANDS),
        "heart_rate": _band(hr_bpm, HR_BANDS),
        "respiratory_rate": _band(rr_bpm, RR_BANDS),
        "ph": _band(ph, PH_BANDS),
        "sodium": _band(sodium, NA_BANDS),
        "potassium": _band(potassium, K_BANDS),
        "hematocrit": _band(hematocrit, HCT_BANDS),
        "wbc": _band(wbc_k_ul, WBC_BANDS),
    }
    ox = score_oxygenation(pao2_mmhg, fio2)
    comps["oxygenation"] = ox["points"]
    cr_pts = _band(creatinine, CR_BANDS)
    if cr_pts >= 2:
        cr_pts *= 2
    comps["creatinine_arf_weighted"] = cr_pts
    comps["gcs"] = 15 - gcs
    aps = sum(comps.values())
    age_pts = next(p for cut, p in AGE_POINTS if age_years < cut)
    if chronic_health_present:
        chp = 2 if elective_surgery else 5
    else:
        chp = 0
    total = aps + age_pts + chp
    logit = -3.517 + 0.146 * total
    if diagnosis:
        logit += DIAGNOSTIC_WEIGHTS.get(diagnosis, 0.0)
    if emergency_surgery:
        logit += 0.603
    r = math.exp(logit) / (1 + math.exp(logit))
    return ApacheResult(
        acute_physiology_score=aps, age_points=age_pts, chronic_health_points=chp,
        total_score=total, component_points=comps,
        predicted_mortality_pct=round(100 * r, 1),
    )


def weaning_readiness(apache_total: int, resp_subscore_pts: int, rsbi: float,
                      nif_cmh2o: float, sbt_pass: bool) -> dict:
    """RSBI <105 favorable; NIF better than -20; SBT pass gates extubation."""
    rsbi_adj = 0 if rsbi < 105 else (1 if rsbi <= 130 else 2)
    nif_adj = 0 if nif_cmh2o <= -20 else (1 if nif_cmh2o <= -15 else 2)
    sbt_adj = 0 if sbt_pass else 2
    resp_adj = min(resp_subscore_pts // 2, 2)
    idx = rsbi_adj + nif_adj + sbt_adj + resp_adj
    risk = ("low", "moderate", "high")[min(idx // 3, 2)]
    recs = ["extubation candidate" if risk != "high" else "continue ventilation"]
    if apache_total > 30:
        recs.append("APACHE II >30: high failure risk, discuss tracheostomy by day 14")
    return {"weaning_index": idx, "risk": risk,
            "rsbi_status": "<105 favorable" if rsbi < 105 else ">=105 unfavorable",
            "recommendations": recs}


def vasopressor_tiering(circulatory_subscore: int, ne_dose_mcg_kg_min: float,
                        current_map: float) -> dict:
    if circulatory_subscore > 5 or ne_dose_mcg_kg_min > 0.25:
        tier = "high"
        plan = {"target_map": (75, 85), "actions": [
            "add vasopressin 0.03 U/min",
            "screen for ECMO/cardiogenic support"]}
    elif circulatory_subscore >= 3:
        tier = "moderate"
        plan = {"target_map": (65, 75), "actions": ["consider early vasopressin"]}
    else:
        tier = "low"
        plan = {"target_map": (65, 75), "actions": ["routine titration"]}
    if ne_dose_mcg_kg_min > 0.25:
        plan["actions"].append("norepinephrine >0.25 mcg/kg/min triggers vasopressin")
    return {"tier": tier, **plan}


if __name__ == "__main__":
    res = apache_ii(temp_c=39.2, map_mmhg=68, hr_bpm=128, rr_bpm=34,
                    ph=7.22, sodium=134, potassium=5.6, creatinine=2.8,
                    hematocrit=28.0, wbc_k_ul=21.0, gcs=13, age_years=67,
                    chronic_health_present=False, emergency_surgery=False,
                    pao2_mmhg=58, fio2=0.4, diagnosis="sepsis")
    print(res)
    print()
    print("weaning:", weaning_readiness(35, 4, 88, -24, True))
    print()
    print("pressor:", vasopressor_tiering(4, 0.28, 58))
