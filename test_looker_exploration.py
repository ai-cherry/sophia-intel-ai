#!/usr/bin/env python3
"""
Looker Data Exploration Test Script

This script tests the Looker integration and explores what type of information
can be pulled from your Looker instance. It provides a comprehensive overview
of available data, dashboards, and exploration capabilities.
"""

import asyncio
import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List
import os

# Add the project root to the path
sys.path.insert(0, '/Users/lynnmusil/sophia-intel-ai')

from app.integrations.looker_client import get_looker_client, LookerClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LookerExplorer:
    """Comprehensive Looker data exploration"""
    
    def __init__(self):
        self.client = None
        self.exploration_results = {}
    
    async def initialize(self):
        """Initialize Looker client"""
        try:
            self.client = get_looker_client()
            logger.info("✅ Looker client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Looker client: {str(e)}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test basic Looker connection"""
        print("\n" + "="*60)
        print("🔍 TESTING LOOKER CONNECTION")
        print("="*60)
        
        try:
            result = self.client.test_connection()
            
            if result.get("status") == "connected":
                print("✅ Connection successful!")
                print(f"   User: {result.get('display_name', 'Unknown')} ({result.get('email', 'N/A')})")
                print(f"   User ID: {result.get('user_id', 'N/A')}")
                print(f"   Looker Version: {result.get('looker_version', 'Unknown')}")
                print(f"   Account Disabled: {result.get('is_disabled', 'Unknown')}")
            else:
                print("❌ Connection failed!")
                print(f"   Error: {result.get('error', 'Unknown error')}")
            
            self.exploration_results["connection_test"] = result
            return result
            
        except Exception as e:
            error_msg = f"Connection test failed: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.exploration_results["connection_test"] = {"status": "error", "error": str(e)}
            return {"status": "error", "error": str(e)}
    
    async def explore_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        print("\n" + "="*60)
        print("📊 EXPLORING SYSTEM INFORMATION")
        print("="*60)
        
        try:
            system_info = self.client.get_system_info()
            
            print("✅ System Information Retrieved:")
            print(f"   Looker Version: {system_info.get('looker_version', 'Unknown')}")
            print(f"   API Version: {system_info.get('api_version', 'Unknown')}")
            print(f"   Instance URL: {system_info.get('instance_url', 'Unknown')}")
            
            # Current user info
            user_info = system_info.get('current_user', {})
            print(f"   Current User: {user_info.get('display_name', 'Unknown')} ({user_info.get('email', 'N/A')})")
            
            # Content statistics
            content_counts = system_info.get('content_counts', {})
            print(f"   Total Dashboards: {content_counts.get('dashboards', 0)}")
            print(f"   Total Looks: {content_counts.get('looks', 0)}")
            
            # Supported API versions
            supported_versions = system_info.get('supported_versions', [])
            print(f"   Supported API Versions: {', '.join(supported_versions) if supported_versions else 'Unknown'}")
            
            self.exploration_results["system_info"] = system_info
            return system_info
            
        except Exception as e:
            error_msg = f"System info exploration failed: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.exploration_results["system_info"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def explore_dashboards(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Explore available dashboards"""
        print(f"\n" + "="*60)
        print(f"📋 EXPLORING DASHBOARDS (Limit: {limit})")
        print("="*60)
        
        try:
            dashboards = self.client.get_dashboards(limit=limit)
            
            print(f"✅ Found {len(dashboards)} dashboards:")
            
            dashboard_list = []
            for i, dash in enumerate(dashboards[:10], 1):  # Show first 10 in detail
                print(f"\n   {i}. {dash.title} (ID: {dash.id})")
                print(f"      Description: {dash.description or 'No description'}")
                print(f"      Created: {dash.created_at or 'Unknown'}")
                print(f"      Updated: {dash.updated_at or 'Unknown'}")
                print(f"      Views: {dash.view_count or 0} | Favorites: {dash.favorite_count or 0}")
                
                dashboard_list.append({
                    "id": dash.id,
                    "title": dash.title,
                    "description": dash.description,
                    "created_at": dash.created_at,
                    "updated_at": dash.updated_at,
                    "view_count": dash.view_count,
                    "favorite_count": dash.favorite_count
                })
            
            if len(dashboards) > 10:
                print(f"\n   ... and {len(dashboards) - 10} more dashboards")
            
            self.exploration_results["dashboards"] = {
                "total_found": len(dashboards),
                "dashboards": dashboard_list
            }
            return dashboard_list
            
        except Exception as e:
            error_msg = f"Dashboard exploration failed: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.exploration_results["dashboards"] = {"error": str(e)}
            return []
    
    async def explore_looks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Explore available looks (saved visualizations)"""
        print(f"\n" + "="*60)
        print(f"👁️  EXPLORING LOOKS (Limit: {limit})")
        print("="*60)
        
        try:
            looks = self.client.get_looks(limit=limit)
            
            print(f"✅ Found {len(looks)} looks:")
            
            looks_list = []
            for i, look in enumerate(looks[:10], 1):  # Show first 10 in detail
                print(f"\n   {i}. {look.title} (ID: {look.id})")
                print(f"      Description: {look.description or 'No description'}")
                print(f"      Query ID: {look.query_id or 'N/A'}")
                print(f"      Created: {look.created_at or 'Unknown'}")
                print(f"      Views: {look.view_count or 0}")
                
                looks_list.append({
                    "id": look.id,
                    "title": look.title,
                    "description": look.description,
                    "query_id": look.query_id,
                    "created_at": look.created_at,
                    "view_count": look.view_count
                })
            
            if len(looks) > 10:
                print(f"\n   ... and {len(looks) - 10} more looks")
            
            self.exploration_results["looks"] = {
                "total_found": len(looks),
                "looks": looks_list
            }
            return looks_list
            
        except Exception as e:
            error_msg = f"Looks exploration failed: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.exploration_results["looks"] = {"error": str(e)}
            return []
    
    async def explore_models(self) -> List[Dict[str, Any]]:
        """Explore available data models"""
        print("\n" + "="*60)
        print("🗃️  EXPLORING DATA MODELS")
        print("="*60)
        
        try:
            models = self.client.get_models()
            
            print(f"✅ Found {len(models)} data models:")
            
            for i, model in enumerate(models, 1):
                print(f"\n   {i}. {model.get('name', 'Unnamed Model')}")
                print(f"      Title: {model.get('title', 'No title')}")
                print(f"      Description: {model.get('description', 'No description')}")
                print(f"      Explores: {model.get('explores_count', 0)}")
                
                # Show first few explores
                explores = model.get('explores', [])
                if explores:
                    print("      Available Explores:")
                    for explore in explores[:5]:
                        explore_name = explore.get('name', 'Unnamed')
                        explore_title = explore.get('title', explore_name)
                        print(f"        - {explore_name} ({explore_title})")
                    if len(explores) > 5:
                        print(f"        ... and {len(explores) - 5} more explores")
            
            self.exploration_results["models"] = {
                "total_found": len(models),
                "models": models
            }
            return models
            
        except Exception as e:
            error_msg = f"Models exploration failed: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.exploration_results["models"] = {"error": str(e)}
            return []
    
    async def sample_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Sample data from a specific dashboard"""
        print(f"\n" + "="*60)
        print(f"📈 SAMPLING DASHBOARD DATA (ID: {dashboard_id})")
        print("="*60)
        
        try:
            dashboard_data = self.client.get_dashboard_data(dashboard_id)
            
            dashboard_info = dashboard_data.get("dashboard", {})
            elements = dashboard_data.get("elements", [])
            
            print("✅ Dashboard Data Retrieved:")
            print(f"   Title: {dashboard_info.get('title', 'Unknown')}")
            print(f"   Description: {dashboard_info.get('description', 'No description')}")
            print(f"   Elements: {len(elements)}")
            
            # Show element details
            for i, element in enumerate(elements[:5], 1):
                print(f"\n   Element {i}: {element.get('title', 'Untitled')}")
                print(f"      Type: {element.get('type', 'Unknown')}")
                
                # Show sample data if available
                data = element.get('data', [])
                if data and isinstance(data, list):
                    print(f"      Sample Data ({len(data)} rows):")
                    if data:
                        # Show first row keys
                        if isinstance(data[0], dict):
                            keys = list(data[0].keys())[:5]
                            print(f"        Columns: {', '.join(keys)}")
                            if len(data[0].keys()) > 5:
                                print(f"        ... and {len(data[0].keys()) - 5} more columns")
                elif element.get('data_error'):
                    print(f"      Data Error: {element.get('data_error')}")
                else:
                    print("      No data available")
            
            if len(elements) > 5:
                print(f"\n   ... and {len(elements) - 5} more elements")
            
            self.exploration_results["sample_dashboard"] = dashboard_data
            return dashboard_data
            
        except Exception as e:
            error_msg = f"Dashboard data sampling failed: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.exploration_results["sample_dashboard"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def sample_look_data(self, look_id: str) -> Dict[str, Any]:
        """Sample data from a specific look"""
        print(f"\n" + "="*60)
        print(f"👁️  SAMPLING LOOK DATA (ID: {look_id})")
        print("="*60)
        
        try:
            look_data = self.client.get_look_data(look_id, limit=100)
            
            look_info = look_data.get("look", {})
            data = look_data.get("data", [])
            
            print("✅ Look Data Retrieved:")
            print(f"   Title: {look_info.get('title', 'Unknown')}")
            print(f"   Description: {look_info.get('description', 'No description')}")
            print(f"   Data Rows: {len(data)}")
            
            # Show sample data
            if data and isinstance(data, list):
                print("\n   Sample Data:")
                if data and isinstance(data[0], dict):
                    # Show column names
                    columns = list(data[0].keys())
                    print(f"   Columns ({len(columns)}): {', '.join(columns[:8])}")
                    if len(columns) > 8:
                        print(f"   ... and {len(columns) - 8} more columns")
                    
                    # Show first few rows
                    print("\n   First 3 rows:")
                    for i, row in enumerate(data[:3], 1):
                        print(f"      Row {i}: {dict(list(row.items())[:3])}")
                        if len(row) > 3:
                            print(f"        ... and {len(row) - 3} more fields")
            else:
                print("   No data available or unexpected format")
            
            self.exploration_results["sample_look"] = look_data
            return look_data
            
        except Exception as e:
            error_msg = f"Look data sampling failed: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.exploration_results["sample_look"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def search_content(self, query: str = "revenue") -> Dict[str, Any]:
        """Search for specific content"""
        print(f"\n" + "="*60)
        print(f"🔍 SEARCHING CONTENT (Query: '{query}')")
        print("="*60)
        
        try:
            search_results = self.client.search_content(query=query, limit=20)
            
            total_results = search_results.get("total_results", 0)
            results = search_results.get("results", {})
            
            print(f"✅ Found {total_results} total results:")
            
            for content_type, items in results.items():
                if items:
                    print(f"\n   {content_type.title()} ({len(items)}):")
                    for item in items[:5]:
                        print(f"      - {item.get('title', 'Untitled')} (ID: {item.get('id')})")
                        if item.get('description'):
                            print(f"        {item.get('description')[:100]}...")
                    if len(items) > 5:
                        print(f"      ... and {len(items) - 5} more")
            
            self.exploration_results["search_results"] = search_results
            return search_results
            
        except Exception as e:
            error_msg = f"Content search failed: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            self.exploration_results["search_results"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def save_results(self, filename: str = None):
        """Save exploration results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"looker_exploration_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.exploration_results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
            print(f"❌ Failed to save results: {str(e)}")
            return None

async def main():
    """Main exploration script"""
    print("🚀 LOOKER DATA EXPLORATION SCRIPT")
    print("="*60)
    print("This script will explore your Looker instance to understand")
    print("what data and insights are available through Sophia.")
    print("="*60)
    
    explorer = LookerExplorer()
    
    # Initialize client
    if not await explorer.initialize():
        print("\n❌ Cannot proceed without Looker client. Exiting.")
        return
    
    try:
        # Test connection
        connection_result = await explorer.test_connection()
        if connection_result.get("status") != "connected":
            print("\n❌ Connection failed. Cannot proceed with exploration.")
            return
        
        # Explore system info
        await explorer.explore_system_info()
        
        # Explore dashboards
        dashboards = await explorer.explore_dashboards(limit=20)
        
        # Explore looks
        looks = await explorer.explore_looks(limit=20)
        
        # Explore data models
        models = await explorer.explore_models()
        
        # Sample data from first dashboard if available
        if dashboards and len(dashboards) > 0:
            first_dashboard = dashboards[0]
            await explorer.sample_dashboard_data(first_dashboard["id"])
        
        # Sample data from first look if available
        if looks and len(looks) > 0:
            first_look = looks[0]
            await explorer.sample_look_data(first_look["id"])
        
        # Search for revenue-related content
        await explorer.search_content("revenue")
        
        # Save results
        results_file = await explorer.save_results()
        
        # Summary
        print("\n" + "="*60)
        print("📊 EXPLORATION SUMMARY")
        print("="*60)
        
        system_info = explorer.exploration_results.get("system_info", {})
        dashboards_info = explorer.exploration_results.get("dashboards", {})
        looks_info = explorer.exploration_results.get("looks", {})
        models_info = explorer.exploration_results.get("models", {})
        
        print(f"✅ Connection Status: {'SUCCESS' if connection_result.get('status') == 'connected' else 'FAILED'}")
        print(f"📋 Dashboards Found: {dashboards_info.get('total_found', 0)}")
        print(f"👁️  Looks Found: {looks_info.get('total_found', 0)}")
        print(f"🗃️  Models Found: {models_info.get('total_found', 0)}")
        
        if results_file:
            print(f"💾 Full results saved to: {results_file}")
        
        print("\n🎯 Next Steps:")
        print("   1. Review the saved results file for detailed information")
        print("   2. Test specific endpoints via the API server")
        print("   3. Integrate Looker insights into Sophia workflows")
        
        print("\n🔗 API Endpoints Available:")
        print("   - GET /api/business/looker/health")
        print("   - GET /api/business/looker/dashboards")
        print("   - GET /api/business/looker/looks")
        print("   - GET /api/business/looker/models")
        print("   - GET /api/business/looker/search?q=revenue")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Exploration interrupted by user")
    except Exception as e:
        logger.error(f"Exploration failed with unexpected error: {str(e)}")
        print(f"\n❌ Exploration failed: {str(e)}")
    finally:
        print("\n✅ Exploration complete!")

if __name__ == "__main__":
    asyncio.run(main())