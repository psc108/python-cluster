"""Performance metrics collection"""
import time
import psutil
from typing import Dict, List
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge, generate_latest


@dataclass
class NodeMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    leader_elections: int
    heartbeats_sent: int
    heartbeats_received: int


class MetricsCollector:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.metrics_history: List[NodeMetrics] = []
        
        # Prometheus metrics with unique names per node
        self.cpu_usage = Gauge(f'node_{node_id}_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge(f'node_{node_id}_memory_usage_percent', 'Memory usage percentage')
        self.heartbeat_counter = Counter(f'node_{node_id}_heartbeats_total', 'Total heartbeats', ['type'])
        self.election_counter = Counter(f'node_{node_id}_elections_total', 'Total elections')
        self.request_duration = Histogram(f'node_{node_id}_request_duration_seconds', 'Request duration', ['endpoint'])
        
        # Internal counters
        self.leader_elections = 0
        self.heartbeats_sent = 0
        self.heartbeats_received = 0
        
    def collect_system_metrics(self) -> NodeMetrics:
        """Collect current system metrics"""
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Count active connections
        connections = len(psutil.net_connections())
        
        metrics = NodeMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk.percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            active_connections=connections,
            leader_elections=self.leader_elections,
            heartbeats_sent=self.heartbeats_sent,
            heartbeats_received=self.heartbeats_received
        )
        
        # Update Prometheus metrics
        self.cpu_usage.set(cpu_percent)
        self.memory_usage.set(memory.percent)
        
        # Store in history
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
            
        return metrics
        
    def record_heartbeat_sent(self):
        """Record heartbeat sent"""
        self.heartbeats_sent += 1
        self.heartbeat_counter.labels(type='sent').inc()
        
    def record_heartbeat_received(self):
        """Record heartbeat received"""
        self.heartbeats_received += 1
        self.heartbeat_counter.labels(type='received').inc()
        
    def record_election(self):
        """Record leader election"""
        self.leader_elections += 1
        self.election_counter.inc()
        
    def record_leader_election(self, won: bool):
        """Record leader election result"""
        self.leader_elections += 1
        self.election_counter.inc()
        
    def record_vote_request(self):
        """Record vote request received"""
        # This can be tracked as part of election metrics
        pass
        
    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        return generate_latest().decode('utf-8')
        
    def get_recent_metrics(self, count: int = 10) -> List[Dict]:
        """Get recent metrics as dictionaries"""
        recent = self.metrics_history[-count:] if self.metrics_history else []
        return [asdict(metric) for metric in recent]
        
    def get_average_metrics(self, minutes: int = 5) -> Dict:
        """Get average metrics over time period"""
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
            
        return {
            'avg_cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            'avg_memory_percent': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            'avg_active_connections': sum(m.active_connections for m in recent_metrics) / len(recent_metrics),
            'total_heartbeats_sent': recent_metrics[-1].heartbeats_sent - recent_metrics[0].heartbeats_sent,
            'total_heartbeats_received': recent_metrics[-1].heartbeats_received - recent_metrics[0].heartbeats_received,
        }