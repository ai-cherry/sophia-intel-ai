#!/usr/bin/env python3
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

import click
import httpx

from .policy_guard import PolicyGuard, GuardResult


CONFIG_DIR = Path("config")
ALIASES_PATH = CONFIG_DIR / "model_aliases.json"


def load_aliases() -> dict:
    if ALIASES_PATH.exists():
        try:
            return json.loads(ALIASES_PATH.read_text())
        except Exception:
            return {}
    return {}


def resolve_model(model: Optional[str], alias: Optional[str]) -> str:
    aliases = load_aliases()
    if alias:
        if alias not in aliases:
            raise click.ClickException(f"Unknown alias '{alias}'. Edit {ALIASES_PATH} to add it.")
        return aliases[alias]
    if model:
        return model
    # Default if nothing provided
    default = aliases.get("grok-fast") or aliases.get("magistral-small") or next(iter(aliases.values()), None)
    if not default:
        raise click.ClickException("No model provided and no aliases configured. Use --model or add aliases.")
    return default


def portkey_headers(model: str) -> dict:
    api_key = os.getenv("PORTKEY_API_KEY", "")
    if not api_key:
        raise click.ClickException("Missing PORTKEY_API_KEY. Use ESC→dotenv into .env.master and source it.")
    provider = model.split("/", 1)[0]
    vk_env = f"PORTKEY_VK_{provider.upper()}"
    vk = os.getenv(vk_env, "")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-portkey-provider": provider,
    }
    if vk:
        headers["x-portkey-virtual-key"] = vk
    return headers


