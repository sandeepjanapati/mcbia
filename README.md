# Monday.com Business Intelligence Agent

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![Gemini](https://img.shields.io/badge/AI-Gemini_2.5_Flash-orange.svg)

## 📌 Overview
The **Monday.com Business Intelligence Agent** is an advanced AI-driven analytical backend designed to process and reason over live business data. Operating as a founder-level BI assistant, the application interfaces directly with Monday.com to ingest structured deals, operational tasks, and revenue timelines. Using the Google Gemini 2.5 Flash model alongside a tailored suite of analytical tools, it delivers actionable, real-time business insights through a conversational, multi-turn Streamlit interface.

---

## 🚀 Key Features
* **Real-Time Data Integration:** Connects directly via the Monday.com GraphQL API. To ensure data accuracy and satisfy real-time assessment constraints, no data is cached—each query retrieves the latest organizational metrics.
* **Intelligent Query Resolution:** The core LLM orchestrator interprets complex business queries and dynamically initiates granular data retrieval and operational calculations.
* **Proactive Clarification Loop:** Fully equipped to ask users follow-up questions when parameters (e.g., sector, date range, or status) require clarification.
* **Transparent Execution Tracing:** Provides full visibility into the agent's reasoning process by logging detailed tool execution traces directly within the user interface.
* **Extensible Tool Framework:** Engineered with a highly decoupled architecture, allowing seamless integration of new Python-based analytical tools.

---

## 🏗️ Technical Architecture & Directory Structure

The project strictly adheres to modular design principles to guarantee separation of concerns between configuration, UI, and external service communication.

```text
mcbia2/
├── run_app.py                      # Main entry point linking the agent with the Streamlit UI
├── app/                            # Core Application Logic
│   ├── config.py                   # Environment variable validation and initialization
│   ├── agent/  
│   │   └── gemini_brain.py         # LLM configuration, system prompts, and tool bindings
│   ├── services/  
│   │   ├── monday_api.py           # Monday.com API Client (GraphQL execution & mapping)
│   │   └── data_cleaning.py        # String sanitization, currency parsing, and date standardization
│   └── tools/  
│       └── bi_tools.py             # Specific quantitative metrics aggregation and data querying functions
└── ui/  
    └── interface.py                # Streamlit interface handling chat sessions, state, and rendering
```

---

## 🧠 Supported Analytical Tools
The agent currently delegates work to the following core Python tools:
1. `calculate_work_orders_revenue`: Aggregates finalized revenue with optional sector/status filters.
2. `analyze_deals_pipeline`: Computes total deal pipeline valuations based on stage and probability.
3. `summarize_operational_quantities`: Interprets and aggregates operational unit metrics (e.g., HA, KM).
4. `calculate_sector_performance`: Delivers cross-board insights for specific organizational divisions.
5. `analyze_revenue_by_quarter`: Models work order revenue spread across fiscal quarters.
6. `analyze_deals_timeline`: Distributes expected deal closures across upcoming fiscal periods.

---

## ⚙️ Installation & Setup

### 1. Requirements
Ensure you have Python 3.10+ installed on your system.

### 2. Dependencies
Install the required packages using `pip`:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
The application requires several sensitive credentials to operate. Create a `.env` file in the root directory and populate it with the following:
```env
MONDAY_API_KEY="your_monday_api_key_here"
GOOGLE_API_KEY="your_google_gemini_api_key"
WORK_ORDERS_BOARD_ID="numeric_id"
DEALS_BOARD_ID="numeric_id"
```
*Note: The system performs rigorous startup validation on these keys to prevent silent failures.*

---

## 💻 Execution
Once configured, launch the chatbot locally via Streamlit:
```bash
streamlit run run_app.py
```
This command will spin up the local server, and your default web browser will automatically open the interactive BI dashboard.
