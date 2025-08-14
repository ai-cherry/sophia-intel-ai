#!/usr/bin/env python3
"""
Documentation Search MCP Server

Provides tools for indexing and searching documentation from various sources
including local files, GitHub repos, websites, PyPI, and npm packages.
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set

try:
    import requests
    from bs4 import BeautifulSoup
    from whoosh.index import create_in, exists_in, open_dir
    from whoosh.fields import Schema, TEXT, ID, STORED
    from whoosh.qparser import QueryParser
    from whoosh.query import Term
except ImportError:
    print("Error: Required packages not found. Please run:")
    print("pip install requests beautifulsoup4 whoosh")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Repository root - adjust as needed
REPO_ROOT = Path(os.getcwd()).resolve()
INDEX_DIR = REPO_ROOT / ".docs_mcp_index"
CACHE_DIR = REPO_ROOT / ".docs_mcp_cache"


def ensure_dirs():
    """Ensure index and cache directories exist."""
    INDEX_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)


class DocSearchIndex:
    """Documentation search index using Whoosh."""

    def __init__(self):
        ensure_dirs()
        self.schema = Schema(
            id=ID(stored=True, unique=True),
            source=ID(stored=True),
            title=TEXT(stored=True),
            content=TEXT(stored=True),
            url=STORED,
            path=STORED,
            last_updated=STORED
        )

        if not exists_in(str(INDEX_DIR)):
            self.index = create_in(str(INDEX_DIR), self.schema)
        else:
            self.index = open_dir(str(INDEX_DIR))

        self.last_index_time = None
        self._load_last_index_time()

    def _load_last_index_time(self):
        """Load the last indexing time from file."""
        index_time_file = INDEX_DIR / "last_index_time.txt"
        if index_time_file.exists():
            try:
                with open(index_time_file, "r") as f:
                    timestamp = float(f.read().strip())
                    self.last_index_time = datetime.fromtimestamp(timestamp)
                    logger.info(f"Last index time: {self.last_index_time}")
            except (ValueError, IOError) as e:
                logger.error(f"Error loading last index time: {e}")
                self.last_index_time = None
        else:
            self.last_index_time = None

    def _save_last_index_time(self):
        """Save the current time as the last indexing time."""
        index_time_file = INDEX_DIR / "last_index_time.txt"
        try:
            with open(index_time_file, "w") as f:
                timestamp = datetime.now().timestamp()
                f.write(str(timestamp))
            self.last_index_time = datetime.now()
        except IOError as e:
            logger.error(f"Error saving last index time: {e}")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search the index for documents matching the query.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            List of matching documents
        """
        with self.index.searcher() as searcher:
            query_parser = QueryParser("content", self.index.schema)
            q = query_parser.parse(query)
            results = searcher.search(q, limit=limit)

            return [
                {
                    "id": result["id"],
                    "source": result["source"],
                    "title": result["title"],
                    "snippet": self._get_snippet(result["content"], query),
                    "url": result.get("url", ""),
                    "path": result.get("path", "")
                }
                for result in results
            ]

    def _get_snippet(self, content: str, query: str, context_chars: int = 100) -> str:
        """Extract a relevant snippet around the query terms."""
        # Simple approach: find first occurrence of any word in the query
        query_words = re.sub(r'[^\w\s]', '', query.lower()).split()
        content_lower = content.lower()

        for word in query_words:
            if len(word) < 3:
                continue  # Skip short words

            pos = content_lower.find(word)
            if pos >= 0:
                # Found a query word, extract snippet around it
                start = max(0, pos - context_chars)
                end = min(len(content), pos + len(word) + context_chars)

                # Adjust to not cut words
                if start > 0:
                    while start > 0 and content[start] != ' ':
                        start -= 1

                if end < len(content):
                    while end < len(content) and content[end] != ' ':
                        end += 1

                snippet = content[start:end]
                # Add ellipsis if needed
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."

                return snippet

        # Fallback: return the beginning of the content
        if len(content) <= context_chars * 2:
            return content
        return content[:context_chars * 2] + "..."

    def index_local_files(self, file_patterns: List[str]) -> int:
        """
        Index local markdown and RST files.

        Args:
            file_patterns: List of glob patterns for files to index

        Returns:
            Number of files indexed
        """
        writer = self.index.writer()
        count = 0

        for pattern in file_patterns:
            for path in REPO_ROOT.glob(pattern):
                try:
                    if not path.is_file():
                        continue

                    # Skip files in .git directory
                    if ".git" in path.parts:
                        continue

                    rel_path = path.relative_to(REPO_ROOT)
                    file_id = f"local:{rel_path}"

                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Use filename as title if no title found in content
                    title = path.stem.replace(
                        "_", " ").replace("-", " ").title()

                    # Try to extract a better title from first heading in markdown
                    if path.suffix.lower() in [".md", ".markdown"]:
                        title_match = re.search(
                            r'^#\s+(.*?)$', content, re.MULTILINE)
                        if title_match:
                            title = title_match.group(1).strip()
                    elif path.suffix.lower() in [".rst"]:
                        # Look for RST title patterns
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if i > 0 and re.match(r'^[=\-`~]+$', line) and i > 0:
                                title = lines[i-1].strip()
                                break

                    writer.add_document(
                        id=file_id,
                        source="local",
                        title=title,
                        content=content,
                        path=str(rel_path),
                        last_updated=datetime.now().isoformat()
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Error indexing {path}: {e}")

        writer.commit()
        return count

    def index_github_repo(self, repo: str, include_patterns: List[str]) -> int:
        """
        Index files from a GitHub repository.

        Args:
            repo: GitHub repo in format "owner/repo"
            include_patterns: List of glob patterns for files to include

        Returns:
            Number of files indexed
        """
        try:
            api_url = f"https://api.github.com/repos/{repo}/contents"
            response = requests.get(api_url)
            response.raise_for_status()

            writer = self.index.writer()
            count = 0

            def should_include(path):
                for pattern in include_patterns:
                    if re.match(pattern.replace("*", ".*"), path):
                        return True
                return False

            def process_item(item):
                nonlocal count
                if item["type"] == "file" and should_include(item["path"]):
                    try:
                        # Get file content
                        download_url = item["download_url"]
                        file_response = requests.get(download_url)
                        file_response.raise_for_status()
                        content = file_response.text

                        # Extract title
                        filename = os.path.basename(item["path"])
                        title = filename.split(".")[0].replace(
                            "_", " ").replace("-", " ").title()

                        # Try to extract a better title from content
                        if filename.lower().endswith((".md", ".markdown")):
                            title_match = re.search(
                                r'^#\s+(.*?)$', content, re.MULTILINE)
                            if title_match:
                                title = title_match.group(1).strip()

                        file_id = f"github:{repo}/{item['path']}"
                        writer.add_document(
                            id=file_id,
                            source=f"github:{repo}",
                            title=title,
                            content=content,
                            url=item["html_url"],
                            path=item["path"],
                            last_updated=datetime.now().isoformat()
                        )
                        count += 1
                    except Exception as e:
                        logger.error(f"Error indexing {item['path']}: {e}")

                elif item["type"] == "dir":
                    # Recursively process directory
                    dir_url = item["url"]
                    dir_response = requests.get(dir_url)
                    if dir_response.status_code == 200:
                        for child_item in dir_response.json():
                            process_item(child_item)

            for item in response.json():
                process_item(item)

            writer.commit()
            return count
        except Exception as e:
            logger.error(f"Error indexing GitHub repo {repo}: {e}")
            return 0

    def index_website(self, url: str, scope: str = "path", allow_robots: bool = True) -> int:
        """
        Index content from a website.

        Args:
            url: Base URL of the website
            scope: Scope of crawling ("path", "domain", or "subdomain")
            allow_robots: Whether to respect robots.txt

        Returns:
            Number of pages indexed
        """
        from urllib.parse import urlparse, urljoin

        try:
            # Simple function to check if URL is within scope
            def is_in_scope(page_url):
                parsed_base = urlparse(url)
                parsed_page = urlparse(page_url)

                if scope == "path":
                    return parsed_page.netloc == parsed_base.netloc and parsed_page.path.startswith(parsed_base.path)
                elif scope == "domain":
                    return parsed_page.netloc == parsed_base.netloc
                elif scope == "subdomain":
                    return parsed_page.netloc.endswith(f".{parsed_base.netloc}") or parsed_page.netloc == parsed_base.netloc
                return False

            # Set to track visited URLs
            visited = set()
            to_visit = [url]
            count = 0
            writer = self.index.writer()

            # Limit the number of pages to index
            max_pages = 100

            while to_visit and count < max_pages:
                current_url = to_visit.pop(0)

                if current_url in visited:
                    continue

                visited.add(current_url)

                try:
                    response = requests.get(current_url, timeout=5)
                    if response.status_code != 200:
                        continue

                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" not in content_type:
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")

                    # Extract title
                    title = soup.title.string.strip() if soup.title else current_url

                    # Extract text content
                    text_content = ""
                    for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"]):
                        if tag.string:
                            text_content += tag.string.strip() + "\n\n"

                    if not text_content:
                        # Fallback to all text
                        text_content = soup.get_text(" ", strip=True)

                    # Index the page
                    page_id = f"website:{current_url}"
                    writer.add_document(
                        id=page_id,
                        source=f"website:{urlparse(url).netloc}",
                        title=title,
                        content=text_content,
                        url=current_url,
                        last_updated=datetime.now().isoformat()
                    )
                    count += 1

                    # Find links to other pages
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        absolute_url = urljoin(current_url, href)

                        # Check if URL is within scope and not already visited
                        if is_in_scope(absolute_url) and absolute_url not in visited and absolute_url not in to_visit:
                            to_visit.append(absolute_url)

                except Exception as e:
                    logger.error(f"Error indexing {current_url}: {e}")

            writer.commit()
            return count

        except Exception as e:
            logger.error(f"Error indexing website {url}: {e}")
            return 0

    def index_pypi_package(self, package_name: str) -> int:
        """
        Index documentation from a PyPI package.

        Args:
            package_name: Name of the PyPI package

        Returns:
            Number of pages indexed
        """
        try:
            # Get package info from PyPI
            api_url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(api_url)
            response.raise_for_status()

            package_data = response.json()

            # Find documentation URL
            project_urls = package_data["info"].get("project_urls", {})
            docs_url = None

            for url_type, url in project_urls.items():
                if "doc" in url_type.lower() or "docs" in url_type.lower():
                    docs_url = url
                    break

            if not docs_url and "documentation_url" in package_data["info"]:
                docs_url = package_data["info"]["documentation_url"]

            if not docs_url and "home_page" in package_data["info"]:
                docs_url = package_data["info"]["home_page"]

            # If no docs URL found, use the PyPI page
            if not docs_url:
                docs_url = f"https://pypi.org/project/{package_name}/"

            # Index the docs site
            count = self.index_website(docs_url, scope="domain")

            # Also index the package description
            writer = self.index.writer()

            description = package_data["info"].get("description", "")
            summary = package_data["info"].get("summary", "")

            writer.add_document(
                id=f"pypi:{package_name}",
                source=f"pypi:{package_name}",
                title=f"{package_name} - {summary}",
                content=description,
                url=f"https://pypi.org/project/{package_name}/",
                last_updated=datetime.now().isoformat()
            )

            writer.commit()
            return count + 1

        except Exception as e:
            logger.error(f"Error indexing PyPI package {package_name}: {e}")
            return 0

    def index_npm_package(self, package_name: str) -> int:
        """
        Index documentation from an npm package.

        Args:
            package_name: Name of the npm package

        Returns:
            Number of pages indexed
        """
        try:
            # Get package info from npm registry
            api_url = f"https://registry.npmjs.org/{package_name}"
            response = requests.get(api_url)
            response.raise_for_status()

            package_data = response.json()

            # Find documentation URL
            latest_version = package_data["dist-tags"]["latest"]
            version_data = package_data["versions"][latest_version]

            docs_url = None

            # Check for docs in homepage, repository, or bugs
            if "homepage" in version_data:
                docs_url = version_data["homepage"]
            elif "repository" in version_data and isinstance(version_data["repository"], dict):
                repo_url = version_data["repository"].get("url", "")
                if repo_url.startswith("git+"):
                    repo_url = repo_url[4:]
                if repo_url.endswith(".git"):
                    repo_url = repo_url[:-4]
                if "github.com" in repo_url:
                    docs_url = repo_url.replace(
                        "git://", "https://").replace("git@github.com:", "https://github.com/")

            # If no docs URL found, use the npm page
            if not docs_url:
                docs_url = f"https://www.npmjs.com/package/{package_name}"

            # Index the docs site
            count = self.index_website(docs_url, scope="domain")

            # Also index the package description
            writer = self.index.writer()

            description = version_data.get("description", "")
            readme = version_data.get("readme", "")

            content = f"{description}\n\n{readme}" if readme else description

            writer.add_document(
                id=f"npm:{package_name}",
                source=f"npm:{package_name}",
                title=f"{package_name} - {description}",
                content=content,
                url=f"https://www.npmjs.com/package/{package_name}",
                last_updated=datetime.now().isoformat()
            )

            writer.commit()
            return count + 1

        except Exception as e:
            logger.error(f"Error indexing npm package {package_name}: {e}")
            return 0

    def index_all_sources(self, config: Dict[str, Any]) -> Dict[str, int]:
        """
        Index all sources defined in the config.

        Args:
            config: Configuration dictionary with sources to index

        Returns:
            Dictionary with source types and number of documents indexed
        """
        results = {}
        sources = config.get("sources", [])

        for source in sources:
            source_type = source.get("type", "")

            if source_type == "github":
                repo = source.get("repo", "")
                include = source.get("include", ["**/*.md", "**/*.rst"])
                if repo:
                    count = self.index_github_repo(repo, include)
                    results[f"github:{repo}"] = count

            elif source_type == "local":
                include = source.get("include", ["**/*.md", "**/*.rst"])
                count = self.index_local_files(include)
                results["local"] = count

            elif source_type == "website":
                url = source.get("url", "")
                scope = source.get("scope", "path")
                allow_robots = source.get("allowRobots", True)
                if url:
                    count = self.index_website(url, scope, allow_robots)
                    results[f"website:{url}"] = count

            elif source_type == "pypi":
                package = source.get("package", "")
                if package:
                    count = self.index_pypi_package(package)
                    results[f"pypi:{package}"] = count

            elif source_type == "npm":
                package = source.get("package", "")
                if package:
                    count = self.index_npm_package(package)
                    results[f"npm:{package}"] = count

        self._save_last_index_time()
        return results

    def should_update_index(self, config: Dict[str, Any]) -> bool:
        """
        Check if the index should be updated based on update interval.

        Args:
            config: Configuration dictionary with updateIntervalHours

        Returns:
            True if the index should be updated, False otherwise
        """
        if not self.last_index_time:
            return True

        update_interval = config.get("updateIntervalHours", 24)
        next_update_time = self.last_index_time + \
            timedelta(hours=update_interval)

        return datetime.now() >= next_update_time


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        config_path: Path to the config file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        return {"sources": []}


def handle_request(request: Dict[str, Any], index: DocSearchIndex, config: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming MCP requests"""
    tool = request.get("tool", "")
    params = request.get("params", {})

    if tool == "search_docs":
        query = params.get("query", "")
        limit = params.get("limit", 5)
        return {"results": index.search(query, limit)}

    elif tool == "index_docs":
        # Check if we need to update the index
        if index.should_update_index(config):
            results = index.index_all_sources(config)
            return {"indexed": results}
        else:
            return {"message": "Index is up to date"}

    else:
        return {
            "error": f"Unknown tool: {tool}",
            "available_tools": ["search_docs", "index_docs"]
        }


def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(
        description="Documentation Search MCP Server")
    parser.add_argument(
        "--config", default="mcp/docs-mcp.config.json", help="Path to config file")
    args = parser.parse_args()

    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.getcwd(), config_path)

    logger.info(f"Starting docs_search MCP server with config: {config_path}")

    # Load config
    config = load_config(config_path)

    # Create index
    index = DocSearchIndex()

    # Initial indexing if needed
    if index.should_update_index(config):
        logger.info("Performing initial indexing...")
        index.index_all_sources(config)

    # Protocol: read JSON requests from stdin, write responses to stdout
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = handle_request(request, index, config)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON request"}), flush=True)
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            print(json.dumps({"error": str(e)}), flush=True)


if __name__ == "__main__":
    main()
