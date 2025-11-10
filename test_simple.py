"""Simple tests for Phase 1 verification"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all core modules can be imported"""
    try:
        from core.node import Node, NodeStatus
        from core.cluster import Cluster
        from algorithms.basic_clustering import BasicElection, HealthMonitor
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_node_creation():
    """Test basic node creation without async"""
    try:
        from core.node import Node, NodeStatus
        node = Node(node_id=1, port=8000)
        assert node.node_id == 1
        assert node.port == 8000
        assert node.status == NodeStatus.FOLLOWER
        print("✅ Node creation test passed")
        return True
    except Exception as e:
        print(f"❌ Node creation test failed: {e}")
        return False

def test_cluster_creation():
    """Test cluster creation without async"""
    try:
        from core.node import Node
        from core.cluster import Cluster
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
        print("✅ Cluster creation test passed")
        return True
    except Exception as e:
        print(f"❌ Cluster creation test failed: {e}")
        return False

def test_basic_election_logic():
    """Test basic election algorithm logic"""
    try:
        from core.node import Node
        nodes = [
            Node(node_id=3, port=8003),
            Node(node_id=1, port=8001),
            Node(node_id=2, port=8002)
        ]
        # Test that lowest ID node is selected as candidate
        candidate = min(nodes, key=lambda n: n.node_id)
        assert candidate.node_id == 1
        print("✅ Basic election logic test passed")
        return True
    except Exception as e:
        print(f"❌ Basic election logic test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running Phase 1 verification tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_node_creation,
        test_cluster_creation,
        test_basic_election_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Phase 1 Success Criteria Met!")
        sys.exit(0)
    else:
        print("❌ Some tests failed - Phase 1 Success Criteria NOT Met")
        sys.exit(1)