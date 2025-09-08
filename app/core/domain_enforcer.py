"""
Domain Boundary Enforcer - Validates and enforces domain separation
Ensures Artemis handles only repository/code operations
Ensures Sophia handles only business operations
Provides access control and domain validation
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from app.memory.unified_memory_router import MemoryDomain

logger = logging.getLogger(__name__)

# ==============================================================================
# DOMAIN DEFINITIONS
# ==============================================================================


class OperationType(str, Enum):
    """Types of operations that can be performed"""

    # Artemis Operations
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_REFACTORING = "code_refactoring"
    SECURITY_SCANNING = "security_scanning"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ARCHITECTURE_DESIGN = "architecture_design"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    REPOSITORY_ANALYSIS = "repository_analysis"
    CI_CD_OPERATIONS = "ci_cd_operations"

    # Sophia Operations
    BUSINESS_ANALYSIS = "business_analysis"
    SALES_ANALYTICS = "sales_analytics"
    CUSTOMER_INSIGHTS = "customer_insights"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    REVENUE_FORECASTING = "revenue_forecasting"
    STRATEGIC_PLANNING = "strategic_planning"
    OKR_TRACKING = "okr_tracking"
    CUSTOMER_SUCCESS = "customer_success"
    BUSINESS_INTELLIGENCE = "business_intelligence"

    # Shared Operations
    REPORTING = "reporting"
    MONITORING = "monitoring"
    LOGGING = "logging"
    METRICS_COLLECTION = "metrics_collection"


class UserRole(str, Enum):
    """User roles for access control"""

    ADMIN = "admin"
    DEVELOPER = "developer"
    DEVOPS = "devops"
    ARCHITECT = "architect"
    BUSINESS_ANALYST = "business_analyst"
    EXECUTIVE = "executive"
    SALES = "sales"
    CUSTOMER_SUCCESS = "customer_success"
    MARKETING = "marketing"
    READONLY = "readonly"


class AccessLevel(str, Enum):
    """Access levels for operations"""

    FULL = "full"
    WRITE = "write"
    READ = "read"
    EXECUTE = "execute"
    NONE = "none"


# ==============================================================================
# DATA MODELS
# ==============================================================================


@dataclass
class DomainRequest:
    """Request to be validated for domain access"""

    id: str
    user_id: str
    user_role: UserRole
    target_domain: MemoryDomain
    operation_type: OperationType
    resource_path: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ValidationResult:
    """Result of domain validation"""

    request_id: str
    allowed: bool
    reason: Optional[str] = None
    suggested_domain: Optional[MemoryDomain] = None
    access_level: AccessLevel = AccessLevel.NONE
    restrictions: list[str] = field(default_factory=list)
    audit_logged: bool = False


@dataclass
class CrossDomainRequest:
    """Request for cross-domain operation"""

    id: str
    source_domain: MemoryDomain
    target_domain: MemoryDomain
    operation_type: OperationType
    requestor_id: str
    requestor_role: UserRole
    justification: str
    data: dict[str, Any] = field(default_factory=dict)
    approved: bool = False
    approval_timestamp: Optional[str] = None
    approver_id: Optional[str] = None


@dataclass
class DomainAuditLog:
    """Audit log entry for domain operations"""

    id: str
    request_id: str
    domain: MemoryDomain
    operation: OperationType
    user_id: str
    user_role: UserRole
    allowed: bool
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# DOMAIN ENFORCER CLASS
# ==============================================================================


class DomainEnforcer:
    """
    Enforces strict domain boundaries between Artemis and Sophia
    Validates all requests and maintains access control
    """

    def __init__(self):
        # Domain operation mappings
        self.artemis_operations = {
            OperationType.CODE_GENERATION,
            OperationType.CODE_REVIEW,
            OperationType.CODE_REFACTORING,
            OperationType.SECURITY_SCANNING,
            OperationType.PERFORMANCE_OPTIMIZATION,
            OperationType.ARCHITECTURE_DESIGN,
            OperationType.TEST_GENERATION,
            OperationType.DOCUMENTATION,
            OperationType.REPOSITORY_ANALYSIS,
            OperationType.CI_CD_OPERATIONS,
        }

        self.sophia_operations = {
            OperationType.BUSINESS_ANALYSIS,
            OperationType.SALES_ANALYTICS,
            OperationType.CUSTOMER_INSIGHTS,
            OperationType.MARKET_RESEARCH,
            OperationType.COMPETITIVE_ANALYSIS,
            OperationType.REVENUE_FORECASTING,
            OperationType.STRATEGIC_PLANNING,
            OperationType.OKR_TRACKING,
            OperationType.CUSTOMER_SUCCESS,
            OperationType.BUSINESS_INTELLIGENCE,
        }

        self.shared_operations = {
            OperationType.REPORTING,
            OperationType.MONITORING,
            OperationType.LOGGING,
            OperationType.METRICS_COLLECTION,
        }

        # Access control matrix
        self.access_matrix = self._initialize_access_matrix()

        # Cross-domain request management
        self.pending_cross_domain_requests: dict[str, CrossDomainRequest] = {}
        self.approved_cross_domain_requests: dict[str, CrossDomainRequest] = {}

        # Audit logging
        self.audit_logs: list[DomainAuditLog] = []
        self.enable_audit_logging = True

        # Statistics
        self.validation_stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "denied_requests": 0,
            "cross_domain_requests": 0,
            "violations_detected": 0,
        }

        logger.info("🛡️ Domain Boundary Enforcer initialized with strict separation rules")

    def _initialize_access_matrix(self) -> dict[tuple[UserRole, MemoryDomain], AccessLevel]:
        """Initialize the access control matrix"""
        matrix = {}

        # Admin has full access to both domains
        matrix[(UserRole.ADMIN, MemoryDomain.ARTEMIS)] = AccessLevel.FULL
        matrix[(UserRole.ADMIN, MemoryDomain.SOPHIA)] = AccessLevel.FULL

        # Developer roles for Artemis
        matrix[(UserRole.DEVELOPER, MemoryDomain.ARTEMIS)] = AccessLevel.FULL
        matrix[(UserRole.DEVOPS, MemoryDomain.ARTEMIS)] = AccessLevel.FULL
        matrix[(UserRole.ARCHITECT, MemoryDomain.ARTEMIS)] = AccessLevel.FULL

        # Business roles for Sophia
        matrix[(UserRole.BUSINESS_ANALYST, MemoryDomain.SOPHIA)] = AccessLevel.FULL
        matrix[(UserRole.EXECUTIVE, MemoryDomain.SOPHIA)] = AccessLevel.FULL
        matrix[(UserRole.SALES, MemoryDomain.SOPHIA)] = AccessLevel.WRITE
        matrix[(UserRole.CUSTOMER_SUCCESS, MemoryDomain.SOPHIA)] = AccessLevel.WRITE
        matrix[(UserRole.MARKETING, MemoryDomain.SOPHIA)] = AccessLevel.WRITE

        # Limited cross-domain access
        matrix[(UserRole.BUSINESS_ANALYST, MemoryDomain.ARTEMIS)] = AccessLevel.READ
        matrix[(UserRole.DEVELOPER, MemoryDomain.SOPHIA)] = AccessLevel.READ

        # Readonly has read access to both
        matrix[(UserRole.READONLY, MemoryDomain.ARTEMIS)] = AccessLevel.READ
        matrix[(UserRole.READONLY, MemoryDomain.SOPHIA)] = AccessLevel.READ

        return matrix

    # ==============================================================================
    # VALIDATION METHODS
    # ==============================================================================

    def validate_request(self, request: DomainRequest) -> ValidationResult:
        """
        Validate a domain request

        Args:
            request: The domain request to validate

        Returns:
            ValidationResult with allowed/denied status and details
        """
        self.validation_stats["total_requests"] += 1

        # Create validation result
        result = ValidationResult(request_id=request.id, allowed=False)

        # Check if operation belongs to target domain
        if not self._is_valid_domain_operation(request.operation_type, request.target_domain):
            result.reason = (
                f"Operation {request.operation_type} not allowed in {request.target_domain} domain"
            )
            result.suggested_domain = self._get_correct_domain(request.operation_type)
            self.validation_stats["denied_requests"] += 1
            self.validation_stats["violations_detected"] += 1

            # Log violation
            self._log_audit(request, result)
            return result

        # Check user access level
        access_level = self._get_user_access(request.user_role, request.target_domain)

        if access_level == AccessLevel.NONE:
            result.reason = (
                f"User role {request.user_role} has no access to {request.target_domain} domain"
            )
            self.validation_stats["denied_requests"] += 1
            self._log_audit(request, result)
            return result

        # Check if operation requires specific access level
        required_level = self._get_required_access_level(request.operation_type)

        if not self._has_sufficient_access(access_level, required_level):
            result.reason = (
                f"Insufficient access level. Required: {required_level}, Have: {access_level}"
            )
            result.access_level = access_level
            self.validation_stats["denied_requests"] += 1
            self._log_audit(request, result)
            return result

        # Check resource-specific restrictions
        restrictions = self._check_resource_restrictions(request)
        if restrictions:
            result.restrictions = restrictions
            if self._are_restrictions_blocking(restrictions):
                result.reason = f"Resource restrictions: {', '.join(restrictions)}"
                self.validation_stats["denied_requests"] += 1
                self._log_audit(request, result)
                return result

        # Request is allowed
        result.allowed = True
        result.access_level = access_level
        result.reason = "Request validated successfully"
        self.validation_stats["allowed_requests"] += 1

        # Log successful request
        self._log_audit(request, result)

        return result

    def _is_valid_domain_operation(self, operation: OperationType, domain: MemoryDomain) -> bool:
        """Check if operation is valid for the domain"""
        if operation in self.shared_operations:
            return True

        if domain == MemoryDomain.ARTEMIS:
            return operation in self.artemis_operations
        elif domain == MemoryDomain.SOPHIA:
            return operation in self.sophia_operations

        return False

    def _get_correct_domain(self, operation: OperationType) -> Optional[MemoryDomain]:
        """Get the correct domain for an operation"""
        if operation in self.artemis_operations:
            return MemoryDomain.ARTEMIS
        elif operation in self.sophia_operations:
            return MemoryDomain.SOPHIA
        return None

    def _get_user_access(self, user_role: UserRole, domain: MemoryDomain) -> AccessLevel:
        """Get user's access level for a domain"""
        return self.access_matrix.get((user_role, domain), AccessLevel.NONE)

    def _get_required_access_level(self, operation: OperationType) -> AccessLevel:
        """Get required access level for an operation"""
        # Write operations
        write_operations = {
            OperationType.CODE_GENERATION,
            OperationType.CODE_REFACTORING,
            OperationType.TEST_GENERATION,
            OperationType.REVENUE_FORECASTING,
            OperationType.STRATEGIC_PLANNING,
            OperationType.OKR_TRACKING,
        }

        # Execute operations
        execute_operations = {
            OperationType.CI_CD_OPERATIONS,
            OperationType.SECURITY_SCANNING,
            OperationType.PERFORMANCE_OPTIMIZATION,
        }

        if operation in write_operations:
            return AccessLevel.WRITE
        elif operation in execute_operations:
            return AccessLevel.EXECUTE
        else:
            return AccessLevel.READ

    def _has_sufficient_access(self, user_level: AccessLevel, required_level: AccessLevel) -> bool:
        """Check if user has sufficient access level"""
        access_hierarchy = {
            AccessLevel.NONE: 0,
            AccessLevel.READ: 1,
            AccessLevel.EXECUTE: 2,
            AccessLevel.WRITE: 3,
            AccessLevel.FULL: 4,
        }

        return access_hierarchy.get(user_level, 0) >= access_hierarchy.get(required_level, 0)

    def _check_resource_restrictions(self, request: DomainRequest) -> list[str]:
        """Check for resource-specific restrictions"""
        restrictions = []

        # Check path-based restrictions
        if request.resource_path:
            # Artemis path restrictions
            if request.target_domain == MemoryDomain.ARTEMIS:
                if "production" in request.resource_path.lower():
                    if request.user_role not in [UserRole.ADMIN, UserRole.DEVOPS]:
                        restrictions.append("Production resources require DevOps or Admin role")

                if "secrets" in request.resource_path.lower():
                    if request.user_role != UserRole.ADMIN:
                        restrictions.append("Secrets access requires Admin role")

            # Sophia path restrictions
            elif request.target_domain == MemoryDomain.SOPHIA:
                if "financial" in request.resource_path.lower():
                    if request.user_role not in [UserRole.ADMIN, UserRole.EXECUTIVE]:
                        restrictions.append("Financial data requires Executive or Admin role")

                if "customer_data" in request.resource_path.lower():
                    if request.user_role not in [
                        UserRole.ADMIN,
                        UserRole.CUSTOMER_SUCCESS,
                        UserRole.SALES,
                    ]:
                        restrictions.append("Customer data requires appropriate role")

        # Time-based restrictions
        if request.metadata.get("after_hours"):
            if request.user_role not in [UserRole.ADMIN, UserRole.DEVOPS]:
                restrictions.append("After-hours operations require Admin or DevOps role")

        return restrictions

    def _are_restrictions_blocking(self, restrictions: list[str]) -> bool:
        """Determine if restrictions should block the request"""
        # Any restriction is blocking for now
        # Could be made more sophisticated based on restriction types
        return len(restrictions) > 0

    # ==============================================================================
    # CROSS-DOMAIN REQUEST METHODS
    # ==============================================================================

    def create_cross_domain_request(
        self,
        source_domain: MemoryDomain,
        target_domain: MemoryDomain,
        operation: OperationType,
        requestor_id: str,
        requestor_role: UserRole,
        justification: str,
        data: Optional[dict[str, Any]] = None,
    ) -> CrossDomainRequest:
        """
        Create a cross-domain request that requires approval

        Args:
            source_domain: The requesting domain
            target_domain: The target domain
            operation: The operation to perform
            requestor_id: ID of the requestor
            requestor_role: Role of the requestor
            justification: Justification for cross-domain access
            data: Optional data for the request

        Returns:
            CrossDomainRequest object
        """
        request = CrossDomainRequest(
            id=f"cross_domain_{uuid4().hex[:8]}",
            source_domain=source_domain,
            target_domain=target_domain,
            operation_type=operation,
            requestor_id=requestor_id,
            requestor_role=requestor_role,
            justification=justification,
            data=data or {},
        )

        self.pending_cross_domain_requests[request.id] = request
        self.validation_stats["cross_domain_requests"] += 1

        logger.info(
            f"Cross-domain request created: {request.id} " f"({source_domain} -> {target_domain})"
        )

        return request

    def approve_cross_domain_request(
        self, request_id: str, approver_id: str, approver_role: UserRole
    ) -> bool:
        """
        Approve a cross-domain request

        Args:
            request_id: ID of the request to approve
            approver_id: ID of the approver
            approver_role: Role of the approver

        Returns:
            True if approved, False otherwise
        """
        if request_id not in self.pending_cross_domain_requests:
            logger.warning(f"Cross-domain request {request_id} not found")
            return False

        # Only admins can approve cross-domain requests
        if approver_role != UserRole.ADMIN:
            logger.warning(
                f"User {approver_id} with role {approver_role} "
                f"cannot approve cross-domain requests"
            )
            return False

        request = self.pending_cross_domain_requests.pop(request_id)
        request.approved = True
        request.approval_timestamp = datetime.now(timezone.utc).isoformat()
        request.approver_id = approver_id

        self.approved_cross_domain_requests[request_id] = request

        logger.info(f"Cross-domain request {request_id} approved by {approver_id}")

        return True

    def check_cross_domain_approval(self, request_id: str) -> bool:
        """Check if a cross-domain request is approved"""
        return request_id in self.approved_cross_domain_requests

    # ==============================================================================
    # AUDIT AND MONITORING
    # ==============================================================================

    def _log_audit(self, request: DomainRequest, result: ValidationResult):
        """Log an audit entry"""
        if not self.enable_audit_logging:
            return

        audit_log = DomainAuditLog(
            id=f"audit_{uuid4().hex[:8]}",
            request_id=request.id,
            domain=request.target_domain,
            operation=request.operation_type,
            user_id=request.user_id,
            user_role=request.user_role,
            allowed=result.allowed,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={
                "reason": result.reason,
                "access_level": result.access_level.value if result.access_level else None,
                "restrictions": result.restrictions,
                "resource_path": request.resource_path,
            },
        )

        self.audit_logs.append(audit_log)
        result.audit_logged = True

        # Log violations with higher severity
        if not result.allowed and "violation" in (result.reason or "").lower():
            logger.warning(
                f"DOMAIN VIOLATION: User {request.user_id} ({request.user_role}) "
                f"attempted {request.operation_type} on {request.target_domain}"
            )

    def get_audit_logs(
        self,
        domain: Optional[MemoryDomain] = None,
        user_id: Optional[str] = None,
        allowed: Optional[bool] = None,
        limit: int = 100,
    ) -> list[DomainAuditLog]:
        """
        Get audit logs with optional filtering

        Args:
            domain: Filter by domain
            user_id: Filter by user ID
            allowed: Filter by allowed/denied
            limit: Maximum number of logs to return

        Returns:
            List of audit log entries
        """
        logs = self.audit_logs

        if domain:
            logs = [log for log in logs if log.domain == domain]

        if user_id:
            logs = [log for log in logs if log.user_id == user_id]

        if allowed is not None:
            logs = [log for log in logs if log.allowed == allowed]

        # Return most recent logs first
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_validation_statistics(self) -> dict[str, Any]:
        """Get validation statistics"""
        return {
            **self.validation_stats,
            "approval_rate": (
                self.validation_stats["allowed_requests"]
                / max(self.validation_stats["total_requests"], 1)
            ),
            "violation_rate": (
                self.validation_stats["violations_detected"]
                / max(self.validation_stats["total_requests"], 1)
            ),
            "pending_cross_domain": len(self.pending_cross_domain_requests),
            "approved_cross_domain": len(self.approved_cross_domain_requests),
            "audit_logs_count": len(self.audit_logs),
        }

    def get_domain_summary(self) -> dict[str, Any]:
        """Get summary of domain boundaries and operations"""
        return {
            "artemis_domain": {
                "description": "Repository and code operations",
                "operations": list(self.artemis_operations),
                "allowed_roles": [
                    role.value
                    for role in UserRole
                    if self._get_user_access(role, MemoryDomain.ARTEMIS) != AccessLevel.NONE
                ],
            },
            "sophia_domain": {
                "description": "Business operations",
                "operations": list(self.sophia_operations),
                "allowed_roles": [
                    role.value
                    for role in UserRole
                    if self._get_user_access(role, MemoryDomain.SOPHIA) != AccessLevel.NONE
                ],
            },
            "shared_operations": list(self.shared_operations),
            "cross_domain_enabled": True,
            "audit_logging_enabled": self.enable_audit_logging,
        }

    # ==============================================================================
    # UTILITY METHODS
    # ==============================================================================

    def reset_statistics(self):
        """Reset validation statistics"""
        self.validation_stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "denied_requests": 0,
            "cross_domain_requests": 0,
            "violations_detected": 0,
        }
        logger.info("Validation statistics reset")

    def clear_audit_logs(self, older_than_days: int = 30):
        """Clear audit logs older than specified days"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (older_than_days * 86400)

        original_count = len(self.audit_logs)
        self.audit_logs = [
            log
            for log in self.audit_logs
            if datetime.fromisoformat(log.timestamp).timestamp() > cutoff_time
        ]

        removed_count = original_count - len(self.audit_logs)
        logger.info(f"Cleared {removed_count} audit logs older than {older_than_days} days")

        return removed_count


# ==============================================================================
# GLOBAL INSTANCE
# ==============================================================================

# Global domain enforcer instance
domain_enforcer = DomainEnforcer()

# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================


def validate_domain_request(
    user_id: str,
    user_role: UserRole,
    target_domain: MemoryDomain,
    operation: OperationType,
    resource_path: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> ValidationResult:
    """
    Convenience function to validate a domain request

    Args:
        user_id: ID of the user making the request
        user_role: Role of the user
        target_domain: Target domain for the operation
        operation: Type of operation to perform
        resource_path: Optional resource path
        metadata: Optional metadata

    Returns:
        ValidationResult
    """
    request = DomainRequest(
        id=f"req_{uuid4().hex[:8]}",
        user_id=user_id,
        user_role=user_role,
        target_domain=target_domain,
        operation_type=operation,
        resource_path=resource_path,
        metadata=metadata or {},
    )

    return domain_enforcer.validate_request(request)


def request_cross_domain_access(
    source: MemoryDomain,
    target: MemoryDomain,
    operation: OperationType,
    user_id: str,
    user_role: UserRole,
    justification: str,
) -> CrossDomainRequest:
    """
    Convenience function to request cross-domain access

    Args:
        source: Source domain
        target: Target domain
        operation: Operation to perform
        user_id: ID of the requestor
        user_role: Role of the requestor
        justification: Justification for the request

    Returns:
        CrossDomainRequest
    """
    return domain_enforcer.create_cross_domain_request(
        source_domain=source,
        target_domain=target,
        operation=operation,
        requestor_id=user_id,
        requestor_role=user_role,
        justification=justification,
    )


def get_domain_access_summary(user_role: UserRole) -> dict[str, Any]:
    """
    Get a summary of what domains and operations a user role can access

    Args:
        user_role: The user role to check

    Returns:
        Dictionary with access summary
    """
    artemis_access = domain_enforcer._get_user_access(user_role, MemoryDomain.ARTEMIS)
    sophia_access = domain_enforcer._get_user_access(user_role, MemoryDomain.SOPHIA)

    summary = {
        "role": user_role.value,
        "artemis_access": artemis_access.value,
        "sophia_access": sophia_access.value,
        "allowed_operations": [],
    }

    # Add allowed operations based on access level
    if artemis_access != AccessLevel.NONE:
        for op in domain_enforcer.artemis_operations:
            required = domain_enforcer._get_required_access_level(op)
            if domain_enforcer._has_sufficient_access(artemis_access, required):
                summary["allowed_operations"].append(op.value)

    if sophia_access != AccessLevel.NONE:
        for op in domain_enforcer.sophia_operations:
            required = domain_enforcer._get_required_access_level(op)
            if domain_enforcer._has_sufficient_access(sophia_access, required):
                summary["allowed_operations"].append(op.value)

    # Add shared operations if any access
    if artemis_access != AccessLevel.NONE or sophia_access != AccessLevel.NONE:
        summary["allowed_operations"].extend([op.value for op in domain_enforcer.shared_operations])

    return summary
