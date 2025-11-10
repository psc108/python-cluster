<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Include Phase 3 functions
require_once __DIR__ . '/phase3_functions.php';

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

$cluster_url = getenv('CLUSTER_API_URL') ?: 'http://host.docker.internal:8001';
$action = $_GET['action'] ?? $_POST['action'] ?? 'status';

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
    case 'scale':
        echo json_encode(handleScaleApplication());
        break;
    case 'stop':
        echo json_encode(handleStopApplication());
        break;
    case 'deploy':
        echo json_encode(handleDeployApplication());
        break;
    case 'pause':
        echo json_encode(handlePauseApplication());
        break;
    case 'resume':
        echo json_encode(handleResumeApplication());
        break;
    case 'node_details':
        echo json_encode(getNodeDetails());
        break;
    case 'resource_info':
        echo json_encode(getResourceInfo());
        break;
    case 'create_scaling_policy':
        $input = json_decode(file_get_contents('php://input'), true);
        
        if (!isset($input['application']) || !isset($input['minReplicas']) || !isset($input['maxReplicas'])) {
            echo json_encode(['success' => false, 'error' => 'Missing required fields']);
            break;
        }
        
        $policy = [
            'application' => $input['application'],
            'minReplicas' => (int)$input['minReplicas'],
            'maxReplicas' => (int)$input['maxReplicas'],
            'cpuThreshold' => (int)($input['cpuThreshold'] ?? 70),
            'memoryThreshold' => (int)($input['memoryThreshold'] ?? 80),
            'enabled' => true,
            'created_at' => time()
        ];
        
        $policies_file = '/var/www/html/data/scaling_policies.json';
        $policies = [];
        
        if (file_exists($policies_file)) {
            $policies = json_decode(file_get_contents($policies_file), true) ?: [];
        }
        
        if (!file_exists('/var/www/html/data')) {
            mkdir('/var/www/html/data', 0755, true);
        }
        
        $policies[$input['application']] = $policy;
        file_put_contents($policies_file, json_encode($policies, JSON_PRETTY_PRINT));
        
        echo json_encode(['success' => true, 'policy' => $policy]);
        break;
    case 'get_scaling_policies':
        $policies_file = '/var/www/html/data/scaling_policies.json';
        
        if (!file_exists($policies_file)) {
            echo json_encode([]);
            break;
        }
        
        $policies = json_decode(file_get_contents($policies_file), true) ?: [];
        echo json_encode($policies);
        break;
    case 'scaling_events':
        echo json_encode(getScalingEvents());
        break;
    case 'evaluate_scaling':
        echo json_encode(evaluateScaling());
        break;
    case 'app_details':
        echo json_encode(getApplicationDetails());
        break;
    case 'container_details':
        echo json_encode(getContainerDetails());
        break;
    case 'get_scheduled_policies':
        echo json_encode(getScheduledPolicies());
        break;
    case 'create_scheduled_policy':
        echo json_encode(handleCreateScheduledPolicy());
        break;
    case 'delete_scheduled_policy':
        echo json_encode(handleDeleteScheduledPolicy());
        break;
    case 'schedule_history':
        echo json_encode(getScheduleHistory());
        break;
    case 'schedule_summary':
        echo json_encode(getScheduleSummary());
        break;
    case 'scaling_analytics':
        echo json_encode(getScalingAnalytics());
        break;
    case 'cost_savings_breakdown':
        echo json_encode(getCostSavingsBreakdown());
        break;
    case 'test_action':
        echo json_encode(['success' => true, 'message' => 'Test action works']);
        break;
    default:
        http_response_code(400);
        echo json_encode(['error' => 'Invalid action', 'received' => $action]);
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
    $nodes = getNodeConfiguration();
    
    $leader_id = null;
    $healthy_nodes = 0;
    $total_nodes = count($nodes);
    
    foreach ($nodes as $node) {
        $health = makeNodeRequest($node['url'] . '/health');
        if (!isset($health['error'])) {
            $healthy_nodes++;
            if (isset($health['leader_id']) && $health['leader_id'] == $health['node_id']) {
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
    $nodes = getNodeConfiguration();
    
    $node_list = [];
    
    foreach ($nodes as $node) {
        $health = makeNodeRequest($node['url'] . '/health');
        $metrics = makeNodeRequest($node['url'] . '/metrics', 2);
        
        // Extract CPU and memory from metrics
        $cpu_percent = extractMetricValue($metrics, 'node_' . $node['id'] . '_cpu_usage_percent');
        $memory_percent = extractMetricValue($metrics, 'node_' . $node['id'] . '_memory_usage_percent');
        
        // If no metrics found, try alternative metric names
        if ($cpu_percent == 0) {
            $cpu_percent = extractMetricValue($metrics, 'cpu_usage_percent');
        }
        if ($memory_percent == 0) {
            $memory_percent = extractMetricValue($metrics, 'memory_usage_percent');
        }
        
        // Calculate uptime based on actual container start time
        $uptime = getNodeUptime($node['id']);
        
        $node_info = [
            'id' => $node['id'],
            'status' => isset($health['error']) ? 'unhealthy' : 'healthy',
            'role' => (isset($health['leader_id']) && $health['leader_id'] == $node['id']) ? 'leader' : 'follower',
            'cpu_percent' => $cpu_percent,
            'memory_percent' => $memory_percent,
            'uptime' => $uptime,
            'last_seen' => date('Y-m-d H:i:s')
        ];
        
        $node_list[] = $node_info;
    }
    
    return $node_list;
}

function getApplications() {
    // Get deployed applications from Docker containers
    $applications = [];
    
    try {
        // List all containers with app- prefix (including stopped ones)
        $containers_output = shell_exec('sudo docker ps -a --filter "name=app-" --format "{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null');
        
        if ($containers_output) {
            $lines = explode("\n", trim($containers_output));
            $app_groups = [];
            
            foreach ($lines as $line) {
                if (empty($line)) continue;
                
                $parts = explode("\t", $line);
                if (count($parts) >= 3) {
                    $container_name = $parts[0];
                    $status = $parts[1];
                    $image = $parts[2];
                    $ports = $parts[3] ?? '';
                    
                    // Extract app name (remove app- prefix and instance number)
                    if (preg_match('/^app-(.+?)-\d+$/', $container_name, $matches)) {
                        $app_name = $matches[1];
                        
                        if (!isset($app_groups[$app_name])) {
                            $app_groups[$app_name] = [
                                'name' => $app_name,
                                'image' => $image,
                                'containers' => [],
                                'running' => 0,
                                'total' => 0
                            ];
                        }
                        
                        $app_groups[$app_name]['containers'][] = [
                            'name' => $container_name,
                            'status' => $status,
                            'ports' => $ports
                        ];
                        
                        $app_groups[$app_name]['total']++;
                        if (strpos($status, 'Up') === 0) {
                            $app_groups[$app_name]['running']++;
                        } elseif (strpos($status, 'Exited') === 0) {
                            // Container exists but is stopped (paused)
                        }
                    }
                }
            }
            
            // Convert to application list
            foreach ($app_groups as $app_name => $app_data) {
                $status = 'stopped';
                if ($app_data['running'] > 0) {
                    $status = 'running';
                } elseif ($app_data['total'] > 0) {
                    $status = 'paused';
                }
                
                // Check if auto-scaling is enabled
                $autoScaling = hasAutoScalingPolicy($app_name);
                
                // Get actual resource metrics from containers
                $cpu_percent = 0;
                $memory_mb = 0;
                
                if ($app_data['running'] > 0) {
                    $metrics = getApplicationMetrics($app_name);
                    $cpu_percent = $metrics['cpu_percent'];
                    $memory_mb = $metrics['memory_mb'];
                }
                
                $applications[] = [
                    'name' => $app_name,
                    'status' => $status,
                    'replicas' => $app_data['running'] . '/' . $app_data['total'],
                    'version' => getApplicationVersion($app_name),
                    'cpu_percent' => $cpu_percent,
                    'memory_mb' => $memory_mb,
                    'uptime' => getApplicationUptime($app_name),
                    'autoScaling' => $autoScaling
                ];
            }
        }
        
    } catch (Exception $e) {
        error_log("Error getting applications: " . $e->getMessage());
    }
    
    return $applications;
}

function getApplicationUptime($app_name) {
    $uptime_file = "/var/www/html/data/apps/{$app_name}/deployed_at.txt";
    
    if (file_exists($uptime_file)) {
        $deployed_at = (int)file_get_contents($uptime_file);
        $uptime_seconds = time() - $deployed_at;
        return formatUptime($uptime_seconds);
    }
    
    return '0m';
}

function getClusterMetrics() {
    $metrics_data = [];
    
    // Collect metrics from all nodes
    for ($i = 1; $i <= 3; $i++) {
        $metrics = makeNodeRequest("http://host.docker.internal:800{$i}/metrics", 2);
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
    
    foreach ($metrics_data as $node_id => $node_metrics) {
        // Extract node number from node_id (e.g., "node_1" -> 1)
        $node_num = str_replace('node_', '', $node_id);
        
        // Look for node-specific metrics
        $heartbeat_key = "node_{$node_num}_heartbeats_total";
        $cpu_key = "node_{$node_num}_cpu_usage_percent";
        $memory_key = "node_{$node_num}_memory_usage_percent";
        
        if (isset($node_metrics[$heartbeat_key])) {
            $total_requests += $node_metrics[$heartbeat_key];
        }
        if (isset($node_metrics[$cpu_key])) {
            $total_cpu += $node_metrics[$cpu_key];
            $node_count++;
        }
        if (isset($node_metrics[$memory_key])) {
            $total_memory += $node_metrics[$memory_key];
        }
    }
    
    // If no real metrics, return zeros instead of random values
    if ($node_count == 0) {
        return [
            'request_rate' => 0,
            'avg_cpu_percent' => 0,
            'avg_memory_percent' => 0,
            'response_time_ms' => 0,
            'error_rate' => 0,
            'throughput_mbps' => 0
        ];
    }
    
    return [
        'request_rate' => round($total_requests / 60, 2),
        'avg_cpu_percent' => round($total_cpu / $node_count, 1),
        'avg_memory_percent' => round($total_memory / $node_count, 1),
        'response_time_ms' => extractAverageResponseTime($metrics_data),
        'error_rate' => extractErrorRate($metrics_data),
        'throughput_mbps' => extractThroughput($metrics_data)
    ];
}

function getStorageInfo() {
    // Query actual storage data from cluster
    $storage_data = makeClusterRequest('/storage');
    
    if (isset($storage_data['error'])) {
        // If cluster API not available, return basic info
        return [
            'total_capacity_gb' => 0,
            'used_gb' => 0,
            'available_gb' => 0,
            'volumes' => []
        ];
    }
    
    return [
        'total_capacity_gb' => $storage_data['total_capacity_gb'] ?? 0,
        'used_gb' => $storage_data['used_gb'] ?? 0,
        'available_gb' => $storage_data['available_gb'] ?? 0,
        'volumes' => $storage_data['volumes'] ?? []
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
    
    // Try to match the metric with optional labels
    if (preg_match("/^{$metric_name}(?:\\{[^}]*\\})?\\s+(\\d+(?:\\.\\d+)?)/m", $metrics_text, $matches)) {
        return (float)$matches[1];
    }
    
    // Try simpler pattern
    if (preg_match("/\\b{$metric_name}\\s+(\\d+(?:\\.\\d+)?)/", $metrics_text, $matches)) {
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
        // Detect cluster start time from node process start time
        $cluster_start_time = detectClusterStartTime();
        file_put_contents($uptime_file, $cluster_start_time);
        return time() - $cluster_start_time;
    }
    
    $start_time = (int)file_get_contents($uptime_file);
    return time() - $start_time;
}

function detectClusterStartTime() {
    // Use current time as cluster start time for dashboard tracking
    return time();
}

function getNodeUptime($node_id) {
    try {
        // Get actual container start time from Docker
        $container_name = "cluster-node-{$node_id}";
        $docker_inspect = shell_exec("sudo docker inspect {$container_name} --format '{{.State.StartedAt}}' 2>/dev/null");
        
        if ($docker_inspect && trim($docker_inspect)) {
            $start_time_str = trim($docker_inspect);
            $start_time = strtotime($start_time_str);
            
            if ($start_time) {
                $uptime_seconds = time() - $start_time;
                return formatUptime($uptime_seconds);
            }
        }
        
        // Fallback: use file-based tracking
        $uptime_file = '/var/www/html/data/node_' . $node_id . '_start.txt';
        
        if (!file_exists($uptime_file)) {
            file_put_contents($uptime_file, time());
            return '0m';
        }
        
        $start_time = (int)file_get_contents($uptime_file);
        $uptime_seconds = time() - $start_time;
        
        return formatUptime($uptime_seconds);
        
    } catch (Exception $e) {
        return '0m';
    }
}

function handleScaleApplication() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($input['application']) || !isset($input['replicas'])) {
        return ['success' => false, 'error' => 'Missing application name or replica count'];
    }
    
    $app_name = $input['application'];
    $replicas = (int)$input['replicas'];
    
    // Execute actual scaling
    $result = scaleApplicationContainers($app_name, $replicas);
    
    // Log the scaling operation
    $status = $result['success'] ? 'SUCCESS' : 'FAILED';
    $log_entry = date('Y-m-d H:i:s') . " - [{$status}] Scaled {$app_name} to {$replicas} replicas\n";
    file_put_contents('/var/www/html/data/operations.log', $log_entry, FILE_APPEND);
    
    return $result;
}

function scaleApplicationContainers($app_name, $target_replicas) {
    try {
        // Get all containers (running and stopped)
        $all_output = shell_exec("sudo docker ps -a --filter \"name=app-{$app_name}-\" --format \"{{.Names}}\t{{.Status}}\" 2>/dev/null");
        $running_containers = [];
        $all_containers = [];
        
        if ($all_output) {
            $lines = explode("\n", trim($all_output));
            foreach ($lines as $line) {
                if (empty($line)) continue;
                $parts = explode("\t", $line);
                if (count($parts) >= 2) {
                    $name = $parts[0];
                    $status = $parts[1];
                    $all_containers[] = $name;
                    if (strpos($status, 'Up') === 0) {
                        $running_containers[] = $name;
                    }
                }
            }
        }
        
        $current_running = count($running_containers);
        
        if ($target_replicas > $current_running) {
            // Scale up: start stopped containers first, then create new ones
            $needed = $target_replicas - $current_running;
            $started = [];
            
            // Start stopped containers first
            $stopped_containers = array_diff($all_containers, $running_containers);
            foreach ($stopped_containers as $container_name) {
                if ($needed <= 0) break;
                $start_output = shell_exec("sudo docker start {$container_name} 2>&1");
                if (strpos($start_output, 'Error') === false) {
                    $started[] = $container_name;
                    $needed--;
                }
            }
            
            // Create new containers if still needed
            if ($needed > 0) {
                $image = getApplicationImage($app_name) ?: 'nginx:latest';
                $used_ports = getUsedPorts();
                $base_port = 10000;
                
                // Find highest existing container number
                $max_id = 0;
                foreach ($all_containers as $container_name) {
                    if (preg_match('/-([0-9]+)$/', $container_name, $matches)) {
                        $max_id = max($max_id, (int)$matches[1]);
                    }
                }
                
                for ($i = 1; $i <= $needed; $i++) {
                    $next_id = $max_id + $i;
                    $instance_name = "app-{$app_name}-{$next_id}";
                    
                    // Find available port
                    $instance_port = $base_port;
                    while (in_array($instance_port, $used_ports)) {
                        $instance_port++;
                    }
                    $used_ports[] = $instance_port;
                    
                    $run_cmd = "sudo docker run -d --name {$instance_name} -p {$instance_port}:8080 {$image} 2>&1";
                    $run_output = shell_exec($run_cmd);
                    
                    if (strpos($run_output, 'Error') === false && strlen(trim($run_output)) > 10) {
                        $started[] = $instance_name;
                    }
                }
            }
            
            return [
                'success' => count($started) > 0,
                'message' => "Scaled up {$app_name} to {$target_replicas} replicas",
                'started_containers' => $started,
                'timestamp' => time()
            ];
            
        } elseif ($target_replicas < $current_running) {
            // Scale down: stop highest numbered containers
            $to_stop = $current_running - $target_replicas;
            $stopped = [];
            
            // Sort by container number (highest first)
            usort($running_containers, function($a, $b) {
                preg_match('/-([0-9]+)$/', $a, $matches_a);
                preg_match('/-([0-9]+)$/', $b, $matches_b);
                $num_a = isset($matches_a[1]) ? (int)$matches_a[1] : 0;
                $num_b = isset($matches_b[1]) ? (int)$matches_b[1] : 0;
                return $num_b - $num_a;
            });
            
            for ($i = 0; $i < $to_stop; $i++) {
                $container_name = $running_containers[$i];
                $stop_output = shell_exec("sudo docker stop {$container_name} 2>&1");
                if (strpos($stop_output, 'Error') === false) {
                    $stopped[] = $container_name;
                }
            }
            
            return [
                'success' => count($stopped) > 0,
                'message' => "Scaled down {$app_name} to {$target_replicas} replicas",
                'stopped_containers' => $stopped,
                'timestamp' => time()
            ];
        }
        
        return [
            'success' => true,
            'message' => "Application {$app_name} already at {$target_replicas} replicas",
            'timestamp' => time()
        ];
        
    } catch (Exception $e) {
        return [
            'success' => false,
            'error' => $e->getMessage(),
            'timestamp' => time()
        ];
    }
}



function getApplicationImage($app_name) {
    $containers_output = shell_exec("sudo docker ps -a --filter \"name=app-{$app_name}-\" --format \"{{.Image}}\" 2>/dev/null | head -1");
    return trim($containers_output) ?: null;
}

function getApplicationVersion($app_name) {
    $app_yaml_file = "/var/www/html/data/apps/{$app_name}/app.yaml";
    
    if (file_exists($app_yaml_file)) {
        $yaml_content = file_get_contents($app_yaml_file);
        if (preg_match('/version:\s*([^\n]+)/', $yaml_content, $matches)) {
            return trim($matches[1]);
        }
    }
    
    // Fallback: extract from image tag
    $image = getApplicationImage($app_name);
    if ($image && strpos($image, ':') !== false) {
        $parts = explode(':', $image);
        return end($parts);
    }
    
    return 'unknown';
}

function getApplicationMemoryLimit($app_name) {
    $app_yaml_file = "/var/www/html/data/apps/{$app_name}/app.yaml";
    
    if (file_exists($app_yaml_file)) {
        $yaml_content = file_get_contents($app_yaml_file);
        if (preg_match('/memory:\s*([^\n]+)/', $yaml_content, $matches)) {
            $memory_str = trim($matches[1]);
            
            // Convert memory string to MB
            if (preg_match('/(\d+)([KMGT]?i?)/', $memory_str, $mem_matches)) {
                $value = (int)$mem_matches[1];
                $unit = strtoupper($mem_matches[2]);
                
                switch ($unit) {
                    case 'GI':
                    case 'G':
                        return $value * 1024;
                    case 'MI':
                    case 'M':
                        return $value;
                    case 'KI':
                    case 'K':
                        return $value / 1024;
                    default:
                        return $value; // Assume MB if no unit
                }
            }
        }
    }
    
    // Default memory limit if not specified
    return 128; // 128MB default
}

function handleStopApplication() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($input['application'])) {
        return ['success' => false, 'error' => 'Missing application name'];
    }
    
    $app_name = $input['application'];
    
    try {
        // Stop all containers for this application
        $stop_result = stopApplicationContainers($app_name);
        
        // Log the stop operation
        $status = $stop_result['success'] ? 'SUCCESS' : 'FAILED';
        $log_entry = date('Y-m-d H:i:s') . " - [{$status}] Stopped application {$app_name}\n";
        file_put_contents('/var/www/html/data/operations.log', $log_entry, FILE_APPEND);
        
        return $stop_result;
        
    } catch (Exception $e) {
        return [
            'success' => false,
            'error' => "Failed to stop application: " . $e->getMessage(),
            'timestamp' => time()
        ];
    }
}

