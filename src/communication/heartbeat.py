"""Enhanced heartbeat system for node health monitoring"""
import asyncio
import time
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class NodeHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class HeartbeatInfo:
    node_id: int
    timestamp: float
    term: int
    leader_id: Optional[int]
    load_avg: float = 0.0
    memory_usage: float = 0.0


class HeartbeatMonitor:
    def __init__(self, node_id: int, heartbeat_interval: float = 1.0):
        self.node_id = node_id
        self.heartbeat_interval = heartbeat_interval
        self.failure_threshold = 3.0  # seconds
        self.degraded_threshold = 2.0  # seconds
        
        self.peer_heartbeats: Dict[int, HeartbeatInfo] = {}
        self.health_status: Dict[int, NodeHealth] = {}
        self.failure_callbacks: List[Callable] = []
        self.recovery_callbacks: List[Callable] = []
        
        self.monitoring = False
        
    def register_failure_callback(self, callback: Callable):
        """Register callback for node failure detection"""
        self.failure_callbacks.append(callback)
        
    def register_recovery_callback(self, callback: Callable):
        """Register callback for node recovery detection"""
        self.recovery_callbacks.append(callback)
        
    async def start_monitoring(self):
        """Start heartbeat monitoring"""
        self.monitoring = True
        
        # Start monitoring loop
        asyncio.create_task(self._monitor_loop())
        
    def stop_monitoring(self):
        """Stop heartbeat monitoring"""
        self.monitoring = False
        
    async def record_heartbeat(self, heartbeat: HeartbeatInfo):
        """Record heartbeat from peer"""
        old_health = self.health_status.get(heartbeat.node_id, NodeHealth.UNKNOWN)
        
        self.peer_heartbeats[heartbeat.node_id] = heartbeat
        self.health_status[heartbeat.node_id] = NodeHealth.HEALTHY
        
        # Check for recovery
        if old_health in [NodeHealth.FAILED, NodeHealth.DEGRADED]:
            for callback in self.recovery_callbacks:
                await callback(heartbeat.node_id, old_health, NodeHealth.HEALTHY)
                
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            await self._check_peer_health()
            await asyncio.sleep(self.heartbeat_interval)
            
    async def _check_peer_health(self):
        """Check health of all peers"""
        current_time = time.time()
        
        for node_id, heartbeat in self.peer_heartbeats.items():
            time_since_heartbeat = current_time - heartbeat.timestamp
            old_health = self.health_status.get(node_id, NodeHealth.UNKNOWN)
            new_health = self._calculate_health(time_since_heartbeat)
            
            if new_health != old_health:
                self.health_status[node_id] = new_health
                
                # Trigger callbacks for health changes
                if new_health == NodeHealth.FAILED:
                    for callback in self.failure_callbacks:
                        await callback(node_id, old_health, new_health)
                elif old_health == NodeHealth.FAILED and new_health != NodeHealth.FAILED:
                    for callback in self.recovery_callbacks:
                        await callback(node_id, old_health, new_health)
                        
    def _calculate_health(self, time_since_heartbeat: float) -> NodeHealth:
        """Calculate node health based on heartbeat timing"""
        if time_since_heartbeat > self.failure_threshold:
            return NodeHealth.FAILED
        elif time_since_heartbeat > self.degraded_threshold:
            return NodeHealth.DEGRADED
        else:
            return NodeHealth.HEALTHY
            
    def get_healthy_peers(self) -> List[int]:
        """Get list of healthy peer node IDs"""
        return [
            node_id for node_id, health in self.health_status.items()
            if health == NodeHealth.HEALTHY
        ]
        
    def get_failed_peers(self) -> List[int]:
        """Get list of failed peer node IDs"""
        return [
            node_id for node_id, health in self.health_status.items()
            if health == NodeHealth.FAILED
        ]