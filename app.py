import streamlit as st
import json
# We import the 'chat_session' object from your existing main.py
# This gives the UI access to the Gemini brain and the Monday.com tools you already built.
from main import chat_session

# 1. Configure the Page
st.set_page_config(
    page_title="Monday.com BI Agent",
    page_icon="🤖",
    layout="wide" 
)

st.title("🤖 Founder BI Assistant")
st.caption("Live integration with Monday.com | Boards: Work Orders & Deals")

# 2. Setup Session State (Memory for the UI)
if "messages" not in st.session_state:
    st.session_state.messages = []

if "traces" not in st.session_state:
    st.session_state.traces = []

# 3. Sidebar: The "Visible Trace" Feature
with st.sidebar:
    st.header("🧠 Agent Thought Process")
    st.info("This log shows live API calls and Data Cleaning steps.")
    
    # Display the collected traces
    if st.session_state.traces:
        for trace in reversed(st.session_state.traces):
            with st.expander(f"Action: {trace['tool']}", expanded=True):
                for step in trace['logs']:
                    st.text(f"→ {step}")
                    
    if st.button("Clear History"):
        st.session_state.messages = []
        st.session_state.traces = []
        st.rerun()

# 4. Main Chat Interface
# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle User Input
if prompt := st.chat_input("Ask a question (e.g., 'How is the pipeline for Mining?')..."):
    
    # A. Display User Message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. Generate AI Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking & Querying Monday.com...")
        
        try:
            # --- THE CORE ACTION ---
            # Send message to Gemini (which calls your main.py tools automatically)
            response = chat_session.send_message(prompt)
            final_text = response.text
            
            # --- CAPTURE TRACES (The Magic Step) ---
            # We look at the Gemini history to find the Tool Outputs
            # The history contains the JSON returned by your Python functions.
            history = chat_session.history
            
            # Iterate backwards through history to find the most recent Function Response
            for part in reversed(history):
                # Check if this part of the conversation was a "Function Response" (Tool Output)
                if hasattr(part, 'parts'):
                    for p in part.parts:
                        if hasattr(p, 'function_response'):
                            # We found it! Extract the JSON result
                            result_json = p.function_response.response
                            
                            # Convert 'MapComposite' to dict if needed, or just access keys
                            # Gemini returns a special object, we convert to standard dict
                            try:
                                # Access the 'trace' field we built in Step 6
                                trace_logs = result_json.get("trace", [])
                                metric_name = result_json.get("metric", "Tool Execution")
                                
                                # Save to UI Session State
                                # Only add if we haven't added it recently (simple dedup)
                                if not st.session_state.traces or st.session_state.traces[-1]['logs'] != trace_logs:
                                    st.session_state.traces.append({
                                        "tool": metric_name,
                                        "logs": trace_logs
                                    })
                            except:
                                pass # Skip if parsing fails
                            
                            # Break after finding the most recent tool use
                            break 
            
            # Display Final Answer
            message_placeholder.markdown(final_text)
            st.session_state.messages.append({"role": "assistant", "content": final_text})
            
            # Force a rerun to update the Sidebar immediately
            st.rerun()
            
        except Exception as e:
            message_placeholder.error(f"Error: {str(e)}")