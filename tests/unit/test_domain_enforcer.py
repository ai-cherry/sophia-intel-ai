"""
Unit tests for Domain Boundary Enforcer
Tests access control matrix enforcement, cross-domain request blocking,
allowed domain operations, audit logging, and domain violation detection
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.core.domain_enforcer import (
    AccessLevel,
    CrossDomainRequest,
    DomainAuditLog,
    DomainEnforcer,
    DomainRequest,
    OperationType,
    UserRole,
    ValidationResult,
    domain_enforcer,
    get_domain_access_summary,
    request_cross_domain_access,
    validate_domain_request,
)
from app.memory.unified_memory_router import MemoryDomain


class TestDomainEnforcer:
    """Test suite for Domain Boundary Enforcer"""

    @pytest.fixture
    def enforcer(self):
        """Create a fresh enforcer instance for each test"""
        return DomainEnforcer()

    @pytest.fixture
    def sample_artemis_request(self):
        """Create a sample Artemis domain request"""
        return DomainRequest(
            id="test_req_001",
            user_id="dev_user_123",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_GENERATION,
            resource_path="/src/components",
            metadata={"environment": "development"},
        )

    @pytest.fixture
    def sample_sophia_request(self):
        """Create a sample Sophia domain request"""
        return DomainRequest(
            id="test_req_002",
            user_id="analyst_user_456",
            user_role=UserRole.BUSINESS_ANALYST,
            target_domain=MemoryDomain.SOPHIA,
            operation_type=OperationType.SALES_ANALYTICS,
            resource_path="/reports/sales",
            metadata={"quarter": "Q4"},
        )

    # ==============================================================================
    # CONFIGURATION TESTS
    # ==============================================================================

    def test_enforcer_initialization(self, enforcer):
        """Test that enforcer is properly initialized with domain operations"""
        # Check Artemis operations
        assert OperationType.CODE_GENERATION in enforcer.artemis_operations
        assert OperationType.CODE_REVIEW in enforcer.artemis_operations
        assert OperationType.SECURITY_SCANNING in enforcer.artemis_operations
        assert OperationType.REPOSITORY_ANALYSIS in enforcer.artemis_operations

        # Check Sophia operations
        assert OperationType.BUSINESS_ANALYSIS in enforcer.sophia_operations
        assert OperationType.SALES_ANALYTICS in enforcer.sophia_operations
        assert OperationType.CUSTOMER_INSIGHTS in enforcer.sophia_operations
        assert OperationType.OKR_TRACKING in enforcer.sophia_operations

        # Check shared operations
        assert OperationType.REPORTING in enforcer.shared_operations
        assert OperationType.MONITORING in enforcer.shared_operations
        assert OperationType.LOGGING in enforcer.shared_operations

        # Check initialization
        assert enforcer.enable_audit_logging is True
        assert len(enforcer.pending_cross_domain_requests) == 0
        assert enforcer.validation_stats["total_requests"] == 0

    def test_access_matrix_initialization(self, enforcer):
        """Test that access control matrix is properly configured"""
        matrix = enforcer.access_matrix

        # Admin has full access to both domains
        assert matrix[(UserRole.ADMIN, MemoryDomain.ARTEMIS)] == AccessLevel.FULL
        assert matrix[(UserRole.ADMIN, MemoryDomain.SOPHIA)] == AccessLevel.FULL

        # Developer roles for Artemis
        assert matrix[(UserRole.DEVELOPER, MemoryDomain.ARTEMIS)] == AccessLevel.FULL
        assert matrix[(UserRole.DEVOPS, MemoryDomain.ARTEMIS)] == AccessLevel.FULL
        assert matrix[(UserRole.ARCHITECT, MemoryDomain.ARTEMIS)] == AccessLevel.FULL

        # Business roles for Sophia
        assert (
            matrix[(UserRole.BUSINESS_ANALYST, MemoryDomain.SOPHIA)] == AccessLevel.FULL
        )
        assert matrix[(UserRole.EXECUTIVE, MemoryDomain.SOPHIA)] == AccessLevel.FULL
        assert matrix[(UserRole.SALES, MemoryDomain.SOPHIA)] == AccessLevel.WRITE
        assert (
            matrix[(UserRole.CUSTOMER_SUCCESS, MemoryDomain.SOPHIA)]
            == AccessLevel.WRITE
        )

        # Limited cross-domain access
        assert (
            matrix[(UserRole.BUSINESS_ANALYST, MemoryDomain.ARTEMIS)]
            == AccessLevel.READ
        )
        assert matrix[(UserRole.DEVELOPER, MemoryDomain.SOPHIA)] == AccessLevel.READ

        # Readonly has read access to both
        assert matrix[(UserRole.READONLY, MemoryDomain.ARTEMIS)] == AccessLevel.READ
        assert matrix[(UserRole.READONLY, MemoryDomain.SOPHIA)] == AccessLevel.READ

    # ==============================================================================
    # ACCESS CONTROL TESTS
    # ==============================================================================

    def test_developer_access_to_artemis(self, enforcer, sample_artemis_request):
        """Test that developers have full access to Artemis domain"""
        result = enforcer.validate_request(sample_artemis_request)

        assert result.allowed is True
        assert result.access_level == AccessLevel.FULL
        assert result.reason == "Request validated successfully"
        assert enforcer.validation_stats["allowed_requests"] == 1

    def test_business_analyst_access_to_sophia(self, enforcer, sample_sophia_request):
        """Test that business analysts have full access to Sophia domain"""
        result = enforcer.validate_request(sample_sophia_request)

        assert result.allowed is True
        assert result.access_level == AccessLevel.FULL
        assert result.reason == "Request validated successfully"

    def test_developer_limited_access_to_sophia(self, enforcer):
        """Test that developers have only read access to Sophia domain"""
        request = DomainRequest(
            id="test_req_003",
            user_id="dev_user",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.SOPHIA,
            operation_type=OperationType.BUSINESS_ANALYSIS,  # Read operation
            resource_path="/analytics/dashboard",
        )

        result = enforcer.validate_request(request)

        assert result.allowed is True
        assert result.access_level == AccessLevel.READ

        # Try a write operation - should be denied
        request.operation_type = OperationType.REVENUE_FORECASTING  # Write operation
        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert "Insufficient access level" in result.reason

    def test_business_analyst_limited_access_to_artemis(self, enforcer):
        """Test that business analysts have only read access to Artemis domain"""
        request = DomainRequest(
            id="test_req_004",
            user_id="analyst_user",
            user_role=UserRole.BUSINESS_ANALYST,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_REVIEW,  # Read operation
            resource_path="/src/analysis",
        )

        result = enforcer.validate_request(request)

        assert result.allowed is True
        assert result.access_level == AccessLevel.READ

        # Try a write operation - should be denied
        request.operation_type = OperationType.CODE_GENERATION  # Write operation
        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert "Insufficient access level" in result.reason

    def test_admin_full_access_both_domains(self, enforcer):
        """Test that admin has full access to both domains"""
        # Test Artemis access
        artemis_request = DomainRequest(
            id="test_req_005",
            user_id="admin_user",
            user_role=UserRole.ADMIN,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_GENERATION,
        )

        result = enforcer.validate_request(artemis_request)
        assert result.allowed is True
        assert result.access_level == AccessLevel.FULL

        # Test Sophia access
        sophia_request = DomainRequest(
            id="test_req_006",
            user_id="admin_user",
            user_role=UserRole.ADMIN,
            target_domain=MemoryDomain.SOPHIA,
            operation_type=OperationType.STRATEGIC_PLANNING,
        )

        result = enforcer.validate_request(sophia_request)
        assert result.allowed is True
        assert result.access_level == AccessLevel.FULL

    def test_readonly_role_access(self, enforcer):
        """Test that readonly role has read-only access to both domains"""
        # Test Artemis read
        request = DomainRequest(
            id="test_req_007",
            user_id="readonly_user",
            user_role=UserRole.READONLY,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_REVIEW,
        )

        result = enforcer.validate_request(request)
        assert result.allowed is True
        assert result.access_level == AccessLevel.READ

        # Test Sophia read
        request.target_domain = MemoryDomain.SOPHIA
        request.operation_type = OperationType.BUSINESS_ANALYSIS
        result = enforcer.validate_request(request)
        assert result.allowed is True

        # Test write operation - should be denied
        request.operation_type = OperationType.CODE_GENERATION
        result = enforcer.validate_request(request)
        assert result.allowed is False

    # ==============================================================================
    # DOMAIN VIOLATION TESTS
    # ==============================================================================

    def test_cross_domain_violation_artemis_operation_in_sophia(self, enforcer):
        """Test detection of Artemis operation attempted in Sophia domain"""
        request = DomainRequest(
            id="test_req_008",
            user_id="analyst_user",
            user_role=UserRole.BUSINESS_ANALYST,
            target_domain=MemoryDomain.SOPHIA,
            operation_type=OperationType.CODE_GENERATION,  # Artemis operation!
        )

        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert "Operation code_generation not allowed in SOPHIA domain" in result.reason
        assert result.suggested_domain == MemoryDomain.ARTEMIS
        assert enforcer.validation_stats["violations_detected"] == 1
        assert enforcer.validation_stats["denied_requests"] == 1

    def test_cross_domain_violation_sophia_operation_in_artemis(self, enforcer):
        """Test detection of Sophia operation attempted in Artemis domain"""
        request = DomainRequest(
            id="test_req_009",
            user_id="dev_user",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.SALES_ANALYTICS,  # Sophia operation!
        )

        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert (
            "Operation sales_analytics not allowed in ARTEMIS domain" in result.reason
        )
        assert result.suggested_domain == MemoryDomain.SOPHIA
        assert enforcer.validation_stats["violations_detected"] == 1

    def test_unauthorized_role_access(self, enforcer):
        """Test that unauthorized roles are denied access"""
        # Sales role trying to access Artemis
        request = DomainRequest(
            id="test_req_010",
            user_id="sales_user",
            user_role=UserRole.SALES,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_REVIEW,
        )

        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert "User role sales has no access to ARTEMIS domain" in result.reason
        assert result.access_level == AccessLevel.NONE

    def test_shared_operations_allowed_both_domains(self, enforcer):
        """Test that shared operations are allowed in both domains"""
        # Test in Artemis
        request = DomainRequest(
            id="test_req_011",
            user_id="dev_user",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.MONITORING,  # Shared operation
        )

        result = enforcer.validate_request(request)
        assert result.allowed is True

        # Test in Sophia
        request.target_domain = MemoryDomain.SOPHIA
        request.user_role = UserRole.BUSINESS_ANALYST
        result = enforcer.validate_request(request)
        assert result.allowed is True

    # ==============================================================================
    # RESOURCE RESTRICTION TESTS
    # ==============================================================================

    def test_production_resource_restriction(self, enforcer):
        """Test that production resources require DevOps or Admin role"""
        request = DomainRequest(
            id="test_req_012",
            user_id="dev_user",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_GENERATION,
            resource_path="/production/api/services",
        )

        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert len(result.restrictions) > 0
        assert (
            "Production resources require DevOps or Admin role" in result.restrictions
        )

        # Test with DevOps role - should succeed
        request.user_role = UserRole.DEVOPS
        result = enforcer.validate_request(request)
        assert result.allowed is True

    def test_secrets_access_restriction(self, enforcer):
        """Test that secrets access requires Admin role"""
        request = DomainRequest(
            id="test_req_013",
            user_id="dev_user",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_REVIEW,
            resource_path="/config/secrets/api_keys",
        )

        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert "Secrets access requires Admin role" in result.restrictions

        # Test with Admin role - should succeed
        request.user_role = UserRole.ADMIN
        result = enforcer.validate_request(request)
        assert result.allowed is True

    def test_financial_data_restriction(self, enforcer):
        """Test that financial data requires Executive or Admin role"""
        request = DomainRequest(
            id="test_req_014",
            user_id="analyst_user",
            user_role=UserRole.BUSINESS_ANALYST,
            target_domain=MemoryDomain.SOPHIA,
            operation_type=OperationType.BUSINESS_ANALYSIS,
            resource_path="/data/financial/revenue",
        )

        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert "Financial data requires Executive or Admin role" in result.restrictions

        # Test with Executive role - should succeed
        request.user_role = UserRole.EXECUTIVE
        result = enforcer.validate_request(request)
        assert result.allowed is True

    def test_customer_data_restriction(self, enforcer):
        """Test that customer data requires appropriate role"""
        request = DomainRequest(
            id="test_req_015",
            user_id="marketing_user",
            user_role=UserRole.MARKETING,
            target_domain=MemoryDomain.SOPHIA,
            operation_type=OperationType.MARKET_RESEARCH,
            resource_path="/data/customer_data/profiles",
        )

        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert "Customer data requires appropriate role" in result.restrictions

        # Test with Customer Success role - should succeed
        request.user_role = UserRole.CUSTOMER_SUCCESS
        result = enforcer.validate_request(request)
        assert result.allowed is True

    def test_after_hours_restriction(self, enforcer):
        """Test that after-hours operations require Admin or DevOps role"""
        request = DomainRequest(
            id="test_req_016",
            user_id="dev_user",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_GENERATION,
            metadata={"after_hours": True},
        )

        result = enforcer.validate_request(request)

        assert result.allowed is False
        assert (
            "After-hours operations require Admin or DevOps role" in result.restrictions
        )

        # Test with DevOps role - should succeed
        request.user_role = UserRole.DEVOPS
        result = enforcer.validate_request(request)
        assert result.allowed is True

    # ==============================================================================
    # CROSS-DOMAIN REQUEST TESTS
    # ==============================================================================

    def test_create_cross_domain_request(self, enforcer):
        """Test creation of cross-domain request"""
        request = enforcer.create_cross_domain_request(
            source_domain=MemoryDomain.ARTEMIS,
            target_domain=MemoryDomain.SOPHIA,
            operation=OperationType.BUSINESS_ANALYSIS,
            requestor_id="dev_user",
            requestor_role=UserRole.DEVELOPER,
            justification="Need business context for API design",
            data={"api_name": "customer_api"},
        )

        assert request.id.startswith("cross_domain_")
        assert request.source_domain == MemoryDomain.ARTEMIS
        assert request.target_domain == MemoryDomain.SOPHIA
        assert request.justification == "Need business context for API design"
        assert request.approved is False
        assert request.id in enforcer.pending_cross_domain_requests
        assert enforcer.validation_stats["cross_domain_requests"] == 1

    def test_approve_cross_domain_request_by_admin(self, enforcer):
        """Test that only admin can approve cross-domain requests"""
        # Create request
        request = enforcer.create_cross_domain_request(
            source_domain=MemoryDomain.ARTEMIS,
            target_domain=MemoryDomain.SOPHIA,
            operation=OperationType.BUSINESS_ANALYSIS,
            requestor_id="dev_user",
            requestor_role=UserRole.DEVELOPER,
            justification="Need business metrics",
        )

        request_id = request.id

        # Try approval by non-admin - should fail
        success = enforcer.approve_cross_domain_request(
            request_id=request_id,
            approver_id="manager_user",
            approver_role=UserRole.BUSINESS_ANALYST,
        )

        assert success is False
        assert request_id in enforcer.pending_cross_domain_requests

        # Approve by admin - should succeed
        success = enforcer.approve_cross_domain_request(
            request_id=request_id,
            approver_id="admin_user",
            approver_role=UserRole.ADMIN,
        )

        assert success is True
        assert request_id not in enforcer.pending_cross_domain_requests
        assert request_id in enforcer.approved_cross_domain_requests

        approved_request = enforcer.approved_cross_domain_requests[request_id]
        assert approved_request.approved is True
        assert approved_request.approver_id == "admin_user"
        assert approved_request.approval_timestamp is not None

    def test_check_cross_domain_approval(self, enforcer):
        """Test checking if cross-domain request is approved"""
        # Create and approve request
        request = enforcer.create_cross_domain_request(
            source_domain=MemoryDomain.SOPHIA,
            target_domain=MemoryDomain.ARTEMIS,
            operation=OperationType.CODE_REVIEW,
            requestor_id="analyst_user",
            requestor_role=UserRole.BUSINESS_ANALYST,
            justification="Review integration code",
        )

        # Check before approval
        assert enforcer.check_cross_domain_approval(request.id) is False

        # Approve
        enforcer.approve_cross_domain_request(
            request_id=request.id,
            approver_id="admin_user",
            approver_role=UserRole.ADMIN,
        )

        # Check after approval
        assert enforcer.check_cross_domain_approval(request.id) is True

    def test_approve_nonexistent_request(self, enforcer):
        """Test attempting to approve non-existent request"""
        success = enforcer.approve_cross_domain_request(
            request_id="nonexistent_id",
            approver_id="admin_user",
            approver_role=UserRole.ADMIN,
        )

        assert success is False

    # ==============================================================================
    # AUDIT LOGGING TESTS
    # ==============================================================================

    def test_audit_logging_for_allowed_request(self, enforcer, sample_artemis_request):
        """Test that audit logs are created for allowed requests"""
        result = enforcer.validate_request(sample_artemis_request)

        assert result.audit_logged is True
        assert len(enforcer.audit_logs) == 1

        log = enforcer.audit_logs[0]
        assert log.request_id == sample_artemis_request.id
        assert log.domain == MemoryDomain.ARTEMIS
        assert log.operation == OperationType.CODE_GENERATION
        assert log.user_id == "dev_user_123"
        assert log.user_role == UserRole.DEVELOPER
        assert log.allowed is True
        assert log.details["reason"] == "Request validated successfully"

    def test_audit_logging_for_denied_request(self, enforcer):
        """Test that audit logs are created for denied requests"""
        request = DomainRequest(
            id="test_req_017",
            user_id="sales_user",
            user_role=UserRole.SALES,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_GENERATION,
        )

        result = enforcer.validate_request(request)

        assert result.audit_logged is True
        assert len(enforcer.audit_logs) == 1

        log = enforcer.audit_logs[0]
        assert log.allowed is False
        assert "no access" in log.details["reason"]

    def test_audit_logging_for_violations(self, enforcer):
        """Test that violations are logged with higher severity"""
        request = DomainRequest(
            id="test_req_018",
            user_id="dev_user",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.SOPHIA,
            operation_type=OperationType.CODE_GENERATION,  # Wrong domain!
        )

        with patch("app.core.domain_enforcer.logger") as mock_logger:
            result = enforcer.validate_request(request)

            # Check that warning was logged for violation
            mock_logger.warning.assert_called()
            warning_message = mock_logger.warning.call_args[0][0]
            assert "DOMAIN VIOLATION" in warning_message
            assert "dev_user" in warning_message
            assert "CODE_GENERATION" in warning_message.upper()

    def test_get_audit_logs_with_filtering(self, enforcer):
        """Test retrieving audit logs with various filters"""
        # Create multiple requests to generate logs
        requests = [
            DomainRequest(
                id=f"req_{i}",
                user_id=f"user_{i % 2}",  # Alternating users
                user_role=(
                    UserRole.DEVELOPER if i % 2 == 0 else UserRole.BUSINESS_ANALYST
                ),
                target_domain=(
                    MemoryDomain.ARTEMIS if i % 2 == 0 else MemoryDomain.SOPHIA
                ),
                operation_type=(
                    OperationType.CODE_REVIEW
                    if i % 2 == 0
                    else OperationType.BUSINESS_ANALYSIS
                ),
            )
            for i in range(5)
        ]

        for req in requests:
            enforcer.validate_request(req)

        # Test filtering by domain
        artemis_logs = enforcer.get_audit_logs(domain=MemoryDomain.ARTEMIS)
        assert all(log.domain == MemoryDomain.ARTEMIS for log in artemis_logs)

        # Test filtering by user
        user_0_logs = enforcer.get_audit_logs(user_id="user_0")
        assert all(log.user_id == "user_0" for log in user_0_logs)

        # Test filtering by allowed status
        allowed_logs = enforcer.get_audit_logs(allowed=True)
        assert all(log.allowed is True for log in allowed_logs)

        # Test limit
        limited_logs = enforcer.get_audit_logs(limit=2)
        assert len(limited_logs) <= 2

    def test_disable_audit_logging(self, enforcer, sample_artemis_request):
        """Test that audit logging can be disabled"""
        enforcer.enable_audit_logging = False

        result = enforcer.validate_request(sample_artemis_request)

        assert result.audit_logged is False
        assert len(enforcer.audit_logs) == 0

    def test_clear_old_audit_logs(self, enforcer):
        """Test clearing old audit logs"""
        # Create logs with different timestamps
        now = datetime.now(timezone.utc)

        # Create old log (31 days ago)
        old_log = DomainAuditLog(
            id="old_log",
            request_id="old_req",
            domain=MemoryDomain.ARTEMIS,
            operation=OperationType.CODE_REVIEW,
            user_id="user",
            user_role=UserRole.DEVELOPER,
            allowed=True,
            timestamp=(now - timedelta(days=31)).isoformat(),
        )

        # Create recent log
        recent_log = DomainAuditLog(
            id="recent_log",
            request_id="recent_req",
            domain=MemoryDomain.SOPHIA,
            operation=OperationType.BUSINESS_ANALYSIS,
            user_id="user",
            user_role=UserRole.BUSINESS_ANALYST,
            allowed=True,
            timestamp=now.isoformat(),
        )

        enforcer.audit_logs = [old_log, recent_log]

        # Clear logs older than 30 days
        removed_count = enforcer.clear_audit_logs(older_than_days=30)

        assert removed_count == 1
        assert len(enforcer.audit_logs) == 1
        assert enforcer.audit_logs[0].id == "recent_log"

    # ==============================================================================
    # STATISTICS AND REPORTING TESTS
    # ==============================================================================

    def test_validation_statistics_tracking(self, enforcer):
        """Test that validation statistics are properly tracked"""
        # Initial state
        stats = enforcer.get_validation_statistics()
        assert stats["total_requests"] == 0
        assert stats["approval_rate"] == 0.0

        # Make some requests
        allowed_request = DomainRequest(
            id="allowed",
            user_id="dev",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_GENERATION,
        )

        denied_request = DomainRequest(
            id="denied",
            user_id="sales",
            user_role=UserRole.SALES,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_GENERATION,
        )

        violation_request = DomainRequest(
            id="violation",
            user_id="dev",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.SOPHIA,
            operation_type=OperationType.CODE_GENERATION,
        )

        enforcer.validate_request(allowed_request)
        enforcer.validate_request(denied_request)
        enforcer.validate_request(violation_request)

        # Check updated statistics
        stats = enforcer.get_validation_statistics()
        assert stats["total_requests"] == 3
        assert stats["allowed_requests"] == 1
        assert stats["denied_requests"] == 2
        assert stats["violations_detected"] == 1
        assert stats["approval_rate"] == 1 / 3
        assert stats["violation_rate"] == 1 / 3

    def test_reset_statistics(self, enforcer):
        """Test resetting validation statistics"""
        # Make some requests
        request = DomainRequest(
            id="test",
            user_id="dev",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.ARTEMIS,
            operation_type=OperationType.CODE_GENERATION,
        )

        enforcer.validate_request(request)
        assert enforcer.validation_stats["total_requests"] == 1

        # Reset
        enforcer.reset_statistics()

        assert enforcer.validation_stats["total_requests"] == 0
        assert enforcer.validation_stats["allowed_requests"] == 0
        assert enforcer.validation_stats["denied_requests"] == 0

    def test_get_domain_summary(self, enforcer):
        """Test getting domain boundary summary"""
        summary = enforcer.get_domain_summary()

        # Check Artemis domain
        assert (
            summary["artemis_domain"]["description"] == "Repository and code operations"
        )
        assert OperationType.CODE_GENERATION in summary["artemis_domain"]["operations"]
        assert UserRole.DEVELOPER.value in summary["artemis_domain"]["allowed_roles"]
        assert UserRole.ADMIN.value in summary["artemis_domain"]["allowed_roles"]

        # Check Sophia domain
        assert summary["sophia_domain"]["description"] == "Business operations"
        assert OperationType.BUSINESS_ANALYSIS in summary["sophia_domain"]["operations"]
        assert (
            UserRole.BUSINESS_ANALYST.value in summary["sophia_domain"]["allowed_roles"]
        )

        # Check shared operations
        assert OperationType.MONITORING in summary["shared_operations"]

        # Check settings
        assert summary["cross_domain_enabled"] is True
        assert summary["audit_logging_enabled"] is True

    # ==============================================================================
    # CONVENIENCE FUNCTION TESTS
    # ==============================================================================

    def test_validate_domain_request_convenience_function():
        """Test the convenience function for validating domain requests"""
        result = validate_domain_request(
            user_id="test_user",
            user_role=UserRole.DEVELOPER,
            target_domain=MemoryDomain.ARTEMIS,
            operation=OperationType.CODE_GENERATION,
            resource_path="/src/main.py",
            metadata={"test": True},
        )

        assert isinstance(result, ValidationResult)
        assert result.allowed is True

    def test_request_cross_domain_access_convenience_function():
        """Test the convenience function for requesting cross-domain access"""
        request = request_cross_domain_access(
            source=MemoryDomain.ARTEMIS,
            target=MemoryDomain.SOPHIA,
            operation=OperationType.BUSINESS_ANALYSIS,
            user_id="dev_user",
            user_role=UserRole.DEVELOPER,
            justification="Need business context",
        )

        assert isinstance(request, CrossDomainRequest)
        assert request.source_domain == MemoryDomain.ARTEMIS
        assert request.target_domain == MemoryDomain.SOPHIA

    def test_get_domain_access_summary_convenience_function():
        """Test the convenience function for getting domain access summary"""
        # Test developer role
        dev_summary = get_domain_access_summary(UserRole.DEVELOPER)

        assert dev_summary["role"] == UserRole.DEVELOPER.value
        assert dev_summary["artemis_access"] == AccessLevel.FULL.value
        assert dev_summary["sophia_access"] == AccessLevel.READ.value
        assert OperationType.CODE_GENERATION.value in dev_summary["allowed_operations"]
        assert (
            OperationType.BUSINESS_ANALYSIS.value in dev_summary["allowed_operations"]
        )
        assert (
            OperationType.REVENUE_FORECASTING.value
            not in dev_summary["allowed_operations"]
        )

        # Test business analyst role
        analyst_summary = get_domain_access_summary(UserRole.BUSINESS_ANALYST)

        assert analyst_summary["artemis_access"] == AccessLevel.READ.value
        assert analyst_summary["sophia_access"] == AccessLevel.FULL.value
        assert (
            OperationType.REVENUE_FORECASTING.value
            in analyst_summary["allowed_operations"]
        )
        assert (
            OperationType.CODE_GENERATION.value
            not in analyst_summary["allowed_operations"]
        )

    # ==============================================================================
    # EDGE CASES AND ERROR HANDLING
    # ==============================================================================

    def test_operation_access_level_mapping(self, enforcer):
        """Test correct access level requirements for different operations"""
        # Write operations
        assert (
            enforcer._get_required_access_level(OperationType.CODE_GENERATION)
            == AccessLevel.WRITE
        )
        assert (
            enforcer._get_required_access_level(OperationType.REVENUE_FORECASTING)
            == AccessLevel.WRITE
        )
        assert (
            enforcer._get_required_access_level(OperationType.OKR_TRACKING)
            == AccessLevel.WRITE
        )

        # Execute operations
        assert (
            enforcer._get_required_access_level(OperationType.CI_CD_OPERATIONS)
            == AccessLevel.EXECUTE
        )
        assert (
            enforcer._get_required_access_level(OperationType.SECURITY_SCANNING)
            == AccessLevel.EXECUTE
        )

        # Read operations
        assert (
            enforcer._get_required_access_level(OperationType.CODE_REVIEW)
            == AccessLevel.READ
        )
        assert (
            enforcer._get_required_access_level(OperationType.BUSINESS_ANALYSIS)
            == AccessLevel.READ
        )

    def test_has_sufficient_access_hierarchy(self, enforcer):
        """Test access level hierarchy checking"""
        # FULL has access to everything
        assert (
            enforcer._has_sufficient_access(AccessLevel.FULL, AccessLevel.WRITE) is True
        )
        assert (
            enforcer._has_sufficient_access(AccessLevel.FULL, AccessLevel.EXECUTE)
            is True
        )
        assert (
            enforcer._has_sufficient_access(AccessLevel.FULL, AccessLevel.READ) is True
        )

        # WRITE has access to WRITE and below
        assert (
            enforcer._has_sufficient_access(AccessLevel.WRITE, AccessLevel.WRITE)
            is True
        )
        assert (
            enforcer._has_sufficient_access(AccessLevel.WRITE, AccessLevel.EXECUTE)
            is True
        )
        assert (
            enforcer._has_sufficient_access(AccessLevel.WRITE, AccessLevel.READ) is True
        )
        assert (
            enforcer._has_sufficient_access(AccessLevel.WRITE, AccessLevel.FULL)
            is False
        )

        # READ has access only to READ
        assert (
            enforcer._has_sufficient_access(AccessLevel.READ, AccessLevel.READ) is True
        )
        assert (
            enforcer._has_sufficient_access(AccessLevel.READ, AccessLevel.WRITE)
            is False
        )
        assert (
            enforcer._has_sufficient_access(AccessLevel.READ, AccessLevel.EXECUTE)
            is False
        )

        # NONE has no access
        assert (
            enforcer._has_sufficient_access(AccessLevel.NONE, AccessLevel.READ) is False
        )

    def test_get_correct_domain_for_operations(self, enforcer):
        """Test getting the correct domain for operations"""
        # Artemis operations
        assert (
            enforcer._get_correct_domain(OperationType.CODE_GENERATION)
            == MemoryDomain.ARTEMIS
        )
        assert (
            enforcer._get_correct_domain(OperationType.SECURITY_SCANNING)
            == MemoryDomain.ARTEMIS
        )

        # Sophia operations
        assert (
            enforcer._get_correct_domain(OperationType.BUSINESS_ANALYSIS)
            == MemoryDomain.SOPHIA
        )
        assert (
            enforcer._get_correct_domain(OperationType.OKR_TRACKING)
            == MemoryDomain.SOPHIA
        )

        # Shared operations return None (allowed in both)
        assert enforcer._get_correct_domain(OperationType.MONITORING) is None

    def test_global_domain_enforcer_instance():
        """Test that global domain enforcer instance is available"""
        assert domain_enforcer is not None
        assert isinstance(domain_enforcer, DomainEnforcer)
        assert domain_enforcer.enable_audit_logging is True
