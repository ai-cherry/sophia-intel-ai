# Comprehensive Meta-Tagging System

The meta-tagging system provides intelligent code analysis, classification, and enhancement suggestions for the Sophia AI codebase. It enables AI systems to better understand code structure, component relationships, and optimization opportunities.

## Features

### 🏷️ **Intelligent Code Classification**

- **Semantic Role Detection**: Automatically classifies components as orchestrators, processors, gateways, agents, repositories, services, utilities, etc.
- **Complexity Assessment**: Evaluates code complexity from trivial to critical levels
- **Risk Analysis**: Identifies modification risks and potential impact areas
- **Capability Detection**: Discovers component capabilities (async, API, database, AI, etc.)

### 🤖 **AI-Powered Enhancement Hints**

- **Optimization Opportunities**: Detects performance improvements, caching opportunities, and algorithmic enhancements
- **Refactoring Suggestions**: Identifies code smells, architectural issues, and maintainability concerns
- **Security Analysis**: Finds potential vulnerabilities and security best practices violations
- **Testing Requirements**: Analyzes test coverage gaps and specialized testing needs

### 📊 **Comprehensive Analytics**

- **Dependency Mapping**: Tracks component relationships and coupling
- **Quality Metrics**: Measures documentation, type safety, and code quality
- **Priority Assessment**: Ranks components by maintenance priority and business impact
- **Trend Analysis**: Monitors codebase evolution and technical debt accumulation

## Quick Start

### 1. Initialize the System

Run the initialization script to scan your entire codebase:

```bash
# Basic initialization
python scripts/init_meta_tagging.py

# With custom options
python scripts/init_meta_tagging.py --root-dir . --max-concurrent 10 --output my_registry.json
```

### 2. Basic Usage in Code

```python
from app.scaffolding import (
    MetaTagRegistry, AutoTagger, SemanticClassifier,
    generate_ai_hints, detailed_analysis
)

# Quick classification
from app.scaffolding import quick_classify
role = quick_classify("MyComponent", "my_file.py", code_content)
print(f"Component role: {role.value}")

# Detailed analysis
analysis = detailed_analysis("MyComponent", "my_file.py", code_content)
print(f"Complexity: {analysis['complexity']['level']}")
print(f"Capabilities: {list(analysis['capabilities'].keys())}")
```

### 3. Registry Operations

```python
# Get global registry
registry = get_global_registry()

# Search components
orchestrators = registry.get_by_role(SemanticRole.ORCHESTRATOR)
high_complexity = registry.search(complexity=Complexity.HIGH)

# Get statistics
stats = registry.stats()
print(f"Total components: {stats['total_tags']}")
print(f"High-risk components: {stats['high_risk_components']}")
```

## Architecture

### Core Components

#### 1. **MetaTag** - Component Metadata

```python
@dataclass
class MetaTag:
    # Identity
    component_name: str
    file_path: str
    line_range: tuple[int, int]

    # Classification
    semantic_role: SemanticRole
    complexity: Complexity
    priority: Priority
    modification_risk: ModificationRisk

    # Capabilities & Dependencies
    capabilities: Set[str]
    dependencies: Set[str]
    external_integrations: Set[str]

    # AI Enhancement Hints
    optimization_opportunities: List[str]
    refactoring_suggestions: List[str]
    test_requirements: List[str]
    security_considerations: List[str]

    # Quality Metrics
    cyclomatic_complexity: int
    lines_of_code: int
    documentation_score: float
    type_safety_score: float
```

#### 2. **SemanticClassifier** - Pattern-Based Analysis

- **Multi-Context Analysis**: Analyzes file names, class names, imports, decorators, docstrings
- **Weighted Pattern Matching**: Uses confidence-weighted patterns for accurate classification
- **Capability Detection**: Identifies component capabilities through code analysis
- **Risk Assessment**: Evaluates modification risks based on code patterns

#### 3. **AIHintsPipeline** - Enhancement Suggestions

- **Pattern Analysis**: Detects optimization opportunities and code smells
- **Risk Assessment**: Identifies high-risk modification areas
- **Test Requirements**: Analyzes testing needs and coverage gaps
- **Security Analysis**: Finds potential security vulnerabilities

#### 4. **MetaTagRegistry** - Centralized Management

- **Indexed Storage**: Efficient component lookup and search
- **Dependency Tracking**: Maintains component relationship graphs
- **Persistent Storage**: JSON-based registry with versioning
- **Query Interface**: Flexible search and filtering capabilities

