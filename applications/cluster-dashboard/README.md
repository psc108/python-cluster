# Cluster Dashboard Application

## Overview

The Cluster Dashboard is a web-based monitoring and management interface for the clustering system. It provides real-time visibility into cluster health, node status, application deployments, metrics, and storage usage.

## Features

- **Real-time Monitoring**: Live updates of cluster status and metrics
- **Node Management**: View node health, resource usage, and roles
- **Application Management**: Monitor and manage deployed applications
- **Metrics Visualization**: Performance metrics and charts
- **Storage Monitoring**: Volume usage and storage class information
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **Web Server**: Apache HTTP Server
- **Backend**: PHP 8.2
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Container**: Docker with Debian 12 base image

## Application Structure

```
cluster-dashboard/
├── app.yaml              # Application definition
├── Dockerfile           # Container definition
├── apache.conf          # Apache configuration
├── src/                 # Application source code
│   ├── index.php       # Main dashboard page
│   ├── health.php      # Health check endpoint
│   ├── api/            # API endpoints
│   │   └── cluster.php # Cluster data API
│   └── assets/         # Static assets
│       ├── css/
│       │   └── dashboard.css
│       └── js/
│           └── dashboard.js
└── README.md           # This file
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

# Run locally for testing
docker run -d -p 8080:80 \
  -e CLUSTER_API_URL=http://localhost:8001 \
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

## API Endpoints

### Health Check
- **GET** `/health.php`
- Returns application health status in JSON format
- Used by the application framework for health monitoring

### Cluster API
- **GET** `/api/cluster.php?action=status` - Cluster status
- **GET** `/api/cluster.php?action=nodes` - Node information
- **GET** `/api/cluster.php?action=applications` - Application list
- **GET** `/api/cluster.php?action=metrics` - Performance metrics
- **GET** `/api/cluster.php?action=storage` - Storage information

## Dashboard Features

### Overview Tab
- Cluster health status
- Node count and health
- Application summary
- Resource usage (CPU, Memory)

### Nodes Tab
- List of all cluster nodes
- Node status (healthy/unhealthy)
- Node roles (leader/follower)
- Resource utilization per node
- Node uptime information

### Applications Tab
- Deployed applications list
- Application status and health
- Replica counts and scaling
- Resource usage per application
- Application management actions

### Metrics Tab
- Real-time performance metrics
- Request rate and response times
- Error rates and throughput
- Visual charts and graphs

### Storage Tab
- Storage capacity and usage
- Volume information
- Storage classes and types
- Mount paths and status

## Monitoring and Alerting

### Health Checks
The dashboard implements comprehensive health checks:
- Web server status
- File system accessibility
- Cluster connectivity
- Application metrics

### Metrics Collection
- Request rate monitoring
- Response time tracking
- Error rate calculation
- Resource usage monitoring

## Security Features

- **HTTP Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- **Input Validation**: All user inputs are validated and sanitized
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **Error Handling**: Secure error messages without sensitive information

## Performance Optimization

- **Compression**: Gzip compression for static assets
- **Caching**: Browser caching for CSS and JavaScript files
- **Efficient Queries**: Optimized API calls with timeouts
- **Responsive Design**: Mobile-optimized interface

## Development

### Local Development Setup

1. **Prerequisites**:
   - Docker Desktop
   - Running cluster (for API connectivity)

2. **Build and Run**:
   ```bash
   docker build -t cluster-dashboard:dev .
   docker run -p 8080:80 -e CLUSTER_API_URL=http://localhost:8001 cluster-dashboard:dev
   ```

3. **Access Dashboard**:
   - Open http://localhost:8080 in your browser

### Customization

#### Adding New Metrics
1. Update `api/cluster.php` to fetch new metrics
2. Modify `assets/js/dashboard.js` to display new data
3. Update `assets/css/dashboard.css` for styling

#### Adding New Tabs
1. Add tab button in `index.php`
2. Create tab content section
3. Implement refresh function in JavaScript
4. Add corresponding API endpoint

## Troubleshooting

### Common Issues

1. **Dashboard Not Loading**:
   - Check if Apache is running: `docker logs <container-id>`
   - Verify port mapping: `docker ps`

2. **No Cluster Data**:
   - Check `CLUSTER_API_URL` environment variable
   - Verify cluster nodes are accessible
   - Check network connectivity

3. **Health Check Failing**:
   - Ensure `/var/www/html/data` is writable
   - Check cluster connectivity
   - Review Apache error logs

### Logs

- **Apache Access Log**: `/var/log/apache2/dashboard_access.log`
- **Apache Error Log**: `/var/log/apache2/dashboard_error.log`
- **Application Data**: `/var/www/html/data/`

## Integration with Cluster Framework

### Application Framework Compliance
- Implements required health check endpoint
- Follows application definition schema
- Supports scaling and lifecycle management
- Provides proper metrics for monitoring

### Storage Integration
- Uses persistent volumes for data storage
- Supports different storage classes
- Implements backup and recovery procedures

### Auto-Scaling Support
- Provides custom metrics for scaling decisions
- Handles graceful scaling up and down
- Supports load balancing across replicas

## Future Enhancements

- **Real-time WebSocket Updates**: Live data streaming
- **Advanced Charts**: Interactive graphs with Chart.js
- **User Authentication**: Login and role-based access
- **Application Deployment**: GUI for deploying new applications
- **Log Aggregation**: Centralized log viewing
- **Alerting System**: Email/SMS notifications for issues