import time

from temporalio import activity

from backend.agent.jarvis_agent import invoke_agent


@activity.defn
def agent_activity(message: str, slow_seconds: int = 0) -> dict:
    # Demo only: a slow first attempt gives time to kill the worker. Heartbeats let
    # Temporal notice a dead worker quickly; the retry skips the delay.
    if slow_seconds and activity.info().attempt == 1:
        for _ in range(slow_seconds):
            activity.heartbeat()
            time.sleep(1)
    return invoke_agent(message)
