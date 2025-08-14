import re, textwrap
BANNED = [
    r"\bas an ai\b", r"\bi'?m (?:excited|happy)\b", r"\bhope this helps\b",
    r"\bkindly\b", r"\bjust\b", r"\bsimply\b", r"\bsit tight\b"
]
SECTIONS = ["Answer", "Actions", "Assumptions", "Risks / Next steps"]

def enforce(text: str) -> str:
    t = (text or "").strip()
    for pat in BANNED:
        t = re.sub(pat, "", t, flags=re.IGNORECASE)
    if not any(h in t for h in SECTIONS):
        t = (
            "Answer\n- " + t + "\n\n"
            "Actions\n- (add exact commands)\n\n"
            "Assumptions\n- (none)\n\n"
            "Risks / Next steps\n- (none)"
        )
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = "\n".join([ln if len(ln) <= 140 else textwrap.shorten(ln, width=140)
                   for ln in t.splitlines()])
    return t.strip()