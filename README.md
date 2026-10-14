# FlowCraft ⚡
> **Agentic Task Decomposer & Flow State Planner for Developers**

FlowCraft is a productivity web application built with **Python**, **FastAPI**, and **Google Gemini (GenAI)** designed specifically to cure developer procrastination, cognitive overload, and task paralysis.

---

## 💡 The Problem It Solves

Developers frequently write broad, intimidating tasks on their to-do lists (e.g. *"Implement OAuth2 authentication"*, *"Dockerize microservice"*, *"Migrate database to PostgreSQL"*). Because these goals are too abstract and complex, engineers experience task paralysis and hesitation.

**FlowCraft acts as an autonomous Senior Staff Engineer:**
1. **Deconstructs** any daunting goal into 10–15 minute atomic micro-steps.
2. **Generates copy-pasteable terminal commands** for each step.
3. **Provides minimal starter code** and file paths.
4. **Defines precise "Definition of Done"** verification tests.
5. **Warns against common pitfalls** before you make them.
6. **Focus / Flow Mode:** Eliminates distraction with an isolated step-by-step runner and built-in Pomodoro timer.
7. **🚨 AI Unblocker:** Stuck on an error? The agent diagnoses the root cause and breaks down the roadblock into 3-minute sub-steps.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.9+, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Pydantic v2](https://docs.pydantic.dev/)
- **AI Engine:** Google Gemini (`gemini-2.5-flash`) via the official `google-genai` SDK (with intelligent offline template fallback)
- **Database:** SQLite (persists plans, past runs, and progress)
- **Frontend:** Modern, dark-mode developer UI (Vanilla JS, CSS, Canvas Confetti)

---

## 🚀 Quickstart

### 1. Start the Server
Run the FastAPI server using the local virtual environment:
```bash
./venv/bin/uvicorn app:app --reload --port 8001
```
*(or run `python app.py`)*

### 2. Open in Your Browser
Navigate to:
```
http://localhost:8001
```

### 3. (Optional) Configure Gemini API Key
- Click the **API Key** button in the top right navbar to paste your key.
- Or copy `.env.example` to `.env` and set `GEMINI_API_KEY`:
  ```bash
  cp .env.example .env
  # Add your GEMINI_API_KEY from https://aistudio.google.com
  ```
*(Note: If no API key is provided, FlowCraft automatically uses its built-in intelligent planner so you can immediately explore all features!)*

---

## 🎯 Features Walkthrough

- **⚡ Quick Idea Presets:** Test with 1-click prompts like *"Google OAuth2 in FastAPI"*, *"Multi-stage Docker Setup"*, *"Postgres & Alembic Migration"*, and *"Redis Rate Limiting"*.
- **🎯 Full-Screen Focus Mode:** Click **"Launch Focus Mode"** to focus on one step at a time with a Pomodoro countdown timer.
- **🚨 "I'm Stuck" Unblocker:** Get instant AI diagnosis and quick fixes when a step fails.
- **📜 Past Plans:** Review and resume your previous projects anytime.
- **📋 Markdown Export:** Export your complete execution plan directly into Notion, Obsidian, or GitHub Issues.
