#!/usr/bin/env python3
"""
Brand Consistency Audit Script for Sophia Intel AI

This script scans the codebase for incorrect brand usage patterns, validates
business name consistency, and generates a comprehensive report with suggestions.

Author: Sophia Intel AI
Version: 1.0.0
"""

import argparse
import json
import logging
import mimetypes
import os
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class BrandIssue:
    """Represents a brand consistency issue"""

    file_path: str
    line_number: int
    line_content: str
    issue_type: str
    incorrect_usage: str
    suggested_fix: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    confidence: float  # 0.0 to 1.0


@dataclass
class AuditReport:
    """Comprehensive audit report"""

    timestamp: str
    total_files_scanned: int
    issues_found: int
    issues_by_type: Dict[str, int]
    issues_by_severity: Dict[str, int]
    files_with_issues: int
    clean_files: int
    execution_time: float
    issues: List[Dict]


class BrandAuditConfig:
    """Configuration for brand audit patterns and rules"""

    def __init__(self):
        # Correct brand names and variations
        self.correct_brands = {
            "sophia_intel_ai": "Sophia Intel AI",
            "sophia": "Sophia",
            "artemis": "Artemis",
            "agno": "AGNO",
        }

        # Common incorrect patterns to look for
        self.incorrect_patterns = [
            # Pay Ready variations (incorrect for this project)
            (
                r"Pay[\s\-_]*Ready",
                "pay_ready_variation",
                "critical",
                "Should be project-specific branding",
            ),
            (
                r"payready",
                "payready_lowercase",
                "critical",
                "Should be project-specific branding",
            ),
            (
                r"PayReady",
                "payready_camelcase",
                "critical",
                "Should be project-specific branding",
            ),
            (
                r"pay[\s\-_]*com",
                "pay_com_variation",
                "critical",
                "Should be project-specific branding",
            ),
            (
                r"Pay\.com",
                "pay_dot_com",
                "critical",
                "Should be project-specific branding",
            ),
            # Generic business name inconsistencies
            (
                r"sophia[\s\-_]+intel[\s\-_]+ai",
                "sophia_spacing_issues",
                "medium",
                'Use consistent "Sophia Intel AI" format',
            ),
            (
                r"SophiaIntelAI",
                "sophia_no_spaces",
                "medium",
                'Use "Sophia Intel AI" with proper spacing',
            ),
            (
                r"sophia-intel-ai",
                "sophia_hyphens",
                "low",
                'Consider "Sophia Intel AI" for display text',
            ),
            (
                r"sophia_intel_ai",
                "sophia_underscores",
                "low",
                'Consider "Sophia Intel AI" for display text',
            ),
            # Case sensitivity issues
            (
                r"SOPHIA(?!\s+INTEL\s+AI)",
                "sophia_all_caps",
                "medium",
                'Use proper case: "Sophia"',
            ),
            (
                r"artemis(?![\s\-_])",
                "artemis_lowercase",
                "medium",
                'Use proper case: "Artemis"',
            ),
            (r"ARTEMIS", "artemis_all_caps", "medium", 'Use proper case: "Artemis"'),
            # Legacy or placeholder names
            (
                r"YourCompany",
                "generic_company",
                "high",
                'Replace with "Sophia Intel AI"',
            ),
            (
                r"CompanyName",
                "generic_company_name",
                "high",
                'Replace with "Sophia Intel AI"',
            ),
            (
                r"Your Business",
                "generic_business",
                "high",
                'Replace with "Sophia Intel AI"',
            ),
            (r"Example Corp", "example_corp", "high", 'Replace with "Sophia Intel AI"'),
            (r"Acme Corp", "acme_corp", "high", 'Replace with "Sophia Intel AI"'),
            # Common typos
            (r"Sofhia", "sophia_typo", "high", 'Correct spelling: "Sophia"'),
            (
                r"Sophia\s+AI\s+Intel",
                "sophia_order_wrong",
                "medium",
                'Correct order: "Sophia Intel AI"',
            ),
        ]

        # File patterns to exclude from scanning
        self.excluded_patterns = [
            r"\.git/",
            r"node_modules/",
            r"\.venv/",
            r"__pycache__/",
            r"\.pyc$",
            r"\.egg-info/",
            r"dist/",
            r"build/",
            r"\.DS_Store",
            r"\.pytest_cache/",
            r"\.mypy_cache/",
            r"\.ruff_cache/",
            r"backup_",
            r"\.backup/",
            r"\.log$",
            r"\.db$",
            r"\.sqlite",
            r"\.lock$",
            r"\.pid$",
        ]

        # File extensions to include (text files only)
        self.included_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".css",
            ".scss",
            ".less",
            ".md",
            ".txt",
            ".yaml",
            ".yml",
            ".json",
            ".toml",
            ".ini",
            ".cfg",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".cmd",
            ".sql",
            ".graphql",
            ".gql",
            ".vue",
            ".svelte",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".java",
            ".kt",
            ".swift",
            ".cs",
            ".cpp",
            ".c",
            ".h",
            ".dockerfile",
            ".dockerignore",
            ".gitignore",
            ".env",
        }

        # Context-sensitive patterns (patterns that might be OK in certain contexts)
        self.context_exceptions = [
            # URLs and domain names might be exceptions
            (r"https?://", "url_context"),
            (r"@[\w\-\.]+\.(com|org|net)", "email_context"),
            (r"\.com/", "domain_path_context"),
        ]