function stopApplicationContainers($app_name) {
    try {
        $stopped_containers = [];
        
        // Find all containers for this application
        $containers_output = shell_exec("sudo docker ps -a --filter \"name=app-{$app_name}-\" --format \"{{.Names}}\" 2>/dev/null");
        
        if ($containers_output) {
            $container_names = explode("\n", trim($containers_output));
            
            foreach ($container_names as $container_name) {
                if (empty($container_name)) continue;
                
                // Stop the container
                $stop_output = shell_exec("sudo docker stop {$container_name} 2>&1");
                
                // Remove the container
                $rm_output = shell_exec("sudo docker rm {$container_name} 2>&1");
                
                $stopped_containers[] = $container_name;
            }
        }
        
        if (empty($stopped_containers)) {
            return [
                'success' => false,
                'error' => "No containers found for application {$app_name}",
                'timestamp' => time()
            ];
        }
        
        return [
            'success' => true,
            'message' => "Application {$app_name} stopped successfully",
            'stopped_containers' => $stopped_containers,
            'timestamp' => time()
        ];
        
    } catch (Exception $e) {
        return [
            'success' => false,
            'error' => $e->getMessage(),
            'timestamp' => time()
        ];
    }
}

function handleDeployApplication() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($input['name']) || !isset($input['image'])) {
        return ['success' => false, 'error' => 'Missing application name or image'];
    }
    
    $app_name = $input['name'];
    $image = $input['image'];
    $replicas = $input['replicas'] ?? 1;
    $port = $input['ports'][0]['port'] ?? 8080;
    $cpu = $input['resources']['cpu'] ?? '100m';
    $memory = $input['resources']['memory'] ?? '128Mi';
    
    // Create application directory and files
    $result = createAndDeployApplication($app_name, $image, $replicas, $port, $cpu, $memory);
    
    // Log the deployment
    $status = $result['success'] ? 'SUCCESS' : 'FAILED';
    $log_entry = date('Y-m-d H:i:s') . " - [{$status}] Deployed {$app_name} with image {$image} ({$replicas} replicas)\n";
    file_put_contents('/var/www/html/data/operations.log', $log_entry, FILE_APPEND);
    
    return $result;
}

