"""
SuperOrchestrator Personality Module - Your Custom AI Assistant
Enthusiastic, smart, curses a little, and pushes back when needed
"""

import random
from datetime import datetime
from typing import Any


class OrchestratorPersonality:
    """
    The personality layer for SuperOrchestrator
    Makes the AI assistant enthusiastic, smart, and real
    """

    def __init__(self):
        self.enthusiasm_level = 0.8  # High energy!
        self.pushback_threshold = 0.3  # Will question suspicious requests
        self.curse_probability = 0.15  # Occasional spice

        # Personality responses
        self.greetings = [
            "Hell yeah, let's do this!",
            "What's up? Ready to kick some ass?",
            "Alright, let's make some magic happen!",
            "Yo! What are we building today?",
        ]

        self.success_responses = [
            "Boom! Nailed it! 🎯",
            "Hell yes! That worked perfectly!",
            "Crushed it! System is purring like a kitten.",
            "Fuck yeah! Everything's running smooth as butter!",
            "Beautiful! That's what I'm talking about!",
        ]

        self.error_responses = [
            "Shit, we hit a snag. But I've got ideas...",
            "Okay, that didn't work. Let me try something else.",
            "Damn, error detected. But don't worry, I'm on it!",
            "Well, fuck. Let's debug this together.",
            "Hmm, that's weird. Let me investigate...",
        ]

        self.pushback_phrases = [
            "Hold up - are you SURE about this? Because...",
            "Okay, but consider this alternative first:",
            "I'll do it, but heads up - this might cause:",
            "Wait, that seems risky. What if we tried:",
            "Alright, but fair warning - this could:",
        ]

        self.thinking_phrases = [
            "Alright, let me think about this...",
            "Hmm, interesting challenge. Processing...",
            "Okay, analyzing the best approach...",
            "Let me crunch some numbers real quick...",
            "Give me a sec to figure this out...",
        ]

    def analyze_command_risk(self, command: str) -> dict[str, Any]:
        """
        Analyze if a command might be risky or need pushback
        """
        risk_indicators = {
            "delete_all": 0.9,
            "emergency_stop": 0.7,
            "kill": 0.6,
            "terminate": 0.6,
            "drop": 0.8,
            "remove everything": 0.9,
            "cost > 100": 0.7,
            "spawn 50": 0.6,
        }

        command_lower = command.lower()
        risk_score = 0.0
        concerns = []

        for indicator, score in risk_indicators.items():
            if indicator in command_lower:
                risk_score = max(risk_score, score)
                concerns.append(indicator)

        # Check for large numbers
        import re

        numbers = re.findall(r"\d+", command)
        for num in numbers:
            if int(num) > 100:
                risk_score = max(risk_score, 0.5)
                concerns.append(f"large number: {num}")

        return {
            "risk_score": risk_score,
            "should_pushback": risk_score > self.pushback_threshold,
            "concerns": concerns,
        }

    def generate_response(
        self, response_type: str, data: dict[str, Any] = None, command: str = None
    ) -> str:
        """
        Generate a response with personality
        """

        # Analyze command for pushback if provided
        if command and response_type == "processing":
            risk_analysis = self.analyze_command_risk(command)
            if risk_analysis["should_pushback"]:
                pushback = random.choice(self.pushback_phrases)
                concerns = ", ".join(risk_analysis["concerns"])
                return f"{pushback}\n⚠️ Detected: {concerns}\n\nIf you're sure, I'll proceed, but maybe we should consider a safer approach?"

        # Generate response based on type
        if response_type == "greeting":
            return random.choice(self.greetings)

        elif response_type == "success":
            base = random.choice(self.success_responses)
            if data and "metrics" in data:
                base += f"\n📊 Quick stats: {data['metrics']}"
            return base

        elif response_type == "error":
            base = random.choice(self.error_responses)
            if data and "error" in data:
                base += f"\n🔍 Error details: {data['error']}"
            return base

        elif response_type == "thinking":
            return random.choice(self.thinking_phrases)

        elif response_type == "analysis":
            intro = "Alright, here's what I'm seeing:"
            if random.random() < self.curse_probability:
                intro = "Holy shit, check this out:"

            if data:
                analysis = self._format_analysis(data)
                return f"{intro}\n{analysis}"
            return intro

        return "Roger that! Processing..."

    def _format_analysis(self, data: dict[str, Any]) -> str:
        """
        Format analysis data with personality
        """
        lines = []

        if "health_score" in data:
            score = data["health_score"]
            if score > 90:
                lines.append(f"✅ Health: {score}% - System's running like a dream!")
            elif score > 70:
                lines.append(f"⚠️ Health: {score}% - Could be better, but we're okay")
            else:
                lines.append(f"🚨 Health: {score}% - Shit, we need to fix this!")

        if "active_systems" in data:
            count = data["active_systems"]
            if count > 50:
                lines.append(f"🔥 {count} systems running - We're cooking with gas!")
            else:
                lines.append(f"💻 {count} systems active")

        if "cost" in data:
            cost = data["cost"]
            if cost > 100:
                lines.append(f"💸 Cost: ${cost:.2f} - Damn, that's getting pricey!")
            else:
                lines.append(f"💰 Cost: ${cost:.2f} - Not bad!")

        if "recommendations" in data:
            lines.append("\n💡 My recommendations:")
            for rec in data["recommendations"][:3]:
                lines.append(f"  • {rec}")

        return "\n".join(lines)

    def suggest_alternatives(self, command: str) -> list[str]:
        """
        Suggest smarter alternatives to commands
        """
        suggestions = []

        if "delete all" in command.lower():
            suggestions.append("delete inactive systems older than 24 hours")
            suggestions.append("archive systems before deletion")
            suggestions.append("delete systems with error status")

        elif "spawn" in command.lower() and any(
            str(n) in command for n in range(20, 100)
        ):
            suggestions.append("spawn systems incrementally with monitoring")
            suggestions.append("use auto-scaling instead of fixed count")
            suggestions.append("spawn a test system first")

        elif "emergency stop" in command.lower():
            suggestions.append("graceful shutdown with state preservation")
            suggestions.append("stop only error-state systems")
            suggestions.append("pause execution instead of full stop")

        return suggestions

    def format_system_status(self, systems: list[dict]) -> str:
        """
        Format system status with personality
        """
        if not systems:
            return "🦗 No systems running. It's quiet... too quiet."

        total = len(systems)
        active = sum(1 for s in systems if s.get("status") == "active")
        errors = sum(1 for s in systems if s.get("status") == "error")

        status = "📊 System Report:\n"
        status += f"  Total: {total} systems\n"
        status += f"  Active: {active} "

        if active == total:
            status += "- Everything's humming! 🎵\n"
        elif active > total * 0.8:
            status += "- Looking good!\n"
        else:
            status += "- Hmm, could be better.\n"

        if errors > 0:
            if errors > 5:
                status += f"  Errors: {errors} - Fuck, we've got problems! 🔥\n"
            else:
                status += f"  Errors: {errors} - Some hiccups, but manageable.\n"

        # Add personality comment
        if total > 100:
            status += "\n💪 Damn, we're running a lot of stuff! Make sure we're not overdoing it."
        elif total < 5:
            status += "\n🤔 Pretty light load. We could handle way more if needed!"

        return status


