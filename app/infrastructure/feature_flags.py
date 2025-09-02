"""
Feature Flags System for Gradual Rollout
Enables controlled feature deployment and A/B testing
"""

import hashlib
import json
from typing import Dict, Any, Optional, List, Set
from enum import Enum
from datetime import datetime, timedelta
import redis
import logging

logger = logging.getLogger(__name__)

# ==================== Feature Flag Types ====================

class RolloutStrategy(Enum):
    """Feature rollout strategies"""
    PERCENTAGE = "percentage"      # Random percentage of users
    ALLOWLIST = "allowlist"        # Specific users only
    DENYLIST = "denylist"         # All except specific users
    GRADUAL = "gradual"           # Time-based gradual rollout
    CANARY = "canary"             # Specific servers/regions
    RING = "ring"                 # Ring-based deployment

class FeatureStatus(Enum):
    """Feature flag status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    CONDITIONAL = "conditional"

# ==================== Feature Flag Configuration ====================

class FeatureFlag:
    """Individual feature flag configuration"""
    
    def __init__(
        self,
        name: str,
        status: FeatureStatus = FeatureStatus.DISABLED,
        strategy: RolloutStrategy = RolloutStrategy.PERCENTAGE,
        percentage: float = 0.0,
        allowlist: List[str] = None,
        denylist: List[str] = None,
        conditions: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        self.name = name
        self.status = status
        self.strategy = strategy
        self.percentage = percentage
        self.allowlist = allowlist or []
        self.denylist = denylist or []
        self.conditions = conditions or {}
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "status": self.status.value,
            "strategy": self.strategy.value,
            "percentage": self.percentage,
            "allowlist": self.allowlist,
            "denylist": self.denylist,
            "conditions": self.conditions,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureFlag':
        """Create from dictionary"""
        return cls(
            name=data["name"],
            status=FeatureStatus(data["status"]),
            strategy=RolloutStrategy(data["strategy"]),
            percentage=data.get("percentage", 0.0),
            allowlist=data.get("allowlist", []),
            denylist=data.get("denylist", []),
            conditions=data.get("conditions", {}),
            metadata=data.get("metadata", {})
        )

# ==================== Feature Flag Manager ====================

class FeatureFlagManager:
    """
    Manages feature flags for gradual rollout
    """
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.flags: Dict[str, FeatureFlag] = {}
        self.cache_ttl = 300  # 5 minutes cache
        self._initialize_default_flags()
    
    def _initialize_default_flags(self):
        """Initialize default feature flags"""
        self.flags = {
            # API Features
            "v2_api": FeatureFlag(
                name="v2_api",
                status=FeatureStatus.ENABLED,
                strategy=RolloutStrategy.PERCENTAGE,
                percentage=100.0,
                metadata={"description": "Version 2 API endpoints"}
            ),
            
            # WebSocket Features
            "websocket_streaming": FeatureFlag(
                name="websocket_streaming",
                status=FeatureStatus.CONDITIONAL,
                strategy=RolloutStrategy.GRADUAL,
                percentage=75.0,
                metadata={
                    "description": "WebSocket token streaming",
                    "rollout_schedule": {
                        "2025-01-01": 25,
                        "2025-01-07": 50,
                        "2025-01-14": 75,
                        "2025-01-21": 100
                    }
                }
            ),
            
            # Swarm Intelligence
            "swarm_intelligence": FeatureFlag(
                name="swarm_intelligence",
                status=FeatureStatus.CONDITIONAL,
                strategy=RolloutStrategy.ALLOWLIST,
                allowlist=["beta-users", "internal-testing"],
                percentage=50.0,
                metadata={"description": "Multi-agent swarm processing"}
            ),
            
            # Memory System
            "advanced_memory": FeatureFlag(
                name="advanced_memory",
                status=FeatureStatus.DISABLED,
                strategy=RolloutStrategy.RING,
                percentage=0.0,
                metadata={
                    "description": "Advanced memory with vector search",
                    "rings": ["internal", "alpha", "beta", "production"]
                }
            ),
            
            # Circuit Breakers
            "circuit_breakers": FeatureFlag(
                name="circuit_breakers",
                status=FeatureStatus.ENABLED,
                strategy=RolloutStrategy.PERCENTAGE,
                percentage=100.0,
                metadata={"description": "Circuit breaker protection"}
            ),
            
            # Graceful Degradation
            "graceful_degradation": FeatureFlag(
                name="graceful_degradation",
                status=FeatureStatus.ENABLED,
                strategy=RolloutStrategy.PERCENTAGE,
                percentage=100.0,
                metadata={"description": "Automatic service degradation"}
            ),
            
            # Metrics Collection
            "enhanced_metrics": FeatureFlag(
                name="enhanced_metrics",
                status=FeatureStatus.CONDITIONAL,
                strategy=RolloutStrategy.CANARY,
                percentage=20.0,
                conditions={"regions": ["us-east-1", "eu-west-1"]},
                metadata={"description": "Enhanced metrics collection"}
            ),
            
            # AI Optimization
            "ai_optimization": FeatureFlag(
                name="ai_optimization",
                status=FeatureStatus.CONDITIONAL,
                strategy=RolloutStrategy.PERCENTAGE,
                percentage=30.0,
                conditions={"user_tier": ["premium", "enterprise"]},
                metadata={"description": "AI-powered query optimization"}
            )
        }
    
    def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a feature flag is enabled for a user
        """
        # Get flag from cache or storage
        flag = self._get_flag(flag_name)
        if not flag:
            logger.warning(f"Feature flag not found: {flag_name}")
            return False
        
        # Check global status
        if flag.status == FeatureStatus.DISABLED:
            return False
        
        if flag.status == FeatureStatus.ENABLED:
            return True
        
        # Handle conditional flags
        return self._evaluate_conditions(flag, user_id, context)
    
    def _get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get flag from cache or storage"""
        # Try local cache first
        if flag_name in self.flags:
            return self.flags[flag_name]
        
        # Try Redis cache
        if self.redis_client:
            try:
                data = self.redis_client.get(f"feature_flag:{flag_name}")
                if data:
                    flag_data = json.loads(data)
                    return FeatureFlag.from_dict(flag_data)
            except Exception as e:
                logger.error(f"Error loading flag from Redis: {e}")
        
        return None
    
    def _evaluate_conditions(
        self,
        flag: FeatureFlag,
        user_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Evaluate conditional feature flag"""
        context = context or {}
        
        # Apply strategy
        if flag.strategy == RolloutStrategy.PERCENTAGE:
            return self._evaluate_percentage(flag, user_id)
        
        elif flag.strategy == RolloutStrategy.ALLOWLIST:
            return self._evaluate_allowlist(flag, user_id, context)
        
        elif flag.strategy == RolloutStrategy.DENYLIST:
            return self._evaluate_denylist(flag, user_id, context)
        
        elif flag.strategy == RolloutStrategy.GRADUAL:
            return self._evaluate_gradual(flag)
        
        elif flag.strategy == RolloutStrategy.CANARY:
            return self._evaluate_canary(flag, context)
        
        elif flag.strategy == RolloutStrategy.RING:
            return self._evaluate_ring(flag, context)
        
        return False
    
    def _evaluate_percentage(
        self,
        flag: FeatureFlag,
        user_id: Optional[str]
    ) -> bool:
        """Evaluate percentage-based rollout"""
        if not user_id:
            # Anonymous users get random assignment
            import random
            return random.random() * 100 < flag.percentage
        
        # Consistent hashing for logged-in users
        hash_input = f"{flag.name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        user_bucket = (hash_value % 100) + 1
        
        return user_bucket <= flag.percentage
    
    def _evaluate_allowlist(
        self,
        flag: FeatureFlag,
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate allowlist-based rollout"""
        if not user_id:
            return False
        
        # Check direct user allowlist
        if user_id in flag.allowlist:
            return True
        
        # Check group allowlist
        user_groups = context.get("groups", [])
        for group in user_groups:
            if group in flag.allowlist:
                return True
        
        # Fall back to percentage if configured
        if flag.percentage > 0:
            return self._evaluate_percentage(flag, user_id)
        
        return False
    
    def _evaluate_denylist(
        self,
        flag: FeatureFlag,
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate denylist-based rollout"""
        if user_id and user_id in flag.denylist:
            return False
        
        # Check group denylist
        user_groups = context.get("groups", [])
        for group in user_groups:
            if group in flag.denylist:
                return False
        
        # Not in denylist, use percentage
        return self._evaluate_percentage(flag, user_id)
    
    def _evaluate_gradual(self, flag: FeatureFlag) -> bool:
        """Evaluate time-based gradual rollout"""
        schedule = flag.metadata.get("rollout_schedule", {})
        current_date = datetime.utcnow().date()
        
        # Find applicable percentage based on date
        applicable_percentage = 0.0
        for date_str, percentage in sorted(schedule.items()):
            rollout_date = datetime.fromisoformat(date_str).date()
            if current_date >= rollout_date:
                applicable_percentage = percentage
        
        # Update flag percentage
        flag.percentage = applicable_percentage
        
        # Use random for gradual rollout
        import random
        return random.random() * 100 < applicable_percentage
    
    def _evaluate_canary(
        self,
        flag: FeatureFlag,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate canary deployment"""
        # Check if current region/server is in canary
        current_region = context.get("region")
        current_server = context.get("server_id")
        
        canary_regions = flag.conditions.get("regions", [])
        canary_servers = flag.conditions.get("servers", [])
        
        if current_region in canary_regions:
            return True
        
        if current_server in canary_servers:
            return True
        
        return False
    
    def _evaluate_ring(
        self,
        flag: FeatureFlag,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate ring-based deployment"""
        rings = flag.metadata.get("rings", [])
        user_ring = context.get("deployment_ring", "production")
        
        if not rings:
            return False
        
        # Find ring index
        try:
            ring_index = rings.index(user_ring)
            # Calculate percentage based on ring
            ring_percentage = ((ring_index + 1) / len(rings)) * 100
            return ring_percentage <= flag.percentage
        except ValueError:
            return False
    
    def update_flag(
        self,
        flag_name: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update feature flag configuration"""
        flag = self._get_flag(flag_name)
        if not flag:
            return False
        
        # Update fields
        if "status" in updates:
            flag.status = FeatureStatus(updates["status"])
        if "percentage" in updates:
            flag.percentage = updates["percentage"]
        if "allowlist" in updates:
            flag.allowlist = updates["allowlist"]
        if "denylist" in updates:
            flag.denylist = updates["denylist"]
        if "conditions" in updates:
            flag.conditions.update(updates["conditions"])
        
        flag.updated_at = datetime.utcnow()
        
        # Save to storage
        self._save_flag(flag)
        
        logger.info(f"Updated feature flag: {flag_name}")
        return True
    
    def _save_flag(self, flag: FeatureFlag):
        """Save flag to storage"""
        # Update local cache
        self.flags[flag.name] = flag
        
        # Save to Redis if available
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"feature_flag:{flag.name}",
                    self.cache_ttl,
                    json.dumps(flag.to_dict(), default=str)
                )
            except Exception as e:
                logger.error(f"Error saving flag to Redis: {e}")
    
    def get_all_flags(self, user_id: Optional[str] = None) -> Dict[str, bool]:
        """Get status of all flags for a user"""
        result = {}
        for flag_name in self.flags:
            result[flag_name] = self.is_enabled(flag_name, user_id)
        return result
    
    def get_flag_metadata(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """Get flag metadata for monitoring"""
        flag = self._get_flag(flag_name)
        if flag:
            return flag.to_dict()
        return None

# ==================== Feature Flag Decorator ====================

def feature_flag(flag_name: str, fallback=None):
    """
    Decorator to conditionally execute functions based on feature flags
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get manager instance (would be injected in real app)
            manager = FeatureFlagManager()
            
            # Extract user context from kwargs or args
            user_id = kwargs.get("user_id")
            context = kwargs.get("context", {})
            
            if manager.is_enabled(flag_name, user_id, context):
                return func(*args, **kwargs)
            elif fallback:
                return fallback(*args, **kwargs)
            else:
                raise FeatureNotEnabledError(f"Feature '{flag_name}' is not enabled")
        
        return wrapper
    return decorator

# ==================== Exceptions ====================

class FeatureNotEnabledError(Exception):
    """Raised when a feature is not enabled"""
    pass

# ==================== Export ====================

__all__ = [
    "FeatureFlag",
    "FeatureFlagManager",
    "RolloutStrategy",
    "FeatureStatus",
    "feature_flag",
    "FeatureNotEnabledError"
]