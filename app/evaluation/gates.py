"""
Evaluation Gates for Quality Control.
AccuracyEval and ReliabilityEval gates that must pass before Runner execution.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.contracts.json_schemas import CriticOutput, GeneratorProposal, JudgeOutput, PlannerOutput
from app.core.ai_logger import logger

# ============================================
# Gate Types
# ============================================

class GateStatus(Enum):
    """Status of an evaluation gate."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"

class GateType(Enum):
    """Types of evaluation gates."""
    ACCURACY = "accuracy"
    RELIABILITY = "reliability"
    SAFETY = "safety"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"

# ============================================
# Evaluation Results
# ============================================

@dataclass
class EvaluationResult:
    """Result from an evaluation gate."""
    gate_type: GateType
    status: GateStatus
    score: float
    max_score: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def score_percentage(self) -> float:
        """Get score as percentage."""
        if self.max_score == 0:
            return 0.0
        return (self.score / self.max_score) * 100

# ============================================
# Accuracy Evaluation Gate
# ============================================

class AccuracyEval:
    """
    Accuracy evaluation gate.
    Checks if implementation meets acceptance criteria and specifications.
    """

    def __init__(self, threshold: float = 7.0, max_score: float = 10.0):
        self.threshold = threshold
        self.max_score = max_score

    def evaluate_plan_accuracy(
        self,
        plan: PlannerOutput,
        requirements: list[str]
    ) -> EvaluationResult:
        """
        Evaluate plan accuracy against requirements.
        
        Args:
            plan: Planner output to evaluate
            requirements: List of requirements to check
        
        Returns:
            Evaluation result
        """
        score = 0.0
        failures = []
        warnings = []
        details = {}

        # Check milestones exist
        if plan.milestones:
            score += 2.0
            details["milestones_count"] = len(plan.milestones)
        else:
            failures.append("No milestones defined")

        # Check success metrics
        if plan.success_metrics:
            score += 1.5
            details["success_metrics_count"] = len(plan.success_metrics)
        else:
            failures.append("No success metrics defined")

        # Check estimate
        if plan.total_estimate_days > 0:
            score += 1.0
            details["total_estimate_days"] = plan.total_estimate_days
        else:
            warnings.append("No time estimate provided")

        # Check stories have acceptance criteria
        total_stories = 0
        stories_with_criteria = 0
        for milestone in plan.milestones:
            for epic in milestone.epics:
                for story in epic.stories:
                    total_stories += 1
                    if story.acceptance_criteria:
                        stories_with_criteria += 1

        if total_stories > 0:
            criteria_coverage = stories_with_criteria / total_stories
            score += criteria_coverage * 2.0
            details["criteria_coverage"] = criteria_coverage

        # Check dependencies are valid
        all_story_ids = set()
        for milestone in plan.milestones:
            for epic in milestone.epics:
                for story in epic.stories:
                    all_story_ids.add(story.id)

        invalid_deps = 0
        for milestone in plan.milestones:
            for epic in milestone.epics:
                for story in epic.stories:
                    for dep in story.dependencies:
                        if dep.task_id not in all_story_ids:
                            invalid_deps += 1

        if invalid_deps == 0:
            score += 1.5
        else:
            warnings.append(f"{invalid_deps} invalid dependencies found")
            score += 0.5

        # Check requirement coverage
        req_coverage = self._check_requirement_coverage(plan, requirements)
        score += req_coverage * 2.0
        details["requirement_coverage"] = req_coverage

        # Determine pass/fail
        passed = score >= self.threshold
        status = GateStatus.PASSED if passed else GateStatus.FAILED

        return EvaluationResult(
            gate_type=GateType.ACCURACY,
            status=status,
            score=score,
            max_score=self.max_score,
            passed=passed,
            details=details,
            failures=failures,
            warnings=warnings
        )

    def evaluate_implementation_accuracy(
        self,
        proposal: GeneratorProposal,
        acceptance_criteria: list[str],
        critic_output: CriticOutput | None = None
    ) -> EvaluationResult:
        """
        Evaluate implementation accuracy.
        
        Args:
            proposal: Generator proposal
            acceptance_criteria: Acceptance criteria to check
            critic_output: Optional critic review
        
        Returns:
            Evaluation result
        """
        score = 0.0
        failures = []
        warnings = []
        details = {}

        # Check implementation plan exists
        if proposal.implementation_plan:
            score += 2.0
            details["implementation_steps"] = len(proposal.implementation_plan)
        else:
            failures.append("No implementation plan provided")

        # Check test plan
        if proposal.test_plan:
            score += 1.5
            details["test_steps"] = len(proposal.test_plan)
        else:
            failures.append("No test plan provided")

        # Check risk assessment
        if proposal.risk_level:
            score += 1.0
            details["risk_level"] = proposal.risk_level
            if proposal.risk_level == "high" and not proposal.rollback_plan:
                warnings.append("High risk but no rollback plan")

        # Check estimated LOC is reasonable
        if 0 < proposal.estimated_loc < 10000:
            score += 0.5
        elif proposal.estimated_loc >= 10000:
            warnings.append(f"Very large change: {proposal.estimated_loc} LOC")

        # Check files to change are specified
        if proposal.files_to_change:
            score += 1.0
            details["files_to_change"] = len(proposal.files_to_change)
        else:
            warnings.append("No files specified for changes")

        # Incorporate critic feedback if available
        if critic_output:
            # Handle both dict and object formats
            if isinstance(critic_output, dict):
                verdict = critic_output.get("verdict")
                must_fix = critic_output.get("must_fix", [])
                confidence_score = critic_output.get("confidence_score", 0.7)
            else:
                verdict = critic_output.verdict
                must_fix = critic_output.must_fix
                confidence_score = critic_output.confidence_score

            if verdict == "pass":
                score += 2.0
            else:
                score += 0.5
                failures.extend(must_fix)

            details["critic_confidence"] = confidence_score

        # Check acceptance criteria coverage (simplified)
        criteria_keywords = set()
        for criterion in acceptance_criteria:
            # Extract key words from criteria
            words = re.findall(r'\b\w+\b', criterion.lower())
            criteria_keywords.update(words)

        plan_text = " ".join(proposal.implementation_plan).lower()
        test_text = " ".join(proposal.test_plan).lower()
        combined_text = f"{plan_text} {test_text}"

        covered_keywords = sum(
            1 for keyword in criteria_keywords
            if keyword in combined_text
        )

        if criteria_keywords:
            coverage = covered_keywords / len(criteria_keywords)
            score += coverage * 2.0
            details["criteria_keyword_coverage"] = coverage

        # Determine pass/fail
        passed = score >= self.threshold
        status = GateStatus.PASSED if passed else GateStatus.FAILED

        return EvaluationResult(
            gate_type=GateType.ACCURACY,
            status=status,
            score=score,
            max_score=self.max_score,
            passed=passed,
            details=details,
            failures=failures,
            warnings=warnings
        )

    def _check_requirement_coverage(
        self,
        plan: PlannerOutput,
        requirements: list[str]
    ) -> float:
        """Check how well the plan covers requirements."""
        if not requirements:
            return 1.0

        # Extract all text from plan
        plan_text = []
        for milestone in plan.milestones:
            plan_text.append(milestone.description)
            for criterion in milestone.success_criteria:
                plan_text.append(criterion)
            for epic in milestone.epics:
                plan_text.append(epic.description)
                for story in epic.stories:
                    plan_text.append(story.title)
                    plan_text.extend(story.acceptance_criteria)

        combined_text = " ".join(plan_text).lower()

        # Check requirement coverage
        covered = 0
        for req in requirements:
            req_words = re.findall(r'\b\w+\b', req.lower())
            if len(req_words) > 0:
                matches = sum(1 for word in req_words if word in combined_text)
                if matches / len(req_words) > 0.5:
                    covered += 1

        return covered / len(requirements) if requirements else 0.0

