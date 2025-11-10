"""Distributed state management"""
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class StateChange:
    key: str
    value: Any
    timestamp: float
    term: int
    applied: bool = False


class DistributedState:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.state: Dict[str, Any] = {}
        self.pending_changes: List[StateChange] = []
        self.version = 0
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state"""
        return self.state.get(key, default)
        
    def set(self, key: str, value: Any, term: int) -> StateChange:
        """Create state change (not applied until committed)"""
        change = StateChange(
            key=key,
            value=value,
            timestamp=time.time(),
            term=term
        )
        self.pending_changes.append(change)
        return change
        
    def apply_change(self, change: StateChange):
        """Apply committed state change"""
        if not change.applied:
            self.state[change.key] = change.value
            change.applied = True
            self.version += 1
            
    def apply_changes_up_to_term(self, term: int):
        """Apply all pending changes up to given term"""
        for change in self.pending_changes:
            if change.term <= term and not change.applied:
                self.apply_change(change)
                
    def get_pending_changes(self) -> List[StateChange]:
        """Get all pending changes"""
        return [change for change in self.pending_changes if not change.applied]
        
    def rollback_changes_from_term(self, term: int):
        """Rollback pending changes from given term"""
        self.pending_changes = [
            change for change in self.pending_changes
            if change.term < term or change.applied
        ]
        
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get current state snapshot"""
        return {
            'node_id': self.node_id,
            'state': self.state.copy(),
            'version': self.version,
            'timestamp': time.time()
        }
        
    def merge_state(self, other_state: Dict[str, Any], other_version: int):
        """Merge state from another node (conflict resolution)"""
        if other_version > self.version:
            # Other node has newer state, adopt it
            self.state.update(other_state)
            self.version = other_version
            return True
        return False
        
    def serialize(self) -> str:
        """Serialize state to JSON"""
        data = {
            'node_id': self.node_id,
            'state': self.state,
            'version': self.version,
            'pending_changes': [
                {
                    'key': change.key,
                    'value': change.value,
                    'timestamp': change.timestamp,
                    'term': change.term,
                    'applied': change.applied
                }
                for change in self.pending_changes
            ]
        }
        return json.dumps(data, default=str)
        
    @classmethod
    def deserialize(cls, data: str) -> 'DistributedState':
        """Deserialize state from JSON"""
        parsed = json.loads(data)
        state = cls(parsed['node_id'])
        state.state = parsed['state']
        state.version = parsed['version']
        
        state.pending_changes = [
            StateChange(
                key=change['key'],
                value=change['value'],
                timestamp=change['timestamp'],
                term=change['term'],
                applied=change['applied']
            )
            for change in parsed['pending_changes']
        ]
        
        return state