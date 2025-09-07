"""
Looker API Integration Client

Provides access to Looker business intelligence data through the Looker SDK.
Supports dashboards, looks, queries, and data exploration.
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

try:
    import looker_sdk
    from looker_sdk import error
    from looker_sdk import models40 as models

    SDK_AVAILABLE = True
except ImportError as e:
    looker_sdk = None
    models = None
    error = None
    SDK_AVAILABLE = False
    SDK_IMPORT_ERROR = str(e)


logger = logging.getLogger(__name__)

# Provide a safe default for INTEGRATIONS if not imported from a central config
try:
    INTEGRATIONS  # type: ignore[name-defined]
except NameError:
    INTEGRATIONS = {}


@dataclass
class LookerDashboard:
    """Looker dashboard metadata"""

    id: str
    title: str
    description: Optional[str]
    folder_id: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    view_count: Optional[int]
    favorite_count: Optional[int]


@dataclass
class LookerLook:
    """Looker look (saved visualization) metadata"""

    id: str
    title: str
    description: Optional[str]
    query_id: Optional[str]
    folder_id: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    view_count: Optional[int]


@dataclass
class LookerQuery:
    """Looker query metadata and results"""

    id: str
    model: str
    explore: str
    dimensions: list[str]
    measures: list[str]
    filters: dict[str, str]
    sorts: list[str]
    limit: Optional[int]
    total: Optional[bool]


class LookerClient:
    """Looker API client wrapper"""

    def __init__(self):
        if not SDK_AVAILABLE:
            raise ImportError(f"Looker SDK import failed: {SDK_IMPORT_ERROR}")

        self.config = INTEGRATIONS.get("looker", {})
        if not self.config.get("enabled"):
            raise ValueError("Looker integration not enabled")

        # Initialize SDK
        self.sdk = None
        self._initialize_sdk()

    def _initialize_sdk(self):
        """Initialize Looker SDK with configuration"""
        try:
            # Set environment variables for SDK
            os.environ["LOOKERSDK_BASE_URL"] = self.config["base_url"]
            os.environ["LOOKERSDK_CLIENT_ID"] = self.config["client_id"]
            os.environ["LOOKERSDK_CLIENT_SECRET"] = self.config["client_secret"]
            os.environ["LOOKERSDK_VERIFY_SSL"] = "true"

            # Initialize SDK
            self.sdk = looker_sdk.init40()
            logger.info("Looker SDK initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Looker SDK: {str(e)}")
            raise

    def test_connection(self) -> dict[str, Any]:
        """Test Looker API connection"""
        try:
            # Test API connection
            me = self.sdk.me()

            return {
                "status": "connected",
                "user_id": me.id,
                "email": me.email,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "display_name": me.display_name,
                "is_disabled": me.is_disabled,
                "looker_version": self.sdk.versions().looker_release_version,
            }

        except Exception as e:
            logger.error(f"Looker connection test failed: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def get_dashboards(self, limit: int = 50) -> list[LookerDashboard]:
        """Get list of Looker dashboards"""
        try:
            dashboards = self.sdk.all_dashboards(
                fields="id,title,description,folder_id,created_at,updated_at,view_count,favorite_count"
            )

            result = []
            for dash in dashboards[:limit]:
                result.append(
                    LookerDashboard(
                        id=str(dash.id),
                        title=dash.title or "Untitled",
                        description=getattr(dash, "description", None),
                        folder_id=(
                            str(getattr(dash, "folder_id", None))
                            if getattr(dash, "folder_id", None)
                            else None
                        ),
                        created_at=getattr(dash, "created_at", None),
                        updated_at=getattr(dash, "updated_at", None),
                        view_count=getattr(dash, "view_count", None),
                        favorite_count=getattr(dash, "favorite_count", None),
                    )
                )

            return result

        except Exception as e:
            logger.error(f"Failed to get dashboards: {str(e)}")
            raise

    def get_looks(self, limit: int = 50) -> list[LookerLook]:
        """Get list of Looker looks (saved visualizations)"""
        try:
            looks = self.sdk.all_looks(
                fields="id,title,description,query_id,folder_id,created_at,updated_at,view_count"
            )

            result = []
            for look in looks[:limit]:
                result.append(
                    LookerLook(
                        id=str(look.id),
                        title=look.title or "Untitled",
                        description=getattr(look, "description", None),
                        query_id=(
                            str(getattr(look, "query_id", None))
                            if getattr(look, "query_id", None)
                            else None
                        ),
                        folder_id=(
                            str(getattr(look, "folder_id", None))
                            if getattr(look, "folder_id", None)
                            else None
                        ),
                        created_at=getattr(look, "created_at", None),
                        updated_at=getattr(look, "updated_at", None),
                        view_count=getattr(look, "view_count", None),
                    )
                )

            return result

        except Exception as e:
            logger.error(f"Failed to get looks: {str(e)}")
            raise

    def get_dashboard_data(
        self, dashboard_id: str, filters: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """Get data from a specific dashboard"""
        try:
            # Get dashboard metadata
            dashboard = self.sdk.dashboard(dashboard_id)

            # Get dashboard elements (tiles)
            elements = []
            if dashboard.dashboard_elements:
                for element in dashboard.dashboard_elements:
                    element_data = {
                        "id": str(element.id),
                        "title": element.title,
                        "type": element.type,
                        "subtitle_text": element.subtitle_text,
                    }

                    # Get query data if available
                    if element.query_id:
                        try:
                            query_data = self.run_query(str(element.query_id), limit=100)
                            element_data["data"] = query_data
                        except Exception as e:
                            element_data["data_error"] = str(e)

                    elements.append(element_data)

            return {
                "dashboard": {
                    "id": str(dashboard.id),
                    "title": dashboard.title,
                    "description": dashboard.description,
                    "created_at": dashboard.created_at,
                    "updated_at": dashboard.updated_at,
                    "view_count": dashboard.view_count,
                },
                "elements": elements,
                "retrieved_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {str(e)}")
            raise

    def get_look_data(self, look_id: str, limit: int = 1000) -> dict[str, Any]:
        """Get data from a specific look"""
        try:
            # Get look metadata
            look = self.sdk.look(look_id)

            # Run the look's query
            data = []
            if look.query_id:
                data = self.run_query(str(look.query_id), limit=limit)

            return {
                "look": {
                    "id": str(look.id),
                    "title": look.title,
                    "description": look.description,
                    "created_at": look.created_at,
                    "updated_at": look.updated_at,
                    "view_count": look.view_count,
                },
                "data": data,
                "retrieved_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get look data: {str(e)}")
            raise

    def run_query(
        self, query_id: str, limit: int = 1000, format_type: str = "json"
    ) -> list[dict[str, Any]]:
        """Run a Looker query and return results"""
        try:
            # Run query
            result = self.sdk.run_query(query_id=query_id, result_format=format_type, limit=limit)

            # Parse JSON results
            if format_type == "json" and result:
                return json.loads(result)

            return []

        except Exception as e:
            logger.error(f"Failed to run query {query_id}: {str(e)}")
            raise

    def explore_data(
        self,
        model: str,
        explore: str,
        dimensions: list[str],
        measures: list[str],
        filters: Optional[dict[str, str]] = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """Explore data using Looker's explore API"""
        try:
            # Create query
            query = models.WriteQuery(
                model=model,
                explore=explore,
                dimensions=dimensions,
                measures=measures,
                filters=filters or {},
                limit=limit,
            )

            # Create and run query
            created_query = self.sdk.create_query(query)

            # Run query and get results
            result = self.sdk.run_query(query_id=str(created_query.id), result_format="json")

            # Parse results
            data = json.loads(result) if result else []

            return {
                "query": {
                    "id": str(created_query.id),
                    "model": model,
                    "explore": explore,
                    "dimensions": dimensions,
                    "measures": measures,
                    "filters": filters or {},
                    "limit": limit,
                },
                "data": data,
                "row_count": len(data),
                "retrieved_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to explore data: {str(e)}")
            raise

    def get_models(self) -> list[dict[str, Any]]:
        """Get list of available Looker models"""
        try:
            models_list = self.sdk.all_lookml_models()

            result = []
            for model in models_list:
                model_data = {
                    "name": getattr(model, "name", "Unknown"),
                    "title": getattr(model, "title", getattr(model, "name", "Unknown")),
                    "description": getattr(model, "description", None),
                    "explores_count": (
                        len(getattr(model, "explores", []))
                        if getattr(model, "explores", None)
                        else 0
                    ),
                }

                # Add explore information
                explores = getattr(model, "explores", [])
                if explores:
                    model_data["explores"] = [
                        {
                            "name": getattr(explore, "name", "Unknown"),
                            "title": getattr(explore, "title", getattr(explore, "name", "Unknown")),
                            "description": getattr(explore, "description", None),
                        }
                        for explore in explores[:10]  # Limit to first 10
                    ]

                result.append(model_data)

            return result

        except Exception as e:
            logger.error(f"Failed to get models: {str(e)}")
            raise

    def search_content(
        self, query: str, types: Optional[list[str]] = None, limit: int = 50
    ) -> dict[str, Any]:
        """Search Looker content (dashboards, looks, etc.)"""
        try:
            # Default search types
            if types is None:
                types = ["dashboard", "look", "query"]

            organized_results = {"dashboards": [], "looks": [], "queries": [], "other": []}

            # Search dashboards by title
            if "dashboard" in types:
                try:
                    dashboards = self.get_dashboards(limit=limit)
                    for dash in dashboards:
                        if query.lower() in dash.title.lower():
                            organized_results["dashboards"].append(
                                {
                                    "id": dash.id,
                                    "title": dash.title,
                                    "description": dash.description,
                                    "content_type": "dashboard",
                                    "updated_at": dash.updated_at,
                                    "view_count": dash.view_count,
                                }
                            )
                except Exception:
                    pass

            # Search looks by title
            if "look" in types:
                try:
                    looks = self.get_looks(limit=limit)
                    for look in looks:
                        if query.lower() in look.title.lower():
                            organized_results["looks"].append(
                                {
                                    "id": look.id,
                                    "title": look.title,
                                    "description": look.description,
                                    "content_type": "look",
                                    "updated_at": look.updated_at,
                                    "view_count": look.view_count,
                                }
                            )
                except Exception:
                    pass

            total_results = sum(len(items) for items in organized_results.values())

            return {
                "search_query": query,
                "total_results": total_results,
                "results": organized_results,
                "searched_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to search content: {str(e)}")
            raise

    def get_system_info(self) -> dict[str, Any]:
        """Get Looker system information and capabilities"""
        try:
            # Get version info
            versions = self.sdk.versions()

            # Get current user info
            me = self.sdk.me()

            # Get basic statistics
            dashboard_count = len(self.sdk.all_dashboards(fields="id"))
            look_count = len(self.sdk.all_looks(fields="id"))

            return {
                "looker_version": versions.looker_release_version,
                "api_version": versions.current_version.version,
                "supported_versions": (
                    [v.version for v in versions.supported_versions]
                    if versions.supported_versions
                    else []
                ),
                "current_user": {
                    "id": me.id,
                    "email": me.email,
                    "display_name": me.display_name,
                    "is_disabled": me.is_disabled,
                },
                "content_counts": {"dashboards": dashboard_count, "looks": look_count},
                "instance_url": self.config["base_url"],
                "retrieved_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            raise


def get_looker_client() -> LookerClient:
    """Get configured Looker client instance"""
    return LookerClient()
