const socket = io();

let currentScenario = null;
let monitoringActive = false;
let performanceChart = null;
let cpuMemoryChart = null;
let networkChart = null;
let attackTemplates = {};
let defenseTemplates = {};

document.addEventListener('DOMContentLoaded', () => {
    try {
        hideLoadingOverlay();
    } catch (e) {
        console.error('Error hiding loading overlay:', e);
    }
    
    try {
        initializeTabs();
    } catch (e) {
        console.error('Error initializing tabs:', e);
    }
    
    try {
        initializeCharts();
    } catch (e) {
        console.error('Error initializing charts:', e);
    }
    
    try {
        initializeWebSocket();
    } catch (e) {
        console.error('Error initializing websocket:', e);
    }
    
    try {
        loadConfig();
    } catch (e) {
        console.error('Error loading config:', e);
    }
    
    try {
        updateTime();
        setInterval(updateTime, 1000);
    } catch (e) {
        console.error('Error setting up time:', e);
    }
    
    try {
        initializeKeyboardNavigation();
    } catch (e) {
        console.error('Error initializing keyboard navigation:', e);
    }
    
    console.log('Dashboard initialization complete');
});

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        setTimeout(() => {
            overlay.classList.add('hidden');
            document.body.classList.add('fade-in');
        }, 500);
    }
}

function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        const messageEl = overlay.querySelector('p');
        if (messageEl) messageEl.textContent = message;
        overlay.classList.remove('hidden');
    }
}

function initializeKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });

    document.addEventListener('mousedown', () => {
        document.body.classList.remove('keyboard-navigation');
    });
}

function createGradient(ctx, color) {
    if (!ctx) return color + '40';
    const context = ctx.getContext('2d');
    if (!context) return color + '40';
    const gradient = context.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, color + '80');
    gradient.addColorStop(1, color + '00');
    return gradient;
}

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;
            
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            if (targetTab === 'topology') {
                drawTopology();
            } else if (targetTab === 'scenarios') {
                loadScenarios();
            }
        });
    });
}

