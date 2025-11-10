"""REST API for cluster management"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Optional
import time


class NodeStatus(BaseModel):
    node_id: int
    status: str
    leader_id: Optional[int]
    uptime: float
    last_heartbeat: float


class ClusterInfo(BaseModel):
    total_nodes: int
    healthy_nodes: int
    leader_id: Optional[int]
    cluster_status: str


class MetricsResponse(BaseModel):
    node_id: int
    timestamp: float
    cpu_percent: float
    memory_percent: float
    active_connections: int


class ClusterAPI:
    def __init__(self, node_manager):
        self.app = FastAPI(title="Cluster Management API", version="1.0.0")
        self.node_manager = node_manager
        self.security = HTTPBearer()
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/api/v1/health")
        async def health_check():
            """Basic health check endpoint"""
            return {"status": "healthy", "timestamp": time.time()}
            
        @self.app.get("/api/v1/cluster/status", response_model=ClusterInfo)
        async def get_cluster_status():
            """Get overall cluster status"""
            nodes = self.node_manager.get_all_nodes()
            healthy_count = len([n for n in nodes if n.get('status') == 'healthy'])
            
            leader_id = None
            for node in nodes:
                if node.get('is_leader'):
                    leader_id = node.get('node_id')
                    break
                    
            return ClusterInfo(
                total_nodes=len(nodes),
                healthy_nodes=healthy_count,
                leader_id=leader_id,
                cluster_status="healthy" if healthy_count > len(nodes) // 2 else "degraded"
            )
            
        @self.app.get("/api/v1/nodes", response_model=List[NodeStatus])
        async def get_all_nodes():
            """Get status of all nodes"""
            nodes = self.node_manager.get_all_nodes()
            return [
                NodeStatus(
                    node_id=node['node_id'],
                    status=node['status'],
                    leader_id=node.get('leader_id'),
                    uptime=node.get('uptime', 0),
                    last_heartbeat=node.get('last_heartbeat', 0)
                )
                for node in nodes
            ]
            
        @self.app.get("/api/v1/nodes/{node_id}", response_model=NodeStatus)
        async def get_node_status(node_id: int):
            """Get status of specific node"""
            node = self.node_manager.get_node(node_id)
            if not node:
                raise HTTPException(status_code=404, detail="Node not found")
                
            return NodeStatus(
                node_id=node['node_id'],
                status=node['status'],
                leader_id=node.get('leader_id'),
                uptime=node.get('uptime', 0),
                last_heartbeat=node.get('last_heartbeat', 0)
            )
            
        @self.app.get("/api/v1/nodes/{node_id}/metrics", response_model=MetricsResponse)
        async def get_node_metrics(node_id: int):
            """Get metrics for specific node"""
            metrics = self.node_manager.get_node_metrics(node_id)
            if not metrics:
                raise HTTPException(status_code=404, detail="Node metrics not found")
                
            return MetricsResponse(**metrics)
            
        @self.app.post("/api/v1/cluster/election")
        async def trigger_election(credentials: HTTPAuthorizationCredentials = Depends(self.security)):
            """Trigger leader election"""
            # Verify admin permissions
            if not self._verify_admin_token(credentials.credentials):
                raise HTTPException(status_code=403, detail="Admin access required")
                
            success = self.node_manager.trigger_election()
            if not success:
                raise HTTPException(status_code=500, detail="Failed to trigger election")
                
            return {"message": "Election triggered successfully"}
            
        @self.app.post("/api/v1/nodes/{node_id}/restart")
        async def restart_node(node_id: int, credentials: HTTPAuthorizationCredentials = Depends(self.security)):
            """Restart specific node"""
            if not self._verify_admin_token(credentials.credentials):
                raise HTTPException(status_code=403, detail="Admin access required")
                
            success = self.node_manager.restart_node(node_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to restart node")
                
            return {"message": f"Node {node_id} restart initiated"}
            
    def _verify_admin_token(self, token: str) -> bool:
        """Verify admin authentication token"""
        # Simplified token verification
        return token == "admin-token-placeholder"