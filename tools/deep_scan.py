#!/usr/bin/env python3
import os
import re
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path('.')
OUT = Path('scan_results')
OUT.mkdir(exist_ok=True)

issues = defaultdict(list)
stats = defaultdict(int)

def scan_py():
  for p in ROOT.rglob('*.py'):
    try:
      text = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
      continue
    # bare except
    for m in re.finditer(r'\n\s*except Exception:\s*\n', text):
      issues['bare_except'].append(f"{p}:{m.start()}")
    # unused import heuristic
    for imp in re.findall(r'\n\s*(?:from\s+([\w\.]+)\s+import\s+([\w\* ,]+)|import\s+([\w\., ]+))', text):
      pass  # keep simple: not auto-fixing here

def scan_ts():
  for p in list(ROOT.rglob('*.ts')) + list(ROOT.rglob('*.tsx')):
    try:
      text = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
      continue
    # any usage
    any_count = len(re.findall(r'\bany\b', text))
    if any_count:
      issues['ts_any'].append(f"{p}:{any_count}")
    # console.log
    if 'console.log' in text:
      issues['console_log'].append(str(p))
    # raw '< number' in text content pattern (line with ">< 123")
    for m in re.finditer(r'>\s*<\s*\d', text):
      issues['tsx_lt_text'].append(f"{p}:{m.start()}")

def scan_circular_py():
  # naive: map file-> list of modules it imports
  imap = {}
  files = list(ROOT.rglob('*.py'))
  for p in files:
    try:
      text = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
      continue
    mods = re.findall(r'\n\s*from\s+([\w\.]+)\s+import', text)
    imap[str(p)] = set(mods)
  # detect simple two-way cycles
  for f1, deps1 in imap.items():
    for f2, deps2 in imap.items():
      if f1>=f2: continue
      name1 = Path(f1).stem
      name2 = Path(f2).stem
      if any(name2 in d for d in deps1) and any(name1 in d for d in deps2):
        issues['circular_py'].append(f"{f1} <-> {f2}")

def write_report():
  report = {
    'summary': {k: len(v) for k,v in issues.items()},
    'issues': issues,
  }
  OUT.joinpath('deep_scan.json').write_text(json.dumps(report, indent=2))
  print('Deep scan complete. Wrote scan_results/deep_scan.json')

if __name__ == '__main__':
  scan_py(); scan_ts(); scan_circular_py(); write_report()