## Configuration

### File Patterns

The system processes these file types by default:

- **Python**: `*.py`
- **JavaScript/TypeScript**: `*.js`, `*.ts`, `*.jsx`, `*.tsx`
- **Configuration**: `*.json`, `*.yaml`, `*.yml`, `*.toml`
- **Documentation**: `*.md`, `*.rst`, `*.txt`

### Classification Patterns

#### Semantic Roles

- **Orchestrator**: Coordinates workflows, manages business processes
- **Processor**: Transforms data, handles computations
- **Gateway**: API endpoints, external interfaces
- **Agent**: AI agents, autonomous systems
- **Repository**: Data persistence, storage layers
- **Service**: Business logic, core operations
- **Utility**: Helper functions, shared components

#### Complexity Levels

- **Trivial** (1): Simple utilities, basic operations
- **Low** (2): Straightforward logic, minimal dependencies
- **Moderate** (3): Multiple responsibilities, some complexity
- **High** (4): Complex algorithms, many dependencies
- **Critical** (5): Core systems, high modification risk

## Advanced Usage

### Custom Analysis Pipeline

```python
from app.scaffolding.ai_hints import AIHintsPipeline, Severity

# Create custom pipeline
pipeline = AIHintsPipeline()

# Generate hints
hints = await pipeline.generate_hints(code_content, meta_tag)

# Filter by criteria
critical_hints = pipeline.filter_hints(
    hints,
    min_severity=Severity.HIGH,
    max_hints=10
)

# Generate summary report
summary = pipeline.generate_summary_report(hints)
```

### Registry Search and Analytics

```python
# Complex searches
high_risk_orchestrators = registry.search(
    role=SemanticRole.ORCHESTRATOR,
    complexity=Complexity.HIGH
)

# Dependency analysis
dependencies = registry.get_dependencies("MyComponent")
dependents = registry.get_dependents("MyComponent")

# Get optimization candidates
candidates = registry.get_optimization_candidates()
```

### Batch Processing

```python
# Process directory
results = await auto_tag_directory(
    directory_path="./app",
    file_patterns=["*.py", "*.js"]
)

# Process specific files
for file_path, tags in results.items():
    print(f"{file_path}: {len(tags)} components")
```

## Command Line Interface

### Initialization Script Options

```bash
python scripts/init_meta_tagging.py [OPTIONS]

Options:
  --root-dir, -r TEXT          Root directory to scan (default: .)
  --output, -o TEXT            Registry output file (default: meta_tags_registry.json)
  --report, -R TEXT            Analysis report file (default: meta_tagging_report.json)
  --max-concurrent, -c INT     Max concurrent processing (default: 10)
  --no-report                  Skip generating analysis report
  --no-registry               Skip saving registry file
  --verbose, -v               Enable verbose logging
  --quiet, -q                 Suppress progress output
```

### Example Commands

```bash
# Full codebase analysis with report
python scripts/init_meta_tagging.py --verbose

# Fast scan without report
python scripts/init_meta_tagging.py --no-report --max-concurrent 20

# Specific directory with custom output
python scripts/init_meta_tagging.py --root-dir ./app/swarms --output swarms_tags.json
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI
from app.scaffolding import get_global_registry

app = FastAPI()

@app.get("/api/components/search")
async def search_components(role: str = None, complexity: int = None):
    registry = get_global_registry()

    if role:
        components = registry.get_by_role(SemanticRole(role))
    else:
        components = registry.search(complexity=Complexity(complexity))

    return [tag.to_dict() for tag in components]

@app.get("/api/components/{component_name}/hints")
async def get_component_hints(component_name: str):
    registry = get_global_registry()
    tag = registry.get_by_component(component_name)

    if not tag:
        raise HTTPException(404, "Component not found")

    return {
        'optimization_opportunities': tag.optimization_opportunities,
        'refactoring_suggestions': tag.refactoring_suggestions,
        'test_requirements': tag.test_requirements,
        'security_considerations': tag.security_considerations
    }
```

### Development Workflow Integration

