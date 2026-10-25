from temporalio import activity

from backend.security.output_guard import scan_output


@activity.defn
def output_scan_activity(input_message: str, agent_output: dict) -> dict:
    return scan_output(input_message, agent_output)
