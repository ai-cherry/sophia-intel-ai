#!/usr/bin/env python3
"""
AI-Friendliness Scoring Engine for Document Management Swarm
Advanced AI-optimized document scoring with neural pattern recognition
"""

import re
import string
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from pathlib import Path
import aiofiles
from textstat import flesch_reading_ease, flesch_kincaid_grade

from ..models.document import (
    AIFriendlinessScore, 
    DocumentClassification, 
    DocumentType, 
    DocumentMetadata
)


class AIFriendlinessScorer:
    """Advanced scoring engine for AI document consumption optimization"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.keywords = self._initialize_keywords()
        self.scoring_weights = self._initialize_scoring_weights()
    
    def _initialize_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize regex patterns for content analysis"""
        return {
            # Structure patterns
            'headings': re.compile(r'^#{1,6}\s+.+$', re.MULTILINE),
            'code_blocks': re.compile(r'```[\s\S]*?```', re.MULTILINE),
            'inline_code': re.compile(r'`[^`]+`'),
            'bullet_points': re.compile(r'^\s*[-*+]\s+', re.MULTILINE),
            'numbered_lists': re.compile(r'^\s*\d+\.\s+', re.MULTILINE),
            'tables': re.compile(r'\|.+\|', re.MULTILINE),
            
            # Content patterns  
            'examples': re.compile(r'\b(example|e\.g\.|for instance|such as)\b', re.IGNORECASE),
            'definitions': re.compile(r'\b(definition|means|refers to|defined as)\b', re.IGNORECASE),
            'procedures': re.compile(r'\b(step \d+|first|next|then|finally)\b', re.IGNORECASE),
            'cross_references': re.compile(r'\[([^\]]+)\]\([^)]+\)'),
            
            # Technical patterns
            'function_signatures': re.compile(r'\b\w+\([^)]*\)\s*{?'),
            'config_values': re.compile(r'\w+\s*[:=]\s*\w+'),
            'urls': re.compile(r'https?://[^\s]+'),
            'file_paths': re.compile(r'[/\\][\w\-\.]+(?:[/\\][\w\-\.]+)*'),
            
            # Quality indicators
            'todo_items': re.compile(r'\b(TODO|FIXME|XXX|HACK)\b', re.IGNORECASE),
            'placeholder_text': re.compile(r'\b(placeholder|todo|tbd|fix|update)\b', re.IGNORECASE),
            'unclear_pronouns': re.compile(r'\b(this|that|it|they)\s+(?!is|are|will|can|should)', re.IGNORECASE),
        }
    
    def _initialize_keywords(self) -> Dict[DocumentType, List[str]]:
        """Initialize keyword patterns for document classification"""
        return {
            DocumentType.ARCHITECTURE: [
                'architecture', 'design', 'pattern', 'component', 'system',
                'microservices', 'api', 'database', 'scalability', 'performance'
            ],
            DocumentType.API_DOCUMENTATION: [
                'endpoint', 'request', 'response', 'parameter', 'authentication',
                'rate limit', 'version', 'sdk', 'client', 'swagger'
            ],
            DocumentType.GUIDE: [
                'guide', 'tutorial', 'how to', 'step by step', 'walkthrough',
                'instructions', 'getting started', 'quickstart'
            ],
            DocumentType.PROMPT: [
                'prompt', 'instruction', 'command', 'directive', 'task',
                'agent', 'ai', 'model', 'generate', 'analyze'
            ],
            DocumentType.REPORT: [
                'report', 'analysis', 'findings', 'results', 'summary',
                'metrics', 'performance', 'audit', 'assessment'
            ],
            DocumentType.AUDIT: [
                'audit', 'review', 'compliance', 'security', 'vulnerability',
                'assessment', 'evaluation', 'inspection', 'check'
            ],
            DocumentType.DEPLOYMENT: [
                'deployment', 'deploy', 'production', 'staging', 'release',
                'environment', 'configuration', 'setup', 'installation'
            ],
            DocumentType.TROUBLESHOOTING: [
                'troubleshoot', 'debug', 'error', 'issue', 'problem',
                'solution', 'fix', 'workaround', 'faq', 'common'
            ]
        }
    
    def _initialize_scoring_weights(self) -> Dict[str, float]:
        """Initialize scoring weights for different criteria"""
        return {
            # Structure & Clarity weights (total: 25 points)
            'has_clear_headings': 8.0,
            'consistent_formatting': 7.0,
            'logical_sections': 6.0,
            'clear_navigation': 4.0,
            
            # Semantic Richness weights (total: 25 points)
            'context_provided': 8.0,
            'examples_included': 7.0,
            'cross_references': 5.0,
            'definitions_present': 5.0,
            
            # Technical Accuracy weights (total: 25 points)
            'code_blocks_formatted': 8.0,
            'accurate_terminology': 7.0,
            'up_to_date_content': 5.0,
            'complete_information': 5.0,
            
            # AI Processing Efficiency weights (total: 25 points)
            'parseable_structure': 10.0,
            'consistent_patterns': 8.0,
            'minimal_ambiguity': 4.0,
            'actionable_content': 3.0,
        }
    
    async def score_document(self, content: str, metadata: DocumentMetadata) -> AIFriendlinessScore:
        """Comprehensive AI-friendliness scoring"""
        
        # Basic content analysis
        content_stats = self._analyze_content_stats(content)
        
        # Score each dimension
        structure_score = await self._score_structure_clarity(content, content_stats)
        semantic_score = await self._score_semantic_richness(content, content_stats)
        technical_score = await self._score_technical_accuracy(content, metadata)
        processing_score = await self._score_processing_efficiency(content, content_stats)
        
        # Calculate overall score
        overall_score = structure_score.structure_score + semantic_score.semantic_score + \
                       technical_score.technical_score + processing_score.processing_score
        
        # Additional metrics
        readability = self._calculate_readability_score(content)
        completeness = self._calculate_completeness_score(content, metadata)
        actionability = self._calculate_actionability_score(content)
        
        return AIFriendlinessScore(
            overall_score=overall_score,
            structure_score=structure_score.structure_score,
            headings_present=structure_score.headings_present,
            consistent_formatting=structure_score.consistent_formatting,
            clear_sections=structure_score.clear_sections,
            
            semantic_score=semantic_score.semantic_score,
            context_provided=semantic_score.context_provided,
            examples_included=semantic_score.examples_included,
            cross_references=semantic_score.cross_references,
            
            technical_score=technical_score.technical_score,
            code_blocks_formatted=technical_score.code_blocks_formatted,
            accurate_terminology=technical_score.accurate_terminology,
            up_to_date_content=technical_score.up_to_date_content,
            
            processing_score=processing_score.processing_score,
            parseable_structure=processing_score.parseable_structure,
            consistent_patterns=processing_score.consistent_patterns,
            minimal_ambiguity=processing_score.minimal_ambiguity,
            
            readability_score=readability,
            completeness_score=completeness,
            actionability_score=actionability
        )
    
    def _analyze_content_stats(self, content: str) -> Dict[str, Any]:
        """Analyze basic content statistics"""
        lines = content.split('\n')
        words = content.split()
        
        return {
            'line_count': len(lines),
            'word_count': len(words),
            'character_count': len(content),
            'avg_line_length': sum(len(line) for line in lines) / max(len(lines), 1),
            'avg_word_length': sum(len(word) for word in words) / max(len(words), 1),
            'blank_lines': sum(1 for line in lines if not line.strip()),
            'headings': len(self.patterns['headings'].findall(content)),
            'code_blocks': len(self.patterns['code_blocks'].findall(content)),
            'bullet_points': len(self.patterns['bullet_points'].findall(content)),
            'numbered_lists': len(self.patterns['numbered_lists'].findall(content)),
            'cross_references': len(self.patterns['cross_references'].findall(content)),
        }
    
    async def _score_structure_clarity(self, content: str, stats: Dict) -> Any:
        """Score document structure and clarity (0-25 points)"""
        score = 0.0
        
        # Check for clear headings
        headings_present = stats['headings'] > 0
        if headings_present:
            score += self.scoring_weights['has_clear_headings']
            # Bonus for hierarchical structure
            heading_hierarchy = self._analyze_heading_hierarchy(content)
            if heading_hierarchy['is_hierarchical']:
                score += 2.0
        
        # Check consistent formatting  
        consistent_formatting = self._check_consistent_formatting(content)
        if consistent_formatting:
            score += self.scoring_weights['consistent_formatting']
        
        # Check for logical sections
        clear_sections = self._has_clear_sections(content, stats)
        if clear_sections:
            score += self.scoring_weights['logical_sections']
        
        # Navigation aids (TOC, links, etc.)
        has_navigation = stats['cross_references'] > 0 or 'table of contents' in content.lower()
        if has_navigation:
            score += self.scoring_weights['clear_navigation']
        
        return type('StructureScore', (), {
            'structure_score': min(25.0, score),
            'headings_present': headings_present,
            'consistent_formatting': consistent_formatting,
            'clear_sections': clear_sections
        })()
    
    async def _score_semantic_richness(self, content: str, stats: Dict) -> Any:
        """Score semantic richness and context (0-25 points)"""
        score = 0.0
        
        # Context indicators
        context_patterns = ['background', 'overview', 'introduction', 'context', 'why']
        context_provided = any(pattern in content.lower() for pattern in context_patterns)
        if context_provided:
            score += self.scoring_weights['context_provided']
        
        # Examples and illustrations
        example_count = len(self.patterns['examples'].findall(content))
        examples_included = example_count > 0
        if examples_included:
            score += self.scoring_weights['examples_included']
            # Bonus for multiple examples
            if example_count > 2:
                score += 2.0
        
        # Cross-references and connections
        cross_references = stats['cross_references'] > 0
        if cross_references:
            score += self.scoring_weights['cross_references']
        
        # Definitions and explanations
        definition_count = len(self.patterns['definitions'].findall(content))
        definitions_present = definition_count > 0
        if definitions_present:
            score += self.scoring_weights['definitions_present']
        
        return type('SemanticScore', (), {
            'semantic_score': min(25.0, score),
            'context_provided': context_provided,
            'examples_included': examples_included,
            'cross_references': cross_references
        })()
    
    async def _score_technical_accuracy(self, content: str, metadata: DocumentMetadata) -> Any:
        """Score technical accuracy and completeness (0-25 points)"""
        score = 0.0
        
        # Formatted code blocks
        code_blocks_formatted = self._check_code_formatting(content)
        if code_blocks_formatted:
            score += self.scoring_weights['code_blocks_formatted']
        
        # Technical terminology accuracy  
        accurate_terminology = self._check_terminology_accuracy(content, metadata)
        if accurate_terminology:
            score += self.scoring_weights['accurate_terminology']
        
        # Content freshness
        up_to_date_content = self._check_content_freshness(content, metadata)
        if up_to_date_content:
            score += self.scoring_weights['up_to_date_content']
        
        # Completeness check
        complete_information = self._check_information_completeness(content)
        if complete_information:
            score += self.scoring_weights['complete_information']
        
        return type('TechnicalScore', (), {
            'technical_score': min(25.0, score),
            'code_blocks_formatted': code_blocks_formatted,
            'accurate_terminology': accurate_terminology,
            'up_to_date_content': up_to_date_content
        })()
    
    async def _score_processing_efficiency(self, content: str, stats: Dict) -> Any:
        """Score AI processing efficiency (0-25 points)"""
        score = 0.0
        
        # Parseable structure
        parseable_structure = self._check_parseable_structure(content, stats)
        if parseable_structure:
            score += self.scoring_weights['parseable_structure']
        
        # Consistent patterns
        consistent_patterns = self._check_pattern_consistency(content)
        if consistent_patterns:
            score += self.scoring_weights['consistent_patterns']
        
        # Minimal ambiguity
        ambiguity_score = self._calculate_ambiguity_score(content)
        minimal_ambiguity = ambiguity_score > 0.7  # Less ambiguous = better
        if minimal_ambiguity:
            score += self.scoring_weights['minimal_ambiguity']
        
        # Actionable content
        actionable_content = self._check_actionability(content)
        if actionable_content:
            score += self.scoring_weights['actionable_content']
        
        return type('ProcessingScore', (), {
            'processing_score': min(25.0, score),
            'parseable_structure': parseable_structure,
            'consistent_patterns': consistent_patterns,
            'minimal_ambiguity': minimal_ambiguity
        })()
    
    def _analyze_heading_hierarchy(self, content: str) -> Dict[str, Any]:
        """Analyze heading structure for hierarchy"""
        headings = self.patterns['headings'].findall(content)
        heading_levels = [len(h.split()[0]) for h in headings]  # Count # characters
        
        return {
            'is_hierarchical': len(set(heading_levels)) > 1,
            'max_depth': max(heading_levels) if heading_levels else 0,
            'level_distribution': {i: heading_levels.count(i) for i in set(heading_levels)}
        }
    
    def _check_consistent_formatting(self, content: str) -> bool:
        """Check for consistent formatting patterns"""
        # Check bullet point consistency
        bullet_styles = set(re.findall(r'^\s*([-*+])', content, re.MULTILINE))
        consistent_bullets = len(bullet_styles) <= 1
        
        # Check heading consistency
        heading_styles = set(re.findall(r'^(#{1,6})', content, re.MULTILINE))
        consistent_headings = len(heading_styles) > 0
        
        # Check code block consistency
        code_block_patterns = len(re.findall(r'```(\w+)?', content))
        has_code_blocks = code_block_patterns > 0
        
        return consistent_bullets and consistent_headings
    
    def _has_clear_sections(self, content: str, stats: Dict) -> bool:
        """Check if document has clear logical sections"""
        section_indicators = [
            'overview', 'introduction', 'getting started', 'installation',
            'usage', 'examples', 'api', 'configuration', 'troubleshooting',
            'conclusion', 'references', 'appendix'
        ]
        
        sections_found = sum(1 for indicator in section_indicators 
                           if indicator in content.lower())
        
        return sections_found >= 3 and stats['headings'] >= 2
    
    def _check_code_formatting(self, content: str) -> bool:
        """Check if code blocks are properly formatted"""
        code_blocks = self.patterns['code_blocks'].findall(content)
        inline_code = self.patterns['inline_code'].findall(content)
        
        # At least some code formatting present
        has_formatted_code = len(code_blocks) > 0 or len(inline_code) > 0
        
        # Check for language specification in code blocks
        lang_specified = len(re.findall(r'```\w+', content)) > 0
        
        return has_formatted_code
    
    def _check_terminology_accuracy(self, content: str, metadata: DocumentMetadata) -> bool:
        """Check for accurate technical terminology"""
        # This is a simplified check - in production, this would use NLP models
        
        # Check for common technical terms
        technical_terms = [
            'api', 'database', 'server', 'client', 'authentication',
            'configuration', 'deployment', 'environment', 'endpoint'
        ]
        
        technical_term_count = sum(1 for term in technical_terms 
                                 if term in content.lower())
        
        # Avoid buzzword overload
        buzzwords = ['synergy', 'paradigm', 'leverage', 'utilize']
        buzzword_count = sum(1 for word in buzzwords if word in content.lower())
        
        return technical_term_count > 0 and buzzword_count < 3
    
    def _check_content_freshness(self, content: str, metadata: DocumentMetadata) -> bool:
        """Check if content appears up-to-date"""
        # Check modification date
        days_old = (datetime.now() - metadata.modified_at).days
        recently_modified = days_old < 90  # 3 months
        
        # Check for outdated references
        outdated_patterns = [
            r'\b20(1[0-9]|2[0-2])\b',  # Years 2010-2022
            r'\bpython\s*2\b',         # Python 2
            r'\bnode\s*[0-9]\b',       # Old Node versions
        ]
        
        has_outdated_refs = any(re.search(pattern, content, re.IGNORECASE) 
                               for pattern in outdated_patterns)
        
        return recently_modified and not has_outdated_refs
    
    def _check_information_completeness(self, content: str) -> bool:
        """Check if information appears complete"""
        # Check for placeholder indicators
        placeholders = len(self.patterns['placeholder_text'].findall(content))
        todo_items = len(self.patterns['todo_items'].findall(content))
        
        # Check for sections that should be present
        word_count = len(content.split())
        has_substance = word_count > 100  # Minimum content
        
        return placeholders < 3 and todo_items < 2 and has_substance
    
    def _check_parseable_structure(self, content: str, stats: Dict) -> bool:
        """Check if structure is easily parseable by AI"""
        # Well-structured documents have:
        structure_score = 0
        
        if stats['headings'] > 0:
            structure_score += 1
        if stats['bullet_points'] > 0 or stats['numbered_lists'] > 0:
            structure_score += 1
        if stats['code_blocks'] > 0:
            structure_score += 1
        if len(re.findall(r'\n\n', content)) > 2:  # Paragraph breaks
            structure_score += 1
        
        return structure_score >= 3
    
    def _check_pattern_consistency(self, content: str) -> bool:
        """Check for consistent patterns throughout document"""
        # This is a simplified check for demonstration
        lines = content.split('\n')
        
        # Check heading pattern consistency
        heading_lines = [line for line in lines if line.strip().startswith('#')]
        consistent_heading_spacing = True
        
        if len(heading_lines) > 1:
            # Check if headings have consistent spacing patterns
            heading_positions = [lines.index(h) for h in heading_lines]
            spacing_patterns = [heading_positions[i+1] - heading_positions[i] 
                              for i in range(len(heading_positions)-1)]
            # Allow some variation but not too much
            avg_spacing = sum(spacing_patterns) / len(spacing_patterns)
            consistent_heading_spacing = all(abs(s - avg_spacing) < avg_spacing * 0.5 
                                           for s in spacing_patterns)
        
        return consistent_heading_spacing
    
    def _calculate_ambiguity_score(self, content: str) -> float:
        """Calculate content ambiguity score (higher = less ambiguous)"""
        # Count ambiguous pronouns
        ambiguous_pronouns = len(self.patterns['unclear_pronouns'].findall(content))
        total_words = len(content.split())
        
        if total_words == 0:
            return 0.0
        
        # Score based on pronoun density (lower is better)
        pronoun_density = ambiguous_pronouns / total_words
        ambiguity_score = max(0.0, 1.0 - (pronoun_density * 10))  # Scale and invert
        
        return ambiguity_score
    
    def _check_actionability(self, content: str) -> bool:
        """Check if content contains actionable information"""
        actionable_patterns = [
            r'\b(run|execute|install|configure|set|create|update)\b',
            r'\b(step \d+|first|next|then|finally)\b',
            r'\b(command|script|function|method)\b'
        ]
        
        actionable_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                             for pattern in actionable_patterns)
        
        return actionable_count > 3
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score using standard metrics"""
        try:
            # Use Flesch Reading Ease score
            ease_score = flesch_reading_ease(content)
            # Convert to 0-100 scale where higher is better
            return max(0.0, min(100.0, ease_score))
        except:
            # Fallback calculation
            words = content.split()
            sentences = content.count('.') + content.count('!') + content.count('?')
            
            if sentences == 0:
                return 50.0  # Neutral score
            
            avg_words_per_sentence = len(words) / sentences
            # Simple readability approximation
            readability = max(0.0, 100.0 - (avg_words_per_sentence * 2))
            return min(100.0, readability)
    
    def _calculate_completeness_score(self, content: str, metadata: DocumentMetadata) -> float:
        """Calculate content completeness score"""
        completeness = 0.0
        
        # Length-based completeness
        word_count = len(content.split())
        if word_count > 100:
            completeness += 25.0
        elif word_count > 50:
            completeness += 15.0
        elif word_count > 20:
            completeness += 10.0
        
        # Structure-based completeness
        has_intro = any(word in content.lower() 
                       for word in ['introduction', 'overview', 'about'])
        has_content = len(self.patterns['headings'].findall(content)) >= 2
        has_examples = len(self.patterns['examples'].findall(content)) > 0
        
        if has_intro:
            completeness += 20.0
        if has_content:
            completeness += 25.0
        if has_examples:
            completeness += 15.0
        
        # Missing placeholder penalty
        placeholders = len(self.patterns['placeholder_text'].findall(content))
        completeness -= (placeholders * 5.0)
        
        return max(0.0, min(100.0, completeness))
    
    def _calculate_actionability_score(self, content: str) -> float:
        """Calculate how actionable the content is"""
        actionability = 0.0
        
        # Procedural elements
        procedures = len(self.patterns['procedures'].findall(content))
        if procedures > 0:
            actionability += min(40.0, procedures * 10.0)
        
        # Code examples
        code_blocks = len(self.patterns['code_blocks'].findall(content))
        if code_blocks > 0:
            actionability += min(30.0, code_blocks * 15.0)
        
        # Specific instructions
        instruction_words = ['install', 'run', 'execute', 'configure', 'setup']
        instruction_count = sum(content.lower().count(word) for word in instruction_words)
        actionability += min(30.0, instruction_count * 3.0)
        
        return min(100.0, actionability)


class DocumentClassificationEngine:
    """Engine for classifying documents by type and purpose"""
    
    def __init__(self):
        self.scorer = AIFriendlinessScorer()
    
    async def classify_document(self, content: str, metadata: DocumentMetadata) -> DocumentClassification:
        """Classify document type and extract metadata"""
        
        # Content-based classification
        primary_type, confidence = self._classify_by_content(content)
        
        # Path-based hints
        path_type = self._classify_by_path(metadata.source_path)
        
        # Combine evidence
        if path_type and confidence < 0.8:
            primary_type = path_type
            confidence = min(0.9, confidence + 0.2)
        
        # Extract keywords and entities
        keywords = self._extract_keywords(content)
        entities = self._extract_entities(content)
        topics = self._extract_topics(content, primary_type)
        
        # Analyze relationships
        dependencies = self._extract_dependencies(content)
        references = self._extract_references(content)
        
        # Determine secondary types
        secondary_types = self._identify_secondary_types(content, primary_type)
        
        return DocumentClassification(
            primary_type=primary_type,
            secondary_types=secondary_types,
            confidence=confidence,
            keywords=keywords,
            entities=entities,
            topics=topics,
            dependencies=dependencies,
            references=references
        )
    
    def _classify_by_content(self, content: str) -> Tuple[DocumentType, float]:
        """Classify based on content analysis"""
        content_lower = content.lower()
        type_scores = {}
        
        # Score each document type based on keyword presence
        for doc_type, keywords in self.scorer.keywords.items():
            score = 0.0
            for keyword in keywords:
                # Count occurrences with diminishing returns
                count = content_lower.count(keyword)
                if count > 0:
                    score += min(1.0, count * 0.3)  # Max 1 point per keyword
            
            # Normalize by keyword count
            type_scores[doc_type] = score / len(keywords)
        
        # Find best match
        best_type = max(type_scores, key=type_scores.get)
        confidence = type_scores[best_type]
        
        # Apply content structure bonuses
        if best_type == DocumentType.API_DOCUMENTATION:
            if 'endpoint' in content_lower and 'response' in content_lower:
                confidence *= 1.3
        elif best_type == DocumentType.GUIDE:
            if re.search(r'step \d+', content_lower):
                confidence *= 1.2
        elif best_type == DocumentType.ARCHITECTURE:
            if 'component' in content_lower and 'design' in content_lower:
                confidence *= 1.25
        
        return best_type, min(1.0, confidence)
    
    def _classify_by_path(self, file_path: str) -> Optional[DocumentType]:
        """Classify based on file path patterns"""
        path_lower = file_path.lower()
        filename = Path(file_path).name.lower()
        
        # Direct filename matches
        if filename == 'readme.md':
            return DocumentType.README
        elif 'api' in filename and ('doc' in filename or 'reference' in filename):
            return DocumentType.API_DOCUMENTATION
        elif filename.endswith('_prompt.md'):
            return DocumentType.PROMPT
        elif 'audit' in filename:
            return DocumentType.AUDIT
        elif 'deployment' in filename or 'deploy' in filename:
            return DocumentType.DEPLOYMENT
        elif 'architecture' in filename or 'arch' in filename:
            return DocumentType.ARCHITECTURE
        elif 'report' in filename:
            return DocumentType.REPORT
        elif 'guide' in filename or 'tutorial' in filename:
            return DocumentType.GUIDE
        elif 'troubleshoot' in filename or 'debug' in filename:
            return DocumentType.TROUBLESHOOTING
        elif 'integration' in filename:
            return DocumentType.INTEGRATION
        elif 'config' in filename:
            return DocumentType.CONFIGURATION
        
        # Directory-based classification
        if '/docs/' in path_lower:
            if '/api/' in path_lower:
                return DocumentType.API_DOCUMENTATION
            elif '/architecture/' in path_lower:
                return DocumentType.ARCHITECTURE
            elif '/guides/' in path_lower:
                return DocumentType.GUIDE
        
        return None
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract key technical terms from content"""
        # This is a simplified version - production would use NLP models
        technical_terms = [
            'api', 'endpoint', 'database', 'server', 'client',
            'authentication', 'authorization', 'configuration', 'deployment',
            'microservice', 'architecture', 'scalability', 'performance',
            'monitoring', 'logging', 'security', 'testing'
        ]
        
        found_terms = []
        content_lower = content.lower()
        for term in technical_terms:
            if term in content_lower:
                found_terms.append(term)
        
        return found_terms[:10]  # Limit to top terms
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract named entities (services, technologies, etc.)"""
        # Common tech entities
        entities = []
        
        # Technology patterns
        tech_patterns = [
            r'\b(FastAPI|Django|Flask|Express|React|Vue|Angular)\b',
            r'\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch)\b',
            r'\b(Docker|Kubernetes|Helm|Terraform)\b',
            r'\b(AWS|Azure|GCP|Heroku)\b',
            r'\b(Git|GitHub|GitLab|Bitbucket)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))[:15]  # Dedupe and limit
    
    def _extract_topics(self, content: str, doc_type: DocumentType) -> List[str]:
        """Extract main topics based on document type"""
        topics = []
        content_lower = content.lower()
        
        if doc_type == DocumentType.API_DOCUMENTATION:
            if 'authentication' in content_lower:
                topics.append('authentication')
            if 'rate limit' in content_lower:
                topics.append('rate_limiting')
            if 'pagination' in content_lower:
                topics.append('pagination')
        elif doc_type == DocumentType.ARCHITECTURE:
            if 'microservice' in content_lower:
                topics.append('microservices')
            if 'event' in content_lower:
                topics.append('event_driven')
            if 'cache' in content_lower:
                topics.append('caching')
        elif doc_type == DocumentType.DEPLOYMENT:
            if 'docker' in content_lower:
                topics.append('containerization')
            if 'environment' in content_lower:
                topics.append('environment_config')
        
        return topics
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract file/system dependencies mentioned in content"""
        dependencies = []
        
        # File references
        file_patterns = [
            r'`([^`]+\.(?:py|js|ts|json|yaml|yml|md))`',
            r'"([^"]+\.(?:py|js|ts|json|yaml|yml|md))"',
            r"'([^']+\.(?:py|js|ts|json|yaml|yml|md))'"
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content)
            dependencies.extend(matches)
        
        return list(set(dependencies))[:10]
    
    def _extract_references(self, content: str) -> List[str]:
        """Extract references to other documents or resources"""
        references = []
        
        # Markdown links
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for link_text, link_url in markdown_links:
            if link_url.endswith('.md'):
                references.append(link_url)
        
        # Direct file mentions
        doc_mentions = re.findall(r'\b([A-Z_]+\.md)\b', content)
        references.extend(doc_mentions)
        
        return list(set(references))[:10]
    
    def _identify_secondary_types(self, content: str, primary_type: DocumentType) -> List[DocumentType]:
        """Identify secondary document types"""
        secondary = []
        content_lower = content.lower()
        
        # Check for secondary characteristics
        if 'troubleshoot' in content_lower or 'debug' in content_lower:
            if primary_type != DocumentType.TROUBLESHOOTING:
                secondary.append(DocumentType.TROUBLESHOOTING)
        
        if 'example' in content_lower and primary_type not in [DocumentType.GUIDE, DocumentType.API_DOCUMENTATION]:
            secondary.append(DocumentType.GUIDE)
        
        if 'config' in content_lower and primary_type != DocumentType.CONFIGURATION:
            secondary.append(DocumentType.CONFIGURATION)
        
        return secondary[:3]  # Limit secondary types