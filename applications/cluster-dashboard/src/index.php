<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cluster Dashboard</title>
    <link rel="stylesheet" href="assets/css/dashboard.css">
    <script src="assets/js/dashboard.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔧 Cluster Dashboard</h1>
            <div class="status-indicator" id="cluster-status">
                <span class="status-dot"></span>
                <span class="status-text">Connecting...</span>
            </div>
        </header>

        <nav class="nav-tabs">
            <button class="tab-button active" onclick="showTab('overview')">Overview</button>
            <button class="tab-button" onclick="showTab('nodes')">Nodes</button>
            <button class="tab-button" onclick="showTab('applications')">Applications</button>
            <button class="tab-button" onclick="showTab('autoscaling')">Auto-Scaling</button>
            <button class="tab-button" onclick="showTab('metrics')">Metrics</button>
            <button class="tab-button" onclick="showTab('storage')">Storage</button>
        </nav>

        <main>
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="cards-grid">
                    <div class="card">
                        <h3>Cluster Status</h3>
                        <div id="cluster-info">
                            <p><strong>Leader:</strong> <span id="leader-node">Loading...</span></p>
                            <p><strong>Total Nodes:</strong> <span id="total-nodes">-</span></p>
                            <p><strong>Healthy Nodes:</strong> <span id="healthy-nodes">-</span></p>
                            <p><strong>Uptime:</strong> <span id="cluster-uptime">-</span></p>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Applications</h3>
                        <div id="apps-summary">
                            <p><strong>Running:</strong> <span id="running-apps">-</span></p>
                            <p><strong>Total Instances:</strong> <span id="total-instances">-</span></p>
                            <p><strong>Failed:</strong> <span id="failed-apps">-</span></p>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Resource Usage</h3>
                        <div id="resource-usage">
                            <div class="progress-bar">
                                <label>CPU Usage</label>
                                <div class="progress">
                                    <div class="progress-fill" id="cpu-progress"></div>
                                </div>
                                <span id="cpu-percent">0%</span>
                            </div>
                            <div class="progress-bar">
                                <label>Memory Usage</label>
                                <div class="progress">
                                    <div class="progress-fill" id="memory-progress"></div>
                                </div>
                                <span id="memory-percent">0%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Nodes Tab -->
            <div id="nodes" class="tab-content">
                <div class="table-container">
                    <table id="nodes-table">
                        <thead>
                            <tr>
                                <th>Node ID</th>
                                <th>Status</th>
                                <th>Role</th>
                                <th>CPU</th>
                                <th>Memory</th>
                                <th>Uptime</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="nodes-tbody">
                            <tr><td colspan="7">Loading nodes...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Applications Tab -->
            <div id="applications" class="tab-content">
                <div class="app-controls">
                    <button class="btn btn-primary" onclick="refreshApplications()">Refresh</button>
                    <button class="btn btn-secondary" onclick="showDeployForm()">Deploy App</button>
                </div>
                <div class="table-container">
                    <table id="apps-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Auto-Scale</th>
                                <th>Status</th>
                                <th>Replicas</th>
                                <th>CPU</th>
                                <th>Memory</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="apps-tbody">
                            <tr><td colspan="7">Loading applications...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Auto-Scaling Tab -->
            <div id="autoscaling" class="tab-content">
                <div class="autoscaling-controls">
                    <button class="btn btn-primary" onclick="refreshPolicies()">Refresh Policies</button>
                    <button class="btn btn-secondary" onclick="showCreatePolicyModal()">Create Policy</button>
                    <button class="btn btn-secondary" onclick="showCreateScheduledPolicyModal()">Create Schedule</button>
                    <button class="btn btn-info" onclick="showAnalyticsModal()">View Analytics</button>
                </div>
                
                <!-- ML PREDICTIVE SCALING SECTION -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: white; margin-bottom: 15px;">🤖 ML Predictive Scaling</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div>
                            <p><strong>ML Policies:</strong> <span id="ml-policies-count">0</span></p>
                            <p><strong>Training Data Points:</strong> <span id="training-data-points">0</span></p>
                        </div>
                        <div>
                            <p><strong>Models Trained:</strong> <span id="models-trained">0</span></p>
                            <p><strong>Last Prediction:</strong> <span id="last-prediction">None</span></p>
                        </div>
                        <div>
                            <p><strong>Prediction Accuracy:</strong> <span id="prediction-accuracy">N/A</span></p>
                            <p><strong>Data Collection:</strong> <span id="data-collection-status">Inactive</span></p>
                        </div>
                    </div>
                    <div style="margin-top: 15px;">
                        <button class="btn" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3);" onclick="showCreateMLPolicyModal()">Create ML Policy</button>
                        <button class="btn" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); margin-left: 10px;" onclick="showMLAnalyticsModal()">ML Analytics</button>
                        <button class="btn" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); margin-left: 10px;" onclick="showMultiHorizonPredictions()">Multi-Horizon</button>
                        <button class="btn" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); margin-left: 10px;" onclick="showAnomalyDetection()">Anomaly Detection</button>
                        <button class="btn" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); margin-left: 10px;" onclick="showPredictionService()">Prediction Service</button>
                        <button class="btn" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); margin-left: 10px;" onclick="showModelWeightsConfig()">Configure Weights</button>
                        <button class="btn" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); margin-left: 10px;" onclick="showAutoRetrainingConfig()">Auto-Retrain Config</button>
                        <button class="btn" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); margin-left: 10px;" onclick="showProactiveScalingConfig()">Proactive Scaling</button>
                    </div>
                </div>
                
                <!-- Auto-Scaling Sub-tabs -->
                <div class="sub-nav-tabs" style="display: flex; background: #f8f9fa; border-radius: 8px; padding: 3px; margin-bottom: 20px; border: 1px solid #e9ecef;">
                    <button class="sub-tab-button active" onclick="showAutoScalingSubTab('policies')" style="flex: 1; padding: 10px 15px; border: none; background: #3498db; color: white; font-size: 0.9rem; font-weight: 500; cursor: pointer; border-radius: 6px; margin-right: 3px;">Policies</button>
                    <button class="sub-tab-button" onclick="showAutoScalingSubTab('ml')" style="flex: 1; padding: 10px 15px; border: none; background: transparent; color: #6c757d; font-size: 0.9rem; font-weight: 500; cursor: pointer; border-radius: 6px; margin-right: 3px;">ML Predictive</button>
                    <button class="sub-tab-button" onclick="showAutoScalingSubTab('events')" style="flex: 1; padding: 10px 15px; border: none; background: transparent; color: #6c757d; font-size: 0.9rem; font-weight: 500; cursor: pointer; border-radius: 6px;">Events</button>
                </div>
                
                <!-- Policies Sub-tab -->
                <div id="policies-subtab" class="sub-tab-content active">
                    <div class="cards-grid">
                        <div class="card">
                            <h3>Scaling Overview</h3>
                            <div id="scaling-summary">
                                <p><strong>Active Policies:</strong> <span id="active-policies">-</span></p>
                                <p><strong>Auto-Scaled Apps:</strong> <span id="autoscaled-apps">-</span></p>
                                <p><strong>Recent Actions:</strong> <span id="recent-actions">-</span></p>
                            </div>
                        </div>
                    </div>
                
                    <div class="table-container">
                        <h3>Scaling Policies</h3>
                        <table id="policies-table">
                            <thead>
                                <tr>
                                    <th>Application</th>
                                    <th>Type</th>
                                    <th>Min/Max Replicas</th>
                                    <th>Thresholds</th>
                                    <th>Cooldown</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="policies-tbody">
                                <tr><td colspan="7">Loading policies...</td></tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="table-container">
                        <h3>ML Predictive Scaling</h3>
                        <div style="background: #e8f4fd; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                            <h4>ML System Status</h4>
                            <p><strong>ML Policies:</strong> <span id="ml-policies-count">0</span></p>
                            <p><strong>Training Data Points:</strong> <span id="training-data-points">0</span></p>
                            <p><strong>Models Trained:</strong> <span id="models-trained">0</span></p>
                            <p><strong>Last Prediction:</strong> <span id="last-prediction">None</span></p>
                            <button class="btn btn-secondary" onclick="alert('ML Policy creation coming soon')">Create ML Policy</button>
                        </div>
                    </div>
                    
                    <div class="table-container">
                        <h3>Scheduled Policies</h3>
                        <table id="scheduled-policies-table">
                            <thead>
                                <tr>
                                    <th>Application</th>
                                    <th>Schedule Name</th>
                                    <th>Time</th>
                                    <th>Days</th>
                                    <th>Target Replicas</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="scheduled-policies-tbody">
                                <tr><td colspan="7">Loading scheduled policies...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- ML Predictive Sub-tab -->
                <div id="ml-subtab" class="sub-tab-content">
                    <div class="ml-controls">
                        <button class="btn btn-primary" onclick="refreshMLData()">Refresh ML Status</button>
                        <button class="btn btn-secondary" onclick="showCreateMLPolicyModal()">Create ML Policy</button>
                        <button class="btn btn-info" onclick="showMLAnalyticsModal()">ML Analytics</button>
                        <button class="btn btn-success" onclick="showMultiHorizonPredictions()">Multi-Horizon Predictions</button>
                        <button class="btn btn-warning" onclick="showAnomalyDetection()">Anomaly Detection</button>
                        <button class="btn btn-info" onclick="showPredictionService()">Prediction Service</button>
                        <button class="btn btn-secondary" onclick="showModelWeightsConfig()">Configure Weights</button>
                        <button class="btn btn-warning" onclick="showAutoRetrainingConfig()">Auto-Retrain Config</button>
                        <button class="btn btn-success" onclick="showProactiveScalingConfig()">Proactive Scaling</button>
                    </div>
                    
                    <div class="cards-grid">
                        <div class="card">
                            <h3>ML System Status</h3>
                            <div id="ml-system-status">
                                <p><strong>ML Policies:</strong> <span id="ml-policies-count">-</span></p>
                                <p><strong>Training Data Points:</strong> <span id="training-data-points">-</span></p>
                                <p><strong>Models Trained:</strong> <span id="models-trained">-</span></p>
                                <p><strong>Last Prediction:</strong> <span id="last-prediction">-</span></p>
                            </div>
                        </div>
                        <div class="card">
                            <h3>ML Performance</h3>
                            <div id="ml-performance">
                                <p><strong>Prediction Accuracy:</strong> <span id="prediction-accuracy">-</span></p>
                                <p><strong>Avg Confidence:</strong> <span id="avg-confidence">-</span></p>
                                <p><strong>ML Scaling Actions:</strong> <span id="ml-scaling-actions">-</span></p>
                                <p><strong>Data Collection:</strong> <span id="data-collection-status">-</span></p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="table-container">
                        <h3>ML Scaling Policies</h3>
                        <table id="ml-policies-table">
                            <thead>
                                <tr>
                                    <th>Application</th>
                                    <th>Prediction Horizon</th>
                                    <th>Confidence Threshold</th>
                                    <th>Min/Max Replicas</th>
                                    <th>Status</th>
                                    <th>Last Prediction</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="ml-policies-tbody">
                                <tr><td colspan="7">Loading ML policies...</td></tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="table-container">
                        <h3>ML Training Data</h3>
                        <table id="ml-training-data-table">
                            <thead>
                                <tr>
                                    <th>Application</th>
                                    <th>Data Points</th>
                                    <th>Date Range</th>
                                    <th>Ready for Training</th>
                                    <th>Last Collection</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="ml-training-data-tbody">
                                <tr><td colspan="6">Loading training data...</td></tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="table-container">
                        <h3>Recent ML Predictions</h3>
                        <table id="ml-predictions-table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Application</th>
                                    <th>Predicted CPU</th>
                                    <th>Predicted Memory</th>
                                    <th>Recommended Replicas</th>
                                    <th>Confidence</th>
                                    <th>Action Taken</th>
                                </tr>
                            </thead>
                            <tbody id="ml-predictions-tbody">
                                <tr><td colspan="7">Loading ML predictions...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- Events Sub-tab -->
                <div id="events-subtab" class="sub-tab-content">
                    <div class="table-container">
                        <h3>Recent Scaling Events</h3>
                        <table id="events-table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Application</th>
                                    <th>Action</th>
                                    <th>From</th>
                                    <th>To</th>
                                    <th>Reason</th>
                                    <th>Type</th>
                                </tr>
                            </thead>
                            <tbody id="events-tbody">
                                <tr><td colspan="7">Loading events...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Metrics Tab -->
            <div id="metrics" class="tab-content">
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h4>Request Rate</h4>
                        <div class="metric-value" id="request-rate">0 req/s</div>
                    </div>
                    <div class="metric-card">
                        <h4>Response Time</h4>
                        <div class="metric-value" id="response-time">0 ms</div>
                    </div>
                    <div class="metric-card">
                        <h4>Error Rate</h4>
                        <div class="metric-value" id="error-rate">0%</div>
                    </div>
                    <div class="metric-card">
                        <h4>Throughput</h4>
                        <div class="metric-value" id="throughput">0 MB/s</div>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="metrics-chart" width="800" height="400"></canvas>
                </div>
            </div>

            <!-- Storage Tab -->
            <div id="storage" class="tab-content">
                <div class="storage-overview">
                    <div class="card">
                        <h3>Storage Summary</h3>
                        <p><strong>Total Capacity:</strong> <span id="total-storage">-</span></p>
                        <p><strong>Used:</strong> <span id="used-storage">-</span></p>
                        <p><strong>Available:</strong> <span id="available-storage">-</span></p>
                    </div>
                </div>
                <div class="table-container">
                    <table id="volumes-table">
                        <thead>
                            <tr>
                                <th>Volume Name</th>
                                <th>Size</th>
                                <th>Used</th>
                                <th>Storage Class</th>
                                <th>Status</th>
                                <th>Mount Path</th>
                            </tr>
                        </thead>
                        <tbody id="volumes-tbody">
                            <tr><td colspan="6">Loading volumes...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>

    <!-- Node Details Modal -->
    <div id="nodeModal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modalTitle">Node Details</h3>
                <span class="close" onclick="closeNodeModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="node-details-grid">
                    <div class="detail-section">
                        <h4>Basic Information</h4>
                        <p><strong>Node ID:</strong> <span id="nodeId">-</span></p>
                        <p><strong>Status:</strong> <span id="nodeStatus">-</span></p>
                        <p><strong>Role:</strong> <span id="nodeRole">-</span></p>
                        <p><strong>Uptime:</strong> <span id="nodeUptime">-</span></p>
                        <p><strong>Last Seen:</strong> <span id="nodeLastSeen">-</span></p>
                    </div>
                    
                    <div class="detail-section">
                        <h4>Resource Usage</h4>
                        <div class="progress-bar">
                            <label>CPU Usage</label>
                            <div class="progress">
                                <div class="progress-fill" id="modalCpuProgress"></div>
                            </div>
                            <span id="modalCpuPercent">0%</span>
                        </div>
                        <div class="progress-bar">
                            <label>Memory Usage</label>
                            <div class="progress">
                                <div class="progress-fill" id="modalMemoryProgress"></div>
                            </div>
                            <span id="modalMemoryPercent">0%</span>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>Network Information</h4>
                        <p><strong>Internal Port:</strong> 8000</p>
                        <p><strong>External Port:</strong> <span id="nodePort">-</span></p>
                        <p><strong>Health Endpoint:</strong> <span id="nodeHealthUrl">-</span></p>
                        <p><strong>Metrics Endpoint:</strong> <span id="nodeMetricsUrl">-</span></p>
                    </div>
                    
                    <div class="detail-section">
                        <h4>Cluster Information</h4>
                        <p><strong>Leader ID:</strong> <span id="nodeLeaderId">-</span></p>
                        <p><strong>Term:</strong> <span id="nodeTerm">-</span></p>
                        <p><strong>Heartbeats:</strong> <span id="nodeHeartbeats">-</span></p>
                        <p><strong>Elections:</strong> <span id="nodeElections">-</span></p>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeNodeModal()">Close</button>
                <button class="btn btn-primary" onclick="refreshNodeDetails()">Refresh</button>
            </div>
        </div>
    </div>

    <!-- Create Scaling Policy Modal -->
    <div id="createPolicyModal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Create Auto-Scaling Policy</h3>
                <span class="close" onclick="closeCreatePolicyModal()">&times;</span>
            </div>
            <div class="modal-body">
                <form id="policyForm">
                    <div class="form-group">
                        <label for="policyApp">Application *</label>
                        <select id="policyApp" name="application" required>
                            <option value="">Select Application</option>
                        </select>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="minReplicas">Min Replicas *</label>
                            <input type="number" id="minReplicas" name="minReplicas" required min="1" value="1">
                        </div>
                        <div class="form-group">
                            <label for="maxReplicas">Max Replicas *</label>
                            <input type="number" id="maxReplicas" name="maxReplicas" required min="1" value="5">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="cpuThreshold">CPU Threshold (%) *</label>
                            <input type="number" id="cpuThreshold" name="cpuThreshold" required min="1" max="100" value="70">
                        </div>
                        <div class="form-group">
                            <label for="memoryThreshold">Memory Threshold (%) *</label>
                            <input type="number" id="memoryThreshold" name="memoryThreshold" required min="1" max="100" value="80">
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h4>Advanced Options</h4>
                        <div class="form-group">
                            <label for="policyType">Policy Type</label>
                            <select id="policyType" name="policyType" onchange="toggleAdvancedOptions()">
                                <option value="basic">Basic Threshold</option>
                                <option value="multi-metric">Multi-Metric</option>
                            </select>
                        </div>
                        
                        <div id="advancedOptions" style="display: none;">
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="scaleUpCooldown">Scale Up Cooldown (seconds)</label>
                                    <input type="number" id="scaleUpCooldown" name="scaleUpCooldown" value="300">
                                </div>
                                <div class="form-group">
                                    <label for="scaleDownCooldown">Scale Down Cooldown (seconds)</label>
                                    <input type="number" id="scaleDownCooldown" name="scaleDownCooldown" value="600">
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="maxScalePerHour">Max Scaling Actions/Hour</label>
                                    <input type="number" id="maxScalePerHour" name="maxScalePerHour" value="10">
                                </div>
                                <div class="form-group">
                                    <label for="scaleIncrement">Scale Increment</label>
                                    <input type="number" id="scaleIncrement" name="scaleIncrement" value="1">
                                </div>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeCreatePolicyModal()">Cancel</button>
                <button class="btn btn-primary" onclick="submitCreatePolicy()">Create Policy</button>
            </div>
        </div>
    </div>

    <!-- Application Details Modal -->
    <div id="appDetailsModal" class="modal" style="display: none;">
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3 id="appModalTitle">Application Details</h3>
                <span class="close" onclick="closeAppDetailsModal()">&times;</span>
            </div>
            <div class="modal-body modal-scrollable">
                <div class="app-details-grid">
                    <div class="detail-section">
                        <h4>Basic Information</h4>
                        <p><strong>Name:</strong> <span id="appName">-</span></p>
                        <p><strong>Status:</strong> <span id="appStatus">-</span></p>
                        <p><strong>Replicas:</strong> <span id="appReplicas">-</span></p>
                        <p><strong>Version:</strong> <span id="appVersion">-</span></p>
                        <p><strong>Uptime:</strong> <span id="appUptime">-</span></p>
                        <p><strong>CPU Usage:</strong> <span id="appCpu">-</span></p>
                        <p><strong>Memory Usage:</strong> <span id="appMemory">-</span></p>
                        <p><strong>Auto-Scaling:</strong> <span id="appAutoScaling">-</span></p>
                    </div>
                    
                    <div class="detail-section">
                        <h4>Container Health</h4>
                        <div id="containerHealth">Loading...</div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>Auto-Scaling Policy</h4>
                        <div id="scalingPolicyInfo">Loading...</div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>Container Instances</h4>
                    <table class="details-table">
                        <thead>
                            <tr>
                                <th>Container Name</th>
                                <th>Status</th>
                                <th>Ports</th>
                                <th>Container ID</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody id="containersTable">
                            <tr><td colspan="5">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="detail-section">
                    <h4>Recent Scaling Events</h4>
                    <table class="details-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Action</th>
                                <th>Replicas</th>
                                <th>Reason</th>
                            </tr>
                        </thead>
                        <tbody id="recentEventsTable">
                            <tr><td colspan="4">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeAppDetailsModal()">Close</button>
            </div>
        </div>
    </div>

    <!-- Container Details Modal -->
    <div id="containerDetailsModal" class="modal" style="display: none;">
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3 id="containerModalTitle">Container Details</h3>
                <span class="close" onclick="closeContainerDetailsModal()">&times;</span>
            </div>
            <div class="modal-body modal-scrollable">
                <div class="app-details-grid">
                    <div class="detail-section">
                        <h4>Basic Information</h4>
                        <p><strong>Name:</strong> <span id="containerName">-</span></p>
                        <p><strong>ID:</strong> <span id="containerId">-</span></p>
                        <p><strong>Image:</strong> <span id="containerImage">-</span></p>
                        <p><strong>Created:</strong> <span id="containerCreated">-</span></p>
                        <p><strong>Status:</strong> <span id="containerStatus">-</span></p>
                        <p><strong>Exit Code:</strong> <span id="containerExitCode">-</span></p>
                        <p><strong>Error:</strong> <span id="containerError">-</span></p>
                    </div>
                    
                    <div class="detail-section">
                        <h4>Resource Usage</h4>
                        <div id="containerStats">Loading...</div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>Container Logs (Last 50 lines)</h4>
                    <pre id="containerLogs" style="background: #f8f9fa; padding: 15px; border-radius: 6px; max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px;">Loading...</pre>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeContainerDetailsModal()">Close</button>
            </div>
        </div>
    </div>

    <!-- Create Scheduled Policy Modal -->
    <div id="createScheduledPolicyModal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Create Scheduled Scaling Policy</h3>
                <span class="close" onclick="closeCreateScheduledPolicyModal()">&times;</span>
            </div>
            <div class="modal-body">
                <form id="scheduledPolicyForm">
                    <div class="form-group">
                        <label for="scheduledApp">Application *</label>
                        <select id="scheduledApp" name="application" required>
                            <option value="">Select Application</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="scheduleName">Schedule Name *</label>
                        <input type="text" id="scheduleName" name="scheduleName" required placeholder="business-hours">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="scheduleTime">Time *</label>
                            <input type="time" id="scheduleTime" name="scheduleTime" required>
                        </div>
                        <div class="form-group">
                            <label for="targetReplicas">Target Replicas *</label>
                            <input type="number" id="targetReplicas" name="targetReplicas" required min="1" value="2">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Days of Week *</label>
                        <div class="checkbox-group">
                            <label><input type="checkbox" name="days" value="1"> Monday</label>
                            <label><input type="checkbox" name="days" value="2"> Tuesday</label>
                            <label><input type="checkbox" name="days" value="3"> Wednesday</label>
                            <label><input type="checkbox" name="days" value="4"> Thursday</label>
                            <label><input type="checkbox" name="days" value="5"> Friday</label>
                            <label><input type="checkbox" name="days" value="6"> Saturday</label>
                            <label><input type="checkbox" name="days" value="0"> Sunday</label>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeCreateScheduledPolicyModal()">Cancel</button>
                <button class="btn btn-primary" onclick="submitCreateScheduledPolicy()">Create Schedule</button>
            </div>
        </div>
    </div>

    <!-- Analytics Modal -->
    <div id="analyticsModal" class="modal" style="display: none;">
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3>Auto-Scaling Analytics</h3>
                <span class="close" onclick="closeAnalyticsModal()">&times;</span>
            </div>
            <div class="modal-body modal-scrollable">
                <div class="analytics-grid">
                    <div class="analytics-card">
                        <h4>Scaling Efficiency</h4>
                        <div class="metric-large" id="efficiencyScore">-</div>
                        <p>Overall efficiency score</p>
                    </div>
                    <div class="analytics-card">
                        <h4>Total Events (24h)</h4>
                        <div class="metric-large" id="totalEvents24h">-</div>
                        <p>Scale up/down actions</p>
                    </div>
                    <div class="analytics-card">
                        <h4>Avg Response Time</h4>
                        <div class="metric-large" id="avgResponseTime">-</div>
                        <p>Time to scale action</p>
                    </div>
                    <div class="analytics-card clickable" onclick="showCostSavingsModal()">
                        <h4>Cost Savings</h4>
                        <div class="metric-large" id="costSavings">-</div>
                        <p>Estimated savings (click for details)</p>
                    </div>
                </div>
                
                <div class="table-container">
                    <h4>Application Analytics</h4>
                    <table id="app-analytics-table">
                        <thead>
                            <tr>
                                <th>Application</th>
                                <th>Total Events</th>
                                <th>Scale Up</th>
                                <th>Scale Down</th>
                                <th>Avg Decision Score</th>
                                <th>Efficiency</th>
                            </tr>
                        </thead>
                        <tbody id="app-analytics-tbody">
                            <tr><td colspan="6">Loading analytics...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeAnalyticsModal()">Close</button>
                <button class="btn btn-primary" onclick="refreshAnalytics()">Refresh</button>
            </div>
        </div>
    </div>

    <!-- Cost Savings Breakdown Modal -->
    <div id="costSavingsModal" class="modal" style="display: none;">
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3>Cost Savings Analysis</h3>
                <span class="close" onclick="closeCostSavingsModal()">&times;</span>
            </div>
            <div class="modal-body modal-scrollable">
                <div class="cost-breakdown">
                    <h4>How Cost Savings Are Calculated</h4>
                    <div class="calculation-section">
                        <h5>Resource Optimization Savings</h5>
                        <div class="calculation-item">
                            <span class="calc-label">Scale-down events (24h):</span>
                            <span class="calc-value" id="scaleDownCount">-</span>
                            <span class="calc-desc">× $0.05/hour per container = <strong id="scaleDownSavings">$0.00</strong></span>
                        </div>
                        <div class="calculation-item">
                            <span class="calc-label">Prevented over-provisioning:</span>
                            <span class="calc-value" id="overProvisionHours">-</span>
                            <span class="calc-desc">hours × $0.02/hour = <strong id="overProvisionSavings">$0.00</strong></span>
                        </div>
                    </div>
                    
                    <div class="calculation-section">
                        <h5>Operational Efficiency Savings</h5>
                        <div class="calculation-item">
                            <span class="calc-label">Manual scaling prevention:</span>
                            <span class="calc-value" id="manualPreventionCount">-</span>
                            <span class="calc-desc">actions × $2.00/action = <strong id="manualPreventionSavings">$0.00</strong></span>
                        </div>
                        <div class="calculation-item">
                            <span class="calc-label">Faster response time:</span>
                            <span class="calc-value" id="responseTimeSavings">-</span>
                            <span class="calc-desc">minutes saved × $0.10/min = <strong id="responseTimeCost">$0.00</strong></span>
                        </div>
                    </div>
                    
                    <div class="calculation-section">
                        <h5>Total Savings Breakdown (24h)</h5>
                        <table class="savings-table">
                            <tr>
                                <td>Resource optimization</td>
                                <td id="totalResourceSavings">$0.00</td>
                            </tr>
                            <tr>
                                <td>Operational efficiency</td>
                                <td id="totalOperationalSavings">$0.00</td>
                            </tr>
                            <tr class="total-row">
                                <td><strong>Total Daily Savings</strong></td>
                                <td><strong id="totalDailySavings">$0.00</strong></td>
                            </tr>
                            <tr class="projection-row">
                                <td>Monthly projection</td>
                                <td id="monthlySavings">$0.00</td>
                            </tr>
                            <tr class="projection-row">
                                <td>Annual projection</td>
                                <td id="annualSavings">$0.00</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="calculation-section">
                        <h5>Cost Calculation Methodology</h5>
                        <ul class="methodology-list">
                            <li><strong>Container costs:</strong> Based on average cloud provider pricing ($0.05/hour per container)</li>
                            <li><strong>Manual intervention:</strong> Estimated DevOps time cost ($2.00 per manual scaling action)</li>
                            <li><strong>Response time:</strong> Business impact of faster scaling response ($0.10 per minute saved)</li>
                            <li><strong>Over-provisioning:</strong> Cost of running unnecessary containers during low demand</li>
                            <li><strong>Projections:</strong> Linear extrapolation based on current 24-hour trends</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeCostSavingsModal()">Close</button>
                <button class="btn btn-primary" onclick="exportCostAnalysis()">Export Analysis</button>
            </div>
        </div>
    </div>

    <!-- Deploy Application Modal -->
    <div id="deployModal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Deploy Application</h3>
                <span class="close" onclick="closeDeployModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="resource-info">
                    <h4>Cluster Resources</h4>
                    <div class="resource-grid">
                        <div class="resource-item">
                            <label>Used Ports:</label>
                            <div id="usedPorts" class="resource-value">Loading...</div>
                        </div>
                        <div class="resource-item">
                            <label>Memory Usage:</label>
                            <div id="memoryInfo" class="resource-value">Loading...</div>
                        </div>
                    </div>
                </div>
                <form id="deployForm">
                    <div class="form-group">
                        <label for="appName">Application Name *</label>
                        <input type="text" id="appName" name="appName" required placeholder="my-app">
                    </div>
                    <div class="form-group">
                        <label for="appImage">Docker Image *</label>
                        <input type="text" id="appImage" name="appImage" required placeholder="nginx:latest">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="replicas">Replicas *</label>
                            <input type="number" id="replicas" name="replicas" required min="1" value="1">
                        </div>
                        <div class="form-group">
                            <label for="port">Port *</label>
                            <input type="number" id="port" name="port" required min="1" max="65535" value="8080">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="cpu">CPU Limit</label>
                            <input type="text" id="cpu" name="cpu" placeholder="100m" value="100m">
                        </div>
                        <div class="form-group">
                            <label for="memory">Memory Limit</label>
                            <input type="text" id="memory" name="memory" placeholder="128Mi" value="128Mi">
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeDeployModal()">Cancel</button>
                <button class="btn btn-primary" onclick="submitDeploy()">Deploy</button>
            </div>
        </div>
    </div>

    <script>
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeDashboard();
            setInterval(refreshData, 5000); // Refresh every 5 seconds
            
            // Initialize ML data on startup
            setTimeout(function() {
                fetch('/api/cluster.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'action=init_ml_data'
                }).catch(e => console.log('ML init skipped:', e.message));
            }, 2000);
        });
    </script>
</body>
</html>