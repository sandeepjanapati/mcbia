import os
import requests
from dotenv import load_dotenv

# 1. Load the secrets from your .env file
load_dotenv()

# 2. Retrieve the API Key from the loaded secrets
# If this returns None, it means your .env file is missing or named wrong.
api_key = os.getenv("MONDAY_API_KEY")

# 3. Define the URL (The Door)
MONDAY_URL = "https://api.monday.com/v2"

# 4. Construct the Header Dictionary (The ID Card)
monday_headers = {
    "Authorization": api_key,
    "API-Version": "2026-01",       # As per your instruction
    "Content-Type": "application/json"
}

# --- TEST BLOCK (Delete this after it works) ---
# This checks if the key was loaded correctly.
if not api_key:
    print("❌ ERROR: API Key not found. Check your .env file.")
else:
    print("✅ SUCCESS: API Key loaded.")
    print(f"✅ Target Version: {monday_headers['API-Version']}")
# -----------------------------------------------

# --- STEP 3 CODE STARTS HERE ---

# 1. Load the Board IDs from the .env file
work_orders_id = os.getenv("WORK_ORDERS_BOARD_ID")
deals_id = os.getenv("DEALS_BOARD_ID")

def get_column_mapping(board_id):
    """
    Asks Monday.com for the column definitions of a specific board.
    Returns a dictionary: {'Human Name': 'machine_id'}
    """
    
    # The GraphQL Query
    query = f"""
    query {{
      boards (ids: [{board_id}]) {{
        columns {{
          title
          id
        }}
      }}
    }}
    """

    # Send the request
    response = requests.post(
        url=MONDAY_URL,
        headers=monday_headers, # Uses the header you built in Step 2
        json={'query': query}
    )

    # Convert response to JSON
    data = response.json()

    # Safety Check: Did the API return an error?
    if "errors" in data:
        print(f"❌ API Error: {data['errors']}")
        return {}

    # Extract the columns list
    # The structure is: data -> data -> boards -> [0] -> columns
    try:
        columns_data = data['data']['boards'][0]['columns']
    except (IndexError, KeyError, TypeError):
        print("❌ Error: Could not find board. Check your Board ID.")
        return {}

    # Build the Rosetta Stone (The Map)
    mapping_dict = {}
    for col in columns_data:
        human_name = col['title']
        machine_id = col['id']
        mapping_dict[human_name] = machine_id

    return mapping_dict

# --- EXECUTION ---
# This runs immediately to create your global maps.
print("mapping Work Orders columns...")
work_orders_map = get_column_mapping(work_orders_id)
print(f"✅ Work Orders Map: {work_orders_map}")

print("\nmapping Deals columns...")
deals_map = get_column_mapping(deals_id)
print(f"✅ Deals Map: {deals_map}")

# --- STEP 4 CODE STARTS HERE ---

import json # Ensure json is imported

def fetch_all_items(board_id, mapping_dict):
    """
    Retrieves ALL items from a board (handles pagination).
    Flattens the data using the provided mapping_dict.
    """
    
    # 1. Flip the map (We need ID -> Name to translate the API response)
    # Current Map: {'Revenue': 'numeric_123'}
    # New Map:     {'numeric_123': 'Revenue'}
    id_to_name_map = {v: k for k, v in mapping_dict.items()}
    
    all_items = []
    cursor = None # Start with no cursor
    
    print(f"🔄 Starting fetch for board {board_id}...")

    while True:
        # 2. Construct Query
        # If cursor is None, we send "null" (no quotes).
        # If cursor exists, we send "cursor_string" (with quotes).
        cursor_param = "null" if cursor is None else f'"{cursor}"'
        
        query = f"""
        query {{
          boards (ids: [{board_id}]) {{
            items_page (limit: 500, cursor: {cursor_param}) {{
              cursor
              items {{
                id
                name
                column_values {{
                  id
                  text
                }}
              }}
            }}
          }}
        }}
        """

        # 3. Send Request
        response = requests.post(
            url=MONDAY_URL,
            headers=monday_headers,
            json={'query': query}
        )
        
        data = response.json()
        
        # Error handling
        if "errors" in data:
            print(f"❌ Error fetching items: {data['errors']}")
            break
            
        # 4. Extract Data
        page_data = data['data']['boards'][0]['items_page']
        items = page_data['items']
        cursor = page_data['cursor'] # Update cursor for next loop

        # 5. FLATTEN THE DATA (Crucial Step)
        for item in items:
            # Create a clean row with just the Name and ID first
            clean_row = {
                "Item ID": item['id'],
                "Name": item['name'] # This maps to 'Deal Name' or 'Project Name'
            }
            
            # Loop through the raw columns and rename them
            for col_val in item['column_values']:
                col_id = col_val['id']
                col_text = col_val['text']
                
                # Look up the Human Name
                if col_id in id_to_name_map:
                    human_name = id_to_name_map[col_id]
                    clean_row[human_name] = col_text
            
            all_items.append(clean_row)

        # 6. Stop condition
        if not cursor:
            print("✅ Fetch complete. No more pages.")
            break
        else:
            print(f"   ...fetched {len(items)} items, getting next page...")

    return all_items

