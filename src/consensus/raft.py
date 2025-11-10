"""Raft consensus algorithm implementation"""
import asyncio
import time
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class RaftState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class LogEntry:
    term: int
    index: int
    command: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class RaftNode:
    def __init__(self, node_id: int, peers: List[int]):
        self.node_id = node_id
        self.peers = peers
        self.state = RaftState.FOLLOWER
        
        # Persistent state
        self.current_term = 0
        self.voted_for: Optional[int] = None
        self.log: List[LogEntry] = []
        
        # Volatile state
        self.commit_index = 0
        self.last_applied = 0
        
        # Leader state
        self.next_index: Dict[int, int] = {}
        self.match_index: Dict[int, int] = {}
        
        # Timing
        self.last_heartbeat = time.time()
        self.election_timeout = 5.0  # seconds
        self.heartbeat_interval = 1.0  # seconds
        
    def reset_election_timeout(self):
        """Reset election timeout"""
        self.last_heartbeat = time.time()
        
    def is_election_timeout(self) -> bool:
        """Check if election timeout has occurred"""
        return time.time() - self.last_heartbeat > self.election_timeout
        
    async def start_election(self):
        """Start leader election"""
        self.state = RaftState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.reset_election_timeout()
        
        votes = 1  # Vote for self
        
        # Request votes from peers
        for peer_id in self.peers:
            if await self.request_vote(peer_id):
                votes += 1
                
        # Become leader if majority
        if votes > len(self.peers) // 2:
            await self.become_leader()
        else:
            self.state = RaftState.FOLLOWER
            
    async def become_leader(self):
        """Become cluster leader"""
        self.state = RaftState.LEADER
        
        # Initialize leader state
        for peer_id in self.peers:
            self.next_index[peer_id] = len(self.log) + 1
            self.match_index[peer_id] = 0
            
        # Start sending heartbeats
        asyncio.create_task(self.send_heartbeats())
        
    async def request_vote(self, peer_id: int) -> bool:
        """Request vote from peer"""
        # Simplified - would make actual network call
        return True
        
    async def send_heartbeats(self):
        """Send heartbeats to followers"""
        while self.state == RaftState.LEADER:
            for peer_id in self.peers:
                await self.send_append_entries(peer_id)
            await asyncio.sleep(self.heartbeat_interval)
            
    async def send_append_entries(self, peer_id: int):
        """Send append entries (heartbeat) to peer"""
        # Simplified - would make actual network call
        pass
        
    def append_entry(self, command: str) -> bool:
        """Append entry to log (leader only)"""
        if self.state != RaftState.LEADER:
            return False
            
        entry = LogEntry(
            term=self.current_term,
            index=len(self.log) + 1,
            command=command
        )
        self.log.append(entry)
        return True