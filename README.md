# APACHE II Calculator

A Python implementation of the **APACHE II** (Acute Physiology and Chronic Health Evaluation II) scoring system for ICU mortality prediction.

Based on: Knaus WA, Draper EA, Wagner DP, Zimmerman JE. *APACHE II: a severity of disease classification system.* Crit Care Med. 1985;13(10):818-829.

## What This Does

Calculates the APACHE II score (0-71) from 12 acute physiology variables, age, and chronic health status, then estimates predicted hospital mortality using the Knaus logistic regression equation.

**This is a clinical reference calculator, not a medical device.** It is not FDA-cleared and must not be used as the sole basis for clinical decisions.

## Scoring Components

### 12 Acute Physiology Variables (each scored 0-4)

| Variable | Normal (0) | Scoring Range |
|---|---|---|
| Temperature (C) | 36.0 - 38.4 | 0 to +4 |
| Mean Arterial Pressure (mmHg) | 70 - 109 | 0 to +4 |
| Heart Rate (bpm) | 70 - 109 | 0 to +4 |
| Respiratory Rate (breaths/min) | 12 - 24 | 0 to +4 |
| Oxygenation (A-aDO2 or PaO2) | varies | 0 to +4 |
| Arterial pH | 7.33 - 7.49 | 0 to +4 |
| Serum Sodium (mEq/L) | 130 - 149 | 0 to +4 |
| Serum Potassium (mEq/L) | 3.5 - 5.4 | 0 to +4 |
| Serum Creatinine (mg/dL) | 0.6 - 1.4 | 0 to +4 (x2 if ARF) |
| Hematocrit (%) | 30 - 45.9 | 0 to +4 |
| WBC (x1000/mm3) | 3 - 14.9 | 0 to +4 |
| Glasgow Coma Scale | 15 - GCS | 0 to +12 |

### Additional Points

- **Age:** 0 (<45) to 6 (>=75)
- **Chronic Health:** +5 (nonoperative/emergency surgery) or +2 (elective surgery) if severe organ insufficiency or immunocompromised

### Mortality Prediction

```
ln(R/(1-R)) = -3.517 + (APACHE II x 0.146) + 0.603 (if emergency surgery) + diagnostic_category_weight
```

## Installation

No dependencies required. Python 3.8+ stdlib only.

```bash
git clone <repo-url>
cd apache-ii-calculator
```

## Usage

### CLI - Single Patient

```bash
python cli.py single \
    --temp 39.2 --map 68 --hr 128 --rr 34 \
    --ph 7.22 --sodium 134 --potassium 5.6 \
    --creatinine 2.8 --hematocrit 28.0 --wbc 21.0 \
    --gcs 13 --age 67 \
    --pao2 58 --fio2 0.4 \
    --diagnosis sepsis
```

Add `--json` for JSON output. Add `--arf` if acute renal failure is present (doubles creatinine points).

### CLI - Batch Processing

```bash
python cli.py batch --input patients.csv --output results.csv
```

CSV columns should match the parameter names (e.g., `temp_c`, `map_mmhg`, `hr`, `rr`, `ph`, `sodium`, `potassium`, `creatinine`, `hematocrit`, `wbc`, `gcs`, `age_years`, `chronic_health_present`, etc.).

### Python API

```python
from apache_ii import apache_ii, severity_tier

result = apache_ii(
    temp_c=39.2, map_mmhg=68, hr=128, rr=34,
    ph=7.22, sodium=134, potassium=5.6, creatinine=2.8,
    hematocrit=28.0, wbc=21.0, gcs=13, age_years=67,
    chronic_health_present=False, emergency_surgery=False,
    pao2=58, fio2=0.4, diagnosis="sepsis",
)

print(result.total_score)             # 26
print(result.predicted_mortality_pct) # ~56.9%
print(severity_tier(result.total_score))  # "Very severe"
```

## Running Tests

```bash
python -m pytest tests/test_apache_ii.py -v
```

## Project Structure

```
apache_ii.py          Core APACHE II scoring engine (stdlib only)
cli.py                Command-line interface
tests/
  test_apache_ii.py   Tests with hand-verified scoring examples
```

## Limitations

- The Knaus mortality equation uses a limited set of diagnostic category weights (a representative subset, not the full ~50 from the original paper).
- Mortality predictions are calibrated to 1980s ICU populations and may not reflect current outcomes.
- This tool does not account for treatment effects, ICU type, or institutional variation.
- Not validated for pediatric patients.

## License

MIT License. See [LICENSE](LICENSE).
