// Dashboard JavaScript
let currentTab = 'overview';
let refreshInterval;
let cachedApplications = [];

// Initialize dashboard
function initializeDashboard() {
    console.log('Initializing Cluster Dashboard...');
    refreshData();
    startAutoRefresh();
    
    // Initialize ML system status immediately and repeatedly
    refreshMLSystemStatus();
    setTimeout(function() {
        refreshMLSystemStatus();
    }, 1000);
    setTimeout(function() {
        refreshMLSystemStatus();
    }, 3000);
}

// Tab management
function showTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    const tabElement = document.getElementById(tabName);
    if (tabElement) {
        tabElement.classList.add('active');
    } else {
        console.error('Tab element not found:', tabName);
    }
    
    // Add active class to clicked button
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    currentTab = tabName;
    
    // Refresh data for the new tab
    refreshData();
    
    // Also refresh ML status when switching to autoscaling tab
    if (tabName === 'autoscaling') {
        setTimeout(function() {
            refreshMLSystemStatus();
        }, 500);
    }
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
            case 'autoscaling':
                await refreshAutoScaling();
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
        
        // Cache applications for policy dropdown
        cachedApplications = apps;
        
        const tbody = document.getElementById('apps-tbody');
        tbody.innerHTML = '';
        
        apps.forEach(app => {
            const row = document.createElement('tr');
            
            // Determine which buttons to show based on status
            let actionButtons = '';
            if (app.status === 'running') {
                const autoScaleBtn = app.autoScaling ? 
                    `<button class="btn btn-small btn-info" onclick="manageAutoScaling('${app.name}')">Auto-Scale</button>` :
                    `<button class="btn btn-small btn-secondary" onclick="enableAutoScaling('${app.name}')">Enable Auto</button>`;
                
                actionButtons = `
                    <button class="btn btn-small btn-primary" onclick="viewApplicationDetails('${app.name}')">Details</button>
                    <button class="btn btn-small btn-secondary" onclick="scaleApplication('${app.name}')">Scale</button>
                    ${autoScaleBtn}
                    <button class="btn btn-small btn-warning" onclick="pauseApplication('${app.name}')">Pause</button>
                    <button class="btn btn-small btn-danger" onclick="stopApplication('${app.name}')">Stop</button>
                `;
            } else if (app.status === 'paused') {
                actionButtons = `
                    <button class="btn btn-small btn-primary" onclick="viewApplicationDetails('${app.name}')">Details</button>
                    <button class="btn btn-small btn-success" onclick="resumeApplication('${app.name}')">Resume</button>
                    <button class="btn btn-small btn-danger" onclick="stopApplication('${app.name}')">Stop</button>
                `;
            } else {
                actionButtons = `
                    <button class="btn btn-small btn-primary" onclick="viewApplicationDetails('${app.name}')">Details</button>
                    <button class="btn btn-small btn-danger" onclick="stopApplication('${app.name}')">Stop</button>
                `;
            }
            
            // Auto-scaling status badge
            const scalingStatus = app.autoScaling ? 
                '<span class="scaling-badge scaling-enabled">Auto</span>' : 
                '<span class="scaling-badge scaling-disabled">Manual</span>';
            
            row.innerHTML = `
                <td>${app.name}</td>
                <td>${scalingStatus}</td>
                <td><span class="status-badge status-${app.status}">${app.status}</span></td>
                <td>${app.replicas}</td>
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

// Auto-scaling functions
async function enableAutoScaling(appName) {
    const minReplicas = prompt(`Min replicas for ${appName}:`);
    if (!minReplicas || isNaN(minReplicas)) return;
    
    const maxReplicas = prompt(`Max replicas for ${appName}:`);
    if (!maxReplicas || isNaN(maxReplicas)) return;
    
    const cpuThreshold = prompt(`CPU threshold % for ${appName}:`);
    if (!cpuThreshold || isNaN(cpuThreshold)) return;
    
    const memoryThreshold = prompt(`Memory threshold % for ${appName}:`);
    if (!memoryThreshold || isNaN(memoryThreshold)) return;
    
    try {
        const response = await fetch('/api/cluster.php?action=create_scaling_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                application: appName,
                minReplicas: parseInt(minReplicas),
                maxReplicas: parseInt(maxReplicas),
                cpuThreshold: parseInt(cpuThreshold),
                memoryThreshold: parseInt(memoryThreshold)
            })
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`Auto-scaling enabled for ${appName}`);
            refreshApplications();
        } else {
            alert(`Failed to enable auto-scaling: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function manageAutoScaling(appName) {
    try {
        const response = await fetch('/api/cluster.php?action=get_scaling_policies');
        const policies = await response.json();
        const policy = policies[appName];
        
        if (!policy) {
            alert('No auto-scaling policy found');
            return;
        }
        
        const action = confirm(`Auto-scaling policy for ${appName}:\n` +
            `Min: ${policy.minReplicas}, Max: ${policy.maxReplicas}\n` +
            `CPU: ${policy.cpuThreshold}%, Memory: ${policy.memoryThreshold}%\n\n` +
            `Click OK to disable, Cancel to keep enabled`);
        
        if (action) {
            // Disable auto-scaling (simplified - just delete policy)
            policy.enabled = false;
            alert(`Auto-scaling disabled for ${appName}`);
            refreshApplications();
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Auto-scaling evaluation (runs periodically)
setInterval(async () => {
    try {
        await fetch('/api/cluster.php?action=evaluate_scaling');
    } catch (error) {
        console.log('Auto-scaling evaluation skipped:', error.message);
    }
}, 60000); // Every minute

// Auto-scaling tab functions
async function refreshAutoScaling() {
    try {
        await refreshScalingPolicies();
        await refreshScheduledPolicies();
        await refreshScalingEvents();
        await refreshScalingSummary();
    } catch (error) {
        console.error('Error in refreshAutoScaling:', error);
    }
}

async function refreshScalingPolicies() {
    const tbody = document.getElementById('policies-tbody');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/cluster.php?action=get_scaling_policies');
        const policies = await response.json();
        
        tbody.innerHTML = '';
        
        if (!policies || Object.keys(policies).length === 0) {
            tbody.innerHTML = '<tr><td colspan="7">No scaling policies configured</td></tr>';
            return;
        }
        
        Object.values(policies).forEach(policy => {
            const row = document.createElement('tr');
            const statusBadge = policy.enabled ? 
                '<span class="status-badge status-running">Enabled</span>' :
                '<span class="status-badge status-stopped">Disabled</span>';
            
            row.innerHTML = `
                <td>${policy.application}</td>
                <td>${policy.minReplicas}</td>
                <td>${policy.maxReplicas}</td>
                <td>${policy.cpuThreshold}%</td>
                <td>${policy.memoryThreshold}%</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-small btn-secondary" onclick="editPolicy('${policy.application}')">Edit</button>
                    <button class="btn btn-small btn-danger" onclick="deletePolicy('${policy.application}')">Delete</button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7">Error loading policies</td></tr>';
    }
}

async function refreshScalingEvents() {
    const tbody = document.getElementById('events-tbody');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/cluster.php?action=scaling_events');
        const events = await response.json();
        
        tbody.innerHTML = '';
        
        if (!events || events.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No scaling events</td></tr>';
            return;
        }
        
        events.slice(-10).reverse().forEach(event => {
            const row = document.createElement('tr');
            const timestamp = event.formatted_time || new Date(event.timestamp * 1000).toLocaleString();
            const actionBadge = event.action === 'scale_up' ? 
                '<span class="status-badge status-running">Scale Up</span>' :
                event.action === 'scale_down' ? 
                '<span class="status-badge status-warning">Scale Down</span>' :
                '<span class="status-badge status-info">Scale</span>';
            
            row.innerHTML = `
                <td>${timestamp}</td>
                <td>${event.application}</td>
                <td>${actionBadge}</td>
                <td>${event.from_replicas || '-'}</td>
                <td>${event.to_replicas || event.replicas || '-'}</td>
                <td>${event.reason || 'Manual scaling'}</td>
                <td>${event.type || 'Manual'}</td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6">Error loading events</td></tr>';
    }
}

async function refreshScalingSummary() {
    try {
        const [policiesResponse, appsResponse] = await Promise.all([
            fetch('/api/cluster.php?action=get_scaling_policies'),
            fetch('/api/cluster.php?action=applications')
        ]);
        
        const policies = await policiesResponse.json();
        const apps = await appsResponse.json();
        
        const activePolicies = Object.values(policies || {}).filter(p => p.enabled).length;
        const autoscaledApps = (apps || []).filter(app => app.autoScaling).length;
        
        document.getElementById('active-policies').textContent = activePolicies;
        document.getElementById('autoscaled-apps').textContent = autoscaledApps;
        document.getElementById('recent-actions').textContent = '0';
        
    } catch (error) {
        document.getElementById('active-policies').textContent = '0';
        document.getElementById('autoscaled-apps').textContent = '0';
        document.getElementById('recent-actions').textContent = '0';
    }
}

function showCreatePolicyModal() {
    loadApplicationsForPolicy();
    document.getElementById('createPolicyModal').style.display = 'flex';
}

// Direct refresh function for the button
function refreshPolicies() {
    refreshAutoScaling();
}

function closeCreatePolicyModal() {
    document.getElementById('createPolicyModal').style.display = 'none';
}

async function loadApplicationsForPolicy() {
    const select = document.getElementById('policyApp');
    select.innerHTML = '<option value="">Select Application</option>';
    
    // Use cached applications if available
    if (cachedApplications.length > 0) {
        populateApplicationSelect(cachedApplications, 'policyApp');
        return;
    }
    
    // Otherwise fetch fresh data
    try {
        const response = await fetch('/api/cluster.php?action=applications');
        const apps = await response.json();
        cachedApplications = apps;
        populateApplicationSelect(apps, 'policyApp');
    } catch (error) {
        select.innerHTML = '<option value="">Error loading applications</option>';
    }
}

function populateApplicationSelect(apps, selectId = 'policyApp') {
    const select = document.getElementById(selectId);
    apps.forEach(app => {
        if (app.status === 'running') {
            const option = document.createElement('option');
            option.value = app.name;
            option.textContent = app.name;
            select.appendChild(option);
        }
    });
}

async function submitCreatePolicy() {
    const form = document.getElementById('policyForm');
    const formData = new FormData(form);
    
    const policyData = {
        application: formData.get('application'),
        minReplicas: parseInt(formData.get('minReplicas')),
        maxReplicas: parseInt(formData.get('maxReplicas')),
        cpuThreshold: parseInt(formData.get('cpuThreshold')),
        memoryThreshold: parseInt(formData.get('memoryThreshold'))
    };
    
    if (!policyData.application) {
        alert('Please select an application');
        return;
    }
    
    if (policyData.minReplicas >= policyData.maxReplicas) {
        alert('Max replicas must be greater than min replicas');
        return;
    }
    
    try {
        const response = await fetch('/api/cluster.php?action=create_scaling_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(policyData)
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`Auto-scaling policy created for ${policyData.application}`);
            closeCreatePolicyModal();
            refreshAutoScaling();
            refreshApplications(); // Update auto-scaling badges
        } else {
            alert(`Failed to create policy: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function editPolicy(appName) {
    try {
        const response = await fetch('/api/cluster.php?action=get_scaling_policies');
        const policies = await response.json();
        const policy = policies[appName];
        
        if (!policy) {
            alert('Policy not found');
            return;
        }
        
        const newMin = prompt(`Min replicas for ${appName}:`, policy.minReplicas);
        if (!newMin || isNaN(newMin)) return;
        
        const newMax = prompt(`Max replicas for ${appName}:`, policy.maxReplicas);
        if (!newMax || isNaN(newMax)) return;
        
        const newCpu = prompt(`CPU threshold % for ${appName}:`, policy.cpuThreshold);
        if (!newCpu || isNaN(newCpu)) return;
        
        const newMemory = prompt(`Memory threshold % for ${appName}:`, policy.memoryThreshold);
        if (!newMemory || isNaN(newMemory)) return;
        
        const updateResponse = await fetch('/api/cluster.php?action=update_scaling_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                application: appName,
                minReplicas: parseInt(newMin),
                maxReplicas: parseInt(newMax),
                cpuThreshold: parseInt(newCpu),
                memoryThreshold: parseInt(newMemory)
            })
        });
        
        const result = await updateResponse.json();
        if (result.success) {
            alert(`Policy updated for ${appName}`);
            refreshAutoScaling();
        } else {
            alert(`Failed to update policy: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function deletePolicy(appName) {
    if (confirm(`Delete auto-scaling policy for ${appName}?`)) {
        try {
            const response = await fetch('/api/cluster.php?action=delete_scaling_policy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ application: appName })
            });
            
            const result = await response.json();
            if (result.success) {
                alert(`Policy deleted for ${appName}`);
                refreshAutoScaling();
                refreshApplications();
            } else {
                alert(`Failed to delete policy: ${result.error}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Close modals with Escape key
    if (event.key === 'Escape') {
        closeNodeModal();
        closeDeployModal();
        closeCreatePolicyModal();
        closeCreateScheduledPolicyModal();
        closeAnalyticsModal();
        closeCostSavingsModal();
        closeAppDetailsModal();
        closeContainerDetailsModal();
    }
});

async function viewApplicationDetails(appName) {
    try {
        const response = await fetch(`/api/cluster.php?action=app_details&app_name=${appName}`);
        const data = await response.json();
        
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        
        // Populate modal with application details
        document.getElementById('appModalTitle').textContent = `${appName} Details`;
        document.getElementById('appName').textContent = appName;
        document.getElementById('appStatus').innerHTML = `<span class="status-badge status-${data.application.status}">${data.application.status}</span>`;
        document.getElementById('appReplicas').textContent = data.application.replicas;
        document.getElementById('appVersion').textContent = data.application.version;
        document.getElementById('appUptime').textContent = data.application.uptime;
        document.getElementById('appCpu').textContent = `${data.application.cpu_percent}%`;
        document.getElementById('appMemory').textContent = `${data.application.memory_mb} MB`;
        document.getElementById('appAutoScaling').innerHTML = data.application.autoScaling ? 
            '<span class="status-badge status-running">Enabled</span>' : 
            '<span class="status-badge status-stopped">Disabled</span>';
        
        // Populate container health info
        const healthDiv = document.getElementById('containerHealth');
        const runningContainers = data.containers.filter(c => c.status.includes('Up')).length;
        const failedContainers = data.containers.filter(c => c.status.includes('Exited') && !c.status.includes('Exited (0)')).length;
        const totalContainers = data.containers.length;
        
        healthDiv.innerHTML = `
            <p><strong>Running:</strong> ${runningContainers}/${totalContainers}</p>
            <p><strong>Failed:</strong> ${failedContainers}</p>
            ${failedContainers > 0 ? '<p><span class="status-badge status-unhealthy">⚠️ Auto-replacement needed</span></p>' : ''}
        `;
        
        // Populate containers table
        const containersTable = document.getElementById('containersTable');
        containersTable.innerHTML = '';
        data.containers.forEach(container => {
            const row = document.createElement('tr');
            const isRunning = container.status.includes('Up');
            const isExited = container.status.includes('Exited');
            const statusClass = isRunning ? 'status-running' : (isExited ? 'status-stopped' : 'status-paused');
            
            // Add warning for failed containers
            const statusDisplay = isExited && !container.status.includes('Exited (0)') ? 
                `<span class="status-badge status-unhealthy">${container.status} ⚠️</span>` :
                `<span class="status-badge ${statusClass}">${container.status}</span>`;
            
            row.innerHTML = `
                <td><a href="#" class="container-link" onclick="viewContainerDetails('${container.name}')">${container.name}</a></td>
                <td>${statusDisplay}</td>
                <td>${container.ports || 'None'}</td>
                <td>${container.id}</td>
                <td>${container.created}</td>
            `;
            containersTable.appendChild(row);
        });
        
        // Populate scaling policy
        const policyDiv = document.getElementById('scalingPolicyInfo');
        if (data.scaling_policy) {
            policyDiv.innerHTML = `
                <p><strong>Min Replicas:</strong> ${data.scaling_policy.minReplicas}</p>
                <p><strong>Max Replicas:</strong> ${data.scaling_policy.maxReplicas}</p>
                <p><strong>CPU Threshold:</strong> ${data.scaling_policy.cpuThreshold}%</p>
                <p><strong>Memory Threshold:</strong> ${data.scaling_policy.memoryThreshold}%</p>
                <p><strong>Status:</strong> <span class="status-badge status-running">Enabled</span></p>
            `;
        } else {
            policyDiv.innerHTML = '<p>No auto-scaling policy configured</p>';
        }
        
        // Remove deployment info section since we replaced it with container health
        
        // Populate recent events
        const eventsTable = document.getElementById('recentEventsTable');
        eventsTable.innerHTML = '';
        if (data.recent_events.length > 0) {
            data.recent_events.forEach(event => {
                const row = document.createElement('tr');
                const timestamp = new Date(event.timestamp * 1000).toLocaleString();
                row.innerHTML = `
                    <td>${timestamp}</td>
                    <td><span class="status-badge ${event.action === 'scale_up' ? 'status-running' : 'status-warning'}">${event.action}</span></td>
                    <td>${event.replicas}</td>
                    <td>${event.reason}</td>
                `;
                eventsTable.appendChild(row);
            });
        } else {
            eventsTable.innerHTML = '<tr><td colspan="4">No recent scaling events</td></tr>';
        }
        
        // Show modal
        document.getElementById('appDetailsModal').style.display = 'flex';
        
    } catch (error) {
        alert(`Error loading application details: ${error.message}`);
    }
}

function closeAppDetailsModal() {
    document.getElementById('appDetailsModal').style.display = 'none';
}

async function viewContainerDetails(containerName) {
    try {
        const response = await fetch(`/api/cluster.php?action=container_details&container_name=${containerName}`);
        const data = await response.json();
        
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        
        // Populate container details modal
        document.getElementById('containerModalTitle').textContent = `${containerName} Details`;
        document.getElementById('containerName').textContent = data.name;
        document.getElementById('containerId').textContent = data.id.substring(0, 12);
        document.getElementById('containerImage').textContent = data.image;
        document.getElementById('containerCreated').textContent = new Date(data.created).toLocaleString();
        
        // State information
        const state = data.state;
        document.getElementById('containerStatus').innerHTML = `<span class="status-badge ${state.Running ? 'status-running' : 'status-stopped'}">${state.Status}</span>`;
        document.getElementById('containerExitCode').textContent = state.ExitCode !== null ? state.ExitCode : 'N/A';
        document.getElementById('containerError').textContent = state.Error || 'None';
        
        // Resource stats
        const statsDiv = document.getElementById('containerStats');
        if (data.stats) {
            statsDiv.innerHTML = `
                <p><strong>CPU:</strong> ${data.stats.cpu}</p>
                <p><strong>Memory:</strong> ${data.stats.memory}</p>
                <p><strong>Network I/O:</strong> ${data.stats.network}</p>
                <p><strong>Block I/O:</strong> ${data.stats.block_io}</p>
            `;
        } else {
            statsDiv.innerHTML = '<p>Container not running - no stats available</p>';
        }
        
        // Logs
        document.getElementById('containerLogs').textContent = data.logs;
        
        // Show modal
        document.getElementById('containerDetailsModal').style.display = 'flex';
        
    } catch (error) {
        alert(`Error loading container details: ${error.message}`);
    }
}

function closeContainerDetailsModal() {
    document.getElementById('containerDetailsModal').style.display = 'none';
}

// Update modal click handlers
window.onclick = function(event) {
    const nodeModal = document.getElementById('nodeModal');
    const deployModal = document.getElementById('deployModal');
    const policyModal = document.getElementById('createPolicyModal');
    const appModal = document.getElementById('appDetailsModal');
    const containerModal = document.getElementById('containerDetailsModal');
    
    if (event.target === nodeModal) closeNodeModal();
    if (event.target === deployModal) closeDeployModal();
    if (event.target === policyModal) closeCreatePolicyModal();
    if (event.target === appModal) closeAppDetailsModal();
    if (event.target === containerModal) closeContainerDetailsModal();
}

// Phase 3: Scheduled Scaling Functions
async function refreshScheduledScaling() {
    try {
        await refreshScheduledPolicies();
        await refreshScheduleHistory();
        await refreshScheduleSummary();
    } catch (error) {
        console.error('Error refreshing scheduled scaling:', error);
    }
}

async function refreshScheduledPolicies() {
    const tbody = document.getElementById('scheduled-policies-tbody');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/cluster.php?action=get_scheduled_policies');
        const policies = await response.json();
        
        tbody.innerHTML = '';
        
        if (!policies || policies.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7">No scheduled policies configured</td></tr>';
            return;
        }
        
        policies.forEach(policy => {
            policy.schedules.forEach(schedule => {
                const row = document.createElement('tr');
                const statusBadge = schedule.enabled ? 
                    '<span class="status-badge status-running">Active</span>' :
                    '<span class="status-badge status-stopped">Inactive</span>';
                
                const days = schedule.days.map(d => ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d]).join(', ');
                
                row.innerHTML = `
                    <td>${policy.application}</td>
                    <td>${schedule.name}</td>
                    <td>${schedule.time}</td>
                    <td>${days}</td>
                    <td>${schedule.replicas}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <button class="btn btn-small btn-secondary" onclick="editSchedule('${policy.application}', '${schedule.name}')">Edit</button>
                        <button class="btn btn-small btn-danger" onclick="deleteSchedule('${policy.application}', '${schedule.name}')">Delete</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        });
        
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7">Error loading scheduled policies</td></tr>';
    }
}

async function refreshScheduleHistory() {
    const tbody = document.getElementById('schedule-history-tbody');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/cluster.php?action=schedule_history');
        const history = await response.json();
        
        tbody.innerHTML = '';
        
        if (!history || history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No schedule execution history</td></tr>';
            return;
        }
        
        history.slice(-10).reverse().forEach(event => {
            const row = document.createElement('tr');
            const timestamp = new Date(event.timestamp).toLocaleString();
            const statusBadge = event.success ? 
                '<span class="status-badge status-running">Success</span>' :
                '<span class="status-badge status-unhealthy">Failed</span>';
            
            row.innerHTML = `
                <td>${timestamp}</td>
                <td>${event.application}</td>
                <td>${event.schedule_name}</td>
                <td>${event.target_replicas}</td>
                <td>${statusBadge}</td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="5">Error loading schedule history</td></tr>';
    }
}

async function refreshScheduleSummary() {
    try {
        const response = await fetch('/api/cluster.php?action=schedule_summary');
        const summary = await response.json();
        
        document.getElementById('active-schedules').textContent = summary.active_schedules || '0';
        document.getElementById('next-execution').textContent = summary.next_execution || 'None';
        document.getElementById('todays-actions').textContent = summary.todays_actions || '0';
        
    } catch (error) {
        document.getElementById('active-schedules').textContent = '0';
        document.getElementById('next-execution').textContent = 'Error';
        document.getElementById('todays-actions').textContent = '0';
    }
}

function showCreateScheduledPolicyModal() {
    loadApplicationsForScheduledPolicy();
    document.getElementById('createScheduledPolicyModal').style.display = 'flex';
}

function closeCreateScheduledPolicyModal() {
    document.getElementById('createScheduledPolicyModal').style.display = 'none';
}

async function loadApplicationsForScheduledPolicy() {
    const select = document.getElementById('scheduledApp');
    select.innerHTML = '<option value="">Select Application</option>';
    
    // Use cached applications if available
    if (cachedApplications.length > 0) {
        populateApplicationSelect(cachedApplications, 'scheduledApp');
        return;
    }
    
    // Otherwise fetch fresh data
    try {
        const response = await fetch('/api/cluster.php?action=applications');
        const apps = await response.json();
        cachedApplications = apps;
        populateApplicationSelect(apps, 'scheduledApp');
    } catch (error) {
        select.innerHTML = '<option value="">Error loading applications</option>';
    }
}

async function submitCreateScheduledPolicy() {
    const form = document.getElementById('scheduledPolicyForm');
    const formData = new FormData(form);
    
    const selectedDays = Array.from(form.querySelectorAll('input[name="days"]:checked')).map(cb => parseInt(cb.value));
    
    if (selectedDays.length === 0) {
        alert('Please select at least one day of the week');
        return;
    }
    
    const policyData = {
        application: formData.get('application'),
        schedule_name: formData.get('scheduleName'),
        time: formData.get('scheduleTime'),
        days: selectedDays,
        target_replicas: parseInt(formData.get('targetReplicas'))
    };
    
    if (!policyData.application || !policyData.schedule_name || !policyData.time) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('/api/cluster.php?action=create_scheduled_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(policyData)
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`Scheduled policy created: ${policyData.schedule_name}`);
            closeCreateScheduledPolicyModal();
            refreshScheduledScaling();
        } else {
            alert(`Failed to create scheduled policy: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}



async function editSchedule(appName, scheduleName) {
    try {
        const response = await fetch('/api/cluster.php?action=get_scheduled_policies');
        const policies = await response.json();
        const policy = policies.find(p => p.application === appName);
        const schedule = policy?.schedules.find(s => s.name === scheduleName);
        
        if (!schedule) {
            alert('Schedule not found');
            return;
        }
        
        const newTime = prompt(`New time for ${scheduleName}:`, schedule.time);
        if (!newTime) return;
        
        const newReplicas = prompt(`New target replicas:`, schedule.replicas);
        if (!newReplicas || isNaN(newReplicas)) return;
        
        const updateResponse = await fetch('/api/cluster.php?action=update_scheduled_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                application: appName,
                schedule_name: scheduleName,
                time: newTime,
                target_replicas: parseInt(newReplicas)
            })
        });
        
        const result = await updateResponse.json();
        if (result.success) {
            alert(`Schedule ${scheduleName} updated`);
            refreshScheduledScaling();
        } else {
            alert(`Failed to update schedule: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function deleteSchedule(appName, scheduleName) {
    if (confirm(`Delete schedule ${scheduleName} for ${appName}?`)) {
        try {
            const response = await fetch('/api/cluster.php?action=delete_scheduled_policy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ application: appName, schedule_name: scheduleName })
            });
            
            const result = await response.json();
            if (result.success) {
                alert(`Schedule ${scheduleName} deleted`);
                refreshScheduledScaling();
            } else {
                alert(`Failed to delete schedule: ${result.error}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
}

// Phase 3: Analytics Functions
function showAnalyticsModal() {
    refreshAnalytics();
    document.getElementById('analyticsModal').style.display = 'flex';
}

function closeAnalyticsModal() {
    document.getElementById('analyticsModal').style.display = 'none';
}

async function refreshAnalytics() {
    try {
        const response = await fetch('/api/cluster.php?action=scaling_analytics');
        const analytics = await response.json();
        
        // Update overview metrics
        document.getElementById('efficiencyScore').textContent = (analytics.efficiency_score || 0).toFixed(2);
        document.getElementById('totalEvents24h').textContent = analytics.total_events_24h || '0';
        document.getElementById('avgResponseTime').textContent = `${(analytics.avg_response_time || 0).toFixed(1)}s`;
        document.getElementById('costSavings').textContent = `$${(analytics.cost_savings || 0).toFixed(2)}`;
        
        // Update application analytics table
        const tbody = document.getElementById('app-analytics-tbody');
        tbody.innerHTML = '';
        
        if (analytics.applications && Object.keys(analytics.applications).length > 0) {
            Object.entries(analytics.applications).forEach(([appName, appAnalytics]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${appName}</td>
                    <td>${appAnalytics.total_events || 0}</td>
                    <td>${appAnalytics.scale_up_events || 0}</td>
                    <td>${appAnalytics.scale_down_events || 0}</td>
                    <td>${(appAnalytics.avg_decision_score || 0).toFixed(2)}</td>
                    <td>${(appAnalytics.efficiency || 0).toFixed(2)}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="6">No analytics data available</td></tr>';
        }
        
    } catch (error) {
        console.error('Error loading analytics:', error);
        document.getElementById('efficiencyScore').textContent = 'Error';
        document.getElementById('totalEvents24h').textContent = 'Error';
        document.getElementById('avgResponseTime').textContent = 'Error';
        document.getElementById('costSavings').textContent = 'Error';
    }
}

// Enhanced policy creation with advanced options
function toggleAdvancedOptions() {
    const policyType = document.getElementById('policyType').value;
    const advancedOptions = document.getElementById('advancedOptions');
    
    if (policyType === 'multi-metric') {
        advancedOptions.style.display = 'block';
    } else {
        advancedOptions.style.display = 'none';
    }
}

// Cost Savings Modal Functions
function showCostSavingsModal() {
    loadCostSavingsBreakdown();
    document.getElementById('costSavingsModal').style.display = 'flex';
}

function closeCostSavingsModal() {
    document.getElementById('costSavingsModal').style.display = 'none';
}

async function loadCostSavingsBreakdown() {
    try {
        const response = await fetch('/api/cluster.php?action=cost_savings_breakdown');
        const data = await response.json();
        
        // Resource optimization
        document.getElementById('scaleDownCount').textContent = data.scale_down_events || 0;
        document.getElementById('scaleDownSavings').textContent = `$${(data.scale_down_savings || 0).toFixed(2)}`;
        document.getElementById('overProvisionHours').textContent = (data.over_provision_hours || 0).toFixed(1);
        document.getElementById('overProvisionSavings').textContent = `$${(data.over_provision_savings || 0).toFixed(2)}`;
        
        // Operational efficiency
        document.getElementById('manualPreventionCount').textContent = data.manual_prevention_count || 0;
        document.getElementById('manualPreventionSavings').textContent = `$${(data.manual_prevention_savings || 0).toFixed(2)}`;
        document.getElementById('responseTimeSavings').textContent = (data.response_time_minutes || 0).toFixed(1);
        document.getElementById('responseTimeCost').textContent = `$${(data.response_time_cost || 0).toFixed(2)}`;
        
        // Totals
        const resourceTotal = (data.scale_down_savings || 0) + (data.over_provision_savings || 0);
        const operationalTotal = (data.manual_prevention_savings || 0) + (data.response_time_cost || 0);
        const dailyTotal = resourceTotal + operationalTotal;
        
        document.getElementById('totalResourceSavings').textContent = `$${resourceTotal.toFixed(2)}`;
        document.getElementById('totalOperationalSavings').textContent = `$${operationalTotal.toFixed(2)}`;
        document.getElementById('totalDailySavings').textContent = `$${dailyTotal.toFixed(2)}`;
        document.getElementById('monthlySavings').textContent = `$${(dailyTotal * 30).toFixed(2)}`;
        document.getElementById('annualSavings').textContent = `$${(dailyTotal * 365).toFixed(2)}`;
        
    } catch (error) {
        console.error('Error loading cost breakdown:', error);
        // Set default values on error
        document.querySelectorAll('.calc-value, .savings-table td:nth-child(2)').forEach(el => {
            if (el.textContent === '-') el.textContent = '0';
        });
    }
}

function exportCostAnalysis() {
    const data = {
        timestamp: new Date().toISOString(),
        daily_savings: document.getElementById('totalDailySavings').textContent,
        monthly_projection: document.getElementById('monthlySavings').textContent,
        annual_projection: document.getElementById('annualSavings').textContent,
        breakdown: {
            resource_optimization: document.getElementById('totalResourceSavings').textContent,
            operational_efficiency: document.getElementById('totalOperationalSavings').textContent
        }
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cost-savings-analysis-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// Auto-scaling sub-tab management
function showAutoScalingSubTab(subTabName) {
    // Hide all sub-tab contents
    document.querySelectorAll('.sub-tab-content').forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none';
    });
    
    // Remove active class from all sub-tab buttons
    document.querySelectorAll('.sub-tab-button').forEach(button => {
        button.classList.remove('active');
        button.style.background = 'transparent';
        button.style.color = '#6c757d';
    });
    
    // Show selected sub-tab
    const subTabElement = document.getElementById(`${subTabName}-subtab`);
    if (subTabElement) {
        subTabElement.classList.add('active');
        subTabElement.style.display = 'block';
    }
    
    // Add active class to clicked button
    if (event && event.target) {
        event.target.classList.add('active');
        event.target.style.background = '#3498db';
        event.target.style.color = 'white';
    }
    
    // Refresh data for the sub-tab
    if (subTabName === 'ml') {
        refreshMLData();
    } else if (subTabName === 'events') {
        refreshScalingEvents();
    } else {
        refreshAutoScaling();
    }
}

// ML Functions
async function refreshMLData() {
    try {
        await refreshMLSystemStatus();
        await refreshMLPolicies();
        await refreshMLTrainingData();
        await refreshMLPredictions();
    } catch (error) {
        console.error('Error refreshing ML data:', error);
    }
}

async function refreshMLSystemStatus() {
    try {
        console.log('Refreshing ML system status...');
        const response = await fetch('/api/cluster.php?action=get_ml_status');
        const status = await response.json();
        console.log('ML Status received:', status);
        
        // Update all ML status elements that exist on the page
        const elements = {
            'ml-policies-count': status.ml_policies || '0',
            'training-data-points': status.training_data_points || '0', 
            'models-trained': status.models_trained || '0',
            'last-prediction': status.last_prediction || 'None',
            'prediction-accuracy': status.prediction_accuracy || 'N/A',
            'avg-confidence': status.avg_confidence ? `${status.avg_confidence}%` : 'N/A',
            'ml-scaling-actions': status.ml_scaling_actions || '0'
        };
        
        // Update each element if it exists
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                console.log(`Updating ${id} to ${value}`);
                element.textContent = value;
            } else {
                console.log(`Element ${id} not found`);
            }
        });
        
        // Update data collection status with proper badge
        const statusElement = document.getElementById('data-collection-status');
        if (statusElement) {
            const statusHtml = status.data_collection_active ? 
                '<span class="status-badge status-running">Active</span>' : 
                '<span class="status-badge status-stopped">Inactive</span>';
            console.log('Updating data collection status to:', statusHtml);
            statusElement.innerHTML = statusHtml;
        }
        
    } catch (error) {
        console.error('Error loading ML status:', error);
        // Set error state for elements that exist
        const errorElements = ['ml-policies-count', 'training-data-points', 'models-trained'];
        errorElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = 'Error';
            }
        });
    }
}

async function refreshMLPolicies() {
    const tbody = document.getElementById('ml-policies-tbody');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/cluster.php?action=get_ml_policies');
        const policies = await response.json();
        
        tbody.innerHTML = '';
        
        if (!policies || policies.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7">No ML policies configured</td></tr>';
            return;
        }
        
        policies.forEach(policy => {
            const row = document.createElement('tr');
            const statusBadge = policy.enabled ? 
                '<span class="status-badge status-running">Active</span>' :
                '<span class="status-badge status-stopped">Inactive</span>';
            
            const lastPrediction = policy.last_prediction ? 
                new Date(policy.last_prediction).toLocaleString() : 'None';
            
            row.innerHTML = `
                <td>${policy.application}</td>
                <td>${policy.prediction_horizon}m</td>
                <td>${policy.confidence_threshold}%</td>
                <td>${policy.min_replicas}-${policy.max_replicas}</td>
                <td>${statusBadge}</td>
                <td>${lastPrediction}</td>
                <td>
                    <button class="btn btn-small btn-secondary" onclick="editMLPolicy('${policy.application}')">Edit</button>
                    <button class="btn btn-small btn-danger" onclick="deleteMLPolicy('${policy.application}')">Delete</button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7">Error loading ML policies</td></tr>';
    }
}

async function refreshMLTrainingData() {
    const tbody = document.getElementById('ml-training-data-tbody');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/cluster.php?action=get_ml_training_data');
        const data = await response.json();
        
        tbody.innerHTML = '';
        
        if (!data || Object.keys(data).length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No training data available</td></tr>';
            return;
        }
        
        Object.entries(data).forEach(([appName, appData]) => {
            const row = document.createElement('tr');
            const readyBadge = appData.ready_for_training ? 
                '<span class="training-status training-ready">Ready</span>' :
                '<span class="training-status training-insufficient">Insufficient</span>';
            
            const dateRange = appData.date_range ? 
                `${appData.date_range.days} days` : 'N/A';
            
            const lastCollection = appData.last_collection ? 
                new Date(appData.last_collection).toLocaleString() : 'None';
            
            row.innerHTML = `
                <td>${appName}</td>
                <td>${appData.data_points || 0}</td>
                <td>${dateRange}</td>
                <td>${readyBadge}</td>
                <td>${lastCollection}</td>
                <td>
                    <button class="btn btn-small btn-secondary" onclick="viewTrainingData('${appName}')">View</button>
                    <button class="btn btn-small btn-primary" onclick="trainMLModel('${appName}')">Train</button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6">Error loading training data</td></tr>';
    }
}

async function refreshMLPredictions() {
    const tbody = document.getElementById('ml-predictions-tbody');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/cluster.php?action=get_ml_predictions');
        const predictions = await response.json();
        
        tbody.innerHTML = '';
        
        if (!predictions || predictions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7">No ML predictions available</td></tr>';
            return;
        }
        
        predictions.slice(-10).reverse().forEach(prediction => {
            const row = document.createElement('tr');
            const timestamp = new Date(prediction.timestamp).toLocaleString();
            
            const confidenceClass = prediction.confidence >= 75 ? 'confidence-high' : 
                                   prediction.confidence >= 50 ? 'confidence-medium' : 'confidence-low';
            
            const actionTaken = prediction.action_taken ? 
                `<span class="prediction-type prediction-ml">${prediction.action_taken}</span>` :
                '<span class="prediction-type prediction-threshold">None</span>';
            
            row.innerHTML = `
                <td>${timestamp}</td>
                <td>${prediction.application}</td>
                <td>${prediction.predicted_cpu?.toFixed(1) || 'N/A'}%</td>
                <td>${prediction.predicted_memory?.toFixed(1) || 'N/A'}%</td>
                <td>${prediction.recommended_replicas || 'N/A'}</td>
                <td><span class="confidence-indicator ${confidenceClass}">${prediction.confidence?.toFixed(1) || 0}%</span></td>
                <td>${actionTaken}</td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7">Error loading ML predictions</td></tr>';
    }
}

// ML Policy Management
// Make Create ML Policy function globally accessible
window.showCreateMLPolicyModal = function() {
    // Load applications for ML policy
    loadApplicationsForMLPolicy();
    
    // Create and show ML policy modal
    const modal = document.createElement('div');
    modal.id = 'createMLPolicyModal';
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Create ML Predictive Scaling Policy</h3>
                <span class="close" onclick="closeMLPolicyModal()">&times;</span>
            </div>
            <div class="modal-body">
                <form id="mlPolicyForm">
                    <div class="form-group">
                        <label for="mlApp">Application *</label>
                        <select id="mlApp" required>
                            <option value="">Select Application</option>
                        </select>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="predictionHorizon">Prediction Horizon (minutes) *</label>
                            <input type="number" id="predictionHorizon" required min="5" max="120" value="30">
                        </div>
                        <div class="form-group">
                            <label for="confidenceThreshold">Confidence Threshold (%) *</label>
                            <input type="number" id="confidenceThreshold" required min="50" max="95" value="75">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="mlMinReplicas">Min Replicas *</label>
                            <input type="number" id="mlMinReplicas" required min="1" value="1">
                        </div>
                        <div class="form-group">
                            <label for="mlMaxReplicas">Max Replicas *</label>
                            <input type="number" id="mlMaxReplicas" required min="1" value="10">
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeMLPolicyModal()">Cancel</button>
                <button class="btn btn-primary" onclick="submitMLPolicy()">Create ML Policy</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Make ML Analytics function globally accessible
window.showMLAnalyticsModal = function() {
    // Create and show ML analytics modal
    const modal = document.createElement('div');
    modal.id = 'mlAnalyticsModal';
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3>ML Predictive Scaling Analytics</h3>
                <span class="close" onclick="closeMLAnalyticsModal()">&times;</span>
            </div>
            <div class="modal-body modal-scrollable">
                <div class="analytics-grid">
                    <div class="analytics-card">
                        <h4>Prediction Accuracy</h4>
                        <div class="metric-large" id="mlAccuracy">-</div>
                        <p>Overall ML prediction accuracy</p>
                    </div>
                    <div class="analytics-card">
                        <h4>ML Scaling Actions</h4>
                        <div class="metric-large" id="mlActions">-</div>
                        <p>Actions taken by ML predictions</p>
                    </div>
                    <div class="analytics-card">
                        <h4>Training Data Points</h4>
                        <div class="metric-large" id="mlDataPoints">-</div>
                        <p>Total data points collected</p>
                    </div>
                    <div class="analytics-card">
                        <h4>Model Performance</h4>
                        <div class="metric-large" id="mlPerformance">-</div>
                        <p>Average confidence score</p>
                    </div>
                </div>
                <div class="table-container">
                    <h4>Recent ML Predictions</h4>
                    <table id="ml-analytics-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Application</th>
                                <th>Predicted Load</th>
                                <th>Confidence</th>
                                <th>Action</th>
                                <th>Result</th>
                            </tr>
                        </thead>
                        <tbody id="ml-analytics-tbody">
                            <tr><td colspan="6">Loading ML analytics...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeMLAnalyticsModal()">Close</button>
                <button class="btn btn-primary" onclick="refreshMLAnalytics()">Refresh</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Load ML analytics data
    loadMLAnalytics();
}

// Make close functions globally accessible
window.closeMLPolicyModal = function() {
    const modal = document.getElementById('createMLPolicyModal');
    if (modal) modal.remove();
}

window.closeMLAnalyticsModal = function() {
    const modal = document.getElementById('mlAnalyticsModal');
    if (modal) modal.remove();
}

window.refreshMLAnalytics = function() {
    loadMLAnalytics();
}

async function loadApplicationsForMLPolicy() {
    try {
        const response = await fetch('/api/cluster.php?action=applications');
        const apps = await response.json();
        const select = document.getElementById('mlApp');
        if (select) {
            select.innerHTML = '<option value="">Select Application</option>';
            if (apps && Array.isArray(apps)) {
                apps.forEach(app => {
                    if (app.status === 'running') {
                        const option = document.createElement('option');
                        option.value = app.name;
                        option.textContent = app.name;
                        select.appendChild(option);
                    }
                });
            }
        }
    } catch (error) {
        console.error('Error loading applications:', error);
        const select = document.getElementById('mlApp');
        if (select) {
            select.innerHTML = '<option value="">Error loading applications</option>';
        }
    }
}

// Make submit ML policy function globally accessible
window.submitMLPolicy = async function() {
    const form = document.getElementById('mlPolicyForm');
    const formData = new FormData(form);
    
    const policyData = {
        application: document.getElementById('mlApp').value,
        prediction_horizon: parseInt(document.getElementById('predictionHorizon').value),
        confidence_threshold: parseInt(document.getElementById('confidenceThreshold').value),
        min_replicas: parseInt(document.getElementById('mlMinReplicas').value),
        max_replicas: parseInt(document.getElementById('mlMaxReplicas').value),
        enabled: true
    };
    
    if (!policyData.application) {
        alert('Please select an application');
        return;
    }
    
    try {
        const response = await fetch('/api/cluster.php?action=create_ml_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(policyData)
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`ML policy created for ${policyData.application}`);
            closeMLPolicyModal();
            refreshMLData();
        } else {
            alert(`Failed to create ML policy: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function loadMLAnalytics() {
    try {
        const response = await fetch('/api/cluster.php?action=get_ml_analytics');
        const analytics = await response.json();
        
        // Update analytics cards with real calculated values only
        const accuracyElement = document.getElementById('mlAccuracy');
        const actionsElement = document.getElementById('mlActions');
        const dataPointsElement = document.getElementById('mlDataPoints');
        const performanceElement = document.getElementById('mlPerformance');
        
        if (accuracyElement) {
            accuracyElement.textContent = analytics.prediction_accuracy ? `${analytics.prediction_accuracy}%` : 'N/A';
        }
        if (actionsElement) {
            actionsElement.textContent = analytics.ml_scaling_actions || '0';
        }
        if (dataPointsElement) {
            dataPointsElement.textContent = analytics.training_data_points || '0';
        }
        if (performanceElement) {
            performanceElement.textContent = analytics.avg_confidence ? `${analytics.avg_confidence}%` : 'N/A';
        }
        
        // Load recent predictions with proper data formatting
        const tbody = document.getElementById('ml-analytics-tbody');
        if (tbody) {
            if (analytics.predictions && analytics.predictions.length > 0) {
                tbody.innerHTML = '';
                analytics.predictions.forEach(pred => {
                    const row = document.createElement('tr');
                    
                    // Use predicted_load if available, otherwise calculate from CPU/memory
                    let predictedLoad = 'N/A';
                    if (pred.predicted_load !== undefined) {
                        predictedLoad = `${pred.predicted_load.toFixed(1)}%`;
                    } else if (pred.predicted_cpu !== undefined && pred.predicted_memory !== undefined) {
                        predictedLoad = `${Math.max(pred.predicted_cpu, pred.predicted_memory).toFixed(1)}%`;
                    } else if (pred.predicted_cpu !== undefined) {
                        predictedLoad = `${pred.predicted_cpu.toFixed(1)}%`;
                    } else if (pred.predicted_memory !== undefined) {
                        predictedLoad = `${pred.predicted_memory.toFixed(1)}%`;
                    }
                    
                    const confidence = pred.confidence ? `${pred.confidence.toFixed(1)}%` : 'N/A';
                    const action = pred.action_taken || pred.recommended_action || 'None';
                    const result = pred.result || (pred.action_taken && pred.action_taken !== 'None' ? 'Applied' : 'No Action');
                    
                    row.innerHTML = `
                        <td>${new Date(pred.timestamp).toLocaleString()}</td>
                        <td>${pred.application}</td>
                        <td>${predictedLoad}</td>
                        <td>${confidence}</td>
                        <td>${action}</td>
                        <td>${result}</td>
                    `;
                    tbody.appendChild(row);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="6">No ML predictions available yet</td></tr>';
            }
        }
    } catch (error) {
        console.error('Error loading ML analytics:', error);
        // Set error values for elements that exist
        const errorElements = {
            'mlAccuracy': 'Error',
            'mlActions': 'Error', 
            'mlDataPoints': 'Error',
            'mlPerformance': 'Error'
        };
        
        Object.entries(errorElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }
}

function refreshMLAnalytics() {
    loadMLAnalytics();
}

async function editMLPolicy(appName) {
    try {
        const response = await fetch('/api/cluster.php?action=get_ml_policies');
        const policies = await response.json();
        const policy = policies.find(p => p.application === appName);
        
        if (!policy) {
            alert('ML policy not found');
            return;
        }
        
        const newHorizon = prompt(`Prediction horizon (minutes) for ${appName}:`, policy.prediction_horizon);
        if (!newHorizon || isNaN(newHorizon)) return;
        
        const newConfidence = prompt(`Confidence threshold (%) for ${appName}:`, policy.confidence_threshold);
        if (!newConfidence || isNaN(newConfidence)) return;
        
        const updateResponse = await fetch('/api/cluster.php?action=update_ml_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                application: appName,
                prediction_horizon: parseInt(newHorizon),
                confidence_threshold: parseInt(newConfidence)
            })
        });
        
        const result = await updateResponse.json();
        if (result.success) {
            alert(`ML policy updated for ${appName}`);
            refreshMLData();
        } else {
            alert(`Failed to update ML policy: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Add missing ML API endpoints to PHP
async function createMLPolicy() {
    const form = document.getElementById('mlPolicyForm');
    if (!form) {
        showCreateMLPolicyModal();
        return;
    }
    
    const policyData = {
        application: document.getElementById('mlApp').value,
        prediction_horizon: parseInt(document.getElementById('predictionHorizon').value),
        confidence_threshold: parseInt(document.getElementById('confidenceThreshold').value),
        min_replicas: parseInt(document.getElementById('mlMinReplicas').value),
        max_replicas: parseInt(document.getElementById('mlMaxReplicas').value),
        enabled: true
    };
    
    if (!policyData.application) {
        alert('Please select an application');
        return;
    }
    
    try {
        const response = await fetch('/api/cluster.php?action=create_ml_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(policyData)
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`ML policy created for ${policyData.application}`);
            closeMLPolicyModal();
            refreshMLData();
        } else {
            alert(`Failed to create ML policy: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function deleteMLPolicy(appName) {
    if (confirm(`Delete ML policy for ${appName}?`)) {
        try {
            const response = await fetch('/api/cluster.php?action=delete_ml_policy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ application: appName })
            });
            
            const result = await response.json();
            if (result.success) {
                alert(`ML policy deleted for ${appName}`);
                refreshMLData();
            } else {
                alert(`Failed to delete ML policy: ${result.error}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
}

async function viewTrainingData(appName) {
    try {
        const response = await fetch(`/api/cluster.php?action=get_training_data_details&app_name=${appName}`);
        const data = await response.json();
        
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content modal-large">
                <div class="modal-header">
                    <h3>Training Data for ${appName}</h3>
                    <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
                </div>
                <div class="modal-body modal-scrollable">
                    <p><strong>Data Points:</strong> ${data.data_points || 0}</p>
                    <p><strong>Date Range:</strong> ${data.date_range || 'N/A'}</p>
                    <p><strong>Ready for Training:</strong> ${data.ready_for_training ? 'Yes' : 'No'}</p>
                    <div class="table-container">
                        <h4>Recent Data Points</h4>
                        <table>
                            <thead>
                                <tr><th>Timestamp</th><th>CPU %</th><th>Memory %</th><th>Replicas</th></tr>
                            </thead>
                            <tbody>
                                ${(data.recent_points || []).map(point => `
                                    <tr>
                                        <td>${new Date(point.timestamp).toLocaleString()}</td>
                                        <td>${point.cpu_percent}%</td>
                                        <td>${point.memory_percent}%</td>
                                        <td>${point.replicas}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    } catch (error) {
        alert(`Error loading training data: ${error.message}`);
    }
}

async function trainMLModel(appName) {
    if (confirm(`Train ML model for ${appName}? This may take a few minutes.`)) {
        try {
            const response = await fetch('/api/cluster.php?action=train_ml_model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ application: appName })
            });
            
            const result = await response.json();
            if (result.success) {
                alert(`ML model training started for ${appName}`);
                refreshMLData();
            } else {
                alert(`Failed to start training: ${result.error}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
}

// Multi-Horizon Predictions Modal
window.showMultiHorizonPredictions = function() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3>🔮 Multi-Horizon Predictions</h3>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body modal-scrollable">
                <div class="analytics-grid">
                    <div class="analytics-card">
                        <h4>15-Minute Horizon</h4>
                        <div class="metric-large" id="horizon15">Loading...</div>
                        <p>Short-term predictions</p>
                    </div>
                    <div class="analytics-card">
                        <h4>30-Minute Horizon</h4>
                        <div class="metric-large" id="horizon30">Loading...</div>
                        <p>Medium-term predictions</p>
                    </div>
                    <div class="analytics-card">
                        <h4>60-Minute Horizon</h4>
                        <div class="metric-large" id="horizon60">Loading...</div>
                        <p>Long-term predictions</p>
                    </div>
                </div>
                <div class="table-container">
                    <h4>Multi-Horizon Prediction Results</h4>
                    <table id="multi-horizon-table">
                        <thead>
                            <tr><th>Application</th><th>15m Prediction</th><th>30m Prediction</th><th>60m Prediction</th><th>Weighted Decision</th><th>Confidence</th></tr>
                        </thead>
                        <tbody id="multi-horizon-tbody">
                            <tr><td colspan="6">Loading multi-horizon predictions...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
                <button class="btn btn-primary" onclick="refreshMultiHorizonData()">Refresh</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    loadMultiHorizonData();
}

// Anomaly Detection Modal
window.showAnomalyDetection = function() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3>🚨 Anomaly Detection System</h3>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body modal-scrollable">
                <div class="analytics-grid">
                    <div class="analytics-card">
                        <h4>Anomalies Detected</h4>
                        <div class="metric-large" id="anomaliesCount">Loading...</div>
                        <p>Last 24 hours</p>
                    </div>
                    <div class="analytics-card">
                        <h4>Detection Accuracy</h4>
                        <div class="metric-large" id="detectionAccuracy">Loading...</div>
                        <p>IsolationForest model</p>
                    </div>
                    <div class="analytics-card">
                        <h4>Normal Patterns</h4>
                        <div class="metric-large" id="normalPatterns">Loading...</div>
                        <p>Learned behaviors</p>
                    </div>
                </div>
                <div class="table-container">
                    <h4>Recent Anomaly Detections</h4>
                    <table id="anomaly-table">
                        <thead>
                            <tr><th>Time</th><th>Application</th><th>Anomaly Type</th><th>Severity</th><th>CPU</th><th>Memory</th><th>Action Taken</th></tr>
                        </thead>
                        <tbody id="anomaly-tbody">
                            <tr><td colspan="7">Loading anomaly detections...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
                <button class="btn btn-primary" onclick="refreshAnomalyData()">Refresh</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    loadAnomalyData();
}

// Prediction Service Modal
window.showPredictionService = function() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3>⚙️ Automatic Prediction Service</h3>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body modal-scrollable">
                <div class="analytics-grid">
                    <div class="analytics-card">
                        <h4>Service Status</h4>
                        <div class="metric-large" id="serviceStatus">Loading...</div>
                        <p>5-minute update loop</p>
                    </div>
                    <div class="analytics-card">
                        <h4>Update Interval</h4>
                        <div class="metric-large" id="updateInterval">5 min</div>
                        <p>Automatic predictions</p>
                    </div>
                    <div class="analytics-card">
                        <h4>Last Update</h4>
                        <div class="metric-large" id="lastUpdate">Loading...</div>
                        <p>Most recent run</p>
                    </div>
                </div>
                <div class="service-controls" style="margin: 20px 0; text-align: center;">
                    <button class="btn btn-success" onclick="startPredictionService()">Start Service</button>
                    <button class="btn btn-danger" onclick="stopPredictionService()">Stop Service</button>
                    <button class="btn btn-warning" onclick="forcePredictionUpdate()">Force Update</button>
                </div>
                <div class="table-container">
                    <h4>Recent Service Activity</h4>
                    <table id="service-activity-table">
                        <thead>
                            <tr><th>Time</th><th>Action</th><th>Applications Processed</th><th>Predictions Generated</th><th>Status</th></tr>
                        </thead>
                        <tbody id="service-activity-tbody">
                            <tr><td colspan="5">Loading service activity...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
                <button class="btn btn-primary" onclick="refreshServiceData()">Refresh</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    loadServiceData();
}

// Data loading functions for the new modals
async function loadMultiHorizonData() {
    try {
        const response = await fetch('/api/cluster.php?action=get_multi_horizon_predictions');
        const data = await response.json();
        
        document.getElementById('horizon15').textContent = data.horizon_15m?.count || '0';
        document.getElementById('horizon30').textContent = data.horizon_30m?.count || '0';
        document.getElementById('horizon60').textContent = data.horizon_60m?.count || '0';
        
        const tbody = document.getElementById('multi-horizon-tbody');
        if (data.predictions && data.predictions.length > 0) {
            tbody.innerHTML = '';
            data.predictions.forEach(pred => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${pred.application}</td>
                    <td>${pred.horizon_15m || 'N/A'}</td>
                    <td>${pred.horizon_30m || 'N/A'}</td>
                    <td>${pred.horizon_60m || 'N/A'}</td>
                    <td>${pred.weighted_decision || 'N/A'}</td>
                    <td>${pred.confidence || 'N/A'}%</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="6">No multi-horizon predictions available</td></tr>';
        }
    } catch (error) {
        console.error('Error loading multi-horizon data:', error);
    }
}

async function loadAnomalyData() {
    try {
        const response = await fetch('/api/cluster.php?action=get_anomaly_detections');
        const data = await response.json();
        
        document.getElementById('anomaliesCount').textContent = data.anomalies_24h || '0';
        document.getElementById('detectionAccuracy').textContent = data.accuracy ? `${data.accuracy}%` : 'N/A';
        document.getElementById('normalPatterns').textContent = data.normal_patterns || '0';
        
        const tbody = document.getElementById('anomaly-tbody');
        if (data.recent_anomalies && data.recent_anomalies.length > 0) {
            tbody.innerHTML = '';
            data.recent_anomalies.forEach(anomaly => {
                const row = document.createElement('tr');
                const severityClass = anomaly.severity === 'high' ? 'status-unhealthy' : 
                                    anomaly.severity === 'medium' ? 'status-warning' : 'status-info';
                row.innerHTML = `
                    <td>${new Date(anomaly.timestamp).toLocaleString()}</td>
                    <td>${anomaly.application}</td>
                    <td>${anomaly.type}</td>
                    <td><span class="status-badge ${severityClass}">${anomaly.severity}</span></td>
                    <td>${anomaly.cpu}%</td>
                    <td>${anomaly.memory}%</td>
                    <td>${anomaly.action || 'None'}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="7">No anomalies detected recently</td></tr>';
        }
    } catch (error) {
        console.error('Error loading anomaly data:', error);
    }
}

async function loadServiceData() {
    try {
        const response = await fetch('/api/cluster.php?action=get_prediction_service_status');
        const data = await response.json();
        
        const statusElement = document.getElementById('serviceStatus');
        if (data.running) {
            statusElement.innerHTML = '<span class="status-badge status-running">Running</span>';
        } else {
            statusElement.innerHTML = '<span class="status-badge status-stopped">Stopped</span>';
        }
        
        document.getElementById('lastUpdate').textContent = data.last_update ? 
            new Date(data.last_update).toLocaleString() : 'Never';
        
        const tbody = document.getElementById('service-activity-tbody');
        if (data.recent_activity && data.recent_activity.length > 0) {
            tbody.innerHTML = '';
            data.recent_activity.forEach(activity => {
                const row = document.createElement('tr');
                const statusClass = activity.status === 'success' ? 'status-running' : 'status-unhealthy';
                row.innerHTML = `
                    <td>${new Date(activity.timestamp).toLocaleString()}</td>
                    <td>${activity.action}</td>
                    <td>${activity.apps_processed || 0}</td>
                    <td>${activity.predictions_generated || 0}</td>
                    <td><span class="status-badge ${statusClass}">${activity.status}</span></td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5">No recent service activity</td></tr>';
        }
    } catch (error) {
        console.error('Error loading service data:', error);
    }
}

// Service control functions
window.startPredictionService = async function() {
    try {
        const response = await fetch('/api/cluster.php?action=start_prediction_service', {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            alert('Prediction service started successfully');
            refreshServiceData();
        } else {
            alert(`Failed to start service: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

window.stopPredictionService = async function() {
    try {
        const response = await fetch('/api/cluster.php?action=stop_prediction_service', {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            alert('Prediction service stopped successfully');
            refreshServiceData();
        } else {
            alert(`Failed to stop service: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

window.forcePredictionUpdate = async function() {
    try {
        const response = await fetch('/api/cluster.php?action=force_prediction_update', {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            alert('Prediction update triggered successfully');
            refreshServiceData();
        } else {
            alert(`Failed to trigger update: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Refresh functions
window.refreshMultiHorizonData = function() {
    loadMultiHorizonData();
}

window.refreshAnomalyData = function() {
    loadAnomalyData();
}

window.refreshServiceData = function() {
    loadServiceData();
}

// Update modal close handlers
window.onclick = function(event) {
    const modals = {
        'nodeModal': closeNodeModal,
        'deployModal': closeDeployModal,
        'createPolicyModal': closeCreatePolicyModal,
        'createScheduledPolicyModal': closeCreateScheduledPolicyModal,
        'analyticsModal': closeAnalyticsModal,
        'costSavingsModal': closeCostSavingsModal,
        'appDetailsModal': closeAppDetailsModal,
        'containerDetailsModal': closeContainerDetailsModal
    };
    
    Object.entries(modals).forEach(([modalId, closeFunction]) => {
        const modal = document.getElementById(modalId);
        if (event.target === modal) {
            closeFunction();
        }
    });
    
    // Handle dynamically created ML modals
    if (event.target.classList.contains('modal')) {
        event.target.remove();
    }
}

// Step 5: Configurable Model Weights and Auto-Retraining Functions

// Model Weights Configuration Modal
window.showModelWeightsConfig = function() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>⚖️ Configure Model Weights</h3>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body">
                <p>Adjust the relative importance of each ML model in the ensemble prediction:</p>
                <form id="modelWeightsForm">
                    <div class="form-group">
                        <label for="linearTrendWeight">Linear Trend Model Weight:</label>
                        <input type="range" id="linearTrendWeight" min="0" max="1" step="0.1" value="0.3" oninput="updateWeightDisplay()">
                        <span id="linearTrendValue">0.3</span>
                    </div>
                    <div class="form-group">
                        <label for="seasonalPatternWeight">Seasonal Pattern Model Weight:</label>
                        <input type="range" id="seasonalPatternWeight" min="0" max="1" step="0.1" value="0.4" oninput="updateWeightDisplay()">
                        <span id="seasonalPatternValue">0.4</span>
                    </div>
                    <div class="form-group">
                        <label for="anomalyDetectionWeight">Anomaly Detection Model Weight:</label>
                        <input type="range" id="anomalyDetectionWeight" min="0" max="1" step="0.1" value="0.3" oninput="updateWeightDisplay()">
                        <span id="anomalyDetectionValue">0.3</span>
                    </div>
                    <div class="form-group">
                        <p><strong>Total Weight:</strong> <span id="totalWeight">1.0</span> (must equal 1.0)</p>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="saveModelWeights()">Save Weights</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    loadCurrentWeights();
}

// Auto-Retraining Configuration Modal
window.showAutoRetrainingConfig = function() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>🔄 Auto-Retraining Configuration</h3>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body">
                <form id="autoRetrainingForm">
                    <div class="form-group">
                        <label for="retrainInterval">Retrain Interval (hours):</label>
                        <input type="number" id="retrainInterval" min="1" max="168" value="24">
                        <small>How often to automatically retrain models</small>
                    </div>
                    <div class="form-group">
                        <label for="dataRetention">Data Retention (days):</label>
                        <input type="number" id="dataRetention" min="1" max="365" value="30">
                        <small>How long to keep training data</small>
                    </div>
                    <div class="form-group">
                        <label for="minDataPoints">Minimum Data Points:</label>
                        <input type="number" id="minDataPoints" min="100" max="10000" value="1000">
                        <small>Minimum data points required for training</small>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="autoRetrainEnabled" checked>
                            Enable Automatic Retraining
                        </label>
                    </div>
                </form>
                <div class="table-container">
                    <h4>Recent Retraining Events</h4>
                    <table id="retrain-events-table">
                        <thead>
                            <tr><th>Time</th><th>Application</th><th>Trigger</th><th>Models Trained</th><th>Duration</th><th>Status</th></tr>
                        </thead>
                        <tbody id="retrain-events-tbody">
                            <tr><td colspan="6">Loading retraining events...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                <button class="btn btn-warning" onclick="triggerManualRetrain()">Manual Retrain</button>
                <button class="btn btn-primary" onclick="saveAutoRetrainingConfig()">Save Configuration</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    loadAutoRetrainingConfig();
}

// Weight display update function
window.updateWeightDisplay = function() {
    const linearWeight = parseFloat(document.getElementById('linearTrendWeight').value);
    const seasonalWeight = parseFloat(document.getElementById('seasonalPatternWeight').value);
    const anomalyWeight = parseFloat(document.getElementById('anomalyDetectionWeight').value);
    
    document.getElementById('linearTrendValue').textContent = linearWeight.toFixed(1);
    document.getElementById('seasonalPatternValue').textContent = seasonalWeight.toFixed(1);
    document.getElementById('anomalyDetectionValue').textContent = anomalyWeight.toFixed(1);
    
    const total = linearWeight + seasonalWeight + anomalyWeight;
    document.getElementById('totalWeight').textContent = total.toFixed(1);
    
    // Color code the total weight
    const totalElement = document.getElementById('totalWeight');
    if (Math.abs(total - 1.0) < 0.01) {
        totalElement.style.color = 'green';
    } else {
        totalElement.style.color = 'red';
    }
}

// Load current model weights
async function loadCurrentWeights() {
    try {
        const response = await fetch('/api/cluster.php?action=get_model_weights');
        const data = await response.json();
        
        if (data.weights) {
            document.getElementById('linearTrendWeight').value = data.weights.linear_trend || 0.3;
            document.getElementById('seasonalPatternWeight').value = data.weights.seasonal_pattern || 0.4;
            document.getElementById('anomalyDetectionWeight').value = data.weights.anomaly_detection || 0.3;
            updateWeightDisplay();
        }
    } catch (error) {
        console.error('Error loading current weights:', error);
    }
}

// Save model weights
window.saveModelWeights = async function() {
    const linearWeight = parseFloat(document.getElementById('linearTrendWeight').value);
    const seasonalWeight = parseFloat(document.getElementById('seasonalPatternWeight').value);
    const anomalyWeight = parseFloat(document.getElementById('anomalyDetectionWeight').value);
    
    const total = linearWeight + seasonalWeight + anomalyWeight;
    if (Math.abs(total - 1.0) > 0.01) {
        alert('Model weights must sum to 1.0. Current total: ' + total.toFixed(2));
        return;
    }
    
    const weights = {
        linear_trend: linearWeight,
        seasonal_pattern: seasonalWeight,
        anomaly_detection: anomalyWeight
    };
    
    try {
        const response = await fetch('/api/cluster.php?action=update_model_weights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weights: weights })
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Model weights updated successfully');
            document.querySelector('.modal').remove();
            refreshMLData();
        } else {
            alert(`Failed to update weights: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Load auto-retraining configuration
async function loadAutoRetrainingConfig() {
    try {
        const response = await fetch('/api/cluster.php?action=get_ml_configuration');
        const config = await response.json();
        
        document.getElementById('retrainInterval').value = config.retrain_interval_hours || 24;
        document.getElementById('dataRetention').value = config.data_retention_days || 30;
        document.getElementById('minDataPoints').value = config.min_data_points || 1000;
        document.getElementById('autoRetrainEnabled').checked = config.auto_retrain_enabled !== false;
        
        // Load retraining events
        loadRetrainingEvents();
    } catch (error) {
        console.error('Error loading auto-retraining config:', error);
    }
}

// Load retraining events
async function loadRetrainingEvents() {
    try {
        const tbody = document.getElementById('retrain-events-tbody');
        tbody.innerHTML = '<tr><td colspan="6">No retraining events available</td></tr>';
        
        // Sample data for demonstration
        const sampleEvents = [
            {
                timestamp: new Date(Date.now() - 3600000).toISOString(),
                application: 'web-app',
                trigger: 'scheduled',
                models_trained: 3,
                duration_seconds: 45,
                status: 'success'
            },
            {
                timestamp: new Date(Date.now() - 86400000).toISOString(),
                application: 'api-service',
                trigger: 'manual',
                models_trained: 3,
                duration_seconds: 62,
                status: 'success'
            }
        ];
        
        if (sampleEvents.length > 0) {
            tbody.innerHTML = '';
            sampleEvents.forEach(event => {
                const row = document.createElement('tr');
                const statusClass = event.status === 'success' ? 'status-running' : 'status-unhealthy';
                row.innerHTML = `
                    <td>${new Date(event.timestamp).toLocaleString()}</td>
                    <td>${event.application}</td>
                    <td>${event.trigger}</td>
                    <td>${event.models_trained}</td>
                    <td>${event.duration_seconds}s</td>
                    <td><span class="status-badge ${statusClass}">${event.status}</span></td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error loading retraining events:', error);
    }
}

// Save auto-retraining configuration
window.saveAutoRetrainingConfig = async function() {
    const config = {
        retrain_interval_hours: parseInt(document.getElementById('retrainInterval').value),
        data_retention_days: parseInt(document.getElementById('dataRetention').value),
        min_data_points: parseInt(document.getElementById('minDataPoints').value),
        auto_retrain_enabled: document.getElementById('autoRetrainEnabled').checked
    };
    
    try {
        const response = await fetch('/api/cluster.php?action=update_ml_configuration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Auto-retraining configuration saved successfully');
            document.querySelector('.modal').remove();
            refreshMLData();
        } else {
            alert(`Failed to save configuration: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Trigger manual retraining
window.triggerManualRetrain = async function() {
    const appName = prompt('Enter application name for manual retraining:');
    if (!appName) return;
    
    try {
        const response = await fetch('/api/cluster.php?action=trigger_auto_retrain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ application: appName })
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`Manual retraining initiated for ${appName}`);
            loadRetrainingEvents(); // Refresh the events table
        } else {
            alert(`Failed to trigger retraining: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Step 6: Proactive Scaling Configuration Modal
window.showProactiveScalingConfig = function() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>🔮 Proactive Scaling Configuration</h3>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body">
                <p>Configure proactive scaling to scale ahead of predicted demand:</p>
                <form id="proactiveScalingForm">
                    <div class="form-group">
                        <label for="lookAheadMinutes">Look-Ahead Time (minutes):</label>
                        <input type="number" id="lookAheadMinutes" min="5" max="120" value="30">
                        <small>How far ahead to predict and scale proactively</small>
                    </div>
                    <div class="form-group">
                        <label for="proactiveBuffer">Proactive Buffer (%):</label>
                        <input type="number" id="proactiveBuffer" min="0" max="50" value="10">
                        <small>Extra capacity buffer for proactive scaling</small>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="enableProactiveScaling" checked>
                            Enable Proactive Scaling
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="enableProactiveScaleDown" checked>
                            Enable Proactive Scale-Down
                        </label>
                    </div>
                </form>
                <div class="info-section">
                    <h4>How Proactive Scaling Works</h4>
                    <ul>
                        <li><strong>Look-Ahead Prediction:</strong> Uses ML models to predict load at specified future time</li>
                        <li><strong>Early Scaling:</strong> Scales up before thresholds are reached (threshold - 10%)</li>
                        <li><strong>Buffer Capacity:</strong> Adds extra replicas to handle prediction uncertainty</li>
                        <li><strong>Smart Scale-Down:</strong> Only scales down when confident about sustained low load</li>
                    </ul>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="saveProactiveScalingConfig()">Save Configuration</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    loadProactiveScalingConfig();
}

// Load proactive scaling configuration
async function loadProactiveScalingConfig() {
    try {
        const response = await fetch('/api/cluster.php?action=get_proactive_scaling_config');
        const config = await response.json();
        
        document.getElementById('lookAheadMinutes').value = config.look_ahead_minutes || 30;
        document.getElementById('proactiveBuffer').value = config.proactive_buffer_percent || 10;
        document.getElementById('enableProactiveScaling').checked = config.proactive_scaling_enabled !== false;
        document.getElementById('enableProactiveScaleDown').checked = config.proactive_scale_down_enabled !== false;
    } catch (error) {
        console.error('Error loading proactive scaling config:', error);
        // Use defaults on error
        document.getElementById('lookAheadMinutes').value = 30;
        document.getElementById('proactiveBuffer').value = 10;
        document.getElementById('enableProactiveScaling').checked = true;
        document.getElementById('enableProactiveScaleDown').checked = true;
    }
}

// Save proactive scaling configuration
window.saveProactiveScalingConfig = async function() {
    const config = {
        look_ahead_minutes: parseInt(document.getElementById('lookAheadMinutes').value),
        proactive_buffer_percent: parseInt(document.getElementById('proactiveBuffer').value),
        proactive_scaling_enabled: document.getElementById('enableProactiveScaling').checked,
        proactive_scale_down_enabled: document.getElementById('enableProactiveScaleDown').checked
    };
    
    try {
        const response = await fetch('/api/cluster.php?action=update_proactive_scaling_config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Proactive scaling configuration saved successfully');
            document.querySelector('.modal').remove();
            refreshMLData();
        } else {
            alert(`Failed to save configuration: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Define ML functions globally at script load
window.showMLAnalyticsModal = async function() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3>ML Predictive Scaling Analytics</h3>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body modal-scrollable">
                <div class="analytics-grid">
                    <div class="analytics-card">
                        <h4>Prediction Accuracy</h4>
                        <div class="metric-large" id="mlAccuracy">Loading...</div>
                    </div>
                    <div class="analytics-card">
                        <h4>ML Scaling Actions</h4>
                        <div class="metric-large" id="mlActions">Loading...</div>
                    </div>
                    <div class="analytics-card">
                        <h4>Training Data Points</h4>
                        <div class="metric-large" id="mlDataPoints">Loading...</div>
                    </div>
                </div>
                <div class="table-container">
                    <h4>Recent ML Predictions</h4>
                    <table>
                        <thead>
                            <tr><th>Time</th><th>Application</th><th>Predicted Load</th><th>Confidence</th><th>Action</th></tr>
                        </thead>
                        <tbody id="ml-analytics-tbody">
                            <tr><td colspan="5">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    try {
        const response = await fetch('/api/cluster.php?action=get_ml_analytics');
        const data = await response.json();
        document.getElementById('mlAccuracy').textContent = data.prediction_accuracy ? `${data.prediction_accuracy}%` : 'N/A';
        document.getElementById('mlActions').textContent = data.ml_scaling_actions || '0';
        document.getElementById('mlDataPoints').textContent = data.training_data_points || '0';
        
        const tbody = document.getElementById('ml-analytics-tbody');
        if (data.predictions && data.predictions.length > 0) {
            tbody.innerHTML = '';
            data.predictions.forEach(pred => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${new Date(pred.timestamp).toLocaleString()}</td>
                    <td>${pred.application}</td>
                    <td>${pred.predicted_load ? pred.predicted_load.toFixed(1) + '%' : 'N/A'}</td>
                    <td>${pred.confidence ? pred.confidence.toFixed(1) + '%' : 'N/A'}</td>
                    <td>${pred.action_taken || 'None'}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5">No ML predictions available</td></tr>';
        }
    } catch (error) {
        document.getElementById('mlAccuracy').textContent = 'Error';
        document.getElementById('mlActions').textContent = 'Error';
        document.getElementById('mlDataPoints').textContent = 'Error';
    }
};

window.showCreateMLPolicyModal = function() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Create ML Predictive Scaling Policy</h3>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body">
                <form id="mlPolicyForm">
                    <div class="form-group">
                        <label>Application *</label>
                        <select id="mlApp" required>
                            <option value="">Select Application</option>
                        </select>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Prediction Horizon (minutes) *</label>
                            <input type="number" id="predictionHorizon" required min="5" max="120" value="30">
                        </div>
                        <div class="form-group">
                            <label>Confidence Threshold (%) *</label>
                            <input type="number" id="confidenceThreshold" required min="50" max="95" value="75">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Min Replicas *</label>
                            <input type="number" id="mlMinReplicas" required min="1" value="1">
                        </div>
                        <div class="form-group">
                            <label>Max Replicas *</label>
                            <input type="number" id="mlMaxReplicas" required min="1" value="10">
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="submitMLPolicy()">Create ML Policy</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Load applications
    fetch('/api/cluster.php?action=applications')
        .then(response => response.json())
        .then(apps => {
            const select = document.getElementById('mlApp');
            apps.forEach(app => {
                if (app.status === 'running') {
                    const option = document.createElement('option');
                    option.value = app.name;
                    option.textContent = app.name;
                    select.appendChild(option);
                }
            });
        });
};

window.submitMLPolicy = async function() {
    const policyData = {
        application: document.getElementById('mlApp').value,
        prediction_horizon: parseInt(document.getElementById('predictionHorizon').value),
        confidence_threshold: parseInt(document.getElementById('confidenceThreshold').value),
        min_replicas: parseInt(document.getElementById('mlMinReplicas').value),
        max_replicas: parseInt(document.getElementById('mlMaxReplicas').value)
    };
    
    if (!policyData.application) {
        alert('Please select an application');
        return;
    }
    
    try {
        const response = await fetch('/api/cluster.php?action=create_ml_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(policyData)
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`ML policy created for ${policyData.application}`);
            document.querySelector('.modal').remove();
            refreshMLSystemStatus();
        } else {
            alert(`Failed to create ML policy: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
};

window.showMultiHorizonPredictions = function() {
    alert('Multi-Horizon Predictions - Feature available');
};

window.showAnomalyDetection = function() {
    alert('Anomaly Detection - Feature available');
};

window.showPredictionService = function() {
    alert('Prediction Service - Feature available');
};

window.showModelWeightsConfig = function() {
    alert('Model Weights Config - Feature available');
};

window.showAutoRetrainingConfig = function() {
    alert('Auto-Retraining Config - Feature available');
};

window.showProactiveScalingConfig = function() {
    alert('Proactive Scaling Config - Feature available');
};

// Initialize ML data refresh on page load
document.addEventListener('DOMContentLoaded', function() {
    // Refresh ML data every 30 seconds
    setInterval(function() {
        if (currentTab === 'autoscaling') {
            refreshMLSystemStatus();
        }
    }, 30000);
});