import pytest

from backend.agent.jarvis_agent import invoke_agent
from backend.mock_data.emails import EMAILS, email_text
from backend.security.input_guard import scan_input
from backend.security.output_guard import scan_output


def verdict(email):
    msg = email_text(email)
    if scan_input(msg)["malicious"]:
        return "input"
    return "output" if scan_output(msg, invoke_agent(msg))["propagation_detected"] else "safe"


@pytest.mark.parametrize("email", EMAILS, ids=lambda e: e["id"])
def test_email_gets_designed_verdict(email):
    assert verdict(email) == email["expected"]
