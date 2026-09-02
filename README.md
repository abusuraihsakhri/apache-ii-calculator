# Apache II Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

APACHE II Calculator
APACHE II (0-71) from 12 physiologic variables, age and chronic health for ICU mortality.
Points-based score with tiered action thresholds. Stdlib only.

APACHE II Full Component Scoring + ICU Decision Modules.

Real APACHE II (Knaus 1985) implementation:
- 12 physiologic variables scored 0-4 from published band tables
- GCS points = 15 - GCS; creatinine doubled in acute renal failure
- Age points and chronic health points
- Knaus mortality equation: ln(R/(1-R)) = -3.517 + 0.146*score
  + diagnostic category weight + 0.603 if emergency surgery
Plus: ventilator weaning readiness (RSBI/NIF/SBT) and vasopressor tiering.
Stdlib only.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`ApacheResult`** — dedicated module for apache result evaluation and state verification.
- **`ApacheIIResult`**: Complete APACHE II scoring result.

---

## 📐 Mathematical Formulation & Logic

```text
  return calculate_score(present)
  res=calculate_score(present); print(res); return 0
  risk = ("low", "moderate", "high")[min(idx // 3, 2)]
  Calculate the APACHE II score and predicted mortality.
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --temp <value> --map <value> --hr <value> --rr <value>
```

### Parameter Reference
- `--temp`: Specifies input measurement or parameter value.
- `--map`: Specifies input measurement or parameter value.
- `--hr`: Specifies input measurement or parameter value.
- `--rr`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.
- `---`: Specifies input measurement or parameter value.
- `--ph`: Specifies input measurement or parameter value.
- `--sodium`: Specifies input measurement or parameter value.
- `--potassium`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `patient_id` | Parameter / observation metric | Required |
| `age` | Parameter / observation metric | Required |
| `sex` | Parameter / observation metric | Required |
| `prior_vte` | Parameter / observation metric | Required |
| `cancer` | Parameter / observation metric | Required |
| `immobility` | Parameter / observation metric | Required |
| `surgery` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t apache-ii-calculator .
docker run -p 8000:8000 apache-ii-calculator
```
