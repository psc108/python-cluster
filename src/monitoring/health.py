"""Health monitoring and alerting"""
import time
import asyncio
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class HealthAlert:
    level: AlertLevel
    message: str
    timestamp: float
    node_id: int
    metric_name: str
    current_value: float
    threshold: float


class HealthMonitor:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.thresholds = {
            'cpu_percent': {'warning': 80.0, 'critical': 95.0},
            'memory_percent': {'warning': 85.0, 'critical': 95.0},
            'disk_usage_percent': {'warning': 85.0, 'critical': 95.0},
            'response_time_ms': {'warning': 1000.0, 'critical': 5000.0}
        }
        self.alerts: List[HealthAlert] = []
        self.alert_callbacks: List[Callable] = []
        self.monitoring = False
        
    def add_alert_callback(self, callback: Callable):
        """Add callback for alert notifications"""
        self.alert_callbacks.append(callback)
        
    def check_metric_thresholds(self, metric_name: str, value: float):
        """Check if metric exceeds thresholds"""
        if metric_name not in self.thresholds:
            return
            
        thresholds = self.thresholds[metric_name]
        
        if value >= thresholds['critical']:
            self._create_alert(AlertLevel.CRITICAL, metric_name, value, thresholds['critical'])
        elif value >= thresholds['warning']:
            self._create_alert(AlertLevel.WARNING, metric_name, value, thresholds['warning'])
            
    def _create_alert(self, level: AlertLevel, metric_name: str, value: float, threshold: float):
        """Create and process alert"""
        alert = HealthAlert(
            level=level,
            message=f"{metric_name} is {value:.1f}% (threshold: {threshold:.1f}%)",
            timestamp=time.time(),
            node_id=self.node_id,
            metric_name=metric_name,
            current_value=value,
            threshold=threshold
        )
        
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
            
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass  # Don't let callback errors break monitoring
                
    def get_recent_alerts(self, minutes: int = 60) -> List[HealthAlert]:
        """Get alerts from recent time period"""
        cutoff_time = time.time() - (minutes * 60)
        return [alert for alert in self.alerts if alert.timestamp > cutoff_time]
        
    def get_critical_alerts(self) -> List[HealthAlert]:
        """Get all critical alerts"""
        return [alert for alert in self.alerts if alert.level == AlertLevel.CRITICAL]
        
    def clear_old_alerts(self, hours: int = 24):
        """Clear alerts older than specified hours"""
        cutoff_time = time.time() - (hours * 3600)
        self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]
        
    def get_health_summary(self) -> Dict:
        """Get overall health summary"""
        recent_alerts = self.get_recent_alerts(60)  # Last hour
        critical_count = len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL])
        warning_count = len([a for a in recent_alerts if a.level == AlertLevel.WARNING])
        
        if critical_count > 0:
            status = "critical"
        elif warning_count > 0:
            status = "warning"
        else:
            status = "healthy"
            
        return {
            'node_id': self.node_id,
            'status': status,
            'critical_alerts': critical_count,
            'warning_alerts': warning_count,
            'last_check': time.time(),
            'uptime_seconds': time.time() - getattr(self, 'start_time', time.time())
        }