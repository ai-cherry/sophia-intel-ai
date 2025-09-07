"""
Predictive Intelligence Engine for Operational Analytics
Provides predictive models for stuck account detection, team performance forecasting, and operational intelligence
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from app.core.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class PredictionConfidence(Enum):
    """Confidence levels for predictions"""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PredictionType(Enum):
    """Types of predictions"""

    STUCK_ACCOUNT_RISK = "stuck_account_risk"
    TEAM_PERFORMANCE_FORECAST = "team_performance_forecast"
    DEADLINE_RISK = "deadline_risk"
    RESOURCE_BOTTLENECK = "resource_bottleneck"
    VELOCITY_TREND = "velocity_trend"


@dataclass
class PredictionResult:
    """Result of a predictive analysis"""

    prediction_id: str
    prediction_type: PredictionType
    target_id: str  # Account, team, or project ID
    target_type: str  # "account", "team", "project"
    prediction_value: float  # 0.0 to 1.0 risk/probability score
    confidence: PredictionConfidence
    features_analyzed: dict[str, Any]
    contributing_factors: list[str]
    recommendations: list[str]
    generated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeSeriesPoint:
    """Point in time series data"""

    timestamp: datetime
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)


class MovingAverageCalculator:
    """Calculate moving averages for time series analysis"""

    def __init__(self, window_size: int = 7):
        self.window_size = window_size
        self.data_points: deque = deque(maxlen=window_size)

    def add_point(self, value: float, timestamp: datetime = None):
        """Add a data point"""
        self.data_points.append(
            TimeSeriesPoint(timestamp=timestamp or datetime.utcnow(), value=value)
        )

    def get_moving_average(self) -> Optional[float]:
        """Get current moving average"""
        if not self.data_points:
            return None
        return sum(point.value for point in self.data_points) / len(self.data_points)

    def get_trend(self) -> Optional[float]:
        """Get trend direction (-1 to 1, negative = declining, positive = improving)"""
        if len(self.data_points) < 2:
            return None

        points = list(self.data_points)
        recent_avg = sum(p.value for p in points[-3:]) / min(3, len(points))
        older_avg = sum(p.value for p in points[:3]) / min(3, len(points))

        if older_avg == 0:
            return 0

        return (recent_avg - older_avg) / older_avg


class StuckAccountPredictor:
    """Predicts likelihood of accounts becoming stuck"""

    def __init__(self):
        self.feature_weights = {
            "days_since_activity": 0.25,
            "overdue_ratio": 0.30,
            "velocity_decline": 0.20,
            "communication_gaps": 0.15,
            "dependency_blocks": 0.10,
        }

    async def predict_stuck_risk(self, account_data: dict[str, Any]) -> PredictionResult:
        """Predict risk of account becoming stuck"""

        # Extract and calculate features
        features = await self._extract_features(account_data)

        # Calculate weighted risk score
        risk_score = self._calculate_risk_score(features)

        # Determine confidence based on data completeness
        confidence = self._calculate_confidence(features)

        # Generate contributing factors and recommendations
        contributing_factors = self._identify_contributing_factors(features)
        recommendations = self._generate_recommendations(features, contributing_factors)

        return PredictionResult(
            prediction_id=f"stuck_risk_{account_data['id']}_{int(datetime.utcnow().timestamp())}",
            prediction_type=PredictionType.STUCK_ACCOUNT_RISK,
            target_id=account_data["id"],
            target_type=account_data.get("type", "account"),
            prediction_value=risk_score,
            confidence=confidence,
            features_analyzed=features,
            contributing_factors=contributing_factors,
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            metadata={"model_version": "1.0", "algorithm": "weighted_features"},
        )

    async def _extract_features(self, account_data: dict[str, Any]) -> dict[str, float]:
        """Extract predictive features from account data"""
        features = {}

        # Days since last activity (normalized 0-1)
        last_activity = account_data.get("last_activity")
        if last_activity:
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
            days_since = (datetime.utcnow() - last_activity).days
            features["days_since_activity"] = min(days_since / 14.0, 1.0)  # Cap at 14 days
        else:
            features["days_since_activity"] = 1.0  # No activity = max risk

        # Overdue task ratio
        total_tasks = account_data.get("total_tasks", 0)
        overdue_tasks = account_data.get("overdue_tasks", 0)
        features["overdue_ratio"] = overdue_tasks / max(total_tasks, 1)

        # Velocity decline (based on recent vs historical)
        current_velocity = account_data.get("current_velocity", 0)
        historical_velocity = account_data.get("historical_velocity", 0)
        if historical_velocity > 0:
            velocity_ratio = current_velocity / historical_velocity
            features["velocity_decline"] = max(
                0, 1 - velocity_ratio
            )  # 0 = no decline, 1 = complete stop
        else:
            features["velocity_decline"] = 0.5  # Unknown = medium risk

        # Communication gaps
        communication_score = account_data.get("communication_score", 0.5)
        features["communication_gaps"] = 1 - communication_score

        # Dependency blocks
        blocked_dependencies = account_data.get("blocked_dependencies", 0)
        total_dependencies = account_data.get("total_dependencies", 0)
        features["dependency_blocks"] = blocked_dependencies / max(total_dependencies, 1)

        return features

    def _calculate_risk_score(self, features: dict[str, float]) -> float:
        """Calculate weighted risk score"""
        total_score = 0
        total_weight = 0

        for feature_name, weight in self.feature_weights.items():
            if feature_name in features:
                total_score += features[feature_name] * weight
                total_weight += weight

        return total_score / max(total_weight, 0.001)  # Normalize

    def _calculate_confidence(self, features: dict[str, float]) -> PredictionConfidence:
        """Calculate prediction confidence based on data completeness"""
        available_features = len(features)
        total_features = len(self.feature_weights)
        completeness = available_features / total_features

        if completeness >= 0.9:
            return PredictionConfidence.VERY_HIGH
        elif completeness >= 0.7:
            return PredictionConfidence.HIGH
        elif completeness >= 0.5:
            return PredictionConfidence.MEDIUM
        elif completeness >= 0.3:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW

    def _identify_contributing_factors(self, features: dict[str, float]) -> list[str]:
        """Identify main contributing factors to stuck risk"""
        factors = []

        for feature_name, value in features.items():
            if value > 0.6:  # High risk threshold
                if feature_name == "days_since_activity":
                    factors.append("Extended period without activity")
                elif feature_name == "overdue_ratio":
                    factors.append("High percentage of overdue tasks")
                elif feature_name == "velocity_decline":
                    factors.append("Significant decline in work velocity")
                elif feature_name == "communication_gaps":
                    factors.append("Poor communication patterns")
                elif feature_name == "dependency_blocks":
                    factors.append("Multiple blocked dependencies")

        return factors

    def _generate_recommendations(
        self, features: dict[str, float], factors: list[str]
    ) -> list[str]:
        """Generate recommendations based on risk factors"""
        recommendations = []

        if features.get("days_since_activity", 0) > 0.5:
            recommendations.append("Schedule immediate check-in with account owner")

        if features.get("overdue_ratio", 0) > 0.4:
            recommendations.append("Review and reprioritize overdue tasks")
            recommendations.append("Consider deadline extensions or scope reduction")

        if features.get("velocity_decline", 0) > 0.5:
            recommendations.append("Investigate causes of velocity decline")
            recommendations.append("Consider additional resources or support")

        if features.get("communication_gaps", 0) > 0.5:
            recommendations.append("Establish regular communication cadence")

        if features.get("dependency_blocks", 0) > 0.4:
            recommendations.append("Escalate blocked dependencies immediately")

        # Add general recommendations if high risk
        risk_score = self._calculate_risk_score(features)
        if risk_score > 0.7:
            recommendations.extend(
                [
                    "Implement daily check-ins until risk decreases",
                    "Document blockers and escalation paths",
                    "Consider breaking work into smaller, independent tasks",
                ]
            )

        return list(set(recommendations))  # Remove duplicates


class TeamPerformancePredictor:
    """Predicts team performance trends"""

    def __init__(self):
        self.velocity_trackers: dict[str, MovingAverageCalculator] = defaultdict(
            lambda: MovingAverageCalculator(window_size=14)
        )

    async def predict_team_performance(self, team_data: dict[str, Any]) -> PredictionResult:
        """Predict team performance trend"""

        team_id = team_data["id"]

        # Update velocity tracker
        current_velocity = team_data.get("current_velocity", 0)
        self.velocity_trackers[team_id].add_point(current_velocity)

        # Get trend analysis
        trend = self.velocity_trackers[team_id].get_trend()
        moving_avg = self.velocity_trackers[team_id].get_moving_average()

        # Calculate performance prediction (0 = decline, 0.5 = stable, 1 = improving)
        if trend is None:
            performance_score = 0.5  # Unknown = neutral
        else:
            # Convert trend (-1 to 1) to performance score (0 to 1)
            performance_score = (trend + 1) / 2

        # Adjust based on absolute velocity
        target_velocity = team_data.get("target_velocity", moving_avg or current_velocity)
        if target_velocity > 0:
            velocity_ratio = current_velocity / target_velocity
            # Weight absolute performance with trend
            performance_score = (performance_score * 0.7) + (min(velocity_ratio, 1.0) * 0.3)

        # Analyze additional factors
        features = {
            "velocity_trend": trend or 0,
            "current_velocity": current_velocity,
            "moving_average": moving_avg or 0,
            "capacity_utilization": team_data.get("capacity_utilization", 0.8),
            "blocked_items": team_data.get("blocked_items", 0),
            "team_satisfaction": team_data.get("team_satisfaction", 0.7),
        }

        # Generate insights
        contributing_factors = self._analyze_performance_factors(features, performance_score)
        recommendations = self._generate_performance_recommendations(features, performance_score)

        return PredictionResult(
            prediction_id=f"team_perf_{team_id}_{int(datetime.utcnow().timestamp())}",
            prediction_type=PredictionType.TEAM_PERFORMANCE_FORECAST,
            target_id=team_id,
            target_type="team",
            prediction_value=performance_score,
            confidence=PredictionConfidence.HIGH if moving_avg else PredictionConfidence.LOW,
            features_analyzed=features,
            contributing_factors=contributing_factors,
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=12),
            metadata={
                "trend_direction": (
                    "improving"
                    if trend and trend > 0.1
                    else "declining" if trend and trend < -0.1 else "stable"
                )
            },
        )

    def _analyze_performance_factors(
        self, features: dict[str, float], performance_score: float
    ) -> list[str]:
        """Analyze factors affecting team performance"""
        factors = []

        if features["velocity_trend"] < -0.2:
            factors.append("Declining velocity trend over recent periods")

        if features["capacity_utilization"] > 0.9:
            factors.append("Team operating at high capacity utilization")
        elif features["capacity_utilization"] < 0.6:
            factors.append("Team has available capacity for additional work")

        if features["blocked_items"] > 2:
            factors.append("Multiple blocked items impacting progress")

        if features["team_satisfaction"] < 0.6:
            factors.append("Low team satisfaction scores")

        return factors

    def _generate_performance_recommendations(
        self, features: dict[str, float], performance_score: float
    ) -> list[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        if performance_score < 0.4:  # Poor performance
            recommendations.extend(
                [
                    "Investigate root causes of performance decline",
                    "Review sprint planning and estimation accuracy",
                    "Consider team retrospective to identify blockers",
                ]
            )

        if features["blocked_items"] > 1:
            recommendations.append("Prioritize unblocking dependencies")

        if features["capacity_utilization"] > 0.9:
            recommendations.extend(
                [
                    "Consider reducing sprint commitments",
                    "Evaluate options for additional resources",
                ]
            )
        elif features["capacity_utilization"] < 0.6:
            recommendations.append("Team has capacity for additional strategic work")

        if features["team_satisfaction"] < 0.7:
            recommendations.extend(
                [
                    "Address team satisfaction concerns",
                    "Consider process improvements or team building",
                ]
            )

        return recommendations


class PredictiveIntelligenceEngine:
    """Main engine for predictive operational intelligence"""

    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.stuck_account_predictor = StuckAccountPredictor()
        self.team_performance_predictor = TeamPerformancePredictor()

        # Prediction cache and history
        self.prediction_cache: dict[str, PredictionResult] = {}
        self.prediction_history: list[PredictionResult] = []

        # Model performance tracking
        self.model_metrics = {
            "predictions_generated": 0,
            "accuracy_scores": [],
            "false_positive_rate": 0.0,
            "false_negative_rate": 0.0,
        }

    async def analyze_operational_data(self, operational_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze operational data and generate predictions"""
        logger.info("🔮 Running predictive intelligence analysis...")

        start_time = datetime.utcnow()
        predictions = []

        try:
            # Analyze accounts for stuck risk
            accounts = operational_data.get("accounts", [])
            for account in accounts:
                prediction = await self.stuck_account_predictor.predict_stuck_risk(account)
                predictions.append(prediction)

                # Cache high-risk predictions
                if prediction.prediction_value > 0.6:
                    self.prediction_cache[prediction.prediction_id] = prediction

            # Analyze teams for performance forecasting
            teams = operational_data.get("teams", [])
            for team in teams:
                prediction = await self.team_performance_predictor.predict_team_performance(team)
                predictions.append(prediction)
                self.prediction_cache[prediction.prediction_id] = prediction

            # Store in history
            self.prediction_history.extend(predictions)

            # Generate summary insights
            summary = await self._generate_prediction_summary(predictions)

            # Broadcast real-time updates
            await self._broadcast_predictions(predictions, summary)

            # Update model metrics
            self.model_metrics["predictions_generated"] += len(predictions)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return {
                "status": "completed",
                "execution_time_seconds": execution_time,
                "total_predictions": len(predictions),
                "high_risk_predictions": len([p for p in predictions if p.prediction_value > 0.7]),
                "predictions_by_type": self._group_predictions_by_type(predictions),
                "summary_insights": summary,
                "model_performance": self.model_metrics,
                "timestamp": start_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Predictive analysis failed: {e}")
            return {"status": "failed", "error": str(e), "timestamp": start_time.isoformat()}

    async def _generate_prediction_summary(
        self, predictions: list[PredictionResult]
    ) -> dict[str, Any]:
        """Generate summary insights from predictions"""

        high_risk_accounts = [
            p
            for p in predictions
            if p.prediction_type == PredictionType.STUCK_ACCOUNT_RISK and p.prediction_value > 0.7
        ]
        declining_teams = [
            p
            for p in predictions
            if p.prediction_type == PredictionType.TEAM_PERFORMANCE_FORECAST
            and p.prediction_value < 0.4
        ]

        return {
            "critical_alerts": len(high_risk_accounts) + len(declining_teams),
            "accounts_at_risk": len(high_risk_accounts),
            "teams_declining": len(declining_teams),
            "top_risk_factors": self._extract_top_risk_factors(predictions),
            "recommended_actions": self._extract_top_recommendations(predictions),
            "confidence_distribution": self._analyze_confidence_distribution(predictions),
        }

    def _group_predictions_by_type(self, predictions: list[PredictionResult]) -> dict[str, int]:
        """Group predictions by type"""
        type_counts = defaultdict(int)
        for prediction in predictions:
            type_counts[prediction.prediction_type.value] += 1
        return dict(type_counts)

    def _extract_top_risk_factors(self, predictions: list[PredictionResult]) -> list[str]:
        """Extract most common risk factors"""
        factor_counts = defaultdict(int)
        for prediction in predictions:
            for factor in prediction.contributing_factors:
                factor_counts[factor] += 1

        return [
            factor
            for factor, count in sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

    def _extract_top_recommendations(self, predictions: list[PredictionResult]) -> list[str]:
        """Extract most common recommendations"""
        rec_counts = defaultdict(int)
        for prediction in predictions:
            for rec in prediction.recommendations:
                rec_counts[rec] += 1

        return [
            rec for rec, count in sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)[:7]
        ]

    def _analyze_confidence_distribution(
        self, predictions: list[PredictionResult]
    ) -> dict[str, int]:
        """Analyze distribution of prediction confidence levels"""
        confidence_counts = defaultdict(int)
        for prediction in predictions:
            confidence_counts[prediction.confidence.value] += 1
        return dict(confidence_counts)

    async def _broadcast_predictions(
        self, predictions: list[PredictionResult], summary: dict[str, Any]
    ):
        """Broadcast prediction results via WebSocket"""

        # Broadcast high-priority predictions immediately
        for prediction in predictions:
            if prediction.prediction_value > 0.8:  # Critical threshold
                await self.websocket_manager.broadcast_operational_intelligence(
                    "critical_prediction",
                    {
                        "prediction_id": prediction.prediction_id,
                        "prediction_type": prediction.prediction_type.value,
                        "target_id": prediction.target_id,
                        "risk_score": prediction.prediction_value,
                        "confidence": prediction.confidence.value,
                        "contributing_factors": prediction.contributing_factors,
                        "recommendations": prediction.recommendations[:3],  # Top 3
                        "expires_at": (
                            prediction.expires_at.isoformat() if prediction.expires_at else None
                        ),
                    },
                )

        # Broadcast summary
        await self.websocket_manager.broadcast_operational_intelligence(
            "prediction_analysis_complete",
            {
                "summary": summary,
                "total_predictions": len(predictions),
                "confidence": (
                    "high"
                    if summary["confidence_distribution"].get("high", 0) > len(predictions) * 0.6
                    else "medium"
                ),
            },
        )

    async def get_prediction_dashboard_data(self) -> dict[str, Any]:
        """Get comprehensive prediction dashboard data"""
        active_predictions = {
            pid: pred
            for pid, pred in self.prediction_cache.items()
            if pred.expires_at is None or pred.expires_at > datetime.utcnow()
        }

        return {
            "active_predictions": len(active_predictions),
            "critical_predictions": len(
                [p for p in active_predictions.values() if p.prediction_value > 0.8]
            ),
            "predictions_by_type": self._group_predictions_by_type(
                list(active_predictions.values())
            ),
            "recent_trends": await self._calculate_recent_trends(),
            "model_performance": self.model_metrics,
            "top_risk_factors": self._extract_top_risk_factors(list(active_predictions.values())),
            "recommended_actions": self._extract_top_recommendations(
                list(active_predictions.values())
            ),
            "last_analysis": (
                max(p.generated_at for p in active_predictions.values()).isoformat()
                if active_predictions
                else None
            ),
        }

    async def _calculate_recent_trends(self) -> dict[str, Any]:
        """Calculate recent prediction trends"""
        recent_predictions = [
            p
            for p in self.prediction_history
            if p.generated_at > datetime.utcnow() - timedelta(days=7)
        ]

        if not recent_predictions:
            return {"trend": "insufficient_data"}

        # Calculate average risk scores over time
        daily_averages = defaultdict(list)
        for prediction in recent_predictions:
            day_key = prediction.generated_at.date().isoformat()
            daily_averages[day_key].append(prediction.prediction_value)

        # Convert to average scores
        daily_scores = {day: sum(scores) / len(scores) for day, scores in daily_averages.items()}

        if len(daily_scores) < 2:
            return {
                "trend": "stable",
                "average_risk": list(daily_scores.values())[0] if daily_scores else 0,
            }

        # Calculate trend
        scores = list(daily_scores.values())
        recent_avg = sum(scores[-3:]) / min(3, len(scores))
        older_avg = sum(scores[:3]) / min(3, len(scores))

        trend_direction = (
            "improving"
            if recent_avg < older_avg
            else "worsening" if recent_avg > older_avg else "stable"
        )

        return {
            "trend": trend_direction,
            "average_risk": sum(scores) / len(scores),
            "recent_average": recent_avg,
            "change_magnitude": abs(recent_avg - older_avg),
        }

    async def cleanup_expired_predictions(self):
        """Clean up expired predictions from cache"""
        now = datetime.utcnow()
        expired_keys = [
            pid
            for pid, pred in self.prediction_cache.items()
            if pred.expires_at and pred.expires_at <= now
        ]

        for key in expired_keys:
            del self.prediction_cache[key]

        # Keep only last 1000 predictions in history
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-1000:]

        logger.info(f"Cleaned up {len(expired_keys)} expired predictions")

    def get_prediction_by_id(self, prediction_id: str) -> Optional[PredictionResult]:
        """Get specific prediction by ID"""
        return self.prediction_cache.get(prediction_id)
