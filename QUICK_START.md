# Quick Start Guide (Windows)

## Overview
This clustering system provides a complete distributed computing solution with three phases of functionality:
- **Phase 1**: Basic clustering with leader election and health monitoring
- **Phase 2**: Advanced consensus (Raft), fault tolerance, and reliable messaging
- **Phase 3**: Production features with TLS security, authentication, monitoring, and management APIs

## Prerequisites
- Docker Desktop for Windows (must be running)
- Python 3.11+ (for local development)
- All dependencies installed: `pip install -r requirements.txt`

## Troubleshooting

### Docker Issues
1. **Start Docker Desktop**: Ensure Docker Desktop is running (check system tray)
2. **Run as Administrator**: If you get permission errors, run PowerShell/CMD as Administrator
3. **Test Docker**: Run `docker --version` to verify Docker is working

### Quick Docker Test
```cmd
# Test if Docker is working
docker --version
docker run hello-world
```

## Automated Cluster Management

### Start the Cluster
```cmd
python docker\scripts\cluster_manager.py start
```

### Check Cluster Status
```cmd
python docker\scripts\cluster_manager.py status
```

### Stop the Cluster
```cmd
python docker\scripts\cluster_manager.py stop
```

### Restart the Cluster
```cmd
python docker\scripts\cluster_manager.py restart
```

## Phase 1 Features (Basic Clustering)

### Health Monitoring
```cmd
# Check individual node health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### Leader Election
- Automatic leader election on startup
- Leader sends heartbeats to followers
- Re-election on leader failure

## Phase 2 Features (Advanced Consensus)

### Raft Consensus
- Distributed log replication
- Strong consistency guarantees
- Automatic failover and recovery

### Fault Tolerance Testing
```cmd
# Stop a follower node (cluster remains operational)
docker stop cluster-node-2

# Stop leader node (triggers re-election)
docker stop cluster-node-1

# Restart nodes
docker start cluster-node-1 cluster-node-2
```

### Reliable Messaging
- Guaranteed message delivery
- Automatic retry with exponential backoff
- Message ordering and deduplication

## Phase 3 Features (Production Ready)

### Security (TLS + Authentication)
```cmd
# All inter-node communication is encrypted with TLS
# API endpoints require authentication tokens
# Self-signed certificates generated automatically
```

### REST API Management
```cmd
# Access cluster management API (requires auth token)
curl -H "Authorization: Bearer <token>" http://localhost:8001/api/cluster/status
curl -H "Authorization: Bearer <token>" http://localhost:8001/api/nodes
curl -H "Authorization: Bearer <token>" http://localhost:8001/api/metrics
```

### CLI Tools
```cmd
# Use CLI for cluster management
python -m src.api.cli cluster status
python -m src.api.cli node list
python -m src.api.cli metrics show
```

### Monitoring & Metrics
```cmd
# Prometheus metrics available at:
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics
curl http://localhost:8003/metrics

# Metrics include:
# - System metrics (CPU, memory, disk, network)
# - Cluster metrics (heartbeats, elections, votes)
# - Node-specific performance data
# - Python runtime metrics
```

### Configuration Management
```cmd
# YAML-based configuration
# Environment variable overrides
# Runtime configuration updates
```

## Manual Docker Commands (Alternative)

### Start
```cmd
# Build image
docker build -f docker/Dockerfile -t cluster-node .

# Create network
docker network create cluster-net

# Start nodes
docker run -d --name cluster-node-1 --network cluster-net -p 8001:8000 -e NODE_ID=1 -e NODE_PORT=8000 -e CLUSTER_SIZE=3 -e CLUSTER_NODES=cluster-node-1:8000,cluster-node-2:8000,cluster-node-3:8000 cluster-node
docker run -d --name cluster-node-2 --network cluster-net -p 8002:8000 -e NODE_ID=2 -e NODE_PORT=8000 -e CLUSTER_SIZE=3 -e CLUSTER_NODES=cluster-node-1:8000,cluster-node-2:8000,cluster-node-3:8000 cluster-node
docker run -d --name cluster-node-3 --network cluster-net -p 8003:8000 -e NODE_ID=3 -e NODE_PORT=8000 -e CLUSTER_SIZE=3 -e CLUSTER_NODES=cluster-node-1:8000,cluster-node-2:8000,cluster-node-3:8000 cluster-node
```

### Stop
```cmd
docker stop cluster-node-1 cluster-node-2 cluster-node-3
docker rm cluster-node-1 cluster-node-2 cluster-node-3
docker network rm cluster-net
```

## Accessing Nodes
- Node 1: http://localhost:8001 (typically leader)
- Node 2: http://localhost:8002 (follower)
- Node 3: http://localhost:8003 (follower)

### Available Endpoints
- `GET /health` - Node health status
- `POST /vote` - Participate in leader election
- `POST /heartbeat` - Receive leader heartbeat
- `GET /metrics` - Prometheus metrics (Phase 3)
- `GET /api/*` - REST API endpoints (Phase 3, requires auth)

## Development Workflow
1. Make code changes in `src\`
2. Restart cluster to test: `python docker\scripts\cluster_manager.py restart`
3. Check logs: `docker logs cluster-node-1` (or cluster-node-2, cluster-node-3)
4. Run tests: `pytest tests/` (36 tests covering all phases)
5. Monitor metrics: Check Prometheus endpoints for performance data

## Testing

### Run All Tests
```cmd
pytest tests/ -v
```

### Run Phase-Specific Tests
```cmd
# Phase 1 tests (5 tests)
pytest tests/test_phase1.py -v

# Phase 2 tests (18 tests)
pytest tests/test_phase2.py -v

# Phase 3 tests (13 tests)
pytest tests/test_phase3.py -v
```

### Success Criteria Verification
```cmd
# Verify all phase requirements are met
pytest tests/test_phase1_success_criteria.py -v
pytest tests/test_phase2_success_criteria.py -v
pytest tests/test_phase3_success_criteria.py -v
```

## Windows-Specific Notes
- Use `cmd` or PowerShell for commands (preferably as Administrator)
- File paths use backslashes (`\`)
- Ensure Docker Desktop is running before starting cluster
- If Docker commands fail, restart Docker Desktop