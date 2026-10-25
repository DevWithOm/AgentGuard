export const TITLES = ["Incoming Email", "Input Guard", "AI Agent", "Output Guard", "Action"];

// Turn the /run result into one {state, rows, risk?, quote?} per pipeline stage.
export function deriveStages(r) {
  const inp = r.input, out = r.output;
  const blockedAtInput = r.stage === "INPUT_GUARD" && r.status === "BLOCKED";
  const blockedAtOutput = r.stage === "OUTPUT_GUARD" && r.status === "BLOCKED";
  // When blocked, show the external action that caused it rather than a harmless internal one.
  const actions = r.agent?.actions ?? [];
  const act = (blockedAtOutput && actions.find((a) => !a.to?.endsWith("@company.com"))) || actions[0];
  return [
    { state: "passed", quote: r.message },
    {
      state: inp.malicious ? "blocked" : inp.risk > 0 ? "warning" : "passed",
      risk: inp.risk,
      rows: [
        ["Risk Score", `${inp.risk}/100`],
        ["Threat", inp.threat || "None"],
        ["Status", inp.malicious ? "BLOCKED" : inp.risk > 0 ? "ALLOWED (low confidence)" : "PASSED"],
      ],
      quote: inp.evidence.join(" | "),
    },
    r.agent
      ? { state: "passed", rows: [["Model", r.model], ["Status", "Executed"]], quote: r.agent.response }
      : { state: "skipped", rows: [["Model", r.model], ["Status", "Not executed"]] },
    out
      ? {
          state: out.propagation_detected ? "blocked" : "passed",
          risk: out.risk,
          rows: [["Propagation Risk", `${out.risk}/100`], ["Status", out.propagation_detected ? "BLOCKED" : "PASSED"]],
          quote: out.evidence,
        }
      : { state: "skipped", rows: [["Status", "Not reached"]] },
    blockedAtInput || !act
      ? { state: "skipped", rows: [["Status", blockedAtInput ? "Not reached" : "No action requested"]] }
      : {
          state: blockedAtOutput ? "blocked" : "passed",
          rows: [["Action", act.tool], ["Target", act.to], ["Status", blockedAtOutput ? "BLOCKED" : "SUCCESS (mock)"]],
        },
  ];
}
