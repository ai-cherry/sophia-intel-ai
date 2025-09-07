"""
Web Research Teams for Sophia and Artemis

Provides deep web research capabilities with fact-checking, citation tracking,
and confidence scoring for both Business Intelligence and Code domains.
"""

import asyncio
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.core.circuit_breaker import CircuitBreaker
from app.core.portkey_manager import TaskType, get_portkey_manager
from app.memory.unified_memory_router import DocChunk, MemoryDomain, get_memory_router

logger = logging.getLogger(__name__)


class ResearchDomain(Enum):
    """Research domain types"""

    BUSINESS = "business"  # Sophia domain
    TECHNICAL = "technical"  # Artemis domain
    GENERAL = "general"  # Cross-domain


class SourceReliability(Enum):
    """Source reliability ratings"""

    VERIFIED = "verified"  # Official sources, documentation
    TRUSTED = "trusted"  # Well-known publications
    MODERATE = "moderate"  # General sources
    UNCERTAIN = "uncertain"  # Unverified sources
    UNRELIABLE = "unreliable"  # Known unreliable sources


class ResearchProvider(Enum):
    """Research provider types"""

    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    EXA = "exa"
    BRAVE = "brave"
    SERPER = "serper"
    APIFY = "apify"  # For scraping
    ZENROWS = "zenrows"  # For scraping


@dataclass
class Citation:
    """Research citation"""

    source_url: str
    source_name: str
    timestamp: datetime
    excerpt: str
    confidence: float
    reliability: SourceReliability


@dataclass
class ResearchFinding:
    """Individual research finding"""

    content: str
    citations: List[Citation]
    confidence: float
    domain: ResearchDomain
    keywords: List[str]
    contradictions: Optional[List[str]] = None


@dataclass
class ResearchReport:
    """Complete research report"""

    query: str
    domain: ResearchDomain
    findings: List[ResearchFinding]
    summary: str
    total_confidence: float
    research_time: float
    provider_used: ResearchProvider
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResearchCache:
    """Cache for research results"""

    def __init__(self):
        self.memory_router = get_memory_router()
        self.cache_ttl = timedelta(hours=24)

    async def get(self, query: str, domain: ResearchDomain) -> Optional[ResearchReport]:
        """Get cached research report"""
        key = self._generate_key(query, domain)
        cached = await self.memory_router.get_ephemeral(key)

        if cached:
            report_dict = json.loads(cached)
            # Reconstruct report from dict
            return self._dict_to_report(report_dict)

        return None

    async def put(self, report: ResearchReport) -> None:
        """Cache research report"""
        key = self._generate_key(report.query, report.domain)
        report_dict = self._report_to_dict(report)
        await self.memory_router.put_ephemeral(
            key, json.dumps(report_dict), ttl_s=int(self.cache_ttl.total_seconds())
        )

    def _generate_key(self, query: str, domain: ResearchDomain) -> str:
        """Generate cache key"""
        content = f"{query}:{domain.value}"
        return f"research:{hashlib.md5(content.encode()).hexdigest()}"

    def _report_to_dict(self, report: ResearchReport) -> Dict[str, Any]:
        """Convert report to dict for caching"""
        return {
            "query": report.query,
            "domain": report.domain.value,
            "findings": [
                {
                    "content": f.content,
                    "citations": [
                        {
                            "source_url": c.source_url,
                            "source_name": c.source_name,
                            "timestamp": c.timestamp.isoformat(),
                            "excerpt": c.excerpt,
                            "confidence": c.confidence,
                            "reliability": c.reliability.value,
                        }
                        for c in f.citations
                    ],
                    "confidence": f.confidence,
                    "keywords": f.keywords,
                    "contradictions": f.contradictions,
                }
                for f in report.findings
            ],
            "summary": report.summary,
            "total_confidence": report.total_confidence,
            "research_time": report.research_time,
            "provider_used": report.provider_used.value,
            "cached": True,
            "metadata": report.metadata,
        }

    def _dict_to_report(self, data: Dict[str, Any]) -> ResearchReport:
        """Convert dict to report"""
        findings = []
        for f_data in data["findings"]:
            citations = [
                Citation(
                    source_url=c["source_url"],
                    source_name=c["source_name"],
                    timestamp=datetime.fromisoformat(c["timestamp"]),
                    excerpt=c["excerpt"],
                    confidence=c["confidence"],
                    reliability=SourceReliability(c["reliability"]),
                )
                for c in f_data["citations"]
            ]
            findings.append(
                ResearchFinding(
                    content=f_data["content"],
                    citations=citations,
                    confidence=f_data["confidence"],
                    domain=ResearchDomain(data["domain"]),
                    keywords=f_data["keywords"],
                    contradictions=f_data.get("contradictions"),
                )
            )

        return ResearchReport(
            query=data["query"],
            domain=ResearchDomain(data["domain"]),
            findings=findings,
            summary=data["summary"],
            total_confidence=data["total_confidence"],
            research_time=data["research_time"],
            provider_used=ResearchProvider(data["provider_used"]),
            cached=data.get("cached", False),
            metadata=data.get("metadata", {}),
        )


