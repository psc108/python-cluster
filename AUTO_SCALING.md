# Auto-Scaling

## Overview

The Auto-Scaling system automatically adjusts application instances and cluster resources based on demand, performance metrics, and predefined policies. It ensures optimal resource utilization while maintaining application performance and availability.

## Scaling Types

### Horizontal Scaling (Scale Out/In)
- **Add/remove application instances** across cluster nodes
- **Distribute load** among multiple instances
- **Use cases**: Web applications, stateless services, microservices
- **Benefits**: Better fault tolerance, linear performance scaling

### Vertical Scaling (Scale Up/Down)
- **Increase/decrease resources** (CPU, memory) for existing instances
- **Single instance optimization**
- **Use cases**: Databases, memory-intensive applications
- **Benefits**: Simpler architecture, no data distribution complexity

### Cluster Scaling
- **Add/remove cluster nodes** based on overall resource demand
- **Infrastructure-level scaling**
- **Use cases**: High demand periods, resource exhaustion
- **Benefits**: Increased total cluster capacity

## Scaling Policies

### Metric-Based Scaling
```yaml
apiVersion: v1
kind: AutoScalingPolicy
metadata:
  name: web-app-scaling
spec:
  application: web-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: cpu
      target: 70%
      scaleUp:
        threshold: 80%
        cooldown: 300s
        increment: 2
      scaleDown:
        threshold: 30%
        cooldown: 600s
        decrement: 1
        
    - type: memory
      target: 80%
      scaleUp:
        threshold: 90%
        cooldown: 300s
        increment: 1
        
    - type: requests_per_second
      target: 1000
      scaleUp:
        threshold: 1200
        cooldown: 180s
        increment: 2
      scaleDown:
        threshold: 500
        cooldown: 900s
        decrement: 1
```

### Schedule-Based Scaling
```yaml
apiVersion: v1
kind: ScheduledScaling
metadata:
  name: business-hours-scaling
spec:
  application: web-app
  schedules:
    - name: morning-ramp-up
      cron: "0 8 * * 1-5"    # 8 AM weekdays
      replicas: 8
      
    - name: lunch-peak
      cron: "0 12 * * 1-5"   # 12 PM weekdays
      replicas: 12
      
    - name: evening-scale-down
      cron: "0 18 * * 1-5"   # 6 PM weekdays
      replicas: 4
      
    - name: weekend-minimal
      cron: "0 0 * * 6,0"    # Midnight weekends
      replicas: 2
```

### Predictive Scaling
```yaml
apiVersion: v1
kind: PredictiveScaling
metadata:
  name: ml-based-scaling
spec:
  application: web-app
  model: time-series-forecast
  lookAhead: 30m
  confidence: 85%
  metrics:
    - cpu_usage
    - request_rate
    - response_time
  training:
    dataRetention: 30d
    retrainInterval: 24h
```

## Scaling Engine

### Core Scaling Logic
```python
class AutoScaler:
    def __init__(self, cluster_client, metrics_client):
        self.cluster = cluster_client
        self.metrics = metrics_client
        self.policies = {}
        self.scaling_history = []
        
    async def evaluate_scaling_policies(self):
        """Evaluate all scaling policies and make scaling decisions"""
        for policy_name, policy in self.policies.items():
            try:
                decision = await self.evaluate_policy(policy)
                if decision:
                    await self.execute_scaling_decision(decision)
            except Exception as e:
                logger.error(f"Policy evaluation failed: {policy_name}: {e}")
                
    async def evaluate_policy(self, policy):
        """Evaluate a single scaling policy"""
        app_name = policy["application"]
        current_replicas = await self.get_current_replicas(app_name)
        
        # Get current metrics
        metrics = await self.get_application_metrics(app_name)
        
        # Check each metric threshold
        scale_up_votes = 0
        scale_down_votes = 0
        
        for metric_config in policy["metrics"]:
            metric_value = metrics.get(metric_config["type"])
            if metric_value is None:
                continue
                
            # Check scale up conditions
            if metric_value > metric_config["scaleUp"]["threshold"]:
                if self.can_scale_up(policy, metric_config):
                    scale_up_votes += 1
                    
            # Check scale down conditions
            elif metric_value < metric_config["scaleDown"]["threshold"]:
                if self.can_scale_down(policy, metric_config):
                    scale_down_votes += 1
        
        # Make scaling decision
        if scale_up_votes > 0 and current_replicas < policy["maxReplicas"]:
            return self.create_scale_up_decision(policy, scale_up_votes)
        elif scale_down_votes > 0 and current_replicas > policy["minReplicas"]:
            return self.create_scale_down_decision(policy, scale_down_votes)
            
        return None
        
    async def execute_scaling_decision(self, decision):
        """Execute scaling decision"""
        app_name = decision["application"]
        target_replicas = decision["targetReplicas"]
        
        logger.info(f"Scaling {app_name} to {target_replicas} replicas")
        
        # Update application replicas
        await self.cluster.scale_application(app_name, target_replicas)
        
        # Record scaling event
        self.scaling_history.append({
            "timestamp": time.time(),
            "application": app_name,
            "action": decision["action"],
            "from_replicas": decision["currentReplicas"],
            "to_replicas": target_replicas,
            "reason": decision["reason"]
        })
```

