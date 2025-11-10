#!/usr/bin/env python3
"""
Auto-scaler startup script
"""

import sys
import os
import asyncio

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from autoscaler import BasicAutoScaler

async def main():
    print("Starting Cluster Auto-Scaler...")
    
    # Check if dashboard is accessible
    autoscaler = BasicAutoScaler()
    
    try:
        policies = await autoscaler.load_policies()
        print(f"Connected to dashboard, found {len(policies)} scaling policies")
    except Exception as e:
        print(f"Failed to connect to dashboard: {e}")
        print("Make sure the cluster dashboard is running on http://localhost:8080")
        return
    
    print("Auto-scaler running (Press Ctrl+C to stop)")
    await autoscaler.run(interval_seconds=60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAuto-scaler stopped")