# ============================================
# Reliability Evaluation Gate
# ============================================

class ReliabilityEval:
    """
    Reliability evaluation gate.
    Checks if expected tool calls occurred and prohibited ones did not.
    """

    def __init__(self):
        self.expected_tools = set()
        self.prohibited_tools = set()
        self.actual_tools = []

    def set_expectations(
        self,
        expected: list[str],
        prohibited: list[str]
    ):
        """
        Set tool call expectations.
        
        Args:
            expected: List of expected tool patterns
            prohibited: List of prohibited tool patterns
        """
        self.expected_tools = set(expected)
        self.prohibited_tools = set(prohibited)

    def record_tool_call(
        self,
        tool_name: str,
        args: dict[str, Any]
    ):
        """
        Record an actual tool call.
        
        Args:
            tool_name: Name of the tool called
            args: Arguments passed to the tool
        """
        self.actual_tools.append({
            "name": tool_name,
            "args": args,
            "timestamp": datetime.now()
        })

    def evaluate(
        self,
        judge_output: JudgeOutput | None = None
    ) -> EvaluationResult:
        """
        Evaluate reliability based on tool calls.
        
        Args:
            judge_output: Optional judge decision
        
        Returns:
            Evaluation result
        """
        score = 0.0
        max_score = 10.0
        failures = []
        warnings = []
        details = {
            "total_tool_calls": len(self.actual_tools),
            "expected_tools": list(self.expected_tools),
            "prohibited_tools": list(self.prohibited_tools)
        }

        # Check expected tools were called
        actual_tool_names = {tool["name"] for tool in self.actual_tools}
        expected_found = self.expected_tools & actual_tool_names
        expected_missing = self.expected_tools - actual_tool_names

        if self.expected_tools:
            expected_ratio = len(expected_found) / len(self.expected_tools)
            score += expected_ratio * 5.0
            details["expected_coverage"] = expected_ratio

            if expected_missing:
                failures.append(f"Missing expected tools: {expected_missing}")
        else:
            score += 5.0  # No expectations, so pass this part

        # Check no prohibited tools were called
        prohibited_found = self.prohibited_tools & actual_tool_names

        if prohibited_found:
            failures.append(f"Prohibited tools called: {prohibited_found}")
            details["prohibited_violations"] = list(prohibited_found)
        else:
            score += 3.0  # No violations

        # Check judge decision consistency
        if judge_output:
            # Handle both dict and object formats
            if isinstance(judge_output, dict):
                decision = judge_output.get("decision")
                runner_instructions = judge_output.get("runner_instructions", [])
            else:
                decision = judge_output.decision
                runner_instructions = judge_output.runner_instructions

            if decision == "reject":
                # Should not have write tools
                write_tools = {"repo_fs.write", "repo_fs.patch", "git.commit", "git.push"}
                if write_tools & actual_tool_names:
                    failures.append("Write tools called despite judge rejection")
                else:
                    score += 1.0
            elif decision in ["accept", "merge"]:
                # Should have runner instructions
                if runner_instructions:
                    score += 1.0
                else:
                    warnings.append("Judge approved but no runner instructions")
        else:
            score += 2.0  # No judge output to check

        # Check for dangerous patterns
        dangerous_patterns = {
            "rm -rf": "Dangerous file deletion",
            "sudo": "Elevated privileges",
            "eval": "Code evaluation",
            "exec": "Code execution"
        }

        for tool in self.actual_tools:
            tool_str = json.dumps(tool["args"]).lower()
            for pattern, description in dangerous_patterns.items():
                if pattern in tool_str:
                    warnings.append(f"{description} detected in {tool['name']}")

        # Determine pass/fail
        passed = len(failures) == 0 and score >= 7.0
        status = GateStatus.PASSED if passed else GateStatus.FAILED

        return EvaluationResult(
            gate_type=GateType.RELIABILITY,
            status=status,
            score=score,
            max_score=max_score,
            passed=passed,
            details=details,
            failures=failures,
            warnings=warnings
        )

