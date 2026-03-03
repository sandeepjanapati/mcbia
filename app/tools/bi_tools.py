from app.config import Config
from app.services.monday_api import MondayClient
from app.services.data_cleaning import (
    clean_money,
    parse_quantity_unit,
    parse_date_flexible,
)

def _get_client():
    """Instantiates a fresh client and fetches column mappings WITHOUT caching, as per requirements."""
    client = MondayClient()
    wo_map = client.get_column_mapping(Config.WORK_ORDERS_BOARD_ID)
    deals_map = client.get_column_mapping(Config.DEALS_BOARD_ID)
    return client, wo_map, deals_map


def calculate_work_orders_revenue(sector=None, status=None):
    """Calculates realized revenue from Work Orders. Optionally filter by sector and execution status."""
    trace = ["[Tool: calculate_work_orders_revenue] Started."]
    client, wo_map, _ = _get_client()
    data = client.fetch_all_items(Config.WORK_ORDERS_BOARD_ID, wo_map)
    trace.append(f"Fetched {len(data)} rows from Work Orders board.")

    total = 0.0
    matched = 0
    nulls = 0

    for row in data:
        r_sec = str(row.get("Sector", "")).strip().lower()
        r_stat = str(row.get("Execution Status", "")).strip().lower()

        if sector and sector.lower() not in r_sec:
            continue
        if status and status.lower() not in r_stat:
            continue

        raw_val = row.get("Amount in Rupees (Excl of GST) (Masked)", "")
        if not raw_val:
            nulls += 1
        total += clean_money(raw_val)
        matched += 1

    if sector:
        trace.append(f"Filtered by sector: '{sector}'")
    if status:
        trace.append(f"Filtered by status: '{status}'")
    trace.append(f"Matched {matched} records ({nulls} had empty revenue).")
    trace.append(f"Total Revenue: ₹{total:,.2f}")
    return {"metric": "WO Revenue", "total_value": total, "matched": matched, "nulls": nulls, "trace": trace}


def analyze_deals_pipeline(stage=None, probability=None, sector=None):
    """Calculates pipeline value from Deals. Optionally filter by deal stage, closure probability, or sector."""
    trace = ["[Tool: analyze_deals_pipeline] Started."]
    client, _, deals_map = _get_client()
    data = client.fetch_all_items(Config.DEALS_BOARD_ID, deals_map)
    trace.append(f"Fetched {len(data)} rows from Deals board.")

    total = 0.0
    matched = 0

    for row in data:
        r_stage = str(row.get("Deal Status", "")).strip().lower()
        r_prob = str(row.get("Closure Probability", "")).strip().lower()
        r_sec = str(row.get("Sector/service", "")).strip().lower()

        if stage and stage.lower() not in r_stage:
            continue
        if probability and probability.lower() not in r_prob:
            continue
        if sector and sector.lower() not in r_sec:
            continue

        total += clean_money(row.get("Masked Deal value", ""))
        matched += 1

    if stage:
        trace.append(f"Filtered by stage: '{stage}'")
    if probability:
        trace.append(f"Filtered by probability: '{probability}'")
    if sector:
        trace.append(f"Filtered by sector: '{sector}'")
    trace.append(f"Matched {matched} deals. Pipeline Value: ₹{total:,.2f}")
    return {"metric": "Pipeline Value", "total_value": total, "matched": matched, "trace": trace}


def summarize_operational_quantities(sector=None):
    """Aggregates operational quantities (HA, KM, etc) from Work Orders. Optionally filter by sector."""
    trace = ["[Tool: summarize_operational_quantities] Started."]
    client, wo_map, _ = _get_client()
    data = client.fetch_all_items(Config.WORK_ORDERS_BOARD_ID, wo_map)
    trace.append(f"Fetched {len(data)} rows from Work Orders board.")
    totals = {}

    for row in data:
        if sector and sector.lower() not in str(row.get("Sector", "")).lower():
            continue
        val, unit = parse_quantity_unit(row.get("Quantity by Ops", ""))
        if val > 0:
            totals[unit] = totals.get(unit, 0.0) + val

    if sector:
        trace.append(f"Filtered by sector: '{sector}'")
    trace.append(f"Aggregated into {len(totals)} unit types.")
    return {"metric": "Ops Quantities", "totals": totals, "trace": trace}


