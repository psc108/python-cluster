"""Phase 2 tests for advanced clustering features"""
import pytest
import asyncio
import time
from src.consensus.raft import RaftNode, RaftState, LogEntry
from src.communication.messaging import MessageQueue, Message, MessageType
from src.communication.heartbeat import HeartbeatMonitor, HeartbeatInfo, NodeHealth
from src.storage.log import DistributedLog
from src.storage.state import DistributedState, StateChange


@pytest.mark.asyncio
async def test_raft_node_creation():
    """Test Raft node creation"""
    node = RaftNode(node_id=1, peers=[2, 3])
    assert node.node_id == 1
    assert node.state == RaftState.FOLLOWER
    assert node.current_term == 0
    assert node.voted_for is None


@pytest.mark.asyncio
async def test_raft_election_timeout():
    """Test Raft election timeout"""
    node = RaftNode(node_id=1, peers=[2, 3])
    node.election_timeout = 0.1  # Short timeout for testing
    
    # Should not timeout initially
    assert not node.is_election_timeout()
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    assert node.is_election_timeout()


@pytest.mark.asyncio
async def test_message_queue():
    """Test message queue functionality"""
    queue = MessageQueue(node_id=1)
    
    message = Message(
        msg_id="test-1",
        msg_type=MessageType.HEARTBEAT,
        sender_id=1,
        receiver_id=2,
        term=1,
        data={"test": "data"}
    )
    
    # Test message creation
    assert message.sender_id == 1
    assert message.msg_type == MessageType.HEARTBEAT


@pytest.mark.asyncio
async def test_heartbeat_monitor():
    """Test heartbeat monitoring"""
    monitor = HeartbeatMonitor(node_id=1)
    
    # Record heartbeat
    heartbeat = HeartbeatInfo(
        node_id=2,
        timestamp=time.time(),
        term=1,
        leader_id=1
    )
    
    await monitor.record_heartbeat(heartbeat)
    assert monitor.health_status[2] == NodeHealth.HEALTHY


@pytest.mark.asyncio
async def test_distributed_log():
    """Test distributed log functionality"""
    log = DistributedLog(node_id=1)
    
    # Test append entry
    entry = log.append_entry(term=1, command="set x=1")
    assert entry.term == 1
    assert entry.index == 1
    assert entry.command == "set x=1"
    
    # Test get entry
    retrieved = log.get_entry(1)
    assert retrieved is not None
    assert retrieved.command == "set x=1"
    
    # Test commit
    log.commit_entries_up_to(1)
    assert log.commit_index == 1
    assert entry.committed


@pytest.mark.asyncio
async def test_distributed_state():
    """Test distributed state management"""
    state = DistributedState(node_id=1)
    
    # Test state change
    change = state.set("key1", "value1", term=1)
    assert change.key == "key1"
    assert change.value == "value1"
    assert not change.applied
    
    # Test apply change
    state.apply_change(change)
    assert state.get("key1") == "value1"
    assert change.applied
    assert state.version == 1


def test_log_serialization():
    """Test log serialization/deserialization"""
    log = DistributedLog(node_id=1)
    log.append_entry(term=1, command="test command")
    
    # Serialize
    serialized = log.serialize()
    assert isinstance(serialized, str)
    
    # Deserialize
    deserialized = DistributedLog.deserialize(serialized)
    assert deserialized.node_id == 1
    assert len(deserialized.entries) == 1
    assert deserialized.entries[0].command == "test command"


def test_state_serialization():
    """Test state serialization/deserialization"""
    state = DistributedState(node_id=1)
    change = state.set("test_key", "test_value", term=1)
    state.apply_change(change)
    
    # Serialize
    serialized = state.serialize()
    assert isinstance(serialized, str)
    
    # Deserialize
    deserialized = DistributedState.deserialize(serialized)
    assert deserialized.node_id == 1
    assert deserialized.get("test_key") == "test_value"
    assert deserialized.version == 1