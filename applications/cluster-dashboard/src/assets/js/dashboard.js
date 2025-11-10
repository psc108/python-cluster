// Dashboard JavaScript
let currentTab = 'overview';
let refreshInterval;

// Initialize dashboard
function initializeDashboard() {
    console.log('Initializing Cluster Dashboard...');
    refreshData();
    startAutoRefresh();
}

// Tab management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    currentTab = tabName;
    
    // Refresh data for the new tab
    refreshData();
}

// Auto refresh
function startAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    refreshInterval = setInterval(refreshData, 5000);
}

// Main data refresh function
async function refreshData() {
    try {
        switch (currentTab) {
            case 'overview':
                await refreshOverview();
                break;
            case 'nodes':
                await refreshNodes();
                break;
            case 'applications':
                await refreshApplications();
                break;
            case 'metrics':
                await refreshMetrics();
                break;
            case 'storage':
                await refreshStorage();
                break;
        }
        updateClusterStatus();
    } catch (error) {
        console.error('Error refreshing data:', error);
        showError('Failed to refresh dashboard data');
    }
}

// Update cluster status indicator
async function updateClusterStatus() {
    try {
        const response = await fetch('/api/cluster.php?action=status');
        const data = await response.json();
        
        const statusElement = document.getElementById('cluster-status');
        const statusDot = statusElement.querySelector('.status-dot');
        const statusText = statusElement.querySelector('.status-text');
        
        // Remove existing status classes
        statusDot.classList.remove('healthy', 'unhealthy', 'degraded');
        
        // Add appropriate status class
        statusDot.classList.add(data.cluster_status);
        
        // Update status text
        const statusMessages = {
            'healthy': 'Cluster Healthy',
            'degraded': 'Cluster Degraded',
            'unhealthy': 'Cluster Unhealthy'
        };
        
        statusText.textContent = statusMessages[data.cluster_status] || 'Unknown Status';
        
    } catch (error) {
        console.error('Error updating cluster status:', error);
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        statusDot.classList.add('unhealthy');
        statusText.textContent = 'Connection Error';
    }
}

// Refresh overview tab
async function refreshOverview() {
    try {
        const [statusResponse, metricsResponse] = await Promise.all([
            fetch('/api/cluster.php?action=status'),
            fetch('/api/cluster.php?action=metrics')
        ]);
        
        const statusData = await statusResponse.json();
        const metricsData = await metricsResponse.json();
        
        // Update cluster info
        document.getElementById('leader-node').textContent = statusData.leader_id || 'None';
        document.getElementById('total-nodes').textContent = statusData.total_nodes;
        document.getElementById('healthy-nodes').textContent = statusData.healthy_nodes;
        document.getElementById('cluster-uptime').textContent = formatUptime(statusData.uptime);
        
        // Update resource usage
        updateProgressBar('cpu-progress', 'cpu-percent', metricsData.avg_cpu_percent);
        updateProgressBar('memory-progress', 'memory-percent', metricsData.avg_memory_percent);
        
        // Get real application summary
        try {
            const appsResponse = await fetch('/api/cluster.php?action=applications');
            const apps = await appsResponse.json();
            
            const runningApps = apps.filter(app => app.status === 'running').length;
            const totalInstances = apps.reduce((sum, app) => {
                const replicas = app.replicas.split('/')[1] || '0';
                return sum + parseInt(replicas);
            }, 0);
            const failedApps = apps.filter(app => app.status !== 'running').length;
            
            document.getElementById('running-apps').textContent = runningApps;
            document.getElementById('total-instances').textContent = totalInstances;
            document.getElementById('failed-apps').textContent = failedApps;
        } catch (error) {
            // Show zeros when no data available
            document.getElementById('running-apps').textContent = '0';
            document.getElementById('total-instances').textContent = '0';
            document.getElementById('failed-apps').textContent = '0';
        }
        
    } catch (error) {
        console.error('Error refreshing overview:', error);
    }
}

