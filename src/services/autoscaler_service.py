#!/usr/bin/env python3
import docker
import json
import os
import sys
import time
from typing import Dict, Optional

class AutoScalerService:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.cooldown_period = 300  # 5 minutes
        
    def scale_application(self, app_name: str, target_replicas: int) -> Dict:
        """Scale application containers"""
        try:
            containers = self.docker_client.containers.list(
                all=True, filters={'label': f'app={app_name}'}
            )
            
            running = [c for c in containers if c.status == 'running']
            current_count = len(running)
            
            if target_replicas > current_count:
                self._scale_up(app_name, target_replicas - current_count)
            elif target_replicas < current_count:
                self._scale_down(running, current_count - target_replicas)
                
            return {"success": True, "replicas": target_replicas}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _scale_up(self, app_name: str, count: int):
        """Create new containers"""
        existing = self.docker_client.containers.list(
            all=True, filters={'label': f'app={app_name}'}
        )
        next_id = len(existing) + 1
        
        for i in range(count):
            container_name = f"{app_name}-{next_id + i}"
            self.docker_client.containers.run(
                "nginx:latest",
                name=container_name,
                labels={"app": app_name},
                ports={'80/tcp': None},
                detach=True
            )
            
    def _scale_down(self, containers, count: int):
        """Stop containers"""
        for i in range(min(count, len(containers))):
            containers[i].stop()
            containers[i].remove()

    def create_policy(self, policy_data: Dict) -> Dict:
        """Create scaling policy"""
        try:
            policies_file = 'data/scaling_policies.json'
            policies = {}
            
            if os.path.exists(policies_file):
                with open(policies_file, 'r') as f:
                    policies = json.load(f)
            
            policies[policy_data['application']] = {
                'application': policy_data['application'],
                'minReplicas': int(policy_data['minReplicas']),
                'maxReplicas': int(policy_data['maxReplicas']),
                'cpuThreshold': int(policy_data.get('cpuThreshold', 70)),
                'memoryThreshold': int(policy_data.get('memoryThreshold', 80)),
                'enabled': True,
                'created_at': time.time()
            }
            
            os.makedirs('data', exist_ok=True)
            with open(policies_file, 'w') as f:
                json.dump(policies, f, indent=2)
                
            return {"success": True, "policy": policies[policy_data['application']]}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def get_policies(self) -> Dict:
        """Get all scaling policies"""
        try:
            policies_file = 'data/scaling_policies.json'
            if not os.path.exists(policies_file):
                return {}
            with open(policies_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {}

if __name__ == "__main__":
    import os
    service = AutoScalerService()
    
    if len(sys.argv) >= 4 and sys.argv[1] == "scale":
        app_name = sys.argv[2]
        replicas = int(sys.argv[3])
        result = service.scale_application(app_name, replicas)
        print(json.dumps(result))
    elif len(sys.argv) >= 3 and sys.argv[1] == "create_policy":
        policy_json = sys.argv[2]
        policy_data = json.loads(policy_json)
        result = service.create_policy(policy_data)
        print(json.dumps(result))
    elif len(sys.argv) >= 2 and sys.argv[1] == "get_policies":
        result = service.get_policies()
        print(json.dumps(result))
    else:
        print(json.dumps({"error": "Usage: python autoscaler_service.py <command> [args]"}))