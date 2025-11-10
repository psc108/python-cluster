"""Configuration management"""
import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class SecurityConfig:
    enable_tls: bool = True
    cert_path: str = "/tmp/cluster_certs"
    require_auth: bool = True
    token_expiry_hours: int = 24


@dataclass
class MonitoringConfig:
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    alert_thresholds: Dict[str, Dict[str, float]] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'cpu_percent': {'warning': 80.0, 'critical': 95.0},
                'memory_percent': {'warning': 85.0, 'critical': 95.0}
            }


@dataclass
class ClusterConfig:
    node_id: int
    cluster_size: int = 3
    election_timeout: float = 5.0
    heartbeat_interval: float = 1.0
    max_log_entries: int = 10000


@dataclass
class APIConfig:
    enable_rest_api: bool = True
    api_port: int = 8080
    enable_swagger: bool = True
    cors_origins: list = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


class ConfigManager:
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv('CLUSTER_CONFIG', 'cluster_config.yaml')
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        self.cluster = ClusterConfig(node_id=int(os.getenv('NODE_ID', '1')))
        self.api = APIConfig()
        
        # Load from file if exists
        if os.path.exists(self.config_file):
            self.load_from_file()
            
        # Override with environment variables
        self.load_from_env()
        
    def load_from_file(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                
            if 'security' in config_data:
                self.security = SecurityConfig(**config_data['security'])
            if 'monitoring' in config_data:
                self.monitoring = MonitoringConfig(**config_data['monitoring'])
            if 'cluster' in config_data:
                self.cluster = ClusterConfig(**config_data['cluster'])
            if 'api' in config_data:
                self.api = APIConfig(**config_data['api'])
                
        except Exception as e:
            print(f"Warning: Failed to load config file {self.config_file}: {e}")
            
    def load_from_env(self):
        """Load configuration from environment variables"""
        # Cluster config
        if os.getenv('NODE_ID'):
            self.cluster.node_id = int(os.getenv('NODE_ID'))
        if os.getenv('CLUSTER_SIZE'):
            self.cluster.cluster_size = int(os.getenv('CLUSTER_SIZE'))
            
        # Security config
        if os.getenv('ENABLE_TLS'):
            self.security.enable_tls = os.getenv('ENABLE_TLS').lower() == 'true'
        if os.getenv('CERT_PATH'):
            self.security.cert_path = os.getenv('CERT_PATH')
            
        # Monitoring config
        if os.getenv('ENABLE_METRICS'):
            self.monitoring.enable_metrics = os.getenv('ENABLE_METRICS').lower() == 'true'
        if os.getenv('METRICS_PORT'):
            self.monitoring.metrics_port = int(os.getenv('METRICS_PORT'))
            
        # API config
        if os.getenv('API_PORT'):
            self.api.api_port = int(os.getenv('API_PORT'))
            
    def save_to_file(self):
        """Save current configuration to file"""
        config_data = {
            'security': asdict(self.security),
            'monitoring': asdict(self.monitoring),
            'cluster': asdict(self.cluster),
            'api': asdict(self.api)
        }
        
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config file: {e}")
            
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            'security': asdict(self.security),
            'monitoring': asdict(self.monitoring),
            'cluster': asdict(self.cluster),
            'api': asdict(self.api)
        }
        
    def update_config(self, section: str, updates: Dict[str, Any]):
        """Update configuration section"""
        if section == 'security':
            for key, value in updates.items():
                if hasattr(self.security, key):
                    setattr(self.security, key, value)
        elif section == 'monitoring':
            for key, value in updates.items():
                if hasattr(self.monitoring, key):
                    setattr(self.monitoring, key, value)
        elif section == 'cluster':
            for key, value in updates.items():
                if hasattr(self.cluster, key):
                    setattr(self.cluster, key, value)
        elif section == 'api':
            for key, value in updates.items():
                if hasattr(self.api, key):
                    setattr(self.api, key, value)