### Metrics Collection
```python
class ScalingMetricsCollector:
    def __init__(self, cluster_client):
        self.cluster = cluster_client
        self.metric_cache = {}
        
    async def get_application_metrics(self, app_name):
        """Collect comprehensive application metrics"""
        instances = await self.cluster.get_application_instances(app_name)
        
        # Aggregate metrics from all instances
        total_cpu = 0
        total_memory = 0
        total_requests = 0
        total_response_time = 0
        
        for instance in instances:
            instance_metrics = await self.get_instance_metrics(instance)
            total_cpu += instance_metrics.get("cpu_percent", 0)
            total_memory += instance_metrics.get("memory_percent", 0)
            total_requests += instance_metrics.get("requests_per_second", 0)
            total_response_time += instance_metrics.get("avg_response_time", 0)
            
        instance_count = len(instances)
        if instance_count == 0:
            return {}
            
        return {
            "cpu": total_cpu / instance_count,
            "memory": total_memory / instance_count,
            "requests_per_second": total_requests,
            "avg_response_time": total_response_time / instance_count,
            "instance_count": instance_count,
            "healthy_instances": sum(1 for i in instances if i["status"] == "healthy")
        }
        
    async def get_cluster_metrics(self):
        """Get cluster-wide resource metrics"""
        nodes = await self.cluster.get_cluster_nodes()
        
        total_cpu_capacity = 0
        total_cpu_used = 0
        total_memory_capacity = 0
        total_memory_used = 0
        
        for node in nodes:
            node_metrics = await self.get_node_metrics(node["id"])
            total_cpu_capacity += node_metrics["cpu_capacity"]
            total_cpu_used += node_metrics["cpu_used"]
            total_memory_capacity += node_metrics["memory_capacity"]
            total_memory_used += node_metrics["memory_used"]
            
        return {
            "cpu_utilization": (total_cpu_used / total_cpu_capacity) * 100,
            "memory_utilization": (total_memory_used / total_memory_capacity) * 100,
            "node_count": len(nodes),
            "healthy_nodes": sum(1 for n in nodes if n["status"] == "healthy")
        }
```

## Scaling Strategies

### Conservative Scaling
- **Gradual changes** with longer cooldown periods
- **Higher thresholds** for scaling actions
- **Suitable for**: Production environments, cost-sensitive applications

### Aggressive Scaling
- **Rapid response** to metric changes
- **Lower thresholds** and shorter cooldowns
- **Suitable for**: High-performance requirements, traffic spikes

### Predictive Scaling
```python
class PredictiveScaler:
    def __init__(self, metrics_history):
        self.model = TimeSeriesForecaster()
        self.metrics_history = metrics_history
        
    async def predict_scaling_needs(self, app_name, look_ahead_minutes=30):
        """Predict future scaling needs using ML"""
        # Get historical metrics
        historical_data = await self.get_historical_metrics(
            app_name, 
            days=30
        )
        
        # Train/update model
        self.model.fit(historical_data)
        
        # Predict future metrics
        future_metrics = self.model.predict(
            steps=look_ahead_minutes,
            confidence_interval=0.95
        )
        
        # Generate scaling recommendations
        recommendations = []
        for timestamp, predicted_metrics in future_metrics.items():
            if predicted_metrics["cpu"] > 80:
                recommendations.append({
                    "timestamp": timestamp,
                    "action": "scale_up",
                    "reason": f"Predicted CPU: {predicted_metrics['cpu']:.1f}%",
                    "confidence": predicted_metrics["confidence"]
                })
                
        return recommendations
```

