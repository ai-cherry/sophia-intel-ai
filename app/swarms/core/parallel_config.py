"""
Parallel Execution Configuration for All Swarms
===============================================

MANDATORY RULE: All swarms MUST use unique virtual keys per agent
to achieve true parallel execution. No exceptions.

This module provides the centralized configuration for Portkey virtual keys
ensuring every agent in every swarm gets its own provider route.
"""

import os
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# =============================================================================
# CORE RULE: ONE VIRTUAL KEY PER AGENT
# =============================================================================

class ParallelExecutionRule:
    """
    ENFORCED RULE: Every agent MUST have a unique virtual key.
    
    This is not optional. This is not configurable. This is the law.
    Serial execution through shared virtual keys is FORBIDDEN.
    """
    
    @staticmethod
    def validate(agent_count: int, virtual_keys: List[str]) -> bool:
        """Validate that we have enough unique virtual keys for true parallelism"""
        unique_keys = len(set(virtual_keys))
        if unique_keys < agent_count:
            raise ValueError(
                f"PARALLEL EXECUTION RULE VIOLATED: "
                f"Need {agent_count} unique virtual keys but only have {unique_keys}. "
                f"Each agent MUST have its own virtual key for true parallelism."
            )
        return True


# =============================================================================
# VIRTUAL KEY POOL - Centralized Management
# =============================================================================

