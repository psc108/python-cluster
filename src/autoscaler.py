#!/usr/bin/env python3
"""
Basic Auto-Scaler for Phase 2 Implementation
Evaluates scaling policies and triggers scaling actions
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasicAutoScaler:
    def __init__(self, dashboard_url: str = "http://localhost:8080"):
        self.dashboard_url = dashboard_url
        self.policies: Dict = {}
        self.cooldowns: Dict[str, float] = {}
        self.running = False
        
    async def load_policies(self) -> Dict:
        """Load scaling policies from dashboard API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.dashboard_url}/api/cluster.php?action=get_scaling_policies") as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except Exception as e:
            logger.error(f"Failed to load policies: {e}")
            return {}
    
    async def get_applications(self) -> List[Dict]:
        """Get current application status"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.dashboard_url}/api/cluster.php?action=applications") as response:
                    if response.status == 200:
                        return await response.json()
                    return []
        except Exception as e:
            logger.error(f"Failed to get applications: {e}")
            return []
    
    async def trigger_scaling(self, app_name: str, target_replicas: int) -> bool:
        """Trigger scaling action via dashboard API"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "application": app_name,
                    "replicas": target_replicas
                }
                async with session.post(
                    f"{self.dashboard_url}/api/cluster.php?action=scale",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    return result.get("success", False)
        except Exception as e:
            logger.error(f"Failed to trigger scaling for {app_name}: {e}")
            return False
    
    def is_in_cooldown(self, app_name: str, cooldown_seconds: int = 300) -> bool:
        """Check if application is in cooldown period"""
        last_action = self.cooldowns.get(app_name, 0)
        return (time.time() - last_action) < cooldown_seconds
    
    def set_cooldown(self, app_name: str):
        """Set cooldown for application"""
        self.cooldowns[app_name] = time.time()
    
    async def evaluate_policy(self, app_name: str, policy: Dict, app_data: Dict) -> Optional[Dict]:
        """Evaluate single scaling policy"""
        if not policy.get("enabled", True):
            return None
            
        if app_data["status"] != "running":
            return None
            
        # Parse current replicas
        replicas_parts = app_data["replicas"].split("/")
        current_replicas = int(replicas_parts[0])
        
        # Check cooldown
        if self.is_in_cooldown(app_name):
            logger.debug(f"Application {app_name} in cooldown, skipping evaluation")
            return None
        
        # Scale up conditions
        cpu_threshold = policy.get("cpuThreshold", 70)
        memory_threshold = policy.get("memoryThreshold", 80)
        
        # Get actual memory limit for this application
        memory_limit_mb = await self.get_application_memory_limit(app_name)
        memory_threshold_mb = (memory_threshold / 100) * memory_limit_mb
        
        if (app_data["cpu_percent"] > cpu_threshold or 
            app_data["memory_mb"] > memory_threshold_mb) and \
           current_replicas < policy["maxReplicas"]:
            
            target_replicas = min(current_replicas + 1, policy["maxReplicas"])
            return {
                "application": app_name,
                "action": "scale_up",
                "current_replicas": current_replicas,
                "target_replicas": target_replicas,
                "reason": f"High resource usage (CPU: {app_data['cpu_percent']}%, Memory: {app_data['memory_mb']}MB)"
            }
        
        # Scale down conditions
        memory_scale_down_mb = ((memory_threshold - 20) / 100) * memory_limit_mb
        
        if (app_data["cpu_percent"] < (cpu_threshold - 20) and 
            app_data["memory_mb"] < memory_scale_down_mb) and \
           current_replicas > policy["minReplicas"]:
            
            target_replicas = max(current_replicas - 1, policy["minReplicas"])
            return {
                "application": app_name,
                "action": "scale_down",
                "current_replicas": current_replicas,
                "target_replicas": target_replicas,
                "reason": f"Low resource usage (CPU: {app_data['cpu_percent']}%, Memory: {app_data['memory_mb']}MB)"
            }
        
        return None
    
    async def get_application_memory_limit(self, app_name: str) -> int:
        """Get memory limit for application from dashboard API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.dashboard_url}/api/cluster.php?action=resource_info") as response:
                    if response.status == 200:
                        data = await response.json()
                        # For now, return default 128MB - could be enhanced to read from app.yaml
                        return 128
                    return 128
        except Exception as e:
            logger.error(f"Failed to get memory limit for {app_name}: {e}")
            return 128
    
    async def evaluate_all_policies(self):
        """Evaluate all scaling policies"""
        policies = await self.load_policies()
        applications = await self.get_applications()
        
        if not policies or not applications:
            return
        
        # Create app lookup
        app_lookup = {app["name"]: app for app in applications}
        
        scaling_actions = []
        
        for app_name, policy in policies.items():
            if app_name not in app_lookup:
                continue
                
            app_data = app_lookup[app_name]
            decision = await self.evaluate_policy(app_name, policy, app_data)
            
            if decision:
                scaling_actions.append(decision)
        
        # Execute scaling actions
        for action in scaling_actions:
            success = await self.trigger_scaling(
                action["application"], 
                action["target_replicas"]
            )
            
            if success:
                self.set_cooldown(action["application"])
                logger.info(f"Executed {action['action']} for {action['application']}: "
                          f"{action['current_replicas']} -> {action['target_replicas']} replicas. "
                          f"Reason: {action['reason']}")
            else:
                logger.error(f"Failed to execute {action['action']} for {action['application']}")
    
    async def run(self, interval_seconds: int = 60):
        """Run auto-scaler with specified interval"""
        self.running = True
        logger.info(f"Starting auto-scaler with {interval_seconds}s interval")
        
        while self.running:
            try:
                await self.evaluate_all_policies()
            except Exception as e:
                logger.error(f"Error during policy evaluation: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Stop auto-scaler"""
        self.running = False
        logger.info("Auto-scaler stopped")

async def main():
    """Main entry point"""
    autoscaler = BasicAutoScaler()
    
    try:
        await autoscaler.run(interval_seconds=60)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        autoscaler.stop()

if __name__ == "__main__":
    asyncio.run(main())