class BaseResearchProvider(ABC):
    """Base class for research providers"""

    def __init__(self, provider: ResearchProvider):
        self.provider = provider
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60, expected_exception=Exception
        )
        self.portkey_manager = get_portkey_manager()

    @abstractmethod
    async def search(self, query: str, domain: ResearchDomain, **kwargs) -> List[ResearchFinding]:
        """Execute search with provider"""
        pass

    @abstractmethod
    async def verify_source(self, url: str) -> SourceReliability:
        """Verify source reliability"""
        pass

    async def _rate_confidence(self, content: str, citations: List[Citation]) -> float:
        """Rate confidence of findings"""
        # Base confidence on number and quality of citations
        if not citations:
            return 0.3

        reliability_scores = {
            SourceReliability.VERIFIED: 1.0,
            SourceReliability.TRUSTED: 0.8,
            SourceReliability.MODERATE: 0.6,
            SourceReliability.UNCERTAIN: 0.4,
            SourceReliability.UNRELIABLE: 0.2,
        }

        scores = [reliability_scores[c.reliability] * c.confidence for c in citations]
        return min(0.95, sum(scores) / len(scores))


class PerplexityProvider(BaseResearchProvider):
    """Perplexity research provider"""

    def __init__(self):
        super().__init__(ResearchProvider.PERPLEXITY)
        self.api_key = self.portkey_manager.get_virtual_key("perplexity")

    async def search(self, query: str, domain: ResearchDomain, **kwargs) -> List[ResearchFinding]:
        """Execute Perplexity search"""
        try:
            # Use Portkey to call Perplexity with citations
            messages = [
                {
                    "role": "system",
                    "content": f"You are a research assistant specializing in {domain.value} domain. Provide detailed, factual answers with citations.",
                },
                {"role": "user", "content": query},
            ]

            result = await self.portkey_manager.execute_with_fallback(
                task_type=TaskType.RESEARCH, messages=messages, provider="perplexity", **kwargs
            )

            # Parse Perplexity response with citations
            findings = await self._parse_perplexity_response(result, domain)
            return findings

        except Exception as e:
            logger.error(f"Perplexity search failed: {e}")
            return []

    async def verify_source(self, url: str) -> SourceReliability:
        """Verify source reliability"""
        domain = urlparse(url).netloc.lower()

        # Known reliable domains
        verified_domains = {
            "docs.python.org",
            "developer.mozilla.org",
            "github.com",
            "arxiv.org",
            "stackoverflow.com",
        }

        trusted_domains = {
            "medium.com",
            "dev.to",
            "hackernews.com",
            "reddit.com",
            "wikipedia.org",
        }

        if any(d in domain for d in verified_domains):
            return SourceReliability.VERIFIED
        elif any(d in domain for d in trusted_domains):
            return SourceReliability.TRUSTED
        else:
            return SourceReliability.MODERATE

    async def _parse_perplexity_response(
        self, response: Dict[str, Any], domain: ResearchDomain
    ) -> List[ResearchFinding]:
        """Parse Perplexity response into findings"""
        findings = []

        # Extract content and citations from response
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        citations_data = response.get("citations", [])

        # Create finding with citations
        citations = []
        for cite in citations_data:
            reliability = await self.verify_source(cite.get("url", ""))
            citations.append(
                Citation(
                    source_url=cite.get("url", ""),
                    source_name=cite.get("title", "Unknown"),
                    timestamp=datetime.now(),
                    excerpt=cite.get("snippet", ""),
                    confidence=0.8,
                    reliability=reliability,
                )
            )

        if content:
            confidence = await self._rate_confidence(content, citations)
            findings.append(
                ResearchFinding(
                    content=content,
                    citations=citations,
                    confidence=confidence,
                    domain=domain,
                    keywords=self._extract_keywords(content),
                )
            )

        return findings

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Simple keyword extraction - could be enhanced with NLP
        import re

        words = re.findall(r"\b[A-Z][a-z]+\b|\b[A-Z]+\b", content)
        return list(set(words))[:10]