// Refresh nodes tab
async function refreshNodes() {
    try {
        const response = await fetch('/api/cluster.php?action=nodes');
        const nodes = await response.json();
        
        const tbody = document.getElementById('nodes-tbody');
        tbody.innerHTML = '';
        
        nodes.forEach(node => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>Node ${node.id}</td>
                <td><span class="status-badge status-${node.status}">${node.status}</span></td>
                <td><span class="status-badge ${node.role === 'leader' ? 'status-running' : 'status-healthy'}">${node.role}</span></td>
                <td>${node.cpu_percent.toFixed(1)}%</td>
                <td>${node.memory_percent.toFixed(1)}%</td>
                <td>${node.uptime}</td>
                <td>
                    <button class="btn btn-small btn-secondary" onclick="viewNodeDetails(${node.id})">Details</button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error refreshing nodes:', error);
        document.getElementById('nodes-tbody').innerHTML = '<tr><td colspan="7">Error loading nodes</td></tr>';
    }
}

// Refresh applications tab
async function refreshApplications() {
    try {
        const response = await fetch('/api/cluster.php?action=applications');
        const apps = await response.json();
        
        const tbody = document.getElementById('apps-tbody');
        tbody.innerHTML = '';
        
        apps.forEach(app => {
            const row = document.createElement('tr');
            
            // Determine which buttons to show based on status
            let actionButtons = '';
            if (app.status === 'running') {
                actionButtons = `
                    <button class="btn btn-small btn-secondary" onclick="scaleApplication('${app.name}')">Scale</button>
                    <button class="btn btn-small btn-warning" onclick="pauseApplication('${app.name}')">Pause</button>
                    <button class="btn btn-small btn-danger" onclick="stopApplication('${app.name}')">Stop</button>
                `;
            } else if (app.status === 'paused') {
                actionButtons = `
                    <button class="btn btn-small btn-success" onclick="resumeApplication('${app.name}')">Resume</button>
                    <button class="btn btn-small btn-danger" onclick="stopApplication('${app.name}')">Stop</button>
                `;
            } else {
                actionButtons = `
                    <button class="btn btn-small btn-danger" onclick="stopApplication('${app.name}')">Stop</button>
                `;
            }
            
            row.innerHTML = `
                <td>${app.name}</td>
                <td><span class="status-badge status-${app.status}">${app.status}</span></td>
                <td>${app.replicas}</td>
                <td>${app.version}</td>
                <td>${app.cpu_percent}%</td>
                <td>${app.memory_mb} MB</td>
                <td>${actionButtons}</td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error refreshing applications:', error);
        document.getElementById('apps-tbody').innerHTML = '<tr><td colspan="7">Error loading applications</td></tr>';
    }
}

// Refresh metrics tab
async function refreshMetrics() {
    try {
        const response = await fetch('/api/cluster.php?action=metrics');
        const metrics = await response.json();
        
        // Update metric cards
        document.getElementById('request-rate').textContent = `${metrics.request_rate} req/s`;
        document.getElementById('response-time').textContent = `${metrics.response_time_ms} ms`;
        document.getElementById('error-rate').textContent = `${metrics.error_rate}%`;
        document.getElementById('throughput').textContent = `${metrics.throughput_mbps} MB/s`;
        
        // Update chart
        updateMetricsChart(metrics);
        
    } catch (error) {
        console.error('Error refreshing metrics:', error);
    }
}

// Refresh storage tab
async function refreshStorage() {
    try {
        const response = await fetch('/api/cluster.php?action=storage');
        const storage = await response.json();
        
        // Update storage summary
        document.getElementById('total-storage').textContent = `${storage.total_capacity_gb} GB`;
        document.getElementById('used-storage').textContent = `${storage.used_gb} GB`;
        document.getElementById('available-storage').textContent = `${storage.available_gb} GB`;
        
        // Update volumes table
        const tbody = document.getElementById('volumes-tbody');
        tbody.innerHTML = '';
        
        storage.volumes.forEach(volume => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${volume.name}</td>
                <td>${volume.size}</td>
                <td>${volume.used}</td>
                <td>${volume.storage_class}</td>
                <td><span class="status-badge status-healthy">${volume.status}</span></td>
                <td>${volume.mount_path}</td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error refreshing storage:', error);
        document.getElementById('volumes-tbody').innerHTML = '<tr><td colspan="6">Error loading storage info</td></tr>';
    }
}

// Utility functions
function updateProgressBar(progressId, percentId, value) {
    const progressBar = document.getElementById(progressId);
    const percentSpan = document.getElementById(percentId);
    
    if (progressBar && percentSpan) {
        progressBar.style.width = `${value}%`;
        percentSpan.textContent = `${value.toFixed(1)}%`;
        
        // Update color based on value
        progressBar.classList.remove('warning', 'danger');
        if (value > 80) {
            progressBar.classList.add('danger');
        } else if (value > 60) {
            progressBar.classList.add('warning');
        }
    }
}

function formatUptime(seconds) {
    if (!seconds) return '0m';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

function updateMetricsChart(metrics) {
    // Simplified chart update - in real implementation, use a charting library
    const canvas = document.getElementById('metrics-chart');
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw simple bar chart
    const barWidth = 80;
    const barSpacing = 100;
    const maxHeight = 300;
    
    const data = [
        { label: 'CPU %', value: metrics.avg_cpu_percent, max: 100 },
        { label: 'Memory %', value: metrics.avg_memory_percent, max: 100 },
        { label: 'Requests/s', value: metrics.request_rate, max: 10 },
        { label: 'Response ms', value: metrics.response_time_ms, max: 100 }
    ];
    
    data.forEach((item, index) => {
        const x = 50 + index * (barWidth + barSpacing);
        const height = (item.value / item.max) * maxHeight;
        const y = canvas.height - height - 50;
        
        // Draw bar
        ctx.fillStyle = '#3498db';
        ctx.fillRect(x, y, barWidth, height);
        
        // Draw label
        ctx.fillStyle = '#2c3e50';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(item.label, x + barWidth/2, canvas.height - 30);
        ctx.fillText(item.value.toFixed(1), x + barWidth/2, y - 10);
    });
}

function showError(message) {
    console.error(message);
    
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.textContent = message;
    toast.style.cssText = 'position:fixed;top:20px;right:20px;background:#e74c3c;color:white;padding:12px 20px;border-radius:4px;z-index:1000;';
    
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

// Application management functions
async function scaleApplication(appName) {
    const replicas = prompt(`Enter new replica count for ${appName}:`, '1');
    if (replicas && !isNaN(replicas)) {
        try {
            const response = await fetch('/api/cluster.php?action=scale', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    application: appName,
                    replicas: parseInt(replicas)
                })
            });
            
            const result = await response.json();
            if (result.success) {
                alert(`Successfully scaled ${appName} to ${replicas} replicas`);
                refreshApplications();
            } else {
                alert(`Failed to scale ${appName}: ${result.error}`);
            }
        } catch (error) {
            console.error('Error scaling application:', error);
            alert(`Error scaling ${appName}: ${error.message}`);
        }
    }
}

async function stopApplication(appName) {
    if (confirm(`Are you sure you want to stop ${appName}?`)) {
        try {
            const response = await fetch('/api/cluster.php?action=stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    application: appName
                })
            });
            
            const result = await response.json();
            if (result.success) {
                alert(`Successfully stopped ${appName}`);
                refreshApplications();
            } else {
                alert(`Failed to stop ${appName}: ${result.error}`);
            }
        } catch (error) {
            console.error('Error stopping application:', error);
            alert(`Error stopping ${appName}: ${error.message}`);
        }
    }
}

async function viewNodeDetails(nodeId) {
    try {
        // Fetch detailed node information
        const [nodesResponse, metricsResponse] = await Promise.all([
            fetch('/api/cluster.php?action=nodes'),
            fetch('/api/cluster.php?action=metrics')
        ]);
        
        const nodes = await nodesResponse.json();
        const metrics = await metricsResponse.json();
        
        // Find the specific node
        const node = nodes.find(n => n.id === nodeId);
        if (!node) {
            alert('Node not found');
            return;
        }
        
        // Populate modal with node details
        document.getElementById('modalTitle').textContent = `Node ${nodeId} Details`;
        document.getElementById('nodeId').textContent = nodeId;
        document.getElementById('nodeStatus').innerHTML = `<span class="status-badge status-${node.status}">${node.status}</span>`;
        document.getElementById('nodeRole').innerHTML = `<span class="status-badge ${node.role === 'leader' ? 'status-running' : 'status-healthy'}">${node.role}</span>`;
        document.getElementById('nodeUptime').textContent = node.uptime;
        document.getElementById('nodeLastSeen').textContent = node.last_seen;
        
        // Resource usage
        updateProgressBar('modalCpuProgress', 'modalCpuPercent', node.cpu_percent);
        updateProgressBar('modalMemoryProgress', 'modalMemoryPercent', node.memory_percent);
        
        // Network information
        const externalPort = 8000 + nodeId;
        document.getElementById('nodePort').textContent = externalPort;
        document.getElementById('nodeHealthUrl').textContent = `http://localhost:${externalPort}/health`;
        document.getElementById('nodeMetricsUrl').textContent = `http://localhost:${externalPort}/metrics`;
        
        // Get cluster information through our API
        try {
            const nodeDetailsResponse = await fetch(`/api/cluster.php?action=node_details&node_id=${nodeId}`);
            const nodeDetails = await nodeDetailsResponse.json();
            
            document.getElementById('nodeLeaderId').textContent = nodeDetails.leader_id || 'Unknown';
            document.getElementById('nodeTerm').textContent = nodeDetails.current_term || '0';
            document.getElementById('nodeHeartbeats').textContent = nodeDetails.heartbeats || 'N/A';
            document.getElementById('nodeElections').textContent = nodeDetails.elections || 'N/A';
            
        } catch (error) {
            // Show unavailable when data cannot be retrieved
            document.getElementById('nodeLeaderId').textContent = 'Unavailable';
            document.getElementById('nodeTerm').textContent = 'Unavailable';
            document.getElementById('nodeHeartbeats').textContent = 'Unavailable';
            document.getElementById('nodeElections').textContent = 'Unavailable';
        }
        
        // Show modal
        document.getElementById('nodeModal').style.display = 'flex';
        
    } catch (error) {
        console.error('Error fetching node details:', error);
        alert('Failed to load node details');
    }
}

function closeNodeModal() {
    document.getElementById('nodeModal').style.display = 'none';
}

function refreshNodeDetails() {
    const nodeId = parseInt(document.getElementById('nodeId').textContent);
    viewNodeDetails(nodeId);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const nodeModal = document.getElementById('nodeModal');
    const deployModal = document.getElementById('deployModal');
    
    if (event.target === nodeModal) {
        closeNodeModal();
    }
    
    if (event.target === deployModal) {
        closeDeployModal();
    }
}

async function showDeployForm() {
    // Reset form
    document.getElementById('deployForm').reset();
    document.getElementById('replicas').value = '1';
    document.getElementById('port').value = '8080';
    document.getElementById('cpu').value = '100m';
    document.getElementById('memory').value = '128Mi';
    
    // Load resource information
    await loadResourceInfo();
    
    // Show modal
    document.getElementById('deployModal').style.display = 'flex';
}

async function loadResourceInfo() {
    try {
        const response = await fetch('/api/cluster.php?action=resource_info');
        const data = await response.json();
        
        // Display used ports (remove duplicates)
        const usedPortsElement = document.getElementById('usedPorts');
        if (data.used_ports && data.used_ports.length > 0) {
            const uniquePorts = [...new Set(data.used_ports)].sort((a, b) => a - b);
            usedPortsElement.textContent = uniquePorts.join(', ');
        } else {
            usedPortsElement.textContent = 'None';
        }
        
        // Display memory information
        const memoryInfoElement = document.getElementById('memoryInfo');
        const memory = data.memory;
        memoryInfoElement.innerHTML = `
            Total: ${memory.total_mb} MB<br>
            Used: ${memory.used_mb} MB (${memory.usage_percent}%)<br>
            Available: ${memory.available_mb} MB
        `;
        
    } catch (error) {
        console.error('Error loading resource info:', error);
        document.getElementById('usedPorts').textContent = 'Error loading';
        document.getElementById('memoryInfo').textContent = 'Error loading';
    }
}

function closeDeployModal() {
    document.getElementById('deployModal').style.display = 'none';
}

function submitDeploy() {
    const form = document.getElementById('deployForm');
    const formData = new FormData(form);
    
    const appName = formData.get('appName').trim();
    const appImage = formData.get('appImage').trim();
    const replicas = parseInt(formData.get('replicas'));
    const port = parseInt(formData.get('port'));
    const cpu = formData.get('cpu').trim() || '100m';
    const memory = formData.get('memory').trim() || '128Mi';
    
    // Validate required fields
    if (!appName || !appImage || !replicas || !port) {
        alert('Please fill in all required fields');
        return;
    }
    
    // Validate numeric fields
    if (isNaN(replicas) || replicas < 1) {
        alert('Replicas must be a positive number');
        return;
    }
    
    if (isNaN(port) || port < 1 || port > 65535) {
        alert('Port must be between 1 and 65535');
        return;
    }
    
    // Close modal and deploy
    closeDeployModal();
    deployApplication(appName, appImage, replicas, port, cpu, memory);
}

async function deployApplication(appName, image, replicas, port, cpu, memory) {
    try {
        const response = await fetch('/api/cluster.php?action=deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: appName,
                image: image,
                replicas: replicas,
                ports: [{ name: 'http', port: port }],
                resources: { cpu: cpu, memory: memory }
            })
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`Successfully deployed ${appName}`);
            refreshApplications();
        } else {
            alert(`Failed to deploy ${appName}: ${result.error}`);
        }
    } catch (error) {
        console.error('Error deploying application:', error);
        alert(`Error deploying ${appName}: ${error.message}`);
    }
}

