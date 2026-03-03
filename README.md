# Monday.com Business Intelligence Agent

An AI-powered Founder's Business Intelligence Assistant that answers complex queries about Revenue, Deal Pipeline, and Operational Metrics by integrating directly with Monday.com boards. 

Built to answer founder-level business intelligence queries natively, bridging the gap between raw board data and actionable insights.

## Features

- **Live Monday.com Integration**: Executes live GraphQL API queries against Work Orders and Deals boards on every request. Data is never cached or preloaded.
- **Data Resilience & Cleaning**: Normalizes inconsistent data formats (currencies, units, dates) and handles missing values gracefully.
- **6 Customized BI Tools**: 
  - `calculate_work_orders_revenue`
  - `analyze_deals_pipeline`
  - `summarize_operational_quantities`
  - `calculate_sector_performance`
  - `analyze_revenue_by_quarter`
  - `analyze_deals_timeline`
- **Real-time Trace Visibility**: See exactly which tools the AI is calling and what parameters it uses directly in the chat interface.
- **Conversational Memory**: Maintains chat history with an intuitive sidebar.

## Tech Stack

- **UI Framework**: Streamlit
- **AI Model**: Google Gemini 2.5 Flash (via `google-generativeai` SDK)
- **API Integration**: Python `requests` (GraphQL)

## Setup & Local Execution

### 1. Requirements

Ensure you have Python 3.9+ installed. Install the requirements:
```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root directory and populate it with the following:
```
MONDAY_API_KEY="your_monday_api_key_here"
GOOGLE_API_KEY="your_google_gemini_api_key_here"

WORK_ORDERS_BOARD_ID="your_work_orders_board_id"
DEALS_BOARD_ID="your_deals_board_id"
```

### 3. Run the App

Start the Streamlit application:
```bash
streamlit run run_app.py
```