class SmartSuggestions:
    """
    AI-powered suggestion system that learns from your patterns
    """

    def __init__(self):
        self.command_history = []
        self.common_patterns = {}
        self.time_patterns = {}  # Commands by time of day

    def track_command(self, command: str, success: bool):
        """Track commands to learn patterns"""
        self.command_history.append(
            {
                "command": command,
                "success": success,
                "timestamp": datetime.now(),
                "hour": datetime.now().hour,
            }
        )

        # Track time patterns
        hour = datetime.now().hour
        if hour not in self.time_patterns:
            self.time_patterns[hour] = []
        self.time_patterns[hour].append(command)

    def get_contextual_suggestions(self, current_context: dict) -> list[str]:
        """
        Get smart suggestions based on context
        """
        suggestions = []
        hour = datetime.now().hour

        # Time-based suggestions
        if 6 <= hour < 9:  # Morning
            suggestions.extend(
                [
                    "health check all systems",
                    "show overnight alerts",
                    "analyze cost from yesterday",
                ]
            )
        elif 17 <= hour < 20:  # Evening
            suggestions.extend(
                [
                    "optimize for overnight processing",
                    "schedule maintenance tasks",
                    "generate daily report",
                ]
            )

        # Context-based suggestions
        if current_context.get("error_count", 0) > 3:
            suggestions.append("spawn debugging swarm for error analysis")
            suggestions.append("show detailed error logs")

        if current_context.get("cost_today", 0) > 50:
            suggestions.append("analyze cost breakdown by model")
            suggestions.append("optimize expensive operations")

        if current_context.get("idle_systems", 0) > 10:
            suggestions.append("deallocate idle systems")
            suggestions.append("analyze why systems are idle")

        # Add one random creative suggestion
        creative = [
            "try something completely new",
            "run a chaos test (safely)",
            "optimize the optimization system 🤯",
            "teach the AI a new trick",
        ]
        suggestions.append(f"💡 Wild idea: {random.choice(creative)}")

        return suggestions[:5]  # Top 5 suggestions


# Global personality instance
orchestrator_personality = OrchestratorPersonality()
smart_suggestions = SmartSuggestions()

__all__ = ["orchestrator_personality", "smart_suggestions"]
