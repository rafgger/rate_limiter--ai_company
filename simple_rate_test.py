#!/usr/bin/env python3
"""
Simple rate limiter test using the requests library
Run this after starting your FastAPI server
"""

import requests
import time
import json
from typing import Dict, List

class SimpleRateLimiterTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def test_endpoint(self, endpoint: str, num_requests: int = 15, delay: float = 0.1):
        """Test an endpoint with multiple requests"""
        print(f"\n🧪 Testing {endpoint} with {num_requests} requests")
        print("-" * 50)
        
        successful = 0
        rate_limited = 0
        
        for i in range(num_requests):
            try:
                start_time = time.time()
                
                if endpoint == "/api/upload":
                    response = requests.post(
                        f"{self.base_url}{endpoint}", 
                        json={"test": f"data_{i}"},
                        timeout=5
                    )
                else:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                
                response_time = time.time() - start_time
                
                # Status indicator
                if response.status_code == 200:
                    status_icon = "✅"
                    successful += 1
                elif response.status_code == 429:
                    status_icon = "🚫"
                    rate_limited += 1
                else:
                    status_icon = "❓"
                
                print(f"Request {i+1:2d}: {status_icon} {response.status_code} ({response_time:.3f}s)", end="")
                
                # Show rate limit headers
                if 'x-ratelimit-remaining' in response.headers:
                    remaining = response.headers.get('x-ratelimit-remaining')
                    print(f" | Remaining: {remaining}", end="")
                
                if response.status_code == 429:
                    retry_after = response.headers.get('retry-after', 'N/A')
                    print(f" | Retry-After: {retry_after}s", end="")
                
                print()  # New line
                
                # Small delay between requests
                if delay > 0:
                    time.sleep(delay)
                    
            except requests.exceptions.RequestException as e:
                print(f"Request {i+1:2d}: ❌ Error: {e}")
        
        print(f"\nSummary:")
        print(f"  ✅ Successful: {successful}")
        print(f"  🚫 Rate Limited: {rate_limited}")
        print(f"  📊 Success Rate: {successful/num_requests*100:.1f}%")
    
    def test_burst_and_recovery(self, endpoint: str):
        """Test burst capacity and rate recovery"""
        print(f"\n🚀 Testing burst capacity and recovery for {endpoint}")
        print("-" * 50)
        
        # Phase 1: Burst test
        print("Phase 1: Testing burst capacity...")
        burst_requests = 12  # More than any burst limit
        
        for i in range(burst_requests):
            try:
                if endpoint == "/api/upload":
                    response = requests.post(f"{self.base_url}{endpoint}", json={"burst": f"test_{i}"})
                else:
                    response = requests.get(f"{self.base_url}{endpoint}")
                
                status_icon = "✅" if response.status_code == 200 else "🚫"
                print(f"  Burst {i+1:2d}: {status_icon} {response.status_code}")
                
                if response.status_code == 429:
                    retry_after = response.headers.get('retry-after', '5')
                    print(f"    Rate limited! Waiting {retry_after} seconds for recovery...")
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"  Burst {i+1:2d}: ❌ Error: {e}")
        
        # Phase 2: Wait and test recovery
        print("\nPhase 2: Testing rate limit recovery...")
        wait_time = 3  # Wait a few seconds
        print(f"Waiting {wait_time} seconds...")
        time.sleep(wait_time)
        
        try:
            if endpoint == "/api/upload":
                response = requests.post(f"{self.base_url}{endpoint}", json={"recovery": "test"})
            else:
                response = requests.get(f"{self.base_url}{endpoint}")
            
            if response.status_code == 200:
                print("✅ Rate limit recovered successfully!")
            else:
                print(f"❌ Still rate limited (status: {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error during recovery test: {e}")
    
    def check_server_status(self):
        """Check if the FastAPI server is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ FastAPI server is running")  
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            print("Make sure your FastAPI server is running on http://localhost:8000")
            return False
    
    def show_rate_limit_status(self):
        """Show current rate limit status"""
        try:
            response = requests.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                data = response.json()
                print("\n📊 Current Rate Limit Status:") # test step ### (2)
                print("-" * 30)
                
                status = data.get('rate_limit_status', {})
                for limiter_name, info in status.items():
                    print(f"{limiter_name.capitalize()} Limiter:")
                    print(f"  Remaining: {info.get('remaining_requests', 'N/A')}")
                    print(f"  Capacity: {info.get('capacity', 'N/A')}")
                    print(f"  Rate: {info.get('refill_rate_per_minute', 'N/A')} req/min")
                    print()
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not get rate limit status: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🔧 FastAPI Rate Limiter Test Suite") # test starts with step ### (1)
        print("=" * 60)
        
        # Check server status first
        if not self.check_server_status():
            return
        
        # Show initial status
        self.show_rate_limit_status()
        
        # Test different endpoints
        endpoints_to_test = [
            ("/api/data", "Default limiter (60/min, burst 10)"),
            ("/api/premium", "Strict limiter (20/min, burst 5)"),
            ("/api/upload", "Upload limiter (10/min, burst 2)")
        ]
        
        for endpoint, description in endpoints_to_test:
            print(f"\n🎯 Testing {endpoint}")
            print(f"   {description}")
            self.test_endpoint(endpoint, num_requests=8, delay=0.1)
        
        # Test burst and recovery for one endpoint
        self.test_burst_and_recovery("/api/data")
        
        # Show final status
        self.show_rate_limit_status()
        
        print("\n" + "=" * 60)
        print("✅ Test suite completed!")

def quick_burst_test():
    """Quick test to see rate limiting in action"""
    tester = SimpleRateLimiterTest()
    
    if not tester.check_server_status():
        return
    
    print("\n🏃 Quick Burst Test")
    print("Making 15 rapid requests to /api/data...")
    
    for i in range(15):
        try:
            response = requests.get("http://localhost:8000/api/data")
            status_icon = "✅" if response.status_code == 200 else "🚫"
            remaining = response.headers.get('x-ratelimit-remaining', 'N/A')
            print(f"{i+1:2d}: {status_icon} {response.status_code} (Remaining: {remaining})")
        except Exception as e:
            print(f"{i+1:2d}: ❌ {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_burst_test()
    else:
        tester = SimpleRateLimiterTest()
        tester.run_all_tests()