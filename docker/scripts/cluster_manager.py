#!/usr/bin/env python3
"""Automated cluster management for Python clustering software."""

import subprocess
import time
import sys
import json
import requests
from pathlib import Path

class ClusterManager:
    def __init__(self):
        self.docker_dir = Path(__file__).parent.parent
        self.compose_file = self.docker_dir / "docker-compose.yml"
        self.nodes = ["node1", "node2", "node3"]
        self.ports = [8001, 8002, 8003]
        self.compose_cmd = self._detect_compose_command()
    
    def _detect_compose_command(self):
        """Use direct Docker commands instead of compose"""
        return None

    def start_cluster(self):
        """Start the 3-node cluster."""
        print("Starting cluster...")
        try:
            # Create network
            subprocess.run(["docker", "network", "create", "cluster-net"], 
                         capture_output=True)
            
            # Build image
            subprocess.run(["docker", "build", "-f", "docker/Dockerfile", "-t", "cluster-node", "."], 
                         check=True, cwd=self.docker_dir.parent)
            
            # Start nodes
            for i in range(1, 4):
                port = 8000 + i
                subprocess.run([
                    "docker", "run", "-d", "--name", f"cluster-node-{i}",
                    "--network", "cluster-net",
                    "-p", f"{port}:8000",
                    "-e", f"NODE_ID={i}",
                    "-e", "NODE_PORT=8000",
                    "-e", "CLUSTER_SIZE=3",
                    "-e", "CLUSTER_NODES=cluster-node-1:8000,cluster-node-2:8000,cluster-node-3:8000",
                    "cluster-node"
                ], check=True)
            
            print("Waiting for nodes to be ready...")
            self._wait_for_cluster_ready()
            print("✅ Cluster started successfully!")
            self._show_cluster_status()
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start cluster: {e}")
            sys.exit(1)

    def stop_cluster(self):
        """Stop and cleanup the cluster."""
        print("Stopping cluster...")
        try:
            # Stop and remove containers
            for i in range(1, 4):
                subprocess.run(["docker", "stop", f"cluster-node-{i}"], 
                             capture_output=True)
                subprocess.run(["docker", "rm", f"cluster-node-{i}"], 
                             capture_output=True)
            
            # Remove network
            subprocess.run(["docker", "network", "rm", "cluster-net"], 
                         capture_output=True)
            print("✅ Cluster stopped successfully!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stop cluster: {e}")
            sys.exit(1)

    def restart_cluster(self):
        """Restart the entire cluster."""
        self.stop_cluster()
        time.sleep(2)
        self.start_cluster()

    def status(self):
        """Show cluster status."""
        self._show_cluster_status()

    def _wait_for_cluster_ready(self, timeout=60):
        """Wait for all nodes to be healthy."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            ready_nodes = 0
            
            for port in self.ports:
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=2)
                    if response.status_code == 200:
                        ready_nodes += 1
                except requests.RequestException:
                    pass
            
            if ready_nodes == len(self.ports):
                return True
                
            print(f"Nodes ready: {ready_nodes}/{len(self.ports)}")
            time.sleep(5)
        
        raise TimeoutError("Cluster failed to become ready within timeout")

    def _show_cluster_status(self):
        """Display current cluster status."""
        print("\n📊 Cluster Status:")
        print("-" * 50)
        
        for i, port in enumerate(self.ports, 1):
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                status = "🟢 HEALTHY" if response.status_code == 200 else "🟡 DEGRADED"
            except requests.RequestException:
                status = "🔴 UNHEALTHY"
            
            print(f"Node {i} (port {port}): {status}")
        
        print("-" * 50)

def main():
    manager = ClusterManager()
    
    if len(sys.argv) < 2:
        print("Usage: python cluster_manager.py [start|stop|restart|status]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_cluster()
    elif command == "stop":
        manager.stop_cluster()
    elif command == "restart":
        manager.restart_cluster()
    elif command == "status":
        manager.status()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: start, stop, restart, status")
        sys.exit(1)

if __name__ == "__main__":
    main()