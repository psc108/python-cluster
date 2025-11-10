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
                                <th>Status</th>
                                <th>Replicas</th>
                                <th>Version</th>
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
        });
    </script>
</body>
</html>