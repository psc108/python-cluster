<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

$cluster_url = getenv('CLUSTER_API_URL') ?: 'http://cluster-node-1:8000';
$action = $_GET['action'] ?? 'status';

switch ($action) {
    case 'status':
        echo json_encode(getClusterStatus());
        break;
    case 'nodes':
        echo json_encode(getClusterNodes());
        break;
    case 'applications':
        echo json_encode(getApplications());
        break;
    case 'metrics':
        echo json_encode(getClusterMetrics());
        break;
    case 'storage':
        echo json_encode(getStorageInfo());
        break;
    default:
        http_response_code(400);
        echo json_encode(['error' => 'Invalid action']);
}

function makeClusterRequest($endpoint, $timeout = 5) {
    global $cluster_url;
    
    $context = stream_context_create([
        'http' => [
            'timeout' => $timeout,
            'method' => 'GET',
            'header' => 'Content-Type: application/json'
        ]
    ]);
    
    $result = @file_get_contents($cluster_url . $endpoint, false, $context);
    
    if ($result === false) {
        return ['error' => 'Failed to connect to cluster'];
    }
    
    return json_decode($result, true) ?: ['error' => 'Invalid response'];
}

function getClusterStatus() {
    // Get status from multiple nodes
    $nodes = [
        ['id' => 1, 'url' => 'http://cluster-node-1:8000'],
        ['id' => 2, 'url' => 'http://cluster-node-2:8000'],
        ['id' => 3, 'url' => 'http://cluster-node-3:8000']
    ];
    
    $leader_id = null;
    $healthy_nodes = 0;
    $total_nodes = count($nodes);
    
    foreach ($nodes as $node) {
        $health = makeNodeRequest($node['url'] . '/health');
        if (!isset($health['error'])) {
            $healthy_nodes++;
            if ($health['status'] === 'leader') {
                $leader_id = $health['node_id'];
            }
        }
    }
    
    return [
        'leader_id' => $leader_id,
        'total_nodes' => $total_nodes,
        'healthy_nodes' => $healthy_nodes,
        'cluster_status' => $healthy_nodes > ($total_nodes / 2) ? 'healthy' : 'degraded',
        'uptime' => getClusterUptime()
    ];
}

function getClusterNodes() {
    $nodes = [
        ['id' => 1, 'url' => 'http://cluster-node-1:8000', 'port' => 8001],
        ['id' => 2, 'url' => 'http://cluster-node-2:8000', 'port' => 8002],
        ['id' => 3, 'url' => 'http://cluster-node-3:8000', 'port' => 8003]
    ];
    
    $node_list = [];
    
    foreach ($nodes as $node) {
        $health = makeNodeRequest($node['url'] . '/health');
        $metrics = makeNodeRequest('http://localhost:' . $node['port'] . '/metrics', 2);
        
        $node_info = [
            'id' => $node['id'],
            'status' => isset($health['error']) ? 'unhealthy' : 'healthy',
            'role' => isset($health['leader_id']) && $health['leader_id'] == $node['id'] ? 'leader' : 'follower',
            'cpu_percent' => extractMetricValue($metrics, 'cpu_usage_percent'),
            'memory_percent' => extractMetricValue($metrics, 'memory_usage_percent'),
            'uptime' => isset($health['uptime']) ? formatUptime($health['uptime']) : 'Unknown',
            'last_seen' => date('Y-m-d H:i:s')
        ];
        
        $node_list[] = $node_info;
    }
    
    return $node_list;
}

function getApplications() {
    // Mock application data - in real implementation, this would query the cluster
    return [
        [
            'name' => 'cluster-dashboard',
            'status' => 'running',
            'replicas' => '2/2',
            'version' => '1.0.0',
            'cpu_percent' => rand(10, 30),
            'memory_mb' => rand(100, 200),
            'uptime' => formatUptime(rand(3600, 86400))
        ],
        [
            'name' => 'web-api',
            'status' => 'running',
            'replicas' => '3/3',
            'version' => '2.1.0',
            'cpu_percent' => rand(20, 50),
            'memory_mb' => rand(150, 300),
            'uptime' => formatUptime(rand(7200, 172800))
        ]
    ];
}

