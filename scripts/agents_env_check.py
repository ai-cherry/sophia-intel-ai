#!/usr/bin/env python3
"""
Environment preflight validator for Sophia-Intel AI

Checks for common architecture/runtime mismatches and reports clear remediation.

Behavior
- Exit code 0 for success and warnings
- Exit code 2 for hard failures (e.g., arch mismatch, broken wheels)

Usage
- scripts/agents_env_check.py
- scripts/agents_env_check.py --json
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass
class CheckResult:
    status: str  # "ok" | "warn" | "fail"
    message: str
    details: Dict[str, str] = field(default_factory=dict)


@dataclass
class EnvReport:
    python_version: str
    python_arch: str
    platform: str
    is_rosetta: bool
    checks: List[CheckResult]

    def to_json(self) -> str:
        return json.dumps(
            {
                "python_version": self.python_version,
                "python_arch": self.python_arch,
                "platform": self.platform,
                "is_rosetta": self.is_rosetta,
                "checks": [asdict(c) for c in self.checks],
                "summary": self.summary(),
            },
            indent=2,
        )

    def summary(self) -> Dict[str, int]:
        counts = {"ok": 0, "warn": 0, "fail": 0}
        for c in self.checks:
            counts[c.status] = counts.get(c.status, 0) + 1
        return counts


def detect_rosetta() -> bool:
    if sys.platform != "darwin":
        return False
    try:
        # sysctl -in sysctl.proc_translated returns 1 when under Rosetta 2
        out = subprocess.check_output(["/usr/sbin/sysctl", "-in", "sysctl.proc_translated"], stderr=subprocess.DEVNULL)
        return out.decode().strip() == "1"
    except Exception:
        return False


def check_python() -> List[CheckResult]:
    results: List[CheckResult] = []
    py_ver = sys.version.split()[0]
    machine = platform.machine()
    arch_bits = platform.architecture()[0]
    is_64 = sys.maxsize > 2**32
    arch_detail = f"{machine}/{arch_bits}"

    # Version policy: prefer 3.11.x but warn only
    if not py_ver.startswith("3.11"):
        results.append(
            CheckResult(
                status="warn",
                message=f"Python {py_ver} detected; 3.11.x recommended for dev",
                details={
                    "recommendation": "Install via pyenv and set with .python-version",
                },
            )
        )
    else:
        results.append(CheckResult(status="ok", message=f"Python version {py_ver}", details={}))

    results.append(
        CheckResult(status="ok", message=f"Python arch {arch_detail}", details={"sys.maxsize": str(sys.maxsize)})
    )

    if sys.platform == "darwin":
        # Common macOS pitfall: Intel Python under Rosetta on Apple Silicon
        try:
            uname_m = subprocess.check_output(["/usr/bin/uname", "-m"]).decode().strip()
        except Exception:
            uname_m = machine

        if uname_m == "arm64" and machine == "x86_64":
            results.append(
                CheckResult(
                    status="warn",
                    message="Running x86_64 Python on arm64 macOS (Rosetta)",
                    details={
                        "impact": "Binary wheels may mismatch (e.g., pydantic-core)",
                        "remediation": "Use arm64 Python or devcontainer; avoid mixing Rosetta terminals",
                    },
                )
            )

    # 64-bit requirement check
    if not is_64:
        results.append(
            CheckResult(
                status="fail",
                message="32-bit Python not supported",
                details={"remediation": "Install 64-bit Python (via pyenv or system package manager)"},
            )
        )

    return results


def check_pydantic_core() -> List[CheckResult]:
    results: List[CheckResult] = []
    try:
        import pydantic_core

        details: Dict[str, str] = {
            "module": getattr(pydantic_core, "__file__", "unknown"),
            "version": getattr(pydantic_core, "__version__", "unknown"),
        }

        # Attempt to detect whether it's a binary wheel vs source build
        module_path = str(getattr(pydantic_core, "__file__", ""))
        if module_path.endswith((".so", ".dylib", ".pyd")):
            details["build"] = "binary"
        else:
            # Best-effort: source builds typically put artifacts under pydantic_core/_pydantic_core.*
            details["build"] = "source_or_pure"

        results.append(CheckResult(status="ok", message="pydantic_core import ok", details=details))

    except Exception as e:
        machine = platform.machine()
        details = {
            "error": str(e),
            "remediation_mac_arm64": (
                "pip3 uninstall pydantic-core pydantic && "
                "pip3 install --force-reinstall pydantic pydantic-core"
            ),
            "source_build": "brew install rust && pip3 install --no-binary :all: pydantic-core pydantic",
        }
        if sys.platform == "darwin" and machine == "arm64":
            details["note"] = "Ensure Python is arm64; avoid Rosetta terminals mixing x86_64 wheels"
        results.append(CheckResult(status="fail", message="pydantic_core import failed", details=details))
    return results


def main() -> int:
    want_json = "--json" in sys.argv
    checks: List[CheckResult] = []

    py = check_python()
    checks.extend(py)

    # Rosetta detection
    rosetta = detect_rosetta()
    if rosetta:
        checks.append(
            CheckResult(
                status="warn",
                message="Running under Rosetta translation (macOS)",
                details={
                    "impact": "Binary wheels may mismatch host arch",
                    "remediation": "Use arm64 terminal/Python or devcontainer",
                },
            )
        )

    # pydantic_core import check (common failure)
    checks.extend(check_pydantic_core())

    report = EnvReport(
        python_version=sys.version.split()[0],
        python_arch=f"{platform.machine()}/{platform.architecture()[0]}",
        platform=sys.platform,
        is_rosetta=rosetta,
        checks=checks,
    )

    has_fail = any(c.status == "fail" for c in checks)

    if want_json:
        print(report.to_json())
    else:
        # Human-readable summary
        print("Sophia-Intel AI Environment Preflight\n")
        print(f"Python: {report.python_version} ({report.python_arch}) on {report.platform}")
        if rosetta:
            print("Note: Rosetta translation detected (macOS)")
        print("")
        for c in checks:
            icon = {"ok": "✅", "warn": "⚠️", "fail": "❌"}[c.status]
            print(f"{icon} {c.message}")
            if c.details:
                for k, v in c.details.items():
                    print(f"   - {k}: {v}")
        print("")
        summary = report.summary()
        print(f"Summary: ok={summary['ok']} warn={summary['warn']} fail={summary['fail']}")

    # 0 on success/warn, 2 on fail (to allow gating)
    return 2 if has_fail else 0


if __name__ == "__main__":
    sys.exit(main())

