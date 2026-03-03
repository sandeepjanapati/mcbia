# Decision Log: Monday.com Business Intelligence Agent

## 1. Technology Stack

**Language: Python 3**
- *Reasoning*: Python is the industry standard for both data engineering (fetching/cleaning messy data) and AI integrations. It allows rapid prototyping and seamless API interactions.

**UI Framework: Streamlit**
- *Reasoning*: The assessment requires a conversational interface and a hosted prototype. Streamlit provides out-of-the-box chat components (`st.chat_message`, `st.chat_input`) and real-time status components (`st.status`). It also allows for instant, one-click hosting via Streamlit Community Cloud with zero infrastructure setup for the evaluator.

**AI Model: Google Gemini 2.5 Flash**
- *Reasoning*: Gemini Flash is exceptionally fast and inexpensive, which is critical for interactive chat interfaces relying heavily on multi-turn function calling. Its native support for `enable_automatic_function_calling=False` allows us to intercept function calls and display live traces in the UI.

**API Integration: Monday.com GraphQL API via `requests`**
- *Reasoning*: Using standard HTTP requests with GraphQL provides granular control over the data payload. While a dedicated Monday package exists, `requests` minimizes dependencies and allows direct control over pagination (`items_page`, `cursor`) and error handling timeouts.

## 2. Architecture & Design Decisions

**Live Fetching vs Caching (Strict Compliance)**
- *Decision*: The constraint "Do NOT preload or cache data" was strictly adhered to. `MondayClient` instantiates on every single tool call, dynamically pulling the exact column mappings for the board in question before firing the data query. 
- *Trade-off*: Adds mild latency to every query since we execute two GraphQL calls (one for mapping, one for pagination data). However, this ensures 100% compliance with live-data expectations.

**Manual vs Automatic Function Calling**
- *Decision*: We opted for a manual function calling loop inside `interface.py` rather than letting the AI SDK resolve tools automatically behind the scenes.
- *Reasoning*: The prompt specifically requested "Visible action/tool-call traces". Automatic calling hides the intermediate steps from the UI until the final message generates. Manual handling allows us to populate `st.status` in real-time, showing which tool the Agent decided to call, its arguments, and the raw metric results before the final LLM synthesis.

**Deterministic Tools vs Complete LLM Autonomy**
- *Decision*: Rather than give the LLM a generic "Execute GraphQL" tool, we provided 6 strictly defined BI tools (e.g., `analyze_revenue_by_quarter`, `calculate_sector_performance`).
- *Reasoning*: BI data is notoriously messy (currency strings like "10k", "cr", date strings like "November", "YYYY-MM-DD"). By using strict python functions, we enforce deterministic, regex-based data cleaning (`data_cleaning.py`) on every payload before the LLM sees the numbers. This prevents hallucinated math and ensures high "Data Resilience".

**Handling Messy Values**
- *Decision*: All tools log specific exceptions and trace logs (e.g., "Matched 45 rows, 3 had empty revenue"). These traces are returned to the LLM directly as tool output.
- *Reasoning*: This allows the LLM to inherently answer the requirement "Communicate data quality caveats". If the data is empty, the LLM reads the trace and alerts the founder organically.
