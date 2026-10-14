"""Agentic Task Decomposition and Flow Coach Engine using Google Gemini."""
import os
import json
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from models import DecomposeRequest, FlowPlan, MicroStep, UnblockRequest, UnblockResponse

load_dotenv()


def get_api_key(request_key: Optional[str] = None) -> Optional[str]:
    """Retrieve API key from request payload or environment."""
    if request_key and request_key.strip():
        return request_key.strip()
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    return None


SYSTEM_PROMPT = """You are a Senior Staff Engineer and Flow State Coach.
Your mission is to cure developer procrastination and cognitive overload.
When given an intimidating or broad coding/engineering goal, you decompose it into atomic, non-intimidating micro-steps.

Rules:
1. Each micro-step MUST take between 5 and 20 minutes to complete.
2. Group the micro-steps into sequential phases (e.g. Phase 1: Environment & Setup, Phase 2: Schema/Data, Phase 3: Core Implementation, Phase 4: Integration & Verification).
3. For each step, provide:
   - Action-oriented title (e.g. "Create virtualenv and install Authlib")
   - Copy-pasteable terminal commands (if applicable).
   - Starter code or configuration snippet with the suggested file path (keep it focused, concise, and copy-ready).
   - Definition of Done (how the developer knows this exact 10-minute step is finished).
   - 1-2 Common pitfalls/gotchas to avoid.
4. Total steps should generally be between 4 and 10 steps so it stays achievable within the user's available time.
5. Return ONLY a valid JSON object matching this schema:
{
  "title": "Clean Project Title",
  "summary": "1-2 sentence strategy explaining how this plan conquers the goal effortlessly.",
  "tech_stack": "Specified or inferred tech stack",
  "total_estimated_minutes": 90,
  "phases": ["Phase 1: Setup", "Phase 2: Implementation", "Phase 3: Verification"],
  "steps": [
    {
      "id": "step-1",
      "phase": "Phase 1: Setup",
      "title": "Short action title",
      "description": "What to do and why it matters.",
      "estimated_minutes": 10,
      "commands": ["npm install ...", "mkdir -p ..."],
      "file_path": "path/to/file.py",
      "starter_code": "// code here",
      "definition_of_done": "Run test or verify terminal output shows X.",
      "pitfalls": ["Avoid doing Y before Z"]
    }
  ]
}
"""


def decompose_with_gemini(req: DecomposeRequest, api_key: str) -> FlowPlan:
    """Decompose using Gemini 2.5 Flash via google-genai."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    user_prompt = f"""
Goal / Task to Decompose:
"{req.task}"

Target Tech Stack: {req.tech_stack or "Python / Web"}
Available Time Budget: {req.available_time_minutes} minutes
Developer Experience Level: {req.experience_level}

Deconstruct this into a clean, actionable, step-by-step Flow Plan with copyable terminal commands, starter code, and verified definitions of done.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    data = json.loads(response.text)
    plan_id = f"plan-{uuid.uuid4().hex[:8]}"

    steps = []
    for idx, s in enumerate(data.get("steps", [])):
        steps.append(MicroStep(
            id=s.get("id", f"step-{idx + 1}"),
            phase=s.get("phase", "Phase 1"),
            title=s.get("title", f"Step {idx + 1}"),
            description=s.get("description", ""),
            estimated_minutes=int(s.get("estimated_minutes", 15)),
            commands=s.get("commands", []),
            file_path=s.get("file_path"),
            starter_code=s.get("starter_code"),
            definition_of_done=s.get("definition_of_done", "Step completed and verified."),
            pitfalls=s.get("pitfalls", []),
            status="pending"
        ))

    return FlowPlan(
        id=plan_id,
        title=data.get("title", req.task),
        summary=data.get("summary", "Custom AI-decomposed execution roadmap."),
        tech_stack=data.get("tech_stack", req.tech_stack or "Fullstack"),
        total_estimated_minutes=int(data.get("total_estimated_minutes", sum(s.estimated_minutes for s in steps))),
        phases=data.get("phases", list(dict.fromkeys(s.phase for s in steps))),
        steps=steps,
        created_at=datetime.utcnow().isoformat()
    )


def unblock_with_gemini(req: UnblockRequest, api_key: str) -> UnblockResponse:
    """Diagnose a roadblock and provide instant sub-steps with Gemini."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    prompt = f"""You are an expert developer unblocker.
The user is stuck on this micro-step:
Title: {req.step_title}
Context: {req.step_description}

User's Roadblock / Error:
"{req.problem_details}"

