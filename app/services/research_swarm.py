"""
Research Swarm - Autonomous research system for finding best solutions
Includes browser, scraper, and GitHub tracking capabilities
"""
import os
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse, quote
import hashlib
import re

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import aioredis
from github import Github, GithubException
from pydantic import BaseModel, Field

class SearchResult(BaseModel):
    """Search result from web"""
    url: str
    title: str
    snippet: str
    source: str
    relevance: float = 1.0

class ExtractedContent(BaseModel):
    """Extracted content from a page"""
    url: str
    title: str
    summary: str
    code_blocks: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    implementation_steps: List[str] = Field(default_factory=list)
    
class Solution(BaseModel):
    """Analyzed solution"""
    title: str
    description: str
    category: str
    url: str
    score: float
    implementation_difficulty: str  # easy, medium, hard
    time_estimate: str
    technologies: List[str]
    pros: List[str]
    cons: List[str]
    code_example: Optional[str] = None
    
class ResearchQuery(BaseModel):
    """Research query request"""
    query: str
    context: Dict[str, Any] = Field(default_factory=dict)
    max_results: int = Field(default=10)
    include_code: bool = Field(default=True)
    track_in_github: bool = Field(default=True)

class BrowserAgent:
    """Web browsing and search capabilities"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.search_apis = {
            'google': self._search_google_custom,
            'github': self._search_github,
            'stackoverflow': self._search_stackoverflow
        }
    
    async def initialize(self):
        """Initialize browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def search(self, queries: List[str], max_results: int = 10) -> List[SearchResult]:
        """Multi-source search with deduplication"""
        all_results = []
        
        for query in queries:
            # Search multiple sources
            for source, search_func in self.search_apis.items():
                try:
                    results = await search_func(query, max_results=5)
                    all_results.extend(results)
                except Exception as e:
                    print(f"Search error ({source}): {e}")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # Sort by relevance and return top results
        unique_results.sort(key=lambda x: x.relevance, reverse=True)
        return unique_results[:max_results]
    
    async def _search_google_custom(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search using Google Custom Search API"""
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        cx = os.getenv("GOOGLE_SEARCH_CX")
        
        if not api_key or not cx:
            return []
        
        results = []
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    'key': api_key,
                    'cx': cx,
                    'q': query,
                    'num': max_results
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    results.append(SearchResult(
                        url=item['link'],
                        title=item['title'],
                        snippet=item.get('snippet', ''),
                        source='google',
                        relevance=1.0
                    ))
        
        return results
    
    async def _search_github(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search GitHub repositories and code"""
        token = os.getenv("GITHUB_TOKEN")
        
        results = []
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'token {token}'} if token else {}
            
            # Search repositories
            response = await client.get(
                "https://api.github.com/search/repositories",
                params={'q': query, 'sort': 'stars', 'per_page': max_results},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                for repo in data.get('items', []):
                    results.append(SearchResult(
                        url=repo['html_url'],
                        title=repo['full_name'],
                        snippet=repo.get('description', ''),
                        source='github',
                        relevance=min(repo.get('stargazers_count', 0) / 1000, 1.0)
                    ))
        
        return results
    
    async def _search_stackoverflow(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search StackOverflow"""
        results = []
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.stackexchange.com/2.3/search/advanced",
                params={
                    'q': query,
                    'site': 'stackoverflow',
                    'pagesize': max_results,
                    'order': 'desc',
                    'sort': 'relevance'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    results.append(SearchResult(
                        url=item['link'],
                        title=item['title'],
                        snippet=BeautifulSoup(item.get('body', ''), 'html.parser').text[:200],
                        source='stackoverflow',
                        relevance=min(item.get('score', 0) / 100, 1.0)
                    ))
        
        return results
    
    async def browse_page(self, url: str) -> Optional[str]:
        """Navigate and extract page content"""
        if not self.browser:
            await self.initialize()
        
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Get page content
            content = await page.content()
            await page.close()
            
            return content
            
        except Exception as e:
            print(f"Browse error: {e}")
            return None

class ScraperAgent:
    """Intelligent content extraction"""
    
    def __init__(self):
        self.extractors = {
            'github.com': self._extract_github,
            'stackoverflow.com': self._extract_stackoverflow,
            'medium.com': self._extract_medium,
            'dev.to': self._extract_devto,
            'docs.': self._extract_documentation  # Any docs site
        }
    
    async def extract_content(self, results: List[SearchResult]) -> List[ExtractedContent]:
        """Extract and structure content from search results"""
        extracted = []
        
        for result in results:
            try:
                # Get appropriate extractor
                domain = urlparse(result.url).netloc
                extractor = None
                
                for pattern, func in self.extractors.items():
                    if pattern in domain:
                        extractor = func
                        break
                
                if not extractor:
                    extractor = self._extract_generic
                
                # Extract content
                content = await extractor(result)
                if content:
                    extracted.append(content)
                    
            except Exception as e:
                print(f"Extraction error ({result.url}): {e}")
        
        return extracted
    
    async def _extract_github(self, result: SearchResult) -> Optional[ExtractedContent]:
        """Extract GitHub-specific content"""
        async with httpx.AsyncClient() as client:
            # Parse GitHub URL
            parts = result.url.replace('https://github.com/', '').split('/')
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                
                # Get README
                readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
                readme_response = await client.get(readme_url)
                readme = readme_response.text if readme_response.status_code == 200 else ""
                
                # Extract key information
                content = ExtractedContent(
                    url=result.url,
                    title=result.title,
                    summary=result.snippet or readme[:500],
                    technologies=self._extract_technologies(readme),
                    key_points=self._extract_key_points(readme),
                    implementation_steps=self._extract_steps(readme)
                )
                
                # Get example code from repo
                if '/blob/' in result.url:
                    code_response = await client.get(result.url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/'))
                    if code_response.status_code == 200:
                        content.code_blocks = [code_response.text[:2000]]
                
                return content
        
        return None
    
    async def _extract_stackoverflow(self, result: SearchResult) -> Optional[ExtractedContent]:
        """Extract StackOverflow content"""
        async with httpx.AsyncClient() as client:
            # Get question ID from URL
            question_id = result.url.split('/')[-2] if '/questions/' in result.url else None
            
            if question_id:
                # Use SO API to get detailed answer
                response = await client.get(
                    f"https://api.stackexchange.com/2.3/questions/{question_id}",
                    params={'site': 'stackoverflow', 'filter': '!9Z(-wzu0T'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items'):
                        item = data['items'][0]
                        
                        # Get accepted answer if available
                        answers_response = await client.get(
                            f"https://api.stackexchange.com/2.3/questions/{question_id}/answers",
                            params={'site': 'stackoverflow', 'filter': '!9Z(-wzftf', 'sort': 'votes'}
                        )
                        
                        code_blocks = []
                        if answers_response.status_code == 200:
                            answers = answers_response.json().get('items', [])
                            if answers:
                                # Extract code from top answer
                                answer_html = answers[0].get('body', '')
                                soup = BeautifulSoup(answer_html, 'html.parser')
                                code_blocks = [code.text for code in soup.find_all('code')][:3]
                        
                        return ExtractedContent(
                            url=result.url,
                            title=item['title'],
                            summary=BeautifulSoup(item.get('body', ''), 'html.parser').text[:500],
                            code_blocks=code_blocks,
                            key_points=[f"Score: {item.get('score')}", f"Views: {item.get('view_count')}"],
                            technologies=item.get('tags', [])
                        )
        
        return None
    
    async def _extract_medium(self, result: SearchResult) -> Optional[ExtractedContent]:
        """Extract Medium article content"""
        # Medium requires more complex extraction due to their anti-scraping
        # For now, return basic info
        return ExtractedContent(
            url=result.url,
            title=result.title,
            summary=result.snippet,
            key_points=["Medium article - visit link for full content"]
        )
    
    async def _extract_devto(self, result: SearchResult) -> Optional[ExtractedContent]:
        """Extract dev.to article content"""
        async with httpx.AsyncClient() as client:
            response = await client.get(result.url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract article content
                article = soup.find('div', class_='crayons-article__body')
                if article:
                    # Get code blocks
                    code_blocks = [code.text for code in article.find_all('code')][:3]
                    
                    # Get text content
                    text = article.get_text()
                    
                    return ExtractedContent(
                        url=result.url,
                        title=result.title,
                        summary=text[:500],
                        code_blocks=code_blocks,
                        key_points=self._extract_key_points(text),
                        technologies=self._extract_technologies(text)
                    )
        
        return None
    
    async def _extract_documentation(self, result: SearchResult) -> Optional[ExtractedContent]:
        """Extract documentation site content"""
        async with httpx.AsyncClient() as client:
            response = await client.get(result.url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                text = soup.get_text()
                
                # Extract code examples
                code_blocks = []
                for code in soup.find_all(['code', 'pre']):
                    if len(code.text) > 50:  # Skip small snippets
                        code_blocks.append(code.text)
                        if len(code_blocks) >= 3:
                            break
                
                return ExtractedContent(
                    url=result.url,
                    title=result.title,
                    summary=text[:500],
                    code_blocks=code_blocks,
                    key_points=self._extract_key_points(text),
                    implementation_steps=self._extract_steps(text)
                )
        
        return None
    
    async def _extract_generic(self, result: SearchResult) -> ExtractedContent:
        """Generic content extraction"""
        return ExtractedContent(
            url=result.url,
            title=result.title,
            summary=result.snippet,
            key_points=["Generic extraction - visit link for full content"]
        )
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technology mentions from text"""
        tech_patterns = [
            r'\b(React|Vue|Angular|Svelte)\b',
            r'\b(Node\.?js|Python|Java|Go|Rust|TypeScript|JavaScript)\b',
            r'\b(PostgreSQL|MySQL|MongoDB|Redis|SQLite)\b',
            r'\b(Docker|Kubernetes|AWS|GCP|Azure)\b',
            r'\b(FastAPI|Flask|Django|Express|Spring)\b',
            r'\b(TensorFlow|PyTorch|scikit-learn|Keras)\b'
        ]
        
        technologies = set()
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            technologies.update(matches)
        
        return list(technologies)[:10]
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text"""
        # Look for bullet points or numbered lists
        points = []
        
        # Find lines starting with bullets or numbers
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0] in '•·*-' or (line[0].isdigit() and '.' in line[:3])):
                points.append(line)
                if len(points) >= 5:
                    break
        
        return points
    
    def _extract_steps(self, text: str) -> List[str]:
        """Extract implementation steps from text"""
        steps = []
        
        # Look for step indicators
        step_patterns = [
            r'(?:Step\s+\d+[:.]?\s*)(.+)',
            r'(?:\d+\.\s+)(.+)',
            r'(?:First|Second|Third|Then|Next|Finally)[:,]?\s*(.+)'
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            steps.extend(matches)
            if len(steps) >= 5:
                break
        
        return steps[:5]

class AnalyzerAgent:
    """Analyze and rank solutions"""
    
    def __init__(self):
        self.criteria_weights = {
            'relevance': 0.3,
            'implementation_ease': 0.2,
            'performance': 0.2,
            'maintainability': 0.15,
            'community_support': 0.15
        }
    
    async def evaluate_solutions(self, content_list: List[ExtractedContent], context: Dict[str, Any]) -> List[Solution]:
        """Evaluate and rank extracted solutions"""
        solutions = []
        
        for content in content_list:
            # Score based on various criteria
            scores = {
                'relevance': self._score_relevance(content, context),
                'implementation_ease': self._score_implementation(content),
                'performance': self._score_performance(content),
                'maintainability': self._score_maintainability(content),
                'community_support': self._score_community(content)
            }
            
            # Calculate weighted score
            total_score = sum(scores[k] * self.criteria_weights[k] for k in scores)
            
            # Determine implementation difficulty
            if len(content.implementation_steps) > 10:
                difficulty = 'hard'
                time_estimate = '1-2 weeks'
            elif len(content.implementation_steps) > 5:
                difficulty = 'medium'
                time_estimate = '3-5 days'
            else:
                difficulty = 'easy'
                time_estimate = '1-2 days'
            
            # Create solution
            solution = Solution(
                title=content.title,
                description=content.summary,
                category=self._categorize_solution(content),
                url=content.url,
                score=total_score,
                implementation_difficulty=difficulty,
                time_estimate=time_estimate,
                technologies=content.technologies,
                pros=content.pros or self._extract_pros(content),
                cons=content.cons or self._extract_cons(content),
                code_example=content.code_blocks[0] if content.code_blocks else None
            )
            
            solutions.append(solution)
        
        # Sort by score
        solutions.sort(key=lambda x: x.score, reverse=True)
        
        return solutions
    
    def _score_relevance(self, content: ExtractedContent, context: Dict[str, Any]) -> float:
        """Score based on relevance to context"""
        score = 0.5  # Base score
        
        # Check technology match
        project_tech = context.get('technologies', [])
        matching_tech = len(set(content.technologies) & set(project_tech))
        score += min(matching_tech * 0.1, 0.3)
        
        # Check if addresses specific requirements
        requirements = context.get('requirements', [])
        for req in requirements:
            if req.lower() in content.summary.lower():
                score += 0.1
        
        return min(score, 1.0)
    
    def _score_implementation(self, content: ExtractedContent) -> float:
        """Score based on implementation ease"""
        if content.implementation_steps:
            steps = len(content.implementation_steps)
            if steps <= 3:
                return 1.0
            elif steps <= 5:
                return 0.8
            elif steps <= 10:
                return 0.6
            else:
                return 0.4
        
        # If has code examples, easier to implement
        if content.code_blocks:
            return 0.7
        
        return 0.5
    
    def _score_performance(self, content: ExtractedContent) -> float:
        """Score based on performance indicators"""
        performance_keywords = ['fast', 'efficient', 'optimized', 'performance', 'speed', 'quick']
        
        score = 0.5
        text = (content.summary + ' '.join(content.key_points)).lower()
        
        for keyword in performance_keywords:
            if keyword in text:
                score += 0.1
        
        return min(score, 1.0)
    
    def _score_maintainability(self, content: ExtractedContent) -> float:
        """Score based on maintainability"""
        maintainability_keywords = ['clean', 'modular', 'testable', 'documented', 'simple', 'readable']
        
        score = 0.5
        text = (content.summary + ' '.join(content.key_points)).lower()
        
        for keyword in maintainability_keywords:
            if keyword in text:
                score += 0.1
        
        return min(score, 1.0)
    
    def _score_community(self, content: ExtractedContent) -> float:
        """Score based on community support"""
        # GitHub stars, SO votes, etc would be better indicators
        # For now, use source as proxy
        source_scores = {
            'github': 0.9,
            'stackoverflow': 0.8,
            'official_docs': 1.0
        }
        
        if 'github.com' in content.url:
            return source_scores['github']
        elif 'stackoverflow.com' in content.url:
            return source_scores['stackoverflow']
        elif 'docs.' in content.url or 'documentation' in content.url:
            return source_scores['official_docs']
        
        return 0.5
    
    def _categorize_solution(self, content: ExtractedContent) -> str:
        """Categorize the solution"""
        categories = {
            'architecture': ['design', 'pattern', 'structure', 'architecture'],
            'implementation': ['implement', 'code', 'build', 'create'],
            'optimization': ['optimize', 'performance', 'speed', 'improve'],
            'debugging': ['debug', 'fix', 'error', 'issue'],
            'testing': ['test', 'validate', 'verify'],
            'deployment': ['deploy', 'docker', 'kubernetes', 'ci/cd'],
            'security': ['security', 'auth', 'encryption', 'vulnerability']
        }
        
        text = content.summary.lower()
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'general'
    
    def _extract_pros(self, content: ExtractedContent) -> List[str]:
        """Extract pros from content"""
        pros = []
        positive_indicators = ['advantage', 'benefit', 'pro', 'good', 'great', 'excellent', 'best']
        
        for point in content.key_points:
            if any(indicator in point.lower() for indicator in positive_indicators):
                pros.append(point)
        
        return pros[:3] if pros else ['Solution available', 'Documentation exists']
    
    def _extract_cons(self, content: ExtractedContent) -> List[str]:
        """Extract cons from content"""
        cons = []
        negative_indicators = ['disadvantage', 'drawback', 'con', 'issue', 'problem', 'limitation']
        
        for point in content.key_points:
            if any(indicator in point.lower() for indicator in negative_indicators):
                cons.append(point)
        
        return cons[:3] if cons else ['Requires implementation effort']

class GitHubTracker:
    """Track solutions in GitHub repositories"""
    
    def __init__(self):
        self.github = Github(os.getenv("GITHUB_TOKEN"))
        self.org_name = "sophia-intel"
        self.repos = {
            'tech-stack': 'sophia-tech-stack',
            'solutions': 'sophia-solutions',
            'research': 'sophia-research'
        }
    
    async def save_solution(self, solution: Solution, repo_type: str = 'solutions'):
        """Save solution to GitHub repository"""
        try:
            repo = self.github.get_repo(f"{self.org_name}/{self.repos[repo_type]}")
            
            # Create issue for tracking
            issue_body = self._format_solution_issue(solution)
            issue = repo.create_issue(
                title=f"[{solution.category}] {solution.title}",
                body=issue_body,
                labels=[solution.category, f"score-{int(solution.score*10)}", solution.implementation_difficulty]
            )
            
            # If high value, create wiki page
            if solution.score > 0.8:
                self._create_wiki_page(repo, solution)
            
            return issue.html_url
            
        except GithubException as e:
            print(f"GitHub tracking error: {e}")
            return None
    
    def _format_solution_issue(self, solution: Solution) -> str:
        """Format solution as GitHub issue"""
        body = f"""
# {solution.title}

**Score:** {solution.score:.2f}/1.0
**Category:** {solution.category}
**Difficulty:** {solution.implementation_difficulty}
**Time Estimate:** {solution.time_estimate}
**Source:** {solution.url}

## Description
{solution.description}

## Technologies
{', '.join(solution.technologies)}

## Pros
{chr(10).join(f"- {pro}" for pro in solution.pros)}

## Cons
{chr(10).join(f"- {con}" for con in solution.cons)}

## Implementation Example
```
{solution.code_example if solution.code_example else 'No code example available'}
```

## Metadata
- Research Date: {datetime.now().isoformat()}
- Auto-generated by Research Swarm
"""
        return body
    
    def _create_wiki_page(self, repo, solution: Solution):
        """Create wiki page for high-value solutions"""
        # GitHub API doesn't support wiki creation directly
        # Would need to clone wiki repo and push
        pass

class ResearchSwarm:
    """Orchestrator for research agents"""
    
    def __init__(self):
        self.browser = BrowserAgent()
        self.scraper = ScraperAgent()
        self.analyzer = AnalyzerAgent()
        self.tracker = GitHubTracker()
        self.redis_client = None
    
    async def initialize(self):
        """Initialize swarm components"""
        await self.browser.initialize()
        
        # Initialize Redis for caching
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = await aioredis.from_url(redis_url, decode_responses=True)
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.browser.cleanup()
        if self.redis_client:
            await self.redis_client.close()
    
    async def research(self, query: ResearchQuery) -> Dict[str, Any]:
        """Execute research pipeline"""
        start_time = datetime.now()
        
        # Check cache
        cache_key = f"research:{hashlib.md5(query.query.encode()).hexdigest()}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        # Phase 1: Search
        search_queries = self._generate_search_queries(query)
        search_results = await self.browser.search(search_queries, query.max_results)
        
        # Phase 2: Extract
        extracted_content = await self.scraper.extract_content(search_results)
        
        # Phase 3: Analyze
        solutions = await self.analyzer.evaluate_solutions(extracted_content, query.context)
        
        # Phase 4: Track (if requested)
        tracked_urls = []
        if query.track_in_github and solutions:
            for solution in solutions[:3]:  # Track top 3
                url = await self.tracker.save_solution(solution)
                if url:
                    tracked_urls.append(url)
        
        # Prepare result
        result = {
            'query': query.query,
            'timestamp': datetime.now().isoformat(),
            'duration': (datetime.now() - start_time).total_seconds(),
            'solutions_found': len(solutions),
            'top_solution': solutions[0].dict() if solutions else None,
            'all_solutions': [s.dict() for s in solutions],
            'github_tracking': tracked_urls,
            'search_sources': list(set(r.source for r in search_results)),
            'technologies_discovered': list(set(t for s in solutions for t in s.technologies))
        }
        
        # Cache result
        await self._cache_result(cache_key, result)
        
        return result
    
    def _generate_search_queries(self, query: ResearchQuery) -> List[str]:
        """Generate multiple search queries for better coverage"""
        base = query.query
        queries = [
            base,
            f"{base} best practices 2024",
            f"{base} implementation guide",
            f"{base} production ready",
            f"{base} site:github.com",
            f"{base} site:stackoverflow.com"
        ]
        
        # Add technology-specific queries
        if 'technologies' in query.context:
            for tech in query.context['technologies'][:2]:
                queries.append(f"{base} {tech}")
        
        return queries
    
    async def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached research result"""
        if not self.redis_client:
            return None
        
        try:
            cached = await self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        
        return None
    
    async def _cache_result(self, key: str, result: Dict[str, Any], ttl: int = 3600):
        """Cache research result"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.setex(key, ttl, json.dumps(result))
        except Exception:
            pass

# Singleton instance
_swarm = None

async def get_research_swarm() -> ResearchSwarm:
    """Get or create research swarm instance"""
    global _swarm
    if _swarm is None:
        _swarm = ResearchSwarm()
        await _swarm.initialize()
    return _swarm