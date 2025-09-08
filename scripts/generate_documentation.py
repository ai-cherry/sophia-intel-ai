"""
Automated Documentation Generation System
Generates comprehensive documentation from code annotations, API specs, and other sources
"""

import argparse
import ast
import asyncio
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Import documentation generation libraries
try:
    import sphinx
    from sphinx.application import Sphinx
    from sphinx.util.docutils import docutils_namespace

    SPHINX_AVAILABLE = True
except ImportError:
    SPHINX_AVAILABLE = False

try:
    import pydoc

    PYDOC_AVAILABLE = True
except ImportError:
    PYDOC_AVAILABLE = False


@dataclass
class DocumentationConfig:
    """Configuration for documentation generation"""

    source_dirs: List[str]
    output_dir: str
    formats: List[str]  # ['markdown', 'html', 'pdf']
    include_private: bool
    include_tests: bool
    api_spec_paths: List[str]
    template_dir: Optional[str]
    custom_css: Optional[str]
    logo_path: Optional[str]

    @classmethod
    def from_file(cls, config_path: str) -> "DocumentationConfig":
        """Load configuration from file"""
        with open(config_path) as f:
            if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                config_data = yaml.safe_load(f)
            else:
                config_data = json.load(f)

        return cls(**config_data)


@dataclass
class APIEndpoint:
    """API endpoint documentation"""

    path: str
    method: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    examples: List[Dict[str, Any]]
    tags: List[str]


@dataclass
class ModuleDocumentation:
    """Module documentation structure"""

    name: str
    path: str
    description: str
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    constants: List[Dict[str, Any]]
    imports: List[str]