# --- STEP 5 CODE STARTS HERE: Data Processing Engine ---

import re
from datetime import datetime, date

# 1. Money Cleaner
def clean_money(value):
    """
    Converts string currency to float.
    Input: "264398.08", "$10,000", "", "10k", None
    Output: 264398.08 (float) or 0.0
    """
    if not value:
        return 0.0
    
    # Remove whitespace
    value = str(value).strip().lower()
    if value == "":
        return 0.0

    try:
        # Handle 'k' for thousands (e.g., "10k")
        multiplier = 1.0
        if 'k' in value:
            multiplier = 1000.0
            value = value.replace('k', '')
        
        # Remove common non-numeric chars (currency symbols, commas)
        # We keep digits, dots, and negative signs.
        clean_str = re.sub(r'[^\d.-]', '', value)
        
        if not clean_str:
            return 0.0
            
        return float(clean_str) * multiplier
    except ValueError:
        return 0.0

# 2. Quantity & Unit Extractor (Critical for "Messy" Data)
def parse_quantity_unit(value):
    """
    Extracts number and unit from strings like "5360 HA", "350 KM", "1250 towers".
    Input: "5360 HA"
    Output: (5360.0, "HA")
    """
    if not value:
        return 0.0, "Unknown"
    
    value = str(value).strip().upper()
    
    # Regex to find the number at the start
    # Matches: 123, 123.45, .45
    match = re.search(r'([-+]?\d*\.?\d+)', value)
    
    if match:
        number_str = match.group(1)
        number = float(number_str)
        
        # The "Unit" is whatever is left after the number
        # e.g. "5360 HA" -> remove "5360" -> "HA"
        unit = value.replace(number_str, '').strip()
        
        # Clean up the unit (remove extra chars)
        unit = re.sub(r'[^A-Z/]', '', unit) # Keep letters and slashes (L/S)
        
        if not unit:
            unit = "Count" # Default if just a number
            
        return number, unit
    
    return 0.0, "Unknown"

# 3. Date Cleaner (ISO Format)
def clean_date_iso(value):
    """
    Parses 'YYYY-MM-DD'. Returns a date object or None.
    """
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None

# 4. Fuzzy Month Cleaner
def clean_month_name(value, reference_year=2025):
    """
    Parses month names like "Dec", "November", "June" into a Date object.
    Assumption: Sets day to the last day of that month.
    Assumption: Uses reference_year (default 2025 based on your data).
    """
    if not value:
        return None
        
    value = str(value).strip().title() # Dec, November
    
    # Map short/long names to month numbers
    months = {
        'Jan': 1, 'January': 1,
        'Feb': 2, 'February': 2,
        'Mar': 3, 'March': 3,
        'Apr': 4, 'April': 4,
        'May': 5,
        'Jun': 6, 'June': 6,
        'Jul': 7, 'July': 7,
        'Aug': 8, 'August': 8,
        'Sep': 9, 'September': 9, 'Sept': 9,
        'Oct': 10, 'October': 10,
        'Nov': 11, 'November': 11,
        'Dec': 12, 'December': 12
    }
    
    # Check if the text starts with a month name
    for name, month_num in months.items():
        if value.startswith(name):
            # Found a month! Return the last day of that month
            # (Simple logic: just use 28th for safe mapping or 1st)
            return date(reference_year, month_num, 1)
            
    return None

# 5. Fiscal Quarter Calculator
def get_fiscal_quarter(date_obj):
    """
    Returns 'Q1', 'Q2', 'Q3', 'Q4' based on standard Fiscal Year (Apr-Mar) or Calendar (Jan-Dec).
    Let's assume Calendar Year (Jan-Mar = Q1) for simplicity unless specified.
    """
    if not date_obj:
        return "Unknown"
    
    month = date_obj.month
    if 1 <= month <= 3: return "Q1"
    if 4 <= month <= 6: return "Q2"
    if 7 <= month <= 9: return "Q3"
    return "Q4"

