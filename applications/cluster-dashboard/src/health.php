<?php
header('Content-Type: application/json');

// Health check endpoint for the application framework
$health_data = [
    'status' => 'healthy',
    'timestamp' => date('c'),
    'checks' => [
        'web_server' => 'healthy',
        'file_system' => is_writable('/var/www/html/data') ? 'healthy' : 'unhealthy',
        'cluster_connection' => checkClusterConnection()
    ],
    'metrics' => [
        'requests_per_second' => getRequestRate(),
        'error_rate' => 0.0,
        'response_time_ms' => getAverageResponseTime(),
        'memory_usage_mb' => round(memory_get_usage(true) / 1024 / 1024, 2)
    ],
    'application' => [
        'name' => 'cluster-dashboard',
        'version' => '1.0.0',
        'node_id' => gethostname(),
        'uptime' => getUptime()
    ]
];

// Determine overall health status
$overall_healthy = true;
foreach ($health_data['checks'] as $check => $status) {
    if ($status !== 'healthy') {
        $overall_healthy = false;
        break;
    }
}

$health_data['status'] = $overall_healthy ? 'healthy' : 'unhealthy';

// Set appropriate HTTP status code
http_response_code($overall_healthy ? 200 : 503);

echo json_encode($health_data, JSON_PRETTY_PRINT);

function checkClusterConnection() {
    $cluster_url = getenv('CLUSTER_API_URL') ?: 'http://cluster-node-1:8000';
    
    $context = stream_context_create([
        'http' => [
            'timeout' => 2,
            'method' => 'GET'
        ]
    ]);
    
    $result = @file_get_contents($cluster_url . '/health', false, $context);
    return $result !== false ? 'healthy' : 'unhealthy';
}

function getRequestRate() {
    // Simple request rate calculation based on access log
    $log_file = '/var/log/apache2/dashboard_access.log';
    if (!file_exists($log_file)) {
        return 0;
    }
    
    $lines = @file($log_file);
    if (!$lines) {
        return 0;
    }
    
    // Count requests in last minute
    $one_minute_ago = time() - 60;
    $recent_requests = 0;
    
    foreach (array_reverse(array_slice($lines, -100)) as $line) {
        if (preg_match('/\[(\d{2}\/\w{3}\/\d{4}:\d{2}:\d{2}:\d{2})/', $line, $matches)) {
            $timestamp = strtotime(str_replace(':', ' ', $matches[1]));
            if ($timestamp >= $one_minute_ago) {
                $recent_requests++;
            } else {
                break;
            }
        }
    }
    
    return round($recent_requests / 60, 2);
}

function getAverageResponseTime() {
    // Simulate response time calculation
    return rand(10, 50);
}

function getUptime() {
    $uptime_file = '/var/www/html/data/uptime.txt';
    
    if (!file_exists($uptime_file)) {
        file_put_contents($uptime_file, time());
        return 0;
    }
    
    $start_time = (int)file_get_contents($uptime_file);
    return time() - $start_time;
}
?>