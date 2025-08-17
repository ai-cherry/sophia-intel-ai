"""
Entity Recognition Agent for SOPHIA Intel
Automatically identifies and extracts Pay Ready business entities from conversations and data sources
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from celery import Task
from .celery_app import celery_app
from ..database.unified_knowledge_repository import UnifiedKnowledgeRepository
from ..core.sophia_orchestrator_enhanced import SophiaOrchestratorEnhanced

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityRecognitionAgent:
    """Agent for recognizing and extracting business entities"""
    
    def __init__(self):
        self.knowledge_repo = UnifiedKnowledgeRepository()
        self.orchestrator = SophiaOrchestratorEnhanced()
        
        # Pay Ready specific entity patterns
        self.entity_patterns = {
            'revenue_metrics': [
                'revenue', 'sales', 'income', 'earnings', 'profit', 'margin',
                'ARR', 'MRR', 'LTV', 'CAC', 'churn', 'retention'
            ],
            'customer_entities': [
                'customer', 'client', 'user', 'subscriber', 'account',
                'lead', 'prospect', 'conversion', 'acquisition'
            ],
            'product_entities': [
                'product', 'feature', 'service', 'offering', 'solution',
                'platform', 'API', 'integration', 'workflow'
            ],
            'operational_entities': [
                'process', 'workflow', 'automation', 'efficiency',
                'cost', 'expense', 'budget', 'resource', 'team'
            ],
            'market_entities': [
                'market', 'competition', 'competitor', 'industry',
                'trend', 'opportunity', 'threat', 'analysis'
            ],
            'financial_entities': [
                'cash flow', 'funding', 'investment', 'valuation',
                'burn rate', 'runway', 'EBITDA', 'gross margin'
            ]
        }
        
        # Data source priorities for entity extraction
        self.data_source_priorities = {
            'salesforce': 1,
            'hubspot': 2,
            'gong': 3,
            'intercom': 4,
            'netsuite': 5,
            'looker': 6,
            'slack': 7,
            'asana': 8,
            'linear': 9,
            'notion': 10,
            'factor_ai': 11
        }
    
    def extract_entities_from_text(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Extract business entities from text using pattern matching and AI analysis"""
        entities = []
        
        try:
            # Pattern-based extraction
            for category, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in text.lower():
                        entities.append({
                            'text': pattern,
                            'category': category,
                            'confidence': 0.8,
                            'extraction_method': 'pattern_matching',
                            'context': context or {}
                        })
            
            # AI-enhanced extraction using orchestrator
            if len(entities) > 0:  # Only if we found some entities
                ai_analysis = self.orchestrator.process_business_intelligence_query(
                    f"Extract and categorize business entities from this text: {text[:500]}",
                    context={'entity_extraction': True}
                )
                
                if ai_analysis and 'entities' in ai_analysis:
                    for entity in ai_analysis['entities']:
                        entities.append({
                            'text': entity.get('text', ''),
                            'category': entity.get('category', 'unknown'),
                            'confidence': entity.get('confidence', 0.6),
                            'extraction_method': 'ai_analysis',
                            'context': context or {}
                        })
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
        
        return entities
    
    def store_entities(self, entities: List[Dict[str, Any]], source_id: str, source_type: str) -> bool:
        """Store extracted entities in the knowledge repository"""
        try:
            for entity in entities:
                entity_data = {
                    'entity_text': entity['text'],
                    'entity_category': entity['category'],
                    'confidence_score': entity['confidence'],
                    'extraction_method': entity['extraction_method'],
                    'source_id': source_id,
                    'source_type': source_type,
                    'context_data': json.dumps(entity['context']),
                    'extracted_at': datetime.utcnow(),
                    'status': 'active'
                }
                
                self.knowledge_repo.store_business_entity(entity_data)
            
            logger.info(f"Stored {len(entities)} entities from {source_type}:{source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing entities: {e}")
            return False
    
    def get_pending_entities(self) -> List[Dict[str, Any]]:
        """Get entities that need processing or validation"""
        try:
            # Get recent conversations that haven't been processed
            recent_conversations = self.knowledge_repo.get_recent_conversations(
                hours=24, 
                processed=False
            )
            
            # Get data from external sources that need entity extraction
            pending_data = []
            for source in self.data_source_priorities.keys():
                source_data = self.knowledge_repo.get_unprocessed_data_by_source(source)
                pending_data.extend(source_data)
            
            return recent_conversations + pending_data
            
        except Exception as e:
            logger.error(f"Error getting pending entities: {e}")
            return []
    
    def validate_entity_quality(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and score entity quality"""
        quality_score = 0.0
        issues = []
        
        try:
            # Check confidence threshold
            if entity.get('confidence', 0) < 0.5:
                issues.append('low_confidence')
            else:
                quality_score += 0.3
            
            # Check category validity
            if entity.get('category') in self.entity_patterns:
                quality_score += 0.3
            else:
                issues.append('invalid_category')
            
            # Check text quality
            entity_text = entity.get('text', '').strip()
            if len(entity_text) > 2 and entity_text.isalpha():
                quality_score += 0.2
            else:
                issues.append('poor_text_quality')
            
            # Check context relevance
            context = entity.get('context', {})
            if context and 'pay_ready' in str(context).lower():
                quality_score += 0.2
            
            return {
                'quality_score': quality_score,
                'issues': issues,
                'validated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error validating entity quality: {e}")
            return {'quality_score': 0.0, 'issues': ['validation_error']}

# Celery Tasks
@celery_app.task(bind=True, name='sophia_agents.entity_recognition.process_pending_entities')
def process_pending_entities(self: Task) -> Dict[str, Any]:
    """Process pending entities from various data sources"""
    agent = EntityRecognitionAgent()
    
    try:
        pending_items = agent.get_pending_entities()
        processed_count = 0
        entities_extracted = 0
        
        for item in pending_items[:50]:  # Process up to 50 items per run
            try:
                # Extract entities from the item
                text_content = item.get('content', '') or item.get('text', '')
                if not text_content:
                    continue
                
                entities = agent.extract_entities_from_text(
                    text_content,
                    context={
                        'source_id': item.get('id'),
                        'source_type': item.get('source_type', 'unknown'),
                        'timestamp': item.get('timestamp'),
                        'pay_ready_context': True
                    }
                )
                
                if entities:
                    success = agent.store_entities(
                        entities,
                        item.get('id', 'unknown'),
                        item.get('source_type', 'unknown')
                    )
                    
                    if success:
                        entities_extracted += len(entities)
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing item {item.get('id')}: {e}")
                continue
        
        result = {
            'task': 'process_pending_entities',
            'processed_items': processed_count,
            'entities_extracted': entities_extracted,
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
        logger.info(f"Entity recognition completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Entity recognition task failed: {e}")
        return {
            'task': 'process_pending_entities',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

@celery_app.task(bind=True, name='sophia_agents.entity_recognition.extract_from_conversation')
def extract_from_conversation(self: Task, conversation_id: str, message_content: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Extract entities from a specific conversation in real-time"""
    agent = EntityRecognitionAgent()
    
    try:
        entities = agent.extract_entities_from_text(
            message_content,
            context={
                'conversation_id': conversation_id,
                'source_type': 'chat_conversation',
                'user_context': user_context or {},
                'pay_ready_context': True,
                'real_time': True
            }
        )
        
        if entities:
            success = agent.store_entities(entities, conversation_id, 'chat_conversation')
            
            return {
                'task': 'extract_from_conversation',
                'conversation_id': conversation_id,
                'entities_found': len(entities),
                'entities': entities,
                'stored_successfully': success,
                'completed_at': datetime.utcnow().isoformat(),
                'status': 'success'
            }
        
        return {
            'task': 'extract_from_conversation',
            'conversation_id': conversation_id,
            'entities_found': 0,
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'no_entities'
        }
        
    except Exception as e:
        logger.error(f"Conversation entity extraction failed: {e}")
        return {
            'task': 'extract_from_conversation',
            'conversation_id': conversation_id,
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

@celery_app.task(bind=True, name='sophia_agents.entity_recognition.validate_entity_batch')
def validate_entity_batch(self: Task, entity_ids: List[str]) -> Dict[str, Any]:
    """Validate a batch of entities for quality and accuracy"""
    agent = EntityRecognitionAgent()
    
    try:
        validated_count = 0
        quality_scores = []
        
        for entity_id in entity_ids:
            entity = agent.knowledge_repo.get_entity_by_id(entity_id)
            if entity:
                validation_result = agent.validate_entity_quality(entity)
                
                # Update entity with validation results
                agent.knowledge_repo.update_entity_validation(
                    entity_id,
                    validation_result['quality_score'],
                    validation_result['issues']
                )
                
                validated_count += 1
                quality_scores.append(validation_result['quality_score'])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            'task': 'validate_entity_batch',
            'entities_validated': validated_count,
            'average_quality_score': avg_quality,
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Entity validation batch failed: {e}")
        return {
            'task': 'validate_entity_batch',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

