import streamlit as st
from datetime import datetime
import google.generativeai as genai
from app.agent.gemini_brain import TOOL_FUNCTIONS


def _init_session_state():
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    if "active_chat_id" not in st.session_state:
        st.session_state.active_chat_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []


def _new_chat(agent_init_fn):
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    if st.session_state.active_chat_id and st.session_state.messages:
        _save_current_chat()

    st.session_state.active_chat_id = chat_id
    st.session_state.messages = []
    st.session_state.agent_session = agent_init_fn()
    return chat_id


def _save_current_chat():
    chat_id = st.session_state.active_chat_id
    if chat_id and st.session_state.messages:
        first_user_msg = ""
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                first_user_msg = msg["content"][:50]
                break
        title = first_user_msg if first_user_msg else "Untitled Chat"

        st.session_state.conversations[chat_id] = {
            "title": title,
            "messages": list(st.session_state.messages),
            "timestamp": chat_id,
        }


def _load_chat(chat_id):
    if st.session_state.active_chat_id and st.session_state.messages:
        _save_current_chat()

    conv = st.session_state.conversations[chat_id]
    st.session_state.active_chat_id = chat_id
    st.session_state.messages = list(conv["messages"])


def _run_agent_with_tools(chat_session, prompt, status_container):
    """Manual function calling loop with real-time UI updates."""
    all_traces = []

    with status_container:
        st.write("📡 Sending your question to AI agent...")

    response = chat_session.send_message(prompt)

    loop_count = 0
    max_loops = 10

    while loop_count < max_loops:
        function_calls = []
        for part in response.candidates[0].content.parts:
            if part.function_call.name:
                function_calls.append(part.function_call)

        if not function_calls:
            break

        loop_count += 1
        function_responses = []

        for fc in function_calls:
            fn_name = fc.name
            fn_args = dict(fc.args) if fc.args else {}

            with status_container:
                st.write(f"🔧 **Calling tool: `{fn_name}`**")
                if fn_args:
                    args_str = ", ".join(f"{k}=\"{v}\"" for k, v in fn_args.items())
                    st.caption(f"   Parameters: {args_str}")

            if fn_name in TOOL_FUNCTIONS:
                try:
                    result = TOOL_FUNCTIONS[fn_name](**fn_args)

                    trace_logs = result.get("trace", [])
                    metric_name = result.get("metric", fn_name)

                    with status_container:
                        st.write(f"✅ **{metric_name}** — completed")
                        for log in trace_logs:
                            st.caption(f"   → {log}")

                    all_traces.append({"tool": metric_name, "logs": trace_logs})
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fn_name,
                                response={"result": result},
                            )
                        )
                    )

                except Exception as e:
                    error_msg = f"Error executing {fn_name}: {str(e)}"
                    with status_container:
                        st.write(f"❌ **{fn_name}** — failed: {str(e)}")
                    all_traces.append({"tool": fn_name, "logs": [error_msg]})
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fn_name,
                                response={"error": error_msg},
                            )
                        )
                    )
            else:
                error_msg = f"Unknown tool: {fn_name}"
                with status_container:
                    st.write(f"⚠️ Unknown tool: `{fn_name}`")
                function_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fn_name,
                            response={"error": error_msg},
                        )
                    )
                )

        with status_container:
            st.write("🧠 AI agent is analyzing the results...")

        response = chat_session.send_message(
            genai.protos.Content(parts=function_responses)
        )

    final_text = ""
    for part in response.candidates[0].content.parts:
        if part.text:
            final_text += part.text

    with status_container:
        st.write(f"✅ Done! (used {loop_count} tool call{'s' if loop_count != 1 else ''})")

    status_container.update(
        label=f"✅ Finished — {loop_count} tool{'s' if loop_count != 1 else ''} used",
        state="complete",
        expanded=False,
    )

    return final_text, all_traces


def _render_sidebar(agent_init_fn):
    with st.sidebar:
        st.header("💬 Chat History")

        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            _new_chat(agent_init_fn)
            st.rerun()

        st.divider()

        if st.session_state.conversations:
            sorted_convs = sorted(
                st.session_state.conversations.items(),
                key=lambda x: x[0],
                reverse=True,
            )
            for chat_id, conv in sorted_convs:
                is_active = chat_id == st.session_state.active_chat_id
                label = f"{'▶ ' if is_active else ''}{conv['title']}"

                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(
                        label,
                        key=f"load_{chat_id}",
                        use_container_width=True,
                        disabled=is_active,
                    ):
                        _load_chat(chat_id)
                        st.rerun()
                with col2:
                    if st.button("🗑", key=f"del_{chat_id}"):
                        del st.session_state.conversations[chat_id]
                        if st.session_state.active_chat_id == chat_id:
                            _new_chat(agent_init_fn)
                        st.rerun()
        else:
            st.caption("No chat history yet.")


def render_ui(agent_init_fn):
    st.set_page_config(page_title="Monday BI Agent", page_icon="📊", layout="wide")
    _init_session_state()

    if st.session_state.active_chat_id is None:
        _new_chat(agent_init_fn)

    _render_sidebar(agent_init_fn)

    st.title("📊 Founder BI Assistant")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "traces" in msg and msg["traces"]:
                with st.expander("🔍 View Process Steps", expanded=False):
                    for t in msg["traces"]:
                        st.markdown(f"**🛠 {t['tool']}**")
                        for log in t["logs"]:
                            st.text(f"   → {log}")

    if prompt := st.chat_input("Ask about Revenue, Pipeline, or Sectors..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            status_container = st.status("🧠 Agent is working...", expanded=True)

            try:
                chat_session = st.session_state.agent_session
                final_text, traces = _run_agent_with_tools(
                    chat_session, prompt, status_container
                )

                st.markdown(final_text)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_text,
                    "traces": traces,
                })

                _save_current_chat()
                st.rerun()

            except Exception as e:
                status_container.update(label="❌ Error", state="error", expanded=True)
                with status_container:
                    st.error(f"Agent Error: {str(e)}")
                st.error(f"Something went wrong: {str(e)}")