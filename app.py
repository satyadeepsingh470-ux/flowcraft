"""FastAPI Backend Server for FlowCraft - Agentic Task Decomposer & Flow Planner."""
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from models import DecomposeRequest, FlowPlan, UnblockRequest, UnblockResponse
import database
import agent

app = FastAPI(title="FlowCraft API", description="Agentic Task Decomposer & Flow State Planner")

# Initialize SQLite database
database.init_db()

# Mount static files directory
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


class UpdateStatusRequest(BaseModel):
    status: str  # pending | in_progress | completed | skipped


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


@app.post("/api/decompose", response_model=FlowPlan)
def decompose_endpoint(req: DecomposeRequest):
    """Decompose high-level intimidating task into atomic micro-steps."""
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task description cannot be empty.")
    
    plan = agent.decompose_task(req)
    database.save_plan(plan)
    return plan


@app.get("/api/plans")
def list_plans_endpoint():
    """List recent flow plans with progress stats."""
    return database.list_plans()


@app.get("/api/plans/{plan_id}", response_model=FlowPlan)
def get_plan_endpoint(plan_id: str):
    """Retrieve full plan with all micro-steps."""
    plan = database.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return plan


@app.patch("/api/plans/{plan_id}/steps/{step_id}")
def update_step_status_endpoint(plan_id: str, step_id: str, req: UpdateStatusRequest):
    """Update step completion status."""
    plan = database.update_step_status(plan_id, step_id, req.status)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan or step not found.")
    return plan


@app.post("/api/unblock", response_model=UnblockResponse)
def unblock_endpoint(req: UnblockRequest):
    """Diagnose a roadblock and provide instant sub-steps with AI."""
    return agent.unblock_task(req)


@app.get("/api/export/{plan_id}")
def export_plan_markdown(plan_id: str):
    """Export plan formatted as clean Markdown for Notion, Obsidian, or GitHub."""
    plan = database.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")
    
    md_lines = [
        f"# 🎯 {plan.title}",
        f"> **Tech Stack:** `{plan.tech_stack}` | **Total Time:** ~{plan.total_estimated_minutes} min",
        "",
        f"**Strategy:** {plan.summary}",
        "",
        "---",
        ""
    ]
    
    current_phase = None
    for step in plan.steps:
        if step.phase != current_phase:
            current_phase = step.phase
            md_lines.append(f"\n## 📌 {current_phase}\n")
        
        status_icon = "✅" if step.status == "completed" else "⏳"
        md_lines.append(f"### {status_icon} {step.title} (~{step.estimated_minutes} min)")
        md_lines.append(f"{step.description}\n")
        
        if step.commands:
            md_lines.append("**Terminal Commands:**")
            md_lines.append("```bash")
            for cmd in step.commands:
                md_lines.append(cmd)
            md_lines.append("```\n")
            
        if step.starter_code:
            lang = "python" if "py" in (step.file_path or "") else "text"
            md_lines.append(f"**Starter Snippet** (`{step.file_path or 'code'}`):")
            md_lines.append(f"```{lang}")
            md_lines.append(step.starter_code)
            md_lines.append("```\n")
            
        md_lines.append(f"- **Definition of Done:** {step.definition_of_done}")
        if step.pitfalls:
            md_lines.append(f"- **Pitfall to Avoid:** {step.pitfalls[0]}")
        md_lines.append("")
        
    return PlainTextResponse("\n".join(md_lines), media_type="text/markdown")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)
