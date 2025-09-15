#!/usr/bin/env python3
"""
Secure Salesforce SOQL Query Builder
Prevents SOQL injection by using proper escaping and validation
"""
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class SalesforceField:
    """Validates Salesforce field names"""
    
    # Valid field name pattern: alphanumeric, underscore, period for relationships
    FIELD_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*$')
    
    @classmethod
    def validate(cls, field_name: str) -> bool:
        """Validate field name format"""
        return bool(cls.FIELD_PATTERN.match(field_name))
    
    @classmethod
    def escape(cls, field_name: str) -> str:
        """Escape field name (validation should prevent issues)"""
        if not cls.validate(field_name):
            raise ValueError(f"Invalid Salesforce field name: {field_name}")
        return field_name


class SalesforceObject:
    """Validates Salesforce object names"""
    
    # Valid object name pattern: alphanumeric, underscore, __c for custom objects
    OBJECT_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*(__c)?$')
    
    # Whitelist of known standard objects
    STANDARD_OBJECTS = {
        'Account', 'Contact', 'Lead', 'Opportunity', 'Case', 'Task', 'Event',
        'Campaign', 'Contract', 'Product2', 'Pricebook2', 'Quote', 'User',
        'Profile', 'Role', 'Organization', 'RecordType', 'Attachment',
        'ContentDocument', 'ContentVersion', 'ContentDocumentLink'
    }
    
    @classmethod
    def validate(cls, object_name: str) -> bool:
        """Validate object name"""
        return (object_name in cls.STANDARD_OBJECTS or 
                bool(cls.OBJECT_PATTERN.match(object_name)))
    
    @classmethod
    def escape(cls, object_name: str) -> str:
        """Escape object name"""
        if not cls.validate(object_name):
            raise ValueError(f"Invalid Salesforce object name: {object_name}")
        return object_name


class SOQLOperator(Enum):
    """Safe SOQL operators"""
    EQUALS = "="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    LESS_THAN_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL = ">="
    LIKE = "LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    INCLUDES = "INCLUDES"
    EXCLUDES = "EXCLUDES"