def portkey_models() -> list[str]:
    api_key = os.getenv("PORTKEY_API_KEY", "")
    if not api_key:
        return []
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get("https://api.portkey.ai/v1/models", headers={"Authorization": f"Bearer {api_key}"})
            if r.status_code != 200:
                return []
            data = r.json()
            return [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
    except Exception:
        return []


def portkey_chat(model: str, messages: list[dict], max_tokens: int = 512, temperature: float = 0.2) -> dict:
    headers = portkey_headers(model)
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post("https://api.portkey.ai/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _is_thinking_model(model: str, alias: Optional[str]) -> bool:
    if "thinking" in model.lower():
        return True
    try:
        tops = json.loads((CONFIG_DIR / "top_models.json").read_text())
        for m in tops:
            if isinstance(m, dict) and m.get("id") == model:
                tags = m.get("tags") or []
                return any(t == "thinking" for t in tags)
    except Exception:
        pass
    if alias and "thinking" in alias.lower():
        return True
    return False


PRICE_PER_KTOK = {
    "x-ai/grok-code-fast-1": (0.2, 0.8),
    "mistralai/magistral-small-2506": (0.05, 0.15),
    "mistralai/magistral-medium-2506": (0.15, 0.6),
    "mistralai/magistral-medium-2506-thinking": (0.2, 0.8),
    "deepseek/v3-0324": (0.02, 0.08),
    "deepseek/v3.1": (0.03, 0.1),
    "google/gemini-2.5-flash": (0.05, 0.1),
    "google/gemini-2.5-pro": (1.0, 2.0),
}


def _estimate_cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    inp, outp = PRICE_PER_KTOK.get(model, (0.5, 1.5))
    return (in_tokens / 1000.0) * inp + (out_tokens / 1000.0) * outp


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="0.1.0")
def main() -> None:
    """Sophia CLI — chat · plan · code · apply (Portkey-only)"""


@main.command()
@click.option("--model", "model_id", help="Full model id, e.g. mistralai/magistral-small-2506")
@click.option("--alias", "alias", help="Alias from config/model_aliases.json, e.g. magistral-small")
@click.option("--input", "input_text", help="Prompt text")
@click.option("--input-file", "input_file", type=click.Path(exists=True), help="Read prompt from file")
@click.option("--json-output", is_flag=True, help="Print raw JSON response instead of text")
@click.option("--max-input", type=int, default=8000, show_default=True, help="Max input tokens allowed")
@click.option("--max-output", type=int, default=800, show_default=True, help="Max output tokens to request")
@click.option("--max-cost", type=float, default=None, help="Max estimated USD cost for call")
@click.option("--thinking", is_flag=True, help="Allow thinking models")
def chat(model_id: Optional[str], alias: Optional[str], input_text: Optional[str], input_file: Optional[str], json_output: bool, max_input: int, max_output: int, max_cost: Optional[float], thinking: bool) -> None:
    """Quick chat/completions via Portkey (no MCP)."""
    model = resolve_model(model_id, alias)
    if not input_text and input_file:
        input_text = Path(input_file).read_text()
    if not input_text:
        click.echo("Enter prompt (Ctrl-D to finish):\n", err=True)
        lines = sys.stdin.read()
        input_text = lines.strip()
    if _is_thinking_model(model, alias) and not thinking:
        raise click.ClickException("Thinking models require --thinking flag.")
    messages = [{"role": "user", "content": input_text}]
    est_in = sum(_estimate_tokens(m.get("content", "")) for m in messages)
    if est_in > max_input:
        raise click.ClickException(f"Input too large: ~{est_in} tokens exceeds --max-input {max_input}")
    if max_cost is not None:
        est = _estimate_cost_usd(model, est_in, max_output)
        if est > max_cost:
            raise click.ClickException(f"Estimated cost ${est:.2f} exceeds --max-cost ${max_cost:.2f}")
    try:
        try:
            avail = portkey_models()
            if avail and model not in avail:
                raise click.ClickException(f"Model '{model}' not available via Portkey")
        except click.ClickException:
            raise
        except Exception:
            pass
        data = portkey_chat(model, messages, max_tokens=max_output)
    except httpx.HTTPStatusError as e:
        raise click.ClickException(f"Portkey error: {e.response.status_code} {e.response.text[:200]}")
    except Exception as e:
        raise click.ClickException(str(e))
    if json_output:
        click.echo(json.dumps(data, indent=2))
        return
    try:
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        click.echo(content)
    except Exception:
        click.echo(json.dumps(data, indent=2))


@main.command()
@click.option("--alias", "alias", help="Model alias for planning (see config/model_aliases.json)")
@click.option("--model", "model_id", help="Explicit model id")
@click.option("--task", "task", required=True, help="Coding task to plan")
@click.option("--max-input", type=int, default=4000, show_default=True)
@click.option("--max-output", type=int, default=800, show_default=True)
@click.option("--max-cost", type=float, default=None)
@click.option("--thinking", is_flag=True)
def plan(alias: Optional[str], model_id: Optional[str], task: str, max_input: int, max_output: int, max_cost: Optional[float], thinking: bool) -> None:
    """Generate a step-by-step coding plan (lightweight template)."""
    model = resolve_model(model_id, alias)
    if _is_thinking_model(model, alias) and not thinking:
        raise click.ClickException("Thinking models require --thinking flag.")
    system = "You are a senior engineer. Produce a concise, numbered plan with files to edit and tests to run."
    user = f"Task: {task}\nConstraints: keep changes minimal, follow repo style, list impacted files and tests."
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        est_in = sum(_estimate_tokens(m.get("content", "")) for m in messages)
        if est_in > max_input:
            raise click.ClickException(f"Input too large: ~{est_in} tokens exceeds --max-input {max_input}")
        if max_cost is not None:
            est = _estimate_cost_usd(model, est_in, max_output)
            if est > max_cost:
                raise click.ClickException(f"Estimated cost ${est:.2f} exceeds --max-cost ${max_cost:.2f}")
        data = portkey_chat(model, messages, max_tokens=max_output, temperature=0.1)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        click.echo(content)
    except Exception as e:
        raise click.ClickException(str(e))


@main.command()
@click.option("--alias", "alias", help="Model alias for coding (see config/model_aliases.json)")
@click.option("--model", "model_id", help="Explicit model id")
@click.option("--task", required=True, help="Coding task to perform")
@click.option("--paths", multiple=True, help="Target files/dirs (globs allowed)")
@click.option("--out", "out_path", type=click.Path(), default="artifacts/cli/patch.json", help="Where to save proposed changes (JSON)")
@click.option("--max-changes", type=int, default=20, help="Cap number of file changes")
@click.option("--max-input", type=int, default=8000, show_default=True)
@click.option("--max-output", type=int, default=1800, show_default=True)
@click.option("--max-cost", type=float, default=None)
@click.option("--thinking", is_flag=True)
def code(alias: Optional[str], model_id: Optional[str], task: str, paths: List[str], out_path: str, max_changes: int, max_input: int, max_output: int, max_cost: Optional[float], thinking: bool) -> None:
    """Propose concrete edits as JSON changes using LLM (Portkey)."""
    model = resolve_model(model_id, alias)
    if _is_thinking_model(model, alias) and not thinking:
        raise click.ClickException("Thinking models require --thinking flag.")
    target_hint = ", ".join(paths) if paths else "repository"
    system = (
        "You are a senior engineer. Produce a STRICT JSON array of file changes. "
        "Each item is {\"path\": string, \"content\": string}. "
        "No prose, no code fences, JSON only."
    )
    user = (
        f"Task: {task}\n"
        f"Scope: {target_hint}\n"
        f"Constraints: At most {max_changes} files; minimal diff; keep style; include full target file content as 'content'."
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        est_in = sum(_estimate_tokens(m.get("content", "")) for m in messages)
        if est_in > max_input:
            raise click.ClickException(f"Input too large: ~{est_in} tokens exceeds --max-input {max_input}")
        if max_cost is not None:
            est = _estimate_cost_usd(model, est_in, max_output)
            if est > max_cost:
                raise click.ClickException(f"Estimated cost ${est:.2f} exceeds --max-cost ${max_cost:.2f}")
        data = portkey_chat(model, messages, max_tokens=max_output, temperature=0.1)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Try to extract JSON
        parsed: Any
        try:
            parsed = json.loads(content)
        except Exception:
            # Attempt to strip code fences if present
            cleaned = content.strip().strip("` ")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].lstrip()
            parsed = json.loads(cleaned)
        if not isinstance(parsed, list):
            raise click.ClickException("Model did not return a JSON array of changes.")
        # Ensure directories
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(parsed, indent=2))
        click.echo(f"Wrote proposed changes to {out_file}")
    except httpx.HTTPStatusError as e:
        raise click.ClickException(f"Portkey error: {e.response.status_code} {e.response.text[:200]}")
    except Exception as e:
        raise click.ClickException(str(e))