async function pauseApplication(appName) {
    if (confirm(`Are you sure you want to pause ${appName}?`)) {
        try {
            const response = await fetch('/api/cluster.php?action=pause', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    application: appName
                })
            });
            
            const result = await response.json();
            if (result.success) {
                alert(`Successfully paused ${appName}`);
                refreshApplications();
            } else {
                alert(`Failed to pause ${appName}: ${result.error}`);
            }
        } catch (error) {
            console.error('Error pausing application:', error);
            alert(`Error pausing ${appName}: ${error.message}`);
        }
    }
}

async function resumeApplication(appName) {
    try {
        const response = await fetch('/api/cluster.php?action=resume', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                application: appName
            })
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`Successfully resumed ${appName}`);
            refreshApplications();
        } else {
            alert(`Failed to resume ${appName}: ${result.error}`);
        }
    } catch (error) {
        console.error('Error resuming application:', error);
        alert(`Error resuming ${appName}: ${error.message}`);
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

// Helper function to extract metrics from Prometheus text
function extractMetricFromText(metricsText, metricName) {
    const regex = new RegExp(`${metricName}(?:\\{[^}]*\\})?\\s+(\\d+(?:\\.\\d+)?)`, 'm');
    const match = metricsText.match(regex);
    return match ? parseFloat(match[1]) : 0;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Close modals with Escape key
    if (event.key === 'Escape') {
        closeNodeModal();
        closeDeployModal();
    }
});