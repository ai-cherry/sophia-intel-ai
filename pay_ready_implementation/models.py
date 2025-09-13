"""Pay Ready Data Models for Operational Intelligence"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
class AccountStatus(Enum):
    ACTIVE = "active"
    STUCK = "stuck"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
@dataclass
class StuckAccount:
    """Model for tracking stuck accounts in Pay Ready system"""
    account_id: str
    customer_name: str
    amount: float
    days_stuck: int
    severity: SeverityLevel
    status: AccountStatus
    assigned_team: str
    blockers: List[str] = field(default_factory=list)
    resolution_notes: Optional[str] = None
    predicted_resolution_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    @property
    def risk_score(self) -> float:
        """Calculate risk score based on amount and days stuck"""
        base_score = (self.days_stuck / 30) * 0.5
        amount_factor = min(self.amount / 100000, 1.0) * 0.5
        severity_multiplier = {
            SeverityLevel.LOW: 0.25,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.HIGH: 0.75,
            SeverityLevel.CRITICAL: 1.0,
        }
        return (base_score + amount_factor) * severity_multiplier[self.severity]
@dataclass
class TeamPerformanceMetrics:
    """Track team performance for Pay Ready operations"""
    team_name: str
    completion_rate: float  # Percentage
    velocity: float  # Stories per sprint
    capacity: int  # Team members
    current_load: int  # Active tasks
    blocked_tasks: int
    average_resolution_time: float  # Days
    burnout_risk: float  # 0-1 scale
    last_updated: datetime = field(default_factory=datetime.now)
    @property
    def efficiency_score(self) -> float:
        """Calculate team efficiency score"""
        if self.capacity == 0:
            return 0.0
        load_factor = min(self.current_load / (self.capacity * 10), 1.0)
        completion_factor = self.completion_rate / 100
        burnout_penalty = 1 - (self.burnout_risk * 0.5)
        return (completion_factor * 0.5 + (1 - load_factor) * 0.3) * burnout_penalty
@dataclass
class PaymentReport:
    """Automated payment report to reduce manual views"""
    report_id: str
    report_type: str  # daily, weekly, monthly
    total_volume: float
    total_transactions: int
    success_rate: float
    failed_transactions: int
    stuck_accounts: List[StuckAccount]
    key_insights: List[str]
    generated_at: datetime = field(default_factory=datetime.now)
    viewed: bool = False
    def to_summary(self) -> Dict:
        """Generate executive summary"""
        return {
            "id": self.report_id,
            "type": self.report_type,
            "volume": f"${self.total_volume:,.2f}",
            "success_rate": f"{self.success_rate:.1f}%",
            "stuck_accounts": len(self.stuck_accounts),
            "key_insights": self.key_insights[:3],  # Top 3 insights
            "generated": self.generated_at.isoformat(),
        }
@dataclass
class CrossPlatformActivity:
    """Unified activity tracking across Asana, Linear, and Slack"""
    activity_id: str
    platform: str  # asana, linear, slack
    activity_type: str  # task_created, issue_updated, message_sent
    related_account: Optional[str] = None
    team: str = ""
    user: str = ""
    description: str = ""
    sentiment: Optional[float] = None  # -1 to 1 scale
    urgency: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    def is_bottleneck_indicator(self) -> bool:
        """Check if this activity indicates a bottleneck"""
        negative_keywords = ["blocked", "stuck", "waiting", "delayed", "issue"]
        return any(keyword in self.description.lower() for keyword in negative_keywords)
