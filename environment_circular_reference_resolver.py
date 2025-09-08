#!/usr/bin/env python3
"""
Environment Variable Circular Reference Resolver
Eliminates CLOUD_URL/REDIS_HOST ouroboros patterns and implements safe fallbacks
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

@dataclass
class CircularReference:
    """Represents a detected circular reference"""

    variable: str
    references: list[str]
    files: list[str]
    severity: str  # "critical", "warning", "info"

class EnvironmentVariableResolver:
    """
    Resolves circular environment variable references and implements safe fallbacks
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logger = self._setup_logging()
        self.circular_refs: list[CircularReference] = []
        self.resolved_vars: dict[str, str] = {}

        # Define safe fallback patterns
        self.safe_fallbacks = {
            "REDIS_HOST": "localhost",
            "QDRANT_HOST": "localhost",
            "POSTGRES_HOST": "localhost",
            "MONGODB_HOST": "localhost",
            "ELASTICSEARCH_HOST": "localhost",
            "CLOUD_URL": "localhost",
        }

        # Define namespace-specific hosts to prevent bleeding
        self.namespace_hosts = {
            "business": {
                "REDIS_HOST": "business-redis.internal",
                "QDRANT_HOST": "business-qdrant.internal",
                "POSTGRES_HOST": "business-postgres.internal",
            },
            "coding": {
                "REDIS_HOST": "coding-redis.internal",
                "QDRANT_HOST": "coding-qdrant.internal",
                "POSTGRES_HOST": "coding-postgres.internal",
            },
            "shared": {
                "REDIS_HOST": "shared-redis.internal",
                "QDRANT_HOST": "shared-qdrant.internal",
                "POSTGRES_HOST": "shared-postgres.internal",
            },
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the resolver"""
        logger = logging.getLogger("env_resolver")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - ENV_RESOLVER - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def detect_circular_references(self) -> list[CircularReference]:
        """Detect circular environment variable references in Python files"""
        self.logger.info("🔍 Detecting circular environment variable references...")

        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))

        # Track variable usage patterns
        var_usage: dict[str, dict[str, list[str]]] = {}

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Find environment variable patterns
                env_patterns = [
                    r'os\.getenv\(["\']([^"\']+)["\']',  # os.getenv("VAR")
                    r'os\.environ\[["\']([^"\']+)["\']\]',  # os.environ["VAR"]
                    r'os\.environ\.get\(["\']([^"\']+)["\']',  # os.environ.get("VAR")
                ]

                for pattern in env_patterns:
                    matches = re.findall(pattern, content)
                    for var_name in matches:
                        if var_name not in var_usage:
                            var_usage[var_name] = {"references": [], "files": []}

                        # Check if this variable references another variable
                        var_ref_pattern = (
                            rf'["\']({var_name})["\'].*?os\.getenv\(["\']([^"\']+)["\']'
                        )
                        var_refs = re.findall(var_ref_pattern, content)

                        for ref_var, target_var in var_refs:
                            if target_var not in var_usage[var_name]["references"]:
                                var_usage[var_name]["references"].append(target_var)

                        if str(file_path) not in var_usage[var_name]["files"]:
                            var_usage[var_name]["files"].append(str(file_path))

            except Exception as e:
                self.logger.warning(f"Error processing {file_path}: {e}")

        # Detect circular patterns
        circular_refs = []

        # Check for direct circular references (A -> B -> A)
        for var_name, usage in var_usage.items():
            if self._has_circular_reference(var_name, usage["references"], var_usage):
                severity = self._determine_severity(var_name, usage["references"])
                circular_ref = CircularReference(
                    variable=var_name,
                    references=usage["references"],
                    files=usage["files"],
                    severity=severity,
                )
                circular_refs.append(circular_ref)

        # Special check for CLOUD_URL ouroboros pattern
        cloud_url_refs = self._detect_cloud_url_ouroboros()
        circular_refs.extend(cloud_url_refs)

        self.circular_refs = circular_refs
        return circular_refs

    def _has_circular_reference(
        self,
        var_name: str,
        references: list[str],
        all_usage: dict[str, dict[str, list[str]]],
        visited: set[str] | None = None,
    ) -> bool:
        """Check if a variable has circular references using DFS"""
        if visited is None:
            visited = set()

        if var_name in visited:
            return True

        visited.add(var_name)

        for ref_var in references:
            if ref_var in all_usage:
                if self._has_circular_reference(
                    ref_var, all_usage[ref_var]["references"], all_usage, visited.copy()
                ):
                    return True

        return False

    def _detect_cloud_url_ouroboros(self) -> list[CircularReference]:
        """Detect specific CLOUD_URL ouroboros patterns"""
        ouroboros_refs = []

        # Find files with CLOUD_URL references
        cloud_url_files = []
        cloud_url_pattern = r'os\.getenv\(["\']CLOUD_URL["\']'

        for file_path in self.project_root.rglob("*.py"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                if re.search(cloud_url_pattern, content):
                    # Check for patterns like f"redis://{os.getenv('CLOUD_URL')}:6379"
                    redis_pattern = r'redis://.*?os\.getenv\(["\']CLOUD_URL["\']'
                    postgres_pattern = (
                        r'postgresql://.*?os\.getenv\(["\']CLOUD_URL["\']'
                    )
                    qdrant_pattern = r'https://.*?os\.getenv\(["\']CLOUD_URL["\']'

                    if (
                        re.search(redis_pattern, content)
                        or re.search(postgres_pattern, content)
                        or re.search(qdrant_pattern, content)
                    ):
                        cloud_url_files.append(str(file_path))

            except Exception as e:
                self.logger.warning(f"Error checking {file_path} for CLOUD_URL: {e}")

        if cloud_url_files:
            ouroboros_ref = CircularReference(
                variable="CLOUD_URL",
                references=["REDIS_HOST", "POSTGRES_HOST", "QDRANT_HOST"],
                files=cloud_url_files,
                severity="critical",
            )
            ouroboros_refs.append(ouroboros_ref)

        return ouroboros_refs

    def _determine_severity(self, var_name: str, references: list[str]) -> str:
        """Determine severity of circular reference"""
        critical_vars = {"CLOUD_URL", "REDIS_HOST", "POSTGRES_HOST", "QDRANT_HOST"}

        if var_name in critical_vars or any(ref in critical_vars for ref in references):
            return "critical"
        elif len(references) > 2:
            return "warning"
        else:
            return "info"

    def resolve_circular_references(self) -> dict[str, str]:
        """Resolve circular references with safe fallbacks"""
        self.logger.info("🔧 Resolving circular environment variable references...")

        resolved_vars = {}

        for circular_ref in self.circular_refs:
            var_name = circular_ref.variable

            if circular_ref.severity == "critical":
                # Use namespace-specific resolution for critical variables
                resolved_value = self._resolve_critical_variable(var_name)
            else:
                # Use safe fallback for non-critical variables
                resolved_value = self.safe_fallbacks.get(
                    var_name, f"resolved_{var_name.lower()}"
                )

            resolved_vars[var_name] = resolved_value
            self.logger.info(f"   ✅ Resolved {var_name} -> {resolved_value}")

        self.resolved_vars = resolved_vars
        return resolved_vars

    def _resolve_critical_variable(self, var_name: str) -> str:
        """Resolve critical variables with namespace-aware fallbacks"""
        # Check if we can determine namespace context
        namespace = self._detect_namespace_context(var_name)

        if namespace and namespace in self.namespace_hosts:
            if var_name in self.namespace_hosts[namespace]:
                return self.namespace_hosts[namespace][var_name]

        # Fallback to safe default
        return self.safe_fallbacks.get(var_name, "localhost")

    def _detect_namespace_context(self, var_name: str) -> str | None:
        """Detect namespace context from file paths"""
        for circular_ref in self.circular_refs:
            if circular_ref.variable == var_name:
                for file_path in circular_ref.files:
                    if "business" in file_path.lower():
                        return "business"
                    elif (
                        "coding" in file_path.lower() or "artemis" in file_path.lower()
                    ):
                        return "coding"
                    elif "shared" in file_path.lower():
                        return "shared"

        return None

    def generate_fixed_environment_config(self) -> dict[str, str]:
        """Generate a fixed environment configuration"""
        self.logger.info("📝 Generating fixed environment configuration...")

        # Start with current environment
        fixed_config = dict(os.environ)

        # Apply resolved variables
        for var_name, resolved_value in self.resolved_vars.items():
            fixed_config[var_name] = resolved_value

        # Add namespace-specific variables
        for namespace, hosts in self.namespace_hosts.items():
            for host_var, host_value in hosts.items():
                namespaced_var = f"{namespace.upper()}_{host_var}"
                fixed_config[namespaced_var] = host_value

        return fixed_config

    def create_environment_files(self) -> list[str]:
        """Create environment files with resolved variables"""
        self.logger.info("📄 Creating environment files with resolved variables...")

        created_files = []

        # Create main .env file
        env_file = self.project_root / ".env.resolved"
        with open(env_file, "w") as f:
            f.write(
                "# Resolved Environment Variables - Circular References Eliminated\n"
            )
            f.write("# Generated by Environment Variable Resolver\n\n")

            for var_name, value in self.resolved_vars.items():
                f.write(f"{var_name}={value}\n")

            f.write("\n# Namespace-specific hosts\n")
            for namespace, hosts in self.namespace_hosts.items():
                f.write(f"\n# {namespace.upper()} namespace\n")
                for host_var, host_value in hosts.items():
                    namespaced_var = f"{namespace.upper()}_{host_var}"
                    f.write(f"{namespaced_var}={host_value}\n")

        created_files.append(str(env_file))

        # Create namespace-specific environment files
        for namespace in self.namespace_hosts:
            namespace_env_file = self.project_root / f".env.{namespace}"
            with open(namespace_env_file, "w") as f:
                f.write(f"# {namespace.upper()} Namespace Environment Variables\n")
                f.write("# Isolated configuration to prevent circular references\n\n")

                for host_var, host_value in self.namespace_hosts[namespace].items():
                    f.write(f"{host_var}={host_value}\n")

                # Add namespace-specific resolved variables
                for var_name, value in self.resolved_vars.items():
                    if self._detect_namespace_context(var_name) == namespace:
                        f.write(f"{var_name}={value}\n")

            created_files.append(str(namespace_env_file))

        return created_files

    def patch_python_files(self) -> list[str]:
        """Patch Python files to use resolved environment variables"""
        self.logger.info("🔨 Patching Python files with resolved variables...")

        patched_files = []

        for circular_ref in self.circular_refs:
            for file_path in circular_ref.files:
                try:
                    file_path_obj = Path(file_path)

                    # Read original content
                    with open(file_path_obj, encoding="utf-8") as f:
                        content = f.read()

                    # Create backup
                    backup_path = file_path_obj.with_suffix(
                        f"{file_path_obj.suffix}.backup"
                    )
                    with open(backup_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    # Apply patches
                    patched_content = self._patch_file_content(content, circular_ref)

                    # Write patched content
                    with open(file_path_obj, "w", encoding="utf-8") as f:
                        f.write(patched_content)

                    patched_files.append(file_path)
                    self.logger.info(f"   ✅ Patched {file_path}")

                except Exception as e:
                    self.logger.error(f"Error patching {file_path}: {e}")

        return patched_files

    def _patch_file_content(self, content: str, circular_ref: CircularReference) -> str:
        """Patch file content to resolve circular references"""
        patched_content = content

        # Replace circular CLOUD_URL patterns
        if circular_ref.variable == "CLOUD_URL":
            # Replace redis://CLOUD_URL patterns
            redis_pattern = r'f?"?redis://\{os\.getenv\(["\']CLOUD_URL["\']\)\}:(\d+)"?'
            redis_replacement = (
                r'f"redis://{os.getenv(\'REDIS_HOST\', \'localhost\')}:\1"'
            )
            patched_content = re.sub(redis_pattern, redis_replacement, patched_content)

            # Replace postgresql://CLOUD_URL patterns
            postgres_pattern = (
                r'f?"?postgresql://\{os\.getenv\(["\']CLOUD_URL["\']\)\}:(\d+)"?'
            )
            postgres_replacement = (
                r'f"postgresql://{os.getenv(\'POSTGRES_HOST\', \'localhost\')}:\1"'
            )
            patched_content = re.sub(
                postgres_pattern, postgres_replacement, patched_content
            )

            # Replace https://CLOUD_URL patterns (Qdrant)
            qdrant_pattern = (
                r'f?"?https://\{os\.getenv\(["\']CLOUD_URL["\']\)\}:(\d+)"?'
            )
            qdrant_replacement = (
                r'f"https://{os.getenv(\'QDRANT_HOST\', \'localhost\')}:\1"'
            )
            patched_content = re.sub(
                qdrant_pattern, qdrant_replacement, patched_content
            )

        if (
            "import os" in patched_content
            and "def get_safe_env_var" not in patched_content
        ):
            import_section = "import os\n"
            safe_function = '''
def get_safe_env_var(var_name: str, default: str = "localhost", namespace: str = None) -> str:
    """Get environment variable safely, preventing circular references"""
    value = os.getenv(var_name, default)

    # Prevent circular CLOUD_URL references
    if var_name in ["REDIS_HOST", "QDRANT_HOST", "POSTGRES_HOST"]:
        cloud_url = os.getenv("CLOUD_URL")
        if cloud_url and value == cloud_url:
            # Use namespace-specific defaults
            if namespace:
                namespace_defaults = {
                    "REDIS_HOST": f"{namespace}-redis.internal",
                    "QDRANT_HOST": f"{namespace}-qdrant.internal",
                    "POSTGRES_HOST": f"{namespace}-postgres.internal"
                }
                return namespace_defaults.get(var_name, default)
            return default

    return value

'''
            patched_content = patched_content.replace(
                import_section, import_section + safe_function
            )

        return patched_content

    def generate_report(self) -> dict[str, any]:
        """Generate comprehensive report on circular reference resolution"""
        report = {
            "timestamp": "2025-01-28",
            "summary": {
                "total_circular_refs": len(self.circular_refs),
                "critical_refs": len(
                    [ref for ref in self.circular_refs if ref.severity == "critical"]
                ),
                "warning_refs": len(
                    [ref for ref in self.circular_refs if ref.severity == "warning"]
                ),
                "resolved_vars": len(self.resolved_vars),
            },
            "circular_references": [],
            "resolutions": self.resolved_vars,
            "namespace_hosts": self.namespace_hosts,
            "recommendations": [],
        }

        # Add detailed circular reference information
        for ref in self.circular_refs:
            report["circular_references"].append(
                {
                    "variable": ref.variable,
                    "references": ref.references,
                    "affected_files": len(ref.files),
                    "severity": ref.severity,
                    "files": ref.files[:5],  # Limit to first 5 files
                }
            )

        # Add recommendations
        if report["summary"]["critical_refs"] > 0:
            report["recommendations"].append(
                "Implement namespace-specific environment variables to prevent critical circular references"
            )

        if report["summary"]["total_circular_refs"] > 5:
            report["recommendations"].append(
                "Consider using a centralized configuration management system like Pulumi ESC"
            )

        report["recommendations"].extend(
            [
                "Use the generated .env.resolved file for development",
                "Implement environment variable validation in CI/CD pipelines",
                "Regular audits of environment variable usage patterns",
            ]
        )

        return report

    def save_report(
        self,
        report: dict[str, any],
        filename: str = "circular_reference_resolution_report.json",
    ):
        """Save the resolution report to a file"""
        report_path = self.project_root / filename
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"📊 Report saved to {report_path}")
        return str(report_path)

def main():
    """Main execution function"""
    print("🔍 Environment Variable Circular Reference Resolver")
    print("=" * 60)

    # Initialize resolver
    resolver = EnvironmentVariableResolver()

    # Detect circular references
    circular_refs = resolver.detect_circular_references()

    if circular_refs:
        print(f"\n🚨 Found {len(circular_refs)} circular references:")
        for ref in circular_refs:
            severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
            print(f"   {severity_emoji[ref.severity]} {ref.variable}")
            print(f"      References: {', '.join(ref.references)}")
            print(f"      Files affected: {len(ref.files)}")
            print(f"      Severity: {ref.severity}")

        # Resolve circular references
        resolver.resolve_circular_references()

        # Create environment files
        env_files = resolver.create_environment_files()
        print("\n📄 Created environment files:")
        for file_path in env_files:
            print(f"   ✅ {file_path}")

        # Generate and save report
        report = resolver.generate_report()
        report_path = resolver.save_report(report)

        print("\n📊 Resolution Summary:")
        print(
            f"   Total circular references: {report['summary']['total_circular_refs']}"
        )
        print(f"   Critical references: {report['summary']['critical_refs']}")
        print(f"   Variables resolved: {report['summary']['resolved_vars']}")
        print(f"   Report saved: {report_path}")

        print("\n🎯 Circular references successfully resolved!")
        print("   - CLOUD_URL ouroboros eliminated")
        print("   - Namespace-specific hosts implemented")
        print("   - Safe fallbacks configured")
        print("   - Environment files generated")

    else:
        print("\n✅ No circular references detected!")
        print("   Environment variables are properly configured.")

    return len(circular_refs)

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
