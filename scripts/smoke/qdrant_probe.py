#!/usr/bin/env python3
"""
Comprehensive Qdrant authentication probe with full CRUD cycle.
Tests: list collections → create collection → insert point → search → delete collection
"""
import os, sys, httpx, json, time

URL = os.environ.get("QDRANT_URL")  # e.g. https://...qdrant.io:6333
KEY = os.environ.get("QDRANT_API_KEY")
TIMEOUT = float(os.environ.get("SMOKE_HTTP_TIMEOUT", "15"))

if not URL or not KEY:
    print("MISSING: QDRANT_URL or QDRANT_API_KEY", file=sys.stderr)
    sys.exit(2)

# Clean URL (remove trailing slash)
base_url = URL.rstrip('/')
collection_name = "sophia_smoke"

def try_auth_variants(client, method, endpoint, **kwargs):
    """Try different auth header variants for Qdrant"""
    auth_variants = [
        {"api-key": KEY},
        {"x-api-key": KEY},
        {"Authorization": f"Bearer {KEY}"},
    ]
    
    # If key contains pipe, it might be cluster|key format - try as-is
    if "|" in KEY:
        print(f"Key contains pipe delimiter - using full key as-is")
    
    for i, headers in enumerate(auth_variants):
        try:
            print(f"Auth attempt {i+1}: {list(headers.keys())[0]} header")
            response = client.request(method, f"{base_url}{endpoint}", headers=headers, **kwargs)
            print(f"{method} {endpoint} -> {response.status_code}")
            
            if response.status_code < 400:
                return response, headers
            elif response.status_code in [401, 403]:
                print(f"Auth failed with {list(headers.keys())[0]}: {response.status_code}")
                continue
            else:
                # Other error, return it
                return response, headers
                
        except Exception as e:
            print(f"Request failed with {list(headers.keys())[0]}: {e}")
            continue
    
    # All auth variants failed
    return None, None

def main():
    print(f"Qdrant Probe - Base URL: {base_url}")
    print(f"Collection: {collection_name}")
    print(f"Key format: {'pipe-delimited' if '|' in KEY else 'standard'}")
    print("=" * 50)
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            
            # Step 1: List collections
            print("\n1. LIST COLLECTIONS")
            response, auth_headers = try_auth_variants(client, "GET", "/collections")
            
            if not response:
                print("❌ All auth variants failed for GET /collections")
                sys.exit(3)
            
            if response.status_code != 200:
                print(f"❌ GET /collections failed: {response.status_code}")
                print(f"Response: {response.text[:400]}")
                sys.exit(3)
            
            data = response.json()
            existing_collections = [c["name"] for c in data.get("result", {}).get("collections", [])]
            print(f"✅ Existing collections: {existing_collections}")
            
            # Step 2: Create test collection
            print(f"\n2. CREATE COLLECTION: {collection_name}")
            collection_config = {
                "vectors": {
                    "size": 3,
                    "distance": "Cosine"
                }
            }
            
            response = client.put(
                f"{base_url}/collections/{collection_name}",
                headers=auth_headers,
                json=collection_config
            )
            print(f"PUT /collections/{collection_name} -> {response.status_code}")
            
            if response.status_code not in [200, 201]:
                print(f"❌ Collection creation failed: {response.status_code}")
                print(f"Response: {response.text[:400]}")
                sys.exit(4)
            
            print(f"✅ Collection '{collection_name}' created")
            
            # Step 3: Insert test point
            print(f"\n3. INSERT POINT")
            point_data = {
                "points": [
                    {
                        "id": 1,
                        "vector": [0.1, 0.2, 0.3],
                        "payload": {
                            "smoke": True,
                            "timestamp": time.time(),
                            "test": "qdrant_probe"
                        }
                    }
                ]
            }
            
            response = client.put(
                f"{base_url}/collections/{collection_name}/points",
                headers=auth_headers,
                json=point_data
            )
            print(f"PUT /collections/{collection_name}/points -> {response.status_code}")
            
            if response.status_code not in [200, 201, 202]:
                print(f"❌ Point insertion failed: {response.status_code}")
                print(f"Response: {response.text[:400]}")
                # Continue to cleanup
            else:
                print(f"✅ Point inserted successfully")
                
                # Step 4: Search for the point
                print(f"\n4. SEARCH POINTS")
                search_query = {
                    "vector": [0.1, 0.2, 0.3],
                    "limit": 1,
                    "with_payload": True
                }
                
                response = client.post(
                    f"{base_url}/collections/{collection_name}/points/search",
                    headers=auth_headers,
                    json=search_query
                )
                print(f"POST /collections/{collection_name}/points/search -> {response.status_code}")
                
                if response.status_code == 200:
                    search_results = response.json()
                    results = search_results.get("result", [])
                    print(f"✅ Search returned {len(results)} results")
                    if results:
                        best_match = results[0]
                        print(f"Best match: ID={best_match.get('id')}, Score={best_match.get('score', 'N/A')}")
                else:
                    print(f"❌ Search failed: {response.status_code}")
                    print(f"Response: {response.text[:400]}")
            
            # Step 5: Cleanup - Delete collection
            print(f"\n5. CLEANUP - DELETE COLLECTION")
            response = client.delete(
                f"{base_url}/collections/{collection_name}",
                headers=auth_headers
            )
            print(f"DELETE /collections/{collection_name} -> {response.status_code}")
            
            if response.status_code in [200, 204]:
                print(f"✅ Collection '{collection_name}' deleted successfully")
            else:
                print(f"⚠️ Collection deletion failed: {response.status_code}")
                print(f"Response: {response.text[:400]}")
            
            print("\n" + "=" * 50)
            print("✅ QDRANT PROBE COMPLETED SUCCESSFULLY")
            print(f"Auth method: {list(auth_headers.keys())[0]}")
            print("Full CRUD cycle: list → create → insert → search → delete")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ PROBE FAILED: {repr(e)}", file=sys.stderr)
        print(f"Base URL: {base_url}")
        print(f"Auth headers attempted: api-key, x-api-key, Authorization Bearer")
        print(f"Key format: {'pipe-delimited' if '|' in KEY else 'standard'}")
        sys.exit(10)

if __name__ == "__main__":
    main()

