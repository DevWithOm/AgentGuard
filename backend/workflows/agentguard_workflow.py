from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from backend.activities.action import action_activity
    from backend.activities.agent_activity import agent_activity
    from backend.activities.input_scan import input_scan_activity
    from backend.activities.output_scan import output_scan_activity

TIMEOUT = timedelta(seconds=60)
RETRY = RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=5)
HEARTBEAT_TIMEOUT = timedelta(seconds=5)


async def _run(activity, *args, heartbeat_timeout=None):
    return await workflow.execute_activity(
        activity, args=list(args), start_to_close_timeout=TIMEOUT, retry_policy=RETRY,
        heartbeat_timeout=heartbeat_timeout)


@workflow.defn
class AgentGuardWorkflow:
    def __init__(self) -> None:
        self.stage = "INPUT_GUARD"

    @workflow.query
    def state(self) -> dict:
        return {"stage": self.stage}

    @workflow.run
    async def run(self, message: str, slow_seconds: int = 0) -> dict:
        # "input" / "agent" / "output" / "actions" carry per-stage details for the dashboard.
        result = {"input": None, "agent": None, "output": None, "actions": []}

        result["input"] = inp = await _run(input_scan_activity, message)
        if inp["malicious"]:
            return {**result, "status": "BLOCKED", "stage": "INPUT_GUARD",
                    "risk": inp["risk"], "reason": inp["reason"]}

        self.stage = "AGENT"
        result["agent"] = out = await _run(agent_activity, message, slow_seconds, heartbeat_timeout=HEARTBEAT_TIMEOUT)

        self.stage = "OUTPUT_GUARD"
        result["output"] = scan = await _run(output_scan_activity, message, out)
        if scan["propagation_detected"]:
            return {**result, "status": "BLOCKED", "stage": "OUTPUT_GUARD",
                    "risk": scan["risk"], "reason": scan["reason"]}

        self.stage = "ACTION"
        for action in out["actions"]:
            result["actions"].append(await _run(action_activity, action))
        self.stage = "DONE"
        return {**result, "status": "COMPLETED", "stage": "ACTION", "risk": 0, "reason": "All checks passed"}
