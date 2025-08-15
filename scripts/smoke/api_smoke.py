#!/usr/bin/env python3
"""
FastAPI smoke test - Boot the API and validate health endpoint.
Real API testing with actual FastAPI server startup.
"""
import os, sys, time, subprocess, httpx, signal
from pathlib import Path

TIMEOUT = float(os.environ.get("SMOKE_HTTP_TIMEOUT", "15"))
API_PORT = int(os.environ.get("API_PORT", "8000"))
API_HOST = os.environ.get("API_HOST", "127.0.0.1")

def main():
    print("FASTAPI SMOKE TEST")
    print("=" * 40)
    print(f"Target: http://{API_HOST}:{API_PORT}")
    
    # Start FastAPI server
    print("\n1. STARTING FASTAPI SERVER")
    try:
        # Use uvicorn to start the FastAPI app
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "backend.main:app",
            "--host", API_HOST,
            "--port", str(API_PORT),
            "--log-level", "info"
        ]
        
        print(f"Command: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        print("Waiting for server startup...")
        time.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start")
            print(f"STDOUT: {stdout[:500]}")
            print(f"STDERR: {stderr[:500]}")
            sys.exit(3)
        
        print("✅ Server process started")
        
        # Test health endpoint
        print("\n2. TESTING HEALTH ENDPOINT")
        base_url = f"http://{API_HOST}:{API_PORT}"
        
        with httpx.Client(timeout=TIMEOUT) as client:
            # Try multiple health endpoint variations
            health_endpoints = ["/health", "/healthz", "/", "/status", "/ping"]
            
            for endpoint in health_endpoints:
                try:
                    print(f"Testing {endpoint}...")
                    response = client.get(f"{base_url}{endpoint}")
                    print(f"GET {endpoint} -> {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"✅ Health endpoint found: {endpoint}")
                        try:
                            data = response.json()
                            print(f"Response: {data}")
                        except:
                            print(f"Response: {response.text[:200]}")
                        
                        # Test additional endpoints if health works
                        print("\n3. TESTING ADDITIONAL ENDPOINTS")
                        additional_endpoints = ["/docs", "/openapi.json", "/metrics"]
                        
                        for extra_endpoint in additional_endpoints:
                            try:
                                extra_response = client.get(f"{base_url}{extra_endpoint}")
                                print(f"GET {extra_endpoint} -> {extra_response.status_code}")
                            except Exception as e:
                                print(f"GET {extra_endpoint} -> Error: {repr(e)}")
                        
                        print("\n✅ FASTAPI SMOKE TEST SUCCESSFUL")
                        return True
                        
                    elif response.status_code == 404:
                        print(f"404 - endpoint not found")
                        continue
                    else:
                        print(f"Unexpected status: {response.text[:200]}")
                        
                except httpx.ConnectError:
                    print(f"Connection failed - server may not be ready")
                    if endpoint == health_endpoints[0]:
                        # Wait a bit more for first endpoint
                        print("Waiting additional 2 seconds...")
                        time.sleep(2)
                    continue
                except Exception as e:
                    print(f"Request error: {repr(e)}")
                    continue
            
            print("❌ No working health endpoint found")
            return False
            
    except Exception as e:
        print(f"❌ Smoke test failed: {repr(e)}")
        return False
        
    finally:
        # Cleanup: terminate server process
        if 'process' in locals() and process.poll() is None:
            print("\n4. CLEANUP - Terminating server")
            try:
                process.terminate()
                process.wait(timeout=5)
                print("✅ Server terminated gracefully")
            except subprocess.TimeoutExpired:
                print("⚠️ Force killing server")
                process.kill()
                process.wait()
            except Exception as e:
                print(f"⚠️ Cleanup error: {repr(e)}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 3)