```python
# Pre-commit hook
import subprocess
from app.scaffolding import quick_pattern_analysis

def analyze_changed_files():
    # Get changed files
    result = subprocess.run(['git', 'diff', '--name-only'], capture_output=True, text=True)
    changed_files = result.stdout.strip().split('\n')

    issues = []
    for file_path in changed_files:
        if file_path.endswith('.py'):
            with open(file_path, 'r') as f:
                content = f.read()

            hints = quick_pattern_analysis(content, file_path)
            critical_hints = [h for h in hints if h.severity.value >= 4]

            if critical_hints:
                issues.extend(critical_hints)

    if issues:
        print(f"⚠️  Found {len(issues)} critical issues in changed files:")
        for issue in issues:
            print(f"  - {issue.title} in {issue.file_path}")
        return False

    return True
```

## Performance and Scalability

### Processing Performance

- **Concurrent Processing**: Configurable concurrency for large codebases
- **Incremental Updates**: Only reprocess changed files
- **Efficient Storage**: Indexed JSON storage with fast lookups
- **Memory Management**: Streaming processing for large files

### Scalability Features

- **Distributed Processing**: Support for multi-machine analysis
- **Database Backend**: Optional PostgreSQL/MongoDB storage
- **API Integration**: RESTful interface for external tools
- **Plugin Architecture**: Extensible pattern matching and hint generation

## Best Practices

### 1. **Regular Analysis**

```bash
# Set up weekly analysis
crontab -e
0 2 * * 1 cd /path/to/sophia-intel-ai && python scripts/init_meta_tagging.py
```

### 2. **CI/CD Integration**

```yaml
# .github/workflows/code-analysis.yml
- name: Run Meta-Tagging Analysis
  run: |
    python scripts/init_meta_tagging.py --no-report
    python -c "
    from app.scaffolding import get_global_registry
    registry = get_global_registry()
    critical = registry.get_high_risk_components()
    if len(critical) > 10:
        exit(1)
    "
```

### 3. **Team Dashboard**

```python
# Generate team insights
def generate_team_report():
    registry = get_global_registry()
    stats = registry.stats()

    return {
        'total_components': stats['total_tags'],
        'technical_debt_score': calculate_debt_score(registry),
        'security_issues': len([tag for tag in registry.get_all()
                              if tag.security_considerations]),
        'optimization_opportunities': len(registry.get_optimization_candidates()),
        'testing_gaps': calculate_testing_gaps(registry)
    }
```

## Troubleshooting

### Common Issues

#### 1. **Import Errors**

```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH="${PYTHONPATH}:/path/to/sophia-intel-ai"

# Or add to your script
import sys
sys.path.insert(0, '/path/to/sophia-intel-ai')
```

#### 2. **Performance Issues**

```bash
# Reduce concurrency for memory-constrained systems
python scripts/init_meta_tagging.py --max-concurrent 5

# Process specific directories
python scripts/init_meta_tagging.py --root-dir ./app/core
```

#### 3. **Registry Corruption**

```python
# Reset registry
import os
if os.path.exists('meta_tags_registry.json'):
    os.remove('meta_tags_registry.json')

# Reinitialize
python scripts/init_meta_tagging.py
```

### Logging and Debugging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Check registry stats
registry = get_global_registry()
print(registry.stats())

# Validate specific component
tag = registry.get_by_component("MyComponent")
if tag:
    print(f"Found: {tag.component_name} - {tag.semantic_role.value}")
else:
    print("Component not found")
```

## Contributing

### Adding New Pattern Types

1. **Extend SemanticRole enum** in `meta_tagging.py`
2. **Add patterns** to `SemanticClassifier._initialize_role_patterns()`
3. **Update documentation** and examples

### Adding New Hint Types

1. **Extend HintType enum** in `ai_hints.py`
2. **Add analyzer class** following existing patterns
3. \*\*Integrate with AIHintsPipeline.generate_hints()`

### Testing

```bash
# Run comprehensive tests
python scripts/test_meta_tagging.py

# Test specific components
python -c "
from app.scaffolding import detailed_analysis
result = detailed_analysis('TestComponent', 'test.py', 'def test(): pass')
print(result['classification']['semantic_role'])
"
```

## Roadmap

### Planned Features

- **Machine Learning Integration**: Training custom classification models
- **IDE Plugins**: VS Code and IntelliJ extensions
- **Real-time Analysis**: File watcher integration
- **Team Collaboration**: Shared annotations and reviews
- **Quality Gates**: Automated quality enforcement
- **Metrics Dashboard**: Web-based analytics interface

### Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0** (Planned): ML classification models
- **v1.2.0** (Planned): IDE integration
- **v2.0.0** (Planned): Distributed processing

---

_For questions, issues, or contributions, please refer to the project repository or contact the development team._
