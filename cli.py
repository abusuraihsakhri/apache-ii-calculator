#!/usr/bin/env python3
"""
Command-line interface for the APACHE II Calculator.

Usage:
    python cli.py single --temp 39.2 --map 68 --hr 128 --rr 34 ...
    python cli.py batch  --input patients.csv --output results.csv

Stdlib only.
"""

import argparse
import csv
import json
import sys

from apache_ii import apache_ii, apache_ii_from_dict, severity_tier


def _format_result(result) -> str:
    """Format an ApacheIIResult as a human-readable summary."""
    lines = [
        "=" * 60,
        "  APACHE II SCORE REPORT",
        "=" * 60,
        f"  Total Score:            {result.total_score} / 71",
        f"  Severity:               {severity_tier(result.total_score)}",
        f"  Predicted Mortality:    {result.predicted_mortality_pct}%",
        "",
        "  Acute Physiology Score (APS):  {0}".format(result.acute_physiology_score),
        "    Temperature:     {0}".format(result.temperature_points),
        "    MAP:             {0}".format(result.map_points),
        "    Heart Rate:      {0}".format(result.heart_rate_points),
        "    Resp Rate:       {0}".format(result.respiratory_rate_points),
        "    Oxygenation:     {0}  ({1})".format(
            result.oxygenation_points,
            "{0}={1}".format(
                result.oxygenation_detail["variable"],
                result.oxygenation_detail["value"],
            ),
        ),
        "    pH:              {0}".format(result.ph_points),
        "    Sodium:          {0}".format(result.sodium_points),
        "    Potassium:       {0}".format(result.potassium_points),
        "    Creatinine:      {0}".format(result.creatinine_points),
        "    Hematocrit:      {0}".format(result.hematocrit_points),
        "    WBC:             {0}".format(result.wbc_points),
        "    GCS:             {0}".format(result.gcs_points),
        "",
        "  Age Points:            {0}".format(result.age_points),
        "  Chronic Health Points: {0}".format(result.chronic_health_points),
        "=" * 60,
    ]
    return "\n".join(lines)


def cmd_single(args):
    """Score a single patient from CLI arguments."""
    params = {
        "temp_c": args.temp,
        "map_mmhg": args.map,
        "hr": args.hr,
        "rr": args.rr,
        "ph": args.ph,
        "sodium": args.sodium,
        "potassium": args.potassium,
        "creatinine": args.creatinine,
        "hematocrit": args.hematocrit,
        "wbc": args.wbc,
        "gcs": args.gcs,
        "age_years": args.age,
        "chronic_health_present": args.chronic_health,
        "emergency_surgery": args.emergency_surgery,
        "elective_surgery": args.elective_surgery,
        "acute_renal_failure": args.arf,
    }

    # Optional parameters
    if args.pao2 is not None:
        params["pao2"] = args.pao2
    if args.fio2 is not None:
        params["fio2"] = args.fio2
    if args.paco2 is not None:
        params["paco2"] = args.paco2
    if args.diagnosis is not None:
        params["diagnosis"] = args.diagnosis

    result = apache_ii(**params)

    if args.json:
        out = {
            "total_score": result.total_score,
            "acute_physiology_score": result.acute_physiology_score,
            "age_points": result.age_points,
            "chronic_health_points": result.chronic_health_points,
            "predicted_mortality_pct": result.predicted_mortality_pct,
            "severity": severity_tier(result.total_score),
            "components": {
                "temperature": result.temperature_points,
                "map": result.map_points,
                "heart_rate": result.heart_rate_points,
                "respiratory_rate": result.respiratory_rate_points,
                "oxygenation": result.oxygenation_points,
                "ph": result.ph_points,
                "sodium": result.sodium_points,
                "potassium": result.potassium_points,
                "creatinine": result.creatinine_points,
                "hematocrit": result.hematocrit_points,
                "wbc": result.wbc_points,
                "gcs": result.gcs_points,
            },
            "oxygenation_detail": result.oxygenation_detail,
            "inputs": result.inputs,
        }
        print(json.dumps(out, indent=2))
    else:
        print(_format_result(result))

    return 0


