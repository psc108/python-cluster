<?php
// Initialize ML data structure for dashboard

// Create dashboard-data directory structure
$base_dir = '/var/www/html/dashboard-data';
$ml_dir = $base_dir . '/ml';

if (!file_exists($base_dir)) {
    mkdir($base_dir, 0755, true);
}

if (!file_exists($ml_dir)) {
    mkdir($ml_dir, 0755, true);
}

// Create sample ML policies file
$ml_policies_file = $base_dir . '/ml_scaling_policies.json';
if (!file_exists($ml_policies_file)) {
    $sample_policies = [];
    file_put_contents($ml_policies_file, json_encode($sample_policies, JSON_PRETTY_PRINT));
}

// Create sample training data
$training_data_file = $ml_dir . '/metrics_timeseries.json';
if (!file_exists($training_data_file)) {
    $sample_training_data = [];
    
    // Generate some sample data points
    $apps = ['web-app', 'api-service', 'worker'];
    $base_time = time() - (24 * 3600); // 24 hours ago
    
    for ($i = 0; $i < 200; $i++) {
        $timestamp = $base_time + ($i * 300); // Every 5 minutes
        $app = $apps[array_rand($apps)];
        
        $sample_training_data[] = [
            'timestamp' => date('Y-m-d H:i:s', $timestamp),
            'application' => $app,
            'cpu_percent' => rand(20, 90),
            'memory_percent' => rand(30, 85),
            'replicas' => rand(1, 5),
            'request_rate' => rand(10, 100)
        ];
    }
    
    file_put_contents($training_data_file, json_encode($sample_training_data, JSON_PRETTY_PRINT));
}

// Create sample predictions file
$predictions_file = $base_dir . '/ml_predictions.json';
if (!file_exists($predictions_file)) {
    $sample_predictions = [];
    
    for ($i = 0; $i < 20; $i++) {
        $timestamp = time() - (rand(1, 3600)); // Random time in last hour
        $app = $apps[array_rand($apps)];
        
        $sample_predictions[] = [
            'timestamp' => date('Y-m-d H:i:s', $timestamp),
            'application' => $app,
            'predicted_cpu' => rand(40, 95),
            'predicted_memory' => rand(35, 90),
            'recommended_replicas' => rand(2, 6),
            'confidence' => rand(60, 95),
            'action_taken' => rand(0, 1) ? 'scale_up' : 'None'
        ];
    }
    
    file_put_contents($predictions_file, json_encode($sample_predictions, JSON_PRETTY_PRINT));
}

echo "ML data structure initialized successfully\n";
?>