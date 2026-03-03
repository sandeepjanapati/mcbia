import google.generativeai as genai
from app.config import Config
from app.tools.bi_tools import (
    calculate_work_orders_revenue,
    analyze_deals_pipeline,
    summarize_operational_quantities,
    calculate_sector_performance,
    analyze_revenue_by_quarter,
    analyze_deals_timeline,
)

TOOL_FUNCTIONS = {
    "calculate_work_orders_revenue": calculate_work_orders_revenue,
    "analyze_deals_pipeline": analyze_deals_pipeline,
    "summarize_operational_quantities": summarize_operational_quantities,
    "calculate_sector_performance": calculate_sector_performance,
    "analyze_revenue_by_quarter": analyze_revenue_by_quarter,
    "analyze_deals_timeline": analyze_deals_timeline,
}

TOOL_LIST = [
    calculate_work_orders_revenue,
    analyze_deals_pipeline,
    summarize_operational_quantities,
    calculate_sector_performance,
    analyze_revenue_by_quarter,
    analyze_deals_timeline,
]

SYSTEM_PROMPT = """You are a Founder's Business Intelligence Agent connected to Monday.com.
You have access to Monday.com boards and 6 analysis tools.

RULES:
1. Use tools whenever necessary. Do NOT make up numbers.
2. You ARE allowed and ENCOURAGED to do your own calculations, comparisons, percentages, averages, and analysis on top of the tool results.
3. Format currency with ₹ symbol and use commas for readability.
4. If a tool returns zero or empty results, mention it as a caveat.
5. Be concise but insightful — highlight key figures, trends, and actionable insights.
6. Query Understanding: Interpret founder-level questions. If a query is ambiguous or lacks necessary context, ask the user clarifying questions.
"""


def init_agent():
    Config.validate()
    genai.configure(api_key=Config.GOOGLE_API_KEY)

    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        tools=TOOL_LIST,
        system_instruction=SYSTEM_PROMPT,
    )

    chat = model.start_chat(enable_automatic_function_calling=False)
    return chat