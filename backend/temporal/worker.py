import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.worker import Worker

from backend.activities.action import action_activity
from backend.activities.agent_activity import agent_activity
from backend.activities.input_scan import input_scan_activity
from backend.activities.output_scan import output_scan_activity
from backend.temporal.client import TASK_QUEUE, get_client
from backend.workflows.agentguard_workflow import AgentGuardWorkflow

ACTIVITIES = [input_scan_activity, agent_activity, output_scan_activity, action_activity]


def make_worker(client) -> Worker:
    return Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AgentGuardWorkflow],
        activities=ACTIVITIES,
        activity_executor=ThreadPoolExecutor(max_workers=8),
    )


async def main() -> None:
    print(f"Worker listening on task queue '{TASK_QUEUE}'")
    await make_worker(await get_client()).run()


if __name__ == "__main__":
    asyncio.run(main())