def cmd_batch(args):
    """Score multiple patients from a CSV file."""
    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + [
        "apache_ii_score", "acute_physiology_score",
        "age_points", "chronic_health_points",
        "predicted_mortality_pct", "severity",
    ]
    out_rows = []

    for row in rows:
        try:
            result = apache_ii_from_dict(row)
            row_out = dict(row)
            row_out["apache_ii_score"] = result.total_score
            row_out["acute_physiology_score"] = result.acute_physiology_score
            row_out["age_points"] = result.age_points
            row_out["chronic_health_points"] = result.chronic_health_points
            row_out["predicted_mortality_pct"] = result.predicted_mortality_pct
            row_out["severity"] = severity_tier(result.total_score)
            out_rows.append(row_out)
        except Exception as e:
            row_out = dict(row)
            row_out["apache_ii_score"] = "ERROR"
            row_out["acute_physiology_score"] = str(e)
            row_out["age_points"] = ""
            row_out["chronic_health_points"] = ""
            row_out["predicted_mortality_pct"] = ""
            row_out["severity"] = ""
            out_rows.append(row_out)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {args.output}")
    return 0


def build_parser():
    """Build the argument parser."""
    p = argparse.ArgumentParser(
        prog="apache-ii-calculator",
        description="APACHE II (Acute Physiology and Chronic Health Evaluation II) Calculator",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # --- single patient ---
    s = sub.add_parser("single", help="Score a single patient")
    s.add_argument("--temp", type=float, required=True, help="Temperature (C)")
    s.add_argument("--map", type=float, required=True, help="Mean arterial pressure (mmHg)")
    s.add_argument("--hr", type=float, required=True, help="Heart rate (bpm)")
    s.add_argument("--rr", type=float, required=True, help="Respiratory rate (breaths/min)")
    s.add_argument("--ph", type=float, required=True, help="Arterial pH")
    s.add_argument("--sodium", type=float, required=True, help="Serum sodium (mEq/L)")
    s.add_argument("--potassium", type=float, required=True, help="Serum potassium (mEq/L)")
    s.add_argument("--creatinine", type=float, required=True, help="Serum creatinine (mg/dL)")
    s.add_argument("--hematocrit", type=float, required=True, help="Hematocrit (%%)")
    s.add_argument("--wbc", type=float, required=True, help="WBC (x1000/mm3)")
    s.add_argument("--gcs", type=int, required=True, help="Glasgow Coma Scale (3-15)")
    s.add_argument("--age", type=int, required=True, help="Age (years)")
    s.add_argument("--chronic-health", action="store_true", help="Chronic health present")
    s.add_argument("--emergency-surgery", action="store_true", help="Emergency surgery")
    s.add_argument("--elective-surgery", action="store_true", help="Elective surgery")
    s.add_argument("--arf", action="store_true", help="Acute renal failure (doubles creatinine pts)")
    s.add_argument("--pao2", type=float, help="PaO2 (mmHg)")
    s.add_argument("--fio2", type=float, help="FiO2 (0.0-1.0)")
    s.add_argument("--paco2", type=float, help="PaCO2 (mmHg, default 40)")
    s.add_argument("--diagnosis", type=str, help="Diagnostic category for mortality weight")
    s.add_argument("--json", action="store_true", help="Output as JSON")

    # --- batch ---
    b = sub.add_parser("batch", help="Batch process CSV file")
    b.add_argument("-i", "--input", required=True, help="Input CSV path")
    b.add_argument("-o", "--output", default="results.csv", help="Output CSV path")

    return p


def main(argv=None):
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "single":
        return cmd_single(args)
    elif args.cmd == "batch":
        return cmd_batch(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
