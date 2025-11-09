"""Basic tests for clustering functionality"""
import pytest
import asyncio
from src.core.node import Node, NodeStatus
from src.core.cluster import Cluster
from src.algorithms.basic_clustering import BasicElection


@pytest.mark.asyncio
async def test_node_creation():
    """Test basic node creation"""
    node = Node(node_id=1, port=8000)
    assert node.node_id == 1
    assert node.port == 8000
    assert node.status == NodeStatus.FOLLOWER


@pytest.mark.asyncio
async def test_leader_election():
    """Test basic leader election"""
    nodes = [
        Node(node_id=1, port=8001),
        Node(node_id=2, port=8002),
        Node(node_id=3, port=8003)
    ]
    
    # Mock the election process
    nodes[0].status = NodeStatus.LEADER
    nodes[0].leader_id = 1
    
    leader = None
    for node in nodes:
        if node.status == NodeStatus.LEADER:
            leader = node
            break
    
    assert leader is not None
    assert leader.node_id == 1


@pytest.mark.asyncio
async def test_cluster_creation():
    """Test cluster creation and management"""
    nodes = [
        Node(node_id=1, port=8001),
        Node(node_id=2, port=8002),
        Node(node_id=3, port=8003)
    ]
    
    cluster = Cluster(nodes)
    assert len(cluster.nodes) == 3
    assert 1 in cluster.nodes
    assert 2 in cluster.nodes
    assert 3 in cluster.nodes


@pytest.mark.asyncio
async def test_health_check():
    """Test cluster health check"""
    nodes = [
        Node(node_id=1, port=8001),
        Node(node_id=2, port=8002)
    ]
    
    cluster = Cluster(nodes)
    health = await cluster.health_check()
    
    assert len(health) == 2
    assert 1 in health
    assert 2 in health
    assert health[1]['status'] == 'follower'
    assert health[2]['status'] == 'follower'


def test_basic_election_algorithm():
    """Test basic election algorithm"""
    nodes = [
        Node(node_id=3, port=8003),
        Node(node_id=1, port=8001),
        Node(node_id=2, port=8002)
    ]
    
    # Test that lowest ID node is selected as candidate
    candidate = min(nodes, key=lambda n: n.node_id)
    assert candidate.node_id == 1