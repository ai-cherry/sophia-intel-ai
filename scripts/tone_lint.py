import re, sys, pathlib
BANNED = ["as an AI", "I'm excited", "I'm excited", "hope this helps", "kindly", "just", "simply", "sit tight"]
bad = []
for arg in sys.argv[1:]:
    p = pathlib.Path(arg)
    if not p.is_file():
        continue
    try:
        text = p.read_text(errors="ignore")
    except Exception:
        continue
    hits = [w for w in BANNED if re.search(re.escape(w), text, re.IGNORECASE)]
    if hits:
        bad.append((p, hits))
if bad:
    for p, h in bad:
        print(f"{p}: banned phrases -> {h}")
    sys.exit(1)