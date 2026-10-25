import os

# Keep tests hermetic: an empty value stops load_dotenv from enabling the real Jarvis model.
os.environ["JARVIS_BASE_URL"] = ""

import shutil

import pytest
from temporalio.testing import WorkflowEnvironment


@pytest.fixture
async def env():
    async with await WorkflowEnvironment.start_local(dev_server_existing_path=shutil.which("temporal")) as e:
        yield e