function getClusterMetrics() {
    $metrics_data = [];
    
    // Collect metrics from all nodes
    for ($i = 1; $i <= 3; $i++) {
        $metrics = makeNodeRequest("http://localhost:800{$i}/metrics", 2);
        if (!isset($metrics['error']) && is_string($metrics)) {
            $parsed = parsePrometheusMetrics($metrics);
            $metrics_data["node_{$i}"] = $parsed;
        }
    }
    
    // Calculate aggregate metrics
    $total_requests = 0;
    $total_cpu = 0;
    $total_memory = 0;
    $node_count = 0;
    
    foreach ($metrics_data as $node_metrics) {
        if (isset($node_metrics['heartbeats_total'])) {
            $total_requests += $node_metrics['heartbeats_total'];
        }
        if (isset($node_metrics['cpu_usage_percent'])) {
            $total_cpu += $node_metrics['cpu_usage_percent'];
            $node_count++;
        }
        if (isset($node_metrics['memory_usage_percent'])) {
            $total_memory += $node_metrics['memory_usage_percent'];
        }
    }
    
    return [
        'request_rate' => round($total_requests / 60, 2), // Approximate requests per second
        'avg_cpu_percent' => $node_count > 0 ? round($total_cpu / $node_count, 1) : 0,
        'avg_memory_percent' => $node_count > 0 ? round($total_memory / $node_count, 1) : 0,
        'response_time_ms' => rand(15, 45),
        'error_rate' => 0.1,
        'throughput_mbps' => round(rand(50, 200) / 10, 1)
    ];
}

function getStorageInfo() {
    // Mock storage data - in real implementation, this would query the storage system
    return [
        'total_capacity_gb' => 1000,
        'used_gb' => 250,
        'available_gb' => 750,
        'volumes' => [
            [
                'name' => 'dashboard-data',
                'size' => '1Gi',
                'used' => '256Mi',
                'storage_class' => 'fast-ssd',
                'status' => 'bound',
                'mount_path' => '/var/www/html/data'
            ],
            [
                'name' => 'app-logs',
                'size' => '5Gi',
                'used' => '1.2Gi',
                'storage_class' => 'replicated-ssd',
                'status' => 'bound',
                'mount_path' => '/var/log/apps'
            ]
        ]
    ];
}

function makeNodeRequest($url, $timeout = 5) {
    $context = stream_context_create([
        'http' => [
            'timeout' => $timeout,
            'method' => 'GET'
        ]
    ]);
    
    $result = @file_get_contents($url, false, $context);
    
    if ($result === false) {
        return ['error' => 'Connection failed'];
    }
    
    $decoded = json_decode($result, true);
    return $decoded !== null ? $decoded : $result;
}

function extractMetricValue($metrics_text, $metric_name) {
    if (!is_string($metrics_text)) {
        return 0;
    }
    
    if (preg_match("/{$metric_name}\\s+(\\d+(?:\\.\\d+)?)/", $metrics_text, $matches)) {
        return (float)$matches[1];
    }
    
    return 0;
}

function parsePrometheusMetrics($metrics_text) {
    $parsed = [];
    $lines = explode("\n", $metrics_text);
    
    foreach ($lines as $line) {
        if (preg_match('/^([a-zA-Z_:][a-zA-Z0-9_:]*(?:\{[^}]*\})?)\\s+(\\S+)/', $line, $matches)) {
            $metric_name = preg_replace('/\{.*\}/', '', $matches[1]);
            $value = $matches[2];
            
            if (is_numeric($value)) {
                $parsed[$metric_name] = (float)$value;
            }
        }
    }
    
    return $parsed;
}

function formatUptime($seconds) {
    $days = floor($seconds / 86400);
    $hours = floor(($seconds % 86400) / 3600);
    $minutes = floor(($seconds % 3600) / 60);
    
    if ($days > 0) {
        return "{$days}d {$hours}h {$minutes}m";
    } elseif ($hours > 0) {
        return "{$hours}h {$minutes}m";
    } else {
        return "{$minutes}m";
    }
}

function getClusterUptime() {
    $uptime_file = '/var/www/html/data/cluster_uptime.txt';
    
    if (!file_exists($uptime_file)) {
        file_put_contents($uptime_file, time());
        return 0;
    }
    
    $start_time = (int)file_get_contents($uptime_file);
    return time() - $start_time;
}
?>