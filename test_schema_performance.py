#!/usr/bin/env python3
"""Test script to profile label schema creation performance."""

import asyncio
import json
import logging
import time
from typing import Dict, Any

import httpx
from pydantic import BaseModel

# Configure logging to see all profiling output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set specific loggers to INFO level
logging.getLogger('server.routers.review.label_schemas').setLevel(logging.INFO)
logging.getLogger('server.utils.review_apps_utils').setLevel(logging.INFO)
logging.getLogger('server.utils.proxy').setLevel(logging.INFO)

class LabelingSchema(BaseModel):
    """Schema for labeling configuration."""
    name: str
    type: str = "FEEDBACK"  # Must be FEEDBACK or EXPECTATION
    title: str
    instruction: str
    numeric: dict = None

async def test_schema_creation():
    """Test label schema creation and measure performance."""
    
    # Get review app from manifest
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get manifest to find review app ID
        print(f"🔍 Getting review app from manifest...")
        response = await client.get(f"{base_url}/api/manifest")
        
        if response.status_code != 200:
            print(f"❌ Failed to get manifest: {response.text}")
            return
            
        manifest = response.json()
        review_app_id = manifest.get('config', {}).get('review_app_id')
        
        if not review_app_id:
            print("❌ No review app configured in manifest")
            return
            
        print(f"✓ Found review app: {review_app_id}")
        # First, get current schemas to avoid conflicts
        print(f"\n📋 Getting current schemas for review app {review_app_id}...")
        response = await client.get(f"{base_url}/api/review-apps/{review_app_id}/schemas")
        if response.status_code == 200:
            existing_schemas = response.json()
            print(f"Found {len(existing_schemas)} existing schemas")
        
        # Create test schema with correct format
        test_schema = LabelingSchema(
            name=f"test_performance_{int(time.time())}",
            type="FEEDBACK",
            title="Performance Test Schema",
            instruction="Test schema for performance profiling",
            numeric={"min_value": 1, "max_value": 10}
        )
        
        print(f"\n🚀 Creating new schema: {test_schema.name}")
        print("=" * 60)
        
        # Measure API call time
        start_time = time.time()
        response = await client.post(
            f"{base_url}/api/review-apps/{review_app_id}/schemas",
            json=test_schema.dict()
        )
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            print(f"\n✅ Schema created successfully!")
            print(f"⏱️  Total API call time: {total_time:.1f}ms")
            print("\n📊 Check server logs for detailed timing breakdown:")
            print("   - get_review_app time")
            print("   - check_existing time")
            print("   - append_schema time")
            print("   - update_review_app time (MLflow API call)")
            print("\n💡 Look for lines with [SCHEMA CREATE], [DATABRICKS], and [MLFLOW GENAI] tags")
        else:
            print(f"\n❌ Failed to create schema: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Test multiple creations to see if there's caching benefit
        print("\n" + "=" * 60)
        print("📈 Testing multiple schema creations for caching analysis...")
        print("=" * 60)
        
        timings = []
        for i in range(3):
            test_schema = LabelingSchema(
                name=f"test_performance_{int(time.time())}_{i}",
                type="FEEDBACK",
                title=f"Test Schema #{i+1}",
                instruction=f"Test schema #{i+1} for performance profiling",
                numeric={"min_value": 1, "max_value": 5}
            )
            
            print(f"\n🔄 Creating schema #{i+1}: {test_schema.name}")
            start_time = time.time()
            response = await client.post(
                f"{base_url}/api/review-apps/{review_app_id}/schemas",
                json=test_schema.dict()
            )
            end_time = time.time()
            
            timing = (end_time - start_time) * 1000
            timings.append(timing)
            
            if response.status_code == 200:
                print(f"   ✓ Created in {timing:.1f}ms")
            else:
                print(f"   ✗ Failed: {response.status_code}")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
        
        if timings:
            avg_time = sum(timings) / len(timings)
            print(f"\n📊 Performance Summary:")
            print(f"   Average time: {avg_time:.1f}ms")
            print(f"   Min time: {min(timings):.1f}ms")
            print(f"   Max time: {max(timings):.1f}ms")
            print(f"   All timings: {[f'{t:.1f}ms' for t in timings]}")

if __name__ == "__main__":
    print("🔬 Label Schema Creation Performance Test")
    print("=" * 60)
    print("Make sure the development server is running (./watch.sh)")
    print("Watch the server logs for detailed profiling information")
    print("=" * 60)
    
    asyncio.run(test_schema_creation())