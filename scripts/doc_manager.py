#!/usr/bin/env python3
"""
Documentation Manager CLI
Validates, updates, and manages documentation for AI swarm optimization
"""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

import yaml

from app.core.ai_logger import logger


class DocType(Enum):
    GUIDE = "guide"
    REFERENCE = "reference"
    DECISION = "decision"
    REPORT = "report"
    INDEX = "index"


class DocStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class DocMetadata:
    """Document metadata structure"""

    title: str
    type: DocType
    status: DocStatus
    version: str
    last_updated: str
    ai_context: str
    tags: list[str]
    dependencies: list[str] | None = None

    def to_yaml(self) -> str:
        """Convert to YAML front matter"""
        data = {
            "title": self.title,
            "type": self.type.value,
            "status": self.status.value,
            "version": self.version,
            "last_updated": self.last_updated,
            "ai_context": self.ai_context,
            "tags": self.tags,
        }
        if self.dependencies:
            data["dependencies"] = self.dependencies

        return "---\n" + yaml.dump(data, default_flow_style=False) + "---\n"


class DocumentManager:
    """Manages documentation for AI swarm optimization"""

    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir)
        self.docs_dir = self.root / "docs"
        self.errors = []
        self.warnings = []

    def validate_all(self) -> tuple[int, int]:
        """Validate all documentation files"""
        logger.info("🔍 Validating documentation...")

        valid = 0
        invalid = 0

        for md_file in self.root.glob("**/*.md"):
            # Skip node_modules and other generated content
            if any(
                skip in str(md_file) for skip in ["node_modules", ".git", "archive"]
            ):
                continue

            if self.validate_file(md_file):
                valid += 1
            else:
                invalid += 1

        return valid, invalid

    def validate_file(self, filepath: Path) -> bool:
        """Validate a single documentation file"""
        try:
            with open(filepath) as f:
                content = f.read()

            # Check for metadata
            if content.startswith("---"):
                metadata_end = content.find("---", 3)
                if metadata_end == -1:
                    self.warnings.append(f"{filepath}: Incomplete metadata block")
                    return False

                metadata_str = content[3:metadata_end]
                try:
                    metadata = yaml.safe_load(metadata_str)

                    # Validate required fields
                    required = [
                        "title",
                        "type",
                        "status",
                        "version",
                        "last_updated",
                        "ai_context",
                    ]
                    for field in required:
                        if field not in metadata:
                            self.errors.append(
                                f"{filepath}: Missing required field '{field}'"
                            )
                            return False

                    # Validate field values
                    if metadata["type"] not in [t.value for t in DocType]:
                        self.warnings.append(
                            f"{filepath}: Invalid type '{metadata['type']}'"
                        )

                    if metadata["status"] not in [s.value for s in DocStatus]:
                        self.warnings.append(
                            f"{filepath}: Invalid status '{metadata['status']}'"
                        )

                    if metadata["ai_context"] not in ["high", "medium", "low"]:
                        self.warnings.append(
                            f"{filepath}: Invalid ai_context '{metadata['ai_context']}'"
                        )

                    logger.info(f"✅ {filepath.relative_to(self.root)}")
                    return True

                except yaml.YAMLError as e:
                    self.errors.append(f"{filepath}: Invalid YAML metadata - {e}")
                    return False
            else:
                # No metadata found
                relative_path = filepath.relative_to(self.root)

                # Skip certain files that don't need metadata
                skip_files = [
                    "README.md",
                    "CONTRIBUTING.md",
                    "CHANGELOG.md",
                    "LICENSE.md",
                ]
                if filepath.name in skip_files:
                    return True

                self.warnings.append(f"{relative_path}: No metadata found")
                return False

        except Exception as e:
            self.errors.append(f"{filepath}: Error reading file - {e}")
            return False

    def add_metadata(self, filepath: Path, auto_detect: bool = True):
        """Add metadata to a documentation file"""
        logger.info(f"📝 Adding metadata to {filepath}...")

        with open(filepath) as f:
            content = f.read()

        # Check if metadata already exists
        if content.startswith("---"):
            logger.info("⚠️  File already has metadata")
            return

        # Auto-detect metadata if requested
        if auto_detect:
            metadata = self.detect_metadata(filepath, content)
        else:
            metadata = self.prompt_for_metadata(filepath)

        # Add metadata to file
        new_content = metadata.to_yaml() + "\n" + content

        with open(filepath, "w") as f:
            f.write(new_content)

        logger.info(f"✅ Metadata added to {filepath}")

    def detect_metadata(self, filepath: Path, content: str) -> DocMetadata:
        """Auto-detect metadata from file content and path"""
        # Detect title from first heading
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = (
            title_match.group(1)
            if title_match
            else filepath.stem.replace("_", " ").title()
        )

        # Detect type from path and content
        doc_type = DocType.REFERENCE  # default
        if "guide" in str(filepath).lower() or "how" in title.lower():
            doc_type = DocType.GUIDE
        elif "ADR" in filepath.name or "decision" in str(filepath).lower():
            doc_type = DocType.DECISION
        elif "report" in str(filepath).lower() or "summary" in str(filepath).lower():
            doc_type = DocType.REPORT

        # Detect status
        status = DocStatus.ACTIVE
        if "archive" in str(filepath).lower():
            status = DocStatus.ARCHIVED
        elif "deprecated" in content.lower()[:500]:
            status = DocStatus.DEPRECATED

        # Detect AI context importance
        ai_context = "medium"  # default
        if any(
            keyword in content.lower()
            for keyword in ["swarm", "orchestrat", "ai", "llm", "agent"]
        ):
            ai_context = "high"
        elif "archive" in str(filepath).lower():
            ai_context = "low"

        # Extract tags from content
        tags = []
        if "deployment" in content.lower():
            tags.append("deployment")
        if "api" in content.lower():
            tags.append("api")
        if "swarm" in content.lower():
            tags.append("swarm")
        if "monitor" in content.lower():
            tags.append("monitoring")

        return DocMetadata(
            title=title,
            type=doc_type,
            status=status,
            version="1.0.0",
            last_updated=datetime.now().strftime("%Y-%m-%d"),
            ai_context=ai_context,
            tags=tags or ["general"],
        )

    def update_index(self):
        """Update the documentation index"""
        logger.info("📚 Updating documentation index...")

        index_path = self.docs_dir / "INDEX.md"

        # Scan all documentation
        docs_by_category = {
            "guides": [],
            "architecture": [],
            "api": [],
            "swarms": [],
            "reference": [],
        }

        for md_file in self.docs_dir.glob("**/*.md"):
            if "archive" in str(md_file) or md_file.name == "INDEX.md":
                continue

            relative_path = md_file.relative_to(self.docs_dir)

            # Categorize
            if "guide" in str(md_file):
                docs_by_category["guides"].append(relative_path)
            elif "architecture" in str(md_file) or "ADR" in md_file.name:
                docs_by_category["architecture"].append(relative_path)
            elif "api" in str(md_file):
                docs_by_category["api"].append(relative_path)
            elif "swarm" in str(md_file):
                docs_by_category["swarms"].append(relative_path)
            else:
                docs_by_category["reference"].append(relative_path)

        # Generate index content
        content = """---
title: Documentation Index
type: index
status: active
version: 1.0.0
last_updated: {}
ai_context: high
---

# 📚 Documentation Index

_Auto-generated on {}_

## Quick Links
- [README](../README.md) - Project overview
- [QUICKSTART](../QUICKSTART.md) - 5-minute setup
- [CURRENT_STATE](CURRENT_STATE.md) - Live system state

""".format(
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        # Add categorized links
        for category, files in docs_by_category.items():
            if files:
                content += f"\n## {category.title()}\n"
                for file in sorted(files):
                    # Read title from file if possible
                    file_path = self.docs_dir / file
                    title = file.stem.replace("_", " ").replace("-", " ").title()

                    try:
                        with open(file_path) as f:
                            first_line = f.readline()
                            if first_line.startswith("#"):
                                title = first_line.strip("#").strip()
                    except:
                        pass

                    content += f"- [{title}]({file})\n"

        # Write index
        with open(index_path, "w") as f:
            f.write(content)

        logger.info(f"✅ Index updated at {index_path}")

    def check_health(self):
        """Check overall documentation health"""
        logger.info("\n📊 Documentation Health Check")
        logger.info("=" * 50)

        # Count files
        total_files = len(list(self.root.glob("**/*.md")))
        root_files = len(list(self.root.glob("*.md")))

        # Validate all
        valid, invalid = self.validate_all()

        # Calculate metrics
        metadata_coverage = (valid / total_files * 100) if total_files > 0 else 0

        # Report
        logger.info("\n📈 Metrics:")
        logger.info(f"  Total documentation files: {total_files}")
        logger.info(f"  Root-level files: {root_files} (target: < 10)")
        logger.info(f"  Files with valid metadata: {valid}")
        logger.info(f"  Files missing/invalid metadata: {invalid}")
        logger.info(f"  Metadata coverage: {metadata_coverage:.1f}%")

        if self.errors:
            logger.info(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors[:5]:
                logger.info(f"  - {error}")

        if self.warnings:
            logger.info(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:
                logger.info(f"  - {warning}")

        # Overall health score
        score = metadata_coverage * 0.5 + (10 - min(root_files, 10)) * 5
        logger.info(f"\n🏆 Overall Health Score: {score:.1f}/100")

        if score >= 90:
            logger.info("✅ Documentation is in excellent shape!")
        elif score >= 70:
            logger.info("👍 Documentation is good, minor improvements needed")
        elif score >= 50:
            logger.info("⚠️  Documentation needs attention")
        else:
            logger.info("🚨 Documentation needs significant work")


def main():
    parser = argparse.ArgumentParser(
        description="Documentation Manager for AI Swarm Optimization"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate documentation")
    validate_parser.add_argument("path", nargs="?", help="Specific file to validate")

    # Add metadata command
    metadata_parser = subparsers.add_parser(
        "add-metadata", help="Add metadata to files"
    )
    metadata_parser.add_argument("path", help="File to add metadata to")
    metadata_parser.add_argument(
        "--auto", action="store_true", help="Auto-detect metadata"
    )

    # Update index command
    subparsers.add_parser("update-index", help="Update documentation index")

    # Health check command
    subparsers.add_parser("health", help="Check documentation health")

    args = parser.parse_args()

    # Initialize manager
    manager = DocumentManager()

    # Execute command
    if args.command == "validate":
        if args.path:
            valid = manager.validate_file(Path(args.path))
            sys.exit(0 if valid else 1)
        else:
            valid, invalid = manager.validate_all()
            logger.info(f"\n✅ Valid: {valid}, ❌ Invalid: {invalid}")
            sys.exit(0 if invalid == 0 else 1)

    elif args.command == "add-metadata":
        manager.add_metadata(Path(args.path), auto_detect=args.auto)

    elif args.command == "update-index":
        manager.update_index()

    elif args.command == "health":
        manager.check_health()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
