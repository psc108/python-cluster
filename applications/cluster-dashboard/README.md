# Cluster Dashboard Application

## Overview

The Cluster Dashboard is a comprehensive web-based monitoring and management interface for the clustering system. It provides real-time visibility into cluster health, node status, application deployments, metrics, and storage usage with full application lifecycle management capabilities.

## Features

- **Real-time Monitoring**: Live updates of cluster status and metrics with 5-second refresh
- **Node Management**: View node health, resource usage, roles, and detailed information
- **Complete Application Lifecycle**: Deploy, scale, pause, resume, and stop applications
- **Modal-based Deployment**: User-friendly deployment interface with form validation
- **Application State Management**: Track running, paused, and stopped applications
- **Dynamic Port Allocation**: Automatic port assignment to prevent conflicts
- **Metrics Visualization**: Performance metrics and charts with real-time data
- **Storage Monitoring**: Volume usage and storage class information
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Docker Integration**: Direct Docker container management with socket access

## Technology Stack

- **Web Server**: Apache HTTP Server with mod_rewrite and compression
- **Backend**: PHP 8.2 with Docker CLI integration
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla) with modal interfaces
- **Container**: Docker with Debian 12 base image and Docker socket access
- **Container Management**: Direct Docker API integration via socket
- **Styling**: Custom CSS with responsive design and status indicators
- **Data Storage**: File-based persistence with JSON APIs

## Application Structure

```
cluster-dashboard/
├── app.yaml              # Application definition
├── Dockerfile           # Container definition with Docker CLI
├── apache.conf          # Apache configuration
├── src/                 # Application source code
│   ├── index.php       # Main dashboard with modal interfaces
│   ├── health.php      # Health check endpoint
│   ├── api/            # API endpoints
│   │   └── cluster.php # Complete cluster management API
│   └── assets/         # Static assets
│       ├── css/
│       │   └── dashboard.css # Enhanced styling with modals
│       └── js/
│           └── dashboard.js  # Full application management
└── README.md           # This comprehensive guide
```

## Deployment

### Using Application Framework CLI

**Note**: Run these commands from the cluster root directory, not from within the application directory.

```bash
# From cluster root directory (c:\Users\pscott32\IdeaProjects\cluster)
python -m src.apps.cli deploy applications/cluster-dashboard/

# Check deployment status
python -m src.apps.cli status cluster-dashboard

# Scale the application
python -m src.apps.cli scale cluster-dashboard --replicas 3

# View application logs
python -m src.apps.cli logs cluster-dashboard
```

### Manual Docker Build

```bash
# Build from cluster root directory
cd c:\Users\pscott32\IdeaProjects\cluster
docker build -f applications/cluster-dashboard/Dockerfile -t cluster-dashboard:latest applications/cluster-dashboard/

# Or build from application directory
cd applications/cluster-dashboard
docker build -t cluster-dashboard:latest .

# Run with Docker socket access (REQUIRED for app management)
docker run -d -p 8080:80 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e CLUSTER_API_URL=http://host.docker.internal:8001 \
  -e LOG_LEVEL=INFO \
  -e CLUSTER_MODE=true \
  --health-cmd="curl -f http://localhost/health.php || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  --name dashboard-accurate \
  cluster-dashboard:latest

# Access the dashboard
# Open http://localhost:8080 in your browser
```

## Configuration

### Environment Variables

