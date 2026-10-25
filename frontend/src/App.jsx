import { useEffect, useRef, useState } from "react";
import { TITLES, deriveStages } from "./derive.js";

const ICONS = { pending: "○", running: "◌", passed: "✓", warning: "⚠", blocked: "🚨", skipped: "–" };
const STEP_MS = 650;
const STAGE_INDEX = { INPUT_GUARD: 1, AGENT: 2, OUTPUT_GUARD: 3, ACTION: 4 };
const sleep = (ms) => new Promise((res) => setTimeout(res, ms));

const verdict = (r) =>
  r.status === "COMPLETED" ? ["SAFE", "ok"] : r.stage === "INPUT_GUARD" ? ["BLOCKED · INPUT GUARD", "bad"] : ["BLOCKED · OUTPUT GUARD", "bad"];

const Row = ({ k, v }) => <div className="row">{k}: <b>{v}</b></div>;

function Stage({ title, stage }) {
  const { state, rows = [], risk, quote } = stage;
  const color = risk >= 50 ? "var(--bad)" : risk > 0 ? "var(--warn)" : "var(--ok)";
  return (
    <div className={`stage ${state}`}>
      <h3>{title}</h3>
      <div className="badge">{ICONS[state]}</div>
      <div className="state">{state.toUpperCase()}</div>
      {rows.map(([k, v]) => <Row key={k} k={k} v={v} />)}
      {risk !== undefined && <div className="bar"><i style={{ width: `${risk}%`, background: color }} /></div>}
      {quote && <div className="quote">{quote}</div>}
    </div>
  );
}

function Inbox({ emails, results, active, busy, onPick }) {
  const done = Object.values(results);
  const safe = done.filter((r) => r.status === "COMPLETED").length;
  const atInput = done.filter((r) => r.stage === "INPUT_GUARD" && r.status === "BLOCKED").length;
  const atOutput = done.filter((r) => r.stage === "OUTPUT_GUARD" && r.status === "BLOCKED").length;
  return (
    <section className="panel" id="inbox">
      <h2>Inbox</h2>
      {emails.map((e) => {
        const [label, tone] = results[e.id] ? verdict(results[e.id]) : ["NOT SCANNED", "dim"];
        return (
          <button key={e.id} className={`mail ${active === e.id ? "active" : ""}`} disabled={busy} onClick={() => onPick(e.id)}>
            <span className="from">{e.sender}</span>
            <span className="subj">{e.subject}</span>
            <span className={`tag ${tone}`}>{label}</span>
          </button>
        );
      })}
      {done.length === emails.length && emails.length > 0 && (
        <div className="row">{done.length} scanned · <b>{safe} safe</b> · <b>{atInput} blocked at Input Guard</b> · <b>{atOutput} blocked at Output Guard</b></div>
      )}
    </section>
  );
}

function SecurityEvent({ r }) {
  const atInput = r.stage === "INPUT_GUARD";
  return (
    <section className="panel" id="event">
      <h2>Security Event</h2>
      <div className="title">🚨 {atInput ? "PROMPT INJECTION BLOCKED" : "PROPAGATION DETECTED"}</div>
      <Row k="Risk" v={r.risk} />
      <Row k="Reason" v={r.reason} />
      <Row k="Evidence" v={atInput ? r.input.evidence.join(" | ") : r.output.evidence} />
      <Row k="Action" v="BLOCKED" />
    </section>
  );
}

function Temporal({ temporal, events, hint, error }) {
  return (
    <section className="panel" id="temporal">
      <h2>Temporal</h2>
      {error ? (
        <><Row k="Status" v="API unreachable" /><div className="quote">{error}</div></>
      ) : (
        <>
          <div className="grid">
            {temporal.id && <Row k="Workflow ID" v={temporal.id} />}
            <Row k="Status" v={temporal.status} />
            {temporal.stage && <Row k="Current Stage" v={temporal.stage} />}
          </div>
          {hint && <div className="hint">{hint}</div>}
          {events.map((e) => <div key={e} className="event-line">{e}</div>)}
          {temporal.id && (
            <div className="row">
              <a href={`http://localhost:8233/namespaces/default/workflows/${encodeURIComponent(temporal.id)}`} target="_blank" rel="noopener noreferrer">
                Open in Temporal UI ↗
              </a>
            </div>
          )}
        </>
      )}
    </section>
  );
}