function createAndDeployApplication($app_name, $image, $replicas, $port, $cpu, $memory) {
    try {
        // Create application directory
        $app_dir = "/var/www/html/data/apps/{$app_name}";
        if (!file_exists($app_dir)) {
            mkdir($app_dir, 0755, true);
        }
        
        // Create app.yaml
        $app_yaml = generateAppYaml($app_name, $image, $replicas, $port, $cpu, $memory);
        file_put_contents("{$app_dir}/app.yaml", $app_yaml);
        
        // Create Dockerfile
        $dockerfile = generateDockerfile($image);
        file_put_contents("{$app_dir}/Dockerfile", $dockerfile);
        
        // Deploy using Docker directly (simulating cluster deployment)
        $container_name = "app-{$app_name}";
        $deploy_result = deployWithDocker($container_name, $image, $port, $replicas);
        
        if ($deploy_result['success']) {
            // Record deployment time
            file_put_contents("{$app_dir}/deployed_at.txt", time());
            
            return [
                'success' => true,
                'message' => "Application {$app_name} deployed successfully",
                'timestamp' => time(),
                'details' => $deploy_result['details']
            ];
        } else {
            return [
                'success' => false,
                'error' => $deploy_result['error'],
                'timestamp' => time()
            ];
        }
        
    } catch (Exception $e) {
        return [
            'success' => false,
            'error' => "Deployment failed: " . $e->getMessage(),
            'timestamp' => time()
        ];
    }
}

