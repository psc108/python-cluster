# Storage Integration

## Overview

The Storage Integration system provides persistent data storage for applications running on the cluster. It supports multiple storage types, replication strategies, and consistency models to meet different application requirements.

## Storage Types

### Local Storage
- **Node-local** persistent volumes
- **Fast access** but not replicated
- **Use cases**: Temporary data, caches, logs
- **Lifecycle**: Tied to node availability

### Distributed Storage
- **Replicated** across multiple nodes
- **Fault tolerant** with automatic failover
- **Use cases**: Application data, databases, shared files
- **Consistency**: Strong or eventual consistency

### External Storage
- **Cloud storage** integration (AWS S3, Azure Blob, GCS)
- **Network attached** storage (NFS, CIFS)
- **Use cases**: Backups, large datasets, archival

## Storage Classes

### Performance Tiers
```yaml
storageClasses:
  - name: fast-ssd
    type: local
    medium: ssd
    replication: 1
    
  - name: replicated-ssd
    type: distributed
    medium: ssd
    replication: 3
    consistency: strong
    
  - name: bulk-storage
    type: distributed
    medium: hdd
    replication: 2
    consistency: eventual
    
  - name: external-backup
    type: external
    provider: s3
    bucket: cluster-backups
```

## Volume Types

### Persistent Volumes (PV)
Long-lived storage that persists beyond application lifecycle:
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: app-data-pv
spec:
  capacity: 10Gi
  storageClass: replicated-ssd
  accessModes:
    - ReadWriteOnce    # Single node read/write
    - ReadOnlyMany     # Multiple nodes read-only
    - ReadWriteMany    # Multiple nodes read/write
  mountPath: /data
  backup:
    enabled: true
    schedule: "0 2 * * *"  # Daily at 2 AM
    retention: 30d
```

### Ephemeral Volumes
Temporary storage tied to application instance:
```yaml
apiVersion: v1
kind: EphemeralVolume
metadata:
  name: temp-storage
spec:
  capacity: 1Gi
  storageClass: fast-ssd
  mountPath: /tmp
  lifecycle: application
```

### Shared Volumes
Storage accessible by multiple applications:
```yaml
apiVersion: v1
kind: SharedVolume
metadata:
  name: shared-config
spec:
  capacity: 100Mi
  storageClass: replicated-ssd
  accessModes:
    - ReadOnlyMany
  mountPath: /etc/shared
  applications:
    - web-app
    - worker-app
    - monitor-app
