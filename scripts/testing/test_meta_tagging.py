#!/usr/bin/env python3
"""
Test script for the meta-tagging system.
This script provides a simple way to test the meta-tagging components
with sample code and verify the system is working correctly.
"""
import asyncio
import os
import sys
# Add the app directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from app.scaffolding import (
        AIHintsPipeline,
        AutoTagger,
        Complexity,
        MetaTag,
        MetaTagRegistry,
        SemanticClassifier,
        SemanticRole,
        detailed_analysis,
        generate_ai_hints,
    )
except ImportError as e:
    print(f"Error importing meta-tagging modules: {e}")
    print("Please ensure the scaffolding package is properly installed")
    sys.exit(1)
# Sample code for testing
SAMPLE_ORCHESTRATOR = '''
import asyncio
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
class UserOrchestrator:
    """
    Orchestrates user management operations across multiple services.
    This orchestrator coordinates user creation, validation, and notification
    processes while maintaining data consistency across systems.
    """
    def __init__(self, user_service, email_service, audit_service):
        self.user_service = user_service
        self.email_service = email_service
        self.audit_service = audit_service
        self.logger = logging.getLogger(__name__)
    async def create_user_workflow(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete user creation workflow with validation and notifications.
        Args:
            user_data: Dictionary containing user information
        Returns:
            Dict containing creation results and user ID
        Raises:
            ValidationError: If user data is invalid
            ServiceError: If external services fail
        """
        try:
            # TODO: Add input validation
            self.logger.info(f"Starting user creation workflow for {user_data.get('email')}")
            # Step 1: Validate user data
            if not self._validate_user_data(user_data):
                raise ValidationError("Invalid user data provided")
            # Step 2: Check for duplicate users
            existing_user = await self.user_service.find_by_email(user_data['email'])
            if existing_user:
                raise DuplicateUserError(f"User already exists: {user_data['email']}")
            # Step 3: Create user account
            user_id = await self.user_service.create_user(user_data)
            # Step 4: Send welcome email
            await self.email_service.send_welcome_email(user_data['email'], user_id)
            # Step 5: Log audit event
            await self.audit_service.log_user_creation(user_id, user_data)
            self.logger.info(f"User creation completed successfully: {user_id}")
            return {
                'success': True,
                'user_id': user_id,
                'message': 'User created successfully'
            }
        except Exception as e:
            self.logger.error(f"User creation failed: {str(e)}")
            # TODO: Implement rollback logic
            raise
    def _validate_user_data(self, user_data: Dict[str, Any]) -> bool:
        """Validate user data before processing."""
        required_fields = ['email', 'first_name', 'last_name']
        # Check required fields
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                return False
        # Validate email format
        email = user_data.get('email', '')
        if '@' not in email or '.' not in email:
            return False
        return True
    async def bulk_user_creation(self, users_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process multiple user creations in batch.
        This method has potential performance issues with sequential processing.
        """
        results = []
        failed_users = []
        # FIXME: This is inefficient - should use concurrent processing
        for user_data in users_data:
            try:
                result = await self.create_user_workflow(user_data)
                results.append(result)
            except Exception as e:
                failed_users.append({
                    'user_data': user_data,
                    'error': str(e)
                })
        return {
            'successful_creations': len(results),
            'failed_creations': len(failed_users),
            'results': results,
            'failures': failed_users
        }
'''
SAMPLE_GATEWAY = '''
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
app = FastAPI(title="User Management API", version="1.0.0")
security = HTTPBearer()
class UserCreateRequest(BaseModel):
    """Request model for user creation."""
    email: EmailStr
    first_name: str
    last_name: str
    password: str  # TODO: This should be hashed
    phone: Optional[str] = None
class UserResponse(BaseModel):
    """Response model for user data."""
    user_id: str
    email: str
    first_name: str
    last_name: str
    created_at: str
@app.post("/api/v1/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_request: UserCreateRequest,
                     token: str = Depends(security)) -> UserResponse:
    """
    Create a new user account.
    This endpoint creates a new user and returns the user information.
    Authentication is required via Bearer token.
    """
    try:
        # Validate authentication token
        user_info = verify_token(token.credentials)
        # TODO: Add rate limiting
        # TODO: Add request validation
        # Call orchestrator to handle user creation
        orchestrator = get_user_orchestrator()
        result = await orchestrator.create_user_workflow(user_request.dict())
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        # Return user data
        return UserResponse(
            user_id=result['user_id'],
            email=user_request.email,
            first_name=user_request.first_name,
            last_name=user_request.last_name,
            created_at="2024-01-01T00:00:00Z"  # This should be dynamic
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
def verify_token(token: str) -> dict:
    """Verify JWT token and return user information."""
    # FIXME: Secret key should come from environment
    secret_key = "your-secret-key"
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
'''
SAMPLE_UTILITY = r'''
import hashlib
import secrets
import re
from typing import Optional, Dict, Any
class SecurityUtils:
    """Utility functions for security operations."""
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """
        Hash a password using SHA-256 with salt.
        WARNING: SHA-256 is not recommended for password hashing.
        Consider using bcrypt, scrypt, or Argon2 instead.
        """
        if not salt:
            salt = secrets.token_hex(16)
        # This is a security vulnerability - using weak hashing
        hashed = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return {
            'hash': hashed,
            'salt': salt
        }
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validate password meets minimum security requirements.
        Requirements:
        - At least 8 characters
        - Contains uppercase and lowercase letters
        - Contains at least one digit
        - Contains at least one special character
        """
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        return True
    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """
        Sanitize user input to prevent injection attacks.
        This is a basic implementation - use proper sanitization libraries
        for production code.
        """
        if not isinstance(user_input, str):
            return ""
        # Remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript']
        sanitized = user_input
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive data in dictionaries for logging.
        TODO: Make the sensitive fields configurable
        """
        sensitive_fields = ['password', 'secret', 'token', 'key', 'ssn']
        masked_data = data.copy()
        for key, value in masked_data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                if isinstance(value, str) and len(value) > 4:
                    masked_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    masked_data[key] = '***'
        return masked_data
'''
async def test_basic_functionality():
    """Test basic functionality of the meta-tagging system."""
    print("Testing Meta-Tagging System")
    print("=" * 50)
    # Test 1: Semantic Classification
    print("\n1. Testing Semantic Classification...")
    classifier = SemanticClassifier()
    # Test orchestrator classification
    orchestrator_result = classifier.classify_component(
        "UserOrchestrator", "user_orchestrator.py", SAMPLE_ORCHESTRATOR
    )
    print(f"   Orchestrator classified as: {orchestrator_result.semantic_role.value}")
    print(f"   Confidence: {orchestrator_result.confidence:.2f}")
    # Test gateway classification
    gateway_result = classifier.classify_component(
        "create_user", "user_api.py", SAMPLE_GATEWAY
    )
    print(f"   Gateway classified as: {gateway_result.semantic_role.value}")
    print(f"   Confidence: {gateway_result.confidence:.2f}")
    # Test utility classification
    utility_result = classifier.classify_component(
        "SecurityUtils", "security_utils.py", SAMPLE_UTILITY
    )
    print(f"   Utility classified as: {utility_result.semantic_role.value}")
    print(f"   Confidence: {utility_result.confidence:.2f}")
    # Test 2: Auto-Tagging
    print("\n2. Testing Auto-Tagging...")
    registry = MetaTagRegistry("test_registry.json")
    tagger = AutoTagger(registry)
    # Create temporary test files
    test_files = {
        "test_orchestrator.py": SAMPLE_ORCHESTRATOR,
        "test_gateway.py": SAMPLE_GATEWAY,
        "test_utility.py": SAMPLE_UTILITY,
    }
    for filename, content in test_files.items():
        with open(filename, "w") as f:
            f.write(content)
        tags = await tagger.tag_file(filename)
        print(f"   {filename}: {len(tags)} tags created")
        for tag in tags:
            print(f"     - {tag.component_name} ({tag.semantic_role.value})")
    # Test 3: AI Hints Generation
    print("\n3. Testing AI Hints Generation...")
    hints_pipeline = AIHintsPipeline()
    # Create a sample meta-tag
    sample_tag = MetaTag(
        file_path="test_orchestrator.py",
        component_name="UserOrchestrator",
        semantic_role=SemanticRole.ORCHESTRATOR,
        complexity=Complexity.MODERATE,
    )
    hints = await generate_ai_hints(SAMPLE_ORCHESTRATOR, sample_tag)
    print(f"   Generated {len(hints)} hints for UserOrchestrator:")
    for hint in hints[:5]:  # Show first 5 hints
        print(f"     - {hint.title} ({hint.severity.name})")
    # Test 4: Registry Operations
    print("\n4. Testing Registry Operations...")
    stats = registry.stats()
    print(f"   Registry contains {stats['total_tags']} tags")
    print(f"   Files covered: {stats['files_covered']}")
    print(f"   Role distribution: {stats['role_distribution']}")
    # Clean up test files
    for filename in test_files:
        if os.path.exists(filename):
            os.remove(filename)
    if os.path.exists("test_registry.json"):
        os.remove("test_registry.json")
    print("\n5. Testing Detailed Analysis...")
    analysis = detailed_analysis("SecurityUtils", "security_utils.py", SAMPLE_UTILITY)
    print("   Security Utils Analysis:")
    print(f"   - Role: {analysis['classification']['semantic_role']}")
    print(f"   - Complexity: {analysis['complexity']['level']}")
    print(f"   - Risk Level: {analysis['risk']['level']}")
    print(f"   - Capabilities: {list(analysis['capabilities'].keys())}")
    print("\n" + "=" * 50)
    print("All tests completed successfully!")
    return True
