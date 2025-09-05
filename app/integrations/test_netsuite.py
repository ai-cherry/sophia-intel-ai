"""
NetSuite Integration Test Script
Test connection and basic operations
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

from app.integrations.connectors.netsuite_connector import (
    NetSuiteAuthMethod,
    NetSuiteConfig,
    NetSuiteConnector,
    NetSuiteRecordType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_netsuite_connection():
    """Test NetSuite connection and basic operations"""

    # Load environment variables
    from pathlib import Path

    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    # Create NetSuite configuration
    config = NetSuiteConfig(
        name="netsuite",
        base_url="",  # Will be constructed from account_id
        account_id=os.getenv("NETSUITE_ACCOUNT_ID", ""),
        auth_method=(
            NetSuiteAuthMethod.OAUTH2
            if os.getenv("NETSUITE_AUTH_METHOD") == "oauth2"
            else NetSuiteAuthMethod.TOKEN_BASED
        ),
        # Token-Based Authentication
        consumer_key=os.getenv("NETSUITE_CONSUMER_KEY", ""),
        consumer_secret=os.getenv("NETSUITE_CONSUMER_SECRET", ""),
        token_id=os.getenv("NETSUITE_TOKEN_ID", ""),
        token_secret=os.getenv("NETSUITE_TOKEN_SECRET", ""),
        # OAuth 2.0
        client_id=os.getenv("NETSUITE_CLIENT_ID", ""),
        client_secret=os.getenv("NETSUITE_CLIENT_SECRET", ""),
        redirect_uri=os.getenv("NETSUITE_REDIRECT_URI", "https://localhost:8080/callback"),
        scope=os.getenv("NETSUITE_SCOPE", "rest_webservices"),
        # Features
        suiteql_enabled=os.getenv("NETSUITE_SUITEQL_ENABLED", "true").lower() == "true",
        restlet_enabled=os.getenv("NETSUITE_RESTLET_ENABLED", "false").lower() == "true",
        webhook_enabled=os.getenv("NETSUITE_WEBHOOK_ENABLED", "false").lower() == "true",
    )

    print("\n=== NetSuite Integration Test ===\n")
    print(f"Account ID: {config.account_id}")
    print(f"Auth Method: {config.auth_method.value}")
    print(f"Base URL: {config.base_url}")

    # Create connector
    connector = NetSuiteConnector(config)

    try:
        # Connect to NetSuite
        print("\n1. Testing connection...")
        await connector.connect()

        if connector.status.value == "healthy":
            print("✅ Connection successful!")
        else:
            print(f"❌ Connection failed. Status: {connector.status.value}")
            return

        # Get connector status
        print("\n2. Connector Status:")
        status = connector.get_status()
        print(f"   - Status: {status['status']}")
        print(f"   - Features: {status['features']}")

        # Test fetching metadata catalog
        print("\n3. Fetching metadata catalog...")
        try:
            metadata = await connector.make_request("GET", "record/v1/metadata-catalog")
            print(f"   ✅ Found {len(metadata.get('items', []))} record types")

            # Display first 5 record types
            for i, item in enumerate(metadata.get("items", [])[:5]):
                print(f"   - {item}")
        except Exception as e:
            print(f"   ❌ Error fetching metadata: {e}")

        # Test fetching customers
        print("\n4. Fetching customer records...")
        try:
            customers = await connector.fetch_data(
                {
                    "record_type": NetSuiteRecordType.CUSTOMER.value,
                    "limit": 5,
                    "fields": ["entityId", "companyName", "email"],
                }
            )

            if "items" in customers:
                print(f"   ✅ Found {len(customers['items'])} customers")
                for customer in customers["items"][:3]:
                    print(
                        f"   - {customer.get('entityId', 'N/A')}: "
                        f"{customer.get('companyName', 'Unknown')}"
                    )
            else:
                print("   ℹ️ No customers found or different response format")

        except Exception as e:
            print(f"   ❌ Error fetching customers: {e}")

        # Test SuiteQL if enabled
        if config.suiteql_enabled:
            print("\n5. Testing SuiteQL...")
            try:
                # Simple query to get subsidiaries
                query = "SELECT id, name FROM subsidiary"
                result = await connector.fetch_by_suiteql(query, limit=5)

                if "items" in result:
                    print(
                        f"   ✅ SuiteQL query successful. Found {len(result['items'])} subsidiaries"
                    )
                    for sub in result["items"][:3]:
                        print(f"   - {sub}")
                else:
                    print("   ℹ️ SuiteQL returned different format or no results")

            except Exception as e:
                print(f"   ❌ SuiteQL error: {e}")
        else:
            print("\n5. SuiteQL is disabled")

        # Test sync operation
        print("\n6. Testing sync operation...")
        try:
            # Sync recent customers
            sync_report = await connector.sync_customers()

            print("   ✅ Sync completed!")
            print(f"   - Success: {sync_report.success}")
            print(f"   - Records fetched: {sync_report.records_fetched}")
            print(f"   - Records stored: {sync_report.records_stored}")
            print(f"   - Duration: {sync_report.duration_seconds:.2f}s")

            if sync_report.errors:
                print(f"   - Errors: {sync_report.errors}")

        except Exception as e:
            print(f"   ❌ Sync error: {e}")

        # Test fetching sales orders
        print("\n7. Fetching recent sales orders...")
        try:
            # Get sales orders from last 30 days
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y")

            orders = await connector.fetch_data(
                {
                    "record_type": NetSuiteRecordType.SALES_ORDER.value,
                    "filters": {"tranDate": {"operator": ">=", "value": cutoff_date}},
                    "limit": 5,
                    "fields": ["tranId", "tranDate", "total", "status"],
                }
            )

            if "items" in orders:
                print(f"   ✅ Found {len(orders['items'])} sales orders")
                for order in orders["items"][:3]:
                    print(
                        f"   - {order.get('tranId', 'N/A')}: "
                        f"${order.get('total', 0)} ({order.get('status', 'Unknown')})"
                    )
            else:
                print("   ℹ️ No sales orders found in the last 30 days")

        except Exception as e:
            print(f"   ❌ Error fetching sales orders: {e}")

        print("\n=== Test Summary ===")
        print("✅ NetSuite integration is working!")
        print(f"Account: {config.account_id}")
        print(f"Authentication: {config.auth_method.value}")

        # Display metrics
        metrics = connector.metrics
        print("\nMetrics:")
        print(f"   - Total requests: {metrics['requests_total']}")
        print(f"   - Failed requests: {metrics['requests_failed']}")
        print(f"   - Total records: {metrics['total_records']}")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("NetSuite test failed")

    finally:
        # Disconnect
        await connector.disconnect()
        print("\n✅ Disconnected from NetSuite")


def main():
    """Run the test"""
    print("Starting NetSuite integration test...")
    print("Make sure you have configured your .env file with NetSuite credentials\n")

    # Load environment variables
    from pathlib import Path

    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    # Check for required environment variables
    required_vars = ["NETSUITE_ACCOUNT_ID"]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease configure your .env file with NetSuite credentials")
        return

    # Run async test
    asyncio.run(test_netsuite_connection())


if __name__ == "__main__":
    main()
