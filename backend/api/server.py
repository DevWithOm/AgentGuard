import os
import uuid
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from temporalio.service import RPCError, RPCStatusCode

from backend.mock_data.emails import BY_ID, EMAILS, email_text
from backend.temporal.client import get_client, run_workflow
from backend.workflows.agentguard_workflow import AgentGuardWorkflow

app = FastAPI(title="AgentGuard")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_client = None


async def temporal_client():
    global _client
    _client = _client or await get_client()
    return _client


class RunRequest(BaseModel):
    scenario: str
    workflow_id: str | None = None  # lets the dashboard poll /status while /run is pending


@app.get("/emails")
def emails() -> list[dict]:
    return [{k: e[k] for k in ("id", "sender", "subject", "body")} for e in EMAILS]


@app.post("/run")
async def run(req: RunRequest, client=Depends(temporal_client)) -> dict:
    email = BY_ID.get(req.scenario)
    if email is None:
        raise HTTPException(404, f"Unknown email '{req.scenario}'. Options: {list(BY_ID)}")
    message = email_text(email)
    workflow_id = req.workflow_id or f"agentguard-{uuid.uuid4().hex[:8]}"
    result = await run_workflow(message, client=client, workflow_id=workflow_id,
                                slow_seconds=email.get("slow_seconds", 0))
    model = os.getenv("JARVIS_MODEL") if os.getenv("JARVIS_BASE_URL") else "Mock agent (Jarvis not configured)"
    return {"workflow_id": workflow_id, "message": message, "model": model, **result}


@app.get("/status/{workflow_id}")
async def status(workflow_id: str, client=Depends(temporal_client)) -> dict:
    """Live workflow state. worker_connected is false when no worker answers a query."""
    handle = client.get_workflow_handle(workflow_id)
    try:
        desc = await handle.describe()
    except RPCError as e:
        if e.status == RPCStatusCode.NOT_FOUND:
            return {"status": "PENDING", "stage": None, "worker_connected": True, "attempt": 0}
        raise
    stage, connected = None, True
    if desc.status.name == "RUNNING":
        try:
            stage = (await handle.query(AgentGuardWorkflow.state, rpc_timeout=timedelta(seconds=2)))["stage"]
        except Exception:
            connected = False
    attempt = max((a.attempt for a in desc.raw_description.pending_activities), default=0)
    return {"status": desc.status.name, "stage": stage, "worker_connected": connected, "attempt": attempt}


# Serves the built React app (cd frontend && npm run build). Registered last so it doesn't shadow /run.
if os.path.isdir("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