function generateAppYaml($name, $image, $replicas, $port, $cpu, $memory) {
    return "apiVersion: v1
kind: Application
metadata:
  name: {$name}
  version: 1.0.0
  description: \"Deployed via dashboard\"
spec:
  replicas: {$replicas}
  image: {$image}
  ports:
    - name: http
      port: {$port}
      protocol: TCP
  resources:
    cpu: {$cpu}
    memory: {$memory}
  healthCheck:
    path: /health
    port: {$port}
    interval: 30s
    timeout: 5s
  environment:
    - name: LOG_LEVEL
      value: INFO
    - name: CLUSTER_MODE
      value: \"true\"
";
}

function generateDockerfile($image) {
    return "FROM {$image}
EXPOSE 8080
CMD [\"sh\", \"-c\", \"echo 'Application running' && sleep infinity\"]
";
}

function deployWithDocker($container_name, $image, $port, $replicas) {
    try {
        // Check if image exists locally or pull it
        $pull_cmd = "sudo docker pull {$image} 2>&1";
        $pull_output = shell_exec($pull_cmd);
        
        // Deploy containers (simplified - in real cluster this would be distributed)
        $deployed_containers = [];
        
        // Find available ports starting from 10000
        $base_port = 10000;
        $used_ports = getUsedPorts();
        
        for ($i = 1; $i <= $replicas; $i++) {
            $instance_name = "{$container_name}-{$i}";
            
            // Find next available port
            $instance_port = $base_port;
            while (in_array($instance_port, $used_ports)) {
                $instance_port++;
            }
            $used_ports[] = $instance_port;
            
            // Stop existing container if it exists
            shell_exec("sudo docker stop {$instance_name} 2>/dev/null");
            shell_exec("sudo docker rm {$instance_name} 2>/dev/null");
            
            // Start new container with dynamic port
            $run_cmd = "sudo docker run -d --name {$instance_name} -p {$instance_port}:{$port} {$image} 2>&1";
            $run_output = shell_exec($run_cmd);
            
            if (strpos($run_output, 'Error') === false && strlen(trim($run_output)) > 10) {
                $deployed_containers[] = [
                    'name' => $instance_name,
                    'port' => $instance_port,
                    'container_id' => trim($run_output)
                ];
            } else {
                throw new Exception("Failed to start container {$instance_name}: {$run_output}");
            }
        }
        
        return [
            'success' => true,
            'details' => [
                'containers' => $deployed_containers,
                'pull_output' => $pull_output
            ]
        ];
        
    } catch (Exception $e) {
        return [
            'success' => false,
            'error' => $e->getMessage()
        ];
    }
}

function getUsedPorts() {
    $used_ports = [];
    
    // Get all running containers and their ports
    $containers_output = shell_exec('sudo docker ps --format "{{.Ports}}" 2>/dev/null');
    
    if ($containers_output) {
        $lines = explode("\n", trim($containers_output));
        foreach ($lines as $line) {
            if (preg_match_all('/(\d+)->/', $line, $matches)) {
                foreach ($matches[1] as $port) {
                    $used_ports[] = (int)$port;
                }
            }
        }
    }
    
    return $used_ports;
}

function getNodeConfiguration() {
    // Discover nodes dynamically by checking which ports respond
    $base_url = 'http://host.docker.internal';
    $nodes = [];
    
    // Check standard cluster ports
    for ($port = 8001; $port <= 8003; $port++) {
        $url = $base_url . ':' . $port;
        $health = makeNodeRequest($url . '/health', 2);
        
        if (!isset($health['error'])) {
            $node_id = $health['node_id'] ?? ($port - 8000);
            $nodes[] = [
                'id' => $node_id,
                'url' => $url,
                'port' => $port
            ];
        }
    }
    
    return $nodes;
}

function extractAverageResponseTime($metrics_data) {
    $total_time = 0;
    $count = 0;
    
    foreach ($metrics_data as $node_metrics) {
        if (isset($node_metrics['response_time_ms'])) {
            $total_time += $node_metrics['response_time_ms'];
            $count++;
        }
    }
    
    return $count > 0 ? round($total_time / $count, 1) : 0;
}

function extractErrorRate($metrics_data) {
    $total_errors = 0;
    $total_requests = 0;
    
    foreach ($metrics_data as $node_metrics) {
        if (isset($node_metrics['errors_total'])) {
            $total_errors += $node_metrics['errors_total'];
        }
        if (isset($node_metrics['requests_total'])) {
            $total_requests += $node_metrics['requests_total'];
        }
    }
    
    return $total_requests > 0 ? round(($total_errors / $total_requests) * 100, 1) : 0;
}

function extractThroughput($metrics_data) {
    $total_bytes = 0;
    $count = 0;
    
    foreach ($metrics_data as $node_metrics) {
        if (isset($node_metrics['bytes_transferred'])) {
            $total_bytes += $node_metrics['bytes_transferred'];
            $count++;
        }
    }
    
    // Convert bytes to Mbps (approximate)
    return $count > 0 ? round(($total_bytes / 1024 / 1024) / 60, 1) : 0;
}

function handlePauseApplication() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($input['application'])) {
        return ['success' => false, 'error' => 'Missing application name'];
    }
    
    $app_name = $input['application'];
    
    try {
        $paused_containers = [];
        
        // Find all running containers for this application
        $containers_output = shell_exec("sudo docker ps --filter \"name=app-{$app_name}-\" --format \"{{.Names}}\" 2>/dev/null");
        
        if ($containers_output) {
            $container_names = explode("\n", trim($containers_output));
            
            foreach ($container_names as $container_name) {
                if (empty($container_name)) continue;
                
                // Stop the container (but don't remove it)
                $stop_output = shell_exec("sudo docker stop {$container_name} 2>&1");
                $paused_containers[] = $container_name;
            }
        }
        
        if (empty($paused_containers)) {
            return [
                'success' => false,
                'error' => "No running containers found for application {$app_name}",
                'timestamp' => time()
            ];
        }
        
        // Log the pause operation
        $log_entry = date('Y-m-d H:i:s') . " - [SUCCESS] Paused application {$app_name}\n";
        file_put_contents('/var/www/html/data/operations.log', $log_entry, FILE_APPEND);
        
        return [
            'success' => true,
            'message' => "Application {$app_name} paused successfully",
            'paused_containers' => $paused_containers,
            'timestamp' => time()
        ];
        
    } catch (Exception $e) {
        return [
            'success' => false,
            'error' => $e->getMessage(),
            'timestamp' => time()
        ];
    }
}

