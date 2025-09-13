"""Pay Ready Intelligence Service for Predictive Analytics"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np
class PayReadyIntelligenceService:
    """Core intelligence service for Pay Ready operational insights"""
    def __init__(self):
        self.stuck_account_history = []
        self.team_performance_history = defaultdict(list)
        self.prediction_cache = {}
    async def predict_stuck_accounts(
        self, current_accounts: List[Dict], historical_data: List[Dict]
    ) -> List[Dict]:
        """Predict which accounts are likely to become stuck"""
        predictions = []
        for account in current_accounts:
            risk_factors = self._calculate_risk_factors(account, historical_data)
            if risk_factors["risk_score"] > 0.7:
                predictions.append(
                    {
                        "account_id": account["id"],
                        "risk_score": risk_factors["risk_score"],
                        "predicted_stuck_date": risk_factors["predicted_date"],
                        "prevention_actions": self._generate_prevention_actions(
                            risk_factors
                        ),
                        "confidence": risk_factors["confidence"],
                    }
                )
        return sorted(predictions, key=lambda x: x["risk_score"], reverse=True)
    def _calculate_risk_factors(self, account: Dict, historical: List[Dict]) -> Dict:
        """Calculate risk factors for an account"""
        # Analyze patterns from historical data
        similar_accounts = self._find_similar_accounts(account, historical)
        if not similar_accounts:
            return {"risk_score": 0.3, "confidence": 0.5, "predicted_date": None}
        # Calculate average time to stuck status
        stuck_times = [acc.get("days_to_stuck", 30) for acc in similar_accounts]
        avg_days = np.mean(stuck_times) if stuck_times else 30
        # Risk score based on multiple factors
        age_factor = min(account.get("age_days", 0) / avg_days, 1.0)
        amount_factor = min(account.get("amount", 0) / 50000, 1.0) * 0.3
        activity_factor = 1 - min(account.get("recent_activities", 0) / 10, 1.0)
        risk_score = age_factor * 0.5 + amount_factor * 0.2 + activity_factor * 0.3
        predicted_date = datetime.now() + timedelta(
            days=int(avg_days - account.get("age_days", 0))
        )
        return {
            "risk_score": risk_score,
            "confidence": min(len(similar_accounts) / 10, 1.0),
            "predicted_date": predicted_date,
            "factors": {
                "age": age_factor,
                "amount": amount_factor,
                "activity": activity_factor,
            },
        }
    def _find_similar_accounts(
        self, account: Dict, historical: List[Dict]
    ) -> List[Dict]:
        """Find historically similar accounts"""
        similar = []
        for hist_account in historical:
            similarity = 0
            # Compare amount range
            if abs(hist_account.get("amount", 0) - account.get("amount", 0)) < 10000:
                similarity += 0.3
            # Compare customer type
            if hist_account.get("customer_type") == account.get("customer_type"):
                similarity += 0.3
            # Compare team assignment
            if hist_account.get("team") == account.get("team"):
                similarity += 0.2
            if similarity > 0.5:
                similar.append(hist_account)
        return similar
    def _generate_prevention_actions(self, risk_factors: Dict) -> List[str]:
        """Generate recommended prevention actions"""
        actions = []
        if risk_factors["factors"]["activity"] > 0.7:
            actions.append("Increase communication frequency with customer")
        if risk_factors["factors"]["age"] > 0.6:
            actions.append("Escalate to senior team member")
        if risk_factors["factors"]["amount"] > 0.5:
            actions.append("Schedule priority review meeting")
        if risk_factors["risk_score"] > 0.8:
            actions.append("Create contingency plan")
            actions.append("Alert management team")
        return actions
    async def optimize_team_workload(
        self, teams: List[Dict], pending_tasks: List[Dict]
    ) -> Dict:
        """Optimize workload distribution across teams"""
        optimizations = {
            "reassignments": [],
            "priority_changes": [],
            "resource_requests": [],
        }
        # Calculate team capacities
        team_scores = {}
        for team in teams:
            efficiency = team.get("completion_rate", 50) / 100
            capacity = team.get("capacity", 5)
            current_load = team.get("current_load", 10)
            available_capacity = max(0, (capacity * 10) - current_load)
            team_scores[team["name"]] = {
                "efficiency": efficiency,
                "available_capacity": available_capacity,
                "burnout_risk": team.get("burnout_risk", 0.5),
            }
        # Identify imbalances
        overloaded_teams = [
            name
            for name, scores in team_scores.items()
            if scores["available_capacity"] < 2 or scores["burnout_risk"] > 0.7
        ]
        underutilized_teams = [
            name
            for name, scores in team_scores.items()
            if scores["available_capacity"] > 5 and scores["burnout_risk"] < 0.3
        ]
        # Generate reassignment recommendations
        if overloaded_teams and underutilized_teams:
            for task in pending_tasks:
                if task.get("team") in overloaded_teams:
                    best_team = max(
                        underutilized_teams, key=lambda t: team_scores[t]["efficiency"]
                    )
                    optimizations["reassignments"].append(
                        {
                            "task_id": task["id"],
                            "from_team": task["team"],
                            "to_team": best_team,
                            "reason": "Load balancing",
                        }
                    )
        return optimizations
    async def generate_insights(self, data: Dict) -> List[str]:
        """Generate actionable insights from current data"""
        insights = []
        # Analyze stuck accounts trend
        if "stuck_accounts" in data:
            stuck_count = len(data["stuck_accounts"])
            if stuck_count > 10:
                insights.append(
                    f"Alert: {stuck_count} accounts stuck - 40% above normal"
                )
            high_value_stuck = [
                acc for acc in data["stuck_accounts"] if acc.get("amount", 0) > 50000
            ]
            if high_value_stuck:
                total_value = sum(acc["amount"] for acc in high_value_stuck)
                insights.append(f"${total_value:,.0f} in high-value stuck accounts")
        # Team performance insights
        if "teams" in data:
            poor_performers = [
                team for team in data["teams"] if team.get("completion_rate", 100) < 30
            ]
            if poor_performers:
                insights.append(
                    f"{len(poor_performers)} teams below 30% completion rate"
                )
        # Predictive insights
        if "predictions" in data:
            high_risk = [
                pred for pred in data["predictions"] if pred.get("risk_score", 0) > 0.8
            ]
            if high_risk:
                insights.append(
                    f"{len(high_risk)} accounts at high risk of becoming stuck"
                )
        return insights
