"""
Cross-Platform Correlation Agent for SOPHIA Intel
Correlates data across 11 Pay Ready data sources for comprehensive business intelligence
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from celery import Task
from .celery_app import celery_app
from ..database.unified_knowledge_repository import UnifiedKnowledgeRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrossPlatformCorrelationAgent:
    """Agent for correlating data across multiple platforms"""
    
    def __init__(self):
        self.knowledge_repo = UnifiedKnowledgeRepository()
        
        # Pay Ready data sources configuration
        self.data_sources = {
            'salesforce': {
                'priority': 1,
                'data_types': ['leads', 'opportunities', 'accounts', 'contacts'],
                'correlation_keys': ['email', 'company_name', 'phone', 'account_id'],
                'business_impact': 'high'
            },
            'gong': {
                'priority': 2,
                'data_types': ['calls', 'meetings', 'conversations', 'deals'],
                'correlation_keys': ['email', 'deal_id', 'account_name', 'participant_email'],
                'business_impact': 'high'
            },
            'hubspot': {
                'priority': 3,
                'data_types': ['contacts', 'companies', 'deals', 'tickets'],
                'correlation_keys': ['email', 'company_id', 'contact_id', 'deal_id'],
                'business_impact': 'high'
            },
            'intercom': {
                'priority': 4,
                'data_types': ['conversations', 'users', 'events', 'segments'],
                'correlation_keys': ['user_id', 'email', 'company_id', 'conversation_id'],
                'business_impact': 'medium'
            },
            'looker': {
                'priority': 5,
                'data_types': ['dashboards', 'reports', 'metrics', 'kpis'],
                'correlation_keys': ['metric_name', 'dimension', 'date_range'],
                'business_impact': 'high'
            },
            'slack': {
                'priority': 6,
                'data_types': ['messages', 'channels', 'users', 'threads'],
                'correlation_keys': ['user_id', 'channel_id', 'thread_id', 'mention'],
                'business_impact': 'medium'
            },
            'asana': {
                'priority': 7,
                'data_types': ['tasks', 'projects', 'teams', 'goals'],
                'correlation_keys': ['project_id', 'task_id', 'assignee_id', 'team_id'],
                'business_impact': 'medium'
            },
            'linear': {
                'priority': 8,
                'data_types': ['issues', 'projects', 'cycles', 'teams'],
                'correlation_keys': ['issue_id', 'project_id', 'assignee_id', 'cycle_id'],
                'business_impact': 'medium'
            },
            'factor_ai': {
                'priority': 9,
                'data_types': ['analytics', 'insights', 'predictions', 'models'],
                'correlation_keys': ['model_id', 'prediction_id', 'metric_name'],
                'business_impact': 'high'
            },
            'notion': {
                'priority': 10,
                'data_types': ['pages', 'databases', 'blocks', 'properties'],
                'correlation_keys': ['page_id', 'database_id', 'property_name'],
                'business_impact': 'medium'
            },
            'netsuite': {
                'priority': 11,
                'data_types': ['transactions', 'customers', 'items', 'financial_records'],
                'correlation_keys': ['customer_id', 'transaction_id', 'item_id', 'account_number'],
                'business_impact': 'high'
            }
        }
        
        # Correlation patterns for business intelligence
        self.correlation_patterns = {
            'customer_journey': {
                'sources': ['salesforce', 'hubspot', 'gong', 'intercom'],
                'correlation_strength': 0.9,
                'business_value': 'customer_lifecycle_tracking'
            },
            'revenue_attribution': {
                'sources': ['salesforce', 'hubspot', 'netsuite', 'looker'],
                'correlation_strength': 0.95,
                'business_value': 'revenue_tracking'
            },
            'product_development': {
                'sources': ['linear', 'asana', 'notion', 'slack'],
                'correlation_strength': 0.8,
                'business_value': 'development_efficiency'
            },
            'customer_success': {
                'sources': ['intercom', 'gong', 'hubspot', 'looker'],
                'correlation_strength': 0.85,
                'business_value': 'customer_satisfaction'
            },
            'sales_performance': {
                'sources': ['salesforce', 'gong', 'hubspot', 'factor_ai'],
                'correlation_strength': 0.9,
                'business_value': 'sales_optimization'
            }
        }
    
    def find_correlations_by_keys(self, source1: str, source2: str, time_window_hours: int = 24) -> List[Dict[str, Any]]:
        """Find correlations between two data sources using correlation keys"""
        correlations = []
        
        try:
            source1_config = self.data_sources.get(source1, {})
            source2_config = self.data_sources.get(source2, {})
            
            if not source1_config or not source2_config:
                return correlations
            
            # Get correlation keys that exist in both sources
            common_keys = set(source1_config['correlation_keys']) & set(source2_config['correlation_keys'])
            
            if not common_keys:
                return correlations
            
            # Get recent data from both sources
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_window_hours)
            
            source1_data = self.knowledge_repo.get_data_by_source_and_time(source1, start_time, end_time)
            source2_data = self.knowledge_repo.get_data_by_source_and_time(source2, start_time, end_time)
            
            # Find matches based on common keys
            for key in common_keys:
                matches = self.match_records_by_key(source1_data, source2_data, key)
                
                for match in matches:
                    correlation = {
                        'source1': source1,
                        'source2': source2,
                        'correlation_key': key,
                        'record1': match['record1'],
                        'record2': match['record2'],
                        'confidence': self.calculate_correlation_confidence(match, key),
                        'business_impact': self.assess_business_impact(source1, source2, match),
                        'detected_at': datetime.utcnow()
                    }
                    
                    correlations.append(correlation)
            
        except Exception as e:
            logger.error(f"Error finding correlations between {source1} and {source2}: {e}")
        
        return correlations
    
    def match_records_by_key(self, data1: List[Dict[str, Any]], data2: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
        """Match records from two datasets based on a correlation key"""
        matches = []
        
        try:
            # Create lookup dictionary for data2
            data2_lookup = {}
            for record in data2:
                key_value = self.extract_key_value(record, key)
                if key_value:
                    if key_value not in data2_lookup:
                        data2_lookup[key_value] = []
                    data2_lookup[key_value].append(record)
            
            # Find matches in data1
            for record1 in data1:
                key_value = self.extract_key_value(record1, key)
                if key_value and key_value in data2_lookup:
                    for record2 in data2_lookup[key_value]:
                        matches.append({
                            'record1': record1,
                            'record2': record2,
                            'key_value': key_value
                        })
            
        except Exception as e:
            logger.error(f"Error matching records by key {key}: {e}")
        
        return matches
    
    def extract_key_value(self, record: Dict[str, Any], key: str) -> Optional[str]:
        """Extract correlation key value from a record"""
        try:
            # Try direct key access
            if key in record:
                return str(record[key]).lower().strip()
            
            # Try nested access for common patterns
            data = record.get('data', {})
            if isinstance(data, dict) and key in data:
                return str(data[key]).lower().strip()
            
            # Try properties access
            properties = record.get('properties', {})
            if isinstance(properties, dict) and key in properties:
                return str(properties[key]).lower().strip()
            
            # Try custom field patterns
            custom_fields = record.get('custom_fields', {})
            if isinstance(custom_fields, dict) and key in custom_fields:
                return str(custom_fields[key]).lower().strip()
            
        except Exception as e:
            logger.error(f"Error extracting key {key} from record: {e}")
        
        return None
    
    def calculate_correlation_confidence(self, match: Dict[str, Any], key: str) -> float:
        """Calculate confidence score for a correlation"""
        base_confidence = 0.7
        
        try:
            record1 = match['record1']
            record2 = match['record2']
            
            # Boost confidence for exact matches
            key_value = match.get('key_value', '')
            if key_value and len(key_value) > 3:
                base_confidence += 0.1
            
            # Boost confidence for temporal proximity
            time1 = self.extract_timestamp(record1)
            time2 = self.extract_timestamp(record2)
            
            if time1 and time2:
                time_diff = abs((time1 - time2).total_seconds())
                if time_diff < 3600:  # Within 1 hour
                    base_confidence += 0.2
                elif time_diff < 86400:  # Within 1 day
                    base_confidence += 0.1
            
            # Boost confidence for additional matching fields
            additional_matches = self.count_additional_field_matches(record1, record2)
            base_confidence += min(additional_matches * 0.05, 0.15)
            
        except Exception as e:
            logger.error(f"Error calculating correlation confidence: {e}")
        
        return min(base_confidence, 1.0)
    
    def extract_timestamp(self, record: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from a record"""
        timestamp_fields = ['timestamp', 'created_at', 'updated_at', 'date', 'time']
        
        for field in timestamp_fields:
            if field in record:
                try:
                    timestamp_value = record[field]
                    if isinstance(timestamp_value, str):
                        return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                    elif isinstance(timestamp_value, datetime):
                        return timestamp_value
                except Exception:
                    continue
        
        return None
    
    def count_additional_field_matches(self, record1: Dict[str, Any], record2: Dict[str, Any]) -> int:
        """Count additional matching fields between two records"""
        matches = 0
        
        try:
            # Compare common field names
            common_fields = set(record1.keys()) & set(record2.keys())
            
            for field in common_fields:
                if field not in ['id', 'timestamp', 'created_at', 'updated_at']:
                    value1 = str(record1[field]).lower().strip()
                    value2 = str(record2[field]).lower().strip()
                    
                    if value1 == value2 and len(value1) > 2:
                        matches += 1
            
        except Exception as e:
            logger.error(f"Error counting additional field matches: {e}")
        
        return matches
    
    def assess_business_impact(self, source1: str, source2: str, match: Dict[str, Any]) -> str:
        """Assess the business impact of a correlation"""
        try:
            source1_impact = self.data_sources.get(source1, {}).get('business_impact', 'low')
            source2_impact = self.data_sources.get(source2, {}).get('business_impact', 'low')
            
            # Check if this correlation matches a known pattern
            for pattern_name, pattern_config in self.correlation_patterns.items():
                if source1 in pattern_config['sources'] and source2 in pattern_config['sources']:
                    return pattern_config['business_value']
            
            # Default assessment based on source impacts
            if source1_impact == 'high' and source2_impact == 'high':
                return 'high_value_correlation'
            elif source1_impact == 'high' or source2_impact == 'high':
                return 'medium_value_correlation'
            else:
                return 'low_value_correlation'
                
        except Exception as e:
            logger.error(f"Error assessing business impact: {e}")
            return 'unknown_impact'
    
    def store_correlations(self, correlations: List[Dict[str, Any]]) -> bool:
        """Store correlations in the knowledge repository"""
        try:
            stored_count = 0
            
            for correlation in correlations:
                if correlation['confidence'] >= 0.6:  # Only store high-confidence correlations
                    correlation_data = {
                        'source1': correlation['source1'],
                        'source2': correlation['source2'],
                        'correlation_key': correlation['correlation_key'],
                        'confidence_score': correlation['confidence'],
                        'business_impact': correlation['business_impact'],
                        'record1_data': json.dumps(correlation['record1']),
                        'record2_data': json.dumps(correlation['record2']),
                        'detected_at': correlation['detected_at'],
                        'status': 'active'
                    }
                    
                    self.knowledge_repo.store_cross_platform_correlation(correlation_data)
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} cross-platform correlations")
            return True
            
        except Exception as e:
            logger.error(f"Error storing correlations: {e}")
            return False
    
    def correlate_all_sources(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Correlate data across all configured sources"""
        try:
            all_correlations = []
            source_pairs_processed = 0
            
            sources = list(self.data_sources.keys())
            
            # Process all source pairs
            for i, source1 in enumerate(sources):
                for source2 in sources[i+1:]:
                    correlations = self.find_correlations_by_keys(source1, source2, time_window_hours)
                    all_correlations.extend(correlations)
                    source_pairs_processed += 1
            
            # Store correlations
            storage_success = self.store_correlations(all_correlations)
            
            # Calculate summary statistics
            high_confidence_correlations = [c for c in all_correlations if c['confidence'] >= 0.8]
            business_impact_distribution = {}
            
            for correlation in all_correlations:
                impact = correlation['business_impact']
                business_impact_distribution[impact] = business_impact_distribution.get(impact, 0) + 1
            
            return {
                'source_pairs_processed': source_pairs_processed,
                'total_correlations_found': len(all_correlations),
                'high_confidence_correlations': len(high_confidence_correlations),
                'business_impact_distribution': business_impact_distribution,
                'storage_successful': storage_success,
                'time_window_hours': time_window_hours,
                'processed_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error correlating all sources: {e}")
            return {'error': str(e)}

# Celery Tasks
@celery_app.task(bind=True, name='sophia_agents.cross_platform_correlation.correlate_data_sources')
def correlate_data_sources(self: Task, time_window_hours: int = 24) -> Dict[str, Any]:
    """Correlate data across all Pay Ready data sources"""
    agent = CrossPlatformCorrelationAgent()
    
    try:
        result = agent.correlate_all_sources(time_window_hours)
        result.update({
            'task': 'correlate_data_sources',
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        })
        
        logger.info(f"Cross-platform correlation completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Cross-platform correlation failed: {e}")
        return {
            'task': 'correlate_data_sources',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

@celery_app.task(bind=True, name='sophia_agents.cross_platform_correlation.correlate_specific_sources')
def correlate_specific_sources(self: Task, source1: str, source2: str, time_window_hours: int = 24) -> Dict[str, Any]:
    """Correlate data between two specific sources"""
    agent = CrossPlatformCorrelationAgent()
    
    try:
        correlations = agent.find_correlations_by_keys(source1, source2, time_window_hours)
        
        if correlations:
            storage_success = agent.store_correlations(correlations)
            
            return {
                'task': 'correlate_specific_sources',
                'source1': source1,
                'source2': source2,
                'correlations_found': len(correlations),
                'storage_successful': storage_success,
                'time_window_hours': time_window_hours,
                'completed_at': datetime.utcnow().isoformat(),
                'status': 'success'
            }
        
        return {
            'task': 'correlate_specific_sources',
            'source1': source1,
            'source2': source2,
            'correlations_found': 0,
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'no_correlations'
        }
        
    except Exception as e:
        logger.error(f"Specific source correlation failed: {e}")
        return {
            'task': 'correlate_specific_sources',
            'source1': source1,
            'source2': source2,
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

@celery_app.task(bind=True, name='sophia_agents.cross_platform_correlation.analyze_correlation_trends')
def analyze_correlation_trends(self: Task, days_back: int = 7) -> Dict[str, Any]:
    """Analyze correlation trends over time"""
    agent = CrossPlatformCorrelationAgent()
    
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        # Get correlations from the time period
        correlations = agent.knowledge_repo.get_correlations_by_time_range(start_time, end_time)
        
        # Analyze trends
        daily_counts = {}
        source_pair_counts = {}
        business_impact_trends = {}
        
        for correlation in correlations:
            # Daily trend
            date_key = correlation['detected_at'].date().isoformat()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            
            # Source pair trend
            pair_key = f"{correlation['source1']}-{correlation['source2']}"
            source_pair_counts[pair_key] = source_pair_counts.get(pair_key, 0) + 1
            
            # Business impact trend
            impact = correlation['business_impact']
            if date_key not in business_impact_trends:
                business_impact_trends[date_key] = {}
            business_impact_trends[date_key][impact] = business_impact_trends[date_key].get(impact, 0) + 1
        
        return {
            'task': 'analyze_correlation_trends',
            'days_analyzed': days_back,
            'total_correlations': len(correlations),
            'daily_correlation_counts': daily_counts,
            'top_source_pairs': dict(sorted(source_pair_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'business_impact_trends': business_impact_trends,
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Correlation trend analysis failed: {e}")
        return {
            'task': 'analyze_correlation_trends',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