async def demonstrate_usage():
    """Demonstrate practical usage of the meta-tagging system."""
    print("\nDemonstrating Practical Usage")
    print("=" * 50)
    # Example: Analyzing a complex component
    print("\n1. Complex Component Analysis:")
    analysis = detailed_analysis(
        "UserOrchestrator", "user_orchestrator.py", SAMPLE_ORCHESTRATOR
    )
    print("   Component: UserOrchestrator")
    print(f"   Role: {analysis['classification']['semantic_role']}")
    print(f"   Complexity: {analysis['complexity']['level']}")
    print(f"   Risk: {analysis['risk']['level']}")
    print(f"   Confidence: {analysis['overall_confidence']:.2f}")
    print("\n   Capabilities detected:")
    for capability, confidence in analysis["capabilities"].items():
        print(f"     - {capability}: {confidence:.2f}")
    print("\n   Risk factors:")
    for factor in analysis["risk"]["factors"][:3]:
        print(f"     - {factor}")
    # Example: Priority recommendations
    print("\n2. Priority Assessment:")
    priority_info = analysis["priority"]
    print(f"   Priority Level: {priority_info['level']}")
    print("   Reasoning:")
    for reason in priority_info["reasoning"]:
        print(f"     - {reason}")
    # Example: Generating actionable hints
    print("\n3. Actionable Recommendations:")
    sample_tag = MetaTag(
        file_path="user_orchestrator.py",
        component_name="UserOrchestrator",
        semantic_role=SemanticRole.ORCHESTRATOR,
        complexity=Complexity.MODERATE,
    )
    hints_pipeline = AIHintsPipeline()
    all_hints = await hints_pipeline.generate_hints(SAMPLE_ORCHESTRATOR, sample_tag)
    # Filter and prioritize hints
    from app.scaffolding.ai_hints import Severity
    high_priority_hints = hints_pipeline.filter_hints(
        all_hints, min_severity=Severity.MEDIUM, max_hints=5
    )
    for i, hint in enumerate(high_priority_hints, 1):
        print(f"\n   {i}. {hint.title}")
        print(f"      Type: {hint.hint_type.value.title()}")
        print(f"      Severity: {hint.severity.name}")
        print(f"      Action: {hint.suggested_action}")
        print(f"      Effort: {hint.estimated_effort}")
    # Generate summary report
    summary = hints_pipeline.generate_summary_report(all_hints)
    print("\n4. Summary Report:")
    print(f"   Total Hints: {summary['total_hints']}")
    print(f"   Critical Issues: {summary['critical_issues']}")
    print(f"   High Priority: {summary['high_priority']}")
    print(f"   Estimated Effort: {summary['estimated_total_effort']}")
    print("\n" + "=" * 50)
    print("Usage demonstration completed!")
def main():
    """Main test function."""
    async def run_tests():
        try:
            await test_basic_functionality()
            await demonstrate_usage()
            print("\nAll tests passed! The meta-tagging system is working correctly.")
            return 0
        except Exception as e:
            print(f"\nTest failed with error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    return asyncio.run(run_tests())
if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
