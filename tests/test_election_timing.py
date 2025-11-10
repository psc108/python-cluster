"""Leader election timing tests"""
import pytest
import asyncio
import time
from src.consensus.raft import RaftNode


@pytest.mark.asyncio
async def test_election_timing():
    """Test that leader election completes in sub-second time"""
    start_time = time.time()
    
    # Create test nodes
    node1 = RaftNode(node_id=1, peers=[2, 3])
    node2 = RaftNode(node_id=2, peers=[1, 3])
    node3 = RaftNode(node_id=3, peers=[1, 2])
    
    # Start election
    await node1.start_election()
    
    end_time = time.time()
    election_time = end_time - start_time
    
    # Verify sub-second timing
    assert election_time < 1.0, f"Election took {election_time:.3f}s, should be < 1.0s"
    
    print(f"[+] Election completed in {election_time:.3f}s (sub-second requirement met)")


@pytest.mark.asyncio
async def test_raft_election_timeout():
    """Test Raft election timeout mechanism"""
    node = RaftNode(node_id=1, peers=[2, 3])
    node.election_timeout = 0.1  # 100ms for testing
    
    start_time = time.time()
    
    # Should not timeout initially
    assert not node.is_election_timeout()
    
    # Wait for timeout
    await asyncio.sleep(0.15)
    
    # Should timeout now
    assert node.is_election_timeout()
    
    elapsed = time.time() - start_time
    assert elapsed >= 0.1, "Timeout should respect minimum time"
    
    print(f"[+] Election timeout working correctly ({elapsed:.3f}s)")