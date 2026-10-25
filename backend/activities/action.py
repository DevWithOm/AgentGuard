from temporalio import activity

from backend.tools.mock_tools import execute_action


@activity.defn
def action_activity(action: dict) -> dict:
    return execute_action(action)
