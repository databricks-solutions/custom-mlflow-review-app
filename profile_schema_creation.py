#!/usr/bin/env python3
"""Profile schema creation performance using cProfile."""

import cProfile
import pstats
import io
import asyncio
import time
from contextlib import contextmanager

import httpx


@contextmanager
def profile_block(name: str):
    """Context manager for profiling a code block."""
    pr = cProfile.Profile()
    start_time = time.time()
    
    pr.enable()
    try:
        yield pr
    finally:
        pr.disable()
        end_time = time.time()
        
        print(f"\n{'=' * 60}")
        print(f"Profile: {name}")
        print(f"Total time: {(end_time - start_time) * 1000:.1f}ms")
        print(f"{'=' * 60}")
        
        # Print top 20 time-consuming functions
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)
        
        # Filter and display relevant lines
        lines = s.getvalue().split('\n')
        for line in lines:
            # Show lines related to our code or network calls
            if any(keyword in line.lower() for keyword in [
                'review_app', 'databricks', 'mlflow', 'fetch', 'http', 
                'request', 'socket', 'ssl', 'proxy', 'update', 'schema'
            ]):
                print(line)


async def test_single_creation():
    """Test a single schema creation with profiling."""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get manifest to find review app ID
        print("Getting review app from manifest...")
        response = await client.get(f"{base_url}/api/manifest")
        if response.status_code != 200:
            print(f"Failed to get manifest: {response.text}")
            return
            
        manifest = response.json()
        review_app_id = manifest.get('config', {}).get('review_app_id')
        
        if not review_app_id:
            print("No review app configured in manifest")
            return
            
        print(f"Found review app: {review_app_id}")
        
        # Create schema with profiling
        schema_data = {
            "name": f"perf_test_{int(time.time())}",
            "type": "FEEDBACK",
            "title": "Performance Test",
            "instruction": "Testing performance",
            "numeric": {"min_value": 1, "max_value": 5}
        }
        
        print(f"\nCreating schema: {schema_data['name']}")
        
        with profile_block("Schema Creation"):
            response = await client.post(
                f"{base_url}/api/review-apps/{review_app_id}/schemas",
                json=schema_data
            )
            
            if response.status_code == 200:
                print(f"✅ Schema created successfully")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")


async def test_multiple_creations():
    """Test multiple schema creations to see caching effect."""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get manifest to find review app ID
        response = await client.get(f"{base_url}/api/manifest")
        manifest = response.json()
        review_app_id = manifest.get('config', {}).get('review_app_id')
        
        if not review_app_id:
            print("No review app configured")
            return
        
        print(f"\n{'=' * 60}")
        print("Testing 3 consecutive schema creations")
        print(f"{'=' * 60}")
        
        for i in range(3):
            schema_data = {
                "name": f"perf_test_{int(time.time())}_{i}",
                "type": "FEEDBACK",
                "title": f"Test #{i+1}",
                "instruction": "Testing",
                "numeric": {"min_value": 1, "max_value": 5}
            }
            
            print(f"\n🔄 Creation #{i+1}: {schema_data['name']}")
            
            start = time.time()
            response = await client.post(
                f"{base_url}/api/review-apps/{review_app_id}/schemas",
                json=schema_data
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                print(f"   ✓ Created in {elapsed:.1f}ms")
            else:
                print(f"   ✗ Failed in {elapsed:.1f}ms")
            
            # Small delay between requests
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    print("🔬 Schema Creation Performance Profiling")
    print("=" * 60)
    
    # Test single creation with detailed profiling
    asyncio.run(test_single_creation())
    
    # Test multiple creations
    asyncio.run(test_multiple_creations())
    
    print("\n" + "=" * 60)
    print("Profiling complete!")
    print("\nKey insights to look for:")
    print("1. Time spent in HTTP requests (fetch_databricks, http_request)")
    print("2. Time spent in MLflow SDK calls")
    print("3. Time spent in authentication (get_databricks_host_creds)")
    print("4. Socket/SSL overhead")
    print("=" * 60)