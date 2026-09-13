import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.utils.regex_extractor import (
    extract_bill_data,
    parse_percentage_value,
    parse_monetary_value,
    parse_date_value
)

def test_parse_percentage():
    assert parse_percentage_value("2.5%") == 2.5
    assert parse_percentage_value("2.5 per cent") == 2.5
    assert parse_percentage_value("two point five per cent") == 2.5
    assert parse_percentage_value("five per cent") == 5.0
    assert parse_percentage_value("5%") == 5.0
    assert parse_percentage_value("5 percent") == 5.0
    assert parse_percentage_value("fifty percent") == 50.0

def test_parse_monetary():
    assert parse_monetary_value("KES 10,000") == 10000.0
    assert parse_monetary_value("Kshs 500,000") == 500000.0
    assert parse_monetary_value("10 million shillings") == 10000000.0
    assert parse_monetary_value("5 billion Kenya shillings") == 5000000000.0
    assert parse_monetary_value("Ksh 2.5 million") == 2500000.0
    assert parse_monetary_value("500 shillings") == 500.0

def test_parse_date():
    assert parse_date_value("29th July 2026") == "2026-07-29"
    assert parse_date_value("July 29, 2026") == "2026-07-29"
    assert parse_date_value("2026-07-29") == "2026-07-29"
    assert parse_date_value("29/07/2026") == "2026-07-29"
    assert parse_date_value("29/07/26") == "2026-07-29"

def test_extract_bill_data():
    sample_text = (
        "THE MOTOR VEHICLE CIRCULATION TAX BILL, 2026. "
        "Imposed on 29th July 2026. The tax shall be charged at the rate of "
        "two point five per cent (2.5%) of the assessed value. "
        "If unpaid, a penalty equal to five per cent (5%) per month shall be charged. "
        "The minimum penalty shall be KES 10,000 or Ksh 5,000 depending on the model."
    )
    
    extractions = extract_bill_data(sample_text)
    
    # Verify we extracted all expected values
    types = [ext["type"] for ext in extractions]
    assert "date" in types
    assert "percentage" in types
    assert "monetary" in types
    
    # Check specific extractions
    date_exts = [e for e in extractions if e["type"] == "date"]
    assert len(date_exts) == 1
    assert date_exts[0]["value"] == "2026-07-29"
    assert date_exts[0]["raw"] == "29th July 2026"
    
    percent_exts = [e for e in extractions if e["type"] == "percentage"]
    # "two point five per cent" and "(2.5%)" might both match, let's verify both
    percent_values = [e["value"] for e in percent_exts]
    assert 2.5 in percent_values
    assert 5.0 in percent_values
    
    monetary_exts = [e for e in extractions if e["type"] == "monetary"]
    monetary_values = [e["value"] for e in monetary_exts]
    assert 10000.0 in monetary_values
    assert 5000.0 in monetary_values

def test_context_boundaries():
    sample_text = "A" * 300 + " 2.5% " + "B" * 300
    extractions = extract_bill_data(sample_text)
    assert len(extractions) == 1
    ext = extractions[0]
    
    # Context should be 400 + match length (404 characters)
    # ±200 characters surrounding
    assert len(ext["context"]) == 404
    assert ext["context"].startswith("A" * 199 + " ")
    assert ext["context"].endswith(" " + "B" * 199)

def test_parse_compound_percentages():
    assert parse_percentage_value("twenty-five percent") == 25.0
    assert parse_percentage_value("twenty five per cent") == 25.0
    assert parse_percentage_value("fifteen per cent") == 15.0
    assert parse_percentage_value("twenty-five point five percent") == 25.5
    
    # Test through extract_bill_data
    text = "The rate is twenty-five percent or thirty five per cent."
    extractions = extract_bill_data(text)
    assert len(extractions) == 2
    percent_vals = [e["value"] for e in extractions]
    assert 25.0 in percent_vals
    assert 35.0 in percent_vals

def test_edge_cases():
    # Empty string
    assert extract_bill_data("") == []
    
    # Text with zero matches
    assert extract_bill_data("This text contains no dates, percentages, or money values.") == []
    
    # Overlapping date and percent: e.g. "2026-07-29%" (should extract date, date has priority)
    # Note: date wins and overlap checker prevents percent from matching same span
    text = "On 2026-07-29 we had an event."
    extractions = extract_bill_data(text)
    assert len(extractions) == 1
    assert extractions[0]["type"] == "date"
    assert extractions[0]["value"] == "2026-07-29"

