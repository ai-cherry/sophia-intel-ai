#!/usr/bin/env python3
"""
Meta-Tagging System Initialization Script

This script initializes the meta-tagging system by scanning the entire codebase,
generating initial tags, storing them in the registry, and producing a comprehensive report.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from app.scaffolding.ai_hints import AIHintsPipeline, generate_ai_hints
    from app.scaffolding.meta_tagging import (
        AutoTagger,
        Complexity,
        MetaTagRegistry,
        ModificationRisk,
        SemanticRole,
        auto_tag_directory,
        get_global_registry,
    )
    from app.scaffolding.semantic_classifier import SemanticClassifier
except ImportError as e:
    print(f"Error importing meta-tagging modules: {e}")
    print("Please ensure you're running this script from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("meta_tagging_init.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class MetaTaggingInitializer:
    """Handles the initialization of the meta-tagging system."""

    def __init__(
        self,
        root_directory: str = ".",
        output_path: str = "meta_tags_registry.json",
        report_path: str = "meta_tagging_report.json",
    ):
        """Initialize with configuration parameters."""
        self.root_directory = Path(root_directory).resolve()
        self.output_path = output_path
        self.report_path = report_path

        # File patterns to include
        self.include_patterns = [
            "*.py",
            "*.js",
            "*.ts",
            "*.jsx",
            "*.tsx",
            "*.json",
            "*.yaml",
            "*.yml",
            "*.toml",
            "*.md",
            "*.rst",
            "*.txt",
        ]

        # Directories to exclude
        self.exclude_dirs = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            "dist",
            "build",
            ".tox",
            "htmlcov",
            ".coverage",
            ".env",
        }

        # File patterns to exclude
        self.exclude_files = {
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "*.so",
            "*.egg",
            "*.log",
            "*.tmp",
            "*.swp",
            "*.bak",
        }

        # Initialize components
        self.registry = MetaTagRegistry(self.output_path)
        self.tagger = AutoTagger(self.registry)
        self.classifier = SemanticClassifier()
        self.hints_pipeline = AIHintsPipeline()

        # Statistics tracking
        self.stats = {
            "total_files_scanned": 0,
            "files_successfully_tagged": 0,
            "files_with_errors": 0,
            "total_tags_created": 0,
            "total_hints_generated": 0,
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "errors": [],
        }

    def discover_files(self) -> List[Path]:
        """Discover all files to be processed."""
        logger.info(f"Discovering files in {self.root_directory}")

        discovered_files = []

        for pattern in self.include_patterns:
            for file_path in self.root_directory.rglob(pattern):
                if self._should_include_file(file_path):
                    discovered_files.append(file_path)

        # Remove duplicates and sort
        discovered_files = list(set(discovered_files))
        discovered_files.sort()

        logger.info(f"Discovered {len(discovered_files)} files to process")
        return discovered_files

    def _should_include_file(self, file_path: Path) -> bool:
        """Determine if a file should be included in processing."""

        # Check if file is in excluded directory
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return False

        # Check if file matches excluded patterns
        for pattern in self.exclude_files:
            if file_path.match(pattern):
                return False

        # Must be a regular file
        if not file_path.is_file():
            return False

        # Must be readable
        try:
            file_path.read_text(encoding="utf-8", errors="ignore")
            return True
        except Exception:
            return False

    async def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single file and return results."""
        result = {
            "file_path": str(file_path),
            "tags_created": 0,
            "hints_generated": 0,
            "processing_time": 0,
            "error": None,
            "tags": [],
            "hints": [],
        }

        start_time = time.time()

        try:
            logger.debug(f"Processing file: {file_path}")

            # Read file content
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content.strip():
                logger.debug(f"Skipping empty file: {file_path}")
                return result

            # Generate tags using the auto-tagger
            tags = await self.tagger.tag_file(str(file_path))
            result["tags_created"] = len(tags)
            result["tags"] = [tag.to_dict() for tag in tags]

            # Generate AI hints for each tag
            all_hints = []
            for tag in tags:
                try:
                    hints = await generate_ai_hints(content, tag)
                    all_hints.extend(hints)

                    # Update tag with hints
                    tag.optimization_opportunities = [
                        h.title for h in hints if h.hint_type.value == "optimization"
                    ]
                    tag.refactoring_suggestions = [
                        h.title for h in hints if h.hint_type.value == "refactoring"
                    ]
                    tag.test_requirements = [
                        h.title for h in hints if h.hint_type.value == "testing"
                    ]
                    tag.security_considerations = [
                        h.title for h in hints if h.hint_type.value == "security"
                    ]

                except Exception as e:
                    logger.warning(
                        f"Failed to generate hints for {tag.component_name}: {e}"
                    )

            result["hints_generated"] = len(all_hints)
            result["hints"] = [hint.to_dict() for hint in all_hints]

            self.stats["total_tags_created"] += len(tags)
            self.stats["total_hints_generated"] += len(all_hints)
            self.stats["files_successfully_tagged"] += 1

            logger.debug(
                f"Created {len(tags)} tags and {len(all_hints)} hints for {file_path}"
            )

        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            self.stats["errors"].append(error_msg)
            self.stats["files_with_errors"] += 1

        finally:
            result["processing_time"] = time.time() - start_time
            self.stats["total_files_scanned"] += 1

        return result

    async def process_all_files(
        self,
        files: List[Path],
        max_concurrent: int = 10,
        progress_callback: Optional[callable] = None,
    ) -> List[Dict[str, Any]]:
        """Process all files with controlled concurrency."""
        logger.info(
            f"Processing {len(files)} files with max concurrency {max_concurrent}"
        )

        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        completed = 0

        async def process_with_semaphore(file_path: Path) -> Dict[str, Any]:
            async with semaphore:
                return await self.process_file(file_path)

        # Create tasks for all files
        tasks = [process_with_semaphore(file_path) for file_path in files]

        # Process with progress tracking
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            results.append(result)
            completed += 1

            if progress_callback:
                progress_callback(completed, len(files), result)

            if completed % 10 == 0 or completed == len(files):
                logger.info(f"Progress: {completed}/{len(files)} files processed")

        return results

    def generate_comprehensive_report(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a comprehensive analysis report."""

        # Basic statistics
        successful_files = [r for r in results if not r["error"]]
        failed_files = [r for r in results if r["error"]]

        # Tag statistics by role
        role_stats = {}
        for role in SemanticRole:
            role_stats[role.value] = 0

        # Complexity statistics
        complexity_stats = {}
        for complexity in Complexity:
            complexity_stats[complexity.value] = 0

        # Risk statistics
        risk_stats = {}
        for risk in ModificationRisk:
            risk_stats[risk.value] = 0

        # Hint statistics
        hint_type_stats = {}
        severity_stats = {}

        # Process all tags and hints
        all_tags = []
        all_hints = []

        for result in successful_files:
            for tag_data in result["tags"]:
                all_tags.append(tag_data)

                # Count by role
                role = tag_data.get("semantic_role", "unknown")
                role_stats[role] = role_stats.get(role, 0) + 1

                # Count by complexity
                complexity = tag_data.get("complexity", 3)
                complexity_name = {
                    1: "TRIVIAL",
                    2: "LOW",
                    3: "MODERATE",
                    4: "HIGH",
                    5: "CRITICAL",
                }.get(complexity, "MODERATE")
                complexity_stats[complexity_name] += 1

                # Count by risk
                risk = tag_data.get("modification_risk", 2)
                risk_name = {1: "SAFE", 2: "MODERATE", 3: "HIGH", 4: "CRITICAL"}.get(
                    risk, "MODERATE"
                )
                risk_stats[risk_name] += 1

            for hint_data in result["hints"]:
                all_hints.append(hint_data)

                # Count by hint type
                hint_type = hint_data.get("hint_type", "unknown")
                hint_type_stats[hint_type] = hint_type_stats.get(hint_type, 0) + 1

                # Count by severity
                severity = hint_data.get("severity", 2)
                severity_name = {
                    1: "INFO",
                    2: "LOW",
                    3: "MEDIUM",
                    4: "HIGH",
                    5: "CRITICAL",
                }.get(severity, "MEDIUM")
                severity_stats[severity_name] = severity_stats.get(severity_name, 0) + 1

        # File type analysis
        file_extensions = {}
        for result in results:
            ext = Path(result["file_path"]).suffix
            file_extensions[ext] = file_extensions.get(ext, 0) + 1

        # Top issues by severity
        critical_hints = [h for h in all_hints if h.get("severity") == 5]
        high_hints = [h for h in all_hints if h.get("severity") == 4]

        # Component analysis
        components_by_role = {}
        for role in SemanticRole:
            components_by_role[role.value] = [
                tag for tag in all_tags if tag.get("semantic_role") == role.value
            ]

        # Optimization opportunities
        optimization_hints = [
            h for h in all_hints if h.get("hint_type") == "optimization"
        ]
        security_hints = [h for h in all_hints if h.get("hint_type") == "security"]

        # Generate recommendations
        recommendations = self._generate_recommendations(all_tags, all_hints)

        report = {
            "summary": {
                "total_files": len(results),
                "successful_files": len(successful_files),
                "failed_files": len(failed_files),
                "total_tags": len(all_tags),
                "total_hints": len(all_hints),
                "processing_duration": self.stats["duration_seconds"],
                "average_tags_per_file": len(all_tags) / max(len(successful_files), 1),
                "average_hints_per_file": len(all_hints)
                / max(len(successful_files), 1),
            },
            "file_analysis": {
                "by_extension": file_extensions,
                "successful_files": [r["file_path"] for r in successful_files],
                "failed_files": [
                    {"file": r["file_path"], "error": r["error"]} for r in failed_files
                ],
            },
            "tag_analysis": {
                "by_semantic_role": role_stats,
                "by_complexity": complexity_stats,
                "by_modification_risk": risk_stats,
                "total_components": len(all_tags),
            },
            "hint_analysis": {
                "by_type": hint_type_stats,
                "by_severity": severity_stats,
                "critical_issues": len(critical_hints),
                "high_priority_issues": len(high_hints),
                "optimization_opportunities": len(optimization_hints),
                "security_concerns": len(security_hints),
            },
            "component_insights": {
                "orchestrators": len(components_by_role.get("orchestrator", [])),
                "processors": len(components_by_role.get("processor", [])),
                "gateways": len(components_by_role.get("gateway", [])),
                "agents": len(components_by_role.get("agent", [])),
                "repositories": len(components_by_role.get("repository", [])),
                "services": len(components_by_role.get("service", [])),
                "utilities": len(components_by_role.get("utility", [])),
            },
            "top_issues": {
                "critical_hints": critical_hints[:10],
                "high_priority_hints": high_hints[:10],
                "most_complex_components": sorted(
                    all_tags, key=lambda x: x.get("complexity", 0), reverse=True
                )[:10],
                "highest_risk_components": sorted(
                    all_tags, key=lambda x: x.get("modification_risk", 0), reverse=True
                )[:10],
            },
            "recommendations": recommendations,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "root_directory": str(self.root_directory),
                "registry_file": self.output_path,
                "version": "1.0.0",
                "statistics": self.stats,
            },
        }

        return report

    def _generate_recommendations(
        self, tags: List[Dict], hints: List[Dict]
    ) -> Dict[str, List[str]]:
        """Generate actionable recommendations based on analysis."""
        recommendations = {
            "immediate_actions": [],
            "architectural_improvements": [],
            "security_enhancements": [],
            "testing_priorities": [],
            "optimization_opportunities": [],
            "maintenance_tasks": [],
        }

        # Critical security issues
        critical_security = [
            h
            for h in hints
            if h.get("hint_type") == "security" and h.get("severity") >= 4
        ]
        if critical_security:
            recommendations["immediate_actions"].append(
                f"Address {len(critical_security)} critical security vulnerabilities immediately"
            )

        # High-risk components
        high_risk_components = [t for t in tags if t.get("modification_risk") >= 3]
        if len(high_risk_components) > len(tags) * 0.2:  # More than 20% are high risk
            recommendations["architectural_improvements"].append(
                f"Review and refactor {len(high_risk_components)} high-risk components"
            )

        # Complex orchestrators
        complex_orchestrators = [
            t
            for t in tags
            if t.get("semantic_role") == "orchestrator" and t.get("complexity") >= 4
        ]
        if complex_orchestrators:
            recommendations["architectural_improvements"].append(
                f"Simplify {len(complex_orchestrators)} complex orchestrator(s)"
            )

        # Testing gaps
        test_hints = [h for h in hints if h.get("hint_type") == "testing"]
        if test_hints:
            recommendations["testing_priorities"].append(
                f"Address {len(test_hints)} testing requirements across the codebase"
            )

        # Optimization opportunities
        optimization_hints = [h for h in hints if h.get("hint_type") == "optimization"]
        if optimization_hints:
            recommendations["optimization_opportunities"].append(
                f"Implement {len(optimization_hints)} optimization opportunities for better performance"
            )

        # Documentation needs
        undocumented = [t for t in tags if t.get("documentation_score", 0) < 0.5]
        if undocumented:
            recommendations["maintenance_tasks"].append(
                f"Improve documentation for {len(undocumented)} components"
            )

        return recommendations

    async def run_initialization(
        self,
        max_concurrent: int = 10,
        generate_report: bool = True,
        save_registry: bool = True,
    ) -> Dict[str, Any]:
        """Run the complete initialization process."""

        logger.info("Starting meta-tagging system initialization")
        self.stats["start_time"] = datetime.now()

        try:
            # Discover files
            files = self.discover_files()
            if not files:
                logger.warning("No files found to process")
                return {"error": "No files found to process"}

            # Progress callback
            def progress_callback(completed: int, total: int, result: Dict):
                if completed % 25 == 0 or completed == total:
                    logger.info(
                        f"Processed {completed}/{total} files - "
                        f"Tags: {result['tags_created']}, "
                        f"Hints: {result['hints_generated']}"
                    )

            # Process all files
            logger.info("Processing files...")
            results = await self.process_all_files(
                files,
                max_concurrent=max_concurrent,
                progress_callback=progress_callback,
            )

            # Save registry
            if save_registry:
                logger.info(f"Saving registry to {self.output_path}")
                self.registry.save()

            # Generate and save report
            report = None
            if generate_report:
                logger.info("Generating comprehensive report...")
                report = self.generate_comprehensive_report(results)

                with open(self.report_path, "w") as f:
                    json.dump(report, f, indent=2, default=str)

                logger.info(f"Report saved to {self.report_path}")

            # Final statistics
            self.stats["end_time"] = datetime.now()
            self.stats["duration_seconds"] = (
                self.stats["end_time"] - self.stats["start_time"]
            ).total_seconds()

            logger.info("Initialization completed successfully!")
            logger.info(
                f"Summary: {self.stats['files_successfully_tagged']} files tagged, "
                f"{self.stats['total_tags_created']} tags created, "
                f"{self.stats['total_hints_generated']} hints generated"
            )

            return {
                "success": True,
                "stats": self.stats,
                "registry_path": self.output_path,
                "report_path": self.report_path if generate_report else None,
                "report": report,
            }

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return {"error": str(e), "stats": self.stats}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize the meta-tagging system for the Sophia AI codebase"
    )

    parser.add_argument(
        "--root-dir",
        "-r",
        default=".",
        help="Root directory to scan (default: current directory)",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="meta_tags_registry.json",
        help="Output path for the registry file (default: meta_tags_registry.json)",
    )

    parser.add_argument(
        "--report",
        "-R",
        default="meta_tagging_report.json",
        help="Output path for the analysis report (default: meta_tagging_report.json)",
    )

    parser.add_argument(
        "--max-concurrent",
        "-c",
        type=int,
        default=10,
        help="Maximum concurrent file processing (default: 10)",
    )

    parser.add_argument(
        "--no-report", action="store_true", help="Skip generating the analysis report"
    )

    parser.add_argument(
        "--no-registry", action="store_true", help="Skip saving the registry file"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress output"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    # Initialize and run
    async def run_async():
        initializer = MetaTaggingInitializer(
            root_directory=args.root_dir,
            output_path=args.output,
            report_path=args.report,
        )

        result = await initializer.run_initialization(
            max_concurrent=args.max_concurrent,
            generate_report=not args.no_report,
            save_registry=not args.no_registry,
        )

        if result.get("error"):
            logger.error(f"Initialization failed: {result['error']}")
            return 1

        # Print summary
        stats = result["stats"]
        print("\n" + "=" * 60)
        print("META-TAGGING INITIALIZATION COMPLETE")
        print("=" * 60)
        print(f"Files processed: {stats['files_successfully_tagged']}")
        print(f"Tags created: {stats['total_tags_created']}")
        print(f"Hints generated: {stats['total_hints_generated']}")
        print(f"Processing time: {stats['duration_seconds']:.2f} seconds")

        if result.get("registry_path"):
            print(f"Registry saved to: {result['registry_path']}")

        if result.get("report_path"):
            print(f"Report saved to: {result['report_path']}")

            # Print key insights
            report = result.get("report", {})
            summary = report.get("summary", {})
            hint_analysis = report.get("hint_analysis", {})

            print("\nKey Insights:")
            print(
                f"- Average tags per file: {summary.get('average_tags_per_file', 0):.1f}"
            )
            print(f"- Critical issues found: {hint_analysis.get('critical_issues', 0)}")
            print(f"- Security concerns: {hint_analysis.get('security_concerns', 0)}")
            print(
                f"- Optimization opportunities: {hint_analysis.get('optimization_opportunities', 0)}"
            )

        print("=" * 60)
        return 0

    # Run the async function
    exit_code = asyncio.run(run_async())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
