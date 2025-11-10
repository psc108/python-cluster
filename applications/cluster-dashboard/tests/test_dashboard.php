<?php
// Simple test suite for the dashboard application

class DashboardTests {
    private $base_url;
    
    public function __construct($base_url = 'http://localhost') {
        $this->base_url = $base_url;
    }
    
    public function runAllTests() {
        echo "Running Dashboard Tests...\n";
        echo "========================\n\n";
        
        $tests = [
            'testHealthEndpoint',
            'testMainPage',
            'testClusterAPI',
            'testStaticAssets'
        ];
        
        $passed = 0;
        $total = count($tests);
        
        foreach ($tests as $test) {
            echo "Running {$test}... ";
            try {
                $result = $this->$test();
                if ($result) {
                    echo "PASS\n";
                    $passed++;
                } else {
                    echo "FAIL\n";
                }
            } catch (Exception $e) {
                echo "ERROR: " . $e->getMessage() . "\n";
            }
        }
        
        echo "\n========================\n";
        echo "Tests: {$passed}/{$total} passed\n";
        
        return $passed === $total;
    }
    
    private function testHealthEndpoint() {
        $response = $this->makeRequest('/health.php');
        
        if (!$response) {
            return false;
        }
        
        $data = json_decode($response, true);
        
        // Check required fields
        $required_fields = ['status', 'timestamp', 'checks', 'metrics', 'application'];
        foreach ($required_fields as $field) {
            if (!isset($data[$field])) {
                echo "Missing field: {$field} ";
                return false;
            }
        }
        
        // Check status values
        if (!in_array($data['status'], ['healthy', 'unhealthy', 'degraded'])) {
            echo "Invalid status value ";
            return false;
        }
        
        return true;
    }
    
    private function testMainPage() {
        $response = $this->makeRequest('/index.php');
        
        if (!$response) {
            return false;
        }
        
        // Check for essential HTML elements
        $required_elements = [
            '<title>Cluster Dashboard</title>',
            'id="cluster-status"',
            'id="overview"',
            'id="nodes"',
            'id="applications"',
            'id="metrics"',
            'id="storage"'
        ];
        
        foreach ($required_elements as $element) {
            if (strpos($response, $element) === false) {
                echo "Missing element: {$element} ";
                return false;
            }
        }
        
        return true;
    }
    
    private function testClusterAPI() {
        $endpoints = [
            '/api/cluster.php?action=status',
            '/api/cluster.php?action=nodes',
            '/api/cluster.php?action=applications',
            '/api/cluster.php?action=metrics',
            '/api/cluster.php?action=storage'
        ];
        
        foreach ($endpoints as $endpoint) {
            $response = $this->makeRequest($endpoint);
            
            if (!$response) {
                echo "Failed to fetch {$endpoint} ";
                return false;
            }
            
            $data = json_decode($response, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                echo "Invalid JSON from {$endpoint} ";
                return false;
            }
        }
        
        return true;
    }
    
    private function testStaticAssets() {
        $assets = [
            '/assets/css/dashboard.css',
            '/assets/js/dashboard.js'
        ];
        
        foreach ($assets as $asset) {
            $response = $this->makeRequest($asset);
            
            if (!$response) {
                echo "Failed to load {$asset} ";
                return false;
            }
            
            // Check minimum file size (should not be empty)
            if (strlen($response) < 100) {
                echo "Asset too small: {$asset} ";
                return false;
            }
        }
        
        return true;
    }
    
    private function makeRequest($path, $timeout = 5) {
        $url = $this->base_url . $path;
        
        $context = stream_context_create([
            'http' => [
                'timeout' => $timeout,
                'method' => 'GET',
                'header' => 'User-Agent: Dashboard-Test/1.0'
            ]
        ]);
        
        return @file_get_contents($url, false, $context);
    }
}

// Run tests if called directly
if (php_sapi_name() === 'cli') {
    $base_url = $argv[1] ?? 'http://localhost';
    $tests = new DashboardTests($base_url);
    $success = $tests->runAllTests();
    exit($success ? 0 : 1);
}
?>