function handleResumeApplication() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($input['application'])) {
        return ['success' => false, 'error' => 'Missing application name'];
    }
    
    $app_name = $input['application'];
    
    try {
        $resumed_containers = [];
        
        // Find all stopped containers for this application
        $containers_output = shell_exec("sudo docker ps -a --filter \"name=app-{$app_name}-\" --filter \"status=exited\" --format \"{{.Names}}\" 2>/dev/null");
        
        if ($containers_output) {
            $container_names = explode("\n", trim($containers_output));
            
            foreach ($container_names as $container_name) {
                if (empty($container_name)) continue;
                
                // Start the container
                $start_output = shell_exec("sudo docker start {$container_name} 2>&1");
                $resumed_containers[] = $container_name;
            }
        }
        
        if (empty($resumed_containers)) {
            return [
                'success' => false,
                'error' => "No paused containers found for application {$app_name}",
                'timestamp' => time()
            ];
        }
        
        // Log the resume operation
        $log_entry = date('Y-m-d H:i:s') . " - [SUCCESS] Resumed application {$app_name}\n";
        file_put_contents('/var/www/html/data/operations.log', $log_entry, FILE_APPEND);
        
        return [
            'success' => true,
            'message' => "Application {$app_name} resumed successfully",
            'resumed_containers' => $resumed_containers,
            'timestamp' => time()
        ];
        
    } catch (Exception $e) {
        return [
            'success' => false,
            'error' => $e->getMessage(),
            'timestamp' => time()
        ];
    }
}