class FactChecker:
    """Fact checking and contradiction detection"""

    def __init__(self):
        self.portkey_manager = get_portkey_manager()

    async def check_facts(self, findings: List[ResearchFinding]) -> List[ResearchFinding]:
        """Check facts and identify contradictions"""
        if len(findings) < 2:
            return findings

        # Check for contradictions between findings
        for i, finding in enumerate(findings):
            contradictions = await self._find_contradictions(finding, findings[i + 1 :])
            if contradictions:
                finding.contradictions = contradictions
                # Reduce confidence when contradictions found
                finding.confidence *= 0.8

        return findings

    async def _find_contradictions(
        self, finding: ResearchFinding, other_findings: List[ResearchFinding]
    ) -> List[str]:
        """Find contradictions with other findings"""
        if not other_findings:
            return []

        contradictions = []

        # Use LLM to identify contradictions
        for other in other_findings:
            messages = [
                {
                    "role": "system",
                    "content": "You are a fact checker. Identify any contradictions between two statements. Return only contradictions, or 'None' if there are none.",
                },
                {
                    "role": "user",
                    "content": f"Statement 1: {finding.content}\n\nStatement 2: {other.content}",
                },
            ]

            result = await self.portkey_manager.execute_with_fallback(
                task_type=TaskType.RESEARCH, messages=messages, model="fast"
            )

            response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            if response and response.lower() != "none":
                contradictions.append(response)

        return contradictions


class WebResearchTeam:
    """Orchestrates web research with multiple agents"""

    def __init__(self, domain: ResearchDomain):
        self.domain = domain
        self.cache = ResearchCache()
        self.fact_checker = FactChecker()
        self.providers = self._init_providers()
        self.memory_router = get_memory_router()

    def _init_providers(self) -> Dict[ResearchProvider, BaseResearchProvider]:
        """Initialize research providers"""
        providers = {}

        # Add available providers
        try:
            providers[ResearchProvider.PERPLEXITY] = PerplexityProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Perplexity provider: {e}")

        # TODO: Add Tavily, Exa, Brave providers

        return providers

    async def research(
        self, query: str, use_cache: bool = True, deep_search: bool = False
    ) -> ResearchReport:
        """Execute research with caching and fact-checking"""
        start_time = datetime.now()

        # Check cache
        if use_cache:
            cached_report = await self.cache.get(query, self.domain)
            if cached_report:
                logger.info(f"Returning cached research for: {query}")
                return cached_report

        # Execute research with available providers
        all_findings = []
        provider_used = None

        for provider_type, provider in self.providers.items():
            try:
                findings = await provider.search(query, self.domain)
                if findings:
                    all_findings.extend(findings)
                    provider_used = provider_type
                    if not deep_search:
                        break  # Use first successful provider unless deep search
            except Exception as e:
                logger.error(f"Provider {provider_type} failed: {e}")
                continue

        if not all_findings:
            # Return empty report if no findings
            return ResearchReport(
                query=query,
                domain=self.domain,
                findings=[],
                summary="No findings available",
                total_confidence=0.0,
                research_time=0.0,
                provider_used=ResearchProvider.PERPLEXITY,
            )

        # Fact check findings
        checked_findings = await self.fact_checker.check_facts(all_findings)

        # Generate summary
        summary = await self._generate_summary(checked_findings)

        # Calculate total confidence
        total_confidence = sum(f.confidence for f in checked_findings) / len(checked_findings)

        # Create report
        report = ResearchReport(
            query=query,
            domain=self.domain,
            findings=checked_findings,
            summary=summary,
            total_confidence=total_confidence,
            research_time=(datetime.now() - start_time).total_seconds(),
            provider_used=provider_used or ResearchProvider.PERPLEXITY,
        )

        # Cache report
        await self.cache.put(report)

        # Store in long-term memory if high confidence
        if total_confidence > 0.7:
            await self._store_in_memory(report)

        return report

    async def _generate_summary(self, findings: List[ResearchFinding]) -> str:
        """Generate research summary"""
        if not findings:
            return "No findings to summarize"

        # Combine all findings
        combined = "\n\n".join([f.content for f in findings])

        messages = [
            {
                "role": "system",
                "content": f"You are a {self.domain.value} research summarizer. Create a concise summary of research findings.",
            },
            {"role": "user", "content": f"Summarize these findings:\n\n{combined}"},
        ]

        result = await get_portkey_manager().execute_with_fallback(
            task_type=TaskType.RESEARCH, messages=messages, model="fast"
        )

        return result.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def _store_in_memory(self, report: ResearchReport) -> None:
        """Store high-confidence findings in long-term memory"""
        memory_domain = (
            MemoryDomain.SOPHIA
            if report.domain == ResearchDomain.BUSINESS
            else MemoryDomain.ARTEMIS
        )

        chunks = []
        for finding in report.findings:
            if finding.confidence > 0.7:
                chunk = DocChunk(
                    content=finding.content,
                    metadata={
                        "query": report.query,
                        "citations": [c.source_url for c in finding.citations],
                        "confidence": finding.confidence,
                        "timestamp": datetime.now().isoformat(),
                    },
                    embedding=None,  # Will be generated by memory router
                )
                chunks.append(chunk)

        if chunks:
            await self.memory_router.upsert_chunks(chunks, memory_domain)


