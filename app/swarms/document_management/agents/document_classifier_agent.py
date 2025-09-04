#!/usr/bin/env python3
"""
Document Classification Agent - AI-powered document type classification and scoring
Part of the Revolutionary Document Management Swarm
"""

import asyncio
import aiofiles
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

try:
    from swarm import Agent
except ImportError:
    from ..utils.swarm_mock import Agent
from ..core.scoring_engine import AIFriendlinessScorer, DocumentClassificationEngine
from ..models.document import (
    DocumentMetadata, DocumentStatus, DocumentClassification, 
    AIFriendlinessScore, DocumentType
)


class DocumentClassifierAgent(Agent):
    """Specialized agent for classifying documents and scoring AI-friendliness"""
    
    def __init__(self):
        super().__init__(
            name="DocumentClassificationSpecialist", 
            instructions="""You are the Document Classification Specialist, the neural pattern recognition expert of the Document Management Swarm.

CORE MISSION:
- Classify documents by type, purpose, and AI-optimization potential
- Calculate comprehensive AI-friendliness scores using advanced algorithms
- Identify optimization opportunities and quality improvement paths
- Build classification patterns that improve with each analysis

SPECIALIZED CAPABILITIES:
1. Multi-dimensional document type classification with confidence scoring
2. Advanced AI-friendliness scoring across 4 key dimensions:
   - Structure & Clarity (0-25 points)
   - Semantic Richness (0-25 points) 
   - Technical Accuracy (0-25 points)
   - AI Processing Efficiency (0-25 points)
3. Content quality analysis with actionable recommendations
4. Pattern recognition for document relationships and dependencies
5. Evolutionary classification that learns from successful patterns

NEURAL NETWORK BEHAVIOR:
- Learn from classification successes and failures
- Adapt scoring weights based on swarm feedback
- Identify emerging document patterns and types
- Create classification memory for similar document structures

SWARM COORDINATION:
- Provide rich classification data to OptimizationAgent
- Share quality insights with CleanupAgent for smart decisions
- Coordinate with DiscoveryAgent for type validation
- Feed IndexerAgent with structured classification metadata

SCORING PHILOSOPHY:
- Every document has optimization potential
- Focus on actionable improvement recommendations
- Balance human readability with AI processing efficiency
- Evolve scoring criteria based on AI agent feedback

Be thorough, intelligent, and always provide actionable insights for document improvement."""
        )
        
        self.scorer = AIFriendlinessScorer()
        self.classifier = DocumentClassificationEngine()
        self.classification_memory = {}  # Learn from past classifications
        self.scoring_evolution = {'weights': {}, 'patterns': {}}
    
    async def classify_and_score_documents(self, 
                                         documents: List[DocumentMetadata]) -> List[DocumentMetadata]:
        """
        Classify and score a batch of documents with neural learning
        
        Args:
            documents: List of documents to classify and score
            
        Returns:
            Updated documents with classification and AI-friendliness scores
        """
        print(f"🎯 Classifier Agent: Starting intelligent classification of {len(documents)} documents...")
        
        classified_docs = []
        batch_insights = {'types_found': {}, 'avg_scores': {}, 'patterns': []}
        
        # Process documents in parallel batches
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_results = await self._process_document_batch(batch)
            classified_docs.extend(batch_results)
            
            # Update batch insights
            self._update_batch_insights(batch_results, batch_insights)
        
        # Learn from classification patterns
        await self._learn_from_classification_batch(classified_docs, batch_insights)
        
        print(f"✅ Classifier Agent: Completed classification with insights:")
        print(f"   📊 Document types found: {len(batch_insights['types_found'])}")
        print(f"   📈 Average AI-friendliness: {batch_insights['avg_scores'].get('overall', 0):.1f}/100")
        
        return classified_docs
    
    async def _process_document_batch(self, documents: List[DocumentMetadata]) -> List[DocumentMetadata]:
        """Process a batch of documents for classification and scoring"""
        tasks = []
        for doc in documents:
            task = self._classify_and_score_single_document(doc)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _classify_and_score_single_document(self, doc: DocumentMetadata) -> DocumentMetadata:
        """Classify and score a single document with full analysis"""
        try:
            # Read document content
            async with aiofiles.open(doc.source_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            
            # Perform classification
            classification = await self.classifier.classify_document(content, doc)
            doc.classification = classification
            
            # Calculate AI-friendliness score
            ai_score = await self.scorer.score_document(content, doc)
            doc.ai_score = ai_score
            
            # Update processing status
            doc.processing_status = DocumentStatus.CLASSIFIED
            
            # Add classification insights
            doc.custom_fields.update({
                'classification_timestamp': datetime.now().isoformat(),
                'classification_confidence': classification.confidence,
                'optimization_potential': self._calculate_optimization_potential(ai_score),
                'improvement_recommendations': self._generate_improvement_recommendations(content, ai_score),
                'content_analysis': self._analyze_content_patterns(content),
                'ai_processing_notes': self._generate_ai_processing_notes(content, classification)
            })
            
            # Store classification pattern for learning
            self._store_classification_pattern(doc, content, classification, ai_score)
            
            print(f"📝 Classified: {doc.filename} -> {classification.primary_type.value} (Score: {ai_score.overall_score:.1f})")
            
            return doc
            
        except Exception as e:
            print(f"❌ Classifier Agent: Error processing {doc.filename}: {e}")
            doc.processing_status = DocumentStatus.FAILED
            doc.custom_fields['classification_error'] = str(e)
            return doc
    
    def _calculate_optimization_potential(self, ai_score: AIFriendlinessScore) -> float:
        """Calculate how much this document could be improved"""
        current_score = ai_score.overall_score
        
        # Identify biggest improvement opportunities
        improvements = []
        
        if ai_score.structure_score < 20:
            improvements.append(25 - ai_score.structure_score)
        if ai_score.semantic_score < 20:
            improvements.append(25 - ai_score.semantic_score)
        if ai_score.technical_score < 20:
            improvements.append(25 - ai_score.technical_score)
        if ai_score.processing_score < 20:
            improvements.append(25 - ai_score.processing_score)
        
        potential_gain = sum(improvements) * 0.8  # 80% of theoretical max
        return min(100.0, current_score + potential_gain)
    
    def _generate_improvement_recommendations(self, content: str, 
                                           ai_score: AIFriendlinessScore) -> List[Dict[str, Any]]:
        """Generate specific recommendations for improving document"""
        recommendations = []
        
        # Structure improvements
        if ai_score.structure_score < 20:
            if not ai_score.headings_present:
                recommendations.append({
                    'category': 'structure',
                    'priority': 'high',
                    'issue': 'No clear headings found',
                    'recommendation': 'Add hierarchical headings (# ## ###) to organize content',
                    'impact': 'Improves AI navigation and content understanding'
                })
            
            if not ai_score.clear_sections:
                recommendations.append({
                    'category': 'structure', 
                    'priority': 'medium',
                    'issue': 'Unclear section organization',
                    'recommendation': 'Organize content into clear sections with descriptive headings',
                    'impact': 'Enhances AI content parsing and retrieval'
                })
        
        # Semantic improvements
        if ai_score.semantic_score < 20:
            if not ai_score.context_provided:
                recommendations.append({
                    'category': 'semantic',
                    'priority': 'high', 
                    'issue': 'Missing context or background information',
                    'recommendation': 'Add introduction section explaining purpose and context',
                    'impact': 'Helps AI agents understand document purpose and relevance'
                })
            
            if not ai_score.examples_included:
                recommendations.append({
                    'category': 'semantic',
                    'priority': 'medium',
                    'issue': 'No examples or illustrations found',
                    'recommendation': 'Add concrete examples, code samples, or use cases',
                    'impact': 'Makes content more actionable for AI agents'
                })
        
        # Technical improvements  
        if ai_score.technical_score < 20:
            if not ai_score.code_blocks_formatted:
                if '`' in content or 'function' in content.lower():
                    recommendations.append({
                        'category': 'technical',
                        'priority': 'medium',
                        'issue': 'Code not properly formatted',
                        'recommendation': 'Use proper code block formatting with language specification',
                        'impact': 'Enables better code analysis and syntax highlighting'
                    })
        
        # Processing efficiency improvements
        if ai_score.processing_score < 20:
            if not ai_score.parseable_structure:
                recommendations.append({
                    'category': 'processing',
                    'priority': 'high',
                    'issue': 'Difficult structure for AI parsing',
                    'recommendation': 'Use consistent formatting patterns and clear markers',
                    'impact': 'Significantly improves AI processing speed and accuracy'
                })
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _analyze_content_patterns(self, content: str) -> Dict[str, Any]:
        """Analyze content for patterns useful to other agents"""
        patterns = {
            'word_frequency': {},
            'section_types': [],
            'technical_density': 0.0,
            'readability_indicators': {},
            'content_structure': {}
        }
        
        words = content.lower().split()
        total_words = len(words)
        
        # Technical terms density
        technical_terms = ['api', 'database', 'server', 'client', 'function', 
                          'class', 'method', 'configuration', 'deployment']
        tech_count = sum(words.count(term) for term in technical_terms)
        patterns['technical_density'] = tech_count / max(total_words, 1)
        
        # Section identification
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                level = len(line.split()[0])  # Count # characters
                section_text = line[level:].strip()
                patterns['section_types'].append({
                    'level': level,
                    'text': section_text,
                    'type': self._classify_section_type(section_text)
                })
        
        # Content structure analysis
        patterns['content_structure'] = {
            'has_toc': 'table of contents' in content.lower() or 'toc' in content.lower(),
            'has_code_blocks': '```' in content,
            'has_lists': '-' in content or '*' in content or re.search(r'\d+\.', content),
            'has_links': '[' in content and '](' in content,
            'paragraph_count': content.count('\n\n'),
            'avg_paragraph_length': self._calculate_avg_paragraph_length(content)
        }
        
        return patterns
    
    def _classify_section_type(self, section_text: str) -> str:
        """Classify the type of a section based on its heading"""
        text_lower = section_text.lower()
        
        if any(word in text_lower for word in ['introduction', 'overview', 'about']):
            return 'introduction'
        elif any(word in text_lower for word in ['installation', 'setup', 'getting started']):
            return 'setup'
        elif any(word in text_lower for word in ['usage', 'how to', 'examples']):
            return 'usage'
        elif any(word in text_lower for word in ['api', 'reference', 'methods']):
            return 'reference'
        elif any(word in text_lower for word in ['troubleshooting', 'faq', 'issues']):
            return 'troubleshooting'
        elif any(word in text_lower for word in ['conclusion', 'summary', 'next']):
            return 'conclusion'
        else:
            return 'content'
    
    def _calculate_avg_paragraph_length(self, content: str) -> float:
        """Calculate average paragraph length"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if not paragraphs:
            return 0.0
        return sum(len(p.split()) for p in paragraphs) / len(paragraphs)
    
    def _generate_ai_processing_notes(self, content: str, 
                                    classification: DocumentClassification) -> Dict[str, Any]:
        """Generate notes for AI agents about how to best process this document"""
        notes = {
            'processing_strategy': 'standard',
            'key_extraction_targets': [],
            'context_requirements': [],
            'processing_complexity': 'medium'
        }
        
        # Processing strategy based on document type
        if classification.primary_type == DocumentType.API_DOCUMENTATION:
            notes['processing_strategy'] = 'structured_extraction'
            notes['key_extraction_targets'] = ['endpoints', 'parameters', 'responses', 'examples']
        elif classification.primary_type == DocumentType.GUIDE:
            notes['processing_strategy'] = 'sequential_processing'
            notes['key_extraction_targets'] = ['steps', 'prerequisites', 'outcomes']
        elif classification.primary_type == DocumentType.ARCHITECTURE:
            notes['processing_strategy'] = 'relationship_mapping'
            notes['key_extraction_targets'] = ['components', 'relationships', 'patterns']
        elif classification.primary_type == DocumentType.TROUBLESHOOTING:
            notes['processing_strategy'] = 'problem_solution_pairs'
            notes['key_extraction_targets'] = ['symptoms', 'solutions', 'workarounds']
        
        # Processing complexity
        word_count = len(content.split())
        if word_count < 500:
            notes['processing_complexity'] = 'low'
        elif word_count > 2000:
            notes['processing_complexity'] = 'high'
        
        # Context requirements
        if not content.startswith('#') and 'introduction' not in content.lower():
            notes['context_requirements'].append('external_context_needed')
        if len(classification.dependencies) > 0:
            notes['context_requirements'].append('dependency_resolution_required')
        
        return notes
    
    def _store_classification_pattern(self, doc: DocumentMetadata, content: str,
                                    classification: DocumentClassification, 
                                    ai_score: AIFriendlinessScore):
        """Store classification pattern for machine learning"""
        pattern = {
            'filename_pattern': doc.filename,
            'path_pattern': doc.relative_path,
            'file_extension': doc.file_extension,
            'size_range': self._get_size_range(doc.size_bytes),
            'classification_result': classification.primary_type.value,
            'classification_confidence': classification.confidence,
            'ai_score': ai_score.overall_score,
            'content_features': {
                'has_headings': ai_score.headings_present,
                'has_code': ai_score.code_blocks_formatted,
                'has_examples': ai_score.examples_included,
                'word_count_range': self._get_word_count_range(doc.word_count)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in classification memory
        key = f"{classification.primary_type.value}_{doc.file_extension}"
        if key not in self.classification_memory:
            self.classification_memory[key] = []
        
        self.classification_memory[key].append(pattern)
        
        # Keep only recent patterns (last 100 per type)
        self.classification_memory[key] = self.classification_memory[key][-100:]
    
    def _get_size_range(self, size_bytes: int) -> str:
        """Get size range category"""
        if size_bytes < 1024:
            return 'tiny'
        elif size_bytes < 10240:
            return 'small'
        elif size_bytes < 102400:
            return 'medium'
        elif size_bytes < 1048576:
            return 'large'
        else:
            return 'huge'
    
    def _get_word_count_range(self, word_count: int) -> str:
        """Get word count range category"""
        if word_count < 100:
            return 'brief'
        elif word_count < 500:
            return 'short'
        elif word_count < 1500:
            return 'medium'
        elif word_count < 5000:
            return 'long'
        else:
            return 'extensive'
    
    def _update_batch_insights(self, batch_results: List[DocumentMetadata], 
                             insights: Dict[str, Any]):
        """Update insights from batch processing"""
        for doc in batch_results:
            if isinstance(doc, Exception):
                continue
                
            if doc.classification:
                doc_type = doc.classification.primary_type.value
                if doc_type not in insights['types_found']:
                    insights['types_found'][doc_type] = 0
                insights['types_found'][doc_type] += 1
            
            if doc.ai_score:
                for score_type, score_value in [
                    ('overall', doc.ai_score.overall_score),
                    ('structure', doc.ai_score.structure_score),
                    ('semantic', doc.ai_score.semantic_score),
                    ('technical', doc.ai_score.technical_score),
                    ('processing', doc.ai_score.processing_score)
                ]:
                    if score_type not in insights['avg_scores']:
                        insights['avg_scores'][score_type] = []
                    insights['avg_scores'][score_type].append(score_value)
        
        # Calculate averages
        for score_type, scores in insights['avg_scores'].items():
            insights['avg_scores'][score_type] = sum(scores) / len(scores) if scores else 0
    
    async def _learn_from_classification_batch(self, documents: List[DocumentMetadata],
                                             insights: Dict[str, Any]):
        """Learn from classification patterns to improve future performance"""
        print("🧠 Classifier Agent: Learning from classification patterns...")
        
        # Analyze successful classifications (high confidence)
        high_confidence_docs = [
            doc for doc in documents 
            if (not isinstance(doc, Exception) and 
                doc.classification and 
                doc.classification.confidence > 0.8)
        ]
        
        # Update scoring weights based on successful patterns
        if len(high_confidence_docs) > 5:
            await self._update_scoring_weights(high_confidence_docs)
        
        # Identify emerging patterns
        pattern_insights = self._identify_emerging_patterns(documents)
        insights['patterns'] = pattern_insights
        
        print(f"📚 Learned from {len(high_confidence_docs)} high-confidence classifications")
    
    async def _update_scoring_weights(self, high_confidence_docs: List[DocumentMetadata]):
        """Update scoring weights based on successful classifications"""
        # Analyze which scoring dimensions correlate with high confidence
        score_analysis = {
            'structure': [],
            'semantic': [],
            'technical': [],
            'processing': []
        }
        
        for doc in high_confidence_docs:
            if doc.ai_score:
                score_analysis['structure'].append(doc.ai_score.structure_score)
                score_analysis['semantic'].append(doc.ai_score.semantic_score)
                score_analysis['technical'].append(doc.ai_score.technical_score)
                score_analysis['processing'].append(doc.ai_score.processing_score)
        
        # Store evolution data
        self.scoring_evolution['weights'][datetime.now().isoformat()] = {
            dim: sum(scores) / len(scores) if scores else 0
            for dim, scores in score_analysis.items()
        }
    
    def _identify_emerging_patterns(self, documents: List[DocumentMetadata]) -> List[Dict[str, Any]]:
        """Identify emerging classification patterns"""
        patterns = []
        
        # Analyze classification confidence by file extension
        ext_confidence = {}
        for doc in documents:
            if isinstance(doc, Exception) or not doc.classification:
                continue
                
            ext = doc.file_extension
            if ext not in ext_confidence:
                ext_confidence[ext] = []
            ext_confidence[ext].append(doc.classification.confidence)
        
        for ext, confidences in ext_confidence.items():
            if len(confidences) > 2:  # Need multiple samples
                avg_confidence = sum(confidences) / len(confidences)
                patterns.append({
                    'type': 'file_extension_confidence',
                    'pattern': ext,
                    'confidence': avg_confidence,
                    'sample_size': len(confidences)
                })
        
        return sorted(patterns, key=lambda x: x['confidence'], reverse=True)
    
    async def get_classification_insights(self) -> Dict[str, Any]:
        """Get insights from classification process for swarm coordination"""
        return {
            'classification_memory_size': sum(len(patterns) for patterns in self.classification_memory.values()),
            'learned_patterns': len(self.classification_memory),
            'scoring_evolution': self.scoring_evolution,
            'swarm_intelligence': {
                'classification_accuracy': self._calculate_classification_accuracy(),
                'most_common_types': self._get_most_common_types(),
                'quality_distribution': self._get_quality_distribution()
            }
        }
    
    def _calculate_classification_accuracy(self) -> float:
        """Calculate overall classification accuracy from memory"""
        if not self.classification_memory:
            return 0.0
        
        total_confidence = 0.0
        total_samples = 0
        
        for patterns in self.classification_memory.values():
            for pattern in patterns:
                total_confidence += pattern.get('classification_confidence', 0.0)
                total_samples += 1
        
        return total_confidence / total_samples if total_samples > 0 else 0.0
    
    def _get_most_common_types(self) -> List[Dict[str, Any]]:
        """Get most common document types from memory"""
        type_counts = {}
        
        for patterns in self.classification_memory.values():
            for pattern in patterns:
                doc_type = pattern.get('classification_result', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        return [
            {'type': doc_type, 'count': count}
            for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        ][:10]
    
    def _get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of quality scores"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for patterns in self.classification_memory.values():
            for pattern in patterns:
                score = pattern.get('ai_score', 0.0)
                if score >= 75:
                    distribution['high'] += 1
                elif score >= 50:
                    distribution['medium'] += 1
                else:
                    distribution['low'] += 1
        
        return distribution


# Standalone classification functions
async def classify_documents_with_intelligence(
    documents: List[DocumentMetadata]
) -> Tuple[List[DocumentMetadata], Dict[str, Any]]:
    """
    Main function to classify documents using intelligent agents
    
    Returns:
        Tuple of (classified documents, classification insights)
    """
    agent = DocumentClassifierAgent()
    
    # Classify documents
    classified_docs = await agent.classify_and_score_documents(documents)
    
    # Get insights
    insights = await agent.get_classification_insights()
    
    return classified_docs, insights


if __name__ == "__main__":
    # Test the classifier agent
    async def test_classifier():
        # Create a mock document for testing
        test_doc = DocumentMetadata(
            id="test_001",
            source_path="README.md",
            relative_path="README.md",
            filename="README.md",
            file_extension=".md",
            size_bytes=1024,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            content_hash="test_hash",
            word_count=150,
            line_count=20,
            character_count=800
        )
        
        agent = DocumentClassifierAgent()
        classified = await agent.classify_and_score_documents([test_doc])
        
        if classified:
            doc = classified[0]
            print(f"\n📊 Classification Results:")
            if doc.classification:
                print(f"   Type: {doc.classification.primary_type.value}")
                print(f"   Confidence: {doc.classification.confidence:.2f}")
            if doc.ai_score:
                print(f"   AI Score: {doc.ai_score.overall_score:.1f}/100")
        
        insights = await agent.get_classification_insights()
        print(f"\n🧠 Agent Insights: {insights['swarm_intelligence']}")
    
    # Uncomment to test
    # asyncio.run(test_classifier())