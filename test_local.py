"""Test clustering locally without Docker"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.node import Node
from core.cluster import Cluster

async def test_local_cluster():
    """Test cluster functionality locally"""
    print("Testing local cluster without Docker...")
    
    # Create 3 nodes on different ports
    nodes = [
        Node(node_id=1, port=8001),
        Node(node_id=2, port=8002),
        Node(node_id=3, port=8003)
    ]
    
    # Set up cluster environment
    os.environ['CLUSTER_NODES'] = 'localhost:8001,localhost:8002,localhost:8003'
    
    print("Starting nodes...")
    cluster = Cluster(nodes)
    
    try:
        # Start all nodes
        await cluster.start_all_nodes()
        
        print("✅ Cluster started successfully!")
        print("Nodes running on:")
        print("- Node 1: http://localhost:8001/health")
        print("- Node 2: http://localhost:8002/health") 
        print("- Node 3: http://localhost:8003/health")
        
        # Check cluster health
        health = await cluster.health_check()
        print("\n📊 Cluster Health:")
        for node_id, status in health.items():
            print(f"Node {node_id}: {status['status']} ({'Leader' if status['is_leader'] else 'Follower'})")
        
        print("\nPress Ctrl+C to stop...")
        await asyncio.sleep(3600)  # Keep running
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping cluster...")

if __name__ == "__main__":
    asyncio.run(test_local_cluster())