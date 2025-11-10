"""Phase 3 tests for production features"""
import pytest
import time
from src.security.auth import AuthManager
from src.security.tls import TLSManager
from src.monitoring.metrics import MetricsCollector
from src.monitoring.health import HealthMonitor, AlertLevel
from src.config.settings import ConfigManager


def test_auth_manager():
    """Test authentication manager"""
    auth = AuthManager()
    
    # Generate token
    token = auth.generate_node_token(1, {"follower", "admin"})
    assert isinstance(token, str)
    assert len(token) > 20
    
    # Verify token
    assert auth.verify_token(1, token) == True
    assert auth.verify_token(1, "invalid") == False
    
    # Check permissions
    assert auth.has_permission(1, "follower") == True
    assert auth.has_permission(1, "admin") == True
    assert auth.has_permission(1, "invalid_role") == False


def test_tls_manager():
    """Test TLS certificate management"""
    tls = TLSManager(node_id=1)
    
    # Generate certificate
    tls.generate_self_signed_cert()
    assert tls.private_key is not None
    assert tls.certificate is not None
    
    # Save cert files
    tls.save_cert_files()
    
    # Create SSL context
    server_context = tls.create_ssl_context(is_server=True)
    client_context = tls.create_ssl_context(is_server=False)
    
    assert server_context is not None
    assert client_context is not None


def test_metrics_collector():
    """Test metrics collection"""
    collector = MetricsCollector(node_id=1)
    
    # Collect metrics
    metrics = collector.collect_system_metrics()
    assert collector.node_id == 1
    assert metrics.timestamp > 0
    assert metrics.cpu_percent >= 0
    assert metrics.memory_percent >= 0
    
    # Record events
    collector.record_heartbeat_sent()
    collector.record_heartbeat_received()
    collector.record_election()
    
    assert collector.heartbeats_sent == 1
    assert collector.heartbeats_received == 1
    assert collector.leader_elections == 1


def test_health_monitor():
    """Test health monitoring"""
    monitor = HealthMonitor(node_id=1)
    
    # Test threshold checking
    monitor.check_metric_thresholds('cpu_percent', 90.0)  # Should trigger warning
    monitor.check_metric_thresholds('memory_percent', 98.0)  # Should trigger critical
    
    alerts = monitor.get_recent_alerts(1)
    assert len(alerts) == 2
    
    critical_alerts = monitor.get_critical_alerts()
    assert len(critical_alerts) == 1
    assert critical_alerts[0].level == AlertLevel.CRITICAL


def test_config_manager():
    """Test configuration management"""
    config = ConfigManager()
    
    # Test default values
    assert config.cluster.node_id >= 1
    assert config.security.enable_tls == True
    assert config.monitoring.enable_metrics == True
    
    # Test configuration update
    config.update_config('security', {'enable_tls': False})
    assert config.security.enable_tls == False
    
    # Test getting all config
    all_config = config.get_all_config()
    assert 'security' in all_config
    assert 'monitoring' in all_config
    assert 'cluster' in all_config
    assert 'api' in all_config


@pytest.mark.asyncio
async def test_security_integration():
    """Test security components integration"""
    auth = AuthManager()
    tls = TLSManager(node_id=1)
    
    # Generate credentials
    token = auth.generate_node_token(1, {"leader"})
    
    # Generate TLS cert
    tls.generate_self_signed_cert()
    
    # Verify both work together
    assert auth.verify_token(1, token) == True
    assert tls.certificate is not None
    
    # Test role promotion
    assert auth.promote_to_leader(1) == True
    assert auth.has_permission(1, "leader") == True


def test_monitoring_integration():
    """Test monitoring components integration"""
    # Use different node ID to avoid Prometheus metric conflicts
    collector = MetricsCollector(node_id=99)
    monitor = HealthMonitor(node_id=99)
    
    # Collect metrics
    metrics = collector.collect_system_metrics()
    
    # Check thresholds
    monitor.check_metric_thresholds('cpu_percent', metrics.cpu_percent)
    monitor.check_metric_thresholds('memory_percent', metrics.memory_percent)
    
    # Get health summary
    summary = monitor.get_health_summary()
    assert summary['node_id'] == 99
    assert 'status' in summary
    assert 'uptime_seconds' in summary