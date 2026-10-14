"""Data models and schemas for FlowCraft - Agentic Task Decomposer."""
from typing import List, Optional
from pydantic import BaseModel, Field


class MicroStep(BaseModel):
    id: str = Field(..., description="Unique step identifier, e.g., 'step-1'")
    phase: str = Field(..., description="Phase or milestone title, e.g. 'Phase 1: Setup'")
    title: str = Field(..., description="Actionable title for the micro-step")
    description: str = Field(..., description="Clear explanation of the step and rationale")
    estimated_minutes: int = Field(15, description="Estimated time in minutes (typically 5-20m)")
    commands: List[str] = Field(default_factory=list, description="Copyable terminal commands")
    file_path: Optional[str] = Field(None, description="Relevant file path if code is created/edited")
    starter_code: Optional[str] = Field(None, description="Starter code snippet or boilerplate")
    definition_of_done: str = Field(..., description="How to verify this step is 100% complete")
    pitfalls: List[str] = Field(default_factory=list, description="Common traps or errors to avoid")
    status: str = Field("pending", description="'pending' | 'in_progress' | 'completed' | 'skipped'")


class FlowPlan(BaseModel):
    id: str = Field(..., description="Unique plan identifier")
    title: str = Field(..., description="Clean name of the overall project / goal")
    summary: str = Field(..., description="Executive summary and architectural strategy")
    tech_stack: str = Field(..., description="Tech stack identified or provided")
    total_estimated_minutes: int = Field(..., description="Total estimated time in minutes")
    phases: List[str] = Field(default_factory=list, description="Ordered list of phase names")
    steps: List[MicroStep] = Field(default_factory=list, description="Ordered atomic micro-steps")
    created_at: str = Field(..., description="ISO timestamp")


class DecomposeRequest(BaseModel):
    task: str = Field(..., description="The high-level goal or intimidating task to decompose")
    tech_stack: Optional[str] = Field("Python", description="Languages, frameworks, or tools")
    available_time_minutes: Optional[int] = Field(120, description="Available time budget in minutes")
    experience_level: Optional[str] = Field("Intermediate", description="Beginner | Intermediate | Advanced")
    api_key: Optional[str] = Field(None, description="Optional user-provided Gemini API key")


class UnblockRequest(BaseModel):
    step_id: str
    step_title: str
    step_description: str
    problem_details: str = Field(..., description="What the user is stuck on or error message")
    api_key: Optional[str] = Field(None, description="Optional user-provided Gemini API key")


class UnblockResponse(BaseModel):
    step_id: str
    diagnosis: str
    quick_fix: str
    micro_substeps: List[str]
    suggested_commands: List[str]