class CodeAnalyzer:
    """Analyzes Python code to extract documentation"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_module(self, file_path: str) -> ModuleDocumentation:
        """Analyze a Python module and extract documentation"""
        try:
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()

            tree = ast.parse(source_code)

            # Extract module-level docstring
            module_docstring = ast.get_docstring(tree) or ""

            # Extract classes, functions, and constants
            classes = self._extract_classes(tree)
            functions = self._extract_functions(tree)
            constants = self._extract_constants(tree)
            imports = self._extract_imports(tree)

            return ModuleDocumentation(
                name=Path(file_path).stem,
                path=file_path,
                description=module_docstring,
                classes=classes,
                functions=functions,
                constants=constants,
                imports=imports,
            )

        except Exception as e:
            self.logger.error(f"Error analyzing module {file_path}: {e}")
            return ModuleDocumentation(
                name=Path(file_path).stem,
                path=file_path,
                description=f"Error analyzing module: {e}",
                classes=[],
                functions=[],
                constants=[],
                imports=[],
            )

    def _extract_classes(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract class documentation from AST"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_doc = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node) or "",
                    "methods": [],
                    "attributes": [],
                    "inheritance": [base.id for base in node.bases if isinstance(base, ast.Name)],
                }

                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_doc = {
                            "name": item.name,
                            "docstring": ast.get_docstring(item) or "",
                            "args": [arg.arg for arg in item.args.args],
                            "decorators": [
                                self._get_decorator_name(dec) for dec in item.decorator_list
                            ],
                            "is_private": item.name.startswith("_"),
                            "is_async": isinstance(item, ast.AsyncFunctionDef),
                        }
                        class_doc["methods"].append(method_doc)

                classes.append(class_doc)

        return classes

    def _extract_functions(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract function documentation from AST"""
        functions = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_doc = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node) or "",
                    "args": [arg.arg for arg in node.args.args],
                    "defaults": len(node.args.defaults),
                    "decorators": [self._get_decorator_name(dec) for dec in node.decorator_list],
                    "is_private": node.name.startswith("_"),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "return_annotation": (
                        self._get_annotation(node.returns) if node.returns else None
                    ),
                }
                functions.append(func_doc)

        return functions

    def _extract_constants(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract constants from AST"""
        constants = []

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constant_doc = {
                            "name": target.id,
                            "value": self._get_literal_value(node.value),
                            "type": type(self._get_literal_value(node.value)).__name__,
                        }
                        constants.append(constant_doc)

        return constants

    def _extract_imports(self, tree: ast.Module) -> List[str]:
        """Extract import statements"""
        imports = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        return imports

    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}"
        else:
            return str(decorator)

    def _get_annotation(self, annotation) -> str:
        """Get type annotation string"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return f"{annotation.value.id}.{annotation.attr}"
        else:
            return str(annotation)

    def _get_literal_value(self, node):
        """Get literal value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.List):
            return [self._get_literal_value(item) for item in node.elts]
        elif isinstance(node, ast.Dict):
            return {
                self._get_literal_value(k): self._get_literal_value(v)
                for k, v in zip(node.keys, node.values)
            }
        else:
            return "<complex_value>"


class APIDocumentationParser:
    """Parses OpenAPI/Swagger specifications"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_openapi_spec(self, spec_path: str) -> Dict[str, Any]:
        """Parse OpenAPI/Swagger specification file"""
        try:
            with open(spec_path, encoding="utf-8") as f:
                if spec_path.endswith(".yaml") or spec_path.endswith(".yml"):
                    spec_data = yaml.safe_load(f)
                else:
                    spec_data = json.load(f)

            return self._process_openapi_spec(spec_data)

        except Exception as e:
            self.logger.error(f"Error parsing API spec {spec_path}: {e}")
            return {}

    def _process_openapi_spec(self, spec_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process OpenAPI specification data"""
        processed = {
            "info": spec_data.get("info", {}),
            "servers": spec_data.get("servers", []),
            "paths": {},
            "components": spec_data.get("components", {}),
            "security": spec_data.get("security", []),
        }

        # Process paths
        for path, path_data in spec_data.get("paths", {}).items():
            processed["paths"][path] = {}

            for method, method_data in path_data.items():
                if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    endpoint = APIEndpoint(
                        path=path,
                        method=method.upper(),
                        summary=method_data.get("summary", ""),
                        description=method_data.get("description", ""),
                        parameters=method_data.get("parameters", []),
                        responses=method_data.get("responses", {}),
                        examples=self._extract_examples(method_data),
                        tags=method_data.get("tags", []),
                    )
                    processed["paths"][path][method] = asdict(endpoint)

        return processed

    def _extract_examples(self, method_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract examples from method data"""
        examples = []

        # Check for examples in request body
        request_body = method_data.get("requestBody", {})
        content = request_body.get("content", {})

        for content_type, content_data in content.items():
            if "examples" in content_data:
                for example_name, example_data in content_data["examples"].items():
                    examples.append(
                        {
                            "name": example_name,
                            "type": "request",
                            "content_type": content_type,
                            "value": example_data.get("value", {}),
                        }
                    )

        # Check for examples in responses
        responses = method_data.get("responses", {})
        for status_code, response_data in responses.items():
            response_content = response_data.get("content", {})

            for content_type, content_data in response_content.items():
                if "examples" in content_data:
                    for example_name, example_data in content_data["examples"].items():
                        examples.append(
                            {
                                "name": example_name,
                                "type": "response",
                                "status_code": status_code,
                                "content_type": content_type,
                                "value": example_data.get("value", {}),
                            }
                        )

        return examples


class MarkdownGenerator:
    """Generates Markdown documentation"""

    def __init__(self, config: DocumentationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate_module_docs(self, module_docs: List[ModuleDocumentation]) -> str:
        """Generate Markdown documentation for Python modules"""
        markdown = []

        # Title and table of contents
        markdown.append("# API Documentation\n")
        markdown.append("Generated on: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        # Table of contents
        markdown.append("## Table of Contents\n")
        for module in module_docs:
            markdown.append(f"- [{module.name}](#{module.name.lower().replace('_', '-')})")
        markdown.append("")

        # Module documentation
        for module in module_docs:
            markdown.append(f"## {module.name}\n")

            if module.description:
                markdown.append(f"{module.description}\n")

            markdown.append(f"**File:** `{module.path}`\n")

            # Classes
            if module.classes:
                markdown.append("### Classes\n")

                for cls in module.classes:
                    markdown.append(f"#### `{cls['name']}`\n")

                    if cls["inheritance"]:
                        inheritance = ", ".join(cls["inheritance"])
                        markdown.append(f"*Inherits from: {inheritance}*\n")

                    if cls["docstring"]:
                        markdown.append(f"{cls['docstring']}\n")

                    # Methods
                    if cls["methods"]:
                        markdown.append("##### Methods\n")

                        for method in cls["methods"]:
                            if not self.config.include_private and method["is_private"]:
                                continue

                            async_prefix = "async " if method["is_async"] else ""
                            args_str = ", ".join(method["args"])
                            decorators = (
                                ", ".join(method["decorators"]) if method["decorators"] else ""
                            )

                            markdown.append(f"**`{async_prefix}{method['name']}({args_str})`**")

                            if decorators:
                                markdown.append(f"*Decorators: {decorators}*")

                            if method["docstring"]:
                                markdown.append(f"{method['docstring']}")

                            markdown.append("")

            # Functions
            if module.functions:
                markdown.append("### Functions\n")

                for func in module.functions:
                    if not self.config.include_private and func["is_private"]:
                        continue

                    async_prefix = "async " if func["is_async"] else ""
                    args_str = ", ".join(func["args"])
                    decorators = ", ".join(func["decorators"]) if func["decorators"] else ""

                    markdown.append(f"#### `{async_prefix}{func['name']}({args_str})`\n")

                    if decorators:
                        markdown.append(f"*Decorators: {decorators}*\n")

                    if func["return_annotation"]:
                        markdown.append(f"*Returns: {func['return_annotation']}*\n")

                    if func["docstring"]:
                        markdown.append(f"{func['docstring']}\n")

            # Constants
            if module.constants:
                markdown.append("### Constants\n")

                for const in module.constants:
                    markdown.append(f"- **`{const['name']}`**: {const['value']} _{const['type']}_")

                markdown.append("")

            markdown.append("---\n")

        return "\n".join(markdown)

    def generate_api_docs(self, api_specs: Dict[str, Dict[str, Any]]) -> str:
        """Generate Markdown documentation for API specifications"""
        markdown = []

        markdown.append("# API Reference\n")
        markdown.append("Generated on: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        for spec_name, spec_data in api_specs.items():
            info = spec_data.get("info", {})

            markdown.append(f"## {info.get('title', spec_name)}\n")

            if info.get("description"):
                markdown.append(f"{info['description']}\n")

            if info.get("version"):
                markdown.append(f"**Version:** {info['version']}\n")

            # Servers
            servers = spec_data.get("servers", [])
            if servers:
                markdown.append("### Base URLs\n")
                for server in servers:
                    markdown.append(
                        f"- `{server.get('url', '')}` - {server.get('description', '')}"
                    )
                markdown.append("")

            # Endpoints
            paths = spec_data.get("paths", {})
            if paths:
                markdown.append("### Endpoints\n")

                # Group by tags
                endpoints_by_tag = {}
                untagged_endpoints = []

                for path, methods in paths.items():
                    for method, endpoint_data in methods.items():
                        tags = endpoint_data.get("tags", [])
                        if tags:
                            for tag in tags:
                                if tag not in endpoints_by_tag:
                                    endpoints_by_tag[tag] = []
                                endpoints_by_tag[tag].append((path, method, endpoint_data))
                        else:
                            untagged_endpoints.append((path, method, endpoint_data))

                # Generate documentation for each tag
                for tag, endpoints in endpoints_by_tag.items():
                    markdown.append(f"#### {tag}\n")

                    for path, method, endpoint_data in endpoints:
                        self._generate_endpoint_docs(markdown, path, method, endpoint_data)

                # Untagged endpoints
                if untagged_endpoints:
                    markdown.append("#### Other Endpoints\n")

                    for path, method, endpoint_data in untagged_endpoints:
                        self._generate_endpoint_docs(markdown, path, method, endpoint_data)

            markdown.append("---\n")

        return "\n".join(markdown)

    def _generate_endpoint_docs(
        self, markdown: List[str], path: str, method: str, endpoint_data: Dict[str, Any]
    ):
        """Generate documentation for a single API endpoint"""
        summary = endpoint_data.get("summary", "")
        description = endpoint_data.get("description", "")

        markdown.append(f"##### `{method.upper()} {path}`\n")

        if summary:
            markdown.append(f"**{summary}**\n")

        if description:
            markdown.append(f"{description}\n")

        # Parameters
        parameters = endpoint_data.get("parameters", [])
        if parameters:
            markdown.append("**Parameters:**\n")

            for param in parameters:
                param_name = param.get("name", "")
                param_type = param.get("schema", {}).get("type", "string")
                param_desc = param.get("description", "")
                param_required = param.get("required", False)
                param_location = param.get("in", "")

                required_text = " _(required)_" if param_required else " _(optional)_"
                location_text = f" _{param_location}_"

                markdown.append(
                    f"- `{param_name}` ({param_type}){location_text}{required_text}: {param_desc}"
                )

            markdown.append("")

        # Request body
        request_body = endpoint_data.get("requestBody", {})
        if request_body:
            markdown.append("**Request Body:**\n")

            content = request_body.get("content", {})
            for content_type, content_data in content.items():
                markdown.append(f"Content-Type: `{content_type}`\n")

                schema = content_data.get("schema", {})
                if schema:
                    markdown.append(f"```json\n{json.dumps(schema, indent=2)}\n```\n")

        # Responses
        responses = endpoint_data.get("responses", {})
        if responses:
            markdown.append("**Responses:**\n")

            for status_code, response_data in responses.items():
                response_desc = response_data.get("description", "")
                markdown.append(f"- `{status_code}`: {response_desc}")

            markdown.append("")

        # Examples
        examples = endpoint_data.get("examples", [])
        if examples:
            markdown.append("**Examples:**\n")

            for example in examples:
                example_name = example.get("name", "Example")
                example_type = example.get("type", "request")
                example_value = example.get("value", {})

                markdown.append(f"*{example_name} ({example_type}):*\n")
                markdown.append(f"```json\n{json.dumps(example_value, indent=2)}\n```\n")

        markdown.append("")


class HTMLGenerator:
    """Generates HTML documentation"""

    def __init__(self, config: DocumentationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate_html_docs(self, content: str, title: str = "Documentation") -> str:
        """Generate HTML documentation from Markdown content"""
        try:
            import markdown

            # Convert Markdown to HTML
            md = markdown.Markdown(extensions=["codehilite", "toc", "tables", "fenced_code"])
            html_content = md.convert(content)

            # Create full HTML document
            html_template = self._get_html_template()

            return html_template.format(
                title=title,
                content=html_content,
                css=self._get_css_content(),
                generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

        except ImportError:
            self.logger.warning("Markdown library not available, generating simple HTML")
            return self._generate_simple_html(content, title)

    def _get_html_template(self) -> str:
        """Get HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p class="generated">Generated on {generated_date}</p>
        </header>
        <main>
            {content}
        </main>
        <footer>
            <p>Generated by Sophia AI Documentation System</p>
        </footer>
    </div>
</body>
</html>"""

    def _get_css_content(self) -> str:
        """Get CSS content for HTML documentation"""
        if self.config.custom_css and os.path.exists(self.config.custom_css):
            with open(self.config.custom_css) as f:
                return f.read()

        # Default CSS
        return """
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6; 
            color: #333; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        .container { background: white; }
        header { border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }
        h1, h2, h3, h4, h5, h6 { color: #007acc; margin-top: 30px; }
        code { 
            background: #f5f5f5; 
            padding: 2px 4px; 
            border-radius: 3px; 
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', monospace;
        }
        pre { 
            background: #f8f8f8; 
            padding: 15px; 
            border-radius: 5px; 
            overflow-x: auto; 
            border-left: 4px solid #007acc;
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 20px 0;
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }
        th { background-color: #f2f2f2; font-weight: 600; }
        .generated { 
            color: #666; 
            font-style: italic; 
            margin: 0;
        }
        footer { 
            margin-top: 50px; 
            padding-top: 20px; 
            border-top: 1px solid #eee; 
            color: #666; 
            text-align: center;
        }
        """

    def _generate_simple_html(self, content: str, title: str) -> str:
        """Generate simple HTML without Markdown processing"""
        # Basic Markdown to HTML conversion
        html_content = content.replace("\n", "<br>\n")
        html_content = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html_content, flags=re.MULTILINE)
        html_content = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html_content, flags=re.MULTILINE)
        html_content = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html_content, flags=re.MULTILINE)
        html_content = re.sub(r"`([^`]+)`", r"<code>\1</code>", html_content)

        template = self._get_html_template()
        return template.format(
            title=title,
            content=html_content,
            css=self._get_css_content(),
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )


class DocumentationGenerator:
    """Main documentation generation orchestrator"""

    def __init__(self, config: DocumentationConfig):
        self.config = config
        self.code_analyzer = CodeAnalyzer()
        self.api_parser = APIDocumentationParser()
        self.markdown_generator = MarkdownGenerator(config)
        self.html_generator = HTMLGenerator(config)
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up logging"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def generate_documentation(self) -> Dict[str, str]:
        """Generate all documentation"""
        self.logger.info("Starting documentation generation...")

        results = {}

        try:
            # Ensure output directory exists
            os.makedirs(self.config.output_dir, exist_ok=True)

            # Generate code documentation
            if self.config.source_dirs:
                self.logger.info("Generating code documentation...")
                code_docs = await self._generate_code_documentation()
                results.update(code_docs)

            # Generate API documentation
            if self.config.api_spec_paths:
                self.logger.info("Generating API documentation...")
                api_docs = await self._generate_api_documentation()
                results.update(api_docs)

            # Generate index file
            self.logger.info("Generating index...")
            index_content = self._generate_index(results)

            for format_type in self.config.formats:
                if format_type == "markdown":
                    index_path = os.path.join(self.config.output_dir, "index.md")
                    with open(index_path, "w", encoding="utf-8") as f:
                        f.write(index_content)
                    results["index_md"] = index_path

                elif format_type == "html":
                    html_content = self.html_generator.generate_html_docs(
                        index_content, "Documentation Index"
                    )
                    index_path = os.path.join(self.config.output_dir, "index.html")
                    with open(index_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    results["index_html"] = index_path

            self.logger.info(
                f"Documentation generation completed. Files saved to: {self.config.output_dir}"
            )

        except Exception as e:
            self.logger.error(f"Error generating documentation: {e}")
            raise

        return results

    async def _generate_code_documentation(self) -> Dict[str, str]:
        """Generate documentation from source code"""
        results = {}

        # Collect all Python files
        python_files = []
        for source_dir in self.config.source_dirs:
            if os.path.exists(source_dir):
                for root, dirs, files in os.walk(source_dir):
                    # Skip test directories if not including tests
                    if not self.config.include_tests:
                        dirs[:] = [d for d in dirs if not d.startswith("test")]

                    for file in files:
                        if file.endswith(".py") and not file.startswith("__"):
                            python_files.append(os.path.join(root, file))

        self.logger.info(f"Found {len(python_files)} Python files to analyze")

        # Analyze modules in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            module_docs = list(executor.map(self.code_analyzer.analyze_module, python_files))

        # Generate documentation in requested formats
        if module_docs:
            markdown_content = self.markdown_generator.generate_module_docs(module_docs)

            for format_type in self.config.formats:
                if format_type == "markdown":
                    output_path = os.path.join(self.config.output_dir, "code_documentation.md")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    results["code_md"] = output_path

                elif format_type == "html":
                    html_content = self.html_generator.generate_html_docs(
                        markdown_content, "Code Documentation"
                    )
                    output_path = os.path.join(self.config.output_dir, "code_documentation.html")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    results["code_html"] = output_path

        return results

    async def _generate_api_documentation(self) -> Dict[str, str]:
        """Generate documentation from API specifications"""
        results = {}

        # Parse API specifications
        api_specs = {}
        for spec_path in self.config.api_spec_paths:
            if os.path.exists(spec_path):
                spec_name = Path(spec_path).stem
                spec_data = self.api_parser.parse_openapi_spec(spec_path)
                if spec_data:
                    api_specs[spec_name] = spec_data

        self.logger.info(f"Parsed {len(api_specs)} API specifications")

        # Generate documentation in requested formats
        if api_specs:
            markdown_content = self.markdown_generator.generate_api_docs(api_specs)

            for format_type in self.config.formats:
                if format_type == "markdown":
                    output_path = os.path.join(self.config.output_dir, "api_documentation.md")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    results["api_md"] = output_path

                elif format_type == "html":
                    html_content = self.html_generator.generate_html_docs(
                        markdown_content, "API Documentation"
                    )
                    output_path = os.path.join(self.config.output_dir, "api_documentation.html")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    results["api_html"] = output_path

        return results

    def _generate_index(self, results: Dict[str, str]) -> str:
        """Generate index page content"""
        index_content = []

        index_content.append("# Documentation Index\n")
        index_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        index_content.append("## Available Documentation\n")

        # Code documentation links
        if "code_md" in results or "code_html" in results:
            index_content.append("### Code Documentation")
            if "code_md" in results:
                index_content.append("- [Code Documentation (Markdown)](code_documentation.md)")
            if "code_html" in results:
                index_content.append("- [Code Documentation (HTML)](code_documentation.html)")
            index_content.append("")

        # API documentation links
        if "api_md" in results or "api_html" in results:
            index_content.append("### API Documentation")
            if "api_md" in results:
                index_content.append("- [API Documentation (Markdown)](api_documentation.md)")
            if "api_html" in results:
                index_content.append("- [API Documentation (HTML)](api_documentation.html)")
            index_content.append("")

        # Generation statistics
        index_content.append("## Generation Statistics\n")
        index_content.append(f"- Source directories: {len(self.config.source_dirs)}")
        index_content.append(f"- API specifications: {len(self.config.api_spec_paths)}")
        index_content.append(f"- Output formats: {', '.join(self.config.formats)}")
        index_content.append(f"- Include private members: {self.config.include_private}")
        index_content.append(f"- Include tests: {self.config.include_tests}")

        return "\n".join(index_content)


async def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description="Generate comprehensive documentation")
    parser.add_argument(
        "--config", "-c", type=str, help="Configuration file path", default="docs_config.yaml"
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Output directory", default="docs/generated"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "html", "pdf"],
        action="append",
        help="Output format(s)",
    )
    parser.add_argument(
        "--source", "-s", type=str, action="append", help="Source directory to analyze"
    )
    parser.add_argument(
        "--api-spec", "-a", type=str, action="append", help="API specification file path"
    )
    parser.add_argument(
        "--include-private", action="store_true", help="Include private members in documentation"
    )
    parser.add_argument(
        "--include-tests", action="store_true", help="Include test files in documentation"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Load configuration
    if os.path.exists(args.config):
        config = DocumentationConfig.from_file(args.config)
    else:
        # Create config from command line arguments
        config = DocumentationConfig(
            source_dirs=args.source or ["./"],
            output_dir=args.output,
            formats=args.format or ["markdown", "html"],
            include_private=args.include_private,
            include_tests=args.include_tests,
            api_spec_paths=args.api_spec or [],
            template_dir=None,
            custom_css=None,
            logo_path=None,
        )

    # Generate documentation
    generator = DocumentationGenerator(config)
    results = await generator.generate_documentation()

    print("\n✅ Documentation generated successfully!")
    print(f"📁 Output directory: {config.output_dir}")
    print("📄 Generated files:")
    for key, path in results.items():
        print(f"   - {key}: {path}")


if __name__ == "__main__":
    asyncio.run(main())