- `CLUSTER_API_URL`: URL of the cluster API endpoint (default: http://cluster-node-1:8000)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)
- `CLUSTER_MODE`: Set to "true" when running in cluster

### Volume Mounts

- `/var/www/html/data`: Persistent storage for dashboard data and logs
- `/var/run/docker.sock`: **REQUIRED** - Docker socket for container management

### Important Notes

- **Docker Socket Access**: The dashboard MUST have access to the Docker socket to deploy, pause, resume, and stop applications
- **Host Network**: Use `host.docker.internal` for cluster API URL when running in Docker
- **Port Range**: Applications are deployed on ports starting from 10000 to avoid conflicts
- **Memory Information**: The dashboard shows Docker's allocated memory, not total system memory. On Docker Desktop, this is typically 50% of system RAM (e.g., 24GB shown on a 48GB system). This is the correct and relevant memory available for container deployments.

## API Endpoints

### Health Check
- **GET** `/health.php`
- Returns application health status in JSON format
- Used by the application framework for health monitoring

### Cluster API
- **GET** `/api/cluster.php?action=status` - Cluster status
- **GET** `/api/cluster.php?action=nodes` - Node information
- **GET** `/api/cluster.php?action=applications` - Application list with status
- **GET** `/api/cluster.php?action=metrics` - Performance metrics
- **GET** `/api/cluster.php?action=storage` - Storage information
- **GET** `/api/cluster.php?action=node_details&node_id=X` - Detailed node information

### Application Management API
- **POST** `/api/cluster.php?action=deploy` - Deploy new application
- **POST** `/api/cluster.php?action=scale` - Scale application replicas
- **POST** `/api/cluster.php?action=pause` - Pause application (stop containers)
- **POST** `/api/cluster.php?action=resume` - Resume paused application
- **POST** `/api/cluster.php?action=stop` - Stop and remove application

## Dashboard Features

### Overview Tab
- **Cluster Health**: Real-time cluster status indicator
- **Node Summary**: Total and healthy node counts
- **Application Summary**: Running, failed, and total instance counts
- **Resource Usage**: Cluster-wide CPU and memory utilization with progress bars
- **Leader Information**: Current cluster leader identification
- **Uptime Tracking**: Cluster uptime monitoring

### Nodes Tab
- **Node List**: Complete list of all cluster nodes
- **Health Status**: Real-time node health monitoring (healthy/unhealthy)
- **Role Display**: Node roles (leader/follower) with visual indicators
- **Resource Metrics**: Per-node CPU and memory utilization
- **Uptime Information**: Individual node uptime tracking
- **Detailed View**: Click "Details" for comprehensive node information modal
- **Network Information**: Node ports, health endpoints, and connectivity

### Applications Tab
- **Deploy Applications**: Modal-based deployment with comprehensive form
  - Application name and Docker image selection
  - Replica count configuration
  - Port and resource limit settings
  - Form validation and error handling
- **Application Status**: Visual status badges (running/paused/stopped)
- **Lifecycle Management**: Full application lifecycle control
  - **Deploy**: Create new applications from Docker images
  - **Scale**: Adjust replica counts for running applications
  - **Pause**: Stop containers without removing them (preserves deployment)
  - **Resume**: Restart paused applications
  - **Stop**: Permanently remove applications and containers
- **Resource Monitoring**: Real-time CPU and memory usage per application
- **Port Information**: Automatic port allocation starting from 10000
- **Replica Status**: Current vs desired replica counts (e.g., "1/1")

### Metrics Tab
- **Performance Metrics**: Real-time cluster performance data
- **Request Rate**: Requests per second across the cluster
- **Response Time**: Average response times in milliseconds
- **Error Rate**: Error percentage tracking
- **Throughput**: Data throughput in MB/s
- **Visual Charts**: Simple bar chart visualization of key metrics
- **Auto-refresh**: Metrics update every 5 seconds

### Storage Tab
- **Storage Summary**: Total, used, and available storage capacity
- **Volume List**: Detailed volume information table
- **Storage Classes**: Different storage class types and usage
- **Mount Paths**: Volume mount points and accessibility
- **Status Monitoring**: Volume health and availability status

## Application Management Guide

### Deploying Applications

1. **Access Deployment**:
   - Navigate to the "Applications" tab
   - Click the "Deploy App" button
   - A modal dialog will open with deployment form and resource information

2. **Review Resource Information**:
   - **Used Ports**: Shows currently occupied ports to avoid conflicts
   - **Memory Usage**: Displays Docker's allocated memory (not total system memory)
     - Total: Memory allocated to Docker (e.g., 24GB on Docker Desktop)
     - Used: Current memory consumption by containers
     - Available: Memory available for new deployments
   - **Note**: Memory shown is Docker's allocation, typically 50% of system RAM

3. **Fill Deployment Form**:
   - **Application Name**: Unique name for your application (required)
   - **Docker Image**: Full image name (e.g., `nginx:latest`, `redis:alpine`) (required)
   - **Replicas**: Number of container instances (default: 1) (required)
   - **Port**: Application port inside container (default: 8080) (required)
   - **CPU Limit**: Resource limit (e.g., `100m`, `1`) (optional, default: 100m)
   - **Memory Limit**: Memory limit (e.g., `128Mi`, `1Gi`) (optional, default: 128Mi)
   - **Resource Planning**: Use the displayed memory information to set appropriate limits

4. **Deploy**:
   - Click "Deploy" to create the application
   - Click "Cancel" to close without deploying
   - Form validation ensures all required fields are filled

5. **Deployment Process**:
   - Docker image is pulled automaticallyy
   - Containers are created with unique names (`app-{name}-{instance}`)
   - Ports are automatically allocated starting from 10000
   - Application appears in the list with "running" status

### Managing Application Lifecycle

#### Application States
- **Running**: Containers are active and serving traffic
- **Paused**: Containers are stopped but preserved (can be resumed)
- **Stopped**: Containers are removed (requires redeployment)

#### Available Actions by State

**Running Applications**:
- **Scale**: Change the number of replicas
- **Pause**: Stop containers without removing them
- **Stop**: Permanently remove the application

**Paused Applications**:
- **Resume**: Restart the stopped containers
- **Stop**: Permanently remove the application

**Stopped Applications**:
- **Stop**: Remove any remaining artifacts

#### Action Details

**Scaling Applications**:
1. Click "Scale" button for a running application
2. Enter the desired number of replicas
3. New containers will be created or excess ones removed
4. Each replica gets a unique port assignment

**Pausing Applications**:
1. Click "Pause" button for a running application
2. Confirm the action in the dialog
3. Containers are stopped but not removed
4. Status changes to "paused"
5. Resources are freed but deployment is preserved

**Resuming Applications**:
1. Click "Resume" button for a paused application
2. Stopped containers are restarted
3. Original port assignments are restored
4. Status changes back to "running"

**Stopping Applications**:
1. Click "Stop" button for any application
2. Confirm the permanent removal
3. All containers are stopped and removed
4. Application disappears from the list
5. Requires redeployment to restore

### Port Management

- **Automatic Allocation**: Ports are assigned automatically starting from 10000
- **Conflict Prevention**: System checks for used ports and assigns next available
- **External Access**: Applications are accessible via `localhost:{assigned-port}`
- **Port Persistence**: Paused applications retain their port assignments when resumed

## User Interface Guide

### Navigation
- **Tab-based Interface**: Click tabs to switch between different views
- **Auto-refresh**: Data refreshes every 5 seconds automatically
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modal Dialogs**: Deployment and node details use modal overlays

### Keyboard Shortcuts
- **Escape**: Close any open modal dialog
- **Click Outside**: Click outside modals to close them

### Status Indicators
- **Green Dot**: Healthy/Running status
- **Orange Dot**: Degraded/Paused status  
- **Red Dot**: Unhealthy/Stopped status
- **Pulsing Animation**: Indicates active monitoring

### Button Colors and Meanings
- **Blue (Primary)**: Main actions (Deploy, Refresh)
- **Gray (Secondary)**: Secondary actions (Scale, Details)
- **Green (Success)**: Positive actions (Resume)
- **Orange (Warning)**: Caution actions (Pause)
- **Red (Danger)**: Destructive actions (Stop)

## Development

### Local Development Setup

1. **Prerequisites**:
   - Docker Desktop with Docker socket access
   - Running cluster nodes (for API connectivity)
   - Ports 8080 and 10000+ available

2. **Build and Run**:
   ```bash
   # Build the image
   docker build -t cluster-dashboard:dev .
   
   # Run with full capabilities
   docker run -d -p 8080:80 \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -e CLUSTER_API_URL=http://host.docker.internal:8001 \
     -e LOG_LEVEL=DEBUG \
     --name dashboard-dev \
     cluster-dashboard:dev
   ```

3. **Access Dashboard**:
   - Open http://localhost:8080 in your browser
   - Verify cluster connectivity in Overview tab
   - Test application deployment functionality

### Customization

#### Adding New Metrics
1. Update `api/cluster.php` to fetch new metrics from cluster nodes
2. Modify `assets/js/dashboard.js` to display new data in UI
3. Update `assets/css/dashboard.css` for styling new elements
4. Add metric parsing in `parsePrometheusMetrics()` function

#### Adding New Application Actions
1. Add new case in `cluster.php` switch statement
2. Implement handler function (e.g., `handleNewAction()`)
3. Add JavaScript function in `dashboard.js`
4. Update UI in `refreshApplications()` to show new buttons
5. Add CSS styling for new button types

#### Adding New Tabs
1. Add tab button in `index.php` navigation
2. Create tab content section with unique ID
3. Implement refresh function in JavaScript
4. Add corresponding API endpoint in `cluster.php`
5. Update `showTab()` function to handle new tab

#### Extending Modal Functionality
1. Add new modal HTML structure in `index.php`
2. Implement show/hide functions in JavaScript
3. Add form validation and submission logic
4. Update click-outside and ESC key handling
5. Style modal with CSS classes

## Troubleshooting

### Common Issues

1. **Dashboard Not Loading / Connection Refused**:
   ```bash
   # Check if container is running
   docker ps | grep dashboard
   
   # Check container logs
   docker logs dashboard-accurate
   
   # Verify port mapping
   docker port dashboard-accurate
   
   # Test container health
   docker exec dashboard-accurate curl -f http://localhost/health.php
   
   # Check if Apache is running inside container
   docker exec dashboard-accurate ps aux | grep apache
   ```

2. **Application Deployment Fails**:
   ```bash
   # Check Docker socket access
   docker exec dashboard-accurate sudo docker ps
   
   # Verify Docker daemon is accessible
   docker exec dashboard-accurate sudo docker version
   
   # Check deployment logs
   docker exec dashboard-accurate cat /var/www/html/data/operations.log
   
   # Test manual deployment
   curl -X POST -H "Content-Type: application/json" \
     -d '{"name":"test","image":"nginx:latest","replicas":1,"ports":[{"port":80}]}' \
     http://localhost:8080/api/cluster.php?action=deploy
   ```

3. **Deploy Modal Shows Success But No App Appears**:
   - **Cause**: Dashboard container lacks Docker socket access
   - **Solution**: Restart with `-v /var/run/docker.sock:/var/run/docker.sock`
   - **Verification**: Check if containers were actually created:
     ```bash
     docker ps -a | grep app-
     ```

4. **Port Conflicts During Deployment**:
   - **Cause**: Requested port already in use
   - **Solution**: System automatically assigns ports starting from 10000
   - **Check**: View assigned ports in application list or:
     ```bash
     docker ps --format "table {{.Names}}\t{{.Ports}}"
     ```

5. **Applications Show as Paused After Restart**:
   - **Cause**: Docker containers stopped but not removed
   - **Solution**: Use "Resume" button to restart containers
   - **Alternative**: Use "Stop" to fully remove, then redeploy

6. **No Cluster Data Showing**:
   - Check `CLUSTER_API_URL` environment variable
   - Verify cluster nodes are running and accessible
   - Test cluster endpoints manually:
     ```bash
     curl http://localhost:8001/health
     curl http://localhost:8002/health
     curl http://localhost:8003/health
     ```
   - Check network connectivity between dashboard and cluster

7. **Modal Dialogs Not Working**:
   - **Cause**: JavaScript errors or CSS conflicts
   - **Debug**: Open browser developer tools (F12)
   - **Check**: Console for JavaScript errors
   - **Solution**: Refresh page or clear browser cache

8. **Memory Information Shows Less Than Expected**:
   - **Expected Behavior**: Dashboard shows Docker's allocated memory, not total system memory
   - **Docker Desktop**: Typically allocates 50% of system RAM (e.g., 24GB on 48GB system)
   - **Verification**: Check Docker Desktop settings or run:
     ```bash
     docker system info | grep "Total Memory"
     ```
   - **Adjustment**: Increase Docker's memory allocation in Docker Desktop settings if needed

9. **Health Check Failing**:
   - Ensure `/var/www/html/data` is writable
   - Check cluster connectivity
   - Review Apache error logs:
     ```bash
     docker exec dashboard-accurate tail -f /var/log/apache2/error.log
     ```
   - Test health endpoint:
     ```bash
     curl http://localhost:8080/health.php
     ```

### Debugging Commands

```bash
# Check dashboard container status
docker ps -a | grep dashboard

# View dashboard logs
docker logs dashboard-accurate --tail 50

# Access dashboard container shell
docker exec -it dashboard-accurate /bin/bash

# Check Apache status inside container
docker exec dashboard-accurate service apache2 status

# Test health endpoint
curl http://localhost:8080/health.php

# Check deployed applications
curl http://localhost:8080/api/cluster.php?action=applications

# Test Docker access from dashboard
docker exec dashboard-accurate sudo docker ps

# Check port bindings
docker port dashboard-accurate
netstat -an | findstr :8080

# View application deployment logs
docker exec dashboard-accurate cat /var/www/html/data/operations.log

# Check all app containers
docker ps -a --filter "name=app-"

# Monitor real-time logs
docker logs -f dashboard-accurate
```

### Log Files and Locations

- **Apache Access Log**: `/var/log/apache2/dashboard_access.log`
- **Apache Error Log**: `/var/log/apache2/dashboard_error.log`
- **Application Operations**: `/var/www/html/data/operations.log`
- **Cluster Uptime**: `/var/www/html/data/cluster_uptime.txt`
- **Node Start Times**: `/var/www/html/data/node_X_start.txt`
- **Application Data**: `/var/www/html/data/apps/{app-name}/`
- **Docker Container Logs**: `docker logs <container-name>`

### Log Analysis

```bash
# View recent operations
docker exec dashboard-accurate tail -20 /var/www/html/data/operations.log

# Monitor Apache errors
docker exec dashboard-accurate tail -f /var/log/apache2/error.log

# Check application deployment artifacts
docker exec dashboard-accurate ls -la /var/www/html/data/apps/

# View specific application data
docker exec dashboard-accurate cat /var/www/html/data/apps/{app-name}/app.yaml
```

## Integration with Cluster Framework

### Application Framework Compliance
- Implements required health check endpoint (`/health.php`)
- Follows application definition schema with `app.yaml` generation
- Supports complete lifecycle management (deploy/scale/pause/resume/stop)
- Provides comprehensive metrics for monitoring and alerting
- Generates Docker containers with proper naming conventions

### Docker Integration
- **Direct Docker API Access**: Uses Docker socket for container management
- **Container Lifecycle**: Full control over container start/stop/remove operations
- **Image Management**: Automatic Docker image pulling and caching
- **Port Management**: Dynamic port allocation and conflict resolution
- **Resource Limits**: Supports CPU and memory limit configuration

### Storage Integration
- Uses persistent volumes for dashboard data and logs
- Stores application deployment configurations
- Maintains operation logs and audit trails
- Supports different storage classes and volume types
- Implements data persistence across container restarts

### Auto-Scaling Support
- Provides custom metrics for scaling decisions
- Handles graceful scaling up and down of application replicas
- Supports load balancing across multiple container instances
- Monitors resource usage for scaling recommendations
- Maintains replica count consistency during scaling operations

## API Reference

### Application Management Endpoints

#### Deploy Application
```bash
POST /api/cluster.php?action=deploy
Content-Type: application/json

{
  "name": "my-app",
  "image": "nginx:latest",
  "replicas": 2,
  "ports": [{"name": "http", "port": 80}],
  "resources": {"cpu": "200m", "memory": "256Mi"}
}
```

#### Scale Application
```bash
POST /api/cluster.php?action=scale
Content-Type: application/json

{"application": "my-app", "replicas": 3}
```

#### Pause Application
```bash
POST /api/cluster.php?action=pause
Content-Type: application/json

{"application": "my-app"}
```

#### Resume Application
```bash
POST /api/cluster.php?action=resume
Content-Type: application/json

{"application": "my-app"}
```

#### Stop Application
```bash
POST /api/cluster.php?action=stop
Content-Type: application/json

{"application": "my-app"}
```

### Query Endpoints

#### Get Applications
```bash
GET /api/cluster.php?action=applications

Response:
[
  {
    "name": "my-app",
    "status": "running",
    "replicas": "2/2",
    "version": "1.0.0",
    "cpu_percent": 15,
    "memory_mb": 128,
    "uptime": "5m"
  }
]
```

#### Get Cluster Status
```bash
GET /api/cluster.php?action=status

Response:
{
  "leader_id": 1,
  "total_nodes": 3,
  "healthy_nodes": 3,
  "cluster_status": "healthy",
  "uptime": 3600
}
```

## Best Practices

### Application Deployment
- Use specific image tags instead of `latest` for production
- Set appropriate resource limits to prevent resource exhaustion
- Use meaningful application names for easier management
- Test applications locally before deploying to cluster
- Monitor application logs after deployment

### Resource Management
- **Memory Limits**: Use the deployment modal's memory information to set appropriate limits
- **Docker Memory**: Remember that displayed memory is Docker's allocation, not total system memory
- **Conservative Limits**: Start with conservative resource limits and adjust based on monitoring
- **Pause/Resume**: Use pause/resume for temporary resource savings
- **Scaling**: Scale applications based on actual usage patterns
- **Monitoring**: Monitor cluster resource usage in Overview tab

### Operational Practices
- Regularly check application status and health
- Use the pause feature for maintenance windows
- Keep deployment configurations documented
- Monitor operation logs for deployment issues
- Test disaster recovery procedures

## Security Considerations

### Container Security
- Dashboard requires Docker socket access (high privilege)
- Applications run with default Docker security settings
- Network isolation between applications is limited
- Consider using Docker security scanning for images

### Access Control
- Dashboard currently has no authentication
- Anyone with access can deploy/manage applications
- Consider implementing authentication for production use
- Restrict network access to dashboard port (8080)

### Data Protection
- Application data is stored in container volumes
- No automatic backup of application data
- Consider implementing backup strategies for critical applications
- Monitor disk usage to prevent storage exhaustion

## Future Enhancements

### Planned Features
- **Real-time WebSocket Updates**: Live data streaming without page refresh
- **Advanced Charts**: Interactive graphs with Chart.js or D3.js
- **User Authentication**: Login system with role-based access control
- **Log Aggregation**: Centralized log viewing for all applications
- **Alerting System**: Email/SMS notifications for critical issues
- **Backup Management**: Automated backup and restore capabilities
- **Resource Quotas**: Per-application resource limits and quotas
- **Network Policies**: Application-level network isolation
- **Health Checks**: Custom health check configuration per application
- **Rolling Updates**: Zero-downtime application updates

### Integration Opportunities
- **Kubernetes Integration**: Support for Kubernetes deployments
- **CI/CD Integration**: Webhook support for automated deployments
- **Monitoring Integration**: Prometheus/Grafana integration
- **Service Discovery**: Automatic service registration and discovery
- **Load Balancing**: Built-in load balancer configuration