"""SQLite database management for saving and resuming FlowCraft plans."""
import sqlite3
import json
import os
from typing import List, Optional
from models import FlowPlan, MicroStep

DB_FILE = "flowcraft.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        summary TEXT,
        tech_stack TEXT,
        total_estimated_minutes INTEGER,
        phases TEXT,
        steps TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()


def save_plan(plan: FlowPlan):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO plans (id, title, summary, tech_stack, total_estimated_minutes, phases, steps, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        plan.id,
        plan.title,
        plan.summary,
        plan.tech_stack,
        plan.total_estimated_minutes,
        json.dumps(plan.phases),
        json.dumps([s.model_dump() for s in plan.steps]),
        plan.created_at
    ))
    conn.commit()
    conn.close()


def get_plan(plan_id: str) -> Optional[FlowPlan]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    steps_data = json.loads(row["steps"])
    steps = [MicroStep(**s) for s in steps_data]
    return FlowPlan(
        id=row["id"],
        title=row["title"],
        summary=row["summary"],
        tech_stack=row["tech_stack"],
        total_estimated_minutes=row["total_estimated_minutes"],
        phases=json.loads(row["phases"]),
        steps=steps,
        created_at=row["created_at"]
    )


def list_plans() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, tech_stack, total_estimated_minutes, created_at, steps FROM plans ORDER BY created_at DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        steps_list = json.loads(r["steps"])
        completed_count = sum(1 for s in steps_list if s.get("status") == "completed")
        total_count = len(steps_list)
        result.append({
            "id": r["id"],
            "title": r["title"],
            "tech_stack": r["tech_stack"],
            "total_estimated_minutes": r["total_estimated_minutes"],
            "created_at": r["created_at"],
            "completed_steps": completed_count,
            "total_steps": total_count,
            "progress_pct": int((completed_count / total_count * 100) if total_count > 0 else 0)
        })
    return result


def update_step_status(plan_id: str, step_id: str, status: str):
    plan = get_plan(plan_id)
    if not plan:
        return None
    for step in plan.steps:
        if step.id == step_id:
            step.status = status
            break
    save_plan(plan)
    return plan


def delete_plan(plan_id: str) -> bool:
    """Delete a plan by ID from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_db_stats() -> dict:
    """Retrieve database metrics, file stats, and schema details."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM plans")
    total_plans = cursor.fetchone()["count"]
    
    cursor.execute("SELECT steps FROM plans")
    rows = cursor.fetchall()
    total_steps = 0
    completed_steps = 0
    for r in rows:
        try:
            steps_list = json.loads(r["steps"])
            total_steps += len(steps_list)
            completed_steps += sum(1 for s in steps_list if s.get("status") == "completed")
        except Exception:
            pass
            
    cursor.execute("PRAGMA table_info(plans)")
    columns = [dict(c) for c in cursor.fetchall()]
    
    cursor.execute("SELECT sqlite_version()")
    sqlite_ver = cursor.fetchone()[0]
    
    conn.close()
    
    file_size_bytes = os.path.getsize(DB_FILE) if os.path.exists(DB_FILE) else 0
    
    return {
        "db_file": DB_FILE,
        "db_path": os.path.abspath(DB_FILE),
        "file_size_bytes": file_size_bytes,
        "file_size_kb": round(file_size_bytes / 1024, 2),
        "sqlite_version": sqlite_ver,
        "total_plans": total_plans,
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "overall_progress_pct": int((completed_steps / total_steps * 100) if total_steps > 0 else 0),
        "table": "plans",
        "columns": columns
    }

