#!/usr/bin/env python3
from pathlib import Path

def main() -> int:
    scripts = list(Path('scripts').glob('**/*.py'))
    for script in scripts:
        try:
            content = script.read_text().lower()
        except Exception:
            continue
        if 'artemis' in content:
            print(f"ARTEMIS: {script}")
        elif 'load_dotenv' in content:
            print(f"DOTENV:   {script}")
        elif not content.strip():
            print(f"EMPTY:    {script}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

