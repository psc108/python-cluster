# Application Framework

## Overview

The Application Framework provides a standardized way to develop, deploy, and manage applications on the clustering system. Applications run as distributed services across cluster nodes with automatic load balancing, fault tolerance, and lifecycle management.

## Core Concepts

### Application
A distributed service that runs across multiple cluster nodes, consisting of:
- **Application Definition**: Metadata, dependencies, and configuration
- **Application Code**: Business logic and service implementation
- **Deployment Specification**: Resource requirements and placement rules
- **Health Checks**: Monitoring and recovery mechanisms

### Application Lifecycle
1. **Package** - Bundle application code and dependencies
2. **Deploy** - Install application across cluster nodes
3. **Start** - Launch application instances
4. **Monitor** - Track health and performance
5. **Scale** - Adjust instance count based on load
6. **Update** - Deploy new versions with rolling updates
7. **Stop** - Gracefully shutdown application
8. **Undeploy** - Remove application from cluster

## Application Structure

### Directory Layout
```
applications/
├── my-app/
│   ├── app.yaml              # Application definition
│   ├── src/                  # Application source code
│   │   ├── main.py          # Entry point
│   │   ├── handlers/        # Request handlers
│   │   └── utils/           # Utility modules
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Container definition
│   └── tests/              # Application tests
```

### Application Definition (app.yaml)
```yaml
apiVersion: v1
kind: Application
metadata:
  name: my-app
  version: 1.0.0
  description: "Sample distributed application"
spec:
  replicas: 3                 # Number of instances
  image: my-app:latest        # Container image
  ports:
    - name: http
      port: 8080
      protocol: TCP
  resources:
    cpu: 100m                 # CPU request (millicores)
    memory: 128Mi             # Memory request
  healthCheck:
    path: /health
    port: 8080
    interval: 30s
    timeout: 5s
  environment:
    - name: LOG_LEVEL
      value: INFO
    - name: CLUSTER_MODE
      value: "true"
```

## Application Base Class

Applications must inherit from the base `ClusterApplication` class:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio

class ClusterApplication(ABC):
    def __init__(self, app_id: str, config: Dict[str, Any]):
        self.app_id = app_id
        self.config = config
        self.node_id = None
        self.cluster_client = None
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize application resources"""
        pass
        
    @abstractmethod
    async def start(self) -> bool:
        """Start application services"""
        pass
        
    @abstractmethod
    async def stop(self) -> bool:
        """Stop application services"""
        pass
        
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return application health status"""
        pass
        
    @abstractmethod
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming requests"""
        pass
        
    async def on_leader_change(self, new_leader_id: int):
        """Called when cluster leader changes"""
        pass
        
    async def on_node_join(self, node_id: int):
        """Called when a node joins the cluster"""
        pass
        
    async def on_node_leave(self, node_id: int):
        """Called when a node leaves the cluster"""
        pass
```

## Application Types

### Stateless Applications
- No persistent state between requests
- Can run on any cluster node
- Easy to scale horizontally
- Examples: Web APIs, microservices, data processors

### Stateful Applications
- Maintain persistent state
- May require specific node placement
- More complex scaling and failover
- Examples: Databases, caches, session stores

### Leader-Only Applications
- Run only on the cluster leader
- Automatically migrate on leader change
- Examples: Schedulers, coordinators, singleton services

### Distributed Applications
- Run coordinated instances across all nodes
- Share state through cluster consensus
- Examples: Distributed caches, replicated databases

## Deployment Commands

### CLI Interface
```bash
# Deploy application
python -m src.apps.cli deploy applications/my-app/

# List applications
python -m src.apps.cli list

# Get application status
python -m src.apps.cli status my-app

# Scale application
python -m src.apps.cli scale my-app --replicas 5

# Update application
python -m src.apps.cli update my-app --image my-app:2.0.0

# Stop application
python -m src.apps.cli stop my-app

# Remove application
python -m src.apps.cli undeploy my-app

# View application logs
python -m src.apps.cli logs my-app
```

### REST API
```bash
# Deploy application
curl -X POST http://localhost:8001/api/apps \
  -H "Authorization: Bearer <token>" \
  -F "app=@applications/my-app.tar.gz"

# Get application status
curl http://localhost:8001/api/apps/my-app \
  -H "Authorization: Bearer <token>"

# Scale application
curl -X PATCH http://localhost:8001/api/apps/my-app \
  -H "Authorization: Bearer <token>" \
  -d '{"replicas": 5}'

# Delete application
curl -X DELETE http://localhost:8001/api/apps/my-app \
  -H "Authorization: Bearer <token>"
```

## Load Balancing

### Round Robin
Default load balancing distributes requests evenly across healthy instances.

### Sticky Sessions
Route requests from the same client to the same instance.

### Resource-Based
Route requests to instances with available resources.

### Custom Routing
Application-defined routing logic based on request content.

## Service Discovery

Applications can discover and communicate with other applications:

```python
# Find application instances
instances = await self.cluster_client.discover_service("my-other-app")

# Make request to another application
response = await self.cluster_client.request_service(
    "my-other-app", 
    {"action": "process", "data": payload}
)
```

## Configuration Management

### Environment Variables
```yaml
environment:
  - name: DATABASE_URL
    value: "postgresql://localhost:5432/mydb"
  - name: API_KEY
    valueFrom:
      secretRef:
        name: api-credentials
        key: api-key
```

### Configuration Files
```yaml
configMaps:
  - name: app-config
    mountPath: /etc/config
    data:
      config.json: |
        {
          "timeout": 30,
          "retries": 3
        }
```

## Monitoring and Logging

### Health Checks
Applications must implement health check endpoints that return:
```json
{
  "status": "healthy|unhealthy|degraded",
  "timestamp": "2024-01-01T12:00:00Z",
  "checks": {
    "database": "healthy",
    "cache": "healthy",
    "external_api": "degraded"
  },
  "metrics": {
    "requests_per_second": 150,
    "error_rate": 0.01,
    "response_time_ms": 45
  }
}
```

### Metrics Collection
Applications can expose custom metrics:
```python
from prometheus_client import Counter, Histogram

request_count = Counter('app_requests_total', 'Total requests')
request_duration = Histogram('app_request_duration_seconds', 'Request duration')

@request_duration.time()
async def handle_request(self, request):
    request_count.inc()
    # Process request
```

### Logging
Structured logging with cluster context:
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Processing request", extra={
    "app_id": self.app_id,
    "node_id": self.node_id,
    "request_id": request.get("id"),
    "user_id": request.get("user_id")
})
```

## Example Applications

### Simple Web API
```python
from src.apps.base import ClusterApplication
from aiohttp import web

class WebAPIApp(ClusterApplication):
    async def initialize(self):
        self.app = web.Application()
        self.app.router.add_get('/api/status', self.status_handler)
        self.app.router.add_post('/api/process', self.process_handler)
        return True
        
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        return True
        
    async def health_check(self):
        return {"status": "healthy", "port": 8080}
        
    async def status_handler(self, request):
        return web.json_response({"app": self.app_id, "node": self.node_id})
        
    async def process_handler(self, request):
        data = await request.json()
        result = {"processed": True, "data": data}
        return web.json_response(result)
```

### Distributed Task Processor
```python
class TaskProcessorApp(ClusterApplication):
    async def initialize(self):
        self.task_queue = asyncio.Queue()
        self.workers = []
        return True
        
    async def start(self):
        # Start worker tasks
        for i in range(self.config.get('workers', 3)):
            worker = asyncio.create_task(self.worker_loop())
            self.workers.append(worker)
        return True
        
    async def worker_loop(self):
        while True:
            task = await self.task_queue.get()
            try:
                await self.process_task(task)
            except Exception as e:
                logger.error(f"Task processing failed: {e}")
            finally:
                self.task_queue.task_done()
                
    async def handle_request(self, request):
        if request.get('action') == 'submit_task':
            await self.task_queue.put(request['task'])
            return {"status": "queued", "queue_size": self.task_queue.qsize()}
```

## Best Practices

### Development
- Use async/await for non-blocking operations
- Implement proper error handling and retries
- Design for horizontal scaling
- Make applications stateless when possible
- Use structured logging with correlation IDs

### Deployment
- Define resource limits and requests
- Implement comprehensive health checks
- Use rolling updates for zero-downtime deployments
- Test applications in cluster environment
- Monitor application metrics and logs

### Security
- Validate all input data
- Use secure communication between services
- Implement proper authentication and authorization
- Follow principle of least privilege
- Regularly update dependencies

## Next Steps

1. **Storage Integration** - Add persistent storage support
2. **Service Mesh** - Implement inter-service communication
3. **Auto-scaling** - Dynamic scaling based on metrics
4. **CI/CD Pipeline** - Automated testing and deployment
5. **Application Marketplace** - Catalog of pre-built applications