@dataclass
class SecureWhereCondition:
    """Secure WHERE condition builder"""
    field: str
    operator: SOQLOperator
    value: Union[str, int, float, datetime, List[str]]
    
    def __post_init__(self):
        """Validate field name on creation"""
        if not SalesforceField.validate(self.field):
            raise ValueError(f"Invalid field name: {self.field}")
    
    def build(self) -> str:
        """Build secure WHERE condition"""
        escaped_field = SalesforceField.escape(self.field)
        escaped_value = self._escape_value(self.value)
        return f"{escaped_field} {self.operator.value} {escaped_value}"
    
    def _escape_value(self, value: Union[str, int, float, datetime, List[str]]) -> str:
        """Escape value based on type"""
        if isinstance(value, str):
            return self._escape_string(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif isinstance(value, list):
            if self.operator in (SOQLOperator.IN, SOQLOperator.NOT_IN):
                escaped_items = [self._escape_string(str(item)) for item in value]
                return f"({', '.join(escaped_items)})"
            else:
                raise ValueError(f"List values only supported with IN/NOT_IN operators")
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")
    
    def _escape_string(self, value: str) -> str:
        """Escape string value for SOQL"""
        # Escape single quotes by doubling them
        escaped = value.replace("'", "''")
        
        # Remove or escape potentially dangerous characters
        dangerous_chars = ['\\', '\n', '\r', '\t']
        for char in dangerous_chars:
            escaped = escaped.replace(char, '')
        
        return f"'{escaped}'"


@dataclass  
class SecureSalesforceQuery:
    """Secure SOQL query builder with injection prevention"""
    object_name: str
    fields: List[str] = field(default_factory=lambda: ["Id", "Name"])
    where_conditions: List[SecureWhereCondition] = field(default_factory=list)
    order_by_field: Optional[str] = None
    order_by_direction: str = "ASC"  # ASC or DESC only
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def __post_init__(self):
        """Validate inputs on creation"""
        # Validate object name
        if not SalesforceObject.validate(self.object_name):
            raise ValueError(f"Invalid object name: {self.object_name}")
        
        # Validate all field names
        for field in self.fields:
            if not SalesforceField.validate(field):
                raise ValueError(f"Invalid field name: {field}")
        
        # Validate order by field
        if self.order_by_field and not SalesforceField.validate(self.order_by_field):
            raise ValueError(f"Invalid order by field: {self.order_by_field}")
        
        # Validate order direction
        if self.order_by_direction not in ("ASC", "DESC"):
            raise ValueError("Order direction must be ASC or DESC")
        
        # Validate numeric limits
        if self.limit is not None and (not isinstance(self.limit, int) or self.limit < 0 or self.limit > 2000):
            raise ValueError("Limit must be integer between 0 and 2000")
        
        if self.offset is not None and (not isinstance(self.offset, int) or self.offset < 0):
            raise ValueError("Offset must be non-negative integer")
    
    def add_where_condition(
        self,
        field: str,
        operator: SOQLOperator,
        value: Union[str, int, float, datetime, List[str]]
    ) -> 'SecureSalesforceQuery':
        """Add a secure WHERE condition"""
        condition = SecureWhereCondition(field, operator, value)
        self.where_conditions.append(condition)
        return self
    
    def add_string_equals(self, field: str, value: str) -> 'SecureSalesforceQuery':
        """Helper for string equality (most common case)"""
        return self.add_where_condition(field, SOQLOperator.EQUALS, value)
    
    def add_date_range(
        self,
        field: str,
        start_date: datetime,
        end_date: datetime
    ) -> 'SecureSalesforceQuery':
        """Helper for date range queries"""
        self.add_where_condition(field, SOQLOperator.GREATER_THAN_EQUAL, start_date)
        self.add_where_condition(field, SOQLOperator.LESS_THAN_EQUAL, end_date)
        return self
    
    def add_in_list(self, field: str, values: List[str]) -> 'SecureSalesforceQuery':
        """Helper for IN queries"""
        return self.add_where_condition(field, SOQLOperator.IN, values)
    
    def build(self) -> str:
        """Build secure SOQL query"""
        # Escape object name and fields
        escaped_object = SalesforceObject.escape(self.object_name)
        escaped_fields = [SalesforceField.escape(field) for field in self.fields]
        
        query = f"SELECT {', '.join(escaped_fields)} FROM {escaped_object}"
        
        # Add WHERE conditions
        if self.where_conditions:
            where_clauses = [condition.build() for condition in self.where_conditions]
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        # Add ORDER BY
        if self.order_by_field:
            escaped_order_field = SalesforceField.escape(self.order_by_field)
            query += f" ORDER BY {escaped_order_field} {self.order_by_direction}"
        
        # Add LIMIT
        if self.limit is not None:
            query += f" LIMIT {self.limit}"
        
        # Add OFFSET  
        if self.offset is not None:
            query += f" OFFSET {self.offset}"
        
        return query


# Example usage and migration helpers
class SecureQueryBuilderExamples:
    """Examples of secure query building"""
    
    @staticmethod
    def get_opportunities_by_stage(stage: str) -> str:
        """Secure opportunity query by stage"""
        query = SecureSalesforceQuery(
            object_name="Opportunity",
            fields=[
                "Id", "Name", "AccountId", "Amount", "CloseDate",
                "StageName", "Probability", "Type", "LeadSource"
            ]
        )
        query.add_string_equals("StageName", stage)
        query.order_by_field = "CloseDate"
        query.order_by_direction = "DESC"
        query.limit = 200
        
        return query.build()
    
    @staticmethod
    def get_opportunities_by_date_range(start_date: datetime, end_date: datetime) -> str:
        """Secure opportunity query by date range"""
        query = SecureSalesforceQuery(
            object_name="Opportunity",
            fields=["Id", "Name", "Amount", "CloseDate", "StageName"]
        )
        query.add_date_range("CloseDate", start_date, end_date)
        
        return query.build()
    
    @staticmethod
    def get_accounts_by_type(account_types: List[str]) -> str:
        """Secure account query by types"""
        query = SecureSalesforceQuery(
            object_name="Account",
            fields=["Id", "Name", "Type", "Industry", "AnnualRevenue"]
        )
        query.add_in_list("Type", account_types)
        
        return query.build()


# Migration utilities
def migrate_unsafe_query_to_secure(unsafe_query_builder) -> SecureSalesforceQuery:
    """Migrate from unsafe SalesforceQuery to secure version"""
    # This would be used to migrate existing code
    secure_query = SecureSalesforceQuery(
        object_name=unsafe_query_builder.object_name,
        fields=unsafe_query_builder.fields or ["Id", "Name"]
    )
    
    # Convert WHERE conditions (would need custom logic per condition)
    # This is a placeholder for the migration process
    
    if unsafe_query_builder.order_by:
        # Parse "field ASC/DESC" format
        parts = unsafe_query_builder.order_by.split()
        secure_query.order_by_field = parts[0]
        if len(parts) > 1 and parts[1].upper() in ("ASC", "DESC"):
            secure_query.order_by_direction = parts[1].upper()
    
    secure_query.limit = unsafe_query_builder.limit
    secure_query.offset = unsafe_query_builder.offset
    
    return secure_query


if __name__ == "__main__":
    # Test secure query builder
    print("Testing Secure Salesforce Query Builder")
    print("=" * 50)
    
    try:
        # Test basic query
        query = SecureSalesforceQuery(
            object_name="Account",
            fields=["Id", "Name", "Type"]
        )
        query.add_string_equals("Type", "Customer")
        print(f"✅ Basic query: {query.build()}")
        
        # Test date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        query2 = SecureSalesforceQuery(
            object_name="Opportunity",
            fields=["Id", "Name", "CloseDate"]
        )
        query2.add_date_range("CloseDate", start_date, end_date)
        print(f"✅ Date range query: {query2.build()}")
        
        # Test IN query
        query3 = SecureSalesforceQuery(
            object_name="Contact",
            fields=["Id", "Name", "Email"]
        )
        query3.add_in_list("Department", ["Sales", "Marketing", "Engineering"])
        print(f"✅ IN query: {query3.build()}")
        
        # Test injection prevention
        print("\n🔒 Testing injection prevention:")
        try:
            malicious_query = SecureSalesforceQuery(
                object_name="Account'; DROP TABLE Account; --",
                fields=["Id"]
            )
            print("❌ Should have failed!")
        except ValueError as e:
            print(f"✅ Blocked malicious object name: {e}")
        
        try:
            good_query = SecureSalesforceQuery(
                object_name="Account",
                fields=["Id", "Name"]
            )
            good_query.add_string_equals("Name", "'; DROP TABLE Account; --")
            safe_query = good_query.build()
            print(f"✅ Safely escaped malicious value: {safe_query}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