def calculate_sector_performance(sector_name):
    """Cross-board analysis for a specific sector. Combines deal pipeline and work order revenue."""
    trace = [f"[Tool: calculate_sector_performance] Analyzing sector: {sector_name}"]
    deals = analyze_deals_pipeline(sector=sector_name)
    wo = calculate_work_orders_revenue(sector=sector_name)

    return {
        "metric": f"Sector Performance ({sector_name})",
        "pipeline": deals["total_value"],
        "revenue": wo["total_value"],
        "total": deals["total_value"] + wo["total_value"],
        "deals_matched": deals["matched"],
        "wo_matched": wo["matched"],
        "trace": trace + deals["trace"] + wo["trace"],
    }


def analyze_revenue_by_quarter(sector=None, status=None):
    """Breaks down Work Order revenue by fiscal quarter, using date columns. Optionally filter by sector and status."""
    trace = ["[Tool: analyze_revenue_by_quarter] Started."]
    client, wo_map, _ = _get_client()
    data = client.fetch_all_items(Config.WORK_ORDERS_BOARD_ID, wo_map)
    trace.append(f"Fetched {len(data)} rows from Work Orders board.")

    quarterly = {}
    no_date_count = 0

    date_columns = ["Expected Delivery Date", "Timeline", "Date", "Completion Date", "Start Date"]

    for row in data:
        r_sec = str(row.get("Sector", "")).strip().lower()
        r_stat = str(row.get("Execution Status", "")).strip().lower()

        if sector and sector.lower() not in r_sec:
            continue
        if status and status.lower() not in r_stat:
            continue

        date_obj = None
        quarter = "Unknown"
        for col in date_columns:
            raw_date = row.get(col, "")
            if raw_date:
                date_obj, quarter = parse_date_flexible(raw_date)
                if date_obj:
                    break

        revenue = clean_money(row.get("Amount in Rupees (Excl of GST) (Masked)", ""))

        if quarter == "Unknown":
            no_date_count += 1

        if quarter not in quarterly:
            quarterly[quarter] = {"revenue": 0.0, "count": 0}
        quarterly[quarter]["revenue"] += revenue
        quarterly[quarter]["count"] += 1

    if sector:
        trace.append(f"Filtered by sector: '{sector}'")
    if status:
        trace.append(f"Filtered by status: '{status}'")
    trace.append(f"{no_date_count} rows had no parseable date (grouped under 'Unknown').")
    for q, vals in sorted(quarterly.items()):
        trace.append(f"  {q}: ₹{vals['revenue']:,.2f} ({vals['count']} orders)")

    return {"metric": "Quarterly WO Revenue", "quarterly_breakdown": quarterly, "trace": trace}


def analyze_deals_timeline(stage=None, sector=None):
    """Breaks down Deals pipeline by fiscal quarter, using date columns. Optionally filter by stage or sector."""
    trace = ["[Tool: analyze_deals_timeline] Started."]
    client, _, deals_map = _get_client()
    data = client.fetch_all_items(Config.DEALS_BOARD_ID, deals_map)
    trace.append(f"Fetched {len(data)} rows from Deals board.")

    quarterly = {}
    no_date_count = 0

    date_columns = ["Expected Closure Date", "Timeline", "Date", "Close Date", "Expected Date"]

    for row in data:
        r_stage = str(row.get("Deal Status", "")).strip().lower()
        r_sec = str(row.get("Sector/service", "")).strip().lower()

        if stage and stage.lower() not in r_stage:
            continue
        if sector and sector.lower() not in r_sec:
            continue

        date_obj = None
        quarter = "Unknown"
        for col in date_columns:
            raw_date = row.get(col, "")
            if raw_date:
                date_obj, quarter = parse_date_flexible(raw_date)
                if date_obj:
                    break

        deal_val = clean_money(row.get("Masked Deal value", ""))

        if quarter == "Unknown":
            no_date_count += 1

        if quarter not in quarterly:
            quarterly[quarter] = {"pipeline_value": 0.0, "count": 0}
        quarterly[quarter]["pipeline_value"] += deal_val
        quarterly[quarter]["count"] += 1

    if stage:
        trace.append(f"Filtered by stage: '{stage}'")
    if sector:
        trace.append(f"Filtered by sector: '{sector}'")
    trace.append(f"{no_date_count} deals had no parseable date (grouped under 'Unknown').")
    for q, vals in sorted(quarterly.items()):
        trace.append(f"  {q}: ₹{vals['pipeline_value']:,.2f} ({vals['count']} deals)")

    return {"metric": "Quarterly Deals Timeline", "quarterly_breakdown": quarterly, "trace": trace}