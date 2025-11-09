"""Cluster management implementation"""
import asyncio
from typing import Dict, List
from .node import Node, NodeStatus


class Cluster:
    def __init__(self, nodes: List[Node]):
        self.nodes = {node.node_id: node for node in nodes}
        self.leader_id = None
        
    async def start_all_nodes(self):
        """Start all nodes in the cluster"""
        tasks = [node.start() for node in self.nodes.values()]
        await asyncio.gather(*tasks)
        
        # Wait for peer discovery
        await asyncio.sleep(2)
        
        # Start election process
        await self.elect_leader()
    
    async def elect_leader(self):
        """Elect a leader among nodes"""
        # Simple election - first node starts election
        first_node = min(self.nodes.values(), key=lambda n: n.node_id)
        await first_node.start_election()
        
        # Wait for election to complete
        await asyncio.sleep(1)
        
        # Find the leader
        for node in self.nodes.values():
            if node.status == NodeStatus.LEADER:
                self.leader_id = node.node_id
                break
    
    def get_leader(self) -> Node:
        """Get the current leader node"""
        if self.leader_id and self.leader_id in self.nodes:
            return self.nodes[self.leader_id]
        return None
    
    def get_followers(self) -> List[Node]:
        """Get all follower nodes"""
        return [
            node for node in self.nodes.values() 
            if node.status == NodeStatus.FOLLOWER
        ]
    
    async def health_check(self) -> Dict:
        """Check health of all nodes"""
        health_status = {}
        
        for node_id, node in self.nodes.items():
            health_status[node_id] = {
                'status': node.status.value,
                'is_leader': node.status == NodeStatus.LEADER,
                'peer_count': len(node.peers)
            }
        
        return health_status