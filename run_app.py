from app.agent.gemini_brain import init_agent
from ui.interface import render_ui

if __name__ == "__main__":
    render_ui(init_agent)