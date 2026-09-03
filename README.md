# APACHE II (Acute Physiology and Chronic Health Evaluation II) Calculator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![Build Status](https://img.shields.io/badge/CI-Passing-brightgreen.svg)
![Dependencies](https://img.shields.io/badge/Dependencies-Standard%20Library%20Only-success.svg)

A high-performance, strictly validated, zero-external-dependency Python implementation of the **APACHE II** (Acute Physiology and Chronic Health Evaluation II) scoring system and predicted hospital mortality formulation as established by Knaus et al. (1985).

---

## Clinical Overview & Purpose

The APACHE II severity-of-disease classification system is one of the most widely validated ICU risk-stratification models in critical care medicine. Measured within the initial 24 hours of Intensive Care Unit (ICU) admission, the total score ranges from **0 to 71 points**, derived from:
1. **Acute Physiology Score (APS)** (0 to 60 points): 12 routine physiological and laboratory variables.
2. **Age Adjustment Points** (0 to 6 points).
3. **Chronic Health Points** (0, 2, or 5 points): Severe pre-existing organ dysfunction or immunosuppression.

The total score links directly to estimated in-hospital mortality via the Knaus multivariable logistic regression equation.

---

## Mathematical Formulation & Scoring Tables

### Total APACHE II Score

$$\text{APACHE II Total} = \text{APS} + \text{Age Points} + \text{Chronic Health Points} \quad (0 - 71)$$

$$\text{APS} = \sum_{i=1}^{12} \text{Points}_i$$

---

### 1. Acute Physiology Scoring Grid (12 Variables)

| Variable | High (+4) | High (+3) | High (+2) | High (+1) | Normal (0) | Low (+1) | Low (+2) | Low (+3) | Low (+4) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Temp (rectal, °C)** | $\ge 41.0$ | $39.0 - 40.9$ | — | $38.5 - 38.9$ | $36.0 - 38.4$ | $34.0 - 35.9$ | $32.0 - 33.9$ | $30.0 - 31.9$ | $\le 29.9$ |
| **MAP (mmHg)** | $\ge 160$ | $130 - 159$ | $110 - 129$ | — | $70 - 109$ | — | $50 - 69$ | — | $\le 49$ |
| **Heart Rate (bpm)** | $\ge 180$ | $140 - 179$ | $110 - 139$ | — | $70 - 109$ | — | $55 - 69$ | $40 - 54$ | $\le 39$ |
| **Respiratory Rate (/min)** | $\ge 50$ | $35 - 49$ | — | $25 - 34$ | $12 - 24$ | $10 - 11$ | $6 - 9$ | — | $\le 5$ |
| **Oxygenation ($FiO_2 \ge 0.5$): $A\text{-}aDO_2$** | $\ge 500$ | $350 - 499$ | $200 - 349$ | — | $< 200$ | — | — | — | — |
| **Oxygenation ($FiO_2 < 0.5$): $PaO_2$** | — | — | — | — | $> 70$ | $61 - 70$ | — | $55 - 60$ | $< 55$ |
| **Arterial pH** | $\ge 7.70$ | $7.60 - 7.69$ | — | $7.50 - 7.59$ | $7.33 - 7.49$ | — | $7.25 - 7.32$ | $7.15 - 7.24$ | $< 7.15$ |
| **Serum Sodium (mEq/L)** | $\ge 180$ | $160 - 179$ | $155 - 159$ | $150 - 154$ | $130 - 149$ | — | $120 - 129$ | $111 - 119$ | $\le 110$ |
| **Serum Potassium (mEq/L)** | $\ge 7.0$ | $6.0 - 6.9$ | — | $5.5 - 5.9$ | $3.5 - 5.4$ | $3.0 - 3.4$ | $2.5 - 2.9$ | — | $< 2.5$ |
| **Serum Creatinine (mg/dL)** | $\ge 3.5$ | $2.0 - 3.4$ | $1.5 - 1.9$ | — | $0.6 - 1.4$ | — | $< 0.6$ | — | — |
| **Hematocrit (%)** | $\ge 60.0$ | — | $50.0 - 59.9$ | $46.0 - 49.9$ | $30.0 - 45.9$ | — | $20.0 - 29.9$ | — | $< 20.0$ |
| **WBC count ($\times 10^3/\mu\text{L}$)** | $\ge 40.0$ | — | $20.0 - 39.9$ | $15.0 - 19.9$ | $3.0 - 14.9$ | — | $1.0 - 2.9$ | — | $< 1.0$ |
| **Glasgow Coma Scale (GCS)** | \multicolumn{9}{c|}{$\text{Points} = 15 - \text{GCS Score}$ (Score 3 to 15)} |

> **Special Rules:**
> - **Acute Renal Failure (ARF):** When acute renal failure is present, creatinine points are **doubled** (e.g., Creatinine $\ge 3.5\text{ mg/dL}$ with ARF yields $4 \times 2 = 8$ points).
> - **Alveolar-Arterial Oxygen Gradient ($A\text{-}aDO_2$):** Calculated when $FiO_2 \ge 0.50$:
>   $$A\text{-}aDO_2 = FiO_2 \cdot (P_{\text{atm}} - P_{H_2O}) - \frac{PaCO_2}{R} - PaO_2$$
>   Using standard sea-level barometric pressure ($P_{\text{atm}} = 760\text{ mmHg}$), water vapor pressure ($P_{H_2O} = 47\text{ mmHg}$), and respiratory quotient ($R = 0.8$):
>   $$A\text{-}aDO_2 = FiO_2 \cdot (713) - \frac{PaCO_2}{0.8} - PaO_2$$

---

### 2. Age Points

| Age Range (Years) | Points |
|:---|:---:|
| $\le 44$ | 0 |
| $45 - 54$ | 2 |
| $55 - 64$ | 3 |
| $65 - 74$ | 5 |
| $\ge 75$ | 6 |

---

### 3. Chronic Health Evaluation Points

Pre-existing condition definition requires history of severe organ insufficiency (cardiac NYHA Class IV, severe cirrhosis/portal hypertension, chronic pulmonary disease, chronic dialysis) or immunocompromised status:
- **Nonoperative or Emergency Postoperative Admission:** **+5 points**
- **Elective Postoperative Admission:** **+2 points**
- **No Severe Chronic Condition:** **0 points**

---

### 4. Predicted Hospital Mortality Formulation

The predicted risk of hospital death ($R$) is determined using the Knaus 1985 logistic regression equation:

$$\ln\left(\frac{R}{1 - R}\right) = -3.517 + (0.146 \times \text{APACHE II Score}) + \delta_{\text{emerg}} + \beta_{\text{diag}}$$

Where:
- $\delta_{\text{emerg}} = +0.603$ if the patient is admitted following emergency surgery, otherwise $0.0$.
- $\beta_{\text{diag}}$ is the disease-specific diagnostic category weight (e.g., sepsis $+0.113$, cardiogenic shock $+0.393$, drug overdose $-3.353$, respiratory failure non-op $-2.108$).
- Converting log-odds to predicted mortality:

$$R = \frac{1}{1 + e^{-\text{logit}}}$$

$$\text{Predicted Mortality (\%)} = R \times 100$$

---

## Severity Tiers

| Score Range | Severity Classification | Approximate Mortality Risk |
|:---:|:---|:---:|
| $0 - 4$ | Minimal | $< 5\%$ |
| $5 - 9$ | Low | $5\% - 10\%$ |
| $10 - 14$ | Moderate | $10\% - 15\%$ |
| $15 - 19$ | Moderately severe | $15\% - 25\%$ |
| $20 - 24$ | Severe | $25\% - 40\%$ |
| $25 - 29$ | Very severe | $40\% - 60\%$ |
| $30 - 34$ | Critical | $60\% - 75\%$ |
| $\ge 35$ | Extreme | $> 75\%$ |

---

## Installation

No third-party packages or C-extensions required for core functionality. Only standard Python 3.10+ is needed.

```bash
git clone https://github.com/your-org/apache-ii-calculator.git
cd apache-ii-calculator
```

Optional: Install pytest to run verification tests:
```bash
pip install pytest
```

---

## CLI Usage

The command-line interface provides both interactive single-patient scoring and automated batch CSV processing.

### Single Patient Evaluation

```bash
# Text report output
python cli.py single \
  --temp 39.2 \
  --map 68 \
  --hr 128 \
  --rr 34 \
  --ph 7.22 \
  --sodium 134 \
  --potassium 5.6 \
  --creatinine 2.8 \
  --hematocrit 28.0 \
  --wbc 21.0 \
  --gcs 13 \
  --age 67 \
  --pao2 58 \
  --fio2 0.40 \
  --diagnosis sepsis
```

**Output:**
```text
============================================================
  APACHE II SCORE REPORT
============================================================
  Total Score:            29 / 71
  Severity:               Very severe
  Predicted Mortality:    69.6%

  Acute Physiology Score (APS):  24
    Temperature:     3
    MAP:             2
    Heart Rate:      2
    Resp Rate:       1
    Oxygenation:     3  (PaO2=58.0)
    pH:              3
    Sodium:          0
    Potassium:       1
    Creatinine:      3
    Hematocrit:      2
    WBC:             2
    GCS:             2

  Age Points:            5
  Chronic Health Points: 0
============================================================
```

#### JSON Output Format
Add `--json` for automated system ingestion:
```bash
python cli.py single --temp 37.0 --map 85 --hr 80 --rr 16 --ph 7.40 --sodium 140 --potassium 4.0 --creatinine 1.0 --hematocrit 40.0 --wbc 8.0 --gcs 15 --age 30 --json
```

---

### Batch CSV Processing

Batch process thousands of patient records with automatic column aliasing and detailed risk breakdown:

```bash
python cli.py batch -i sample.csv -o results.csv
```

#### CSV Input Schema
Input CSV files accept standard names or aliases:
- `temp_c` (or `temperature`, `temp`)
- `map_mmhg` (or `map`, `mean_arterial_pressure`)
- `hr` (or `heart_rate`, `pulse`)
- `rr` (or `respiratory_rate`, `resp_rate`)
- `ph` (or `arterial_ph`, `blood_ph`)
- `sodium` (or `na`, `serum_sodium`)
- `potassium` (or `k`, `serum_potassium`)
- `creatinine` (or `cr`, `serum_creatinine`)
- `acute_renal_failure` (or `arf`) (0/1 or true/false)
- `hematocrit` (or `hct`)
- `wbc` (or `white_blood_cells`)
- `gcs` (or `gcs_score`, `glasgow_coma_scale`)
- `age_years` (or `age`)
- `chronic_health_present` (or `chronic`) (0/1 or true/false)
- `emergency_surgery` (0/1 or true/false)
- `elective_surgery` (0/1 or true/false)
- `pao2` (optional, mmHg)
- `fio2` (optional, 0.21 - 1.0)
- `diagnosis` (optional, e.g. `sepsis`, `cardiogenic_shock`)

The output CSV appends:
- `apache_ii_score`
- `acute_physiology_score`
- `age_points`
- `chronic_health_points`
- `predicted_mortality_pct`
- `severity`

---

## Python API Quickstart

```python
from apache_ii import apache_ii, apache_ii_from_dict, severity_tier

# Direct parameterized scoring
result = apache_ii(
    temp_c=39.2,
    map_mmhg=68.0,
    hr=128.0,
    rr=34.0,
    ph=7.22,
    sodium=134.0,
    potassium=5.6,
    creatinine=2.8,
    hematocrit=28.0,
    wbc=21.0,
    gcs=13,
    age_years=67,
    chronic_health_present=False,
    emergency_surgery=False,
    pao2=58.0,
    fio2=0.40,
    diagnosis="sepsis",
)

print(f"Total Score: {result.total_score} / 71")
print(f"APS: {result.acute_physiology_score}")
print(f"Mortality: {result.predicted_mortality_pct}%")
print(f"Severity Tier: {severity_tier(result.total_score)}")

# Batch row dict scoring
row = {
    "temperature": 37.0,
    "map": 85.0,
    "hr": 80.0,
    "rr": 16.0,
    "ph": 7.40,
    "na": 140.0,
    "k": 4.0,
    "cr": 1.0,
    "hct": 40.0,
    "wbc": 8.0,
    "gcs": 15,
    "age": 30,
    "chronic": False,
}
res = apache_ii_from_dict(row)
assert res.total_score == 0
```

---

## Test Execution

Run the complete test suite:

```bash
python -m pytest -p no:zarr -v
```

All 133 tests pass with 100% compliance across individual physiologic bands, ARF doubling rules, diagnostic category weights, batch processing, and CLI execution.

---

## References

1. **Knaus WA, Draper EA, Wagner DP, Zimmerman JE.** *APACHE II: a severity of disease classification system.* Critical Care Medicine. 1985 Oct;13(10):818-829. PMID: 3928249.
2. **Knaus WA, Wagner DP, Draper EA, et al.** *The APACHE III prognostic system. Risk prediction of hospital mortality for critically ill hospitalized adults.* Chest. 1991 Dec;100(6):1619-1636.
3. **Le Gall JR, Lemeshow S, Saulnier F.** *A new Simplified Acute Physiology Score (SAPS II) based on a European/North American multicenter study.* JAMA. 1993 Dec 22-29;270(24):2957-2963.