@main.command()
@click.argument("changes_file", type=click.Path(exists=True))
@click.option("--task", required=True, help="Commit message task summary")
@click.option("--branch", default=None, help="Branch to create/use (default: feat/auto/<date>-<slug>)")
@click.option("--no-validate", is_flag=True, help="Skip validation checks")
@click.option("--workspace", default=".", type=click.Path(), help="Workspace root (default: current dir)")
def apply(changes_file: str, task: str, branch: Optional[str], no_validate: bool, workspace: str) -> None:
    """Apply JSON changes safely with policy guard; branch + commit; optional validation."""
    ws = Path(workspace).resolve()
    guard = PolicyGuard(workspace=ws)
    # Load changes
    try:
        changes: List[Dict[str, Any]] = json.loads(Path(changes_file).read_text())
    except Exception as e:
        raise click.ClickException(f"Failed to read changes file: {e}")
    if not isinstance(changes, list) or not all(isinstance(c, dict) for c in changes):
        raise click.ClickException("Changes file must be a JSON array of {path, content}")
    # Ensure git repo
    def _git(*args: str) -> str:
        res = subprocess.run(["git", *args], cwd=str(ws), capture_output=True, text=True)
        if res.returncode != 0:
            raise click.ClickException(f"git {' '.join(args)} failed: {res.stderr.strip()}")
        return res.stdout.strip()
    try:
        _git("rev-parse", "--is-inside-work-tree")
    except click.ClickException:
        raise click.ClickException("Not a git repository. Initialize git in workspace before applying.")
    # Create branch if provided or session branch
    if not branch:
        import datetime, re
        slug = re.sub(r"[^a-z0-9-]+", "-", task.lower()).strip("-")[:40] or "task"
        branch = f"feat/auto/{datetime.datetime.now().strftime('%Y%m%d')}-{slug}"
    # Checkout/create
    try:
        _git("checkout", "-B", branch)
    except click.ClickException as e:
        raise click.ClickException(f"Failed to create/switch branch {branch}: {e}")
    # Apply changes with policy
    applied_count = 0
    violations: List[str] = []
    changed_files: List[str] = []
    for change in changes:
        path = change.get("path")
        content = change.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            violations.append(f"Invalid change entry (path/content): {change}")
            continue
        result: GuardResult = guard.apply_change(path, content)
        if not result.ok:
            violations.append(f"Denied {path}: {result.reason}")
            continue
        applied_count += 1
        changed_files.append(path)
    if violations:
        click.echo("Some changes were denied by policy:", err=True)
        for v in violations:
            click.echo(f"  - {v}", err=True)
    # Stage and commit
    _git("add", ".")
    shortid = _git("rev-parse", "--short", "HEAD")
    msg = f"[sophia] {task} (#{shortid})"
    _git("commit", "-m", msg)
    click.echo(f"Committed {applied_count} files on branch {branch}")
    if changed_files:
        click.echo("Files changed:")
        for p in sorted(set(changed_files)):
            click.echo(f"  - {p}")
    # Validation (basic by default)
    if not no_validate:
        errors = _basic_validation(ws, [c.get("path", "") for c in changes])
        # Optional ruff
        try:
            res = subprocess.run(["ruff", "--version"], capture_output=True, text=True)
            if res.returncode == 0:
                targets = [p for p in {c.get("path", "") for c in changes} if isinstance(p, str) and p.endswith('.py')]
                if targets:
                    rr = subprocess.run(["ruff", "check", *targets], cwd=str(ws), capture_output=True, text=True)
                    if rr.returncode != 0:
                        errors.append(f"ruff: {rr.stdout}\n{rr.stderr}".strip())
        except Exception:
            pass
        # Optional pytest subset
        try:
            pr = subprocess.run(["pytest", "--version"], capture_output=True, text=True)
            if pr.returncode == 0:
                selectors = []
                for p in {c.get("path", "") for c in changes}:
                    if isinstance(p, str) and (p.startswith('tests/') or Path(p).name.startswith('test_')):
                        selectors.append(Path(p).stem)
                if selectors:
                    k = " or ".join(selectors)
                    px = subprocess.run(["pytest", "-q", "-k", k], cwd=str(ws), capture_output=True, text=True)
                    if px.returncode != 0:
                        errors.append(f"pytest: {px.stdout}\n{px.stderr}".strip())
        except Exception:
            pass
        if errors:
            for e in errors:
                click.echo(f"VALIDATE: {e}", err=True)
            raise click.ClickException("Validation failed. See errors above.")
        click.echo("Validation passed.")


def _basic_validation(workspace: Path, paths: List[str]) -> List[str]:
    """Very lightweight validation: py syntax for .py; existence for others."""
    errs: List[str] = []
    unique_paths = sorted({p for p in paths if isinstance(p, str) and p})
    for p in unique_paths:
        fp = (workspace / p).resolve()
        if not fp.exists():
            errs.append(f"Missing after apply: {p}")
            continue
        if fp.suffix == ".py":
            res = subprocess.run([sys.executable, "-m", "py_compile", str(fp)], capture_output=True, text=True)
            if res.returncode != 0:
                errs.append(f"Py syntax error in {p}: {res.stderr.strip()}")
    return errs
