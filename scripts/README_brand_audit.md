# Brand Consistency Audit Tool

A comprehensive Python script that scans your codebase for brand consistency issues and generates detailed reports.

## Features

- ✅ **Comprehensive Scanning**: Scans all text files in your project for brand consistency issues
- 🎯 **Smart Detection**: Uses regex patterns to find incorrect brand usage like "Pay Ready" instead of "Sophia Intel AI"
- 📊 **Multiple Output Formats**: JSON, HTML, and CSV reports
- 🚨 **CI/CD Integration**: Can be used in automated pipelines with exit codes
- ⚙️ **Configurable Thresholds**: Filter by issue severity (low, medium, high, critical)
- 🚀 **Fast & Efficient**: Scans thousands of files quickly with smart exclusions

## Quick Start

```bash
# Basic scan of current directory
python3 scripts/brand_audit.py

# Scan specific directory with HTML report
python3 scripts/brand_audit.py --path /path/to/project --output report.html --format html

# CI/CD mode - only critical issues, exit 1 if found
python3 scripts/brand_audit.py --ci --severity-threshold critical
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--path`, `-p` | Path to scan (default: current directory) |
| `--output`, `-o` | Output file for detailed report |
| `--format`, `-f` | Report format: json, html, csv (default: json) |
| `--ci` | CI/CD mode - exit with status 1 if issues found |
| `--severity-threshold` | Minimum severity: low, medium, high, critical |
| `--verbose`, `-v` | Enable verbose logging |

## Issue Types Detected

### Critical Issues 🔴
- **Pay Ready variations**: "Pay Ready", "PayReady", "payready"
- **Pay.com variations**: "Pay.com", "pay.com"
- **Generic placeholders**: "YourCompany", "CompanyName", "Example Corp"

### High Issues 🟠
- **Typos**: "Sofhia" instead of "Sophia"
- **Generic business terms**: "Your Business", "Acme Corp"

### Medium Issues 🟡
- **Spacing issues**: "sophia intel ai" vs "Sophia Intel AI"
- **Case inconsistencies**: "SOPHIA", "SOPHIA" in wrong contexts

### Low Issues 🟢
- **Technical formatting**: "sophia-intel-ai" in display text

## Sample Output

```
================================================================================
BRAND CONSISTENCY AUDIT SUMMARY
================================================================================
📁 Files Scanned: 72355
⚠️  Issues Found: 1732
🔴 Files with Issues: 493
✅ Clean Files: 71862

📊 ISSUES BY SEVERITY:
  🔴 Critical: 1094
  🟠 High: 35
  🟡 Medium: 603

📋 TOP ISSUE TYPES:
  • pay_ready_variation: 1094
  • payready_lowercase: 318
  • generic_company_name: 12

🔍 SAMPLE ISSUES:

  📁 USER_TOKEN_SETUP.md:11
     ❌ Found: Pay Ready
     ✅ Suggest: Sophia Intel AI
     🎯 Confidence: 100.0%
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Brand Consistency Check
  run: |
    python3 scripts/brand_audit.py --ci --severity-threshold high
    if [ $? -eq 1 ]; then
      echo "Brand consistency issues found! Please review the audit report."
      exit 1
    fi
```

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: brand-audit
        name: Brand Consistency Audit
        entry: python3 scripts/brand_audit.py --ci --severity-threshold critical
        language: system
        pass_filenames: false
```

## Configuration

The script automatically excludes common directories and files:
- `.git/`, `node_modules/`, `.venv/`, `__pycache__/`
- Binary files, logs, databases, lock files
- Backup directories and temporary files

## Report Formats

### JSON Report
Detailed machine-readable format with all issues, metadata, and statistics.

### HTML Report
Visual web-based report with color-coded issues and easy navigation.

### CSV Report  
Spreadsheet-friendly format for analysis and tracking.

## Performance

- Scans ~70,000 files in under 10 seconds
- Memory efficient streaming file processing
- Smart binary file detection
- Configurable confidence thresholds

## Use Cases

1. **Development**: Catch brand inconsistencies during development
2. **Code Reviews**: Automated brand checking in PR workflows
3. **Release Preparation**: Ensure brand consistency before releases  
4. **Maintenance**: Periodic audits of large codebases
5. **Migration**: Verify brand updates during rebranding projects

## Best Practices

1. Run regularly as part of your development workflow
2. Start with `--severity-threshold high` to focus on critical issues
3. Use HTML reports for manual review and sharing with teams
4. Include in CI/CD for automated quality gates
5. Review false positives and adjust patterns as needed

## Troubleshooting

### Common Issues

**Too many false positives?**
- Increase severity threshold: `--severity-threshold high`
- The script may flag legitimate technical references

**Script running slowly?**
- Large repositories with many files take time
- Consider scanning specific directories: `--path app/`

**Need to customize patterns?**
- Edit the `BrandAuditConfig` class in the script
- Add new patterns or adjust existing ones

### Getting Help

```bash
# Show help
python3 scripts/brand_audit.py --help

# Run with verbose output for debugging
python3 scripts/brand_audit.py --verbose
```

## Examples

```bash
# Quick scan for critical issues only
python3 scripts/brand_audit.py --severity-threshold critical

# Generate HTML report for team review
python3 scripts/brand_audit.py --output brand_report.html --format html

# Scan specific app directory
python3 scripts/brand_audit.py --path app/ --output app_brand_issues.json

# CI pipeline check
python3 scripts/brand_audit.py --ci --severity-threshold high --output ci_report.json
```

---

**Note**: This tool is designed for the Sophia Intel AI project but can be adapted for other projects by modifying the brand patterns in the configuration.