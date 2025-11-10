"""Distributed log storage implementation"""
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class LogEntry:
    term: int
    index: int
    command: str
    timestamp: float
    committed: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LogEntry':
        return cls(**data)


class DistributedLog:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.entries: List[LogEntry] = []
        self.commit_index = 0
        self.last_applied = 0
        
    def append_entry(self, term: int, command: str) -> LogEntry:
        """Append new entry to log"""
        entry = LogEntry(
            term=term,
            index=len(self.entries) + 1,
            command=command,
            timestamp=time.time()
        )
        self.entries.append(entry)
        return entry
        
    def get_entry(self, index: int) -> Optional[LogEntry]:
        """Get entry by index"""
        if 1 <= index <= len(self.entries):
            return self.entries[index - 1]
        return None
        
    def get_entries_from(self, start_index: int) -> List[LogEntry]:
        """Get entries starting from index"""
        if start_index <= 0:
            return self.entries.copy()
        return self.entries[start_index - 1:]
        
    def commit_entries_up_to(self, index: int):
        """Mark entries as committed up to index"""
        self.commit_index = min(index, len(self.entries))
        
        for i in range(self.last_applied, self.commit_index):
            if i < len(self.entries):
                self.entries[i].committed = True
                
        self.last_applied = self.commit_index
        
    def get_last_log_info(self) -> tuple[int, int]:
        """Get last log index and term"""
        if not self.entries:
            return 0, 0
        last_entry = self.entries[-1]
        return last_entry.index, last_entry.term
        
    def truncate_from(self, index: int):
        """Remove entries from index onwards"""
        if index <= len(self.entries):
            self.entries = self.entries[:index - 1]
            self.commit_index = min(self.commit_index, len(self.entries))
            self.last_applied = min(self.last_applied, len(self.entries))
            
    def is_up_to_date(self, last_log_index: int, last_log_term: int) -> bool:
        """Check if this log is more up-to-date than given parameters"""
        our_last_index, our_last_term = self.get_last_log_info()
        
        if our_last_term != last_log_term:
            return our_last_term > last_log_term
        return our_last_index >= last_log_index
        
    def get_committed_entries(self) -> List[LogEntry]:
        """Get all committed entries"""
        return [entry for entry in self.entries if entry.committed]
        
    def serialize(self) -> str:
        """Serialize log to JSON"""
        data = {
            'node_id': self.node_id,
            'entries': [entry.to_dict() for entry in self.entries],
            'commit_index': self.commit_index,
            'last_applied': self.last_applied
        }
        return json.dumps(data)
        
    @classmethod
    def deserialize(cls, data: str) -> 'DistributedLog':
        """Deserialize log from JSON"""
        parsed = json.loads(data)
        log = cls(parsed['node_id'])
        log.entries = [LogEntry.from_dict(entry) for entry in parsed['entries']]
        log.commit_index = parsed['commit_index']
        log.last_applied = parsed['last_applied']
        return log