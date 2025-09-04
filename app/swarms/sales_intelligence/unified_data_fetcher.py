"""
Unified Data Fetcher for Sales Intelligence Swarm

This module provides a unified interface to fetch data from all connected platforms:
- Gong: Call recordings, transcripts, user metrics
- Asana: Project data, tasks, team information
- Linear: Issues, teams, project status
- Notion: Database records, user data
- HubSpot: Contacts, deals, pipeline data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import aiohttp
import base64

from app.api.integrations_config import INTEGRATIONS, get_platform_client, get_integration_status

logger = logging.getLogger(__name__)


@dataclass
class PlatformData:
    """Standardized data structure from any platform"""
    platform: str
    data_type: str  # calls, tasks, issues, contacts, etc.
    count: int
    items: List[Dict[str, Any]]
    last_updated: datetime
    metadata: Dict[str, Any]


@dataclass
class UnifiedDataSummary:
    """Summary of all platform data"""
    gong: Optional[PlatformData] = None
    asana: Optional[PlatformData] = None
    linear: Optional[PlatformData] = None
    notion: Optional[PlatformData] = None
    hubspot: Optional[PlatformData] = None
    total_records: int = 0
    connected_platforms: int = 0
    last_sync: datetime = None


class GongDataFetcher:
    """Fetch data from Gong API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config["api_url"]
        self.access_key = config["access_key"]
        self.client_secret = config["client_secret"]
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Gong API"""
        auth_string = base64.b64encode(f"{self.access_key}:{self.client_secret}".encode()).decode()
        return {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json"
        }
    
    async def fetch_calls_data(self, days_back: int = 7) -> PlatformData:
        """Fetch recent calls data from Gong"""
        try:
            headers = await self.get_auth_headers()
            from_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            async with aiohttp.ClientSession() as session:
                # Get calls list
                calls_url = f"{self.base_url}/v2/calls"
                params = {
                    "fromDateTime": from_date,
                    "limit": 100
                }
                
                async with session.get(calls_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        calls = data.get("calls", [])
                        
                        return PlatformData(
                            platform="gong",
                            data_type="calls",
                            count=len(calls),
                            items=calls,
                            last_updated=datetime.now(),
                            metadata={
                                "api_url": self.base_url,
                                "days_back": days_back,
                                "company": self.config.get("stats", {}).get("company", "Unknown")
                            }
                        )
                    else:
                        logger.error(f"Gong API error: {response.status}")
                        return self._empty_platform_data("gong", "calls")
        except Exception as e:
            logger.error(f"Error fetching Gong data: {e}")
            return self._empty_platform_data("gong", "calls")
    
    def _empty_platform_data(self, platform: str, data_type: str) -> PlatformData:
        """Return empty platform data structure"""
        return PlatformData(
            platform=platform,
            data_type=data_type,
            count=0,
            items=[],
            last_updated=datetime.now(),
            metadata={"error": "Failed to fetch data"}
        )


class AsanaDataFetcher:
    """Fetch data from Asana API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.token = config["pat_token"]
        self.base_url = "https://app.asana.com/api/1.0"
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Asana API"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def fetch_workspace_data(self) -> PlatformData:
        """Fetch workspace and project data from Asana"""
        try:
            headers = await self.get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                # Get workspaces
                workspaces_url = f"{self.base_url}/workspaces"
                
                async with session.get(workspaces_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        workspaces = data.get("data", [])
                        
                        # Get projects for each workspace
                        all_projects = []
                        for workspace in workspaces:
                            projects_url = f"{self.base_url}/projects"
                            params = {"workspace": workspace["gid"]}
                            
                            async with session.get(projects_url, headers=headers, params=params) as proj_response:
                                if proj_response.status == 200:
                                    proj_data = await proj_response.json()
                                    projects = proj_data.get("data", [])
                                    all_projects.extend(projects)
                        
                        return PlatformData(
                            platform="asana",
                            data_type="projects",
                            count=len(all_projects),
                            items=all_projects,
                            last_updated=datetime.now(),
                            metadata={
                                "workspaces": len(workspaces),
                                "workspace_names": [w.get("name", "") for w in workspaces]
                            }
                        )
                    else:
                        logger.error(f"Asana API error: {response.status}")
                        return self._empty_platform_data("asana", "projects")
        except Exception as e:
            logger.error(f"Error fetching Asana data: {e}")
            return self._empty_platform_data("asana", "projects")
    
    def _empty_platform_data(self, platform: str, data_type: str) -> PlatformData:
        return PlatformData(
            platform=platform,
            data_type=data_type,
            count=0,
            items=[],
            last_updated=datetime.now(),
            metadata={"error": "Failed to fetch data"}
        )


class LinearDataFetcher:
    """Fetch data from Linear API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config["api_key"]
        self.base_url = "https://api.linear.app/graphql"
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Linear API"""
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def fetch_teams_data(self) -> PlatformData:
        """Fetch teams and issues data from Linear"""
        try:
            headers = await self.get_auth_headers()
            
            # GraphQL query to get teams and issues
            query = """
            {
              teams {
                nodes {
                  id
                  name
                  description
                  issuesCount
                }
              }
              issues(first: 50) {
                nodes {
                  id
                  title
                  state {
                    name
                  }
                  team {
                    name
                  }
                  createdAt
                }
              }
            }
            """
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url, 
                    headers=headers, 
                    json={"query": query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "errors" in data:
                            logger.error(f"Linear GraphQL errors: {data['errors']}")
                            return self._empty_platform_data("linear", "teams")
                        
                        teams = data.get("data", {}).get("teams", {}).get("nodes", [])
                        issues = data.get("data", {}).get("issues", {}).get("nodes", [])
                        
                        return PlatformData(
                            platform="linear",
                            data_type="teams",
                            count=len(teams),
                            items=teams,
                            last_updated=datetime.now(),
                            metadata={
                                "total_issues": len(issues),
                                "team_names": [t.get("name", "") for t in teams]
                            }
                        )
                    else:
                        logger.error(f"Linear API error: {response.status}")
                        return self._empty_platform_data("linear", "teams")
        except Exception as e:
            logger.error(f"Error fetching Linear data: {e}")
            return self._empty_platform_data("linear", "teams")
    
    def _empty_platform_data(self, platform: str, data_type: str) -> PlatformData:
        return PlatformData(
            platform=platform,
            data_type=data_type,
            count=0,
            items=[],
            last_updated=datetime.now(),
            metadata={"error": "Failed to fetch data"}
        )


class NotionDataFetcher:
    """Fetch data from Notion API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.token = config["api_key"]
        self.base_url = "https://api.notion.com/v1"
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Notion API"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    async def fetch_databases_data(self) -> PlatformData:
        """Fetch databases data from Notion"""
        try:
            headers = await self.get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                # Search for databases
                search_url = f"{self.base_url}/search"
                search_body = {
                    "filter": {
                        "property": "object",
                        "value": "database"
                    }
                }
                
                async with session.post(search_url, headers=headers, json=search_body) as response:
                    if response.status == 200:
                        data = await response.json()
                        databases = data.get("results", [])
                        
                        return PlatformData(
                            platform="notion",
                            data_type="databases",
                            count=len(databases),
                            items=databases,
                            last_updated=datetime.now(),
                            metadata={
                                "database_names": [db.get("title", [{}])[0].get("plain_text", "Untitled") for db in databases]
                            }
                        )
                    else:
                        logger.error(f"Notion API error: {response.status}")
                        return self._empty_platform_data("notion", "databases")
        except Exception as e:
            logger.error(f"Error fetching Notion data: {e}")
            return self._empty_platform_data("notion", "databases")
    
    def _empty_platform_data(self, platform: str, data_type: str) -> PlatformData:
        return PlatformData(
            platform=platform,
            data_type=data_type,
            count=0,
            items=[],
            last_updated=datetime.now(),
            metadata={"error": "Failed to fetch data"}
        )


class HubSpotDataFetcher:
    """Fetch data from HubSpot API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.token = config["api_token"]
        self.portal_id = config["portal_id"]
        self.base_url = "https://api.hubapi.com"
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for HubSpot API"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def fetch_contacts_data(self) -> PlatformData:
        """Fetch contacts and deals data from HubSpot"""
        try:
            headers = await self.get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                # Get contacts
                contacts_url = f"{self.base_url}/crm/v3/objects/contacts"
                params = {"limit": 100}
                
                async with session.get(contacts_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        contacts = data.get("results", [])
                        
                        # Get deals
                        deals_url = f"{self.base_url}/crm/v3/objects/deals"
                        deals = []
                        
                        async with session.get(deals_url, headers=headers, params=params) as deals_response:
                            if deals_response.status == 200:
                                deals_data = await deals_response.json()
                                deals = deals_data.get("results", [])
                        
                        return PlatformData(
                            platform="hubspot",
                            data_type="contacts",
                            count=len(contacts),
                            items=contacts,
                            last_updated=datetime.now(),
                            metadata={
                                "portal_id": self.portal_id,
                                "deals_count": len(deals),
                                "total_records": len(contacts) + len(deals)
                            }
                        )
                    else:
                        logger.error(f"HubSpot API error: {response.status}")
                        return self._empty_platform_data("hubspot", "contacts")
        except Exception as e:
            logger.error(f"Error fetching HubSpot data: {e}")
            return self._empty_platform_data("hubspot", "contacts")
    
    def _empty_platform_data(self, platform: str, data_type: str) -> PlatformData:
        return PlatformData(
            platform=platform,
            data_type=data_type,
            count=0,
            items=[],
            last_updated=datetime.now(),
            metadata={"error": "Failed to fetch data"}
        )


class UnifiedDataFetcher:
    """Main unified data fetcher for all platforms"""
    
    def __init__(self):
        self.fetchers = {}
        self._initialize_fetchers()
    
    def _initialize_fetchers(self):
        """Initialize fetchers for all enabled platforms"""
        for platform_name, config in INTEGRATIONS.items():
            if config["enabled"]:
                try:
                    if platform_name == "gong":
                        self.fetchers[platform_name] = GongDataFetcher(config)
                    elif platform_name == "asana":
                        self.fetchers[platform_name] = AsanaDataFetcher(config)
                    elif platform_name == "linear":
                        self.fetchers[platform_name] = LinearDataFetcher(config)
                    elif platform_name == "notion":
                        self.fetchers[platform_name] = NotionDataFetcher(config)
                    elif platform_name == "hubspot":
                        self.fetchers[platform_name] = HubSpotDataFetcher(config)
                    
                    logger.info(f"Initialized {platform_name} fetcher")
                except Exception as e:
                    logger.error(f"Failed to initialize {platform_name} fetcher: {e}")
    
    async def fetch_all_data(self) -> UnifiedDataSummary:
        """Fetch data from all connected platforms"""
        summary = UnifiedDataSummary()
        summary.last_sync = datetime.now()
        
        # Fetch data from all platforms concurrently
        fetch_tasks = []
        
        if "gong" in self.fetchers:
            fetch_tasks.append(self._safe_fetch("gong", self.fetchers["gong"].fetch_calls_data()))
        
        if "asana" in self.fetchers:
            fetch_tasks.append(self._safe_fetch("asana", self.fetchers["asana"].fetch_workspace_data()))
        
        if "linear" in self.fetchers:
            fetch_tasks.append(self._safe_fetch("linear", self.fetchers["linear"].fetch_teams_data()))
        
        if "notion" in self.fetchers:
            fetch_tasks.append(self._safe_fetch("notion", self.fetchers["notion"].fetch_databases_data()))
        
        if "hubspot" in self.fetchers:
            fetch_tasks.append(self._safe_fetch("hubspot", self.fetchers["hubspot"].fetch_contacts_data()))
        
        # Execute all fetches concurrently
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        # Process results
        total_records = 0
        connected_platforms = 0
        
        for platform_name, platform_data in results:
            if platform_data and isinstance(platform_data, PlatformData):
                setattr(summary, platform_name, platform_data)
                total_records += platform_data.count
                connected_platforms += 1
                logger.info(f"Fetched {platform_data.count} records from {platform_name}")
        
        summary.total_records = total_records
        summary.connected_platforms = connected_platforms
        
        return summary
    
    async def _safe_fetch(self, platform_name: str, fetch_coro) -> tuple:
        """Safely fetch data with error handling"""
        try:
            result = await fetch_coro
            return (platform_name, result)
        except Exception as e:
            logger.error(f"Error fetching from {platform_name}: {e}")
            return (platform_name, None)
    
    async def fetch_platform_data(self, platform_name: str) -> Optional[PlatformData]:
        """Fetch data from a specific platform"""
        if platform_name not in self.fetchers:
            logger.warning(f"Fetcher for {platform_name} not available")
            return None
        
        try:
            if platform_name == "gong":
                return await self.fetchers[platform_name].fetch_calls_data()
            elif platform_name == "asana":
                return await self.fetchers[platform_name].fetch_workspace_data()
            elif platform_name == "linear":
                return await self.fetchers[platform_name].fetch_teams_data()
            elif platform_name == "notion":
                return await self.fetchers[platform_name].fetch_databases_data()
            elif platform_name == "hubspot":
                return await self.fetchers[platform_name].fetch_contacts_data()
        except Exception as e:
            logger.error(f"Error fetching data from {platform_name}: {e}")
            return None
    
    def get_connected_platforms(self) -> List[str]:
        """Get list of connected platform names"""
        return list(self.fetchers.keys())
    
    def get_platform_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all platforms from integrations config"""
        stats = {}
        for platform_name, config in INTEGRATIONS.items():
            if config["enabled"]:
                stats[platform_name] = config.get("stats", {})
        return stats


# Convenience functions
async def get_unified_data() -> UnifiedDataSummary:
    """Get unified data from all platforms"""
    fetcher = UnifiedDataFetcher()
    return await fetcher.fetch_all_data()


async def get_platform_data(platform_name: str) -> Optional[PlatformData]:
    """Get data from a specific platform"""
    fetcher = UnifiedDataFetcher()
    return await fetcher.fetch_platform_data(platform_name)


# Example usage
async def example_usage():
    """Example of how to use the unified data fetcher"""
    fetcher = UnifiedDataFetcher()
    
    print("Connected platforms:", fetcher.get_connected_platforms())
    print("Platform stats:", fetcher.get_platform_stats())
    
    # Fetch all data
    summary = await fetcher.fetch_all_data()
    print(f"\nUnified Data Summary:")
    print(f"Total records: {summary.total_records}")
    print(f"Connected platforms: {summary.connected_platforms}")
    print(f"Last sync: {summary.last_sync}")
    
    # Check individual platform data
    for platform in ["gong", "asana", "linear", "notion", "hubspot"]:
        platform_data = getattr(summary, platform)
        if platform_data:
            print(f"\n{platform.title()}:")
            print(f"  Count: {platform_data.count}")
            print(f"  Data type: {platform_data.data_type}")
            print(f"  Metadata: {platform_data.metadata}")


if __name__ == "__main__":
    asyncio.run(example_usage())