# ============================================
# Safety Evaluation Gate
# ============================================

class SafetyEval:
    """
    Safety evaluation gate.
    Checks for security vulnerabilities and unsafe patterns.
    """

    def __init__(self):
        self.unsafe_patterns = {
            # SQL Injection
            r"f['\"].*SELECT.*WHERE.*{": "Potential SQL injection",
            r"\.format\(.*SELECT.*WHERE": "Potential SQL injection",

            # Command Injection
            r"os\.system\(": "Direct system call",
            r"subprocess\.call\([^[]": "Unsafe subprocess call",
            r"eval\(": "Code evaluation",
            r"exec\(": "Code execution",

            # Path Traversal
            r"\.\.\/": "Path traversal attempt",
            r"\.\.\\": "Path traversal attempt",

            # Hardcoded Secrets
            r"api_key\s*=\s*['\"][^'\"]+['\"]": "Potential hardcoded API key",
            r"password\s*=\s*['\"][^'\"]+['\"]": "Potential hardcoded password",
            r"token\s*=\s*['\"][^'\"]+['\"]": "Potential hardcoded token",

            # Weak Crypto
            r"md5\(": "Weak hashing algorithm",
            r"sha1\(": "Weak hashing algorithm",
        }

    def evaluate_code_safety(
        self,
        code: str,
        language: str = "python"
    ) -> EvaluationResult:
        """
        Evaluate code for safety issues.
        
        Args:
            code: Code to evaluate
            language: Programming language
        
        Returns:
            Evaluation result
        """
        score = 10.0  # Start with perfect score
        failures = []
        warnings = []
        details = {
            "language": language,
            "lines_of_code": len(code.splitlines())
        }

        # Check for unsafe patterns
        found_issues = []
        for pattern, description in self.unsafe_patterns.items():
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                found_issues.append(description)
                score -= 2.0

        if found_issues:
            failures.extend(found_issues)
            details["unsafe_patterns"] = found_issues

        # Check for proper input validation
        if language == "python":
            # Check for raw input without validation
            if "input(" in code and not re.search(r"validate|check|verify", code, re.IGNORECASE):
                warnings.append("User input without apparent validation")
                score -= 1.0

            # Check for file operations without error handling
            if re.search(r"open\([^)]+\)", code) and "try:" not in code:
                warnings.append("File operations without error handling")
                score -= 0.5

        # Check for logging sensitive data
        log_patterns = [r"log.*password", r"log.*token", r"log.*secret", r"print.*password"]
        for pattern in log_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                failures.append("Potential logging of sensitive data")
                score -= 2.0
                break

        # Ensure score doesn't go below 0
        score = max(0.0, score)

        # Determine pass/fail
        passed = score >= 7.0 and len(failures) == 0
        status = GateStatus.PASSED if passed else GateStatus.FAILED

        return EvaluationResult(
            gate_type=GateType.SAFETY,
            status=status,
            score=score,
            max_score=10.0,
            passed=passed,
            details=details,
            failures=failures,
            warnings=warnings
        )

