# AgentGuard

Security and containment layer for AI agents. Untrusted input passes through an
**Input Guard**, the **AI agent**, and an **Output Guard** before any action runs.
The whole pipeline runs as a **Temporal** workflow, so it survives crashes.

```
Untrusted Input -> Input Guard -> AI Agent -> Output Guard -> Action
```

## Setup

```bash
/opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
brew install temporal
cd frontend && npm install && npm run build && cd ..
cp .env.example .env   # optional: fill in the Jarvis Labs values
```

Without `JARVIS_BASE_URL` the agent is a deterministic mock.

## Run (three terminals)

```bash
temporal server start-dev
.venv/bin/python -m backend.temporal.worker
.venv/bin/uvicorn backend.api.server:app --port 8000
```

Dashboard: http://localhost:8000 · Temporal UI: http://localhost:8233

For frontend development run `cd frontend && npm run dev` (http://localhost:5173, proxies the API on port 8000).

## Crash demo

Click **Temporal Crash**, and while the AI Agent stage is running:

```bash
pkill -9 -f backend.temporal.worker
.venv/bin/python -m backend.temporal.worker
```

The dashboard shows the worker disconnecting, then Temporal resuming the workflow.

## Tests

```bash
.venv/bin/pytest
```