## Application Integration

### Scaling-Aware Applications
```python
class ScalableApplication(ClusterApplication):
    def __init__(self, app_id, config):
        super().__init__(app_id, config)
        self.scaling_config = config.get("scaling", {})
        
    async def on_scale_up(self, new_instance_count):
        """Called when application is scaled up"""
        logger.info(f"Scaling up to {new_instance_count} instances")
        
        # Redistribute work among instances
        await self.redistribute_workload()
        
        # Update load balancer configuration
        await self.update_load_balancer()
        
    async def on_scale_down(self, new_instance_count):
        """Called when application is scaled down"""
        logger.info(f"Scaling down to {new_instance_count} instances")
        
        # Gracefully handle instance termination
        await self.drain_connections()
        
        # Migrate in-progress work
        await self.migrate_active_sessions()
        
    async def get_scaling_metrics(self):
        """Provide custom metrics for scaling decisions"""
        return {
            "queue_length": await self.get_queue_length(),
            "active_connections": await self.get_connection_count(),
            "processing_time": await self.get_avg_processing_time(),
            "error_rate": await self.get_error_rate()
        }
        
    async def can_scale_down(self):
        """Check if instance can be safely terminated"""
        # Check for active connections
        if await self.get_connection_count() > 0:
            return False
            
        # Check for in-progress work
        if await self.has_active_work():
            return False
            
        return True
```

### Graceful Scaling
```python
class GracefulScaler:
    async def scale_down_instance(self, instance_id, timeout=300):
        """Gracefully scale down an instance"""
        # 1. Stop accepting new requests
        await self.stop_accepting_requests(instance_id)
        
        # 2. Wait for active requests to complete
        start_time = time.time()
        while time.time() - start_time < timeout:
            active_requests = await self.get_active_requests(instance_id)
            if active_requests == 0:
                break
            await asyncio.sleep(5)
            
        # 3. Force terminate if timeout exceeded
        if active_requests > 0:
            logger.warning(f"Force terminating instance {instance_id} with {active_requests} active requests")
            
        # 4. Terminate instance
        await self.terminate_instance(instance_id)
        
    async def scale_up_instance(self, app_name, node_id=None):
        """Scale up by adding new instance"""
        # 1. Select optimal node
        if node_id is None:
            node_id = await self.select_optimal_node(app_name)
            
        # 2. Start new instance
        instance_id = await self.start_instance(app_name, node_id)
        
        # 3. Wait for instance to be ready
        await self.wait_for_instance_ready(instance_id)
        
        # 4. Add to load balancer
        await self.add_to_load_balancer(instance_id)
        
        return instance_id
```

## Cluster Auto-Scaling

### Node Auto-Scaling
```python
class ClusterAutoScaler:
    def __init__(self, cluster_client, cloud_provider):
        self.cluster = cluster_client
        self.cloud = cloud_provider
        
    async def evaluate_cluster_scaling(self):
        """Evaluate if cluster needs more/fewer nodes"""
        cluster_metrics = await self.get_cluster_metrics()
        
        # Check if we need more nodes
        if (cluster_metrics["cpu_utilization"] > 80 or 
            cluster_metrics["memory_utilization"] > 85):
            
            # Check if we can schedule more pods
            unschedulable_apps = await self.get_unschedulable_applications()
            if unschedulable_apps:
                await self.scale_up_cluster()
                
        # Check if we can remove nodes
        elif (cluster_metrics["cpu_utilization"] < 30 and 
              cluster_metrics["memory_utilization"] < 40):
            
            await self.scale_down_cluster()
            
    async def scale_up_cluster(self):
        """Add new node to cluster"""
        # Create new cloud instance
        instance = await self.cloud.create_instance(
            instance_type="m5.large",
            image="cluster-node:latest"
        )
        
        # Wait for instance to be ready
        await self.cloud.wait_for_instance_ready(instance.id)
        
        # Join instance to cluster
        await self.cluster.add_node(instance.private_ip)
        
        logger.info(f"Added new cluster node: {instance.id}")
        
    async def scale_down_cluster(self):
        """Remove underutilized node from cluster"""
        # Find node with lowest utilization
        candidate_node = await self.find_least_utilized_node()
        
        if candidate_node:
            # Drain applications from node
            await self.drain_node(candidate_node["id"])
            
            # Remove from cluster
            await self.cluster.remove_node(candidate_node["id"])
            
            # Terminate cloud instance
            await self.cloud.terminate_instance(candidate_node["instance_id"])
            
            logger.info(f"Removed cluster node: {candidate_node['id']}")
```