class BrandConsistencyAuditor:
    """Main auditor class for brand consistency checking"""

    def __init__(self, config: BrandAuditConfig, root_path: str):
        self.config = config
        self.root_path = Path(root_path).resolve()
        self.issues: List[BrandIssue] = []
        self.stats = {
            "files_scanned": 0,
            "files_with_issues": 0,
            "total_issues": 0,
        }

    def is_excluded_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning"""
        relative_path = str(file_path.relative_to(self.root_path))

        # Check excluded patterns
        for pattern in self.config.excluded_patterns:
            if re.search(pattern, relative_path, re.IGNORECASE):
                return True

        # Check if file extension is included
        if file_path.suffix.lower() not in self.config.included_extensions:
            # Also check if it's a text file by mime type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not (mime_type and mime_type.startswith("text/")):
                return True

        return False

    def is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary"""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                # If we find null bytes, it's likely binary
                return b"\0" in chunk
        except OSError:
            return True

    def has_context_exception(self, line: str, match_start: int) -> bool:
        """Check if the match is in a context where it might be acceptable"""
        # Get surrounding context
        context_start = max(0, match_start - 50)
        context_end = min(len(line), match_start + 100)
        context = line[context_start:context_end]

        for pattern, _ in self.config.context_exceptions:
            if re.search(pattern, context, re.IGNORECASE):
                return True

        return False

    def scan_file(self, file_path: Path) -> List[BrandIssue]:
        """Scan a single file for brand consistency issues"""
        issues = []

        if self.is_excluded_file(file_path) or self.is_binary_file(file_path):
            return issues

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line_issues = self.scan_line(file_path, line_num, line)
                issues.extend(line_issues)

        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read file {file_path}: {e}")

        return issues

    def scan_line(self, file_path: Path, line_num: int, line: str) -> List[BrandIssue]:
        """Scan a single line for brand consistency issues"""
        issues = []

        for (
            pattern,
            issue_type,
            severity,
            description,
        ) in self.config.incorrect_patterns:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                # Skip if in context exception
                if self.has_context_exception(line, match.start()):
                    continue

                # Calculate confidence based on context
                confidence = self.calculate_confidence(line, match, issue_type)

                if confidence < 0.3:  # Skip low-confidence matches
                    continue

                issue = BrandIssue(
                    file_path=str(file_path.relative_to(self.root_path)),
                    line_number=line_num,
                    line_content=line.strip(),
                    issue_type=issue_type,
                    incorrect_usage=match.group(),
                    suggested_fix=self.get_suggested_fix(match.group(), issue_type),
                    severity=severity,
                    confidence=confidence,
                )
                issues.append(issue)

        return issues

    def calculate_confidence(
        self, line: str, match: re.Match, issue_type: str
    ) -> float:
        """Calculate confidence score for a potential issue"""
        confidence = 1.0

        # Lower confidence for comments
        if re.search(r"^\s*(#|//|\*|<!--)", line.strip()):
            confidence *= 0.7

        # Lower confidence for URLs
        if "http" in line.lower():
            confidence *= 0.5

        # Higher confidence for critical issues
        if issue_type.startswith("pay_"):
            confidence = 1.0  # Max confidence for Pay Ready variations

        # Lower confidence for code identifiers vs display text
        if re.search(r"[_\-]", match.group()):
            confidence *= 0.8

        return confidence

    def get_suggested_fix(self, incorrect_usage: str, issue_type: str) -> str:
        """Get suggested fix for the incorrect usage"""
        fixes = {
            "pay_ready_variation": "Sophia Intel AI",
            "payready_lowercase": "Sophia Intel AI",
            "payready_camelcase": "Sophia Intel AI",
            "pay_com_variation": "Sophia Intel AI",
            "pay_dot_com": "Sophia Intel AI",
            "sophia_spacing_issues": "Sophia Intel AI",
            "sophia_no_spaces": "Sophia Intel AI",
            "sophia_hyphens": "Sophia Intel AI (for display) or sophia-intel-ai (for technical)",
            "sophia_underscores": "Sophia Intel AI (for display) or sophia_intel_ai (for technical)",
            "sophia_all_caps": "Sophia",
            "artemis_lowercase": "Artemis",
            "artemis_all_caps": "Artemis",
            "generic_company": "Sophia Intel AI",
            "generic_company_name": "Sophia Intel AI",
            "generic_business": "Sophia Intel AI",
            "example_corp": "Sophia Intel AI",
            "acme_corp": "Sophia Intel AI",
            "sophia_typo": "Sophia",
            "sophia_order_wrong": "Sophia Intel AI",
        }

        return fixes.get(issue_type, "Review and correct brand usage")

    def scan_directory(self) -> List[BrandIssue]:
        """Scan entire directory tree for brand consistency issues"""
        all_issues = []

        logger.info(f"Starting brand consistency audit of {self.root_path}")

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                self.stats["files_scanned"] += 1

                if self.stats["files_scanned"] % 100 == 0:
                    logger.info(f"Scanned {self.stats['files_scanned']} files...")

                file_issues = self.scan_file(file_path)
                if file_issues:
                    self.stats["files_with_issues"] += 1
                    all_issues.extend(file_issues)

        self.issues = all_issues
        self.stats["total_issues"] = len(all_issues)

        logger.info(
            f"Scan complete. Found {len(all_issues)} issues in {self.stats['files_with_issues']} files"
        )
        return all_issues

    def generate_report(self, output_format: str = "json") -> AuditReport:
        """Generate comprehensive audit report"""
        issues_by_type = defaultdict(int)
        issues_by_severity = defaultdict(int)

        for issue in self.issues:
            issues_by_type[issue.issue_type] += 1
            issues_by_severity[issue.severity] += 1

        report = AuditReport(
            timestamp=datetime.now().isoformat(),
            total_files_scanned=self.stats["files_scanned"],
            issues_found=len(self.issues),
            issues_by_type=dict(issues_by_type),
            issues_by_severity=dict(issues_by_severity),
            files_with_issues=self.stats["files_with_issues"],
            clean_files=self.stats["files_scanned"] - self.stats["files_with_issues"],
            execution_time=0.0,  # Will be set by caller
            issues=[asdict(issue) for issue in self.issues],
        )

        return report

    def print_summary(self) -> None:
        """Print audit summary to console"""
        print("\n" + "=" * 80)
        print("BRAND CONSISTENCY AUDIT SUMMARY")
        print("=" * 80)
        print(f"📁 Files Scanned: {self.stats['files_scanned']}")
        print(f"⚠️  Issues Found: {self.stats['total_issues']}")
        print(f"🔴 Files with Issues: {self.stats['files_with_issues']}")
        print(
            f"✅ Clean Files: {self.stats['files_scanned'] - self.stats['files_with_issues']}"
        )

        if self.issues:
            print("\n📊 ISSUES BY SEVERITY:")
            severity_counts = defaultdict(int)
            for issue in self.issues:
                severity_counts[issue.severity] += 1

            for severity in ["critical", "high", "medium", "low"]:
                if severity_counts[severity] > 0:
                    emoji = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢",
                    }
                    print(
                        f"  {emoji[severity]} {severity.title()}: {severity_counts[severity]}"
                    )

            print("\n📋 TOP ISSUE TYPES:")
            issue_type_counts = defaultdict(int)
            for issue in self.issues:
                issue_type_counts[issue.issue_type] += 1

            sorted_types = sorted(
                issue_type_counts.items(), key=lambda x: x[1], reverse=True
            )
            for issue_type, count in sorted_types[:5]:
                print(f"  • {issue_type}: {count}")

            print("\n🔍 SAMPLE ISSUES:")
            # Show top issues by severity
            critical_issues = [i for i in self.issues if i.severity == "critical"][:3]
            high_issues = [i for i in self.issues if i.severity == "high"][:2]
            sample_issues = critical_issues + high_issues

            for issue in sample_issues[:5]:
                print(f"\n  📁 {issue.file_path}:{issue.line_number}")
                print(f"     ❌ Found: {issue.incorrect_usage}")
                print(f"     ✅ Suggest: {issue.suggested_fix}")
                print(f"     🎯 Confidence: {issue.confidence:.1%}")

        print("\n" + "=" * 80)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Brand Consistency Audit Tool for Sophia Intel AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python brand_audit.py                          # Scan current directory
  python brand_audit.py --path /path/to/project  # Scan specific path
  python brand_audit.py --output report.json     # Save detailed report
  python brand_audit.py --format html            # Generate HTML report
  python brand_audit.py --ci                     # CI/CD mode (exit 1 if issues found)
        """,
    )

    parser.add_argument(
        "--path",
        "-p",
        default=os.getcwd(),
        help="Path to scan (default: current directory)",
    )

    parser.add_argument("--output", "-o", help="Output file for detailed report")

    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "html", "csv"],
        default="json",
        help="Report format (default: json)",
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI/CD mode - exit with status 1 if issues found",
    )

    parser.add_argument(
        "--severity-threshold",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Minimum severity to report (default: medium)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize auditor
    config = BrandAuditConfig()
    auditor = BrandConsistencyAuditor(config, args.path)

    # Run audit
    start_time = datetime.now()
    issues = auditor.scan_directory()
    end_time = datetime.now()

    # Filter by severity threshold
    severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    threshold = severity_levels[args.severity_threshold]

    filtered_issues = [
        issue for issue in issues if severity_levels[issue.severity] >= threshold
    ]
    auditor.issues = filtered_issues

    # Generate report
    report = auditor.generate_report()
    report.execution_time = (end_time - start_time).total_seconds()

    # Print summary
    auditor.print_summary()

    # Save detailed report if requested
    if args.output:
        try:
            if args.format == "json":
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(asdict(report), f, indent=2, ensure_ascii=False)
            elif args.format == "html":
                generate_html_report(report, args.output)
            elif args.format == "csv":
                generate_csv_report(report, args.output)

            print(f"\n📄 Detailed report saved to: {args.output}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

    # Exit with appropriate status for CI/CD
    if args.ci and filtered_issues:
        print(
            f"\n❌ CI/CD mode: Exiting with status 1 ({len(filtered_issues)} issues found)"
        )
        exit(1)

    print(f"\n✅ Brand audit completed in {report.execution_time:.2f} seconds")


def generate_html_report(report: AuditReport, output_file: str):
    """Generate HTML report"""
    # Escape HTML content in issue data
    import html

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brand Consistency Audit Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #fff; border: 1px solid #dee2e6; padding: 15px; border-radius: 4px; flex: 1; }}
        .issue {{ background: #fff; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .issue.high {{ border-left-color: #fd7e14; }}
        .issue.medium {{ border-left-color: #ffc107; }}
        .issue.low {{ border-left-color: #28a745; }}
        .file-path {{ font-family: monospace; background: #f8f9fa; padding: 2px 6px; border-radius: 3px; }}
        .code {{ font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Brand Consistency Audit Report</h1>
        <p>Generated: {timestamp}</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <h3>Files Scanned</h3>
            <h2>{total_files_scanned}</h2>
        </div>
        <div class="stat-card">
            <h3>Issues Found</h3>
            <h2>{issues_found}</h2>
        </div>
        <div class="stat-card">
            <h3>Clean Files</h3>
            <h2>{clean_files}</h2>
        </div>
    </div>

    <h2>🔍 Issues Found</h2>
    {issues_html}
</body>
</html>"""

    issues_html = ""
    for issue_data in report.issues:
        # Escape HTML content
        file_path = html.escape(issue_data["file_path"])
        line_content = html.escape(issue_data["line_content"])
        incorrect_usage = html.escape(issue_data["incorrect_usage"])
        suggested_fix = html.escape(issue_data["suggested_fix"])

        issues_html += f"""
        <div class="issue {issue_data['severity']}">
            <strong>📁 {file_path}:{issue_data['line_number']}</strong>
            <div class="code">{line_content}</div>
            <p><strong>Issue:</strong> {incorrect_usage}</p>
            <p><strong>Suggestion:</strong> {suggested_fix}</p>
            <p><strong>Confidence:</strong> {issue_data['confidence']:.1%}</p>
        </div>
        """

    html_content = html_template.format(
        timestamp=report.timestamp,
        total_files_scanned=report.total_files_scanned,
        issues_found=report.issues_found,
        clean_files=report.clean_files,
        issues_html=issues_html,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_csv_report(report: AuditReport, output_file: str):
    """Generate CSV report"""
    import csv

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "file_path",
            "line_number",
            "severity",
            "issue_type",
            "incorrect_usage",
            "suggested_fix",
            "confidence",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for issue_data in report.issues:
            writer.writerow({field: issue_data[field] for field in fieldnames})


if __name__ == "__main__":
    main()
