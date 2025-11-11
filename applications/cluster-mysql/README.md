# MySQL Cluster Application

## Overview

Docker-based MySQL 8.0.35 cluster with master-slave replication, persistent storage, and automatic failover capabilities. Designed for high availability and data consistency in distributed environments.

## Architecture

### Cluster Topology
- **1 Master Node**: Handles all write operations
- **2 Slave Nodes**: Handle read operations and provide redundancy
- **GTID Replication**: Global Transaction Identifier for consistent replication
- **Persistent Storage**: Data persists across container restarts

### Components
- **mysql-master**: Primary database server (port 13306)
- **mysql-slave-1**: First replica server (port 13307)
- **mysql-slave-2**: Second replica server (port 13308)
- **cluster-manager.py**: Python service for cluster monitoring and management

## Quick Start

### Deploy Cluster
```bash
# Build and start MySQL cluster
docker-compose up -d

# Wait for initialization (30-60 seconds)
docker-compose logs -f mysql-master

# Setup replication
python scripts/setup-replication.py

# Verify cluster status
python scripts/cluster-manager.py status
```

### Connect to Database
```bash
# Connect to master (read/write)
mysql -h localhost -P 13306 -u cluster_user -p cluster_db

# Connect to slave (read-only)
mysql -h localhost -P 13307 -u cluster_user -p cluster_db
```

## Configuration

### Database Credentials
- **Root Password**: `cluster_root_pass`
- **Application User**: `cluster_user` / `cluster_pass`
- **Replication User**: `repl_user` / `repl_pass`
- **Monitor User**: `cluster_monitor` / `monitor_pass`

### Ports
- **Master**: 13306 (MySQL), 13360 (MySQL X)
- **Slave 1**: 13307 (MySQL), 13361 (MySQL X)
- **Slave 2**: 13308 (MySQL), 13362 (MySQL X)

### Storage
- **Master Data**: `mysql-master-data` volume
- **Slave 1 Data**: `mysql-slave1-data` volume
- **Slave 2 Data**: `mysql-slave2-data` volume
- **Logs**: `mysql-logs` volume (shared)

## Management Commands

### Cluster Status
```bash
python scripts/cluster-manager.py status
```

### Manual Failover
```bash
# Promote slave-1 to master
python scripts/cluster-manager.py failover mysql-slave-1
```

### Health Monitoring
```bash
# Check individual container health
docker exec mysql-master /usr/local/bin/health-check.sh

# View replication status
docker exec mysql-slave-1 mysql -u cluster_monitor -pmonitor_pass -e "SHOW SLAVE STATUS\G"
```

## API Integration

### Cluster Status Endpoint
```python
from scripts.cluster_manager import MySQLClusterManager

manager = MySQLClusterManager()
status = manager.get_cluster_status()

# Returns:
{
  "cluster_name": "mysql-cluster",
  "nodes": [
    {
      "name": "mysql-master",
      "status": "healthy",
      "role": "master",
      "uptime": "2h 15m",
      "mysql_status": "connected"
    }
  ],
  "replication_status": "healthy",
  "total_nodes": 3,
  "healthy_nodes": 3
}
```

### Dashboard Integration
```javascript
// Add to cluster dashboard
async function getMySQLClusterStatus() {
    const response = await fetch('/api/mysql/status');
    return response.json();
}
```

## Performance Tuning

### Configuration Highlights
- **InnoDB Buffer Pool**: 512MB (adjust based on available memory)
- **Binary Logging**: ROW format for consistent replication
- **GTID Mode**: Enabled for simplified failover
- **Connection Limit**: 200 concurrent connections
- **Query Cache**: Disabled (deprecated in MySQL 8.0)

### Monitoring Metrics
- **Replication Lag**: < 10 seconds (healthy)
- **Connection Usage**: < 80% of max_connections
- **Buffer Pool Hit Ratio**: > 95%
- **Slow Query Rate**: < 5% of total queries

## Security Features

### Access Control
- **Root Access**: Limited to localhost and cluster network
- **Application User**: Limited privileges for application database
- **Replication User**: REPLICATION SLAVE privilege only
- **Monitor User**: SELECT and PROCESS privileges for health checks

### Network Security
- **Bind Address**: 0.0.0.0 (container network only)
- **Skip Name Resolve**: Prevents DNS-based attacks
- **SSL/TLS**: Available for encrypted connections

## Backup and Recovery

### Automated Backups
```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)

docker exec mysql-master mysqldump \
  -u root -pcluster_root_pass \
  --all-databases \
  --single-transaction \
  --routines \
  --triggers > "$BACKUP_DIR/backup_$DATE.sql"
```

### Point-in-Time Recovery
```bash
# Restore from backup
docker exec -i mysql-master mysql -u root -pcluster_root_pass < backup_file.sql

# Apply binary logs for point-in-time recovery
docker exec mysql-master mysqlbinlog mysql-bin.000001 | \
  docker exec -i mysql-master mysql -u root -pcluster_root_pass
```

## Troubleshooting

### Common Issues

#### Replication Lag
```bash
# Check slave status
docker exec mysql-slave-1 mysql -u cluster_monitor -pmonitor_pass \
  -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master"

# Skip problematic transaction (use with caution)
docker exec mysql-slave-1 mysql -u root -pcluster_root_pass \
  -e "SET GLOBAL sql_slave_skip_counter = 1; START SLAVE;"
```

#### Connection Issues
```bash
# Check MySQL process list
docker exec mysql-master mysql -u root -pcluster_root_pass \
  -e "SHOW PROCESSLIST;"

# Check error logs
docker logs mysql-master
```

#### Storage Issues
```bash
# Check disk usage
docker exec mysql-master df -h /var/lib/mysql

# Check InnoDB status
docker exec mysql-master mysql -u root -pcluster_root_pass \
  -e "SHOW ENGINE INNODB STATUS\G"
```

## Integration with Cluster System

### Auto-Scaling Considerations
- **Scaling**: Manual scaling recommended for stateful database
- **Read Replicas**: Can add more slave nodes for read scaling
- **Write Scaling**: Requires application-level sharding

### Health Check Integration
```yaml
# Add to cluster dashboard monitoring
healthChecks:
  - name: mysql-cluster
    endpoint: /api/mysql/health
    interval: 30s
    timeout: 5s
```

### Persistent Storage Requirements
- **Minimum**: 10GB per node
- **Recommended**: 50GB+ for production
- **Backup Storage**: 2x database size
- **Log Retention**: 7 days of binary logs

## Production Deployment

### Resource Requirements
- **CPU**: 2+ cores per node
- **Memory**: 2GB+ per node (4GB+ recommended)
- **Storage**: SSD recommended for performance
- **Network**: Low latency between nodes

### High Availability Setup
1. Deploy across multiple availability zones
2. Configure automated backups
3. Set up monitoring and alerting
4. Test failover procedures regularly
5. Document recovery procedures