Provide an immediate, actionable diagnosis and break this problem into 2-3 instant micro-substeps.
Return ONLY valid JSON matching this schema:
{{
  "diagnosis": "Direct explanation of what is causing the error or blocker.",
  "quick_fix": "1-2 sentence immediate solution.",
  "micro_substeps": ["Sub-step 1: ...", "Sub-step 2: ..."],
  "suggested_commands": ["command 1", "command 2"]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    data = json.loads(response.text)
    return UnblockResponse(
        step_id=req.step_id,
        diagnosis=data.get("diagnosis", "Encountered unexpected hurdle."),
        quick_fix=data.get("quick_fix", "Check local environment and configurations."),
        micro_substeps=data.get("micro_substeps", ["Inspect terminal logs", "Verify package versions"]),
        suggested_commands=data.get("suggested_commands", [])
    )


def generate_fallback_plan(req: DecomposeRequest) -> FlowPlan:
    """Smart local template generator when no API key is configured yet."""
    task_lower = req.task.lower()
    plan_id = f"plan-{uuid.uuid4().hex[:8]}"

    if "auth" in task_lower or "login" in task_lower or "oauth" in task_lower:
        title = "OAuth2 / JWT Authentication Flow"
        summary = "Implement a secure, token-based authentication system without getting lost in boilerplate."
        tech_stack = req.tech_stack or "Python / FastAPI / JWT"
        phases = ["Phase 1: Environment & Secrets", "Phase 2: Security & Password Hashing", "Phase 3: Endpoints & Token Validation"]
        steps = [
            MicroStep(
                id="step-1",
                phase="Phase 1: Environment & Secrets",
                title="Install Auth Dependencies & Setup .env",
                description="Install PyJWT, passlib with bcrypt, and configure secure token secret keys.",
                estimated_minutes=10,
                commands=["pip install \"python-jose[cryptography]\" \"passlib[bcrypt]\" python-dotenv", "openssl rand -hex 32"],
                file_path=".env",
                starter_code="SECRET_KEY=your_generated_32_byte_hex_key\nALGORITHM=HS256\nACCESS_TOKEN_EXPIRE_MINUTES=60\n",
                definition_of_done="Packages install with 0 errors and SECRET_KEY is set in .env",
                pitfalls=["Never commit your .env or hardcode secrets into git."],
                status="pending"
            ),
            MicroStep(
                id="step-2",
                phase="Phase 2: Security & Password Hashing",
                title="Create Password Hashing & Verification Helper",
                description="Write utility functions for hashing plain passwords and verifying incoming credentials.",
                estimated_minutes=15,
                commands=["mkdir -p auth", "touch auth/security.py"],
                file_path="auth/security.py",
                starter_code="from passlib.context import CryptContext\n\npwd_context = CryptContext(schemes=[\"bcrypt\"], deprecated=\"auto\")\n\ndef verify_password(plain_password: str, hashed_password: str) -> bool:\n    return pwd_context.verify(plain_password, hashed_password)\n\ndef get_password_hash(password: str) -> str:\n    return pwd_context.hash(password)\n",
                definition_of_done="Run python -c 'from auth.security import get_password_hash; print(get_password_hash(\"test\"))' successfully",
                pitfalls=["Bcrypt has a 72-byte password length limit; ensure inputs are validated."],
                status="pending"
            ),
            MicroStep(
                id="step-3",
                phase="Phase 2: Security & Password Hashing",
                title="Implement JWT Token Creator & Decoder",
                description="Generate signed bearer tokens with expiration timestamps.",
                estimated_minutes=15,
                commands=["touch auth/tokens.py"],
                file_path="auth/tokens.py",
                starter_code="from datetime import datetime, timedelta\nfrom jose import jwt\nimport os\n\ndef create_access_token(data: dict, expires_delta: timedelta = None) -> str:\n    to_encode = data.copy()\n    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))\n    to_encode.update({\"exp\": expire})\n    return jwt.encode(to_encode, os.getenv(\"SECRET_KEY\"), algorithm=os.getenv(\"ALGORITHM\", \"HS256\"))\n",
                definition_of_done="Unit test token creation and assert decoding returns identical payload.",
                pitfalls=["Always check for expired token exception when decoding."],
                status="pending"
            ),
            MicroStep(
                id="step-4",
                phase="Phase 3: Endpoints & Token Validation",
                title="Add Login Route & Protect Sample Endpoint",
                description="Create the POST /login route and protect a GET /me endpoint using OAuth2PasswordBearer.",
                estimated_minutes=20,
                commands=["python main.py"],
                file_path="main.py",
                starter_code="from fastapi import FastAPI, Depends, HTTPException\nfrom fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm\n\napp = FastAPI()\noauth2_scheme = OAuth2PasswordBearer(tokenUrl=\"token\")\n\n@app.post(\"/token\")\nasync def login(form_data: OAuth2PasswordRequestForm = Depends()):\n    return {\"access_token\": \"demo_token\", \"token_type\": \"bearer\"}\n\n@app.get(\"/users/me\")\nasync def read_users_me(token: str = Depends(oauth2_scheme)):\n    return {\"status\": \"authenticated\", \"token\": token}\n",
                definition_of_done="Test /token endpoint via Swagger UI (http://localhost:8000/docs) and verify protected route returns 200.",
                pitfalls=["FastAPI's OAuth2PasswordRequestForm expects username and password fields in form-data."],
                status="pending"
            )
        ]
    else:
        # General purpose intelligent decomposition
        title = f"Execution Plan: {req.task.title()}"
        summary = "Structured 4-phase micro-execution plan designed to eliminate hesitation and maintain steady momentum."
        tech_stack = req.tech_stack or "Python / Modern Dev Stack"
        phases = ["Phase 1: Environment & Project Scaffolding", "Phase 2: Data Models & Logic", "Phase 3: Integration & Testing"]
        steps = [
            MicroStep(
                id="step-1",
                phase="Phase 1: Environment & Project Scaffolding",
                title="Initialize Repository & Dependency Sandbox",
                description="Create an isolated workspace, clean directory structure, and install foundational libraries.",
                estimated_minutes=10,
                commands=["python3 -m venv venv", "source venv/bin/activate", "pip install --upgrade pip"],
                file_path="requirements.txt",
                starter_code="# Core dependencies\npydantic>=2.0\npython-dotenv\npytest\n",
                definition_of_done="Verify python environment activates cleanly and packages install without warnings.",
                pitfalls=["Ensure .gitignore excludes venv/ and .env."],
                status="pending"
            ),
            MicroStep(
                id="step-2",
                phase="Phase 2: Data Models & Logic",
                title="Define Core Schemas & Validation Contracts",
                description="Outline inputs, outputs, and edge cases using type-safe Pydantic models.",
                estimated_minutes=15,
                commands=["mkdir -p src", "touch src/models.py"],
                file_path="src/models.py",
                starter_code="from pydantic import BaseModel, Field\nfrom typing import Optional\n\nclass CoreEntity(BaseModel):\n    id: str\n    name: str\n    is_active: bool = True\n",
                definition_of_done="Run python -m py_compile src/models.py with zero syntax errors.",
                pitfalls=["Avoid nesting models too deeply before verifying real usage."],
                status="pending"
            ),
            MicroStep(
                id="step-3",
                phase="Phase 2: Data Models & Logic",
                title="Implement Core Business Logic Engine",
                description="Write the essential logic handler with clear input/output contracts.",
                estimated_minutes=20,
                commands=["touch src/service.py"],
                file_path="src/service.py",
                starter_code="def process_task(payload: dict) -> dict:\n    # Core business logic execution\n    result = {'status': 'success', 'data': payload}\n    return result\n",
                definition_of_done="Call service function in python REPL and verify expected dictionary response.",
                pitfalls=["Keep functions pure and avoid hidden side-effects."],
                status="pending"
            ),
            MicroStep(
                id="step-4",
                phase="Phase 3: Integration & Testing",
                title="Automated Test & Verification Suite",
                description="Add unit tests covering both the happy path and critical boundary cases.",
                estimated_minutes=15,
                commands=["pytest tests/ -v"],
                file_path="tests/test_core.py",
                starter_code="def test_core_flow():\n    assert 1 + 1 == 2\n",
                definition_of_done="pytest reports all green checkmarks.",
                pitfalls=["Don't skip mocking external network calls."],
                status="pending"
            )
        ]

    return FlowPlan(
        id=plan_id,
        title=title,
        summary=summary + " (Tip: Connect Gemini API Key for fully autonomous dynamic reasoning on any topic!)",
        tech_stack=tech_stack,
        total_estimated_minutes=sum(s.estimated_minutes for s in steps),
        phases=phases,
        steps=steps,
        created_at=datetime.utcnow().isoformat()
    )


def decompose_task(req: DecomposeRequest) -> FlowPlan:
    """Entry point: routes to Gemini if key available, else provides intelligent template."""
    api_key = get_api_key(req.api_key)
    if api_key:
        try:
            return decompose_with_gemini(req, api_key)
        except Exception as e:
            print(f"Gemini API error, falling back to local planner: {e}")
            plan = generate_fallback_plan(req)
            plan.summary = f"Generated in offline mode ({str(e)[:80]}...). Add a valid Gemini API Key in Settings for live AI generation."
            return plan
    return generate_fallback_plan(req)


def unblock_task(req: UnblockRequest) -> UnblockResponse:
    """Entry point for unblocking a stuck step."""
    api_key = get_api_key(req.api_key)
    if api_key:
        try:
            return unblock_with_gemini(req, api_key)
        except Exception as e:
            print(f"Gemini unblock error: {e}")
    
    # Offline fallback
    return UnblockResponse(
        step_id=req.step_id,
        diagnosis=f"Issue during '{req.step_title}': The process encountered a common dependency or configuration mismatch.",
        quick_fix="Verify directory path, ensure virtual environment is active, and inspect standard output logs.",
        micro_substeps=[
            "Step 1: Check active python interpreter with 'which python' to ensure you're in venv.",
            "Step 2: Print recent traceback or errors by checking logs.",
            "Step 3: Test individual components in Python REPL before running the full script."
        ],
        suggested_commands=[
            "which python",
            "pip list | grep -i " + (req.step_title.split()[0] if req.step_title else "fastapi"),
            "env | grep -i path"
        ]
    )
