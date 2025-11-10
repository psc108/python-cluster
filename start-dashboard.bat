@echo off
echo Starting Cluster Dashboard with Persistent Storage...

REM Create data directory if it doesn't exist
if not exist "dashboard-data" mkdir dashboard-data

REM Stop and remove existing container
docker stop cluster-dashboard 2>nul
docker rm cluster-dashboard 2>nul

REM Start dashboard with persistent data volume
docker run -d -p 8080:80 ^
  -v /var/run/docker.sock:/var/run/docker.sock ^
  -v "%cd%/dashboard-data:/var/www/html/data" ^
  -e CLUSTER_API_URL=http://host.docker.internal:8001 ^
  -e LOG_LEVEL=INFO ^
  -e CLUSTER_MODE=true ^
  --health-cmd="curl -f http://localhost/health.php || exit 1" ^
  --health-interval=30s ^
  --health-timeout=10s ^
  --health-retries=3 ^
  --name cluster-dashboard ^
  cluster-dashboard:latest

echo Dashboard started with persistent storage at: %cd%\dashboard-data
echo Access dashboard at: http://localhost:8080