# Quick Start Guide (Windows)

## Prerequisites
- Docker Desktop for Windows (must be running)
- Python 3.11+ (for local development)

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
- Node 1: http://localhost:8001
- Node 2: http://localhost:8002  
- Node 3: http://localhost:8003

## Development Workflow
1. Make code changes in `src\`
2. Restart cluster to test: `python docker\scripts\cluster_manager.py restart`
3. Check logs: `docker logs cluster-node-1` (or cluster-node-2, cluster-node-3)

## Windows-Specific Notes
- Use `cmd` or PowerShell for commands (preferably as Administrator)
- File paths use backslashes (`\`)
- Ensure Docker Desktop is running before starting cluster
- If Docker commands fail, restart Docker Desktop