export default function App() {
  const [active, setActive] = useState(null);
  const [busy, setBusy] = useState(false);
  const [stages, setStages] = useState(TITLES.map(() => ({ state: "pending" })));
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [temporal, setTemporal] = useState({ status: "IDLE — pick an email" });
  const [events, setEvents] = useState([]);
  const [hint, setHint] = useState(null);
  const [emails, setEmails] = useState([]);
  const [results, setResults] = useState({});
  const finished = useRef(false);
  const crash = useRef({ down: false, restored: false });

  useEffect(() => {
    fetch("/emails").then((r) => r.json()).then(setEmails).catch((e) => setError(e.message));
  }, []);

  const setStage = (i, stage) => setStages((s) => s.map((x, j) => (j === i ? stage : x)));
  const addEvents = (...lines) => setEvents((e) => [...e, ...lines]);

  // Live updates while /run is pending: current stage, plus worker disconnect/recovery.
  function onStatus(id, s) {
    if (finished.current || s.status === "PENDING") return;
    const c = crash.current;
    if (!s.worker_connected && !c.down) {
      c.down = true;
      addEvents("⚠ Worker disconnected", "Recovering workflow...");
    } else if (s.worker_connected && c.down && !c.restored) {
      c.restored = true;
      setHint(null);
      addEvents("✓ Temporal restored execution", "✓ Workflow resumed");
    }
    setTemporal({ id, status: c.down && !c.restored ? "RECOVERING" : s.status, stage: s.stage });
    const idx = STAGE_INDEX[s.stage];
    if (idx) setStages(TITLES.map((_, j) => ({ state: j < idx ? "passed" : j === idx ? "running" : "pending" })));
  }

  async function poll(id) {
    while (!finished.current) {
      try { onStatus(id, await (await fetch(`/status/${id}`)).json()); } catch { /* API busy; retry */ }
      await sleep(1000);
    }
  }

  // Show a stored result instantly, without replaying the animation.
  function showResult(id, r) {
    setActive(id); setResult(r); setError(null); setEvents([]); setHint(null);
    setStages(deriveStages(r));
    setTemporal({ id: r.workflow_id, status: r.status, stage: r.stage });
  }

  async function scanInbox() {
    setBusy(true); setResults({});
    for (const e of emails) {
      try {
        const res = await fetch("/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scenario: e.id }) });
        if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
        const r = await res.json();
        setResults((x) => ({ ...x, [e.id]: r }));
        showResult(e.id, r);
        await sleep(500);
      } catch (err) {
        setError(err.message);
        break;
      }
    }
    setBusy(false);
  }

  async function run(scenario) {
    const id = `agentguard-${Math.random().toString(16).slice(2, 10)}`;
    finished.current = false;
    crash.current = { down: false, restored: false };
    setBusy(true); setActive(scenario); setResult(null); setError(null); setEvents([]);
    setHint(scenario === "temporal_crash" ? "Kill the worker now:  pkill -9 -f backend.temporal.worker   then restart it:  .venv/bin/python -m backend.temporal.worker" : null);
    setTemporal({ id, status: "RUNNING" });
    setStages(TITLES.map(() => ({ state: "pending" })));
    setStage(0, { state: "running" });
    poll(id);
    try {
      const res = await fetch("/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scenario, workflow_id: id }) });
      if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
      const r = await res.json();
      finished.current = true;
      setHint(null);
      const final = deriveStages(r);
      for (let i = 0; i < final.length; i++) {
        if (final[i].state !== "skipped") { setStage(i, { state: "running" }); await sleep(STEP_MS); }
        setStage(i, final[i]);
      }
      setResult(r);
      setResults((x) => ({ ...x, [scenario]: r }));
      setTemporal({ id, status: r.status, stage: r.stage });
    } catch (e) {
      finished.current = true;
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <header>
        <h1>AGENT<span>GUARD</span></h1>
        <p>AI Agent Security &amp; Propagation Defense</p>
      </header>
      <nav id="scenarios">
        <button disabled={busy || !emails.length} onClick={scanInbox}>Scan Inbox</button>
        <button className={active === "temporal_crash" ? "active" : ""} disabled={busy} onClick={() => run("temporal_crash")}>Temporal Crash</button>
      </nav>
      <main>
        <Inbox emails={emails} results={results} active={active} busy={busy}
               onPick={(id) => (results[id] ? showResult(id, results[id]) : run(id))} />
        <section id="pipeline">
          {stages.map((s, i) => <Stage key={i} title={TITLES[i]} stage={s} />)}
        </section>
        {result?.status === "BLOCKED" && <SecurityEvent r={result} />}
        <Temporal temporal={temporal} events={events} hint={hint} error={error} />
      </main>
    </>
  );
}
