"""
Coder Agent for SOPHIA Intel Agent Swarm

Responsible for:
- Code generation and implementation
- API development and integration
- Database schema creation
- Frontend component development
- Script and automation creation
"""

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base_agent import AgentCapability, AgentTask, AgentType, BaseAgent, Priority, TaskStatus


class CoderAgent(BaseAgent):
    """
    Coder Agent specializes in code generation and implementation.

    Capabilities:
    - Backend API development
    - Frontend component creation
    - Database schema design
    - Script automation
    - Code refactoring and optimization
    """

    def __init__(self, ai_router_url: str = "http://localhost:5000/api/ai/route"):
        capabilities = [
            AgentCapability(
                name="backend_development",
                description="Create backend APIs, services, and business logic",
                input_types=["api_spec", "backend_task", "service_implementation"],
                output_types=["python_code", "api_endpoints", "service_code"],
                estimated_duration=1800,  # 30 minutes
                confidence_score=0.92,
            ),
            AgentCapability(
                name="frontend_development",
                description="Create frontend components and user interfaces",
                input_types=["ui_spec", "component_request", "frontend_task"],
                output_types=["react_component", "html_css", "javascript_code"],
                estimated_duration=1200,  # 20 minutes
                confidence_score=0.88,
            ),
            AgentCapability(
                name="database_design",
                description="Design database schemas and queries",
                input_types=["data_model", "schema_request", "database_task"],
                output_types=["sql_schema", "migration_scripts", "query_code"],
                estimated_duration=900,  # 15 minutes
                confidence_score=0.85,
            ),
            AgentCapability(
                name="script_automation",
                description="Create automation scripts and utilities",
                input_types=["automation_request", "script_task", "utility_request"],
                output_types=["bash_script", "python_script", "automation_code"],
                estimated_duration=600,  # 10 minutes
                confidence_score=0.90,
            ),
            AgentCapability(
                name="code_refactoring",
                description="Refactor and optimize existing code",
                input_types=["refactor_request", "optimization_task", "code_improvement"],
                output_types=["refactored_code", "optimized_code", "improved_code"],
                estimated_duration=1200,  # 20 minutes
                confidence_score=0.87,
            ),
        ]

        super().__init__(
            agent_type=AgentType.CODER,
            name="Code Generator",
            description="Generates and implements code across multiple languages and frameworks",
            capabilities=capabilities,
            ai_router_url=ai_router_url,
        )

        # Code generation templates and patterns
        self.code_templates = {
            "flask_api": self._get_flask_api_template(),
            "react_component": self._get_react_component_template(),
            "python_class": self._get_python_class_template(),
            "sql_schema": self._get_sql_schema_template(),
        }

    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a coding task"""
        self.logger.info(f"Executing coding task: {task.type}")

        if task.type == "api_spec":
            return await self._implement_api(task)
        elif task.type == "backend_task":
            return await self._develop_backend(task)
        elif task.type == "frontend_task":
            return await self._develop_frontend(task)
        elif task.type == "database_task":
            return await self._design_database(task)
        elif task.type == "script_task":
            return await self._create_script(task)
        elif task.type == "refactor_request":
            return await self._refactor_code(task)
        else:
            raise ValueError(f"Unknown task type: {task.type}")

    async def _implement_api(self, task: AgentTask) -> Dict[str, Any]:
        """Implement API endpoints based on specification"""
        api_spec = task.requirements.get("api_spec", {})
        endpoints = api_spec.get("endpoints", [])
        framework = task.requirements.get("framework", "flask")

        implementation_prompt = f"""
        Implement a {framework} API with the following specification:
        
        API Specification:
        {api_spec}
        
        Requirements:
        - Use {framework} framework
        - Include proper error handling
        - Add input validation
        - Include CORS support
        - Add logging and monitoring
        - Follow REST conventions
        - Include docstrings and comments
        
        Generate complete, production-ready code with:
        1. Main application file
        2. Route handlers
        3. Data models
        4. Error handling
        5. Configuration
        6. Requirements file
        
        Focus on Claude Sonnet 4 integration via the AI router for any AI functionality.
        """

        ai_response = await self.communicate_with_ai(
            prompt=implementation_prompt,
            task_type="code_generation",
            context={"api_spec": api_spec, "framework": framework},
        )

        # Parse and structure the generated code
        code_files = await self._parse_code_files(ai_response)

        # Validate the generated code
        validation_results = await self._validate_code(code_files)

        return {
            "implementation_type": "api",
            "framework": framework,
            "code_files": code_files,
            "validation": validation_results,
            "endpoints": len(endpoints),
            "estimated_lines": sum(len(code.split("\n")) for code in code_files.values()),
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

    async def _develop_backend(self, task: AgentTask) -> Dict[str, Any]:
        """Develop backend services and business logic"""
        requirements = task.requirements
        description = task.description

        backend_prompt = f"""
        Develop backend functionality for:
        
        Task: {description}
        Requirements: {requirements}
        
        Create:
        1. Service classes with business logic
        2. Data access layer
        3. API endpoints if needed
        4. Error handling and validation
        5. Unit tests
        6. Configuration management
        
        Use modern Python patterns:
        - Async/await for I/O operations
        - Type hints throughout
        - Proper exception handling
        - Logging and monitoring
        - Clean architecture principles
        
        Integrate with SOPHIA Intel's AI router for any AI functionality.
        """

        ai_response = await self.communicate_with_ai(
            prompt=backend_prompt, task_type="code_generation", context={"requirements": requirements}
        )

        code_files = await self._parse_code_files(ai_response)

        return {
            "implementation_type": "backend",
            "code_files": code_files,
            "services": await self._identify_services(code_files),
            "dependencies": await self._extract_dependencies(code_files),
            "test_coverage": await self._estimate_test_coverage(code_files),
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

    async def _develop_frontend(self, task: AgentTask) -> Dict[str, Any]:
        """Develop frontend components and interfaces"""
        requirements = task.requirements
        description = task.description
        framework = requirements.get("framework", "react")

        frontend_prompt = f"""
        Develop frontend functionality for:
        
        Task: {description}
        Requirements: {requirements}
        Framework: {framework}
        
        Create:
        1. React components with TypeScript
        2. State management (hooks/context)
        3. API integration
        4. Responsive design
        5. Error handling
        6. Loading states
        7. Unit tests
        
        Follow best practices:
        - Functional components with hooks
        - TypeScript for type safety
        - Proper component composition
        - Accessibility considerations
        - Performance optimization
        - Clean, maintainable code
        
        Integrate with SOPHIA Intel API endpoints.
        """

        ai_response = await self.communicate_with_ai(
            prompt=frontend_prompt,
            task_type="code_generation",
            context={"requirements": requirements, "framework": framework},
        )

        code_files = await self._parse_code_files(ai_response)

        return {
            "implementation_type": "frontend",
            "framework": framework,
            "code_files": code_files,
            "components": await self._identify_components(code_files),
            "dependencies": await self._extract_dependencies(code_files),
            "accessibility_score": await self._assess_accessibility(code_files),
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

    async def _design_database(self, task: AgentTask) -> Dict[str, Any]:
        """Design database schema and queries"""
        requirements = task.requirements
        data_model = requirements.get("data_model", {})
        database_type = requirements.get("database", "postgresql")

        database_prompt = f"""
        Design database schema for:
        
        Data Model: {data_model}
        Database: {database_type}
        Requirements: {requirements}
        
        Create:
        1. Table schemas with proper data types
        2. Indexes for performance
        3. Foreign key relationships
        4. Migration scripts
        5. Sample queries
        6. Data validation constraints
        
        Follow best practices:
        - Normalized design
        - Proper indexing strategy
        - Security considerations
        - Performance optimization
        - Scalability planning
        
        Include both DDL and sample DML statements.
        """

        ai_response = await self.communicate_with_ai(
            prompt=database_prompt,
            task_type="code_generation",
            context={"data_model": data_model, "database": database_type},
        )

        schema_files = await self._parse_sql_files(ai_response)

        return {
            "implementation_type": "database",
            "database_type": database_type,
            "schema_files": schema_files,
            "tables": await self._identify_tables(schema_files),
            "relationships": await self._identify_relationships(schema_files),
            "indexes": await self._identify_indexes(schema_files),
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

    async def _create_script(self, task: AgentTask) -> Dict[str, Any]:
        """Create automation scripts and utilities"""
        requirements = task.requirements
        description = task.description
        script_type = requirements.get("type", "python")

        script_prompt = f"""
        Create automation script for:
        
        Task: {description}
        Type: {script_type}
        Requirements: {requirements}
        
        Create:
        1. Main script with proper structure
        2. Error handling and logging
        3. Configuration management
        4. Command-line interface
        5. Documentation and usage examples
        6. Unit tests if applicable
        
        Best practices:
        - Robust error handling
        - Clear logging and output
        - Configurable parameters
        - Idempotent operations
        - Security considerations
        - Cross-platform compatibility
        
        Make it production-ready and maintainable.
        """

        ai_response = await self.communicate_with_ai(
            prompt=script_prompt,
            task_type="code_generation",
            context={"requirements": requirements, "script_type": script_type},
        )

        script_files = await self._parse_script_files(ai_response)

        return {
            "implementation_type": "script",
            "script_type": script_type,
            "script_files": script_files,
            "functionality": await self._analyze_script_functionality(script_files),
            "dependencies": await self._extract_dependencies(script_files),
            "complexity_score": await self._assess_complexity(script_files),
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

    async def _refactor_code(self, task: AgentTask) -> Dict[str, Any]:
        """Refactor and optimize existing code"""
        existing_code = task.context.get("existing_code", "")
        refactor_goals = task.requirements.get("goals", [])

        refactor_prompt = f"""
        Refactor the following code:
        
        Existing Code:
        {existing_code}
        
        Refactoring Goals:
        {refactor_goals}
        
        Improvements to make:
        1. Code structure and organization
        2. Performance optimization
        3. Readability and maintainability
        4. Error handling
        5. Type safety
        6. Documentation
        7. Test coverage
        
        Provide:
        1. Refactored code with improvements
        2. Explanation of changes made
        3. Performance impact analysis
        4. Migration guide if needed
        
        Maintain backward compatibility where possible.
        """

        ai_response = await self.communicate_with_ai(
            prompt=refactor_prompt,
            task_type="code_generation",
            context={"existing_code": existing_code, "goals": refactor_goals},
        )

        refactored_files = await self._parse_refactored_code(ai_response)

        return {
            "implementation_type": "refactor",
            "refactored_files": refactored_files,
            "improvements": await self._analyze_improvements(existing_code, refactored_files),
            "performance_impact": await self._assess_performance_impact(refactored_files),
            "breaking_changes": await self._identify_breaking_changes(refactored_files),
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

    # Helper methods for code processing

    async def _parse_code_files(self, ai_response: str) -> Dict[str, str]:
        """Parse code files from AI response"""
        code_files = {}

        # Look for code blocks in the response
        code_blocks = re.findall(r"```(\w+)?\n(.*?)\n```", ai_response, re.DOTALL)

        for i, (language, code) in enumerate(code_blocks):
            # Determine file extension based on language
            ext = self._get_file_extension(language)
            filename = f"generated_file_{i}{ext}"

            # Try to extract filename from comments
            filename_match = re.search(r"#\s*(?:File|Filename):\s*(.+)", code)
            if filename_match:
                filename = filename_match.group(1).strip()

            code_files[filename] = code.strip()

        return code_files

    async def _parse_sql_files(self, ai_response: str) -> Dict[str, str]:
        """Parse SQL files from AI response"""
        sql_files = {}

        # Look for SQL code blocks
        sql_blocks = re.findall(r"```sql\n(.*?)\n```", ai_response, re.DOTALL)

        for i, sql_code in enumerate(sql_blocks):
            filename = f"schema_{i}.sql"

            # Try to extract table name for filename
            table_match = re.search(r"CREATE TABLE\s+(\w+)", sql_code, re.IGNORECASE)
            if table_match:
                filename = f"{table_match.group(1).lower()}.sql"

            sql_files[filename] = sql_code.strip()

        return sql_files

    async def _parse_script_files(self, ai_response: str) -> Dict[str, str]:
        """Parse script files from AI response"""
        script_files = {}

        # Look for script code blocks
        script_blocks = re.findall(r"```(?:bash|python|sh)?\n(.*?)\n```", ai_response, re.DOTALL)

        for i, script_code in enumerate(script_blocks):
            # Determine script type
            if script_code.strip().startswith("#!/bin/bash"):
                filename = f"script_{i}.sh"
            elif script_code.strip().startswith("#!/usr/bin/env python"):
                filename = f"script_{i}.py"
            else:
                filename = f"script_{i}.py"  # Default to Python

            script_files[filename] = script_code.strip()

        return script_files

    async def _parse_refactored_code(self, ai_response: str) -> Dict[str, str]:
        """Parse refactored code from AI response"""
        return await self._parse_code_files(ai_response)

    async def _validate_code(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """Validate generated code"""
        validation_results = {"syntax_valid": True, "errors": [], "warnings": [], "quality_score": 0.0}

        for filename, code in code_files.items():
            if filename.endswith(".py"):
                # Validate Python syntax
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    validation_results["syntax_valid"] = False
                    validation_results["errors"].append(f"{filename}: {str(e)}")

        # Calculate quality score based on various factors
        validation_results["quality_score"] = await self._calculate_quality_score(code_files)

        return validation_results

    async def _calculate_quality_score(self, code_files: Dict[str, str]) -> float:
        """Calculate code quality score"""
        total_score = 0.0
        file_count = len(code_files)

        if file_count == 0:
            return 0.0

        for filename, code in code_files.items():
            file_score = 0.0

            # Check for docstrings
            if '"""' in code or "'''" in code:
                file_score += 0.2

            # Check for type hints
            if ": " in code and "->" in code:
                file_score += 0.2

            # Check for error handling
            if "try:" in code and "except" in code:
                file_score += 0.2

            # Check for logging
            if "logging" in code or "logger" in code:
                file_score += 0.2

            # Check for comments
            comment_lines = len([line for line in code.split("\n") if line.strip().startswith("#")])
            total_lines = len(code.split("\n"))
            if total_lines > 0 and comment_lines / total_lines > 0.1:
                file_score += 0.2

            total_score += min(file_score, 1.0)

        return total_score / file_count

    def _get_file_extension(self, language: str) -> str:
        """Get file extension based on language"""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "html": ".html",
            "css": ".css",
            "sql": ".sql",
            "bash": ".sh",
            "json": ".json",
            "yaml": ".yaml",
            "yml": ".yml",
        }
        return extensions.get(language.lower(), ".txt")

    # Template methods

    def _get_flask_api_template(self) -> str:
        """Get Flask API template"""
        return """
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
"""

    def _get_react_component_template(self) -> str:
        """Get React component template"""
        return """
import React, { useState, useEffect } from 'react';

interface ComponentProps {
  // Define props here
}

const Component: React.FC<ComponentProps> = (props) => {
  const [state, setState] = useState();

  useEffect(() => {
    // Component logic here
  }, []);

  return (
    <div>
      {/* Component JSX here */}
    </div>
  );
};

export default Component;
"""

    def _get_python_class_template(self) -> str:
        """Get Python class template"""
        return """
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ClassName:
    \"\"\"
    Class description here.
    \"\"\"
    
    def __init__(self, param: str):
        self.param = param
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def method(self, arg: Any) -> Any:
        \"\"\"Method description here.\"\"\"
        pass
"""

    def _get_sql_schema_template(self) -> str:
        """Get SQL schema template"""
        return """
-- Table creation script
CREATE TABLE table_name (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_table_name_created_at ON table_name(created_at);
"""

    # Analysis methods (simplified implementations)

    async def _identify_services(self, code_files: Dict[str, str]) -> List[str]:
        """Identify services in the code"""
        services = []
        for filename, code in code_files.items():
            if "class" in code and "Service" in code:
                # Extract service class names
                service_matches = re.findall(r"class (\w*Service\w*)", code)
                services.extend(service_matches)
        return services

    async def _extract_dependencies(self, code_files: Dict[str, str]) -> List[str]:
        """Extract dependencies from code"""
        dependencies = set()
        for filename, code in code_files.items():
            # Extract import statements
            import_matches = re.findall(r"(?:from|import)\s+(\w+)", code)
            dependencies.update(import_matches)
        return list(dependencies)

    async def _estimate_test_coverage(self, code_files: Dict[str, str]) -> float:
        """Estimate test coverage"""
        test_files = [f for f in code_files.keys() if "test" in f.lower()]
        total_files = len(code_files)
        return len(test_files) / total_files if total_files > 0 else 0.0

    async def _identify_components(self, code_files: Dict[str, str]) -> List[str]:
        """Identify React components"""
        components = []
        for filename, code in code_files.items():
            # Extract component names
            component_matches = re.findall(r"const (\w+): React\.FC", code)
            components.extend(component_matches)
        return components

    async def _assess_accessibility(self, code_files: Dict[str, str]) -> float:
        """Assess accessibility score"""
        # Simplified accessibility assessment
        return 0.8  # Placeholder

    async def _identify_tables(self, schema_files: Dict[str, str]) -> List[str]:
        """Identify database tables"""
        tables = []
        for filename, sql in schema_files.items():
            table_matches = re.findall(r"CREATE TABLE\s+(\w+)", sql, re.IGNORECASE)
            tables.extend(table_matches)
        return tables

    async def _identify_relationships(self, schema_files: Dict[str, str]) -> List[Dict[str, str]]:
        """Identify table relationships"""
        # Simplified relationship identification
        return []

    async def _identify_indexes(self, schema_files: Dict[str, str]) -> List[str]:
        """Identify database indexes"""
        indexes = []
        for filename, sql in schema_files.items():
            index_matches = re.findall(r"CREATE INDEX\s+(\w+)", sql, re.IGNORECASE)
            indexes.extend(index_matches)
        return indexes

    async def _analyze_script_functionality(self, script_files: Dict[str, str]) -> List[str]:
        """Analyze script functionality"""
        # Simplified functionality analysis
        return ["automation", "utility"]

    async def _assess_complexity(self, script_files: Dict[str, str]) -> float:
        """Assess code complexity"""
        # Simplified complexity assessment
        return 0.5  # Placeholder

    async def _analyze_improvements(self, original: str, refactored: Dict[str, str]) -> List[str]:
        """Analyze improvements made during refactoring"""
        # Simplified improvement analysis
        return ["improved readability", "better error handling", "added type hints"]

    async def _assess_performance_impact(self, refactored_files: Dict[str, str]) -> Dict[str, Any]:
        """Assess performance impact of refactoring"""
        # Simplified performance assessment
        return {"estimated_improvement": "10-20%", "areas": ["database queries", "async operations"]}

    async def _identify_breaking_changes(self, refactored_files: Dict[str, str]) -> List[str]:
        """Identify potential breaking changes"""
        # Simplified breaking change identification
        return []
