"""
Predictive Assistant
AI-powered assistant that predicts next actions, suggests tools, and provides proactive help
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import logging

from .sophia_client import SophiaMCPClient, MCPServerError
from .repo_intelligence import RepositoryIntelligence

logger = logging.getLogger(__name__)


class PredictiveAssistant:
    """
    AI-powered predictive assistant that learns from user behavior patterns
    to suggest next actions, predict tool needs, and provide contextual help.
    """

    def __init__(self, mcp_client: SophiaMCPClient):
        self.mcp_client = mcp_client
        self.repo_intelligence = RepositoryIntelligence(mcp_client)
        
        # Pattern learning and prediction
        self.action_patterns = {}
        self.tool_sequences = []
        self.context_predictions = {}
        
        # Prediction accuracy tracking
        self.prediction_stats = {
            "predictions_made": 0,
            "predictions_correct": 0,
            "last_updated": datetime.now()
        }

    async def predict_next_actions(self, 
                                 current_context: str,
                                 recent_actions: List[Dict[str, Any]],
                                 max_suggestions: int = 5) -> List[Dict[str, Any]]:
        """
        Predict the most likely next actions based on current context and history
        
        Args:
            current_context: Description of current situation
            recent_actions: List of recent actions taken
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of predicted actions with confidence scores
        """
        try:
            # Analyze recent action patterns
            action_sequence = self._extract_action_sequence(recent_actions)
            
            # Get similar historical sequences
            similar_sequences = await self._find_similar_sequences(
                action_sequence, current_context
            )
            
            # Generate predictions based on patterns
            predictions = self._generate_action_predictions(
                similar_sequences, current_context
            )
            
            # Enhance predictions with context-specific suggestions
            enhanced_predictions = await self._enhance_predictions_with_context(
                predictions, current_context
            )
            
            # Sort by confidence and return top suggestions
            enhanced_predictions.sort(
                key=lambda x: x.get("confidence", 0), reverse=True
            )
            
            # Update prediction stats
            self.prediction_stats["predictions_made"] += len(enhanced_predictions)
            
            return enhanced_predictions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Action prediction failed: {e}")
            return []

    async def suggest_relevant_files(self, 
                                   current_task: str,
                                   current_files: List[str] = None) -> List[Dict[str, Any]]:
        """
        Suggest files that might be relevant to the current task
        
        Args:
            current_task: Description of current task
            current_files: List of currently open/accessed files
            
        Returns:
            List of relevant file suggestions
        """
        try:
            # Get files related to current task
            task_related = await self.repo_intelligence.semantic_code_search(
                query=current_task,
                max_results=10
            )
            
            # Get files commonly accessed together with current files
            if current_files:
                co_occurrence_files = await self._find_co_occurring_files(current_files)
            else:
                co_occurrence_files = []
            
            # Get files from similar past sessions
            similar_session_files = await self._get_files_from_similar_sessions(current_task)
            
            # Combine and rank suggestions
            file_suggestions = self._rank_file_suggestions([
                ("task_related", task_related),
                ("co_occurrence", co_occurrence_files),
                ("similar_sessions", similar_session_files)
            ])
            
            return file_suggestions
            
        except Exception as e:
            logger.error(f"File suggestion failed: {e}")
            return []

    async def predict_code_completion(self, 
                                    file_path: str,
                                    current_code: str,
                                    cursor_position: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        Predict code completion suggestions based on context and patterns
        
        Args:
            file_path: Path to the current file
            current_code: Current code content
            cursor_position: Optional cursor position (line, column)
            
        Returns:
            Code completion suggestions
        """
        try:
            # Analyze current code context
            context_info = self._analyze_code_context(
                current_code, cursor_position, file_path
            )
            
            # Find similar code patterns
            similar_patterns = await self.repo_intelligence.find_similar_code(
                context_info["surrounding_code"],
                context_info["language"],
                similarity_threshold=0.6
            )
            
            # Generate completion suggestions
            suggestions = self._generate_code_completions(
                context_info, similar_patterns
            )
            
            return {
                "suggestions": suggestions,
                "context": context_info,
                "confidence": self._calculate_completion_confidence(suggestions)
            }
            
        except Exception as e:
            logger.error(f"Code completion prediction failed: {e}")
            return {"suggestions": [], "error": str(e)}

    async def get_proactive_help(self, 
                               current_situation: str,
                               user_skill_level: str = "intermediate") -> List[Dict[str, Any]]:
        """
        Provide proactive help suggestions based on current situation
        
        Args:
            current_situation: Description of what user is trying to do
            user_skill_level: User's skill level (beginner, intermediate, advanced)
            
        Returns:
            List of proactive help suggestions
        """
        try:
            help_suggestions = []
            
            # Detect common problems/patterns
            problems = await self._detect_potential_problems(current_situation)
            for problem in problems:
                help_suggestions.append({
                    "type": "problem_prevention",
                    "title": f"Potential issue: {problem['issue']}",
                    "description": problem["suggestion"],
                    "confidence": problem["confidence"],
                    "priority": "high" if problem["confidence"] > 0.8 else "medium"
                })
            
            # Suggest optimizations
            optimizations = await self._suggest_optimizations(current_situation)
            help_suggestions.extend(optimizations)
            
            # Provide learning opportunities
            if user_skill_level != "advanced":
                learning_opportunities = await self._identify_learning_opportunities(
                    current_situation, user_skill_level
                )
                help_suggestions.extend(learning_opportunities)
            
            # Sort by relevance and priority
            help_suggestions.sort(
                key=lambda x: (
                    {"high": 3, "medium": 2, "low": 1}.get(x.get("priority", "low"), 1),
                    x.get("confidence", 0)
                ),
                reverse=True
            )
            
            return help_suggestions
            
        except Exception as e:
            logger.error(f"Proactive help generation failed: {e}")
            return []

    async def learn_from_user_action(self, 
                                   predicted_action: str,
                                   actual_action: str,
                                   context: Dict[str, Any],
                                   was_helpful: bool = True):
        """
        Learn from user actions to improve predictions
        
        Args:
            predicted_action: What we predicted the user would do
            actual_action: What the user actually did
            context: Context information when prediction was made
            was_helpful: Whether our prediction was helpful
        """
        try:
            # Record prediction outcome
            learning_entry = {
                "predicted_action": predicted_action,
                "actual_action": actual_action,
                "context": context,
                "was_helpful": was_helpful,
                "timestamp": datetime.now().isoformat(),
                "prediction_accuracy": predicted_action == actual_action
            }
            
            # Store learning data
            await self.mcp_client.store_context(
                content=json.dumps(learning_entry, default=str),
                context_type="prediction_learning",
                metadata={
                    "prediction_correct": predicted_action == actual_action,
                    "was_helpful": was_helpful,
                    "learning_type": "user_action"
                }
            )
            
            # Update accuracy stats
            if predicted_action == actual_action:
                self.prediction_stats["predictions_correct"] += 1
            
            self.prediction_stats["last_updated"] = datetime.now()
            
            logger.info(f"Learning recorded: predicted='{predicted_action}', actual='{actual_action}', accurate={predicted_action == actual_action}")
            
        except Exception as e:
            logger.error(f"Learning from user action failed: {e}")

    async def get_context_aware_suggestions(self, 
                                          current_file: Optional[str] = None,
                                          selected_text: Optional[str] = None,
                                          recent_errors: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get context-aware suggestions based on current editor state
        
        Args:
            current_file: Currently active file
            selected_text: Currently selected text
            recent_errors: Recent error messages
            
        Returns:
            Context-specific suggestions
        """
        try:
            suggestions = []
            
            # File-specific suggestions
            if current_file:
                file_suggestions = await self._get_file_specific_suggestions(current_file)
                suggestions.extend(file_suggestions)
            
            # Selection-based suggestions
            if selected_text:
                selection_suggestions = await self._get_selection_suggestions(selected_text, current_file)
                suggestions.extend(selection_suggestions)
            
            # Error-based suggestions
            if recent_errors:
                error_suggestions = await self._get_error_suggestions(recent_errors, current_file)
                suggestions.extend(error_suggestions)
            
            # Remove duplicates and sort by relevance
            unique_suggestions = self._deduplicate_suggestions(suggestions)
            
            return unique_suggestions
            
        except Exception as e:
            logger.error(f"Context-aware suggestions failed: {e}")
            return []

    def get_prediction_accuracy(self) -> Dict[str, Any]:
        """Get current prediction accuracy statistics"""
        total_predictions = self.prediction_stats["predictions_made"]
        correct_predictions = self.prediction_stats["predictions_correct"]
        
        accuracy = (correct_predictions / total_predictions) if total_predictions > 0 else 0.0
        
        return {
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions,
            "accuracy_rate": accuracy,
            "last_updated": self.prediction_stats["last_updated"].isoformat()
        }

    # Private methods for internal logic

    def _extract_action_sequence(self, recent_actions: List[Dict[str, Any]]) -> List[str]:
        """Extract action sequence from recent actions"""
        sequence = []
        for action in recent_actions[-10:]:  # Look at last 10 actions
            action_type = action.get("type", action.get("tool_name", "unknown"))
            sequence.append(action_type)
        return sequence

    async def _find_similar_sequences(self, 
                                    action_sequence: List[str], 
                                    current_context: str) -> List[Dict[str, Any]]:
        """Find similar action sequences in history"""
        sequence_str = " ".join(action_sequence)
        query = f"sequence:{sequence_str} {current_context}"
        
        similar = await self.mcp_client.query_context(
            query=query,
            top_k=10,
            threshold=0.6,
            context_types=["tool_usage", "action_sequence"]
        )
        
        return similar

    def _generate_action_predictions(self, 
                                   similar_sequences: List[Dict[str, Any]],
                                   current_context: str) -> List[Dict[str, Any]]:
        """Generate action predictions based on similar sequences"""
        predictions = defaultdict(float)
        
        for sequence in similar_sequences:
            try:
                content = json.loads(sequence.get("content", "{}"))
                next_action = content.get("next_action")
                if next_action:
                    confidence = sequence.get("score", 0.5)
                    predictions[next_action] += confidence
            except json.JSONDecodeError:
                continue
        
        # Convert to list of predictions
        prediction_list = []
        for action, confidence in predictions.items():
            prediction_list.append({
                "action": action,
                "confidence": min(confidence, 1.0),
                "reasoning": f"Based on {len(similar_sequences)} similar sequences"
            })
        
        return prediction_list

    async def _enhance_predictions_with_context(self, 
                                              predictions: List[Dict[str, Any]],
                                              current_context: str) -> List[Dict[str, Any]]:
        """Enhance predictions with additional context-specific information"""
        enhanced = []
        
        for prediction in predictions:
            enhanced_prediction = dict(prediction)
            
            # Add context-specific enhancements
            if "file" in current_context.lower():
                enhanced_prediction["suggested_params"] = self._suggest_file_params(current_context)
            elif "search" in current_context.lower():
                enhanced_prediction["suggested_params"] = self._suggest_search_params(current_context)
            
            enhanced.append(enhanced_prediction)
        
        return enhanced

    async def _find_co_occurring_files(self, current_files: List[str]) -> List[Dict[str, Any]]:
        """Find files that commonly occur together with current files"""
        co_occurring = []
        
        for file in current_files:
            query = f"file:{file}"
            related = await self.mcp_client.query_context(
                query=query,
                top_k=5,
                threshold=0.5,
                context_types=["file_access", "code_change"]
            )
            
            for entry in related:
                other_file = entry.get("metadata", {}).get("file_path")
                if other_file and other_file not in current_files:
                    co_occurring.append({
                        "file_path": other_file,
                        "confidence": entry.get("score", 0.5),
                        "reason": f"Often accessed with {file}"
                    })
        
        return co_occurring

    async def _get_files_from_similar_sessions(self, current_task: str) -> List[Dict[str, Any]]:
        """Get files from sessions with similar tasks"""
        query = f"task:{current_task}"
        similar_sessions = await self.mcp_client.query_context(
            query=query,
            top_k=5,
            threshold=0.6,
            context_types=["session_summary", "file_access"]
        )
        
        files = []
        for session in similar_sessions:
            try:
                content = json.loads(session.get("content", "{}"))
                session_files = content.get("files_accessed", [])
                for file in session_files:
                    files.append({
                        "file_path": file,
                        "confidence": session.get("score", 0.5),
                        "reason": "Used in similar task"
                    })
            except json.JSONDecodeError:
                continue
        
        return files

    def _rank_file_suggestions(self, suggestion_groups: List[Tuple[str, List[Dict[str, Any]]]]) -> List[Dict[str, Any]]:
        """Rank and combine file suggestions from different sources"""
        all_suggestions = {}
        
        # Weight different sources
        source_weights = {
            "task_related": 1.0,
            "co_occurrence": 0.8,
            "similar_sessions": 0.6
        }
        
        for source, suggestions in suggestion_groups:
            weight = source_weights.get(source, 0.5)
            
            for suggestion in suggestions:
                file_path = suggestion.get("file_path")
                if not file_path:
                    continue
                
                if file_path not in all_suggestions:
                    all_suggestions[file_path] = {
                        "file_path": file_path,
                        "confidence": 0.0,
                        "reasons": []
                    }
                
                all_suggestions[file_path]["confidence"] += suggestion.get("confidence", 0.5) * weight
                all_suggestions[file_path]["reasons"].append(suggestion.get("reason", f"From {source}"))
        
        # Convert to list and sort by confidence
        ranked_suggestions = list(all_suggestions.values())
        ranked_suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return ranked_suggestions[:10]  # Return top 10

    def _analyze_code_context(self, 
                            code: str, 
                            cursor_position: Optional[Tuple[int, int]],
                            file_path: str) -> Dict[str, Any]:
        """Analyze the context around cursor position for code completion"""
        from pathlib import Path
        
        lines = code.split('\n')
        language = self.repo_intelligence.language_extensions.get(
            Path(file_path).suffix, "other"
        ) if file_path else "other"
        
        context = {
            "language": language,
            "file_path": file_path,
            "total_lines": len(lines),
            "surrounding_code": code
        }
        
        if cursor_position:
            line_num, col_num = cursor_position
            if 0 <= line_num < len(lines):
                current_line = lines[line_num]
                context.update({
                    "current_line": current_line,
                    "line_number": line_num,
                    "column_number": col_num,
                    "current_line_prefix": current_line[:col_num],
                    "current_line_suffix": current_line[col_num:],
                })
                
                # Get surrounding lines for context
                start_line = max(0, line_num - 3)
                end_line = min(len(lines), line_num + 4)
                context["surrounding_lines"] = lines[start_line:end_line]
        
        return context

    def _generate_code_completions(self, 
                                 context_info: Dict[str, Any],
                                 similar_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate code completion suggestions based on context and patterns"""
        suggestions = []
        
        # Extract completion patterns from similar code
        for pattern in similar_patterns:
            pattern_content = pattern.get("content", "")
            if pattern_content:
                # Simple pattern extraction - could be enhanced with AST analysis
                completion = self._extract_completion_from_pattern(
                    pattern_content, context_info
                )
                if completion:
                    suggestions.append({
                        "completion": completion,
                        "confidence": pattern.get("similarity_score", 0.5),
                        "source": "pattern_matching"
                    })
        
        return suggestions[:5]  # Return top 5 suggestions

    def _extract_completion_from_pattern(self, 
                                       pattern: str, 
                                       context: Dict[str, Any]) -> Optional[str]:
        """Extract completion suggestion from a code pattern"""
        # This is a simplified version - a real implementation would use
        # more sophisticated analysis
        current_line_prefix = context.get("current_line_prefix", "")
        
        pattern_lines = pattern.split('\n')
        for line in pattern_lines:
            if line.strip().startswith(current_line_prefix.strip()):
                # Found matching line, suggest the rest
                remaining = line[len(current_line_prefix):].strip()
                if remaining:
                    return remaining
        
        return None

    def _calculate_completion_confidence(self, suggestions: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in completion suggestions"""
        if not suggestions:
            return 0.0
        
        # Average confidence of all suggestions
        total_confidence = sum(s.get("confidence", 0) for s in suggestions)
        return total_confidence / len(suggestions)

    async def _detect_potential_problems(self, current_situation: str) -> List[Dict[str, Any]]:
        """Detect potential problems based on current situation"""
        problems = []
        
        # Common problem patterns
        problem_patterns = {
            "large file": {
                "issue": "Working with large file",
                "suggestion": "Consider breaking large files into smaller modules",
                "confidence": 0.8
            },
            "complex function": {
                "issue": "Complex function detected",
                "suggestion": "Consider refactoring into smaller functions",
                "confidence": 0.7
            },
            "no tests": {
                "issue": "No tests found",
                "suggestion": "Consider adding unit tests for better code quality",
                "confidence": 0.6
            }
        }
        
        situation_lower = current_situation.lower()
        for pattern, problem_info in problem_patterns.items():
            if pattern in situation_lower:
                problems.append(problem_info)
        
        return problems

    async def _suggest_optimizations(self, current_situation: str) -> List[Dict[str, Any]]:
        """Suggest optimizations based on current situation"""
        optimizations = []
        
        # Add optimization suggestions based on context
        if "performance" in current_situation.lower():
            optimizations.append({
                "type": "optimization",
                "title": "Performance optimization",
                "description": "Consider profiling code to identify bottlenecks",
                "confidence": 0.7,
                "priority": "medium"
            })
        
        return optimizations

    async def _identify_learning_opportunities(self, 
                                             current_situation: str,
                                             skill_level: str) -> List[Dict[str, Any]]:
        """Identify learning opportunities for the user"""
        opportunities = []
        
        if skill_level == "beginner":
            opportunities.append({
                "type": "learning",
                "title": "Learn about debugging",
                "description": "Try using debugging tools to understand code flow",
                "confidence": 0.6,
                "priority": "low"
            })
        
        return opportunities

    async def _get_file_specific_suggestions(self, file_path: str) -> List[Dict[str, Any]]:
        """Get suggestions specific to the current file"""
        suggestions = []
        
        # Get file context and suggest related actions
        file_context = await self.mcp_client.get_file_context(file_path)
        
        if file_context:
            suggestions.append({
                "type": "file_suggestion",
                "title": f"Recent changes to {file_path}",
                "description": f"Found {len(file_context)} recent changes",
                "confidence": 0.8,
                "priority": "medium"
            })
        
        return suggestions

    async def _get_selection_suggestions(self, 
                                       selected_text: str, 
                                       current_file: Optional[str]) -> List[Dict[str, Any]]:
        """Get suggestions based on selected text"""
        suggestions = []
        
        if len(selected_text.split()) > 10:
            suggestions.append({
                "type": "refactor_suggestion",
                "title": "Extract function",
                "description": "Consider extracting selected code into a separate function",
                "confidence": 0.7,
                "priority": "medium"
            })
        
        return suggestions

    async def _get_error_suggestions(self, 
                                   errors: List[str], 
                                   current_file: Optional[str]) -> List[Dict[str, Any]]:
        """Get suggestions based on recent errors"""
        suggestions = []
        
        for error in errors:
            if "import" in error.lower():
                suggestions.append({
                    "type": "error_fix",
                    "title": "Fix import error",
                    "description": "Check if the module is installed and the import path is correct",
                    "confidence": 0.9,
                    "priority": "high"
                })
        
        return suggestions

    def _deduplicate_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate suggestions and sort by relevance"""
        seen_titles = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            title = suggestion.get("title", "")
            if title not in seen_titles:
                seen_titles.add(title)
                unique_suggestions.append(suggestion)
        
        # Sort by priority and confidence
        priority_order = {"high": 3, "medium": 2, "low": 1}
        unique_suggestions.sort(
            key=lambda x: (
                priority_order.get(x.get("priority", "low"), 1),
                x.get("confidence", 0)
            ),
            reverse=True
        )
        
        return unique_suggestions

    def _suggest_file_params(self, context: str) -> Dict[str, Any]:
        """Suggest parameters for file-related operations"""
        return {"encoding": "utf-8", "mode": "r"}

    def _suggest_search_params(self, context: str) -> Dict[str, Any]:
        """Suggest parameters for search operations"""
        return {"case_sensitive": False, "regex": False}