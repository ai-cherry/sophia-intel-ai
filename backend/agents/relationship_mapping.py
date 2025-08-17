"""
Relationship Mapping Agent for SOPHIA Intel
Maps relationships between business entities and maintains knowledge graphs
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

class RelationshipMappingAgent:
    """Agent for mapping relationships between business entities"""
    
    def __init__(self):
        self.knowledge_repo = UnifiedKnowledgeRepository()
        
        # Relationship types for Pay Ready business context
        self.relationship_types = {
            'causal': {
                'strength': 0.9,
                'patterns': ['causes', 'leads to', 'results in', 'drives', 'impacts']
            },
            'correlation': {
                'strength': 0.7,
                'patterns': ['correlates with', 'related to', 'associated with', 'linked to']
            },
            'dependency': {
                'strength': 0.8,
                'patterns': ['depends on', 'requires', 'needs', 'relies on']
            },
            'composition': {
                'strength': 0.9,
                'patterns': ['includes', 'contains', 'comprises', 'consists of']
            },
            'temporal': {
                'strength': 0.6,
                'patterns': ['before', 'after', 'during', 'follows', 'precedes']
            },
            'hierarchical': {
                'strength': 0.8,
                'patterns': ['reports to', 'manages', 'oversees', 'under', 'above']
            }
        }
        
        # Business domain relationship rules
        self.domain_rules = {
            'revenue_customer': {
                'entities': ['revenue_metrics', 'customer_entities'],
                'default_relationship': 'causal',
                'strength_modifier': 1.2
            },
            'product_market': {
                'entities': ['product_entities', 'market_entities'],
                'default_relationship': 'correlation',
                'strength_modifier': 1.1
            },
            'operational_financial': {
                'entities': ['operational_entities', 'financial_entities'],
                'default_relationship': 'dependency',
                'strength_modifier': 1.0
            }
        }
    
    def extract_relationships_from_text(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationships between entities from text"""
        relationships = []
        
        try:
            # Create entity pairs for relationship detection
            for i, entity1 in enumerate(entities):
                for j, entity2 in enumerate(entities[i+1:], i+1):
                    relationship = self.detect_relationship_between_entities(
                        entity1, entity2, text
                    )
                    
                    if relationship:
                        relationships.append(relationship)
            
            # Apply domain-specific rules
            relationships = self.apply_domain_rules(relationships)
            
        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
        
        return relationships
    
    def detect_relationship_between_entities(self, entity1: Dict[str, Any], entity2: Dict[str, Any], text: str) -> Optional[Dict[str, Any]]:
        """Detect relationship between two specific entities"""
        try:
            entity1_text = entity1.get('text', '').lower()
            entity2_text = entity2.get('text', '').lower()
            text_lower = text.lower()
            
            # Find positions of entities in text
            pos1 = text_lower.find(entity1_text)
            pos2 = text_lower.find(entity2_text)
            
            if pos1 == -1 or pos2 == -1:
                return None
            
            # Extract text between entities
            start_pos = min(pos1, pos2)
            end_pos = max(pos1 + len(entity1_text), pos2 + len(entity2_text))
            context_text = text_lower[start_pos:end_pos]
            
            # Detect relationship type
            best_relationship = None
            best_score = 0.0
            
            for rel_type, rel_config in self.relationship_types.items():
                for pattern in rel_config['patterns']:
                    if pattern in context_text:
                        score = rel_config['strength']
                        if score > best_score:
                            best_score = score
                            best_relationship = rel_type
            
            if best_relationship:
                return {
                    'source_entity': entity1,
                    'target_entity': entity2,
                    'relationship_type': best_relationship,
                    'confidence': best_score,
                    'context': context_text,
                    'detected_at': datetime.utcnow()
                }
            
        except Exception as e:
            logger.error(f"Error detecting relationship: {e}")
        
        return None
    
    def apply_domain_rules(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply business domain rules to enhance relationships"""
        enhanced_relationships = []
        
        try:
            for relationship in relationships:
                source_category = relationship['source_entity'].get('category')
                target_category = relationship['target_entity'].get('category')
                
                # Check domain rules
                for rule_name, rule_config in self.domain_rules.items():
                    if (source_category in rule_config['entities'] and 
                        target_category in rule_config['entities']):
                        
                        # Apply rule modifications
                        relationship['confidence'] *= rule_config['strength_modifier']
                        relationship['domain_rule'] = rule_name
                        
                        # Set default relationship if none detected
                        if relationship['confidence'] < 0.5:
                            relationship['relationship_type'] = rule_config['default_relationship']
                            relationship['confidence'] = 0.6
                
                enhanced_relationships.append(relationship)
                
        except Exception as e:
            logger.error(f"Error applying domain rules: {e}")
            return relationships
        
        return enhanced_relationships
    
    def store_relationships(self, relationships: List[Dict[str, Any]], source_id: str, source_type: str) -> bool:
        """Store relationships in the knowledge graph"""
        try:
            stored_count = 0
            
            for relationship in relationships:
                if relationship['confidence'] >= 0.5:  # Only store high-confidence relationships
                    relationship_data = {
                        'source_entity_id': relationship['source_entity'].get('id'),
                        'target_entity_id': relationship['target_entity'].get('id'),
                        'relationship_type': relationship['relationship_type'],
                        'confidence_score': relationship['confidence'],
                        'context_data': json.dumps({
                            'context': relationship.get('context', ''),
                            'domain_rule': relationship.get('domain_rule'),
                            'source_id': source_id,
                            'source_type': source_type
                        }),
                        'created_at': datetime.utcnow(),
                        'status': 'active'
                    }
                    
                    self.knowledge_repo.store_entity_relationship(relationship_data)
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} relationships from {source_type}:{source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing relationships: {e}")
            return False
    
    def update_relationship_graph(self) -> Dict[str, Any]:
        """Update the complete relationship graph with new connections"""
        try:
            # Get all recent entities
            recent_entities = self.knowledge_repo.get_recent_entities(hours=24)
            
            # Get existing relationships
            existing_relationships = self.knowledge_repo.get_all_relationships()
            
            # Calculate graph metrics
            total_entities = len(recent_entities)
            total_relationships = len(existing_relationships)
            
            # Identify potential new relationships
            potential_relationships = self.identify_potential_relationships(recent_entities)
            
            # Calculate graph connectivity
            connectivity_score = self.calculate_graph_connectivity(recent_entities, existing_relationships)
            
            return {
                'total_entities': total_entities,
                'total_relationships': total_relationships,
                'potential_new_relationships': len(potential_relationships),
                'connectivity_score': connectivity_score,
                'updated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error updating relationship graph: {e}")
            return {'error': str(e)}
    
    def identify_potential_relationships(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential relationships that should be explored"""
        potential_relationships = []
        
        try:
            # Group entities by category
            entity_groups = {}
            for entity in entities:
                category = entity.get('category', 'unknown')
                if category not in entity_groups:
                    entity_groups[category] = []
                entity_groups[category].append(entity)
            
            # Find cross-category relationships
            categories = list(entity_groups.keys())
            for i, cat1 in enumerate(categories):
                for cat2 in categories[i+1:]:
                    # Check if these categories should be related
                    for rule_name, rule_config in self.domain_rules.items():
                        if cat1 in rule_config['entities'] and cat2 in rule_config['entities']:
                            for entity1 in entity_groups[cat1]:
                                for entity2 in entity_groups[cat2]:
                                    potential_relationships.append({
                                        'source_entity': entity1,
                                        'target_entity': entity2,
                                        'suggested_type': rule_config['default_relationship'],
                                        'rule': rule_name,
                                        'priority': rule_config['strength_modifier']
                                    })
            
        except Exception as e:
            logger.error(f"Error identifying potential relationships: {e}")
        
        return potential_relationships
    
    def calculate_graph_connectivity(self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> float:
        """Calculate the connectivity score of the knowledge graph"""
        try:
            if len(entities) < 2:
                return 0.0
            
            # Create adjacency list
            adjacency = {}
            for entity in entities:
                entity_id = entity.get('id')
                if entity_id:
                    adjacency[entity_id] = set()
            
            # Add relationships
            for relationship in relationships:
                source_id = relationship.get('source_entity_id')
                target_id = relationship.get('target_entity_id')
                
                if source_id in adjacency and target_id in adjacency:
                    adjacency[source_id].add(target_id)
                    adjacency[target_id].add(source_id)  # Undirected graph
            
            # Calculate connectivity (average degree / max possible degree)
            total_connections = sum(len(connections) for connections in adjacency.values())
            max_possible_connections = len(entities) * (len(entities) - 1)
            
            connectivity_score = total_connections / max_possible_connections if max_possible_connections > 0 else 0.0
            
            return min(connectivity_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating graph connectivity: {e}")
            return 0.0

# Celery Tasks
@celery_app.task(bind=True, name='sophia_agents.relationship_mapping.update_relationship_graph')
def update_relationship_graph(self: Task) -> Dict[str, Any]:
    """Update the relationship graph with new connections"""
    agent = RelationshipMappingAgent()
    
    try:
        result = agent.update_relationship_graph()
        result.update({
            'task': 'update_relationship_graph',
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        })
        
        logger.info(f"Relationship graph update completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Relationship graph update failed: {e}")
        return {
            'task': 'update_relationship_graph',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

@celery_app.task(bind=True, name='sophia_agents.relationship_mapping.map_conversation_relationships')
def map_conversation_relationships(self: Task, conversation_id: str, entities: List[Dict[str, Any]], message_content: str) -> Dict[str, Any]:
    """Map relationships from a specific conversation"""
    agent = RelationshipMappingAgent()
    
    try:
        relationships = agent.extract_relationships_from_text(message_content, entities)
        
        if relationships:
            success = agent.store_relationships(relationships, conversation_id, 'chat_conversation')
            
            return {
                'task': 'map_conversation_relationships',
                'conversation_id': conversation_id,
                'relationships_found': len(relationships),
                'relationships': relationships,
                'stored_successfully': success,
                'completed_at': datetime.utcnow().isoformat(),
                'status': 'success'
            }
        
        return {
            'task': 'map_conversation_relationships',
            'conversation_id': conversation_id,
            'relationships_found': 0,
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'no_relationships'
        }
        
    except Exception as e:
        logger.error(f"Conversation relationship mapping failed: {e}")
        return {
            'task': 'map_conversation_relationships',
            'conversation_id': conversation_id,
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

@celery_app.task(bind=True, name='sophia_agents.relationship_mapping.analyze_relationship_patterns')
def analyze_relationship_patterns(self: Task, time_period_hours: int = 168) -> Dict[str, Any]:
    """Analyze relationship patterns over a time period"""
    agent = RelationshipMappingAgent()
    
    try:
        # Get relationships from the specified time period
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_period_hours)
        
        relationships = agent.knowledge_repo.get_relationships_by_time_range(start_time, end_time)
        
        # Analyze patterns
        relationship_type_counts = {}
        confidence_scores = []
        domain_rule_usage = {}
        
        for relationship in relationships:
            # Count relationship types
            rel_type = relationship.get('relationship_type', 'unknown')
            relationship_type_counts[rel_type] = relationship_type_counts.get(rel_type, 0) + 1
            
            # Collect confidence scores
            confidence = relationship.get('confidence_score', 0.0)
            confidence_scores.append(confidence)
            
            # Count domain rule usage
            context_data = json.loads(relationship.get('context_data', '{}'))
            domain_rule = context_data.get('domain_rule')
            if domain_rule:
                domain_rule_usage[domain_rule] = domain_rule_usage.get(domain_rule, 0) + 1
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            'task': 'analyze_relationship_patterns',
            'time_period_hours': time_period_hours,
            'total_relationships': len(relationships),
            'relationship_type_distribution': relationship_type_counts,
            'average_confidence': avg_confidence,
            'domain_rule_usage': domain_rule_usage,
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Relationship pattern analysis failed: {e}")
        return {
            'task': 'analyze_relationship_patterns',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

