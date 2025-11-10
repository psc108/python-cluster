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
        
        // Mock application summary
        document.getElementById('running-apps').textContent = '2';
        document.getElementById('total-instances').textContent = '5';
        document.getElementById('failed-apps').textContent = '0';
        
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
            row.innerHTML = `
                <td>${app.name}</td>
                <td><span class="status-badge status-${app.status}">${app.status}</span></td>
                <td>${app.replicas}</td>
                <td>${app.version}</td>
                <td>${app.cpu_percent}%</td>
                <td>${app.memory_mb} MB</td>
                <td>
                    <button class="btn btn-small btn-secondary" onclick="scaleApplication('${app.name}')">Scale</button>
                    <button class="btn btn-small btn-danger" onclick="stopApplication('${app.name}')">Stop</button>
                </td>
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
        
        // Update chart (simplified - in real implementation, use Chart.js or similar)
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
    // Simple error display - in real implementation, use a proper notification system
    console.error(message);
    alert(message);
}

// Application management functions
function scaleApplication(appName) {
    const replicas = prompt(`Enter new replica count for ${appName}:`, '3');
    if (replicas && !isNaN(replicas)) {
        console.log(`Scaling ${appName} to ${replicas} replicas`);
        // In real implementation, make API call to scale application
        alert(`Scaling ${appName} to ${replicas} replicas (demo)`);
    }
}

function stopApplication(appName) {
    if (confirm(`Are you sure you want to stop ${appName}?`)) {
        console.log(`Stopping application: ${appName}`);
        // In real implementation, make API call to stop application
        alert(`Stopping ${appName} (demo)`);
    }
}

function viewNodeDetails(nodeId) {
    console.log(`Viewing details for Node ${nodeId}`);
    // In real implementation, show detailed node information
    alert(`Node ${nodeId} details (demo)`);
}

function showDeployForm() {
    console.log('Showing deploy form');
    // In real implementation, show application deployment form
    alert('Deploy application form (demo)');
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});