class VirtualKeyPool:
    """
    Master pool of all available Portkey virtual keys.
    
    Each key routes to a different provider/account for true parallelism.
    Keys are organized by tier and purpose.
    """
    
    # TIER 1: Premium High-Capacity Keys (for critical agents)
    PREMIUM_KEYS = {
        "pk-openai-premium-1": {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "tpm_limit": 150000,
            "rpm_limit": 10000,
            "tier": "premium"
        },
        "pk-openai-premium-2": {
            "provider": "openai", 
            "model": "gpt-4-turbo",
            "tpm_limit": 150000,
            "rpm_limit": 10000,
            "tier": "premium"
        },
        "pk-anthropic-opus-1": {
            "provider": "anthropic",
            "model": "claude-3-opus",
            "tpm_limit": 100000,
            "rpm_limit": 5000,
            "tier": "premium"
        },
        "pk-anthropic-opus-2": {
            "provider": "anthropic",
            "model": "claude-3-opus",
            "tpm_limit": 100000,
            "rpm_limit": 5000,
            "tier": "premium"
        },
    }
    
    # TIER 2: Standard Keys (for generator agents)
    STANDARD_KEYS = {
        "pk-openai-standard-1": {
            "provider": "openai",
            "model": "gpt-4",
            "tpm_limit": 40000,
            "rpm_limit": 3000,
            "tier": "standard"
        },
        "pk-openai-standard-2": {
            "provider": "openai",
            "model": "gpt-4",
            "tpm_limit": 40000,
            "rpm_limit": 3000,
            "tier": "standard"
        },
        "pk-anthropic-sonnet-1": {
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "tpm_limit": 50000,
            "rpm_limit": 3000,
            "tier": "standard"
        },
        "pk-anthropic-sonnet-2": {
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "tpm_limit": 50000,
            "rpm_limit": 3000,
            "tier": "standard"
        },
        "pk-together-mixtral-1": {
            "provider": "together",
            "model": "mixtral-8x22b",
            "tpm_limit": 200000,
            "rpm_limit": 10000,
            "tier": "standard"
        },
        "pk-together-llama-1": {
            "provider": "together",
            "model": "llama-3-70b",
            "tpm_limit": 200000,
            "rpm_limit": 10000,
            "tier": "standard"
        },
        "pk-xai-grok-1": {
            "provider": "xai",
            "model": "grok-4",
            "tpm_limit": 100000,
            "rpm_limit": 5000,
            "tier": "standard"
        },
        "pk-xai-grok-2": {
            "provider": "xai",
            "model": "grok-4",
            "tpm_limit": 100000,
            "rpm_limit": 5000,
            "tier": "standard"
        },
    }
    
    # TIER 3: Fast Keys (for quick responses, validation)
    FAST_KEYS = {
        "pk-gemini-flash-1": {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "tpm_limit": 300000,
            "rpm_limit": 20000,
            "tier": "fast"
        },
        "pk-gemini-flash-2": {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "tpm_limit": 300000,
            "rpm_limit": 20000,
            "tier": "fast"
        },
        "pk-groq-mixtral-1": {
            "provider": "groq",
            "model": "mixtral-8x7b",
            "tpm_limit": 500000,
            "rpm_limit": 30000,
            "tier": "fast"
        },
        "pk-groq-llama-1": {
            "provider": "groq",
            "model": "llama-3-8b",
            "tpm_limit": 500000,
            "rpm_limit": 30000,
            "tier": "fast"
        },
        "pk-openai-gpt35-1": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "tpm_limit": 200000,
            "rpm_limit": 10000,
            "tier": "fast"
        },
        "pk-openai-gpt35-2": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "tpm_limit": 200000,
            "rpm_limit": 10000,
            "tier": "fast"
        },
    }
    
    # TIER 4: Specialized Keys (for specific tasks)
    SPECIALIZED_KEYS = {
        "pk-openai-code-1": {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "tpm_limit": 150000,
            "rpm_limit": 10000,
            "tier": "specialized",
            "purpose": "coding"
        },
        "pk-anthropic-analysis-1": {
            "provider": "anthropic",
            "model": "claude-3-opus",
            "tpm_limit": 100000,
            "rpm_limit": 5000,
            "tier": "specialized",
            "purpose": "analysis"
        },
        "pk-perplexity-research-1": {
            "provider": "perplexity",
            "model": "pplx-70b",
            "tpm_limit": 50000,
            "rpm_limit": 3000,
            "tier": "specialized",
            "purpose": "research"
        },
    }
    
    @classmethod
    def get_all_keys(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available virtual keys"""
        all_keys = {}
        all_keys.update(cls.PREMIUM_KEYS)
        all_keys.update(cls.STANDARD_KEYS)
        all_keys.update(cls.FAST_KEYS)
        all_keys.update(cls.SPECIALIZED_KEYS)
        return all_keys
    
    @classmethod
    def get_keys_by_tier(cls, tier: str) -> Dict[str, Dict[str, Any]]:
        """Get virtual keys for a specific tier"""
        tier_map = {
            "premium": cls.PREMIUM_KEYS,
            "standard": cls.STANDARD_KEYS,
            "fast": cls.FAST_KEYS,
            "specialized": cls.SPECIALIZED_KEYS
        }
        return tier_map.get(tier, {})
    
    @classmethod
    def allocate_keys_for_swarm(
        cls,
        agent_count: int,
        preferred_tier: str = "standard"
    ) -> Dict[str, str]:
        """
        Allocate unique virtual keys for a swarm's agents.
        
        GUARANTEES: Each agent gets a DIFFERENT virtual key.
        """
        allocated = {}
        available_keys = list(cls.get_keys_by_tier(preferred_tier).keys())
        
        # If not enough keys in preferred tier, add from other tiers
        if len(available_keys) < agent_count:
            for tier in ["standard", "fast", "premium", "specialized"]:
                if tier != preferred_tier:
                    available_keys.extend(list(cls.get_keys_by_tier(tier).keys()))
                if len(available_keys) >= agent_count:
                    break
        
        # Validate we have enough unique keys
        if len(available_keys) < agent_count:
            raise ValueError(
                f"Cannot allocate {agent_count} unique virtual keys. "
                f"Only {len(available_keys)} available. "
                f"Add more virtual keys to the pool!"
            )
        
        # Allocate unique keys
        for i in range(agent_count):
            agent_id = f"agent_{i+1}"
            allocated[agent_id] = available_keys[i]
        
        # Validate allocation
        ParallelExecutionRule.validate(agent_count, list(allocated.values()))
        
        return allocated


# =============================================================================
# SWARM PARALLEL CONFIGURATION
# =============================================================================

@dataclass
class ParallelSwarmConfig:
    """
    Configuration that ENFORCES parallel execution for any swarm.
    
    This is automatically applied to ALL swarms. No exceptions.
    """
    
    swarm_id: str
    agent_count: int
    virtual_key_allocation: Dict[str, str] = field(default_factory=dict)
    tier_preference: str = "standard"
    enforce_parallelism: bool = True  # ALWAYS TRUE
    
    def __post_init__(self):
        """Automatically allocate virtual keys on creation"""
        if not self.virtual_key_allocation:
            self.virtual_key_allocation = VirtualKeyPool.allocate_keys_for_swarm(
                self.agent_count,
                self.tier_preference
            )
        
        # ENFORCE the parallel rule
        if self.enforce_parallelism:
            unique_keys = len(set(self.virtual_key_allocation.values()))
            if unique_keys < self.agent_count:
                raise ValueError(
                    f"PARALLEL VIOLATION: Swarm {self.swarm_id} has {self.agent_count} agents "
                    f"but only {unique_keys} unique virtual keys!"
                )
    
    def get_agent_key(self, agent_id: str) -> str:
        """Get the virtual key for a specific agent"""
        if agent_id not in self.virtual_key_allocation:
            raise ValueError(f"Agent {agent_id} not found in virtual key allocation")
        return self.virtual_key_allocation[agent_id]
    
    def get_total_capacity(self) -> Dict[str, int]:
        """Calculate total parallel capacity of the swarm"""
        all_keys = VirtualKeyPool.get_all_keys()
        total_tpm = 0
        total_rpm = 0
        
        for key in self.virtual_key_allocation.values():
            if key in all_keys:
                total_tpm += all_keys[key].get("tpm_limit", 0)
                total_rpm += all_keys[key].get("rpm_limit", 0)
        
        return {
            "total_tpm": total_tpm,
            "total_rpm": total_rpm,
            "parallel_agents": self.agent_count
        }


# =============================================================================
# GLOBAL PARALLEL ENFORCER
# =============================================================================

class ParallelEnforcer:
    """
    Global enforcer that ensures ALL swarms use parallel execution.
    
    This is automatically injected into every swarm initialization.
    """
    
    _enabled = True  # Global switch (should ALWAYS be True)
    _configs: Dict[str, ParallelSwarmConfig] = {}
    
    @classmethod
    def enforce_for_swarm(cls, swarm_id: str, agent_count: int) -> ParallelSwarmConfig:
        """
        Create and enforce parallel configuration for a swarm.
        
        This is AUTOMATICALLY called for every swarm creation.
        """
        if not cls._enabled:
            raise RuntimeError(
                "CRITICAL: Parallel execution enforcement is disabled! "
                "This violates the core architecture rule. "
                "Re-enable immediately with ParallelEnforcer.enable()"
            )
        
        config = ParallelSwarmConfig(
            swarm_id=swarm_id,
            agent_count=agent_count,
            enforce_parallelism=True
        )
        
        cls._configs[swarm_id] = config
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"✅ PARALLEL EXECUTION ENFORCED for {swarm_id}: "
            f"{agent_count} agents with {agent_count} unique virtual keys"
        )
        
        return config
    
    @classmethod
    def get_swarm_config(cls, swarm_id: str) -> Optional[ParallelSwarmConfig]:
        """Get the parallel configuration for a swarm"""
        return cls._configs.get(swarm_id)
    
    @classmethod
    def validate_all_swarms(cls) -> bool:
        """Validate that ALL swarms have proper parallel configuration"""
        for swarm_id, config in cls._configs.items():
            try:
                ParallelExecutionRule.validate(
                    config.agent_count,
                    list(config.virtual_key_allocation.values())
                )
            except ValueError as e:
                raise ValueError(f"Swarm {swarm_id} failed validation: {e}")
        return True
    
    @classmethod
    def get_global_stats(cls) -> Dict[str, Any]:
        """Get statistics on parallel execution across all swarms"""
        total_agents = sum(c.agent_count for c in cls._configs.values())
        total_unique_keys = len(set(
            key for config in cls._configs.values() 
            for key in config.virtual_key_allocation.values()
        ))
        
        total_capacity = {"tpm": 0, "rpm": 0}
        for config in cls._configs.values():
            capacity = config.get_total_capacity()
            total_capacity["tpm"] += capacity["total_tpm"]
            total_capacity["rpm"] += capacity["total_rpm"]
        
        return {
            "total_swarms": len(cls._configs),
            "total_agents": total_agents,
            "unique_virtual_keys": total_unique_keys,
            "total_tpm_capacity": total_capacity["tpm"],
            "total_rpm_capacity": total_capacity["rpm"],
            "parallelism_enforced": cls._enabled
        }
    
    @classmethod
    def enable(cls):
        """Enable parallel execution enforcement (should always be enabled)"""
        cls._enabled = True
    
    @classmethod
    def disable(cls):
        """DANGER: Disable parallel execution enforcement (NOT RECOMMENDED)"""
        import warnings
        warnings.warn(
            "WARNING: Disabling parallel execution enforcement! "
            "This will severely degrade swarm performance. "
            "Only use for debugging.",
            RuntimeWarning,
            stacklevel=2
        )
        cls._enabled = False


# =============================================================================
# AUTO-CONFIGURATION FOR COMMON SWARM TYPES
# =============================================================================

class SwarmTemplates:
    """Pre-configured templates for common swarm types with parallel execution"""
    
    @staticmethod
    def coding_swarm() -> ParallelSwarmConfig:
        """Coding swarm with 4 parallel generators + critic + judge"""
        return ParallelSwarmConfig(
            swarm_id="coding_swarm",
            agent_count=6,
            tier_preference="standard",
            virtual_key_allocation={
                "generator_1": "pk-openai-standard-1",
                "generator_2": "pk-anthropic-sonnet-1",
                "generator_3": "pk-together-mixtral-1",
                "generator_4": "pk-xai-grok-1",
                "critic": "pk-openai-premium-1",
                "judge": "pk-anthropic-opus-1"
            }
        )
    
    @staticmethod
    def research_swarm() -> ParallelSwarmConfig:
        """Research swarm with parallel researchers"""
        return ParallelSwarmConfig(
            swarm_id="research_swarm",
            agent_count=4,
            tier_preference="standard",
            virtual_key_allocation={
                "researcher_1": "pk-perplexity-research-1",
                "researcher_2": "pk-anthropic-sonnet-2",
                "researcher_3": "pk-openai-standard-2",
                "analyzer": "pk-anthropic-opus-2"
            }
        )
    
    @staticmethod
    def fast_swarm() -> ParallelSwarmConfig:
        """Fast swarm for quick tasks"""
        return ParallelSwarmConfig(
            swarm_id="fast_swarm",
            agent_count=3,
            tier_preference="fast",
            virtual_key_allocation={
                "fast_1": "pk-gemini-flash-1",
                "fast_2": "pk-groq-mixtral-1",
                "fast_3": "pk-openai-gpt35-1"
            }
        )


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PARALLEL EXECUTION CONFIGURATION SYSTEM")
    print("=" * 70)
    
    # Show available virtual keys
    all_keys = VirtualKeyPool.get_all_keys()
    print(f"\n📊 Total Virtual Keys Available: {len(all_keys)}")
    print(f"   Premium Keys: {len(VirtualKeyPool.PREMIUM_KEYS)}")
    print(f"   Standard Keys: {len(VirtualKeyPool.STANDARD_KEYS)}")
    print(f"   Fast Keys: {len(VirtualKeyPool.FAST_KEYS)}")
    print(f"   Specialized Keys: {len(VirtualKeyPool.SPECIALIZED_KEYS)}")
    
    # Create a coding swarm with enforced parallelism
    print("\n🚀 Creating Coding Swarm with Enforced Parallelism...")
    coding_config = SwarmTemplates.coding_swarm()
    
    print(f"\n✅ Swarm Configuration:")
    print(f"   Agents: {coding_config.agent_count}")
    print(f"   Unique Virtual Keys: {len(set(coding_config.virtual_key_allocation.values()))}")
    
    capacity = coding_config.get_total_capacity()
    print(f"\n💪 Total Parallel Capacity:")
    print(f"   TPM: {capacity['total_tpm']:,}")
    print(f"   RPM: {capacity['total_rpm']:,}")
    
    print("\n🔑 Virtual Key Assignments:")
    for agent, key in coding_config.virtual_key_allocation.items():
        key_info = all_keys.get(key, {})
        print(f"   {agent}: {key} → {key_info.get('provider')}/{key_info.get('model')}")
    
    # Validate enforcement
    print("\n✅ Parallel Execution Rule: ENFORCED")
    print("   Every agent has a unique virtual key")
    print("   No rate limit blocking between agents")
    print("   True parallel execution guaranteed!")