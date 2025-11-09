"""Main entry point for clustering node"""
import asyncio
import os
import sys
from src.core.node import Node


async def main():
    """Main function to start a cluster node"""
    # Get node configuration from environment
    node_id = int(os.getenv('NODE_ID', '1'))
    node_port = int(os.getenv('NODE_PORT', '8000'))
    
    print(f"Starting node {node_id} on port {node_port}")
    
    # Create and start node
    node = Node(node_id, node_port)
    await node.start()
    
    print(f"Node {node_id} started successfully on port {node_port}")
    
    # No separate health monitoring needed
    
    # Wait for all nodes to start up
    print(f"Node {node_id}: Waiting for cluster to initialize...")
    await asyncio.sleep(3)
    
    # Discover peers multiple times to ensure all nodes are found
    for attempt in range(3):
        await node.discover_peers()
        if len(node.peers) >= 2:  # Expecting 2 other nodes in 3-node cluster
            break
        await asyncio.sleep(2)
    
    # Only node 1 starts the election to prevent split votes
    if node.leader_id is None and node.node_id == 1:
        print(f"Node {node_id}: Starting election as lowest node ID")
        await node.start_election()
    else:
        print(f"Node {node_id}: Waiting for leader election...")
    
    try:
        # Main loop with integrated heartbeat handling
        while True:
            # If this node is the leader, send heartbeats
            if node.status.value == 'leader':
                print(f"Node {node_id}: Sending heartbeats as leader")
                await node.send_heartbeats()
            
            # Wait before next iteration
            await asyncio.sleep(2)
            
    except KeyboardInterrupt:
        print(f"Shutting down node {node_id}")


if __name__ == "__main__":
    asyncio.run(main())