function getResourceInfo() {
    try {
        // Get used ports
        $used_ports = getUsedPorts();
        
        // Get real system memory information
        $memory_info = getSystemMemoryInfo();
        
        return [
            'used_ports' => $used_ports,
            'memory' => $memory_info
        ];
        
    } catch (Exception $e) {
        return [
            'used_ports' => [],
            'memory' => [
                'total_mb' => 0,
                'used_mb' => 0,
                'available_mb' => 0,
                'usage_percent' => 0
            ]
        ];
    }
}

function getSystemMemoryInfo() {
    try {
        // Try to get host system memory via Docker stats
        $docker_info = shell_exec('sudo docker system info --format "{{.MemTotal}}" 2>/dev/null');
        
        if ($docker_info && is_numeric(trim($docker_info))) {
            $total_bytes = (int)trim($docker_info);
            $total_mb = round($total_bytes / 1024 / 1024);
            
            // Get used memory from Docker stats
            $docker_stats = shell_exec('sudo docker stats --no-stream --format "table {{.MemUsage}}" 2>/dev/null');
            $used_mb = 0;
            
            if ($docker_stats) {
                // Parse memory usage from all containers
                $lines = explode("\n", trim($docker_stats));
                foreach ($lines as $line) {
                    if (preg_match('/(\d+(?:\.\d+)?)([KMGT]?i?B)\s*\//', $line, $matches)) {
                        $value = (float)$matches[1];
                        $unit = $matches[2];
                        
                        // Convert to MB
                        switch (strtoupper($unit)) {
                            case 'GB':
                            case 'GIB':
                                $used_mb += $value * 1024;
                                break;
                            case 'MB':
                            case 'MIB':
                                $used_mb += $value;
                                break;
                            case 'KB':
                            case 'KIB':
                                $used_mb += $value / 1024;
                                break;
                        }
                    }
                }
            }
            
            $available_mb = $total_mb - $used_mb;
            
            return [
                'total_mb' => $total_mb,
                'used_mb' => round($used_mb),
                'available_mb' => round($available_mb),
                'usage_percent' => round(($used_mb / $total_mb) * 100, 1)
            ];
        }
        
        // Fallback: read container's /proc/meminfo (will show container limits)
        $meminfo = @file_get_contents('/proc/meminfo');
        
        if ($meminfo) {
            preg_match('/MemTotal:\s+(\d+)\s+kB/', $meminfo, $total_match);
            preg_match('/MemAvailable:\s+(\d+)\s+kB/', $meminfo, $available_match);
            
            if ($total_match && $available_match) {
                $total_kb = (int)$total_match[1];
                $available_kb = (int)$available_match[1];
                $used_kb = $total_kb - $available_kb;
                
                return [
                    'total_mb' => round($total_kb / 1024),
                    'used_mb' => round($used_kb / 1024),
                    'available_mb' => round($available_kb / 1024),
                    'usage_percent' => round(($used_kb / $total_kb) * 100, 1)
                ];
            }
        }
        
        return [
            'total_mb' => 0,
            'used_mb' => 0,
            'available_mb' => 0,
            'usage_percent' => 0
        ];
        
    } catch (Exception $e) {
        return [
            'total_mb' => 0,
            'used_mb' => 0,
            'available_mb' => 0,
            'usage_percent' => 0
        ];
    }
}

function getNodeDetails() {
    $node_id = $_GET['node_id'] ?? 1;
    $port = 8000 + $node_id;
    
    try {
        // Get health data
        $health = makeNodeRequest("http://host.docker.internal:{$port}/health");
        
        // Get metrics data
        $metrics = makeNodeRequest("http://host.docker.internal:{$port}/metrics", 2);
        
        $heartbeats = 0;
        $elections = 0;
        
        if (is_string($metrics)) {
            $heartbeats = extractMetricValue($metrics, "node_{$node_id}_heartbeats_total");
            $elections = extractMetricValue($metrics, "node_{$node_id}_elections_total");
        }
        
        return [
            'leader_id' => $health['leader_id'] ?? 'Unknown',
            'current_term' => $health['current_term'] ?? 0,
            'heartbeats' => (int)$heartbeats,
            'elections' => (int)$elections
        ];
        
    } catch (Exception $e) {
        return [
            'leader_id' => 'Unknown',
            'current_term' => 0,
            'heartbeats' => 'N/A',
            'elections' => 'N/A'
        ];
    }
}

// Auto-scaling functions - routed to Python service

function getScalingEvents() {
    $events_file = '/var/www/html/data/scaling_events.json';
    
    if (!file_exists($events_file)) {
        return [];
    }
    
    $events = json_decode(file_get_contents($events_file), true) ?: [];
    return array_slice($events, -50); // Return last 50 events
}

function hasAutoScalingPolicy($app_name) {
    $policies_file = '/var/www/html/data/scaling_policies.json';
    
    if (!file_exists($policies_file)) {
        return false;
    }
    
    $policies = json_decode(file_get_contents($policies_file), true) ?: [];
    return isset($policies[$app_name]) && $policies[$app_name]['enabled'];
}

function evaluateScaling() {
    $policies_file = '/var/www/html/data/scaling_policies.json';
    
    if (!file_exists($policies_file)) {
        return ['actions' => []];
    }
    
    $policies = json_decode(file_get_contents($policies_file), true) ?: [];
    $scaling_actions = [];
    
    foreach ($policies as $app_name => $policy) {
        if (!$policy['enabled']) continue;
        
        $action = evaluateScalingPolicy($app_name, $policy);
        if ($action) {
            $scaling_actions[] = $action;
        }
    }
    
    return ['actions' => $scaling_actions];
}

