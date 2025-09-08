#!/usr/bin/env python3
from pathlib import Path
import json
import ast


def top_level_docstring(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text())
        doc = ast.get_docstring(tree)
        return (doc or "").strip().splitlines()[0] if doc else ""
    except Exception:
        return ""


def main() -> int:
    scripts = {}
    for p in sorted(Path('scripts').glob('*.py')):
        scripts[p.name] = top_level_docstring(p)
    out = Path('scripts') / 'MANIFEST.json'
    out.write_text(json.dumps(scripts, indent=2))
    print(f"Wrote {out} with {len(scripts)} entries")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

