from backend.security.rules import BLOCK_THRESHOLD, match_rules


def scan_input(message: str) -> dict:
    """Return {"malicious", "risk" (0-100), "reason", "threat", "evidence"}."""
    hits = match_rules(message)
    risk = min(100, sum(w for _, w, _ in hits))
    threats = [t for t, _, _ in hits]
    if not hits:
        reason = "No malicious instructions detected"
    elif risk >= BLOCK_THRESHOLD:
        reason = "Malicious instructions detected: " + " + ".join(threats)
    else:
        reason = "Low-confidence signals, allowed: " + " + ".join(threats)
    return {
        "malicious": risk >= BLOCK_THRESHOLD,
        "risk": risk,
        "reason": reason,
        "threat": threats[0] if hits else None,
        "evidence": [e for _, _, e in hits],
    }