function evaluateScalingPolicy($app_name, $policy) {
    // Get current application metrics
    $apps = getApplications();
    $app = null;
    
    foreach ($apps as $a) {
        if ($a['name'] === $app_name) {
            $app = $a;
            break;
        }
    }
    
    if (!$app) {
        return null;
    }
    
    // Parse current replicas
    $replicas_parts = explode('/', $app['replicas']);
    $current_replicas = (int)$replicas_parts[0];
    $desired_replicas = (int)$replicas_parts[1];
    
    // Check for failed containers that need replacement
    $container_health = checkContainerHealth($app_name);
    if ($container_health['failed_containers'] > 0 && $current_replicas < $desired_replicas) {
        return executeScalingAction($app_name, $desired_replicas, 'replace_failed', 'Replacing failed containers');
    }
    
    // Skip other scaling if app is not running
    if ($app['status'] !== 'running') {
        return null;
    }
    
    // Check cooldown (5 minutes)
    if (isInCooldown($app_name)) {
        return null;
    }
    
    // Get memory threshold in MB (convert percentage to actual MB based on container limits)
    $memory_limit_mb = getApplicationMemoryLimit($app_name);
    $memory_threshold_mb = ($policy['memoryThreshold'] / 100) * $memory_limit_mb;
    $memory_scale_down_mb = (($policy['memoryThreshold'] - 20) / 100) * $memory_limit_mb;
    
    // Scale up conditions
    if (($app['cpu_percent'] > $policy['cpuThreshold'] || $app['memory_mb'] > $memory_threshold_mb) && 
        $current_replicas < $policy['maxReplicas']) {
        
        $target_replicas = min($current_replicas + 1, $policy['maxReplicas']);
        return executeScalingAction($app_name, $target_replicas, 'scale_up', 'High resource usage');
    }
    
    // Scale down conditions
    if (($app['cpu_percent'] < ($policy['cpuThreshold'] - 20) && $app['memory_mb'] < $memory_scale_down_mb) && 
        $current_replicas > $policy['minReplicas']) {
        
        $target_replicas = max($current_replicas - 1, $policy['minReplicas']);
        return executeScalingAction($app_name, $target_replicas, 'scale_down', 'Low resource usage');
    }
    
    return null;
}

function executeScalingAction($app_name, $target_replicas, $action, $reason) {
    // Record scaling event
    recordScalingEvent($app_name, $action, $target_replicas, $reason);
    
    // Set cooldown
    setCooldown($app_name);
    
    // Execute actual scaling by adjusting container count
    $scale_result = scaleApplicationContainers($app_name, $target_replicas);
    
    return [
        'application' => $app_name,
        'action' => $action,
        'target_replicas' => $target_replicas,
        'reason' => $reason,
        'success' => $scale_result['success'] ?? false,
        'timestamp' => time()
    ];
}

function recordScalingEvent($app_name, $action, $replicas, $reason) {
    $events_file = '/var/www/html/data/scaling_events.json';
    $events = [];
    
    if (file_exists($events_file)) {
        $events = json_decode(file_get_contents($events_file), true) ?: [];
    }
    
    $events[] = [
        'application' => $app_name,
        'action' => $action,
        'replicas' => $replicas,
        'reason' => $reason,
        'timestamp' => time()
    ];
    
    // Keep only last 100 events
    if (count($events) > 100) {
        $events = array_slice($events, -100);
    }
    
    file_put_contents($events_file, json_encode($events, JSON_PRETTY_PRINT));
}

function isInCooldown($app_name) {
    $cooldown_file = '/var/www/html/data/cooldowns.json';
    
    if (!file_exists($cooldown_file)) {
        return false;
    }
    
    $cooldowns = json_decode(file_get_contents($cooldown_file), true) ?: [];
    
    if (!isset($cooldowns[$app_name])) {
        return false;
    }
    
    return (time() - $cooldowns[$app_name]) < 300; // 5 minute cooldown
}

function setCooldown($app_name) {
    $cooldown_file = '/var/www/html/data/cooldowns.json';
    $cooldowns = [];
    
    if (file_exists($cooldown_file)) {
        $cooldowns = json_decode(file_get_contents($cooldown_file), true) ?: [];
    }
    
    $cooldowns[$app_name] = time();
    file_put_contents($cooldown_file, json_encode($cooldowns, JSON_PRETTY_PRINT));
}

function getApplicationDetails() {
    $app_name = $_GET['app_name'] ?? '';
    
    if (empty($app_name)) {
        return ['error' => 'Application name required'];
    }
    
    try {
        // Get basic app info
        $apps = getApplications();
        $app = null;
        foreach ($apps as $a) {
            if ($a['name'] === $app_name) {
                $app = $a;
                break;
            }
        }
        
        if (!$app) {
            return ['error' => 'Application not found'];
        }
        
        // Get container details
        $containers = [];
        $containers_output = shell_exec("sudo docker ps -a --filter \"name=app-{$app_name}-\" --format \"{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}\t{{.CreatedAt}}\t{{.ID}}\" 2>/dev/null");
        
        if ($containers_output) {
            $lines = explode("\n", trim($containers_output));
            foreach ($lines as $line) {
                if (empty($line)) continue;
                $parts = explode("\t", $line);
                if (count($parts) >= 6) {
                    $containers[] = [
                        'name' => $parts[0],
                        'status' => $parts[1],
                        'image' => $parts[2],
                        'ports' => $parts[3],
                        'created' => $parts[4],
                        'id' => substr($parts[5], 0, 12)
                    ];
                }
            }
        }
        
        // Get scaling policy if exists
        $scaling_policy = null;
        $policies_file = '/var/www/html/data/scaling_policies.json';
        if (file_exists($policies_file)) {
            $policies = json_decode(file_get_contents($policies_file), true) ?: [];
            $scaling_policy = $policies[$app_name] ?? null;
        }
        
        // Get deployment info
        $deployment_info = [];
        $app_dir = "/var/www/html/data/apps/{$app_name}";
        if (file_exists("{$app_dir}/app.yaml")) {
            $yaml_content = file_get_contents("{$app_dir}/app.yaml");
            $deployment_info['yaml'] = $yaml_content;
        }
        if (file_exists("{$app_dir}/deployed_at.txt")) {
            $deployed_at = (int)file_get_contents("{$app_dir}/deployed_at.txt");
            $deployment_info['deployed_at'] = date('Y-m-d H:i:s', $deployed_at);
        }
        
        // Get recent scaling events
        $recent_events = [];
        $events_file = '/var/www/html/data/scaling_events.json';
        if (file_exists($events_file)) {
            $events = json_decode(file_get_contents($events_file), true) ?: [];
            foreach ($events as $event) {
                if ($event['application'] === $app_name) {
                    $recent_events[] = $event;
                }
            }
            $recent_events = array_slice(array_reverse($recent_events), 0, 5);
        }
        
        return [
            'application' => $app,
            'containers' => $containers,
            'scaling_policy' => $scaling_policy,
            'deployment_info' => $deployment_info,
            'recent_events' => $recent_events
        ];
        
    } catch (Exception $e) {
        return ['error' => $e->getMessage()];
    }
}

