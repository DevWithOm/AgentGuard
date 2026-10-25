from temporalio import activity

from backend.security.input_guard import scan_input


@activity.defn
def input_scan_activity(message: str) -> dict:
    return scan_input(message)
