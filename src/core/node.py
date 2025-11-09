"""Node implementation for clustering system"""
import asyncio
import os
from enum import Enum
from typing import Dict, List, Optional
import aiohttp
from pydantic import BaseModel


class NodeStatus(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class NodeInfo(BaseModel):
    node_id: int
    host: str
    port: int
    status: NodeStatus = NodeStatus.FOLLOWER


class Node:
    def __init__(self, node_id: int, port: int = 8000):
        self.node_id = node_id
        self.port = port
        self.status = NodeStatus.FOLLOWER
        self.peers: Dict[int, NodeInfo] = {}
        self.leader_id: Optional[int] = None
        self.app = None
        
    async def start(self):
        """Start the node server"""
        app = aiohttp.web.Application()
        app.router.add_get('/health', self.health_check)
        app.router.add_post('/vote', self.handle_vote)
        app.router.add_post('/heartbeat', self.handle_heartbeat)
        
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        # Discover peers
        await self.discover_peers()
        
    async def health_check(self, request):
        """Health check endpoint"""
        return aiohttp.web.json_response({
            'node_id': self.node_id,
            'status': self.status.value,
            'leader_id': self.leader_id
        })
    
    async def handle_vote(self, request):
        """Handle vote requests"""
        data = await request.json()
        candidate_id = data.get('candidate_id')
        
        # Simple vote logic - vote for first candidate
        if self.leader_id is None:
            self.leader_id = candidate_id
            return aiohttp.web.json_response({'vote_granted': True})
        
        return aiohttp.web.json_response({'vote_granted': False})
    
    async def handle_heartbeat(self, request):
        """Handle heartbeat from leader"""
        data = await request.json()
        leader_id = data.get('leader_id')
        
        if leader_id:
            self.leader_id = leader_id
            self.status = NodeStatus.FOLLOWER
            
        return aiohttp.web.json_response({'success': True})
    
    async def discover_peers(self):
        """Discover other nodes in cluster"""
        cluster_nodes = os.getenv('CLUSTER_NODES', '').split(',')
        
        for node_addr in cluster_nodes:
            if not node_addr.strip():
                continue
                
            host, port = node_addr.strip().split(':')
            port = int(port)
            
            # Skip self
            if port == self.port:
                continue
                
            # Try to connect to peer
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://{host}:{port}/health', timeout=2) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            peer_id = data['node_id']
                            self.peers[peer_id] = NodeInfo(
                                node_id=peer_id,
                                host=host,
                                port=port
                            )
            except:
                pass  # Peer not available yet
    
    async def start_election(self):
        """Start leader election"""
        self.status = NodeStatus.CANDIDATE
        votes = 1  # Vote for self
        
        for peer in self.peers.values():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f'http://{peer.host}:{peer.port}/vote',
                        json={'candidate_id': self.node_id},
                        timeout=2
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('vote_granted'):
                                votes += 1
            except:
                pass
        
        # Become leader if majority votes
        if votes > len(self.peers) // 2:
            self.status = NodeStatus.LEADER
            self.leader_id = self.node_id
            await self.send_heartbeats()
    
    async def send_heartbeats(self):
        """Send heartbeats to followers"""
        if self.status != NodeStatus.LEADER:
            return
            
        for peer in self.peers.values():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f'http://{peer.host}:{peer.port}/heartbeat',
                        json={'leader_id': self.node_id},
                        timeout=2
                    ) as resp:
                        pass
            except:
                pass