```

## Storage Backends

### Distributed File System
```python
class DistributedFileSystem:
    def __init__(self, cluster_client, replication_factor=3):
        self.cluster = cluster_client
        self.replication_factor = replication_factor
        self.consistency_level = "strong"
        
    async def create_volume(self, volume_spec):
        """Create distributed volume across nodes"""
        nodes = await self.select_storage_nodes(volume_spec)
        volume_id = self.generate_volume_id()
        
        for node_id in nodes:
            await self.cluster.send_message(node_id, {
                "action": "create_volume",
                "volume_id": volume_id,
                "spec": volume_spec
            })
            
        return volume_id
        
    async def write_data(self, volume_id, path, data):
        """Write data with replication"""
        nodes = await self.get_volume_nodes(volume_id)
        write_tasks = []
        
        for node_id in nodes:
            task = self.cluster.send_message(node_id, {
                "action": "write_data",
                "volume_id": volume_id,
                "path": path,
                "data": data
            })
            write_tasks.append(task)
            
        # Wait for majority write success
        results = await asyncio.gather(*write_tasks, return_exceptions=True)
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        
        if success_count >= (len(nodes) // 2 + 1):
            return True
        else:
            raise StorageException("Write failed - insufficient replicas")
            
    async def read_data(self, volume_id, path):
        """Read data with consistency guarantees"""
        nodes = await self.get_volume_nodes(volume_id)
        
        if self.consistency_level == "strong":
            # Read from majority of nodes
            return await self.read_with_quorum(volume_id, path, nodes)
        else:
            # Read from any available node
            return await self.read_from_any(volume_id, path, nodes)
```

### Object Storage
```python
class ObjectStorage:
    def __init__(self, cluster_client):
        self.cluster = cluster_client
        self.buckets = {}
        
    async def create_bucket(self, bucket_name, storage_class="replicated-ssd"):
        """Create object storage bucket"""
        bucket_spec = {
            "name": bucket_name,
            "storage_class": storage_class,
            "versioning": True,
            "encryption": True
        }
        
        bucket_id = await self.cluster.consensus.propose({
            "action": "create_bucket",
            "spec": bucket_spec
        })
        
        self.buckets[bucket_name] = bucket_id
        return bucket_id
        
    async def put_object(self, bucket_name, key, data, metadata=None):
        """Store object with metadata"""
        object_spec = {
            "bucket": bucket_name,
            "key": key,
            "size": len(data),
            "checksum": self.calculate_checksum(data),
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        
        # Store object data across nodes
        storage_nodes = await self.select_storage_nodes(len(data))
        object_id = await self.store_object_data(data, storage_nodes)
        
        # Update object index
        await self.cluster.consensus.propose({
            "action": "put_object",
            "spec": object_spec,
            "object_id": object_id
        })
        
        return object_id
```

### Database Storage
```python
class DatabaseStorage:
    def __init__(self, cluster_client):
        self.cluster = cluster_client
        self.databases = {}
        
    async def create_database(self, db_name, engine="sqlite", replicas=3):
        """Create distributed database"""
        db_spec = {
            "name": db_name,
            "engine": engine,
            "replicas": replicas,
            "sharding": "hash",
            "backup_schedule": "0 1 * * *"
        }
        
        # Select nodes for database replicas
        nodes = await self.select_database_nodes(replicas)
        
        # Initialize database on each node
        for node_id in nodes:
            await self.cluster.send_message(node_id, {
                "action": "init_database",
                "spec": db_spec
            })
            
        self.databases[db_name] = {
            "spec": db_spec,
            "nodes": nodes,
            "primary": nodes[0]
        }
        
    async def execute_query(self, db_name, query, params=None):
        """Execute database query with consistency"""
        db_info = self.databases[db_name]
        
        if query.strip().upper().startswith(('SELECT', 'SHOW')):
            # Read query - can use any replica
            node_id = random.choice(db_info["nodes"])
        else:
            # Write query - must use primary
            node_id = db_info["primary"]
            
        result = await self.cluster.send_message(node_id, {
            "action": "execute_query",
            "database": db_name,
            "query": query,
            "params": params
        })
        
        return result
```

## Application Integration

### Volume Mounting
```python
class StorageAwareApplication(ClusterApplication):
    def __init__(self, app_id, config):
        super().__init__(app_id, config)
        self.storage_client = None
        self.volumes = {}
        
    async def initialize(self):
        self.storage_client = StorageClient(self.cluster_client)
        
        # Mount required volumes
        for volume_spec in self.config.get("volumes", []):
            volume = await self.storage_client.mount_volume(volume_spec)
            self.volumes[volume_spec["name"]] = volume
            
        return True
        
    async def write_data(self, volume_name, path, data):
        """Write data to mounted volume"""
        volume = self.volumes[volume_name]
        return await volume.write(path, data)
        
    async def read_data(self, volume_name, path):
        """Read data from mounted volume"""
        volume = self.volumes[volume_name]
        return await volume.read(path)
```

### Database Integration
```python
class DatabaseApplication(ClusterApplication):
    async def initialize(self):
        self.db = DatabaseClient(
            cluster_client=self.cluster_client,
            database=self.config["database"]["name"]
        )
        
        # Initialize database schema
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        return True
        
    async def create_user(self, username, email):
        """Create user with distributed transaction"""
        async with self.db.transaction():
            user_id = await self.db.execute(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                (username, email)
            )
            
            # Update distributed cache
            await self.cluster_client.set_cache(f"user:{user_id}", {
                "username": username,
                "email": email
            })
            
            return user_id
```

## Storage Management

### CLI Commands
```bash
# Create storage volume
python -m src.storage.cli create-volume \
  --name app-data \
  --size 10Gi \
  --storage-class replicated-ssd \
  --replicas 3

# List volumes
python -m src.storage.cli list-volumes

# Volume status and usage
python -m src.storage.cli describe-volume app-data

# Backup volume
python -m src.storage.cli backup-volume app-data \
  --destination s3://backups/app-data-$(date +%Y%m%d)

# Restore volume
python -m src.storage.cli restore-volume app-data \
  --source s3://backups/app-data-20240101

# Delete volume
python -m src.storage.cli delete-volume app-data

# Storage node management
python -m src.storage.cli add-storage-node node-4 \
  --capacity 1TB \
  --storage-class fast-ssd

# Rebalance storage
python -m src.storage.cli rebalance \
  --strategy even-distribution
```

### REST API
```bash
# Create volume
curl -X POST http://localhost:8001/api/storage/volumes \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "app-data",
    "size": "10Gi",
    "storageClass": "replicated-ssd",
    "replicas": 3
  }'

# Get volume info
curl http://localhost:8001/api/storage/volumes/app-data \
  -H "Authorization: Bearer <token>"

# Update volume
curl -X PATCH http://localhost:8001/api/storage/volumes/app-data \
  -H "Authorization: Bearer <token>" \
  -d '{"size": "20Gi"}'

# Delete volume
curl -X DELETE http://localhost:8001/api/storage/volumes/app-data \
  -H "Authorization: Bearer <token>"
```

## Data Consistency

### Consistency Models
- **Strong Consistency**: All reads return the most recent write
- **Eventual Consistency**: Reads may return stale data temporarily
- **Causal Consistency**: Causally related operations are seen in order
- **Session Consistency**: Consistency within a client session

### Conflict Resolution
```python
class ConflictResolver:
    def resolve_write_conflict(self, current_data, new_data, metadata):
        """Resolve conflicting writes"""
        if metadata["strategy"] == "last-write-wins":
            return new_data if new_data["timestamp"] > current_data["timestamp"] else current_data
            
        elif metadata["strategy"] == "merge":
            return self.merge_data(current_data, new_data)
            
        elif metadata["strategy"] == "application-defined":
            return self.application_resolve(current_data, new_data, metadata)
```

## Backup and Recovery

### Automated Backups
```yaml
backupPolicy:
  schedule: "0 2 * * *"        # Daily at 2 AM
  retention: 30d               # Keep for 30 days
  compression: true            # Compress backup data
  encryption: true             # Encrypt backup data
  destinations:
    - type: s3
      bucket: cluster-backups
      prefix: daily/
    - type: local
      path: /backup/storage/
```

### Point-in-Time Recovery
```bash
# List available backups
python -m src.storage.cli list-backups app-data

# Restore to specific point in time
python -m src.storage.cli restore-volume app-data \
  --timestamp "2024-01-01T12:00:00Z" \
  --target-volume app-data-restored
```

## Performance Optimization

### Caching Layers
- **Memory Cache**: In-memory data for fastest access
- **SSD Cache**: Frequently accessed data on SSD
- **Tiered Storage**: Automatic data movement between tiers

### Data Placement
- **Locality**: Place data close to applications
- **Load Balancing**: Distribute data evenly across nodes
- **Affinity Rules**: Keep related data together

### Monitoring
```python
storage_metrics = {
    "volume_usage_bytes": Gauge("storage_volume_usage_bytes"),
    "read_operations_total": Counter("storage_read_operations_total"),
    "write_operations_total": Counter("storage_write_operations_total"),
    "read_latency_seconds": Histogram("storage_read_latency_seconds"),
    "write_latency_seconds": Histogram("storage_write_latency_seconds"),
    "replication_lag_seconds": Gauge("storage_replication_lag_seconds")
}
```

## Security

### Encryption
- **At Rest**: All stored data encrypted with AES-256
- **In Transit**: TLS encryption for data transfer
- **Key Management**: Distributed key storage with rotation

### Access Control
```yaml
accessPolicy:
  - principal: app:web-server
    permissions:
      - read
      - write
    resources:
      - volume:app-data
      - bucket:uploads
      
  - principal: app:backup-service
    permissions:
      - read
    resources:
      - volume:*
```

## Best Practices

### Design Guidelines
- **Plan for Growth**: Size volumes appropriately with room for expansion
- **Choose Right Storage Class**: Match performance needs with cost
- **Implement Proper Backup**: Regular backups with tested recovery procedures
- **Monitor Usage**: Track storage metrics and set up alerts
- **Security First**: Encrypt sensitive data and implement access controls

### Performance Tips
- **Use Local Storage**: For temporary data and caches
- **Batch Operations**: Group small operations together
- **Async I/O**: Use non-blocking storage operations
- **Cache Frequently Used Data**: Reduce storage access latency
- **Optimize Data Layout**: Structure data for efficient access patterns