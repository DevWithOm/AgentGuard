def send_email(to: str, subject: str = "", body: str = "") -> dict:
    """Mock tool: never sends anything."""
    return {"status": "success", "action": "email_sent", "to": to}


TOOLS = {"send_email": send_email}


def execute_action(action: dict) -> dict:
    args = {k: v for k, v in action.items() if k != "tool"}
    TOOLS[action["tool"]](**args)
    return {"success": True, "action": action["tool"]}
