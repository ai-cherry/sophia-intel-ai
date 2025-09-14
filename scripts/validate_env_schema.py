#!/usr/bin/env python3
import json
import os
import sys
from typing import Dict

try:
    import jsonschema  # type: ignore
except Exception:
    print("jsonschema not installed; run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(__file__))


def parse_env_file(path: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not os.path.exists(path):
        return data
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data


def coerce_types(env: Dict[str, str]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for k, v in env.items():
        if k.endswith("_MS") or k.endswith("_MAX") or k.endswith("_RPM") or k.endswith("_BASE_MS"):
            try:
                out[k] = int(v)
                continue
            except Exception:
                pass
        out[k] = v
    return out


def main() -> int:
    schema_path = os.path.join(ROOT, "config", "env.schema.json")
    env_path = os.path.join(ROOT, ".env.master")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    env = parse_env_file(env_path)
    data = coerce_types(env)
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:  # type: ignore
        print(f"Validation failed: {e.message}", file=sys.stderr)
        return 1
    print(".env.master validates against env.schema.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

