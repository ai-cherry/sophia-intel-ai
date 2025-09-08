"""
Automated Secret Rotation System for Pulumi ESC
Handles automatic rotation of API keys, database passwords, and other secrets.
"""

import asyncio
import json
import logging
import secrets
import string
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

import aiohttp
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

from .secrets_manager import ESCSecretsManager, SecretScope, SecretStatus

logger = logging.getLogger(__name__)


class RotationStatus(str, Enum):
    """Secret rotation status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"


class RotationType(str, Enum):
    """Types of secret rotation"""

    PASSWORD = "password"
    API_KEY = "api_key"
    TOKEN = "token"
    CERTIFICATE = "certificate"
    DATABASE_PASSWORD = "database_password"
    ENCRYPTION_KEY = "encryption_key"


@dataclass
class RotationPolicy:
    """Policy for secret rotation"""

    secret_key: str
    rotation_type: RotationType
    interval_days: int
    max_age_days: int
    grace_period_hours: int = 24
    auto_rotate: bool = True
    notify_before_hours: int = 48
    rollback_timeout_minutes: int = 30
    validation_required: bool = True
    environments: List[str] = field(default_factory=lambda: ["dev", "staging", "production"])


class RotationEvent(BaseModel):
    """Event model for rotation tracking"""

    secret_key: str
    rotation_id: str
    status: RotationStatus
    rotation_type: RotationType
    environment: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    old_secret_hint: Optional[str] = None  # Last 4 chars for identification
    new_secret_hint: Optional[str] = None
    rollback_available: bool = True


class SecretGenerator(ABC):
    """Abstract base class for secret generators"""

    @abstractmethod
    async def generate(self, old_secret: str, policy: RotationPolicy) -> str:
        """Generate new secret based on old secret and policy"""
        pass

    @abstractmethod
    async def validate(self, secret: str, policy: RotationPolicy) -> bool:
        """Validate the generated secret"""
        pass


class PasswordGenerator(SecretGenerator):
    """Generator for passwords and generic secrets"""

    def __init__(self, length: int = 32, use_symbols: bool = True):
        self.length = length
        self.use_symbols = use_symbols

    async def generate(self, old_secret: str, policy: RotationPolicy) -> str:
        """Generate a new password"""
        chars = string.ascii_letters + string.digits
        if self.use_symbols:
            chars += "!@#$%^&*"

        return "".join(secrets.choice(chars) for _ in range(self.length))

    async def validate(self, secret: str, policy: RotationPolicy) -> bool:
        """Validate password strength"""
        if len(secret) < 16:
            return False

        has_upper = any(c.isupper() for c in secret)
        has_lower = any(c.islower() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        has_symbol = any(c in "!@#$%^&*" for c in secret)

        return has_upper and has_lower and has_digit and (has_symbol or not self.use_symbols)


class APIKeyGenerator(SecretGenerator):
    """Generator for API keys"""

    def __init__(self, prefix: str = "", length: int = 48):
        self.prefix = prefix
        self.length = length

    async def generate(self, old_secret: str, policy: RotationPolicy) -> str:
        """Generate a new API key"""
        # Extract prefix from old key if present
        if old_secret and "-" in old_secret:
            prefix_part = old_secret.split("-")[0]
            if len(prefix_part) < 10:  # Reasonable prefix length
                self.prefix = prefix_part

        # Generate random key part
        chars = string.ascii_letters + string.digits
        key_part = "".join(secrets.choice(chars) for _ in range(self.length))

        if self.prefix:
            return f"{self.prefix}-{key_part}"
        else:
            return key_part

    async def validate(self, secret: str, policy: RotationPolicy) -> bool:
        """Validate API key format"""
        return len(secret) >= 32 and secret.replace("-", "").isalnum()


class TokenGenerator(SecretGenerator):
    """Generator for JWT tokens and similar"""

    def __init__(self, length: int = 64):
        self.length = length

    async def generate(self, old_secret: str, policy: RotationPolicy) -> str:
        """Generate a new token"""
        chars = string.ascii_letters + string.digits + "-_"
        return "".join(secrets.choice(chars) for _ in range(self.length))

    async def validate(self, secret: str, policy: RotationPolicy) -> bool:
        """Validate token format"""
        return len(secret) >= 32 and all(
            c in string.ascii_letters + string.digits + "-_" for c in secret
        )


class SecretValidator:
    """Validates secrets against external services"""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def validate_openai_key(self, api_key: str) -> bool:
        """Validate OpenAI API key"""
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with self._session.get(
                "https://api.openai.com/v1/models", headers=headers
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"OpenAI key validation error: {e}")
            return False

    async def validate_anthropic_key(self, api_key: str) -> bool:
        """Validate Anthropic API key"""
        try:
            headers = {"x-api-key": api_key, "Content-Type": "application/json"}
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "test"}],
            }
            async with self._session.post(
                "https://api.anthropic.com/v1/messages", headers=headers, json=payload
            ) as response:
                return response.status in [
                    200,
                    400,
                ]  # 400 is OK, means key is valid but request format issue
        except Exception as e:
            logger.error(f"Anthropic key validation error: {e}")
            return False

    async def validate_redis_connection(self, redis_url: str, password: str) -> bool:
        """Validate Redis connection"""
        try:
            import redis.asyncio as redis

            client = redis.from_url(redis_url, password=password, socket_timeout=5)
            await client.ping()
            await client.close()
            return True
        except Exception as e:
            logger.error(f"Redis validation error: {e}")
            return False


class SecretRotationOrchestrator:
    """Orchestrates automatic secret rotation across environments"""

    def __init__(
        self,
        secrets_manager: ESCSecretsManager,
        rotation_policies: List[RotationPolicy],
        enable_notifications: bool = True,
        dry_run: bool = False,
    ):
        self.secrets_manager = secrets_manager
        self.rotation_policies = {policy.secret_key: policy for policy in rotation_policies}
        self.enable_notifications = enable_notifications
        self.dry_run = dry_run

        # Generators
        self.generators = {
            RotationType.PASSWORD: PasswordGenerator(),
            RotationType.API_KEY: APIKeyGenerator(),
            RotationType.TOKEN: TokenGenerator(),
            RotationType.DATABASE_PASSWORD: PasswordGenerator(length=24, use_symbols=True),
            RotationType.ENCRYPTION_KEY: TokenGenerator(length=32),
        }

        # Validator
        self.validator = SecretValidator()

        # Tracking
        self.rotation_events: List[RotationEvent] = []
        self.active_rotations: Set[str] = set()
        self.rollback_queue: Dict[str, RotationEvent] = {}

        # Callbacks
        self.notification_callbacks: List[Callable[[RotationEvent], None]] = []

        # Background task
        self._rotation_task: Optional[asyncio.Task] = None
        self._stop_rotation = False

    def add_notification_callback(self, callback: Callable[[RotationEvent], None]):
        """Add notification callback"""
        self.notification_callbacks.append(callback)

    async def start_rotation_scheduler(self, check_interval: int = 3600):
        """Start background rotation scheduler"""
        if self._rotation_task:
            logger.warning("Rotation scheduler already running")
            return

        self._rotation_task = asyncio.create_task(self._rotation_scheduler_loop(check_interval))
        logger.info("Secret rotation scheduler started")

    async def stop_rotation_scheduler(self):
        """Stop background rotation scheduler"""
        if self._rotation_task:
            self._stop_rotation = True
            self._rotation_task.cancel()
            try:
                await self._rotation_task
            except asyncio.CancelledError:
                pass
            self._rotation_task = None
        logger.info("Secret rotation scheduler stopped")

    async def _rotation_scheduler_loop(self, check_interval: int):
        """Background loop for checking and rotating secrets"""
        while not self._stop_rotation:
            try:
                await self._check_and_rotate_secrets()
                await asyncio.sleep(check_interval)

            except asyncio.CancelledError:
                logger.info("Rotation scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in rotation scheduler: {e}")
                await asyncio.sleep(60)  # Short sleep before retry

    async def _check_and_rotate_secrets(self):
        """Check all policies and rotate secrets if needed"""
        logger.info("Checking secrets for rotation...")

        for policy in self.rotation_policies.values():
            if not policy.auto_rotate:
                continue

            for environment in policy.environments:
                try:
                    needs_rotation = await self._check_rotation_needed(policy, environment)
                    if needs_rotation:
                        logger.info(f"Scheduling rotation for {policy.secret_key} in {environment}")
                        await self.rotate_secret(policy.secret_key, environment)

                except Exception as e:
                    logger.error(f"Error checking rotation for {policy.secret_key}: {e}")

    async def _check_rotation_needed(self, policy: RotationPolicy, environment: str) -> bool:
        """Check if secret rotation is needed"""
        try:
            # Get secret metadata from cache
            secret_metadata = self.secrets_manager.cache.metadata.get(policy.secret_key)

            if not secret_metadata:
                logger.warning(f"No metadata found for {policy.secret_key}, scheduling rotation")
                return True

            # Check age
            if secret_metadata.last_rotated:
                age_days = (datetime.utcnow() - secret_metadata.last_rotated).days
                return age_days >= policy.interval_days
            else:
                # No rotation history, check creation date
                age_days = (datetime.utcnow() - secret_metadata.created_at).days
                return age_days >= policy.interval_days

        except Exception as e:
            logger.error(f"Error checking rotation need: {e}")
            return False

    async def rotate_secret(self, secret_key: str, environment: str, force: bool = False) -> bool:
        """Rotate a specific secret"""
        if secret_key not in self.rotation_policies:
            logger.error(f"No rotation policy found for {secret_key}")
            return False

        policy = self.rotation_policies[secret_key]
        rotation_id = f"{secret_key}_{environment}_{int(datetime.utcnow().timestamp())}"

        if rotation_id in self.active_rotations:
            logger.warning(f"Rotation already in progress for {secret_key}")
            return False

        event = RotationEvent(
            secret_key=secret_key,
            rotation_id=rotation_id,
            status=RotationStatus.IN_PROGRESS,
            rotation_type=policy.rotation_type,
            environment=environment,
            started_at=datetime.utcnow(),
        )

        try:
            self.active_rotations.add(rotation_id)
            await self._notify_rotation_event(event)

            # Get current secret
            old_secret = await self.secrets_manager.get_secret(
                secret_key, environment, use_cache=False
            )
            if not old_secret and not force:
                raise ValueError(f"Current secret not found for {secret_key}")

            event.old_secret_hint = str(old_secret)[-4:] if old_secret else "none"

            # Generate new secret
            generator = self.generators.get(policy.rotation_type)
            if not generator:
                raise ValueError(f"No generator available for {policy.rotation_type}")

            new_secret = await generator.generate(str(old_secret) if old_secret else "", policy)
            event.new_secret_hint = str(new_secret)[-4:]

            # Validate new secret
            if policy.validation_required:
                is_valid = await generator.validate(new_secret, policy)
                if not is_valid:
                    raise ValueError("Generated secret failed validation")

                # External validation for specific types
                if policy.rotation_type == RotationType.API_KEY:
                    await self._validate_api_key_externally(secret_key, new_secret)

            if self.dry_run:
                logger.info(f"DRY RUN: Would rotate {secret_key} to {event.new_secret_hint}")
                event.status = RotationStatus.COMPLETED
                return True

            # Update secret in ESC
            success = await self.secrets_manager.set_secret(secret_key, new_secret, environment)
            if not success:
                raise ValueError("Failed to update secret in ESC")

            # Store rollback information
            if old_secret:
                self.rollback_queue[rotation_id] = event
                # Schedule rollback cleanup
                asyncio.create_task(
                    self._cleanup_rollback(rotation_id, policy.rollback_timeout_minutes)
                )

            # Update status
            event.status = RotationStatus.COMPLETED
            event.completed_at = datetime.utcnow()

            logger.info(f"Successfully rotated secret {secret_key} in {environment}")
            return True

        except Exception as e:
            event.status = RotationStatus.FAILED
            event.error_message = str(e)
            event.completed_at = datetime.utcnow()
            logger.error(f"Failed to rotate secret {secret_key}: {e}")
            return False

        finally:
            self.active_rotations.discard(rotation_id)
            self.rotation_events.append(event)
            await self._notify_rotation_event(event)

    async def _validate_api_key_externally(self, secret_key: str, api_key: str):
        """Validate API key against external service"""
        async with self.validator:
            if "openai" in secret_key.lower():
                if not await self.validator.validate_openai_key(api_key):
                    raise ValueError("OpenAI API key validation failed")

            elif "anthropic" in secret_key.lower():
                if not await self.validator.validate_anthropic_key(api_key):
                    raise ValueError("Anthropic API key validation failed")

    async def rollback_rotation(self, rotation_id: str) -> bool:
        """Rollback a secret rotation"""
        event = self.rollback_queue.get(rotation_id)
        if not event:
            logger.error(f"No rollback information found for {rotation_id}")
            return False

        try:
            # Get the old secret (this would need to be stored securely)
            old_secret = await self._get_rollback_secret(rotation_id)
            if not old_secret:
                logger.error(f"No rollback secret available for {rotation_id}")
                return False

            # Restore old secret
            success = await self.secrets_manager.set_secret(
                event.secret_key, old_secret, event.environment
            )

            if success:
                event.status = RotationStatus.ROLLBACK
                event.completed_at = datetime.utcnow()
                logger.info(f"Successfully rolled back rotation {rotation_id}")

                # Clean up rollback entry
                self.rollback_queue.pop(rotation_id, None)
                return True
            else:
                logger.error(f"Failed to rollback rotation {rotation_id}")
                return False

        except Exception as e:
            logger.error(f"Error during rollback {rotation_id}: {e}")
            return False

    async def _get_rollback_secret(self, rotation_id: str) -> Optional[str]:
        """Get secret for rollback (implementation depends on storage strategy)"""
        # This would retrieve the old secret from secure storage
        # For now, return None - would need to implement secure rollback storage
        return None

    async def _cleanup_rollback(self, rotation_id: str, timeout_minutes: int):
        """Clean up rollback information after timeout"""
        await asyncio.sleep(timeout_minutes * 60)
        self.rollback_queue.pop(rotation_id, None)
        logger.debug(f"Cleaned up rollback information for {rotation_id}")

    async def _notify_rotation_event(self, event: RotationEvent):
        """Notify about rotation event"""
        if not self.enable_notifications:
            return

        for callback in self.notification_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in rotation notification callback: {e}")

    def get_rotation_status(self, secret_key: str) -> List[RotationEvent]:
        """Get rotation status for a secret"""
        return [event for event in self.rotation_events if event.secret_key == secret_key]

    def get_active_rotations(self) -> Dict[str, RotationEvent]:
        """Get currently active rotations"""
        active = {}
        for event in self.rotation_events:
            if event.status == RotationStatus.IN_PROGRESS:
                active[event.rotation_id] = event
        return active

    def get_rotation_statistics(self) -> Dict[str, Any]:
        """Get rotation statistics"""
        total_rotations = len(self.rotation_events)
        successful = len([e for e in self.rotation_events if e.status == RotationStatus.COMPLETED])
        failed = len([e for e in self.rotation_events if e.status == RotationStatus.FAILED])

        return {
            "total_rotations": total_rotations,
            "successful_rotations": successful,
            "failed_rotations": failed,
            "success_rate": successful / total_rotations if total_rotations > 0 else 0,
            "active_rotations": len(self.active_rotations),
            "rollback_available": len(self.rollback_queue),
            "policies_configured": len(self.rotation_policies),
            "last_rotation": max((e.started_at for e in self.rotation_events), default=None),
        }

    async def create_rotation_report(self) -> Dict[str, Any]:
        """Create detailed rotation report"""
        stats = self.get_rotation_statistics()

        # Group events by secret
        by_secret = {}
        for event in self.rotation_events:
            if event.secret_key not in by_secret:
                by_secret[event.secret_key] = []
            by_secret[event.secret_key].append(
                {
                    "rotation_id": event.rotation_id,
                    "status": event.status.value,
                    "environment": event.environment,
                    "started_at": event.started_at.isoformat(),
                    "completed_at": event.completed_at.isoformat() if event.completed_at else None,
                    "error_message": event.error_message,
                }
            )

        return {
            "report_generated": datetime.utcnow().isoformat(),
            "statistics": stats,
            "rotation_events_by_secret": by_secret,
            "policies": {
                key: {
                    "rotation_type": policy.rotation_type.value,
                    "interval_days": policy.interval_days,
                    "auto_rotate": policy.auto_rotate,
                    "environments": policy.environments,
                }
                for key, policy in self.rotation_policies.items()
            },
        }
