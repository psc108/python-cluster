"""Main entry point for clustering node"""
import asyncio
import os
import sys
from core.node import Node
from algorithms.basic_clustering import HealthMonitor


async def main():
    """Main function to start a cluster node"""
    # Get node configuration from environment
    node_id = int(os.getenv('NODE_ID', '1'))
    node_port = int(os.getenv('NODE_PORT', '8000'))
    
    print(f"Starting node {node_id} on port {node_port}")
    
    # Create and start node
    node = Node(node_id, node_port)
    await node.start()
    
    print(f"Node {node_id} started successfully")
    
    # Start health monitoring
    monitor = HealthMonitor([node])
    monitor_task = asyncio.create_task(monitor.start_monitoring())
    
    # Start election after a delay
    await asyncio.sleep(3)
    if node.leader_id is None:
        await node.start_election()
    
    try:
        # Keep the node running
        await monitor_task
    except KeyboardInterrupt:
        print(f"Shutting down node {node_id}")
        monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())