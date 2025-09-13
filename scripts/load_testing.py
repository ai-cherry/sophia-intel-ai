"""
Comprehensive Load Testing Framework
Tests system performance under various load conditions
"""
import argparse
import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import aiohttp
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@dataclass
class LoadTestConfig:
    """Configuration for load tests"""
    base_url: str = "http://localhost:8000"
    concurrent_users: int = 10
    requests_per_user: int = 100
    ramp_up_time: int = 30  # seconds
    test_duration: int = 300  # seconds
    endpoints_to_test: List[str] = field(
        default_factory=lambda: [
            "/health",
            "/api/teams/run",
            "/api/memory/search",
            "/api/embeddings",
        ]
    )
    api_key: Optional[str] = None
@dataclass
class TestResult:
    """Individual test result"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    success: bool
    error: Optional[str] = None
@dataclass
class LoadTestResults:
    """Complete load test results"""
    config: LoadTestConfig
    results: List[TestResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    @property
    def total_requests(self) -> int:
        return len(self.results)
    @property
    def successful_requests(self) -> int:
        return sum(1 for r in self.results if r.success)
    @property
    def failed_requests(self) -> int:
        return self.total_requests - self.successful_requests
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    @property
    def response_times(self) -> List[float]:
        return [r.response_time for r in self.results if r.success]
    @property
    def avg_response_time(self) -> float:
        times = self.response_times
        return statistics.mean(times) if times else 0.0
    @property
    def median_response_time(self) -> float:
        times = self.response_times
        return statistics.median(times) if times else 0.0
    @property
    def p95_response_time(self) -> float:
        times = self.response_times
        if not times:
            return 0.0
        times.sort()
        index = int(0.95 * len(times))
        return times[index] if index < len(times) else times[-1]
    @property
    def requests_per_second(self) -> float:
        if not self.start_time or not self.end_time:
            return 0.0
        duration = (self.end_time - self.start_time).total_seconds()
        return self.successful_requests / duration if duration > 0 else 0.0
class LoadTester:
    """Main load testing class"""
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_users * 2,
            limit_per_host=self.config.concurrent_users,
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=5)
        headers = {"User-Agent": "Sophia-LoadTester/1.0"}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
        self.session = aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers=headers
        )
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    async def make_request(
        self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """Make a single HTTP request and record result"""
        url = f"{self.config.base_url}{endpoint}"
        start_time = time.time()
        timestamp = datetime.utcnow()
        try:
            async with self.session.request(method, url, json=data) as response:
                await response.text()  # Read response body
                response_time = time.time() - start_time
                return TestResult(
                    endpoint=endpoint,
                    method=method,
                    status_code=response.status,
                    response_time=response_time,
                    timestamp=timestamp,
                    success=200 <= response.status < 400,
                )
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=response_time,
                timestamp=timestamp,
                success=False,
                error=str(e),
            )
    async def user_simulation(self, user_id: int) -> List[TestResult]:
        """Simulate a single user's activity"""
        results = []
        for i in range(self.config.requests_per_user):
            # Distribute requests across endpoints
            endpoint = self.config.endpoints_to_test[
                i % len(self.config.endpoints_to_test)
            ]
            # Create appropriate request data
            data = self.get_request_data(endpoint)
            method = "POST" if data else "GET"
            result = await self.make_request(endpoint, method, data)
            results.append(result)
            # Small delay between requests (simulate human behavior)
            await asyncio.sleep(0.1)
        logger.info(f"User {user_id} completed {len(results)} requests")
        return results
    def get_request_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get appropriate request data for endpoint"""
        if "/teams/run" in endpoint:
            return {
                "message": "Test message for load testing",
                "team_id": "strategic-swarm",
                "temperature": 0.7,
                "max_tokens": 100,
            }
        elif "/memory/search" in endpoint:
            return {"query": "load test query", "top_k": 5}
        elif "/embeddings" in endpoint:
            return {
                "text": "Load testing text for embedding generation",
                "model": "text-embedding-ada-002",
            }
        return None
    async def run_load_test(self) -> LoadTestResults:
        """Run complete load test"""
        logger.info(f"Starting load test with {self.config.concurrent_users} users")
        logger.info(f"Target: {self.config.requests_per_user} requests per user")
        logger.info(f"Endpoints: {self.config.endpoints_to_test}")
        results = LoadTestResults(config=self.config)
        results.start_time = datetime.utcnow()
        # Create user simulation tasks
        tasks = []
        for user_id in range(self.config.concurrent_users):
            task = asyncio.create_task(self.user_simulation(user_id))
            tasks.append(task)
            # Stagger user starts (ramp up)
            if self.config.ramp_up_time > 0:
                delay = self.config.ramp_up_time / self.config.concurrent_users
                await asyncio.sleep(delay)
        # Wait for all users to complete
        logger.info("Waiting for all users to complete...")
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        # Collect all results
        for user_result in user_results:
            if isinstance(user_result, Exception):
                logger.error(f"User simulation failed: {user_result}")
            else:
                results.results.extend(user_result)
        results.end_time = datetime.utcnow()
        return results
    async def run_spike_test(self, spike_multiplier: int = 5) -> LoadTestResults:
        """Run spike test with sudden load increase"""
        logger.info(f"Running spike test with {spike_multiplier}x load")
        # Normal load phase
        normal_config = LoadTestConfig(
            base_url=self.config.base_url,
            concurrent_users=self.config.concurrent_users,
            requests_per_user=50,
            api_key=self.config.api_key,
            endpoints_to_test=self.config.endpoints_to_test,
        )
        normal_results = await LoadTester(normal_config).run_load_test()
        # Spike phase
        spike_config = LoadTestConfig(
            base_url=self.config.base_url,
            concurrent_users=self.config.concurrent_users * spike_multiplier,
            requests_per_user=20,
            ramp_up_time=5,  # Quick ramp up for spike
            api_key=self.config.api_key,
            endpoints_to_test=self.config.endpoints_to_test,
        )
        spike_results = await LoadTester(spike_config).run_load_test()
        # Combine results
        combined_results = LoadTestResults(config=self.config)
        combined_results.results = normal_results.results + spike_results.results
        combined_results.start_time = normal_results.start_time
        combined_results.end_time = spike_results.end_time
        return combined_results
    async def run_endurance_test(self, duration_minutes: int = 60) -> LoadTestResults:
        """Run endurance test with sustained load"""
        logger.info(f"Running endurance test for {duration_minutes} minutes")
        results = LoadTestResults(config=self.config)
        results.start_time = datetime.utcnow()
        # Configure for endurance
        endurance_config = LoadTestConfig(
            base_url=self.config.base_url,
            concurrent_users=max(1, self.config.concurrent_users // 2),
            requests_per_user=duration_minutes * 10,  # Sustained requests
            ramp_up_time=60,  # Gradual ramp up
            api_key=self.config.api_key,
            endpoints_to_test=self.config.endpoints_to_test,
        )
        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        while datetime.utcnow() < end_time:
            batch_results = await LoadTester(endurance_config).run_load_test()
            results.results.extend(batch_results.results)
            # Brief pause between batches
            await asyncio.sleep(30)
        results.end_time = datetime.utcnow()
        return results
    async def run_scalability_test(
        self, max_users: int = 100, step_size: int = 10, step_duration: int = 60
    ) -> List[LoadTestResults]:
        """Run scalability test with increasing user loads"""
        logger.info(f"Running scalability test up to {max_users} users")
        scalability_results = []
        for user_count in range(step_size, max_users + 1, step_size):
            logger.info(f"Testing with {user_count} concurrent users")
            scale_config = LoadTestConfig(
                base_url=self.config.base_url,
                concurrent_users=user_count,
                requests_per_user=min(50, step_duration),
                ramp_up_time=30,
                test_duration=step_duration,
                api_key=self.config.api_key,
                endpoints_to_test=self.config.endpoints_to_test,
            )
            scale_result = await LoadTester(scale_config).run_load_test()
            scalability_results.append(scale_result)
            # Log key metrics for this scale
            logger.info(
                f"Scale {user_count}: {scale_result.avg_response_time*1000:.1f}ms avg, "
                f"{scale_result.success_rate:.1f}% success, "
                f"{scale_result.requests_per_second:.1f} RPS"
            )
            # Brief cooldown
            await asyncio.sleep(10)
        return scalability_results
    async def run_chaos_test(self, chaos_duration: int = 300) -> LoadTestResults:
        """Run chaos test with random load patterns"""
        import random
        logger.info(f"Running chaos test for {chaos_duration} seconds")
        results = LoadTestResults(config=self.config)
        results.start_time = datetime.utcnow()
        end_time = datetime.utcnow() + timedelta(seconds=chaos_duration)
        while datetime.utcnow() < end_time:
            # Random chaos parameters
            chaos_users = random.randint(1, self.config.concurrent_users * 3)
            chaos_requests = random.randint(10, 100)
            chaos_endpoints = random.sample(
                self.config.endpoints_to_test,
                random.randint(1, len(self.config.endpoints_to_test)),
            )
            chaos_config = LoadTestConfig(
                base_url=self.config.base_url,
                concurrent_users=chaos_users,
                requests_per_user=chaos_requests,
                ramp_up_time=random.randint(5, 30),
                api_key=self.config.api_key,
                endpoints_to_test=chaos_endpoints,
            )
            logger.info(
                f"Chaos burst: {chaos_users} users, {chaos_requests} requests, "
                f"{len(chaos_endpoints)} endpoints"
            )
            chaos_results = await LoadTester(chaos_config).run_load_test()
            results.results.extend(chaos_results.results)
            # Random pause between chaos events
            await asyncio.sleep(random.randint(10, 60))
        results.end_time = datetime.utcnow()
        return results
def print_results(results: LoadTestResults):
    """Print formatted test results"""
    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    print(
        f"Test Duration: {(results.end_time - results.start_time).total_seconds():.2f} seconds"
    )
    print(f"Total Requests: {results.total_requests}")
    print(f"Successful Requests: {results.successful_requests}")
    print(f"Failed Requests: {results.failed_requests}")
    print(f"Success Rate: {results.success_rate:.2f}%")
    print(f"Requests/Second: {results.requests_per_second:.2f}")
    print("\nRESPONSE TIMES:")
    print(f"Average: {results.avg_response_time*1000:.2f}ms")
    print(f"Median: {results.median_response_time*1000:.2f}ms")
    print(f"95th Percentile: {results.p95_response_time*1000:.2f}ms")
    # Status code breakdown
    status_codes = {}
    for result in results.results:
        status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1
    print("\nSTATUS CODE BREAKDOWN:")
    for code, count in sorted(status_codes.items()):
        print(f"  {code}: {count}")
    # Endpoint performance
    endpoint_stats = {}
    for result in results.results:
        if result.endpoint not in endpoint_stats:
            endpoint_stats[result.endpoint] = []
        endpoint_stats[result.endpoint].append(result)
    print("\nENDPOINT PERFORMANCE:")
    for endpoint, endpoint_results in endpoint_stats.items():
        successful = [r for r in endpoint_results if r.success]
        if successful:
            avg_time = statistics.mean([r.response_time for r in successful]) * 1000
            success_rate = len(successful) / len(endpoint_results) * 100
            print(f"  {endpoint}: {avg_time:.2f}ms avg, {success_rate:.1f}% success")
    # Error analysis
    errors = [r for r in results.results if not r.success and r.error]
    if errors:
        print("\nERRORS:")
        error_counts = {}
        for error in errors:
            error_counts[error.error] = error_counts.get(error.error, 0) + 1
        for error, count in error_counts.items():
            print(f"  {error}: {count}")
async def main():
    """Main load testing function"""
    parser = argparse.ArgumentParser(description="Sophia Intel AI Load Testing")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Base URL to test"
    )
    parser.add_argument("--users", type=int, default=10, help="Concurrent users")
    parser.add_argument("--requests", type=int, default=100, help="Requests per user")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument(
        "--test-type",
        choices=["load", "spike", "endurance", "scalability", "chaos"],
        default="load",
        help="Test type",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in minutes (for endurance) or seconds (for chaos)",
    )
    parser.add_argument(
        "--max-users", type=int, default=100, help="Maximum users for scalability test"
    )
    parser.add_argument(
        "--step-size",
        type=int,
        default=10,
        help="User increment step for scalability test",
    )
    parser.add_argument("--output", help="Output file for results (JSON format)")
    args = parser.parse_args()
    config = LoadTestConfig(
        base_url=args.url,
        concurrent_users=args.users,
        requests_per_user=args.requests,
        api_key=args.api_key,
    )
    async with LoadTester(config) as tester:
        if args.test_type == "spike":
            results = await tester.run_spike_test()
            print_results(results)
        elif args.test_type == "endurance":
            results = await tester.run_endurance_test(duration_minutes=args.duration)
            print_results(results)
        elif args.test_type == "scalability":
            scalability_results = await tester.run_scalability_test(
                max_users=args.max_users, step_size=args.step_size
            )
            print_scalability_results(scalability_results)
        elif args.test_type == "chaos":
            results = await tester.run_chaos_test(chaos_duration=args.duration * 60)
            print_results(results)
        else:
            results = await tester.run_load_test()
            print_results(results)
        # Save results if output file specified
        if args.output:
            if args.test_type == "scalability":
                save_scalability_results(scalability_results, args.output)
            else:
                save_results(results, args.output)
def print_scalability_results(results_list: List[LoadTestResults]):
    """Print scalability test results"""
    print("\n" + "=" * 60)
    print("SCALABILITY TEST RESULTS")
    print("=" * 60)
    print(
        f"{'Users':<8} {'RPS':<8} {'Avg(ms)':<10} {'P95(ms)':<10} {'Success%':<10} {'Errors':<8}"
    )
    print("-" * 60)
    for result in results_list:
        users = result.config.concurrent_users
        rps = result.requests_per_second
        avg_ms = result.avg_response_time * 1000
        p95_ms = result.p95_response_time * 1000
        success_rate = result.success_rate
        errors = result.failed_requests
        print(
            f"{users:<8} {rps:<8.1f} {avg_ms:<10.1f} {p95_ms:<10.1f} {success_rate:<10.1f} {errors:<8}"
        )
def save_results(results: LoadTestResults, filename: str):
    """Save test results to JSON file"""
    output_data = {
        "test_type": "load_test",
        "config": {
            "base_url": results.config.base_url,
            "concurrent_users": results.config.concurrent_users,
            "requests_per_user": results.config.requests_per_user,
            "test_duration": results.config.test_duration,
        },
        "summary": {
            "total_requests": results.total_requests,
            "successful_requests": results.successful_requests,
            "failed_requests": results.failed_requests,
            "success_rate": results.success_rate,
            "avg_response_time_ms": results.avg_response_time * 1000,
            "p95_response_time_ms": results.p95_response_time * 1000,
            "requests_per_second": results.requests_per_second,
        },
        "timestamp": datetime.utcnow().isoformat(),
        "start_time": results.start_time.isoformat() if results.start_time else None,
        "end_time": results.end_time.isoformat() if results.end_time else None,
    }
    with open(filename, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nResults saved to {filename}")
def save_scalability_results(results_list: List[LoadTestResults], filename: str):
    """Save scalability test results to JSON file"""
    output_data = {"test_type": "scalability_test", "results": []}
    for result in results_list:
        result_data = {
            "concurrent_users": result.config.concurrent_users,
            "total_requests": result.total_requests,
            "success_rate": result.success_rate,
            "avg_response_time_ms": result.avg_response_time * 1000,
            "p95_response_time_ms": result.p95_response_time * 1000,
            "requests_per_second": result.requests_per_second,
        }
        output_data["results"].append(result_data)
    output_data["timestamp"] = datetime.utcnow().isoformat()
    with open(filename, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nScalability results saved to {filename}")
if __name__ == "__main__":
    asyncio.run(main())