// Modified handleScaleApplication to accept array parameter
function checkContainerHealth($app_name) {
    $failed_containers = 0;
    $total_containers = 0;
    $failed_details = [];
    
    try {
        // Get all containers for this application (including stopped ones)
        $containers_output = shell_exec("sudo docker ps -a --filter \"name=app-{$app_name}-\" --format \"{{.Names}}\t{{.Status}}\t{{.ExitCode}}\" 2>/dev/null");
        
        if ($containers_output) {
            $lines = explode("\n", trim($containers_output));
            foreach ($lines as $line) {
                if (empty($line)) continue;
                $parts = explode("\t", $line);
                if (count($parts) >= 2) {
                    $container_name = $parts[0];
                    $status = $parts[1];
                    $exit_code = $parts[2] ?? '';
                    
                    $total_containers++;
                    
                    // Check if container has failed (exited with non-zero code or unhealthy)
                    if (strpos($status, 'Exited') === 0) {
                        $failed_containers++;
                        $failed_details[] = [
                            'name' => $container_name,
                            'status' => $status,
                            'exit_code' => $exit_code
                        ];
                    }
                }
            }
        }
        
        return [
            'failed_containers' => $failed_containers,
            'total_containers' => $total_containers,
            'failed_details' => $failed_details
        ];
        
    } catch (Exception $e) {
        return [
            'failed_containers' => 0,
            'total_containers' => 0,
            'failed_details' => []
        ];
    }
}

function getApplicationMetrics($app_name) {
    try {
        $cpu_total = 0;
        $memory_total = 0;
        $container_count = 0;
        
        // Get stats for all running containers of this application
        $containers_output = shell_exec("sudo docker ps --filter \"name=app-{$app_name}-\" --format \"{{.Names}}\" 2>/dev/null");
        
        if ($containers_output) {
            $container_names = explode("\n", trim($containers_output));
            
            foreach ($container_names as $container_name) {
                if (empty($container_name)) continue;
                
                // Get container stats
                $stats_output = shell_exec("sudo docker stats {$container_name} --no-stream --format \"{{.CPUPerc}},{{.MemUsage}}\" 2>/dev/null");
                
                if ($stats_output) {
                    $stats = explode(',', trim($stats_output));
                    if (count($stats) >= 2) {
                        // Parse CPU percentage
                        $cpu_str = str_replace('%', '', $stats[0]);
                        if (is_numeric($cpu_str)) {
                            $cpu_total += (float)$cpu_str;
                        }
                        
                        // Parse memory usage (extract MB value)
                        if (preg_match('/(\d+(?:\.\d+)?)([KMGT]?i?B)/', $stats[1], $matches)) {
                            $value = (float)$matches[1];
                            $unit = strtoupper($matches[2]);
                            
                            switch ($unit) {
                                case 'GB':
                                case 'GIB':
                                    $memory_total += $value * 1024;
                                    break;
                                case 'MB':
                                case 'MIB':
                                    $memory_total += $value;
                                    break;
                                case 'KB':
                                case 'KIB':
                                    $memory_total += $value / 1024;
                                    break;
                            }
                        }
                        
                        $container_count++;
                    }
                }
            }
        }
        
        return [
            'cpu_percent' => $container_count > 0 ? round($cpu_total / $container_count, 1) : 0,
            'memory_mb' => round($memory_total)
        ];
        
    } catch (Exception $e) {
        return [
            'cpu_percent' => 0,
            'memory_mb' => 0
        ];
    }
}

function getContainerDetails() {
    $container_name = $_GET['container_name'] ?? '';
    
    if (empty($container_name)) {
        return ['error' => 'Container name required'];
    }
    
    try {
        // Get container inspect information
        $inspect_output = shell_exec("sudo docker inspect {$container_name} 2>/dev/null");
        $inspect_data = json_decode($inspect_output, true);
        
        if (!$inspect_data || empty($inspect_data)) {
            return ['error' => 'Container not found'];
        }
        
        $container = $inspect_data[0];
        
        // Get container logs (last 50 lines)
        $logs_output = shell_exec("sudo docker logs --tail 50 {$container_name} 2>&1");
        
        // Get container stats if running
        $stats = null;
        if ($container['State']['Running']) {
            $stats_output = shell_exec("sudo docker stats {$container_name} --no-stream --format \"{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}\" 2>/dev/null");
            if ($stats_output) {
                $stats_parts = explode(',', trim($stats_output));
                $stats = [
                    'cpu' => $stats_parts[0] ?? '0%',
                    'memory' => $stats_parts[1] ?? '0B / 0B',
                    'network' => $stats_parts[2] ?? '0B / 0B',
                    'block_io' => $stats_parts[3] ?? '0B / 0B'
                ];
            }
        }
        
        return [
            'name' => $container['Name'],
            'id' => $container['Id'],
            'image' => $container['Config']['Image'],
            'state' => $container['State'],
            'created' => $container['Created'],
            'logs' => $logs_output ?: 'No logs available',
            'stats' => $stats
        ];
        
    } catch (Exception $e) {
        return ['error' => $e->getMessage()];
    }
}
?>