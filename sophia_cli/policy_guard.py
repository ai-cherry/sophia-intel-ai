from __future__ import annotations
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class GuardResult:
    ok: bool
    reason: Optional[str] = None


class PolicyGuard:
    """
    Enforces filesystem write policy loaded from mcp/policies/filesystem.yml.
    - deny paths (prefix match)
    - allowlist (optional)
    - backup_on_write
    - path safety checks
    """

    def __init__(self, workspace: Path, workspace_name: Optional[str] = None):
        self.workspace = workspace.resolve()
        self.workspace_name = workspace_name or os.getenv("WORKSPACE_NAME", "sophia")
        self.policy = self._load_policy()

    def _load_policy(self) -> dict:
        cfg = self.workspace / "mcp" / "policies" / "filesystem.yml"
        data: dict = {}
        if cfg.exists():
            try:
                data = yaml.safe_load(cfg.read_text()) or {}
            except Exception:
                data = {}
        root = (data.get("filesystem_policies") or {}).get(self.workspace_name, {})
        return {
            "write_allowed_paths": list(root.get("write_allowed_paths", [])),
            "write_denied_paths": list(root.get("write_denied_paths", [])),
            "backup_on_write": bool(root.get("backup_on_write", True)),
        }

    def _safe_target(self, rel_path: str) -> Optional[Path]:
        # Disallow absolute
        if os.path.isabs(rel_path):
            return None
        # Normalize .. and collapse
        target = (self.workspace / rel_path).resolve()
        try:
            target.relative_to(self.workspace)
        except Exception:
            return None
        # Disallow dotfiles by default (except within known code dirs)
        parts = target.relative_to(self.workspace).parts
        if any(part.startswith(".") for part in parts):
            return None
        return target

    def _is_allowed(self, target: Path) -> bool:
        s = "/" + str(target.relative_to(self.workspace)).replace(os.sep, "/")
        # Deny first
        for deny in self.policy["write_denied_paths"]:
            if s.startswith(deny):
                return False
        allowed = self.policy["write_allowed_paths"]
        if not allowed:
            return True
        return any(s.startswith(a) for a in allowed)

    def apply_change(self, rel_path: str, content: str) -> GuardResult:
        target = self._safe_target(rel_path)
        if target is None:
            return GuardResult(False, "invalid_path")
        if not self._is_allowed(target):
            return GuardResult(False, "denied_by_policy")
        target.parent.mkdir(parents=True, exist_ok=True)
        if self.policy.get("backup_on_write", True) and target.exists():
            bak = target.with_suffix(target.suffix + ".bak")
            try:
                shutil.copy2(target, bak)
            except Exception:
                pass
        try:
            target.write_text(content)
        except Exception as e:
            return GuardResult(False, f"write_failed:{e}")
        return GuardResult(True)