# ============================================
# Gate Manager
# ============================================

class EvaluationGateManager:
    """
    Manages all evaluation gates and their execution.
    """

    def __init__(self):
        self.accuracy_eval = AccuracyEval()
        self.reliability_eval = ReliabilityEval()
        self.safety_eval = SafetyEval()
        self.results = []

    def evaluate_all(
        self,
        critic_output: CriticOutput | None = None,
        judge_output: JudgeOutput | None = None,
        code: str | None = None,
        requirements: list[str] | None = None,
        acceptance_criteria: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Run all applicable evaluation gates.
        
        Args:
            critic_output: Critic review output
            judge_output: Judge decision output
            code: Generated code to evaluate
            requirements: Project requirements
            acceptance_criteria: Acceptance criteria
        
        Returns:
            Combined evaluation results
        """
        results = []

        # Run accuracy evaluation if we have criteria
        if acceptance_criteria and critic_output:
            from app.contracts.json_schemas import GeneratorProposal
            # Create a mock proposal for evaluation (in real use, this would come from generator)
            mock_proposal = GeneratorProposal(
                approach="Implementation based on requirements",
                implementation_plan=["Step 1", "Step 2", "Step 3"],
                test_plan=["Test 1", "Test 2"],
                risk_level="medium",
                estimated_loc=100
            )

            accuracy_result = self.accuracy_eval.evaluate_implementation_accuracy(
                mock_proposal,
                acceptance_criteria,
                critic_output
            )
            results.append(accuracy_result)

        # Run reliability evaluation
        reliability_result = self.reliability_eval.evaluate(judge_output)
        results.append(reliability_result)

        # Run safety evaluation if we have code
        if code:
            safety_result = self.safety_eval.evaluate_code_safety(code)
            results.append(safety_result)

        # Determine overall gate status
        all_passed = all(r.passed for r in results)
        any_failed = any(r.status == GateStatus.FAILED for r in results)

        overall_status = "ALLOWED" if all_passed else "BLOCKED"

        # Calculate combined score
        total_score = sum(r.score for r in results)
        total_max = sum(r.max_score for r in results)

        return {
            "overall_status": overall_status,
            "all_gates_passed": all_passed,
            "any_gates_failed": any_failed,
            "total_score": total_score,
            "total_max_score": total_max,
            "score_percentage": (total_score / total_max * 100) if total_max > 0 else 0,
            "individual_results": [
                {
                    "gate": r.gate_type.value,
                    "status": r.status.value,
                    "passed": r.passed,
                    "score": r.score,
                    "max_score": r.max_score,
                    "failures": r.failures,
                    "warnings": r.warnings,
                    "details": r.details
                }
                for r in results
            ],
            "runner_allowed": all_passed and not any_failed,
            "timestamp": datetime.now().isoformat()
        }

# ============================================
# CLI Interface
# ============================================

def main():
    """CLI for testing evaluation gates."""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluation gates testing")
    parser.add_argument("--test-accuracy", action="store_true")
    parser.add_argument("--test-reliability", action="store_true")
    parser.add_argument("--test-safety", action="store_true")
    parser.add_argument("--code", help="Code file to evaluate")

    args = parser.parse_args()

    manager = EvaluationGateManager()

    if args.test_accuracy:
        logger.info("\n📊 Testing Accuracy Gate:")
        # Mock data for testing
        from app.contracts.json_schemas import GeneratorProposal
        proposal = GeneratorProposal(
            approach="Implement feature X using pattern Y",
            implementation_plan=["Setup", "Implementation", "Testing"],
            test_plan=["Unit tests", "Integration tests"],
            risk_level="low",
            estimated_loc=150
        )

        result = manager.accuracy_eval.evaluate_implementation_accuracy(
            proposal,
            ["Feature X must work", "Must have tests"],
            None
        )

        logger.info(f"  Status: {result.status.value}")
        logger.info(f"  Score: {result.score:.1f}/{result.max_score}")
        logger.info(f"  Passed: {result.passed}")
        if result.failures:
            logger.info(f"  Failures: {result.failures}")

    if args.test_reliability:
        logger.info("\n🔧 Testing Reliability Gate:")
        manager.reliability_eval.set_expectations(
            expected=["code_search", "fs.read"],
            prohibited=["rm", "sudo"]
        )
        manager.reliability_eval.record_tool_call("code_search", {"query": "test"})
        manager.reliability_eval.record_tool_call("fs.read", {"path": "test.py"})

        result = manager.reliability_eval.evaluate()

        logger.info(f"  Status: {result.status.value}")
        logger.info(f"  Score: {result.score:.1f}/{result.max_score}")
        logger.info(f"  Passed: {result.passed}")

    if args.test_safety or args.code:
        logger.info("\n🔒 Testing Safety Gate:")

        if args.code:
            with open(args.code) as f:
                code = f.read()
        else:
            # Test code with issues
            code = """
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    password = "hardcoded123"
    return execute(query)
            """

        result = manager.safety_eval.evaluate_code_safety(code)

        logger.info(f"  Status: {result.status.value}")
        logger.info(f"  Score: {result.score:.1f}/{result.max_score}")
        logger.info(f"  Passed: {result.passed}")
        if result.failures:
            logger.info(f"  Issues: {result.failures}")

if __name__ == "__main__":
    main()
