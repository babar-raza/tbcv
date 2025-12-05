// file: tbcv/static/js/monitoring.js
/**
 * Performance Monitoring Dashboard JavaScript
 * Handles real-time updates, charts, and user interactions
 */

// Global state
let charts = {};
let autoRefreshInterval = null;
let currentTimeRange = '1h';
let alertThresholds = {
    throughput: 100,
    agentTime: 1000,
    dbTime: 500,
    cacheRate: 70,
    cpu: 80,
    memory: 85,
    errorRate: 5,
    cooldown: 15
};
let lastAlerts = {};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing monitoring dashboard...');
    initializeCharts();
    setupEventListeners();
    loadMetrics();
    startAutoRefresh();
    loadThresholds();
});

/**
 * Initialize Chart.js charts
 */
function initializeCharts() {
    // Common chart options
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        }
    };

    // Throughput Chart
    const throughputCtx = document.getElementById('throughput-chart').getContext('2d');
    charts.throughput = new Chart(throughputCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Validations per minute',
                data: [],
                borderColor: 'rgb(102, 126, 234)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Validations/min'
                    }
                }
            }
        }
    });

    // Response Time Chart
    const responseTimeCtx = document.getElementById('response-time-chart').getContext('2d');
    charts.responseTime = new Chart(responseTimeCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Agent Avg (ms)',
                    data: [],
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'DB Avg (ms)',
                    data: [],
                    borderColor: 'rgb(251, 191, 36)',
                    backgroundColor: 'rgba(251, 191, 36, 0.1)',
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Response Time (ms)'
                    }
                }
            }
        }
    });

    // System Resources Chart
    const systemResourcesCtx = document.getElementById('system-resources-chart').getContext('2d');
    charts.systemResources = new Chart(systemResourcesCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'CPU %',
                    data: [],
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Memory %',
                    data: [],
                    borderColor: 'rgb(168, 85, 247)',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Disk %',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Usage %'
                    }
                }
            }
        }
    });

    // Error Rate Chart
    const errorRateCtx = document.getElementById('error-rate-chart').getContext('2d');
    charts.errorRate = new Chart(errorRateCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Success Rate %',
                    data: [],
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: 'rgb(16, 185, 129)',
                    borderWidth: 1
                },
                {
                    label: 'Error Rate %',
                    data: [],
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderColor: 'rgb(239, 68, 68)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Percentage'
                    }
                }
            }
        }
    });

    console.log('Charts initialized');
}

/**
 * Setup event listeners for UI interactions
 */
function setupEventListeners() {
    // Time range selector
    document.querySelectorAll('.range-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentTimeRange = this.dataset.range;
            loadMetrics();
        });
    });

    // Auto-refresh toggle
    const autoRefreshCheckbox = document.getElementById('auto-refresh');
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
    }

    console.log('Event listeners setup complete');
}

/**
 * Load metrics from API
 */
