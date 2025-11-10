# Python Clustering Software

## Overview

Distributed clustering system with leader election, application management, and auto-scaling capabilities.

## Current Implementation Status

### ✅ Phase 1: Foundation (Complete)
- Basic node communication
- Simple leader election
- Health monitoring
- Docker-based testing
- Web dashboard for cluster management
- Application lifecycle management (deploy, scale, pause, resume, stop)

### ✅ Phase 2: Basic Auto-Scaling (Complete)
- Metric-based scaling policies
- Simple threshold-based triggers
- Scaling event logging
- Dashboard policy management
- Auto-scaler service
- Container health monitoring and auto-replacement
- Persistent data storage

### ✅ Phase 3: Advanced Policies (Complete)
- Schedule-based scaling with time-based triggers
- Multi-metric scaling decisions with weighted algorithms
- Advanced cooldown and rate limiting
- Comprehensive scaling history analytics

## Quick Start

### Start the Cluster
```bash
# Start cluster nodes
python docker/scripts/cluster_manager.py start

# Start dashboard with persistent storage (RECOMMENDED)
start-dashboard.bat

# Or manually with persistent storage:
docker run -d -p 8080:80 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "%cd%/dashboard-data:/var/www/html/data" \
  -e CLUSTER_API_URL=http://host.docker.internal:8001 \
  --name cluster-dashboard cluster-dashboard:latest

# Start basic auto-scaler (Phase 2)
python scripts/start_autoscaler.py

# Or start advanced auto-scaler (Phase 3 - RECOMMENDED)
python scripts/start_advanced_autoscaler.py
```

### Access Dashboard
- **URL**: http://localhost:8080
- **Navigation Tabs**:
  - **Overview**: Cluster status and resource summary
  - **Nodes**: Individual node monitoring and details
  - **Applications**: Application lifecycle management with detailed container views
  - **Auto-Scaling**: Policy management and scaling events
  - **Metrics**: Performance monitoring
  - **Storage**: Storage information

### Deploy Applications
```bash
# Via dashboard: Click "Deploy App" button
# Or via API:
curl -X POST http://localhost:8080/api/cluster.php?action=deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-app",
    "image": "nginx:latest",
    "replicas": 2,
    "ports": [{"port": 8080}],
    "resources": {"cpu": "100m", "memory": "128Mi"}
  }'
```

### Enable Auto-Scaling

#### Via Dashboard (Recommended)
1. Navigate to **Auto-Scaling** tab
2. Click **Create Policy** button
3. Select application from dropdown
4. Configure scaling parameters:
   - Min/Max replicas
   - CPU threshold (%)
   - Memory threshold (%)
5. Click **Create Policy**

#### Via Application Tab
1. Deploy an application via dashboard
2. Click "Enable Auto" button for the application
3. Enter scaling thresholds in prompts
4. Auto-scaler will evaluate policies every 60 seconds

#### Monitor Auto-Scaling
- **Auto-Scaling Tab**: View all policies and recent events
- **Applications Tab**: See auto-scaling status badges
- **Policy Management**: Edit or delete existing policies

## Architecture

### Core Components
- **Node**: Cluster node with HTTP API and consensus
- **Dashboard**: Web interface for cluster management with persistent storage
- **Auto-Scaler**: Service for automatic scaling decisions
- **Applications**: Containerized workloads managed by cluster

### Auto-Scaling Flow
1. **Policy Creation**: Define scaling rules via dashboard
2. **Metrics Collection**: Monitor CPU/memory usage
3. **Policy Evaluation**: Auto-scaler checks thresholds every minute
4. **Scaling Actions**: Trigger scale up/down based on conditions
5. **Container Health**: Automatic replacement of failed containers
6. **Cooldown**: Prevent rapid scaling oscillations

### Persistent Storage
- **Dashboard Data**: `/dashboard-data` directory on host
- **Scaling Policies**: Preserved across container restarts
- **Scaling Events**: Historical scaling actions maintained
- **Application Metadata**: Deployment information persisted

## API Endpoints

### Cluster Management
- `GET /health` - Node health status
- `POST /vote` - Vote in leader election
- `POST /heartbeat` - Receive leader heartbeat

### Application Management
- `GET /api/cluster.php?action=applications` - List applications
- `POST /api/cluster.php?action=deploy` - Deploy application
- `POST /api/cluster.php?action=scale` - Scale application
- `POST /api/cluster.php?action=pause` - Pause application
- `POST /api/cluster.php?action=resume` - Resume application
- `POST /api/cluster.php?action=stop` - Stop application
- `GET /api/cluster.php?action=app_details&app_name=X` - Application details
- `GET /api/cluster.php?action=container_details&container_name=X` - Container details

### Auto-Scaling
- `POST /api/cluster.php?action=create_scaling_policy` - Create scaling policy
- `GET /api/cluster.php?action=get_scaling_policies` - List policies
- `GET /api/cluster.php?action=scaling_events` - View scaling history
- `POST /api/cluster.php?action=evaluate_scaling` - Trigger evaluation

## Configuration

### Auto-Scaling Policy Example
```json
{
  "application": "web-app",
  "minReplicas": 2,
  "maxReplicas": 10,
  "cpuThreshold": 70,
  "memoryThreshold": 80,
  "enabled": true
}
```

### Scaling Conditions
- **Scale Up**: CPU > threshold OR Memory > threshold
- **Scale Down**: CPU < (threshold - 20%) AND Memory < (threshold - 20%)
- **Container Replacement**: Automatic replacement of failed containers
- **Cooldown**: 5 minutes between scaling actions per application

## Monitoring

### Dashboard Features
- Real-time cluster status
- Node health and resource usage
- Application lifecycle management
- Auto-scaling policy management
- Scaling event history
- Detailed container inspection with logs

### Container Details
- **Clickable Container Names**: Access detailed container information
- **Docker Logs**: Last 50 lines of container output
- **Resource Stats**: Live CPU, memory, network, and disk I/O
- **State Information**: Container status, exit codes, and error messages

### Metrics Collected
- CPU usage percentage
- Memory usage (MB)
- Application replica counts
- Scaling events and timestamps
- Container health status

## Development

### Run Tests
```bash
pytest tests/
```

### Check Status
```bash
python docker/scripts/cluster_manager.py status
```

### View Logs
```bash
# Cluster nodes
docker logs cluster-node-1

# Dashboard
docker logs cluster-dashboard

# Auto-scaler
# Check terminal where start_autoscaler.py is running
```

### Persistent Storage Management
```bash
# View dashboard data
dir dashboard-data

# Backup dashboard settings
copy dashboard-data\*.json backup\

# Clear all dashboard data (reset)
rmdir /s dashboard-data
```

## Important Notes

### Persistent Storage
- **Always use persistent storage** for production deployments
- **Dashboard data** is stored in `dashboard-data/` directory
- **Settings persist** across container restarts and updates
- **Use start-dashboard.bat** for easy deployment with persistence

### Container Management
- **Docker socket access** required for application management
- **Failed containers** are automatically detected and replaced
- **Container details** accessible via clickable container names
- **Real-time logs** available for troubleshooting

### Auto-Scaling
- **Policies persist** across dashboard restarts
- **Container health monitoring** ensures reliability
- **Automatic replacement** maintains desired replica counts
- **Cooldown periods** prevent scaling oscillations