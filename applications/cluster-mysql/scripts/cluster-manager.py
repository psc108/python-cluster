#!/usr/bin/env python3
import docker
import mysql.connector
import json
import time
from typing import Dict, List, Optional

class MySQLClusterManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.cluster_config = {
            "master_host": "mysql-master",
            "slave_hosts": ["mysql-slave-1", "mysql-slave-2"],
            "root_password": "cluster_root_pass",
            "monitor_user": "cluster_monitor",
            "monitor_password": "monitor_pass"
        }
    
    def get_cluster_status(self) -> Dict:
        """Get status of all MySQL cluster nodes"""
        status = {
            "cluster_name": "mysql-cluster",
            "nodes": [],
            "replication_status": "unknown",
            "total_nodes": 0,
            "healthy_nodes": 0
        }
        
        all_hosts = [self.cluster_config["master_host"]] + self.cluster_config["slave_hosts"]
        
        for host in all_hosts:
            node_status = self._get_node_status(host)
            status["nodes"].append(node_status)
            status["total_nodes"] += 1
            if node_status["status"] == "healthy":
                status["healthy_nodes"] += 1
        
        # Check replication status
        if status["healthy_nodes"] > 1:
            status["replication_status"] = self._check_replication_status()
        
        return status
    
    def _get_node_status(self, host: str) -> Dict:
        """Get status of individual MySQL node"""
        try:
            container = self.docker_client.containers.get(host)
            
            node_info = {
                "name": host,
                "container_id": container.id[:12],
                "status": "unknown",
                "role": "master" if host == self.cluster_config["master_host"] else "slave",
                "uptime": self._get_container_uptime(container),
                "mysql_status": "unknown",
                "replication_lag": None
            }
            
            if container.status == "running":
                # Check MySQL connectivity
                if self._check_mysql_connection(host):
                    node_info["mysql_status"] = "connected"
                    node_info["status"] = "healthy"
                    
                    # Check replication lag for slaves
                    if node_info["role"] == "slave":
                        node_info["replication_lag"] = self._get_replication_lag(host)
                else:
                    node_info["mysql_status"] = "disconnected"
                    node_info["status"] = "unhealthy"
            else:
                node_info["status"] = "stopped"
            
            return node_info
            
        except docker.errors.NotFound:
            return {
                "name": host,
                "container_id": None,
                "status": "not_found",
                "role": "master" if host == self.cluster_config["master_host"] else "slave",
                "uptime": "0s",
                "mysql_status": "not_running",
                "replication_lag": None
            }
    
    def _check_mysql_connection(self, host: str) -> bool:
        """Check if MySQL is accessible"""
        try:
            conn = mysql.connector.connect(
                host=host,
                port=3306,
                user=self.cluster_config["monitor_user"],
                password=self.cluster_config["monitor_password"],
                connection_timeout=5
            )
            conn.close()
            return True
        except:
            return False
    
    def _get_replication_lag(self, slave_host: str) -> Optional[int]:
        """Get replication lag in seconds"""
        try:
            conn = mysql.connector.connect(
                host=slave_host,
                port=3306,
                user=self.cluster_config["monitor_user"],
                password=self.cluster_config["monitor_password"]
            )
            cursor = conn.cursor()
            cursor.execute("SHOW SLAVE STATUS")
            result = cursor.fetchone()
            conn.close()
            
            if result and result[32]:  # Seconds_Behind_Master
                return int(result[32])
            return 0
        except:
            return None
    
    def _check_replication_status(self) -> str:
        """Check overall replication health"""
        healthy_slaves = 0
        total_slaves = len(self.cluster_config["slave_hosts"])
        
        for slave_host in self.cluster_config["slave_hosts"]:
            if self._check_mysql_connection(slave_host):
                lag = self._get_replication_lag(slave_host)
                if lag is not None and lag < 10:  # Less than 10 seconds lag
                    healthy_slaves += 1
        
        if healthy_slaves == total_slaves:
            return "healthy"
        elif healthy_slaves > 0:
            return "degraded"
        else:
            return "failed"
    
    def _get_container_uptime(self, container) -> str:
        """Get container uptime in human readable format"""
        try:
            started_at = container.attrs['State']['StartedAt']
            from datetime import datetime
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            uptime = datetime.now(start_time.tzinfo) - start_time
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "unknown"
    
    def failover_to_slave(self, new_master_host: str) -> Dict:
        """Promote slave to master (manual failover)"""
        if new_master_host not in self.cluster_config["slave_hosts"]:
            return {"success": False, "error": "Invalid slave host"}
        
        try:
            # Stop replication on new master
            conn = mysql.connector.connect(
                host=new_master_host,
                port=3306,
                user="root",
                password=self.cluster_config["root_password"]
            )
            cursor = conn.cursor()
            cursor.execute("STOP SLAVE")
            cursor.execute("RESET SLAVE ALL")
            cursor.execute("SET GLOBAL read_only = OFF")
            conn.close()
            
            # Update cluster configuration
            old_master = self.cluster_config["master_host"]
            self.cluster_config["master_host"] = new_master_host
            self.cluster_config["slave_hosts"].remove(new_master_host)
            self.cluster_config["slave_hosts"].append(old_master)
            
            return {
                "success": True,
                "new_master": new_master_host,
                "old_master": old_master
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    import sys
    manager = MySQLClusterManager()
    
    if len(sys.argv) < 2:
        print("Usage: python cluster-manager.py <command>")
        print("Commands: status, failover <slave_host>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        status = manager.get_cluster_status()
        print(json.dumps(status, indent=2))
    elif command == "failover" and len(sys.argv) == 3:
        result = manager.failover_to_slave(sys.argv[2])
        print(json.dumps(result, indent=2))
    else:
        print("Invalid command")
        sys.exit(1)

if __name__ == "__main__":
    main()