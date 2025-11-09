"""Node implementation for clustering system"""
import asyncio
import os
import time
from enum import Enum
from typing import Dict, List, Optional
import aiohttp
import aiohttp.web
from pydantic import BaseModel

# Phase 2 imports
try:
    from ..consensus.raft import RaftNode, RaftState
    from ..communication.messaging import MessageQueue, Message, MessageType
    from ..communication.heartbeat import HeartbeatMonitor, HeartbeatInfo
    from ..storage.log import DistributedLog
    from ..storage.state import DistributedState
except ImportError:
    # Fallback for testing
    pass


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
        self.current_term = 0
        self.voted_for: Optional[int] = None
        self.app = None
        
        # Phase 2 components
        self.raft_node: Optional['RaftNode'] = None
        self.message_queue: Optional['MessageQueue'] = None
        self.heartbeat_monitor: Optional['HeartbeatMonitor'] = None
        self.distributed_log: Optional['DistributedLog'] = None
        self.distributed_state: Optional['DistributedState'] = None
        
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
        
        # Initialize Phase 2 components
        await self.initialize_phase2_components()
        
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
        candidate_term = data.get('term', 0)
        
        # Update term if candidate has higher term
        if candidate_term > self.current_term:
            self.current_term = candidate_term
            self.voted_for = None
            self.status = NodeStatus.FOLLOWER
            self.leader_id = None
        
        # Grant vote if haven't voted in this term and candidate term >= current term
        vote_granted = (candidate_term >= self.current_term and 
                       (self.voted_for is None or self.voted_for == candidate_id))
        
        if vote_granted:
            self.voted_for = candidate_id
            
        return aiohttp.web.json_response({
            'vote_granted': vote_granted,
            'term': self.current_term
        })
    
    async def handle_heartbeat(self, request):
        """Handle heartbeat from leader"""
        data = await request.json()
        leader_id = data.get('leader_id')
        leader_term = data.get('term', 0)
        
        # Accept heartbeat if term is current or higher
        if leader_term >= self.current_term:
            self.current_term = leader_term
            self.leader_id = leader_id
            self.status = NodeStatus.FOLLOWER
            self.voted_for = None
            print(f"Node {self.node_id}: Received heartbeat from leader {leader_id}, term {leader_term}")
            
        return aiohttp.web.json_response({
            'success': leader_term >= self.current_term,
            'term': self.current_term
        })
    
    async def discover_peers(self):
        """Discover other nodes in cluster"""
        cluster_nodes = os.getenv('CLUSTER_NODES', '').split(',')
        discovered = 0
        
        for node_addr in cluster_nodes:
            if not node_addr.strip():
                continue
                
            host, port = node_addr.strip().split(':')
            port = int(port)
            
            # Skip self by comparing hostname
            if host == f'cluster-node-{self.node_id}':
                continue
                
            # Try to connect to peer
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://{host}:{port}/health', timeout=2) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            peer_id = data['node_id']
                            if peer_id not in self.peers:
                                self.peers[peer_id] = NodeInfo(
                                    node_id=peer_id,
                                    host=host,
                                    port=port
                                )
                                discovered += 1
                                print(f"Node {self.node_id}: Discovered peer {peer_id} at {host}:{port}")
            except Exception as e:
                print(f"Node {self.node_id}: Failed to discover peer at {host}:{port}: {e}")
        
        print(f"Node {self.node_id}: Peer discovery complete, found {len(self.peers)} peers")
    
    async def start_election(self):
        """Start leader election"""
        # Only start election if no current leader
        if self.leader_id is not None:
            print(f"Node {self.node_id}: Election skipped, leader already exists: {self.leader_id}")
            return
        
        # Ensure peers are discovered first
        await self.discover_peers()
        print(f"Node {self.node_id}: Starting election, discovered {len(self.peers)} peers")
            
        self.current_term += 1
        self.status = NodeStatus.CANDIDATE
        self.voted_for = self.node_id
        votes = 1  # Vote for self
        
        for peer in self.peers.values():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f'http://{peer.host}:{peer.port}/vote',
                        json={'candidate_id': self.node_id, 'term': self.current_term},
                        timeout=2
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('vote_granted'):
                                votes += 1
                                print(f"Node {self.node_id}: Got vote from peer {peer.node_id}")
            except Exception as e:
                print(f"Node {self.node_id}: Failed to get vote from peer {peer.node_id}: {e}")
        
        # Become leader if majority votes (including self)
        total_nodes = len(self.peers) + 1
        print(f"Node {self.node_id}: Election result: {votes}/{total_nodes} votes")
        
        if votes > total_nodes // 2:
            self.status = NodeStatus.LEADER
            self.leader_id = self.node_id
            print(f"Node {self.node_id}: Became leader with {votes} votes")
        else:
            self.status = NodeStatus.FOLLOWER
            print(f"Node {self.node_id}: Election failed, becoming follower")
    

    async def send_heartbeats(self):
        """Send heartbeats to followers"""
        if self.status != NodeStatus.LEADER:
            return
        
        print(f"Node {self.node_id}: Sending heartbeats to {len(self.peers)} peers")
        for peer in self.peers.values():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f'http://{peer.host}:{peer.port}/heartbeat',
                        json={'leader_id': self.node_id, 'term': self.current_term},
                        timeout=2
                    ) as resp:
                        if resp.status == 200:
                            print(f"Node {self.node_id}: Heartbeat sent to peer {peer.node_id}")
            except Exception as e:
                print(f"Node {self.node_id}: Failed to send heartbeat to peer {peer.node_id}: {e}")
    
    async def initialize_phase2_components(self):
        """Initialize Phase 2 advanced components"""
        try:
            # Initialize distributed log
            self.distributed_log = DistributedLog(self.node_id)
            
            # Initialize distributed state
            self.distributed_state = DistributedState(self.node_id)
            
            # Initialize message queue
            self.message_queue = MessageQueue(self.node_id)
            
            # Initialize heartbeat monitor
            self.heartbeat_monitor = HeartbeatMonitor(self.node_id)
            
            # Initialize Raft node with peer IDs
            peer_ids = list(self.peers.keys())
            self.raft_node = RaftNode(self.node_id, peer_ids)
            
            print(f"Node {self.node_id}: Phase 2 components initialized")
            
        except Exception as e:
            print(f"Node {self.node_id}: Failed to initialize Phase 2 components: {e}")