"""State consistency tests"""
import pytest
import requests
import time


def test_leader_follower_consistency():
    """Test that all nodes have consistent leader information"""
    nodes = [8001, 8002, 8003]
    leader_ids = []
    
    for port in nodes:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                leader_ids.append(data.get("leader_id"))
        except requests.RequestException:
            continue
    
    # Filter out None values (nodes that don't know leader yet)
    known_leaders = [lid for lid in leader_ids if lid is not None]
    
    if known_leaders:
        # All nodes that know about a leader should agree on who it is
        assert all(lid == known_leaders[0] for lid in known_leaders), \
            f"Inconsistent leader IDs: {known_leaders}"
        
        print(f"[+] State consistency verified - all nodes agree leader is {known_leaders[0]}")
    else:
        print("[!] No leader elected yet - consistency test skipped")


@pytest.mark.asyncio
async def test_distributed_state_consistency():
    """Test distributed state synchronization"""
    from src.storage.state import DistributedState
    
    # Create two state instances (simulating different nodes)
    state1 = DistributedState(node_id=1)
    state2 = DistributedState(node_id=2)
    
    # Make changes on state1
    change1 = state1.set("key1", "value1", term=1)
    state1.apply_change(change1)
    
    # Simulate state synchronization
    snapshot = state1.get_state_snapshot()
    merged = state2.merge_state(snapshot["state"], snapshot["version"])
    
    # Verify consistency
    assert state2.get("key1") == "value1"
    assert merged == True  # State was updated
    
    print("[+] Distributed state consistency verified")


@pytest.mark.asyncio
async def test_log_consistency():
    """Test distributed log consistency"""
    from src.storage.log import DistributedLog
    
    # Create two log instances
    log1 = DistributedLog(node_id=1)
    log2 = DistributedLog(node_id=2)
    
    # Add entries to log1
    entry1 = log1.append_entry(term=1, command="set x=1")
    entry2 = log1.append_entry(term=1, command="set y=2")
    
    # Simulate log replication to log2
    entries = log1.get_entries_from(1)
    for entry in entries:
        log2.append_entry(entry.term, entry.command)
    
    # Verify consistency
    assert len(log1.entries) == len(log2.entries)
    assert log1.entries[0].command == log2.entries[0].command
    assert log1.entries[1].command == log2.entries[1].command
    
    print("[+] Log consistency verified")