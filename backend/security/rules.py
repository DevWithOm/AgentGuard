import re

INTERNAL_DOMAIN = "@company.com"
BLOCK_THRESHOLD = 50

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# (threat, weight, pattern). Weights add up per distinct threat, capped at 100.
INPUT_RULES = [
    ("Instruction Override", 50, re.compile(
        r"\b(ignore|disregard|forget)\b[^.\n]{0,20}\b(previous|prior|above|earlier|your)\b[^.\n]{0,20}\binstructions?\b", re.I)),
    ("Secret Extraction", 45, re.compile(
        r"\b(reveal|show|print|leak|read|dump)\b[^.\n]{0,30}\b(credentials?|passwords?|secrets?|api keys?|tokens?)\b", re.I)),
    ("Security Bypass", 45, re.compile(
        r"\b(bypass|disable|turn off)\b[^.\n]{0,20}\b(security|safety|guard|filters?)\b", re.I)),
    ("Data Exfiltration", 35, re.compile(
        r"\b(send|forward|upload|email)\b[^.\n]{0,40}\b(all|every|files?|emails?|secrets?|credentials?|data)\b", re.I)),
    ("Sensitive File Access", 30, re.compile(
        r"\b(download|read|open)\b[^.\n]{0,30}\b(sensitive|credentials? file|ssh key)\b|/etc/passwd|\.env\b", re.I)),
    ("Concealment", 25, re.compile(
        r"\b(do not|don't|without)\b[^.\n]{0,10}\btell(ing)?\b[^.\n]{0,10}\b(the )?user\b", re.I)),
]


def match_rules(text: str) -> list[tuple[str, int, str]]:
    """Return (threat, weight, matched_text) for every rule that fires on text."""
    return [(t, w, m.group(0)) for t, w, rx in INPUT_RULES if (m := rx.search(text))]
