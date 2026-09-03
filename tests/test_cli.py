"""
CLI and Batch Processing Unit Tests for APACHE II Calculator.
"""
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from cli import main, build_parser


def test_parser_build():
    parser = build_parser()
    assert parser is not None
    assert parser.prog == "apache-ii-calculator"


def test_cli_single_text(capsys):
    ret = main([
        "single",
        "--temp", "37.0",
        "--map", "85",
        "--hr", "80",
        "--rr", "16",
        "--ph", "7.40",
        "--sodium", "140",
        "--potassium", "4.0",
        "--creatinine", "1.0",
        "--hematocrit", "40.0",
        "--wbc", "8.0",
        "--gcs", "15",
        "--age", "30",
    ])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "APACHE II SCORE REPORT" in captured
    assert "Total Score:            0 / 71" in captured
    assert "Severity:               Minimal" in captured


def test_cli_single_json(capsys):
    ret = main([
        "single",
        "--temp", "39.2",
        "--map", "68",
        "--hr", "128",
        "--rr", "34",
        "--ph", "7.22",
        "--sodium", "134",
        "--potassium", "5.6",
        "--creatinine", "2.8",
        "--hematocrit", "28.0",
        "--wbc", "21.0",
        "--gcs", "13",
        "--age", "67",
        "--pao2", "58",
        "--fio2", "0.4",
        "--diagnosis", "sepsis",
        "--json",
    ])
    assert ret == 0
    captured = capsys.readouterr().out
    import json
    data = json.loads(captured)
    assert data["total_score"] == 29
    assert data["severity"] == "Very severe"
    assert abs(data["predicted_mortality_pct"] - 69.6) < 0.5


def test_cli_batch_csv(tmp_path):
    input_csv = tmp_path / "patients.csv"
    output_csv = tmp_path / "results.csv"

    # Write a 2-patient test CSV
    input_content = (
        "patient_id,temp_c,map_mmhg,hr,rr,pao2,fio2,ph,sodium,potassium,creatinine,acute_renal_failure,hematocrit,wbc,gcs,age_years,chronic_health_present,emergency_surgery,elective_surgery,diagnosis\n"
        "PT1,37.0,85,80,16,95,0.21,7.40,140,4.0,1.0,0,40.0,8.0,15,30,0,0,0,\n"
        "PT2,39.2,68,128,34,58,0.40,7.22,134,5.6,2.8,0,28.0,21.0,13,67,0,0,0,sepsis\n"
    )
    input_csv.write_text(input_content, encoding="utf-8")

    ret = main(["batch", "-i", str(input_csv), "-o", str(output_csv)])
    assert ret == 0
    assert output_csv.exists()

    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["patient_id"] == "PT1"
    assert rows[0]["apache_ii_score"] == "0"
    assert rows[0]["severity"] == "Minimal"

    assert rows[1]["patient_id"] == "PT2"
    assert rows[1]["apache_ii_score"] == "29"
    assert rows[1]["severity"] == "Very severe"


def test_cli_batch_sample_file(tmp_path):
    sample_path = Path(__file__).parent.parent / "sample.csv"
    assert sample_path.exists()

    output_csv = tmp_path / "sample_out.csv"
    ret = main(["batch", "--input", str(sample_path), "--output", str(output_csv)])
    assert ret == 0
    assert output_csv.exists()

    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 6
    for r in rows:
        assert r["apache_ii_score"] != "ERROR"
        assert int(r["apache_ii_score"]) >= 0
