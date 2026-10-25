import re

from backend.security.rules import BLOCK_THRESHOLD, EMAIL_RE, INTERNAL_DOMAIN, match_rules

EXTERNAL_DESTINATION_RISK = 60
REPRODUCED_INSTRUCTION_RISK = 40
OVERLAP_THRESHOLD = 0.8


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9@ ]+", " ", text.lower()).split())


def _is_instruction(sentence: str) -> bool:
    return bool(match_rules(sentence)) or (
        bool(EMAIL_RE.search(sentence)) and bool(re.search(r"\b(send|forward)\b", sentence, re.I)))


def _reproduced(sentence: str, output_text: str) -> bool:
    s, out = _norm(sentence), _norm(output_text)
    if s in out:
        return True
    tokens = s.split()
    return len(tokens) >= 4 and sum(t in set(out.split()) for t in tokens) / len(tokens) >= OVERLAP_THRESHOLD


def scan_output(input_message: str, agent_output: dict) -> dict:
    """Return {"propagation_detected", "risk", "reason", "evidence"}."""
    actions = agent_output.get("actions", [])
    output_text = " ".join(
        [agent_output.get("response", "")]
        + [str(v) for a in actions for v in a.values()])

    risk, reasons, evidence = 0, [], ""

    external = [a for a in actions if a.get("to") and not a["to"].lower().endswith(INTERNAL_DOMAIN)]
    if external:
        risk += EXTERNAL_DESTINATION_RISK
        reasons.append("Action targets external destination")
        evidence = f"{external[0]['tool']} -> {external[0]['to']}"

    for sentence in re.split(r"(?<=[.!?])\s+|\n+", input_message):
        if sentence.strip() and _is_instruction(sentence) and _reproduced(sentence, output_text):
            risk += REPRODUCED_INSTRUCTION_RISK
            reasons.append("Malicious instruction reproduced in agent output")
            evidence = sentence.strip()
            break

    phrases = match_rules(output_text)
    if phrases:
        risk += sum(w for _, w, _ in phrases)
        reasons.append("Agent output contains malicious instruction patterns")
        evidence = evidence or phrases[0][2]

    risk = min(100, risk)
    return {
        "propagation_detected": risk >= BLOCK_THRESHOLD,
        "risk": risk,
        "reason": " + ".join(reasons) or "No propagation detected",
        "evidence": evidence,
    }
