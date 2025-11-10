"""Authentication and authorization"""
import hashlib
import secrets
import time
from typing import Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class NodeCredentials:
    node_id: int
    token: str
    roles: Set[str]
    created_at: float


class AuthManager:
    def __init__(self):
        self.node_credentials: Dict[int, NodeCredentials] = {}
        self.valid_roles = {"leader", "follower", "admin", "readonly"}
        
    def generate_node_token(self, node_id: int, roles: Set[str] = None) -> str:
        """Generate authentication token for node"""
        if roles is None:
            roles = {"follower"}
            
        # Validate roles
        if not roles.issubset(self.valid_roles):
            raise ValueError(f"Invalid roles: {roles - self.valid_roles}")
            
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Store credentials
        self.node_credentials[node_id] = NodeCredentials(
            node_id=node_id,
            token=token,
            roles=roles,
            created_at=time.time()
        )
        
        return token
        
    def verify_token(self, node_id: int, token: str) -> bool:
        """Verify node authentication token"""
        creds = self.node_credentials.get(node_id)
        if not creds:
            return False
            
        return creds.token == token
        
    def has_permission(self, node_id: int, required_role: str) -> bool:
        """Check if node has required permission"""
        creds = self.node_credentials.get(node_id)
        if not creds:
            return False
            
        return required_role in creds.roles
        
    def promote_to_leader(self, node_id: int) -> bool:
        """Promote node to leader role"""
        creds = self.node_credentials.get(node_id)
        if not creds:
            return False
            
        creds.roles.add("leader")
        return True
        
    def demote_from_leader(self, node_id: int) -> bool:
        """Remove leader role from node"""
        creds = self.node_credentials.get(node_id)
        if not creds:
            return False
            
        creds.roles.discard("leader")
        return True
        
    def revoke_token(self, node_id: int) -> bool:
        """Revoke node authentication token"""
        return self.node_credentials.pop(node_id, None) is not None