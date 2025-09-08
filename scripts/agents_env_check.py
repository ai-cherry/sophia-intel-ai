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
from pathlib import Path
from typing import Dict, List


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
        out = subprocess.check_output(
            ["/usr/sbin/sysctl", "-in", "sysctl.proc_translated"], stderr=subprocess.DEVNULL
        )
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
        CheckResult(
            status="ok",
            message=f"Python arch {arch_detail}",
            details={"sys.maxsize": str(sys.maxsize)},
        )
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
                details={
                    "remediation": "Install 64-bit Python (via pyenv or system package manager)"
                },
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
        results.append(
            CheckResult(status="fail", message="pydantic_core import failed", details=details)
        )
    return results


def check_required_dependencies() -> List[CheckResult]:
    """Check critical runtime dependencies"""
    results: List[CheckResult] = []
    critical_deps = ["fastapi", "uvicorn", "pydantic", "redis", "httpx"]

    for dep in critical_deps:
        try:
            __import__(dep)
            results.append(CheckResult(status="ok", message=f"{dep} available", details={}))
        except ImportError:
            results.append(
                CheckResult(
                    status="fail",
                    message=f"{dep} not available",
                    details={"remediation": "pip3 install -r requirements/base.txt"},
                )
            )

    return results


def check_environment_files() -> List[CheckResult]:
    """Validate .env.* configuration consistency"""
    results: List[CheckResult] = []
    root = Path.cwd()

    # Check for .python-version consistency
    python_version_file = root / ".python-version"
    if python_version_file.exists():
        try:
            blessed_version = python_version_file.read_text().strip()
            current_version = sys.version.split()[0]
            if current_version.startswith(blessed_version[:4]):  # Match major.minor
                results.append(
                    CheckResult(
                        status="ok",
                        message=f"Python version matches .python-version ({blessed_version})",
                        details={},
                    )
                )
            else:
                results.append(
                    CheckResult(
                        status="warn",
                        message=f"Python {current_version} doesn't match .python-version ({blessed_version})",
                        details={"remediation": "Use pyenv or update .python-version"},
                    )
                )
        except Exception as e:
            results.append(
                CheckResult(status="warn", message=f"Cannot read .python-version: {e}", details={})
            )

    # Check for artemis env in secure location
    artemis_locations = [
        Path.home() / ".config" / "artemis" / "env",
        root / ".env.artemis",
        root / ".env",
    ]

    artemis_found = False
    for loc in artemis_locations:
        if loc.exists():
            results.append(
                CheckResult(status="ok", message=f"Found artemis env: {loc}", details={})
            )
            artemis_found = True
            break

    if not artemis_found:
        results.append(
            CheckResult(
                status="warn",
                message="No artemis env found",
                details={"remediation": "Run: make artemis-setup"},
            )
        )

    # Check environment file separation
    sophia_env = root / ".env.sophia"
    ai_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "GROK_API_KEY", "XAI_API_KEY"]

    if sophia_env.exists():
        content = sophia_env.read_text()
        contaminated_keys = [key for key in ai_keys if key in content]
        if contaminated_keys:
            results.append(
                CheckResult(
                    status="warn",
                    message="AI model keys found in .env.sophia",
                    details={
                        "contaminated_keys": ", ".join(contaminated_keys),
                        "remediation": "Move AI keys to ~/.config/artemis/env",
                    },
                )
            )
        else:
            results.append(
                CheckResult(status="ok", message="Clean environment separation", details={})
            )

    return results


def check_docker_availability() -> List[CheckResult]:
    """Check Docker setup for devcontainer option"""
    results: List[CheckResult] = []

    try:
        subprocess.check_output(["docker", "--version"], stderr=subprocess.DEVNULL)
        results.append(CheckResult(status="ok", message="Docker available", details={}))

        # Check if Docker is running
        try:
            subprocess.check_output(["docker", "info"], stderr=subprocess.DEVNULL)
            results.append(CheckResult(status="ok", message="Docker daemon running", details={}))
        except subprocess.CalledProcessError:
            results.append(
                CheckResult(
                    status="warn",
                    message="Docker installed but daemon not running",
                    details={"remediation": "Start Docker Desktop or docker daemon"},
                )
            )
    except (subprocess.CalledProcessError, FileNotFoundError):
        results.append(
            CheckResult(
                status="warn",
                message="Docker not available",
                details={
                    "impact": "Devcontainer option unavailable",
                    "remediation": "Install Docker Desktop for consistent cross-platform development",
                },
            )
        )

    return results


def check_wheel_architecture() -> List[CheckResult]:
    """Deep wheel/arch validation beyond pydantic_core"""
    results: List[CheckResult] = []
    arch_sensitive_packages = ["uvloop", "orjson", "lxml"]

    for package in arch_sensitive_packages:
        try:
            module = __import__(package)
            module_path = getattr(module, "__file__", "")
            if module_path and module_path.endswith((".so", ".dylib", ".pyd")):
                results.append(
                    CheckResult(
                        status="ok",
                        message=f"{package} binary wheel loaded",
                        details={"path": module_path},
                    )
                )
            else:
                results.append(
                    CheckResult(
                        status="warn", message=f"{package} may be pure Python fallback", details={}
                    )
                )
        except ImportError:
            # Package not installed, which is fine for optional deps
            pass
        except Exception as e:
            results.append(
                CheckResult(
                    status="warn",
                    message=f"{package} import issue",
                    details={
                        "error": str(e),
                        "remediation": f"pip3 install --force-reinstall {package}",
                    },
                )
            )

    return results


def check_installation_path() -> List[CheckResult]:
    """Recommend installation method based on platform/arch"""
    results: List[CheckResult] = []
    machine = platform.machine()
    is_rosetta = detect_rosetta()

    if sys.platform == "darwin":
        if machine == "arm64" and not is_rosetta:
            results.append(
                CheckResult(
                    status="ok",
                    message="macOS Apple Silicon - optimal setup",
                    details={
                        "recommendation": "Native arm64 Python with binary wheels or devcontainer"
                    },
                )
            )
        elif machine == "x86_64" and is_rosetta:
            results.append(
                CheckResult(
                    status="warn",
                    message="macOS Apple Silicon with x86_64 Python (Rosetta)",
                    details={
                        "impact": "Higher risk of wheel/arch mismatches",
                        "recommended": "Use devcontainer or install native arm64 Python via pyenv",
                    },
                )
            )
        elif machine == "x86_64" and not is_rosetta:
            results.append(
                CheckResult(
                    status="ok",
                    message="macOS Intel - standard setup",
                    details={"recommendation": "System Python or devcontainer both work well"},
                )
            )
    elif sys.platform.startswith("linux"):
        results.append(
            CheckResult(
                status="ok",
                message=f"Linux {machine} - native setup recommended",
                details={"recommendation": "System Python preferred; devcontainer optional"},
            )
        )

    return results


def main() -> int:
    want_json = "--json" in sys.argv
    checks: List[CheckResult] = []

    # Core Python checks
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

    # Critical dependency checks
    checks.extend(check_pydantic_core())
    checks.extend(check_required_dependencies())

    # Environment and configuration checks
    checks.extend(check_environment_files())
    checks.extend(check_docker_availability())

    # Architecture-specific validation
    checks.extend(check_wheel_architecture())
    checks.extend(check_installation_path())

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