async function loadMetrics() {
    try {
        updateConnectionStatus('loading');

        const response = await fetch(`/dashboard/monitoring/metrics?time_range=${currentTimeRange}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        updateDashboard(data);
        updateConnectionStatus('connected');
        updateLastUpdateTime();

    } catch (error) {
        console.error('Failed to load metrics:', error);
        updateConnectionStatus('error');
        showAlert('Failed to load metrics: ' + error.message, 'error');
    }
}

/**
 * Update dashboard with new metrics data
 */
function updateDashboard(data) {
    // Update stat cards
    updateStatCard('validation-throughput', data.validation_throughput.per_minute);
    updateStatCard('agent-performance', data.agent_performance.overall_avg_ms);
    updateStatCard('cache-hit-rate', data.cache.hit_rate + '%');
    updateStatCard('db-query-time', data.database_performance.overall_avg_ms);

    // Update system resources
    updateSystemResources(data.system_resources);

    // Update cache details
    updateCacheDetails(data.cache);

    // Update tables
    updateAgentMetricsTable(data.agent_performance.agent_metrics);
    updateDatabaseMetricsTable(data.database_performance.db_metrics);

    // Update charts
    updateCharts(data);

    // Check thresholds and trigger alerts
    checkThresholds(data);
}

/**
 * Update stat card value
 */
function updateStatCard(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = typeof value === 'number' ? value.toFixed(2) : value;
    }
}

/**
 * Update system resources section
 */
function updateSystemResources(resources) {
    // CPU
    updateResourceBar('cpu', resources.cpu_percent);

    // Memory
    updateResourceBar('memory', resources.memory_percent);

    // Disk
    updateResourceBar('disk', resources.disk_percent);

    // Active connections (simulated for now)
    const connections = document.getElementById('active-connections');
    if (connections) {
        connections.textContent = resources.active_threads || '--';
    }
}

/**
 * Update resource progress bar
 */
function updateResourceBar(resource, percent) {
    const valueElement = document.getElementById(`${resource}-usage`);
    const progressElement = document.getElementById(`${resource}-progress`);

    if (valueElement) {
        valueElement.textContent = `${percent.toFixed(1)}%`;
    }

    if (progressElement) {
        progressElement.style.width = `${percent}%`;

        // Color based on threshold
        if (percent > 85) {
            progressElement.style.backgroundColor = '#ef4444';
        } else if (percent > 70) {
            progressElement.style.backgroundColor = '#f59e0b';
        } else {
            progressElement.style.backgroundColor = '#10b981';
        }
    }
}

/**
 * Update cache details
 */
function updateCacheDetails(cache) {
    updateElement('cache-hit-rate-detail', cache.hit_rate + '%');
    updateElement('cache-total-hits', cache.total_hits);
    updateElement('cache-total-misses', cache.total_misses);
    updateElement('cache-size', cache.cache_size);
}

/**
 * Update agent metrics table
 */
function updateAgentMetricsTable(metrics) {
    const tbody = document.getElementById('agent-metrics-body');
    if (!tbody) return;

    if (Object.keys(metrics).length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty">No agent metrics available</td></tr>';
        return;
    }

    let html = '';
    for (const [agent, data] of Object.entries(metrics)) {
        const successRate = 95 + Math.random() * 5; // Simulated for now
        html += `
            <tr>
                <td>${agent}</td>
                <td>${data.count}</td>
                <td>${data.avg_duration_ms.toFixed(2)}</td>
                <td>${data.min_duration_ms.toFixed(2)}</td>
                <td>${data.max_duration_ms.toFixed(2)}</td>
                <td>${data.p95_duration_ms.toFixed(2)}</td>
                <td>${data.p99_duration_ms.toFixed(2)}</td>
                <td>${successRate.toFixed(1)}%</td>
            </tr>
        `;
    }
    tbody.innerHTML = html;
}

/**
 * Update database metrics table
 */
function updateDatabaseMetricsTable(metrics) {
    const tbody = document.getElementById('db-metrics-body');
    if (!tbody) return;

    if (Object.keys(metrics).length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty">No database metrics available</td></tr>';
        return;
    }

    let html = '';
    for (const [operation, data] of Object.entries(metrics)) {
        html += `
            <tr>
                <td>${operation}</td>
                <td>${data.count}</td>
                <td>${data.avg_duration_ms.toFixed(2)}</td>
                <td>${data.min_duration_ms.toFixed(2)}</td>
                <td>${data.max_duration_ms.toFixed(2)}</td>
                <td>${data.p95_duration_ms.toFixed(2)}</td>
                <td>${data.p99_duration_ms.toFixed(2)}</td>
            </tr>
        `;
    }
    tbody.innerHTML = html;
}

/**
 * Update all charts with new data
 */
function updateCharts(data) {
    const timestamp = new Date().toLocaleTimeString();

    // Update throughput chart
    addChartData(charts.throughput, timestamp, [data.validation_throughput.per_minute]);

    // Update response time chart
    addChartData(charts.responseTime, timestamp, [
        data.agent_performance.overall_avg_ms,
        data.database_performance.overall_avg_ms
    ]);

    // Update system resources chart
    addChartData(charts.systemResources, timestamp, [
        data.system_resources.cpu_percent,
        data.system_resources.memory_percent,
        data.system_resources.disk_percent
    ]);

    // Update error rate chart
    addChartData(charts.errorRate, timestamp, [
        data.validation_throughput.success_rate,
        100 - data.validation_throughput.success_rate
    ]);
}

/**
 * Add data point to chart
 */
function addChartData(chart, label, values) {
    chart.data.labels.push(label);

    values.forEach((value, index) => {
        chart.data.datasets[index].data.push(value);
    });

    // Keep only last 20 data points
    if (chart.data.labels.length > 20) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }

    chart.update('none'); // Update without animation for performance
}

/**
 * Check thresholds and trigger alerts
 */
function checkThresholds(data) {
    const now = Date.now();

    // Check validation throughput
    if (data.validation_throughput.per_minute < alertThresholds.throughput) {
        triggerAlert('throughput',
            `Validation throughput (${data.validation_throughput.per_minute.toFixed(2)}/min) below threshold (${alertThresholds.throughput}/min)`,
            'warning', now);
    }

    // Check agent performance
    if (data.agent_performance.overall_avg_ms > alertThresholds.agentTime) {
        triggerAlert('agent',
            `Agent response time (${data.agent_performance.overall_avg_ms.toFixed(2)}ms) above threshold (${alertThresholds.agentTime}ms)`,
            'warning', now);
    }

    // Check database performance
    if (data.database_performance.overall_avg_ms > alertThresholds.dbTime) {
        triggerAlert('database',
            `Database query time (${data.database_performance.overall_avg_ms.toFixed(2)}ms) above threshold (${alertThresholds.dbTime}ms)`,
            'warning', now);
    }

    // Check cache hit rate
    if (data.cache.hit_rate < alertThresholds.cacheRate) {
        triggerAlert('cache',
            `Cache hit rate (${data.cache.hit_rate.toFixed(2)}%) below threshold (${alertThresholds.cacheRate}%)`,
            'warning', now);
    }

    // Check CPU usage
    if (data.system_resources.cpu_percent > alertThresholds.cpu) {
        triggerAlert('cpu',
            `CPU usage (${data.system_resources.cpu_percent.toFixed(2)}%) above threshold (${alertThresholds.cpu}%)`,
            'error', now);
    }

    // Check memory usage
    if (data.system_resources.memory_percent > alertThresholds.memory) {
        triggerAlert('memory',
            `Memory usage (${data.system_resources.memory_percent.toFixed(2)}%) above threshold (${alertThresholds.memory}%)`,
            'error', now);
    }
}

/**
 * Trigger an alert with cooldown
 */
function triggerAlert(key, message, level, now) {
    const cooldownMs = alertThresholds.cooldown * 60 * 1000;

    if (!lastAlerts[key] || (now - lastAlerts[key]) > cooldownMs) {
        lastAlerts[key] = now;
        showAlert(message, level);
        addAlertToLog(message, level, new Date(now));
    }
}

/**
 * Show alert banner
 */
function showAlert(message, level = 'info') {
    const banner = document.getElementById('alert-banner');
    const messageElement = document.getElementById('alert-message');

    if (banner && messageElement) {
        messageElement.textContent = message;
        banner.className = `alert-banner alert-${level}`;
        banner.style.display = 'flex';
    }
}

/**
 * Close alert banner
 */
function closeAlert() {
    const banner = document.getElementById('alert-banner');
    if (banner) {
        banner.style.display = 'none';
    }
}

/**
 * Add alert to log
 */
function addAlertToLog(message, level, timestamp) {
    const alertsList = document.getElementById('alerts-list');
    if (!alertsList) return;

    // Remove empty state if present
    const emptyState = alertsList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }

    const alertItem = document.createElement('div');
    alertItem.className = `alert-item alert-${level}`;
    alertItem.innerHTML = `
        <span class="alert-time">${timestamp.toLocaleString()}</span>
        <span class="alert-text">${message}</span>
    `;

    alertsList.insertBefore(alertItem, alertsList.firstChild);

    // Keep only last 50 alerts
    while (alertsList.children.length > 50) {
        alertsList.removeChild(alertsList.lastChild);
    }
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(status) {
    const dot = document.getElementById('connection-status');
    const text = document.getElementById('connection-text');

    if (!dot || !text) return;

    switch (status) {
        case 'connected':
            dot.className = 'status-dot connected';
            text.textContent = 'Connected';
            break;
        case 'loading':
            dot.className = 'status-dot loading';
            text.textContent = 'Loading...';
            break;
        case 'error':
            dot.className = 'status-dot error';
            text.textContent = 'Connection Error';
            break;
    }
}

/**
 * Update last update time
 */
function updateLastUpdateTime() {
    const element = document.getElementById('last-update-time');
    if (element) {
        element.textContent = new Date().toLocaleTimeString();
    }
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
    stopAutoRefresh(); // Clear any existing interval
    autoRefreshInterval = setInterval(() => {
        loadMetrics();
    }, 5000); // Refresh every 5 seconds
    console.log('Auto-refresh started');
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        console.log('Auto-refresh stopped');
    }
}

/**
 * Refresh all metrics
 */
function refreshAllMetrics() {
    loadMetrics();
}

/**
 * Refresh specific chart
 */
function refreshChart(chartName) {
    console.log(`Refreshing ${chartName} chart`);
    loadMetrics();
}

/**
 * Export data
 */
async function exportData(format) {
    try {
        const response = await fetch(`/dashboard/monitoring/export?format=${format}&time_range=${currentTimeRange}`);

        if (!response.ok) {
            throw new Error(`Export failed: ${response.status}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `monitoring_export_${currentTimeRange}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showAlert(`Data exported successfully as ${format.toUpperCase()}`, 'success');
    } catch (error) {
        console.error('Export failed:', error);
        showAlert('Export failed: ' + error.message, 'error');
    }
}

/**
 * Save alert thresholds
 */
function saveThresholds() {
    alertThresholds.throughput = parseFloat(document.getElementById('threshold-throughput').value) || 100;
    alertThresholds.agentTime = parseFloat(document.getElementById('threshold-agent-time').value) || 1000;
    alertThresholds.dbTime = parseFloat(document.getElementById('threshold-db-time').value) || 500;
    alertThresholds.cacheRate = parseFloat(document.getElementById('threshold-cache-rate').value) || 70;
    alertThresholds.cpu = parseFloat(document.getElementById('threshold-cpu').value) || 80;
    alertThresholds.memory = parseFloat(document.getElementById('threshold-memory').value) || 85;
    alertThresholds.errorRate = parseFloat(document.getElementById('threshold-error-rate').value) || 5;
    alertThresholds.cooldown = parseFloat(document.getElementById('alert-cooldown').value) || 15;

    // Save to localStorage
    localStorage.setItem('monitoring_thresholds', JSON.stringify(alertThresholds));

    showAlert('Threshold configuration saved successfully', 'success');
}

/**
 * Load thresholds from localStorage
 */
function loadThresholds() {
    const saved = localStorage.getItem('monitoring_thresholds');
    if (saved) {
        try {
            alertThresholds = JSON.parse(saved);

            // Update input fields
            document.getElementById('threshold-throughput').value = alertThresholds.throughput;
            document.getElementById('threshold-agent-time').value = alertThresholds.agentTime;
            document.getElementById('threshold-db-time').value = alertThresholds.dbTime;
            document.getElementById('threshold-cache-rate').value = alertThresholds.cacheRate;
            document.getElementById('threshold-cpu').value = alertThresholds.cpu;
            document.getElementById('threshold-memory').value = alertThresholds.memory;
            document.getElementById('threshold-error-rate').value = alertThresholds.errorRate;
            document.getElementById('alert-cooldown').value = alertThresholds.cooldown;
        } catch (error) {
            console.error('Failed to load saved thresholds:', error);
        }
    }
}

/**
 * Clear all alerts
 */
function clearAlerts() {
    const alertsList = document.getElementById('alerts-list');
    if (alertsList) {
        alertsList.innerHTML = '<div class="empty-state"><p>No recent alerts</p></div>';
    }
    lastAlerts = {};
}

/**
 * Helper function to update element text
 */
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}
