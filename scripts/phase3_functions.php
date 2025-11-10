<?php
// Phase 3: Scheduled Scaling Functions

function getScheduledPolicies() {
    $schedules_file = '/var/www/html/data/scheduled_policies.json';
    
    if (!file_exists($schedules_file)) {
        return [];
    }
    
    return json_decode(file_get_contents($schedules_file), true) ?: [];
}

function handleCreateScheduledPolicy() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($input['application']) || !isset($input['schedule_name']) || !isset($input['time']) || !isset($input['days'])) {
        return ['success' => false, 'error' => 'Missing required fields'];
    }
    
    $schedules_file = '/var/www/html/data/scheduled_policies.json';
    $policies = [];
    
    if (file_exists($schedules_file)) {
        $policies = json_decode(file_get_contents($schedules_file), true) ?: [];
    }
    
    // Find or create application policy
    $app_policy = null;
    foreach ($policies as &$policy) {
        if ($policy['application'] === $input['application']) {
            $app_policy = &$policy;
            break;
        }
    }
    
    if (!$app_policy) {
        $app_policy = [
            'application' => $input['application'],
            'enabled' => true,
            'schedules' => []
        ];
        $policies[] = &$app_policy;
    }
    
    // Add new schedule
    $schedule = [
        'name' => $input['schedule_name'],
        'time' => $input['time'],
        'days' => $input['days'],
        'replicas' => (int)$input['target_replicas'],
        'enabled' => true,
        'created_at' => time()
    ];
    
    $app_policy['schedules'][] = $schedule;
    
    if (!file_exists('/var/www/html/data')) {
        mkdir('/var/www/html/data', 0755, true);
    }
    
    file_put_contents($schedules_file, json_encode($policies, JSON_PRETTY_PRINT));
    
    return ['success' => true, 'schedule' => $schedule];
}

function handleDeleteScheduledPolicy() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($input['application']) || !isset($input['schedule_name'])) {
        return ['success' => false, 'error' => 'Missing required fields'];
    }
    
    $schedules_file = '/var/www/html/data/scheduled_policies.json';
    
    if (!file_exists($schedules_file)) {
        return ['success' => false, 'error' => 'No scheduled policies found'];
    }
    
    $policies = json_decode(file_get_contents($schedules_file), true) ?: [];
    $found = false;
    
    foreach ($policies as &$policy) {
        if ($policy['application'] === $input['application']) {
            $policy['schedules'] = array_filter($policy['schedules'], function($schedule) use ($input) {
                return $schedule['name'] !== $input['schedule_name'];
            });
            $policy['schedules'] = array_values($policy['schedules']); // Re-index array
            $found = true;
            break;
        }
    }
    
    if (!$found) {
        return ['success' => false, 'error' => 'Schedule not found'];
    }
    
    file_put_contents($schedules_file, json_encode($policies, JSON_PRETTY_PRINT));
    
    return ['success' => true];
}

function getScheduleHistory() {
    $history_file = '/var/www/html/data/schedule_history.json';
    
    if (!file_exists($history_file)) {
        return [];
    }
    
    $history = json_decode(file_get_contents($history_file), true) ?: [];
    return array_slice($history, -50); // Return last 50 events
}

function getScheduleSummary() {
    $schedules = getScheduledPolicies();
    $active_count = 0;
    
    foreach ($schedules as $policy) {
        if ($policy['enabled']) {
            foreach ($policy['schedules'] as $schedule) {
                if ($schedule['enabled']) {
                    $active_count++;
                }
            }
        }
    }
    
    // Count today's actions from history
    $history = getScheduleHistory();
    $today_start = strtotime('today');
    $todays_actions = 0;
    
    foreach ($history as $event) {
        if (strtotime($event['timestamp']) >= $today_start) {
            $todays_actions++;
        }
    }
    
    return [
        'active_schedules' => $active_count,
        'next_execution' => 'None scheduled',
        'todays_actions' => $todays_actions
    ];
}

// Phase 3: Analytics Functions