# --- EXECUTION TEST (You can delete this later) ---
print("\n🧪 Testing Data Processors...")
print(f"Money '264398.08': {clean_money('264398.08')}")
print(f"Money '10k': {clean_money('10k')}")
print(f"Quantity '5360 HA': {parse_quantity_unit('5360 HA')}")
print(f"Quantity '350 KM': {parse_quantity_unit('350 KM')}")
print(f"Quantity '4': {parse_quantity_unit('4')}")
print(f"Date 'Dec': {clean_month_name('Dec')}")

# --- STEP 6 CODE STARTS HERE: The BI Logic Tools ---

def calculate_work_orders_revenue(sector=None, status=None):
    """
    Calculates total revenue from Work Orders.
    Filters: sector (e.g., 'Mining'), status (e.g., 'Completed')
    """
    trace_log = ["[Tool: calculate_work_orders_revenue] Triggered."]
    caveats =[]
    
    # 1. Fetch Data
    trace_log.append(f"Fetching Work Orders from Monday.com API...")
    data = fetch_all_items(work_orders_id, work_orders_map)
    trace_log.append(f"Successfully fetched {len(data)} Work Orders.")
    
    total_revenue = 0.0
    matched_count = 0
    null_count = 0

    # 2. Process & Filter
    for row in data:
        row_sector = str(row.get('Sector', '')).strip().lower()
        row_status = str(row.get('Execution Status', '')).strip().lower()
        
        # Apply filters if provided
        if sector and sector.lower() not in row_sector:
            continue
        if status and status.lower() not in row_status:
            continue
            
        # 3. Clean and Calculate
        raw_amount = row.get('Amount in Rupees (Excl of GST) (Masked)', '')
        if not raw_amount or str(raw_amount).strip() == "":
            null_count += 1
            
        clean_amount = clean_money(raw_amount)
        total_revenue += clean_amount
        matched_count += 1

    # 4. Generate Caveats (Data Resilience)
    if null_count > 0:
        caveat_msg = f"Data Quality Warning: {null_count} matching work orders had missing/blank revenue values. They were treated as $0."
        caveats.append(caveat_msg)
        trace_log.append(caveat_msg)
        
    trace_log.append(f"Calculation complete. Summed {matched_count} records. Total: {total_revenue}")
    
    return {
        "metric": "Work Orders Revenue",
        "total_value": total_revenue,
        "records_analyzed": matched_count,
        "caveats": caveats,
        "trace": trace_log
    }

def analyze_deals_pipeline(stage=None, probability=None, sector=None):
    """
    Calculates the pipeline value from Deals.
    Filters: stage ('Open', 'Won', 'Dead'), probability ('High', 'Medium', 'Low'), sector ('Mining', etc)
    """
    trace_log = ["[Tool: analyze_deals_pipeline] Triggered."]
    caveats =[]
    
    trace_log.append(f"Fetching Deals from Monday.com API...")
    data = fetch_all_items(deals_id, deals_map)
    trace_log.append(f"Successfully fetched {len(data)} Deals.")
    
    pipeline_value = 0.0
    matched_count = 0
    null_count = 0

    for row in data:
        row_stage = str(row.get('Deal Status', '')).strip().lower()
        row_prob = str(row.get('Closure Probability', '')).strip().lower()
        row_sector = str(row.get('Sector/service', '')).strip().lower()
        
        # Apply filters
        if stage and stage.lower() not in row_stage: continue
        if probability and probability.lower() not in row_prob: continue
        if sector and sector.lower() not in row_sector: continue
            
        raw_value = row.get('Masked Deal value', '')
        if not raw_value or str(raw_value).strip() == "":
            null_count += 1
            
        pipeline_value += clean_money(raw_value)
        matched_count += 1

    if null_count > 0:
        caveats.append(f"{null_count} matching deals had missing values and were counted as $0.")
        
    trace_log.append(f"Pipeline calculation complete. Processed {matched_count} deals. Total Value: {pipeline_value}")
    
    return {
        "metric": "Pipeline Health",
        "total_value": pipeline_value,
        "records_analyzed": matched_count,
        "caveats": caveats,
        "trace": trace_log
    }