## Scaling Management

### CLI Commands
```bash
# Create auto-scaling policy
python -m src.scaling.cli create-policy \
  --app web-app \
  --min-replicas 2 \
  --max-replicas 10 \
  --cpu-target 70 \
  --memory-target 80

# List scaling policies
python -m src.scaling.cli list-policies

# Update scaling policy
python -m src.scaling.cli update-policy web-app-scaling \
  --max-replicas 20 \
  --cpu-target 60

# Manual scaling
python -m src.scaling.cli scale web-app --replicas 5

# Scaling history
python -m src.scaling.cli history web-app --last 24h

# Enable/disable auto-scaling
python -m src.scaling.cli enable web-app-scaling
python -m src.scaling.cli disable web-app-scaling

# Cluster scaling
python -m src.scaling.cli cluster-scale \
  --min-nodes 3 \
  --max-nodes 10 \
  --cpu-threshold 80
```

### REST API
```bash
# Create scaling policy
curl -X POST http://localhost:8001/api/scaling/policies \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "web-app-scaling",
    "application": "web-app",
    "minReplicas": 2,
    "maxReplicas": 10,
    "metrics": [
      {"type": "cpu", "target": 70},
      {"type": "memory", "target": 80}
    ]
  }'

# Get scaling status
curl http://localhost:8001/api/scaling/applications/web-app \
  -H "Authorization: Bearer <token>"

# Manual scale
curl -X POST http://localhost:8001/api/scaling/applications/web-app/scale \
  -H "Authorization: Bearer <token>" \
  -d '{"replicas": 5}'

# Scaling history
curl http://localhost:8001/api/scaling/applications/web-app/history \
  -H "Authorization: Bearer <token>"
```

## Monitoring and Alerting

### Scaling Metrics
```python
scaling_metrics = {
    "scaling_events_total": Counter("autoscaler_scaling_events_total", ["app", "action"]),
    "scaling_duration_seconds": Histogram("autoscaler_scaling_duration_seconds"),
    "policy_evaluation_duration": Histogram("autoscaler_policy_evaluation_seconds"),
    "current_replicas": Gauge("autoscaler_current_replicas", ["app"]),
    "target_replicas": Gauge("autoscaler_target_replicas", ["app"]),
    "scaling_cooldown_active": Gauge("autoscaler_cooldown_active", ["app", "direction"])
}
```

### Alerts
```yaml
alerts:
  - name: ScalingFailure
    condition: scaling_events_total{action="failed"} > 0
    severity: critical
    message: "Auto-scaling failed for application {{ $labels.app }}"
    
  - name: FrequentScaling
    condition: rate(scaling_events_total[5m]) > 0.1
    severity: warning
    message: "Application {{ $labels.app }} is scaling frequently"
    
  - name: MaxReplicasReached
    condition: current_replicas == target_replicas and target_replicas == max_replicas
    severity: warning
    message: "Application {{ $labels.app }} has reached maximum replicas"
```

## Best Practices

### Policy Design
- **Set Appropriate Thresholds**: Avoid flapping with proper margins
- **Use Multiple Metrics**: Don't rely on single metric for decisions
- **Configure Cooldowns**: Prevent rapid scaling oscillations
- **Test Policies**: Validate scaling behavior under load

### Application Design
- **Stateless Design**: Make applications easy to scale horizontally
- **Graceful Shutdown**: Handle termination signals properly
- **Health Checks**: Implement comprehensive health endpoints
- **Resource Limits**: Set appropriate CPU/memory limits

### Monitoring
- **Track Scaling Events**: Monitor scaling frequency and success rate
- **Resource Utilization**: Keep track of actual vs. target utilization
- **Application Performance**: Ensure scaling improves performance
- **Cost Optimization**: Balance performance with resource costs