function getScalingAnalytics() {
    $events_file = '/var/www/html/data/scaling_events.json';
    
    // Load events for analysis
    $events = [];
    if (file_exists($events_file)) {
        $events = json_decode(file_get_contents($events_file), true) ?: [];
    }
    
    // Calculate analytics for last 24 hours
    $now = time();
    $day_ago = $now - 86400;
    
    $recent_events = array_filter($events, function($event) use ($day_ago) {
        return $event['timestamp'] >= $day_ago;
    });
    
    $total_events = count($recent_events);
    $scale_up_events = count(array_filter($recent_events, function($e) { return $e['action'] === 'scale_up'; }));
    $scale_down_events = count(array_filter($recent_events, function($e) { return $e['action'] === 'scale_down'; }));
    
    // Per-application analytics
    $app_analytics = [];
    $apps_with_events = array_unique(array_column($recent_events, 'application'));
    
    foreach ($apps_with_events as $app_name) {
        $app_events = array_filter($recent_events, function($e) use ($app_name) {
            return $e['application'] === $app_name;
        });
        
        $app_scale_up = count(array_filter($app_events, function($e) { return $e['action'] === 'scale_up'; }));
        $app_scale_down = count(array_filter($app_events, function($e) { return $e['action'] === 'scale_down'; }));
        
        // Calculate actual decision score from events
        $decision_scores = array_column($app_events, 'decision_score');
        $avg_decision_score = !empty($decision_scores) ? array_sum($decision_scores) / count($decision_scores) : 0;
        
        // Calculate efficiency based on successful scaling actions
        $successful_events = array_filter($app_events, function($e) { return isset($e['success']) && $e['success']; });
        $efficiency = count($app_events) > 0 ? count($successful_events) / count($app_events) : 0;
        
        $app_analytics[$app_name] = [
            'total_events' => count($app_events),
            'scale_up_events' => $app_scale_up,
            'scale_down_events' => $app_scale_down,
            'avg_decision_score' => round($avg_decision_score, 2),
            'efficiency' => round($efficiency, 2)
        ];
    }
    
    // Calculate overall efficiency from all events
    $all_successful = array_filter($recent_events, function($e) { return isset($e['success']) && $e['success']; });
    $overall_efficiency = $total_events > 0 ? count($all_successful) / $total_events : 0;
    
    // Calculate average response time from event timestamps
    $response_times = [];
    foreach ($recent_events as $event) {
        if (isset($event['response_time'])) {
            $response_times[] = $event['response_time'];
        }
    }
    $avg_response_time = !empty($response_times) ? array_sum($response_times) / count($response_times) : 0;
    
    return [
        'efficiency_score' => round($overall_efficiency, 2),
        'total_events_24h' => $total_events,
        'avg_response_time' => round($avg_response_time, 1),
        'cost_savings' => round($total_events * 0.02, 2), // $0.02 per scaling action
        'applications' => $app_analytics,
        'last_updated' => date('Y-m-d H:i:s')
    ];
}

function getCostSavingsBreakdown() {
    $events_file = '/var/www/html/data/scaling_events.json';
    
    // Load events for analysis
    $events = [];
    if (file_exists($events_file)) {
        $events = json_decode(file_get_contents($events_file), true) ?: [];
    }
    
    // Filter last 24 hours
    $now = time();
    $day_ago = $now - 86400;
    
    $recent_events = array_filter($events, function($event) use ($day_ago) {
        return $event['timestamp'] >= $day_ago;
    });
    
    // Calculate scale down events and savings
    $scale_down_events = array_filter($recent_events, function($e) { 
        return $e['action'] === 'scale_down'; 
    });
    $scale_down_count = count($scale_down_events);
    
    // Calculate container hours saved from scale-down events
    $container_hours_saved = 0;
    foreach ($scale_down_events as $event) {
        $containers_removed = isset($event['from_replicas']) && isset($event['to_replicas']) 
            ? $event['from_replicas'] - $event['to_replicas'] 
            : 1;
        $container_hours_saved += $containers_removed * 1; // Assume 1 hour average
    }
    
    // Resource optimization savings
    $scale_down_savings = $container_hours_saved * 0.05; // $0.05 per container hour
    $over_provision_hours = $container_hours_saved * 0.8; // 80% would have been over-provisioning
    $over_provision_savings = $over_provision_hours * 0.02; // $0.02 per hour over-provision cost
    
    // Operational efficiency savings
    $total_auto_actions = count($recent_events);
    $manual_prevention_count = $total_auto_actions; // Each auto action prevents manual intervention
    $manual_prevention_savings = $manual_prevention_count * 2.0; // $2.00 per manual action prevented
    
    // Response time savings (auto-scaling is faster than manual)
    $avg_manual_response_minutes = 15; // Average time for manual scaling
    $avg_auto_response_minutes = 2;   // Auto-scaling response time
    $response_time_minutes_saved = ($avg_manual_response_minutes - $avg_auto_response_minutes) * $total_auto_actions;
    $response_time_cost = $response_time_minutes_saved * 0.10; // $0.10 per minute saved
    
    return [
        'scale_down_events' => $scale_down_count,
        'scale_down_savings' => round($scale_down_savings, 2),
        'over_provision_hours' => round($over_provision_hours, 1),
        'over_provision_savings' => round($over_provision_savings, 2),
        'manual_prevention_count' => $manual_prevention_count,
        'manual_prevention_savings' => round($manual_prevention_savings, 2),
        'response_time_minutes' => round($response_time_minutes_saved, 1),
        'response_time_cost' => round($response_time_cost, 2),
        'calculation_timestamp' => date('Y-m-d H:i:s')
    ];
}