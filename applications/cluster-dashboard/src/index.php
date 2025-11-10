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

    <script>
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeDashboard();
            setInterval(refreshData, 5000); // Refresh every 5 seconds
        });
    </script>
</body>
</html>