class SophiaResearchTeam(WebResearchTeam):
    """Sophia-specific research team for Business Intelligence"""

    def __init__(self):
        super().__init__(ResearchDomain.BUSINESS)

    async def market_research(self, companies: List[str], topics: List[str]) -> ResearchReport:
        """Specialized market research"""
        query = f"Market analysis for {', '.join(companies)} regarding {', '.join(topics)}"
        report = await self.research(query, deep_search=True)

        # Enhance with business-specific analysis
        report.metadata["companies"] = companies
        report.metadata["topics"] = topics
        report.metadata["research_type"] = "market_analysis"

        return report

    async def competitive_analysis(self, company: str, competitors: List[str]) -> ResearchReport:
        """Competitive analysis research"""
        query = f"Competitive analysis: {company} vs {', '.join(competitors)}"
        report = await self.research(query, deep_search=True)

        report.metadata["target_company"] = company
        report.metadata["competitors"] = competitors
        report.metadata["research_type"] = "competitive_analysis"

        return report


class ArtemisResearchTeam(WebResearchTeam):
    """Artemis-specific research team for Technical/Code domains"""

    def __init__(self):
        super().__init__(ResearchDomain.TECHNICAL)

    async def api_research(self, api_name: str, version: Optional[str] = None) -> ResearchReport:
        """Research API changes and documentation"""
        query = f"{api_name} API documentation"
        if version:
            query += f" version {version}"

        report = await self.research(query)
        report.metadata["api_name"] = api_name
        report.metadata["version"] = version
        report.metadata["research_type"] = "api_documentation"

        return report

    async def cve_research(self, keywords: List[str]) -> ResearchReport:
        """Research CVEs and security vulnerabilities"""
        query = f"CVE vulnerabilities: {', '.join(keywords)}"
        report = await self.research(query, deep_search=True)

        report.metadata["keywords"] = keywords
        report.metadata["research_type"] = "security_cve"

        return report

    async def framework_research(self, framework: str, topic: str) -> ResearchReport:
        """Research framework features and best practices"""
        query = f"{framework} best practices for {topic}"
        report = await self.research(query)

        report.metadata["framework"] = framework
        report.metadata["topic"] = topic
        report.metadata["research_type"] = "framework_research"

        return report


# Factory function
def get_research_team(domain: ResearchDomain) -> WebResearchTeam:
    """Get appropriate research team for domain"""
    if domain == ResearchDomain.BUSINESS:
        return SophiaResearchTeam()
    elif domain == ResearchDomain.TECHNICAL:
        return ArtemisResearchTeam()
    else:
        return WebResearchTeam(domain)


if __name__ == "__main__":

    async def main():
        # Test Sophia research
        sophia_team = SophiaResearchTeam()
        report = await sophia_team.market_research(
            companies=["Apple", "Microsoft"], topics=["AI strategy", "cloud services"]
        )
        logger.info(f"Sophia Research: {report.summary}")
        logger.info(f"Confidence: {report.total_confidence:.2%}")

        # Test Artemis research
        artemis_team = ArtemisResearchTeam()
        report = await artemis_team.api_research("OpenAI", "v1")
        logger.info(f"Artemis Research: {report.summary}")
        logger.info(f"Confidence: {report.total_confidence:.2%}")

    asyncio.run(main())
