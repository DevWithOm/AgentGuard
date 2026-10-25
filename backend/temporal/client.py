import os
import uuid

from dotenv import load_dotenv
from temporalio.client import Client

from backend.workflows.agentguard_workflow import AgentGuardWorkflow

TASK_QUEUE = "agentguard"

load_dotenv()


async def get_client() -> Client:
    return await Client.connect(
        os.getenv("TEMPORAL_HOST", "localhost:7233"),
        namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
    )


async def run_workflow(message: str, client: Client | None = None, workflow_id: str | None = None,
                       slow_seconds: int = 0) -> dict:
    client = client or await get_client()
    return await client.execute_workflow(
        AgentGuardWorkflow.run,
        args=[message, slow_seconds],
        id=workflow_id or f"agentguard-{uuid.uuid4().hex[:8]}",
        task_queue=TASK_QUEUE,
    )