def summarize_operational_quantities(sector=None):
    """
    Aggregates the messy 'Quantity by Ops' column (e.g. groups HA, KM, Acres).
    """
    trace_log = ["[Tool: summarize_operational_quantities] Triggered."]
    caveats =[]
    
    trace_log.append("Fetching Work Orders API...")
    data = fetch_all_items(work_orders_id, work_orders_map)
    
    totals_by_unit = {}
    matched_count = 0
    missing_units_count = 0

    for row in data:
        row_sector = str(row.get('Sector', '')).strip().lower()
        if sector and sector.lower() not in row_sector:
            continue
            
        raw_qty = row.get('Quantity by Ops', '')
        number, unit = parse_quantity_unit(raw_qty)
        
        if number > 0:
            if unit not in totals_by_unit:
                totals_by_unit[unit] = 0.0
            totals_by_unit[unit] += number
            matched_count += 1
        else:
            missing_units_count += 1

    if missing_units_count > 0:
        caveats.append(f"Ignored {missing_units_count} work orders because quantity was missing or invalid.")

    trace_log.append(f"Aggregated {matched_count} operational quantities across {len(totals_by_unit)} unit types.")

    return {
        "metric": "Operational Quantities Delivered",
        "totals_by_unit": totals_by_unit,
        "records_analyzed": matched_count,
        "caveats": caveats,
        "trace": trace_log
    }

def calculate_sector_performance(sector_name):
    """
    CROSS-BOARD QUERY: Combines data from Deals AND Work Orders for a holistic view of a sector.
    """
    trace_log = [f"[Tool: calculate_sector_performance] Triggered for sector: {sector_name}"]
    
    trace_log.append("Querying Deals Board...")
    deals_data = analyze_deals_pipeline(sector=sector_name)
    
    trace_log.append("Querying Work Orders Board...")
    wo_data = calculate_work_orders_revenue(sector=sector_name)
    
    combined_trace = trace_log + deals_data['trace'] + wo_data['trace']
    combined_caveats = deals_data['caveats'] + wo_data['caveats']
    
    return {
        "metric": f"Total Sector Performance ({sector_name})",
        "deals_pipeline_value": deals_data['total_value'],
        "work_orders_revenue": wo_data['total_value'],
        "total_combined_value": deals_data['total_value'] + wo_data['total_value'],
        "caveats": combined_caveats,
        "trace": combined_trace
    }

# --- EXECUTION TEST ---
print("\n🧪 Testing BI Logic Tools...")

print("\n--- Testing Pipeline Health (High Probability) ---")
pipeline_res = analyze_deals_pipeline(probability="High")
print(f"Value: {pipeline_res['total_value']}")
print(f"Caveats: {pipeline_res['caveats']}")

print("\n--- Testing Operational Quantities (Mining) ---")
qty_res = summarize_operational_quantities(sector="Mining")
print(f"Totals by Unit: {qty_res['totals_by_unit']}")

print("\n--- Testing Cross-Board Sector Performance (Mining) ---")
sector_res = calculate_sector_performance("Mining")
print(f"Total Combined Value: {sector_res['total_combined_value']}")

# --- STEP 7: The AI Agent Layer (Gemini Version) ---

import google.generativeai as genai
from google.generativeai.types import content_types
from collections.abc import Iterable

# 1. Configure Gemini
google_key = os.getenv("GOOGLE_API_KEY")
if not google_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env")

genai.configure(api_key=google_key)

# 2. Define the Tool List (Gemini accepts the actual functions directly)
my_tools = [
    calculate_work_orders_revenue,
    analyze_deals_pipeline,
    summarize_operational_quantities,
    calculate_sector_performance
]

# 3. Initialize the Model with Tools and System Prompt
# We use 'gemini-flash-latest' because it is fast and cheap.
sys_prompt = """
You are an advanced Business Intelligence Agent for a Founder.
You have access to live Monday.com boards (Work Orders and Deals).

RULES:
1. ALWAYS use a tool to answer data questions. Do not hallucinate numbers.
2. If the user asks a vague question (e.g. "How are we doing?"), ASK CLARIFYING QUESTIONS or pick the 'calculate_sector_performance' tool.
3. If the data is messy (e.g. mixed units), mention this based on the tool's 'caveats' output.
4. Answer concisely based on the tool output.
"""

model = genai.GenerativeModel(
    'gemini-flash-latest',
    tools=my_tools,
    system_instruction=sys_prompt
)

# 4. Initialize Chat Session (Global Variable)
# enable_automatic_function_calling=True means Gemini will run the Python code for you.
chat_session = model.start_chat(enable_automatic_function_calling=True)

def run_agent_conversation(user_input, history_placeholder=None):
    """
    Manages the conversation flow with Gemini.
    """
    print(f"🤖 User asked: {user_input}")
    
    try:
        # Send message to Gemini
        # It will automatically:
        # 1. Detect if it needs a tool
        # 2. Call your Python function (printing the traces to your console)
        # 3. Get the result
        # 4. Generate the final text answer
        response = chat_session.send_message(user_input)
        
        return response.text, [] # We don't need to manually manage history list with Gemini object
        
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return "I encountered an error connecting to the AI brain.", []
