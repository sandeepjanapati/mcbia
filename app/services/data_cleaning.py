import re
from datetime import datetime, date


def clean_money(value):
    """
    Converts string currency to float.
    Input: "264398.08", "$10,000", "", "10k", None
    Output: 264398.08 (float) or 0.0
    """
    if not value:
        return 0.0

    value = str(value).strip().lower()
    if value == "":
        return 0.0

    try:
        multiplier = 1.0
        if "k" in value:
            multiplier = 1000.0
            value = value.replace("k", "")
        elif "m" in value:
            multiplier = 1000000.0
            value = value.replace("m", "")
        elif "cr" in value:
            multiplier = 10000000.0
            value = value.replace("cr", "")
        elif "l" in value:
            multiplier = 100000.0
            value = value.replace("l", "")

        clean_str = re.sub(r"[^\d.-]", "", value)
        if not clean_str:
            return 0.0

        return float(clean_str) * multiplier
    except ValueError:
        return 0.0


def parse_quantity_unit(value):
    """
    Extracts number and unit from strings like "5360 HA", "350 KM", "1250 towers".
    Input: "5360 HA"
    Output: (5360.0, "HA")
    """
    if not value:
        return 0.0, "Unknown"

    value = str(value).strip().upper()

    match = re.search(r"([-+]?\d*\.?\d+)", value)

    if match:
        number_str = match.group(1)
        number = float(number_str)

        unit = value.replace(number_str, "").strip()
        unit = re.sub(r"[^A-Z/]", "", unit)

        if not unit:
            unit = "Count"

        return number, unit

    return 0.0, "Unknown"


def clean_date_iso(value):
    """
    Parses 'YYYY-MM-DD'. Returns a date object or None.
    """
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def clean_month_name(value, reference_year=2026):
    """
    Parses month names like "Dec", "November", "June" into a Date object.
    Sets day to the 1st of that month, using reference_year.
    """
    if not value:
        return None

    value = str(value).strip().title()

    months = {
        "Jan": 1, "January": 1,
        "Feb": 2, "February": 2,
        "Mar": 3, "March": 3,
        "Apr": 4, "April": 4,
        "May": 5,
        "Jun": 6, "June": 6,
        "Jul": 7, "July": 7,
        "Aug": 8, "August": 8,
        "Sep": 9, "September": 9, "Sept": 9,
        "Oct": 10, "October": 10,
        "Nov": 11, "November": 11,
        "Dec": 12, "December": 12,
    }

    for name, month_num in months.items():
        if value.startswith(name):
            return date(reference_year, month_num, 1)

    return None


def get_fiscal_quarter(date_obj):
    """
    Returns 'Q1', 'Q2', 'Q3', 'Q4' based on Calendar Year (Jan-Mar = Q1).
    """
    if not date_obj:
        return "Unknown"

    month = date_obj.month
    if 1 <= month <= 3:
        return "Q1"
    if 4 <= month <= 6:
        return "Q2"
    if 7 <= month <= 9:
        return "Q3"
    return "Q4"


def parse_date_flexible(value):
    """
    Tries ISO date first, then month name. Returns (date_obj, quarter) tuple.
    """
    date_obj = clean_date_iso(value)
    if not date_obj:
        date_obj = clean_month_name(value)
    quarter = get_fiscal_quarter(date_obj)
    return date_obj, quarter