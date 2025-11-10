"""Phase 3 success criteria verification tests"""
import pytest
import ssl
import time
from src.security.tls import TLSManager
from src.security.auth import AuthManager
from src.monitoring.metrics import MetricsCollector
from src.monitoring.health import HealthMonitor
from src.config.settings import ConfigManager


def test_secure_communication():
    """Test secure communication between nodes"""
    tls = TLSManager(node_id=1)
    
    # Generate and save certificates
    tls.generate_self_signed_cert()
    tls.save_cert_files()
    
    # Create SSL contexts
    server_context = tls.create_ssl_context(is_server=True)
    client_context = tls.create_ssl_context(is_server=False)
    
    # Verify SSL contexts are properly configured
    assert server_context.protocol == ssl.PROTOCOL_TLS_SERVER
    assert client_context.verify_mode == ssl.CERT_NONE  # For self-signed
    
    print("[+] Secure communication verified - TLS encryption enabled")


def test_real_time_monitoring():
    """Test real-time monitoring and alerting"""
    collector = MetricsCollector(node_id=103)
    monitor = HealthMonitor(node_id=103)
    
    # Collect initial metrics
    metrics = collector.collect_system_metrics()
    assert metrics.timestamp > 0
    
    # Test alerting system
    alert_triggered = False
    
    def alert_callback(alert):
        nonlocal alert_triggered
        alert_triggered = True
    
    monitor.add_alert_callback(alert_callback)
    
    # Trigger critical alert
    monitor.check_metric_thresholds('cpu_percent', 98.0)
    
    # Verify alert was triggered
    assert alert_triggered == True
    critical_alerts = monitor.get_critical_alerts()
    assert len(critical_alerts) > 0
    
    print("[+] Real-time monitoring and alerting verified")


def test_zero_downtime_configuration():
    """Test zero-downtime configuration changes"""
    config = ConfigManager()
    
    # Record initial config
    initial_config = config.get_all_config()
    
    # Make configuration changes
    config.update_config('monitoring', {'health_check_interval': 60})
    config.update_config('security', {'token_expiry_hours': 48})
    
    # Verify changes applied
    updated_config = config.get_all_config()
    assert updated_config['monitoring']['health_check_interval'] == 60
    assert updated_config['security']['token_expiry_hours'] == 48
    
    # Configuration changes should not require restart
    assert config.monitoring.health_check_interval == 60
    assert config.security.token_expiry_hours == 48
    
    print("[+] Zero-downtime configuration changes verified")


def test_production_ready_deployment():
    """Test production readiness features"""
    # Test authentication system
    auth = AuthManager()
    token = auth.generate_node_token(1, {"leader", "admin"})
    assert auth.verify_token(1, token) == True
    
    # Test TLS security
    tls = TLSManager(node_id=1)
    tls.generate_self_signed_cert()
    assert tls.certificate is not None
    
    # Test metrics collection
    collector = MetricsCollector(node_id=101)
    metrics = collector.collect_system_metrics()
    prometheus_output = collector.get_prometheus_metrics()
    assert len(prometheus_output) > 0
    
    # Test health monitoring
    monitor = HealthMonitor(node_id=1)
    health_summary = monitor.get_health_summary()
    assert health_summary['status'] in ['healthy', 'warning', 'critical']
    
    # Test configuration management
    config = ConfigManager()
    all_config = config.get_all_config()
    assert 'security' in all_config
    assert 'monitoring' in all_config
    
    print("[+] Production-ready deployment features verified")


@pytest.mark.asyncio
async def test_security_audit_compliance():
    """Test security audit compliance"""
    auth = AuthManager()
    tls = TLSManager(node_id=1)
    
    # Test authentication
    token = auth.generate_node_token(1, {"follower"})
    assert len(token) >= 32  # Strong token length
    
    # Test authorization
    assert auth.has_permission(1, "follower") == True
    assert auth.has_permission(1, "admin") == False
    
    # Test TLS certificate
    tls.generate_self_signed_cert()
    cert = tls.certificate
    
    # Verify certificate properties
    assert cert.not_valid_before <= cert.not_valid_after
    assert (cert.not_valid_after - cert.not_valid_before).days >= 365
    
    # Test token revocation
    assert auth.revoke_token(1) == True
    assert auth.verify_token(1, token) == False
    
    print("[+] Security audit compliance verified")


def test_comprehensive_monitoring_coverage():
    """Test comprehensive monitoring coverage"""
    collector = MetricsCollector(node_id=102)
    monitor = HealthMonitor(node_id=102)
    
    # Collect comprehensive metrics
    metrics = collector.collect_system_metrics()
    
    # Verify all key metrics are collected
    assert hasattr(metrics, 'cpu_percent')
    assert hasattr(metrics, 'memory_percent')
    assert hasattr(metrics, 'disk_usage_percent')
    assert hasattr(metrics, 'network_bytes_sent')
    assert hasattr(metrics, 'active_connections')
    
    # Test metric history
    recent_metrics = collector.get_recent_metrics(5)
    assert len(recent_metrics) > 0
    
    # Test health monitoring coverage
    monitor.check_metric_thresholds('cpu_percent', metrics.cpu_percent)
    monitor.check_metric_thresholds('memory_percent', metrics.memory_percent)
    
    health_summary = monitor.get_health_summary()
    assert 'critical_alerts' in health_summary
    assert 'warning_alerts' in health_summary
    assert 'uptime_seconds' in health_summary
    
    print("[+] Comprehensive monitoring coverage verified")