function initializeCharts() {
    try {
        const ctxPerf = document.getElementById('performance-chart');
        if (ctxPerf) {
            const gradientCpu = createGradient(ctxPerf, '#ef4444');
            const gradientMemory = createGradient(ctxPerf, '#f59e0b');
            const gradientConn = createGradient(ctxPerf, '#2563eb');
            
            performanceChart = new Chart(ctxPerf, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU %',
                        data: [],
                        borderColor: '#ef4444',
                        backgroundColor: gradientCpu,
                        tension: 0.4,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    }, {
                        label: 'Memory %',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: gradientMemory,
                        tension: 0.4,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    }, {
                        label: 'Connections',
                        data: [],
                        borderColor: '#2563eb',
                        backgroundColor: gradientConn,
                        tension: 0.4,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    animation: {
                        duration: 750,
                        easing: 'easeInOutQuart'
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                color: '#94a3b8',
                                usePointStyle: true,
                                padding: 15
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(30, 41, 59, 0.95)',
                            titleColor: '#f1f5f9',
                            bodyColor: '#f1f5f9',
                            borderColor: '#334155',
                            borderWidth: 1,
                            padding: 12,
                            cornerRadius: 6,
                            displayColors: true
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: '#94a3b8',
                                maxRotation: 0,
                                autoSkip: true,
                                maxTicksLimit: 10
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            min: 0,
                            max: 100,
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            min: 0,
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                drawOnChartArea: false,
                            }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Error initializing performance chart:', e);
    }

    try {
        const ctxCpuMem = document.getElementById('cpu-memory-chart');
        if (ctxCpuMem) {
            cpuMemoryChart = new Chart(ctxCpuMem, {
                type: 'bar',
                data: {
                    labels: ['CPU', 'Memory', 'Disk'],
                    datasets: [{
                        label: 'Usage %',
                        data: [0, 0, 0],
                        backgroundColor: [
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        borderColor: [
                            '#ef4444',
                            '#f59e0b',
                            '#10b981'
                        ],
                        borderWidth: 2,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1000,
                        easing: 'easeOutBounce'
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(30, 41, 59, 0.95)',
                            titleColor: '#f1f5f9',
                            bodyColor: '#f1f5f9',
                            borderColor: '#334155',
                            borderWidth: 1,
                            padding: 12,
                            cornerRadius: 6
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Error initializing CPU/Memory chart:', e);
    }

    try {
        const ctxNetwork = document.getElementById('network-chart');
        if (ctxNetwork) {
            const gradientSent = createGradient(ctxNetwork, '#10b981');
            const gradientRecv = createGradient(ctxNetwork, '#2563eb');
            
            networkChart = new Chart(ctxNetwork, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Packets Sent',
                        data: [],
                        borderColor: '#10b981',
                        backgroundColor: gradientSent,
                        tension: 0.4,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    }, {
                        label: 'Packets Received',
                        data: [],
                        borderColor: '#2563eb',
                        backgroundColor: gradientRecv,
                        tension: 0.4,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 750,
                        easing: 'easeInOutQuart'
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                color: '#94a3b8',
                                usePointStyle: true,
                                padding: 15
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(30, 41, 59, 0.95)',
                            titleColor: '#f1f5f9',
                            bodyColor: '#f1f5f9',
                            borderColor: '#334155',
                            borderWidth: 1,
                            padding: 12,
                            cornerRadius: 6,
                            displayColors: true
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: '#94a3b8',
                                maxRotation: 0,
                                autoSkip: true,
                                maxTicksLimit: 10
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Error initializing network chart:', e);
    }
}

function initializeWebSocket() {
    socket.on('connect', () => {
        console.log('Connected to server');
        updateConnectionStatus(true);
        fetchStatus();
        setInterval(fetchStatus, 2000);
        setInterval(updateMetricsDisplay, 1000);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });

    socket.on('metrics_update', (data) => {
        if (data && data.metrics) {
            updateMetrics(data.metrics);
        }
    });

    socket.on('anomaly_detected', (data) => {
        showNotification('Anomaly detected!', 'warning');
        addAlert('Anomaly detected in system metrics', 'warning');
    });

    socket.on('status_update', (data) => {
        if (data && data.system) {
            updateSystemStatus(data.system);
        }
    });
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (connected) {
        statusEl.classList.add('connected');
        statusEl.querySelector('span').textContent = 'Connected';
    } else {
        statusEl.classList.remove('connected');
        statusEl.querySelector('span').textContent = 'Disconnected';
    }
}

function updateTime() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timeStr = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    document.getElementById('current-time').textContent = timeStr;
}

async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        attackTemplates = config.attack_types;
        defenseTemplates = config.defense_types;
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) {
            console.error('API response not OK:', response.status);
            return;
        }
        const data = await response.json();
        
        if (data.system) {
            updateSystemStatus(data.system);
        }
        if (data.monitoring) {
            updateMetrics(data.monitoring);
        }
        
        const activeTab = document.querySelector('.tab-btn.active')?.dataset.tab;
        if (activeTab === 'topology') {
            drawTopology();
        }
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

function updateMetricsDisplay() {
    fetch('/api/status')
        .then(res => res.json())
        .then(data => {
            if (data.monitoring) {
                updateMetrics(data.monitoring);
            }
        })
        .catch(err => console.error('Error updating metrics:', err));
}

function updateSystemStatus(status) {
    if (!status) return;
    
    const getStatusDisplay = (statusValue) => {
        if (!statusValue || statusValue === 'unknown' || statusValue === 'Unknown') {
            return { text: 'Unknown', class: 'status-unknown', icon: 'fa-question-circle' };
        }
        if (statusValue === 'running' || statusValue === 'active' || statusValue === 'online') {
            return { text: 'Running', class: 'status-online', icon: 'fa-check-circle' };
        }
        if (statusValue === 'stopped' || statusValue === 'inactive' || statusValue === 'offline') {
            return { text: 'Stopped', class: 'status-offline', icon: 'fa-times-circle' };
        }
        return { text: statusValue, class: 'status-unknown', icon: 'fa-question-circle' };
    };
    
    const updateStatusElement = (elementId, statusValue) => {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const display = getStatusDisplay(statusValue);
        element.innerHTML = `<i class="fas ${display.icon}"></i> <span>${display.text}</span>`;
        element.className = `status-value ${display.class}`;
    };
    
    updateStatusElement('cn5g-status', status.cn5g);
    updateStatusElement('gnb-status', status.gnb);
    updateStatusElement('ue-status', status.ue);
    
    const nsElement = document.getElementById('ns-status');
    if (nsElement) {
        const nsCount = status.namespaces?.length || 0;
        nsElement.textContent = nsCount;
        nsElement.className = nsCount > 0 ? 'status-value status-online' : 'status-value status-offline';
    }
}

function updateMetrics(metrics) {
    if (!metrics) return;
    
    const system = metrics.system || {};
    const network = metrics.network || {};
    const f1 = metrics.f1_interface || {};
    
    document.getElementById('cpu-value').textContent = `${system.cpu_percent?.toFixed(1) || 0}%`;
    document.getElementById('memory-value').textContent = `${system.memory_percent?.toFixed(1) || 0}%`;
    document.getElementById('network-value').textContent = network.connections || 0;
    document.getElementById('latency-value').textContent = `${f1.latency_ms || 0}ms`;
    
    updatePerformanceChart(metrics);
    updateResourceCharts(system, network);
}

function updatePerformanceChart(metrics) {
    const timestamp = new Date().toLocaleTimeString();
    const system = metrics.system || {};
    const network = metrics.network || {};
    
    const maxDataPoints = 30;
    
    if (performanceChart.data.labels.length >= maxDataPoints) {
        performanceChart.data.labels.shift();
        performanceChart.data.datasets.forEach(dataset => dataset.data.shift());
    }
    
    performanceChart.data.labels.push(timestamp);
    performanceChart.data.datasets[0].data.push(system.cpu_percent || 0);
    performanceChart.data.datasets[1].data.push(system.memory_percent || 0);
    performanceChart.data.datasets[2].data.push(network.connections || 0);
    
    performanceChart.update({
        duration: 0,
        lazy: true
    });
}

function updateResourceCharts(system, network) {
    cpuMemoryChart.data.datasets[0].data = [
        system.cpu_percent || 0,
        system.memory_percent || 0,
        system.disk_percent || 0
    ];
    cpuMemoryChart.update('none');
    
    const timestamp = new Date().toLocaleTimeString();
    if (networkChart.data.labels.length > 30) {
        networkChart.data.labels.shift();
        networkChart.data.datasets.forEach(dataset => dataset.data.shift());
    }
    
    networkChart.data.labels.push(timestamp);
    networkChart.data.datasets[0].data.push(network.packets_sent || 0);
    networkChart.data.datasets[1].data.push(network.packets_recv || 0);
    networkChart.update('none');
}

async function systemAction(action) {
    try {
        showNotification(`${action}ing system...`, 'info');
        
        const response = await fetch(`/api/system/${action}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(data.message, 'success');
        } else {
            showNotification(data.message || 'Action failed', 'error');
        }
        
        setTimeout(fetchStatus, 1000);
    } catch (error) {
        showNotification('System action failed: ' + error.message, 'error');
    }
}

function toggleConnectivityResults() {
    const content = document.getElementById('connectivity-content');
    const icon = document.getElementById('connectivity-toggle-icon');
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    }
}

async function testConnectivity() {
    try {
        showNotification('Testing connectivity between UEs...', 'info');
        document.getElementById('connectivity-results').style.display = 'block';
        document.getElementById('connectivity-content').style.display = 'block';
        document.getElementById('connectivity-toggle-icon').classList.remove('fa-chevron-down');
        document.getElementById('connectivity-toggle-icon').classList.add('fa-chevron-up');
        document.getElementById('connectivity-summary').innerHTML = '<p>Testing in progress...</p>';
        document.getElementById('connectivity-details').innerHTML = '';
        
        const response = await fetch('/api/test/connectivity', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success && data.results) {
            const summary = data.summary;
            
            document.getElementById('connectivity-summary').innerHTML = `
                <h4>Summary</h4>
                <p><strong>Total Tests:</strong> ${summary.total}</p>
                <p><strong>Successful:</strong> <span style="color: #10b981;">${summary.successful}</span></p>
                <p><strong>Failed:</strong> <span style="color: #ef4444;">${summary.failed}</span></p>
                <p><strong>Success Rate:</strong> ${summary.success_rate}</p>
            `;
            
            let tableHTML = `
                <table class="metrics-table">
                    <thead>
                        <tr>
                            <th>From</th>
                            <th>To</th>
                            <th>Target IP</th>
                            <th>Status</th>
                            <th>Packet Loss</th>
                            <th>Avg RTT</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.results.forEach(result => {
                const statusColor = result.success ? '#10b981' : '#ef4444';
                const statusText = result.success ? '✓ Success' : '✗ Failed';
                
                tableHTML += `
                    <tr>
                        <td>${result.from_ue}</td>
                        <td>${result.to_ue}</td>
                        <td>${result.target_ip}</td>
                        <td style="color: ${statusColor}; font-weight: bold;">${statusText}</td>
                        <td>${result.packet_loss}</td>
                        <td>${result.avg_rtt}</td>
                        <td style="font-size: 12px;">${result.details}</td>
                    </tr>
                `;
            });
            
            tableHTML += `
                    </tbody>
                </table>
            `;
            
            document.getElementById('connectivity-details').innerHTML = tableHTML;
            
            if (summary.failed === 0) {
                showNotification('All connectivity tests passed!', 'success');
            } else {
                showNotification(`Connectivity tests completed: ${summary.failed} failed`, 'warning');
            }
        } else {
            showNotification(data.error || 'Connectivity test failed', 'error');
            document.getElementById('connectivity-summary').innerHTML = `<p class="no-data">Test failed: ${data.error}</p>`;
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
        document.getElementById('connectivity-summary').innerHTML = `<p class="no-data">Error: ${error.message}</p>`;
    }
}

async function setupNamespaces() {
    try {
        const response = await fetch('/api/system/setup_namespaces', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Network namespaces created successfully', 'success');
            drawTopology();
        } else {
            showNotification(data.message || 'Failed to create namespaces', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function cleanupNamespaces() {
    try {
        const response = await fetch('/api/system/cleanup_namespaces', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Namespaces cleaned up', 'success');
            drawTopology();
        } else {
            showNotification(data.message || 'Cleanup failed', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function updateAttackParams() {
    const attackType = document.getElementById('attack-type').value;
    const container = document.getElementById('attack-params-container');
    
    if (!attackType) {
        container.innerHTML = '';
        updateAttackCommand();
        return;
    }
    
    let paramsHTML = '';
    
    if (attackType.includes('ue') || attackType.includes('bearer')) {
        paramsHTML += `
            <div class="form-group">
                <label>UE/Bearer Count:</label>
                <input type="number" class="form-control" id="param-count" value="1000" min="1">
            </div>
        `;
    }
    
    if (attackType.includes('flood')) {
        paramsHTML += `
            <div class="form-group">
                <label>Packet Size (bytes):</label>
                <input type="number" class="form-control" id="param-packet-size" value="1024" min="64">
            </div>
        `;
    }
    
    paramsHTML += `
        <div class="form-group">
            <label>Rate (packets/sec):</label>
            <input type="number" class="form-control" id="param-rate" value="100" min="1">
        </div>
        <div class="form-group">
            <label>Duration (seconds):</label>
            <input type="number" class="form-control" id="param-duration" value="60" min="1">
        </div>
    `;
    
    container.innerHTML = paramsHTML;
    updateAttackCommand();
}

function updateAttackCommand() {
    const attackType = document.getElementById('attack-type').value;
    const target = document.getElementById('attack-target').value;
    const mode = document.getElementById('attack-mode').value;
    
    if (!attackType) {
        document.getElementById('attack-command-preview').textContent = 
            'Select attack type to generate command...';
        return;
    }
    
    let command = `sudo python3 /home/sp5g/sp5g/add-on/attack/`;
    
    if (attackType.includes('f1c') || attackType.includes('ue') || attackType.includes('bearer') || attackType.includes('handover')) {
        command += `f1c/f1c_attack.py`;
    } else if (attackType.includes('flood') || attackType.includes('gtp')) {
        command += `f1u/f1u_attack.py`;
    } else if (attackType === 'distributed_ddos') {
        command += `botnet/botnet_controller.py`;
    } else {
        command += `generic_attack.py`;
    }
    
    command += ` --type ${attackType} --target ${target} --mode ${mode}`;
    
    const rate = document.getElementById('param-rate')?.value;
    const duration = document.getElementById('param-duration')?.value;
    
    if (rate) command += ` --rate ${rate}`;
    if (duration) command += ` --duration ${duration}`;
    
    document.getElementById('attack-command-preview').textContent = command;
}

async function launchAttack() {
    const attackType = document.getElementById('attack-type').value;
    const target = document.getElementById('attack-target').value;
    const mode = document.getElementById('attack-mode').value;
    
    if (!attackType) {
        showNotification('Please select an attack type', 'warning');
        return;
    }
    
    const params = {
        rate: parseInt(document.getElementById('param-rate')?.value || 100),
        duration: parseInt(document.getElementById('param-duration')?.value || 60)
    };
    
    const countEl = document.getElementById('param-count');
    if (countEl) params.ue_count = parseInt(countEl.value);
    
    const packetSizeEl = document.getElementById('param-packet-size');
    if (packetSizeEl) params.packet_size = parseInt(packetSizeEl.value);
    
    try {
        const response = await fetch('/api/attack/launch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: attackType,
                target: target,
                params: params,
                mode: mode
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Attack launched successfully', 'success');
            document.getElementById('attack-status').innerHTML = `
                <p><strong>Type:</strong> ${attackType}</p>
                <p><strong>Target:</strong> ${target}</p>
                <p><strong>Status:</strong> <span style="color: #ef4444;">RUNNING</span></p>
            `;
        } else {
            showNotification(data.message || 'Attack launch failed', 'error');
        }
    } catch (error) {
        showNotification('Error launching attack: ' + error.message, 'error');
    }
}

async function stopAttack() {
    try {
        const response = await fetch('/api/attack/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Attack stopped', 'success');
            document.getElementById('attack-status').innerHTML = '<p class="no-data">No attack running</p>';
        } else {
            showNotification(data.message || 'Failed to stop attack', 'warning');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function updateDefenseCategory() {
    const category = document.getElementById('defense-category').value;
    const defenseTypeSelect = document.getElementById('defense-type');
    
    if (!category) {
        defenseTypeSelect.innerHTML = '<option value="">-- Select Category First --</option>';
        defenseTypeSelect.disabled = true;
        document.getElementById('defense-params-container').innerHTML = '';
        updateDefenseCommand();
        return;
    }
    
    defenseTypeSelect.disabled = false;
    let optionsHTML = '<option value="">-- Select Defense Type --</option>';
    
    if (category === 'detection') {
        optionsHTML += `
            <option value="threshold_based">Threshold-based Detection</option>
            <option value="statistical_analysis">Statistical Analysis</option>
            <option value="pattern_recognition">Pattern Recognition</option>
        `;
    } else if (category === 'mitigation') {
        optionsHTML += `
            <option value="ip_filtering">IP Filtering</option>
            <option value="rate_limiting">Rate Limiting</option>
            <option value="dynamic_throttling">Dynamic Throttling</option>
            <option value="du_reconnection">DU Reconnection</option>
            <option value="ip_reassignment">IP Reassignment</option>
        `;
    }
    
    defenseTypeSelect.innerHTML = optionsHTML;
    document.getElementById('defense-params-container').innerHTML = '';
    updateDefenseCommand();
}

function updateDefenseParams() {
    const defenseType = document.getElementById('defense-type').value;
    const container = document.getElementById('defense-params-container');
    
    if (!defenseType) {
        container.innerHTML = '';
        updateDefenseCommand();
        return;
    }
    
    let paramsHTML = '';
    
    if (defenseType === 'threshold_based') {
        paramsHTML += `
            <div class="form-group">
                <label>CPU Threshold (%):</label>
                <input type="number" class="form-control" id="defense-cpu-threshold" value="80" min="0" max="100">
            </div>
            <div class="form-group">
                <label>Memory Threshold (%):</label>
                <input type="number" class="form-control" id="defense-memory-threshold" value="85" min="0" max="100">
            </div>
            <div class="form-group">
                <label>Packet Rate Threshold:</label>
                <input type="number" class="form-control" id="defense-packet-threshold" value="10000" min="0">
            </div>
        `;
    } else if (defenseType === 'statistical_analysis' || defenseType === 'pattern_recognition') {
        paramsHTML += `
            <div class="form-group">
                <label>Analysis Window (seconds):</label>
                <input type="number" class="form-control" id="defense-window" value="60" min="10">
            </div>
            <div class="form-group">
                <label>Sensitivity:</label>
                <select class="form-control" id="defense-sensitivity">
                    <option value="low">Low</option>
                    <option value="medium" selected>Medium</option>
                    <option value="high">High</option>
                </select>
            </div>
        `;
    } else if (defenseType === 'rate_limiting') {
        paramsHTML += `
            <div class="form-group">
                <label>Rate Limit (packets/sec):</label>
                <input type="number" class="form-control" id="defense-rate-limit" value="100" min="1">
            </div>
            <div class="form-group">
                <label>Port:</label>
                <input type="number" class="form-control" id="defense-port" value="38472" min="1">
            </div>
        `;
    } else if (defenseType === 'ip_filtering') {
        paramsHTML += `
            <div class="form-group">
                <label>Blocked IPs (comma-separated):</label>
                <input type="text" class="form-control" id="defense-blocked-ips" placeholder="192.168.1.1,192.168.1.2">
            </div>
        `;
    } else if (defenseType === 'dynamic_throttling') {
        paramsHTML += `
            <div class="form-group">
                <label>Initial Rate (packets/sec):</label>
                <input type="number" class="form-control" id="defense-initial-rate" value="1000" min="1">
            </div>
            <div class="form-group">
                <label>Throttle Factor:</label>
                <input type="number" class="form-control" id="defense-throttle-factor" value="0.5" min="0.1" max="1" step="0.1">
            </div>
        `;
    }
    
    container.innerHTML = paramsHTML;
    updateDefenseCommand();
}

function updateDefenseCommand() {
    const defenseType = document.getElementById('defense-type').value;
    
    if (!defenseType) {
        document.getElementById('defense-command-preview').textContent = 
            'Select defense type to generate command...';
        return;
    }
    
    let command = `sudo python3 /home/sp5g/sp5g/add-on/defense/`;
    
    if (defenseType === 'threshold_based') {
        command += `detector.py --type threshold`;
    } else if (defenseType === 'statistical_analysis') {
        command += `detector.py --type statistical`;
    } else if (defenseType === 'pattern_recognition') {
        command += `ml_detector.py --type pattern`;
    } else if (defenseType === 'rate_limiting') {
        command += `rate_limiter.py`;
    } else if (defenseType === 'ip_filtering') {
        command += `filter.py --type ip`;
    } else if (defenseType === 'dynamic_throttling') {
        command += `rate_limiter.py --dynamic`;
    } else if (defenseType === 'du_reconnection') {
        command += `advanced_defense.py --type du_reconnect`;
    } else if (defenseType === 'ip_reassignment') {
        command += `advanced_defense.py --type ip_rotation`;
    } else {
        command += `generic_defense.py --type ${defenseType}`;
    }
    
    document.getElementById('defense-command-preview').textContent = command;
}

async function enableDefense() {
    const defenseType = document.getElementById('defense-type').value;
    
    if (!defenseType) {
        showNotification('Please select a defense type', 'warning');
        return;
    }
    
    const params = {};
    
    if (defenseType === 'threshold_based') {
        params.cpu_threshold = parseInt(document.getElementById('defense-cpu-threshold')?.value || 80);
        params.memory_threshold = parseInt(document.getElementById('defense-memory-threshold')?.value || 85);
        params.packet_threshold = parseInt(document.getElementById('defense-packet-threshold')?.value || 10000);
    } else if (defenseType === 'statistical_analysis' || defenseType === 'pattern_recognition') {
        params.window = parseInt(document.getElementById('defense-window')?.value || 60);
        params.sensitivity = document.getElementById('defense-sensitivity')?.value || 'medium';
    } else if (defenseType === 'rate_limiting') {
        params.rate = parseInt(document.getElementById('defense-rate-limit')?.value || 100);
        params.port = parseInt(document.getElementById('defense-port')?.value || 38472);
    } else if (defenseType === 'ip_filtering') {
        const ips = document.getElementById('defense-blocked-ips')?.value;
        params.blocked_ips = ips ? ips.split(',').map(ip => ip.trim()) : [];
    } else if (defenseType === 'dynamic_throttling') {
        params.initial_rate = parseInt(document.getElementById('defense-initial-rate')?.value || 1000);
        params.throttle_factor = parseFloat(document.getElementById('defense-throttle-factor')?.value || 0.5);
    }
    
    try {
        const response = await fetch('/api/defense/enable', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: defenseType,
                params: params
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Defense enabled successfully', 'success');
            document.getElementById('defense-status').innerHTML = `
                <p><strong>Type:</strong> ${defenseType}</p>
                <p><strong>Status:</strong> <span style="color: #10b981;">ACTIVE</span></p>
            `;
        } else {
            showNotification(data.message || 'Failed to enable defense', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function disableDefense() {
    try {
        const response = await fetch('/api/defense/disable', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Defense disabled', 'success');
            document.getElementById('defense-status').innerHTML = '<p class="no-data">No defense active</p>';
        } else {
            showNotification(data.message || 'Failed to disable defense', 'warning');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function loadScenarios() {
    const scenariosGrid = document.getElementById('scenarios-grid');
    
    const scenarios = [
        {
            id: 'nuclear_plant',
            name: 'Nuclear Plant Control',
            description: 'Critical industrial control with robot arms',
            criticality: 'critical'
        },
        {
            id: 'smart_city',
            name: 'Smart City Traffic',
            description: 'Autonomous vehicle management',
            criticality: 'high'
        },
        {
            id: 'military_ops',
            name: 'Military Operation',
            description: 'Tactical drone operations',
            criticality: 'critical'
        },
        {
            id: 'public_event',
            name: 'Public Event',
            description: 'Live broadcasting scenario',
            criticality: 'medium'
        }
    ];
    
    scenariosGrid.innerHTML = scenarios.map(s => `
        <div class="scenario-card" onclick="selectScenario('${s.id}')">
            <h3>${s.name}</h3>
            <p>${s.description}</p>
            <p><strong>Criticality:</strong> <span style="color: ${s.criticality === 'critical' ? '#ef4444' : '#f59e0b'}">${s.criticality}</span></p>
        </div>
    `).join('');
}

function selectScenario(scenarioId) {
    currentScenario = scenarioId;
    document.getElementById('scenario-details').style.display = 'block';
}

async function loadScenario() {
    if (!currentScenario) {
        showNotification('Please select a scenario first', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/scenario/${currentScenario}/load`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`Scenario loaded: ${currentScenario}`, 'success');
        } else {
            showNotification(data.message || 'Failed to load scenario', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function clearScenario() {
    currentScenario = null;
    document.getElementById('scenario-details').style.display = 'none';
}

async function startMonitoring() {
    try {
        const response = await fetch('/api/monitoring/start', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'started' || data.status === 'already_running') {
            monitoringActive = true;
            showNotification('Monitoring started', 'success');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function stopMonitoring() {
    try {
        const response = await fetch('/api/monitoring/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'stopped') {
            monitoringActive = false;
            showNotification('Monitoring stopped', 'success');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function exportPerformance(format) {
    try {
        const response = await fetch('/api/performance/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ format: format })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`Performance data exported to ${data.filepath}`, 'success');
        } else {
            showNotification(data.message || 'Export failed', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function copyCommand(type) {
    const textToCopy = document.getElementById(`${type}-command-preview`).textContent;
    navigator.clipboard.writeText(textToCopy).then(() => {
        showNotification('Command copied to clipboard', 'info');
    });
}

let topologyStatus = {};

async function drawTopology() {
    const svg = document.getElementById('topology-elements');
    svg.innerHTML = '';
    
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.system) {
            topologyStatus = {
                'core': data.system.cn5g === 'running' ? 'online' : 'offline',
                'cu-cp': data.system.gnb === 'running' ? 'online' : 'offline',
                'cu-up': data.system.gnb === 'running' ? 'online' : 'offline',
                'du1': data.system.gnb === 'running' ? 'online' : 'offline',
                'du2': data.system.gnb === 'running' ? 'online' : 'offline',
                'du3': data.system.gnb === 'running' ? 'online' : 'offline',
                'attacker': 'online',
                'defender': 'online'
            };
        }
    } catch (error) {
        console.error('Error fetching topology status:', error);
    }
    
    const width = document.getElementById('topology-svg').clientWidth;
    const height = 600;
    
    const getNodeColor = (nodeId) => {
        const status = topologyStatus[nodeId] || 'offline';
        if (status === 'online') return '#10b981';
        if (status === 'service_unavailable') return '#ef4444';
        return '#64748b';
    };
    
    const nodes = [
        { id: 'core', label: 'CN5G\nCore', x: width/2, y: 50 },
        { id: 'cu-cp', label: 'CU-CP', x: width/3, y: 200 },
        { id: 'cu-up', label: 'CU-UP', x: 2*width/3, y: 200 },
        { id: 'du1', label: 'DU-1', x: width/4, y: 350 },
        { id: 'du2', label: 'DU-2', x: width/2, y: 350 },
        { id: 'du3', label: 'DU-3', x: 3*width/4, y: 350 },
        { id: 'attacker', label: 'Attacker', x: 100, y: 500 },
        { id: 'defender', label: 'Defender', x: width-100, y: 500 }
    ];
    
    const links = [
        { from: 'core', to: 'cu-cp' },
        { from: 'core', to: 'cu-up' },
        { from: 'cu-cp', to: 'du1' },
        { from: 'cu-cp', to: 'du2' },
        { from: 'cu-cp', to: 'du3' },
        { from: 'cu-up', to: 'du1' },
        { from: 'cu-up', to: 'du2' },
        { from: 'cu-up', to: 'du3' }
    ];
    
    links.forEach(link => {
        const from = nodes.find(n => n.id === link.from);
        const to = nodes.find(n => n.id === link.to);
        const fromStatus = topologyStatus[from.id] || 'offline';
        const toStatus = topologyStatus[to.id] || 'offline';
        const isActive = fromStatus === 'online' && toStatus === 'online';
        
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', from.x);
        line.setAttribute('y1', from.y);
        line.setAttribute('x2', to.x);
        line.setAttribute('y2', to.y);
        line.setAttribute('stroke', isActive ? '#10b981' : '#475569');
        line.setAttribute('stroke-width', isActive ? '3' : '2');
        line.setAttribute('opacity', isActive ? '1' : '0.5');
        if (isActive) {
            line.setAttribute('class', 'topology-link-active');
            line.style.animation = 'pulse-line 2s infinite';
        }
        svg.appendChild(line);
    });
    
    nodes.forEach(node => {
        const status = topologyStatus[node.id] || 'offline';
        const color = getNodeColor(node.id);
        const isOnline = status === 'online';
        
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', `topology-node ${status}`);
        
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', node.x);
        circle.setAttribute('cy', node.y);
        circle.setAttribute('r', '30');
        circle.setAttribute('fill', color);
        circle.setAttribute('stroke', '#fff');
        circle.setAttribute('stroke-width', '2');
        if (isOnline) {
            circle.setAttribute('class', 'topology-node-online');
            circle.style.animation = 'pulse-node 2s infinite';
            circle.style.filter = 'drop-shadow(0 0 8px ' + color + ')';
        }
        group.appendChild(circle);
        
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', node.x);
        text.setAttribute('y', node.y + 5);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#fff');
        text.setAttribute('font-size', '12');
        text.setAttribute('font-weight', 'bold');
        text.textContent = node.label.split('\n')[0];
        group.appendChild(text);
        
        svg.appendChild(group);
    });
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer; font-size: 18px;">&times;</button>
        </div>
    `;
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function addAlert(message, type = 'info') {
    const container = document.getElementById('alerts-container');
    
    if (container.querySelector('.no-data')) {
        container.innerHTML = '';
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <div style="display: flex; justify-content: space-between;">
            <span>${new Date().toISOString().replace('T', ' ').substring(0, 19)}: ${message}</span>
        </div>
    `;
    container.insertBefore(alert, container.firstChild);
    
    if (container.children.length > 10) {
        container.lastChild.remove();
    }
}

document.addEventListener('change', (e) => {
    if (e.target.id === 'attack-target' || e.target.id === 'attack-mode' || e.target.closest('#attack-params-container')) {
        updateAttackCommand();
    }
    if (e.target.id === 'defense-category') {
        updateDefenseCategory();
    }
    if (e.target.id === 'defense-type' || e.target.closest('#defense-params-container')) {
        updateDefenseParams();
        updateDefenseCommand();
    }
});


