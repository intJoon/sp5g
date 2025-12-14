let socket;
let socketReconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let isFallbackMode = false;

let paramsCache = {
    attack: {
        types: [],
        currentIndex: 0
    },
    detection: {
        types: [],
        currentIndex: 0
    },
    defense: {
        types: [],
        currentIndex: 0
    }
};

function initializeSocket() {
    try {
        if (typeof io === 'undefined') {
            console.error('Socket.IO library (io) is not defined');
            socket = null;
            return;
        }
        
        const socketUrl = window.location.origin;
        console.log('Initializing Socket.IO connection to:', socketUrl);
        console.log('Socket.IO version check - io function type:', typeof io);
        
        socket = io(socketUrl, {
            transports: ['polling', 'websocket'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: MAX_RECONNECT_ATTEMPTS,
            timeout: 20000,
            forceNew: false,
            upgrade: true,
            rememberUpgrade: false
        });
        
        console.log('Socket.IO instance created, socket object:', socket);
            
            socket.on('connect', () => {
                console.log('✅ Socket.IO connected successfully! Socket ID:', socket.id);
                socketReconnectAttempts = 0;
                isFallbackMode = false;
                updateConnectionStatus(true);
            });
            
            socket.on('connecting', () => {
                console.log('🔄 Socket.IO connecting...');
            });
            
            socket.on('connected', (data) => {
                console.log('✅ Server confirmed connection:', data);
                if (data.message) {
                    console.log('Server message:', data.message);
                }
            });
            
            socket.on('connect_error', (error) => {
                console.error('❌ Socket.IO connection error:', error);
                console.error('Error details:', {
                    message: error.message,
                    type: error.type,
                    description: error.description,
                    data: error.data
                });
                socketReconnectAttempts++;
                console.log(`Connection attempt ${socketReconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
                if (socketReconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                    console.warn('Max reconnection attempts reached, falling back to HTTP polling');
                    startFallbackPolling();
                }
            });
            
            socket.on('disconnect', (reason) => {
                console.log('Socket.IO disconnected:', reason);
                if (reason === 'io server disconnect') {
                    console.log('Server disconnected, will attempt to reconnect');
                } else if (reason === 'io client disconnect') {
                    console.log('Client disconnected');
                } else {
                    console.log('Transport disconnect, will attempt to reconnect');
                }
                updateConnectionStatus(false);
            });
            
            socket.on('reconnect', (attemptNumber) => {
                console.log('Socket.IO reconnected after', attemptNumber, 'attempts');
                updateConnectionStatus(true);
            });
            
            socket.on('reconnect_attempt', (attemptNumber) => {
                console.log('Socket.IO reconnection attempt', attemptNumber);
            });
            
            socket.on('reconnect_failed', () => {
                console.error('Socket.IO reconnection failed, switching to fallback polling');
                startFallbackPolling();
            });
    } catch (e) {
        console.error('Socket.IO initialization failed:', e);
        socket = null;
        setTimeout(() => {
            startFallbackPolling();
        }, 1000);
    }
}

let currentScenario = null;
let monitoringActive = false;
let performanceChart = null;
let cpuMemoryChart = null;
let networkChart = null;
let attackTemplates = {};
let defenseTemplates = {};

document.addEventListener('DOMContentLoaded', () => {
    hideLoadingOverlay();
    
    if (document.querySelector('.dashboard-container')) {
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
        
        if (typeof io !== 'undefined') {
            console.log('Socket.IO library available, initializing...');
            initializeSocket();
            
            setTimeout(() => {
                if (socket) {
                    initializeWebSocket();
                    setTimeout(() => {
                        if (!socket.connected && !isFallbackMode) {
                            console.log('Socket not connected after 5s, starting fallback polling');
                            startFallbackPolling();
                        }
                    }, 5000);
                } else {
                    console.log('Socket initialization failed, starting fallback polling');
                    startFallbackPolling();
                }
            }, 500);
        } else {
            console.warn('Socket.IO library not loaded, using fallback polling immediately');
            setTimeout(() => {
                startFallbackPolling();
            }, 1000);
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
        
        try {
            initializeTheme();
        } catch (e) {
            console.error('Error initializing theme:', e);
        }
        
        try {
            setTimeout(() => {
                const activeTab = document.querySelector('.nav-item.active')?.dataset.tab;
                if (activeTab === 'overview') {
                    drawTopology();
                }
            }, 800);
        } catch (e) {
            console.error('Error initializing topology:', e);
        }
        
        console.log('Dashboard initialization complete');
    }
});

window.addEventListener('load', () => {
    hideLoadingOverlay();
});

setTimeout(() => {
    hideLoadingOverlay();
}, 1000);

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
        overlay.classList.add('hidden');
        if (document.body) {
            document.body.classList.add('fade-in');
        }
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
    const navItems = document.querySelectorAll('.nav-item[data-tab]');
    const tabContents = document.querySelectorAll('.tab-content');
    
    const pageTitles = {
        'overview': 'Overview',
        'attack': 'Attack Configuration',
        'detection': 'Detection Configuration',
        'defense': 'Defense Configuration',
        'scenarios': 'Attack Scenarios'
    };
    
    const pageDescriptions = {
        'overview': 'System status and real-time metrics',
        'attack': 'Configure and launch attacks',
        'detection': 'Configure and enable detection systems',
        'defense': 'Configure and enable defense mechanisms',
        'scenarios': 'Load and manage attack scenarios'
    };

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = item.dataset.tab;
            
            navItems.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            item.classList.add('active');
            const targetContent = document.getElementById(`${targetTab}-tab`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
            
            document.getElementById('page-title').textContent = pageTitles[targetTab] || 'Dashboard';
            document.getElementById('page-description').textContent = pageDescriptions[targetTab] || '';
            
            if (targetTab === 'scenarios') {
                loadScenarios();
            }
            
            if (targetTab === 'overview') {
                setTimeout(() => {
                    drawTopology();
                }, 300);
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
    if (!socket) {
        console.warn('Socket.IO not available, using fallback polling');
        startFallbackPolling();
        return;
    }
    
    console.log('Initializing WebSocket, socket state:', socket.connected ? 'connected' : 'disconnected');
    
    if (socket.connected) {
        console.log('Socket already connected');
        updateConnectionStatus(true);
        fetchStatus();
        setupStatusPolling();
    } else {
        console.log('Waiting for socket connection...');
        socket.once('connect', () => {
            console.log('Connected to server');
            updateConnectionStatus(true);
            fetchStatus();
            setupStatusPolling();
        });
        
        setTimeout(() => {
            if (!socket.connected) {
                console.warn('Socket connection timeout after 5s, socket state:', socket.connected);
                console.warn('Switching to fallback polling mode');
                startFallbackPolling();
            }
        }, 5000);
    }

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

function setupStatusPolling() {
    if (window.statusInterval) {
        clearInterval(window.statusInterval);
    }
    window.statusInterval = setInterval(() => {
        fetchStatus();
        const activeTab = document.querySelector('.nav-item.active')?.dataset.tab;
        if (activeTab === 'overview') {
            drawTopology();
        }
    }, 3000);
    
    if (window.metricsInterval) {
        clearInterval(window.metricsInterval);
    }
    window.metricsInterval = setInterval(updateMetricsDisplay, 1000);
}

function startFallbackPolling() {
    console.log('Starting fallback polling mode');
    isFallbackMode = true;
    updateConnectionStatus(false, true);
    
    fetchStatus();
    setupStatusPolling();
}

function updateConnectionStatus(connected, isPolling = false) {
    const statusEl = document.getElementById('connection-status');
    if (!statusEl) return;
    
    if (connected) {
        isFallbackMode = false;
        statusEl.classList.add('connected');
        statusEl.classList.remove('polling');
        const span = statusEl.querySelector('span');
        if (span) span.textContent = 'Connected';
        const icon = statusEl.querySelector('i');
        if (icon) icon.className = 'fas fa-circle';
    } else {
        statusEl.classList.remove('connected');
        const span = statusEl.querySelector('span');
        const icon = statusEl.querySelector('i');
        
        if (isPolling || isFallbackMode) {
            statusEl.classList.add('polling');
            if (span) span.textContent = 'Polling Mode';
            if (icon) icon.className = 'fas fa-sync-alt';
        } else {
            statusEl.classList.remove('polling');
            if (span) span.textContent = 'Disconnected';
            if (icon) icon.className = 'fas fa-circle';
        }
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
            return { text: 'Unknown', class: 'offline', icon: 'fa-question-circle' };
        }
        if (statusValue === 'running' || statusValue === 'active' || statusValue === 'online') {
            return { text: 'Running', class: 'online', icon: 'fa-check-circle' };
        }
        if (statusValue === 'stopped' || statusValue === 'inactive' || statusValue === 'offline') {
            return { text: 'Stopped', class: 'offline', icon: 'fa-times-circle' };
        }
        return { text: statusValue, class: 'offline', icon: 'fa-question-circle' };
    };
    
    const updateStatusElement = (elementId, statusValue) => {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const display = getStatusDisplay(statusValue);
        element.textContent = display.text;
        element.className = `status-badge ${display.class}`;
    };
    
    updateStatusElement('cn5g-status', status.cn5g);
    updateStatusElement('gnb-status', status.gnb);
    updateStatusElement('ue-status', status.ue);
    
    const nsElement = document.getElementById('ns-status');
    if (nsElement) {
        const nsCount = status.namespaces?.length || 0;
        nsElement.textContent = nsCount;
        nsElement.className = nsCount > 0 ? 'status-badge online' : 'status-badge offline';
    }
    
}

function updateMetrics(metrics) {
    if (!metrics) return;
    
    const system = metrics.system || {};
    const network = metrics.network || {};
    const f1 = metrics.f1_interface || {};
    
    const cpuValue = system.cpu_percent || 0;
    const memoryValue = system.memory_percent || 0;
    
    
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

let sourceCodeCache = {
    attack: { types: [], currentIndex: 0, data: {} },
    detection: { types: [], currentIndex: 0, data: {} },
    defense: { types: [], currentIndex: 0, data: {} }
};

let sourceCodeAbortControllers = {
    attack: null,
    detection: null,
    defense: null
};

function getSelectedAttackTypes() {
    const checkboxes = document.querySelectorAll('input[name="attack-type"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function updateAttackParams() {
    const selectedTypes = getSelectedAttackTypes();
    const container = document.getElementById('attack-params-container');
    const nav = document.getElementById('attack-params-nav');
    
    paramsCache.attack.types = selectedTypes;
    paramsCache.attack.currentIndex = 0;
    
    if (selectedTypes.length === 0) {
        container.innerHTML = '';
        nav.style.display = 'none';
        updateAttackCommand();
        updateSourceCode('attack', []);
        return;
    }
    
    updateSourceCode('attack', selectedTypes);
    displayAttackParams();
    updateAttackCommand();
}

function displayAttackParams() {
    const selectedTypes = paramsCache.attack.types;
    const currentIndex = paramsCache.attack.currentIndex;
    const container = document.getElementById('attack-params-container');
    const nav = document.getElementById('attack-params-nav');
    const titleEl = document.getElementById('attack-params-title');
    const counterEl = document.getElementById('attack-params-counter');
    const prevBtn = document.getElementById('attack-params-prev');
    const nextBtn = document.getElementById('attack-params-next');
    
    if (selectedTypes.length === 0) {
        container.innerHTML = '';
        nav.style.display = 'none';
        return;
    }
    
    if (selectedTypes.length > 1) {
        nav.style.display = 'flex';
    } else {
        nav.style.display = 'none';
    }
    
    const currentType = selectedTypes[currentIndex];
    const displayName = currentType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    
    if (titleEl) titleEl.textContent = displayName;
    if (counterEl) counterEl.textContent = `${currentIndex + 1} / ${selectedTypes.length}`;
    
    let paramsHTML = '';
    const hasUEOrBearer = currentType.includes('ue') || currentType.includes('bearer');
    const hasFlood = currentType.includes('flood');
    
    if (hasUEOrBearer) {
        paramsHTML += `
            <div class="form-section">
                <label class="form-label">UE/Bearer Count:</label>
                <input type="number" class="form-control" id="param-count-${currentType}" value="1000" min="1" onchange="updateAttackCommand()">
            </div>
        `;
    }
    
    if (hasFlood) {
        paramsHTML += `
            <div class="form-section">
                <label class="form-label">Packet Size (bytes):</label>
                <input type="number" class="form-control" id="param-packet-size-${currentType}" value="1024" min="64" onchange="updateAttackCommand()">
            </div>
        `;
    }
    
    paramsHTML += `
        <div class="form-section">
            <label class="form-label">Rate (packets/sec):</label>
            <input type="number" class="form-control" id="param-rate-${currentType}" value="100" min="1" onchange="updateAttackCommand()">
        </div>
        <div class="form-section">
            <label class="form-label">Duration (seconds):</label>
            <input type="number" class="form-control" id="param-duration-${currentType}" value="60" min="1" onchange="updateAttackCommand()">
        </div>
    `;
    
    container.innerHTML = paramsHTML;
    
    if (prevBtn) {
        prevBtn.disabled = currentIndex === 0;
        if (currentIndex === 0) {
            prevBtn.style.opacity = '0.4';
            prevBtn.style.cursor = 'not-allowed';
        } else {
            prevBtn.style.opacity = '1';
            prevBtn.style.cursor = 'pointer';
        }
    }
    if (nextBtn) {
        nextBtn.disabled = currentIndex === selectedTypes.length - 1;
        if (currentIndex === selectedTypes.length - 1) {
            nextBtn.style.opacity = '0.4';
            nextBtn.style.cursor = 'not-allowed';
        } else {
            nextBtn.style.opacity = '1';
            nextBtn.style.cursor = 'pointer';
        }
    }
}

function navigateParams(category, direction) {
    if (!paramsCache || !paramsCache[category]) {
        console.error('paramsCache not initialized for category:', category);
        return;
    }
    
    const cache = paramsCache[category];
    
    if (!cache.types || cache.types.length === 0) {
        console.warn('No types available for navigation');
        return;
    }
    
    if (direction === 'prev' && cache.currentIndex > 0) {
        cache.currentIndex--;
    } else if (direction === 'next' && cache.currentIndex < cache.types.length - 1) {
        cache.currentIndex++;
    } else {
        return;
    }
    
    try {
        if (category === 'attack') {
            displayAttackParams();
            updateAttackCommand();
        } else if (category === 'detection') {
            displayDetectionParams();
            updateDetectionCommand();
        } else if (category === 'defense') {
            displayDefenseParams();
            updateDefenseCommand();
        }
    } catch (e) {
        console.error('Error navigating params:', e);
    }
}

function updateAttackCommand() {
    const selectedTypes = getSelectedAttackTypes();
    const target = document.getElementById('attack-target').value;
    const mode = document.getElementById('attack-mode').value;
    
    if (selectedTypes.length === 0) {
        document.getElementById('attack-command-preview').textContent = 
            'Select attack type(s) to generate command...';
        return;
    }
    
    let commands = [];
    
    selectedTypes.forEach(attackType => {
        let command = `sudo python3 /home/sp5g/sp5g/add-on/units/actioner/attacker/`;
        
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
        
        const rate = document.getElementById(`param-rate-${attackType}`)?.value;
        const duration = document.getElementById(`param-duration-${attackType}`)?.value;
        const count = document.getElementById(`param-count-${attackType}`)?.value;
        const packetSize = document.getElementById(`param-packet-size-${attackType}`)?.value;
        
        if (rate) command += ` --rate ${rate}`;
        if (duration) command += ` --duration ${duration}`;
        if (count) command += ` --count ${count}`;
        if (packetSize) command += ` --packet-size ${packetSize}`;
        
        commands.push(command);
    });
    
    document.getElementById('attack-command-preview').textContent = commands.join('\n\n');
}

async function launchAttack() {
    const selectedTypes = getSelectedAttackTypes();
    const target = document.getElementById('attack-target').value;
    const mode = document.getElementById('attack-mode').value;
    
    if (selectedTypes.length === 0) {
        showNotification('Please select at least one attack type', 'warning');
        return;
    }
    
    const allParams = [];
    
    selectedTypes.forEach(attackType => {
        const params = {
            rate: parseInt(document.getElementById(`param-rate-${attackType}`)?.value || 100),
            duration: parseInt(document.getElementById(`param-duration-${attackType}`)?.value || 60)
        };
        
        const countEl = document.getElementById(`param-count-${attackType}`);
        if (countEl) params.ue_count = parseInt(countEl.value);
        
        const packetSizeEl = document.getElementById(`param-packet-size-${attackType}`);
        if (packetSizeEl) params.packet_size = parseInt(packetSizeEl.value);
        
        allParams.push({ type: attackType, params: params });
    });
    
    try {
        const response = await fetch('/api/attack/launch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                types: selectedTypes,
                target: target,
                params_list: allParams,
                mode: mode
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`Attack(s) launched successfully: ${selectedTypes.join(', ')}`, 'success');
            document.getElementById('attack-status').innerHTML = `
                <p><strong>Types:</strong> ${selectedTypes.join(', ')}</p>
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

function getSelectedDetectionTypes() {
    const checkboxes = document.querySelectorAll('input[name="detection-type"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function updateDetectionParams() {
    const selectedTypes = getSelectedDetectionTypes();
    const container = document.getElementById('detection-params-container');
    const nav = document.getElementById('detection-params-nav');
    
    paramsCache.detection.types = selectedTypes;
    paramsCache.detection.currentIndex = 0;
    
    if (selectedTypes.length === 0) {
        container.innerHTML = '';
        nav.style.display = 'none';
        updateDetectionCommand();
        updateSourceCode('detection', []);
        return;
    }
    
    updateSourceCode('detection', selectedTypes);
    displayDetectionParams();
    updateDetectionCommand();
}

function displayDetectionParams() {
    const selectedTypes = paramsCache.detection.types;
    const currentIndex = paramsCache.detection.currentIndex;
    const container = document.getElementById('detection-params-container');
    const nav = document.getElementById('detection-params-nav');
    const titleEl = document.getElementById('detection-params-title');
    const counterEl = document.getElementById('detection-params-counter');
    const prevBtn = document.getElementById('detection-params-prev');
    const nextBtn = document.getElementById('detection-params-next');
    
    if (selectedTypes.length === 0) {
        container.innerHTML = '';
        nav.style.display = 'none';
        return;
    }
    
    if (selectedTypes.length > 1) {
        nav.style.display = 'flex';
    } else {
        nav.style.display = 'none';
    }
    
    const currentType = selectedTypes[currentIndex];
    const displayName = currentType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    
    if (titleEl) titleEl.textContent = displayName;
    if (counterEl) counterEl.textContent = `${currentIndex + 1} / ${selectedTypes.length}`;
    
    let paramsHTML = '';
    
    if (currentType === 'threshold_based') {
        paramsHTML += `
            <div class="form-section">
                <label class="form-label">CPU Threshold (%):</label>
                <input type="number" class="form-control" id="detection-cpu-threshold-${currentType}" value="80" min="0" max="100" onchange="updateDetectionCommand()">
            </div>
            <div class="form-section">
                <label class="form-label">Memory Threshold (%):</label>
                <input type="number" class="form-control" id="detection-memory-threshold-${currentType}" value="85" min="0" max="100" onchange="updateDetectionCommand()">
            </div>
            <div class="form-section">
                <label class="form-label">Packet Rate Threshold:</label>
                <input type="number" class="form-control" id="detection-packet-threshold-${currentType}" value="10000" min="0" onchange="updateDetectionCommand()">
            </div>
        `;
    } else if (currentType === 'statistical_analysis' || currentType === 'pattern_recognition') {
        paramsHTML += `
            <div class="form-section">
                <label class="form-label">Analysis Window (seconds):</label>
                <input type="number" class="form-control" id="detection-window-${currentType}" value="60" min="10" onchange="updateDetectionCommand()">
            </div>
            <div class="form-section">
                <label class="form-label">Sensitivity:</label>
                <select class="form-control" id="detection-sensitivity-${currentType}" onchange="updateDetectionCommand()">
                    <option value="low">Low</option>
                    <option value="medium" selected>Medium</option>
                    <option value="high">High</option>
                </select>
            </div>
        `;
    }
    
    container.innerHTML = paramsHTML;
    
    if (prevBtn) {
        prevBtn.disabled = currentIndex === 0;
        if (currentIndex === 0) {
            prevBtn.style.opacity = '0.4';
            prevBtn.style.cursor = 'not-allowed';
        } else {
            prevBtn.style.opacity = '1';
            prevBtn.style.cursor = 'pointer';
        }
    }
    if (nextBtn) {
        nextBtn.disabled = currentIndex === selectedTypes.length - 1;
        if (currentIndex === selectedTypes.length - 1) {
            nextBtn.style.opacity = '0.4';
            nextBtn.style.cursor = 'not-allowed';
        } else {
            nextBtn.style.opacity = '1';
            nextBtn.style.cursor = 'pointer';
        }
    }
}

function updateDetectionCommand() {
    const selectedTypes = getSelectedDetectionTypes();
    
    if (selectedTypes.length === 0) {
        document.getElementById('detection-command-preview').textContent = 
            'Select detection type(s) to generate command...';
        return;
    }
    
    let commands = [];
    
    selectedTypes.forEach(detectionType => {
        let command = `sudo python3 /home/sp5g/sp5g/add-on/units/actioner/detector/detector.py`;
        
        if (detectionType === 'threshold_based') {
            const cpu = document.getElementById(`detection-cpu-threshold-${detectionType}`)?.value || 80;
            const memory = document.getElementById(`detection-memory-threshold-${detectionType}`)?.value || 85;
            const packet = document.getElementById(`detection-packet-threshold-${detectionType}`)?.value || 10000;
            command += ` --type threshold --cpu-threshold ${cpu} --memory-threshold ${memory} --packet-threshold ${packet}`;
        } else if (detectionType === 'statistical_analysis') {
            command += ` --type statistical`;
            const detectionWindow = document.getElementById(`detection-window-${detectionType}`)?.value || 60;
            const sensitivity = document.getElementById(`detection-sensitivity-${detectionType}`)?.value || 'medium';
            command += ` --window ${detectionWindow} --sensitivity ${sensitivity}`;
        } else if (detectionType === 'pattern_recognition') {
            command += ` --type pattern`;
            const detectionWindow = document.getElementById(`detection-window-${detectionType}`)?.value || 60;
            const sensitivity = document.getElementById(`detection-sensitivity-${detectionType}`)?.value || 'medium';
            command += ` --window ${detectionWindow} --sensitivity ${sensitivity}`;
        }
        
        commands.push(command);
    });
    
    document.getElementById('detection-command-preview').textContent = commands.join('\n\n');
}

async function enableDetection() {
    const selectedTypes = getSelectedDetectionTypes();
    
    if (selectedTypes.length === 0) {
        showNotification('Please select at least one detection type', 'warning');
        return;
    }
    
    const allParams = [];
    
    selectedTypes.forEach(detectionType => {
        const params = {};
        
        if (detectionType === 'threshold_based') {
            params.cpu_threshold = parseInt(document.getElementById(`detection-cpu-threshold-${detectionType}`)?.value || 80);
            params.memory_threshold = parseInt(document.getElementById(`detection-memory-threshold-${detectionType}`)?.value || 85);
            params.packet_threshold = parseInt(document.getElementById(`detection-packet-threshold-${detectionType}`)?.value || 10000);
        } else if (detectionType === 'statistical_analysis' || detectionType === 'pattern_recognition') {
            params.window = parseInt(document.getElementById(`detection-window-${detectionType}`)?.value || 60);
            params.sensitivity = document.getElementById(`detection-sensitivity-${detectionType}`)?.value || 'medium';
        }
        
        allParams.push({ type: detectionType, params: params });
    });
    
    try {
        const response = await fetch('/api/defense/enable', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                types: selectedTypes,
                params_list: allParams
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`Detection enabled successfully: ${selectedTypes.join(', ')}`, 'success');
            updateDetectionStatus(data);
        } else {
            showNotification(data.message || 'Failed to enable detection', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function disableDetection() {
    try {
        const response = await fetch('/api/defense/disable', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Detection disabled successfully', 'success');
            document.getElementById('detection-status').innerHTML = '<div class="no-data">No detection active</div>';
        } else {
            showNotification(data.message || 'Failed to disable detection', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function updateDetectionStatus(data) {
    const statusEl = document.getElementById('detection-status');
    if (statusEl && data.config) {
        statusEl.innerHTML = `
            <div style="padding: 12px;">
                <div style="font-weight: 600; margin-bottom: 8px;">Active Detection</div>
                <div style="font-size: 14px; color: var(--text-secondary);">
                    Type: ${data.config.type}<br>
                    Started: ${new Date(data.config.start_time).toLocaleString()}
                </div>
            </div>
        `;
    }
}

function getSelectedDefenseTypes() {
    const checkboxes = document.querySelectorAll('input[name="defense-type"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function updateDefenseParams() {
    const selectedTypes = getSelectedDefenseTypes();
    const container = document.getElementById('defense-params-container');
    const nav = document.getElementById('defense-params-nav');
    
    paramsCache.defense.types = selectedTypes;
    paramsCache.defense.currentIndex = 0;
    
    if (selectedTypes.length === 0) {
        container.innerHTML = '';
        nav.style.display = 'none';
        updateDefenseCommand();
        updateSourceCode('defense', []);
        return;
    }
    
    updateSourceCode('defense', selectedTypes);
    displayDefenseParams();
    updateDefenseCommand();
}

function displayDefenseParams() {
    const selectedTypes = paramsCache.defense.types;
    const currentIndex = paramsCache.defense.currentIndex;
    const container = document.getElementById('defense-params-container');
    const nav = document.getElementById('defense-params-nav');
    const titleEl = document.getElementById('defense-params-title');
    const counterEl = document.getElementById('defense-params-counter');
    const prevBtn = document.getElementById('defense-params-prev');
    const nextBtn = document.getElementById('defense-params-next');
    
    if (selectedTypes.length === 0) {
        container.innerHTML = '';
        nav.style.display = 'none';
        return;
    }
    
    if (selectedTypes.length > 1) {
        nav.style.display = 'flex';
    } else {
        nav.style.display = 'none';
    }
    
    const currentType = selectedTypes[currentIndex];
    const displayName = currentType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    
    if (titleEl) titleEl.textContent = displayName;
    if (counterEl) counterEl.textContent = `${currentIndex + 1} / ${selectedTypes.length}`;
    
    let paramsHTML = '';
    
    if (currentType === 'rate_limiting') {
        paramsHTML += `
            <div class="form-section">
                <label class="form-label">Rate Limit (packets/sec):</label>
                <input type="number" class="form-control" id="defense-rate-limit-${currentType}" value="100" min="1" onchange="updateDefenseCommand()">
            </div>
            <div class="form-section">
                <label class="form-label">Port:</label>
                <input type="number" class="form-control" id="defense-port-${currentType}" value="38472" min="1" onchange="updateDefenseCommand()">
            </div>
        `;
    } else if (currentType === 'ip_filtering') {
        paramsHTML += `
            <div class="form-section">
                <label class="form-label">Blocked IPs (comma-separated):</label>
                <input type="text" class="form-control" id="defense-blocked-ips-${currentType}" placeholder="192.168.1.1,192.168.1.2" onchange="updateDefenseCommand()">
            </div>
        `;
    } else if (currentType === 'dynamic_throttling') {
        paramsHTML += `
            <div class="form-section">
                <label class="form-label">Initial Rate (packets/sec):</label>
                <input type="number" class="form-control" id="defense-initial-rate-${currentType}" value="1000" min="1" onchange="updateDefenseCommand()">
            </div>
            <div class="form-section">
                <label class="form-label">Throttle Factor:</label>
                <input type="number" class="form-control" id="defense-throttle-factor-${currentType}" value="0.5" min="0.1" max="1" step="0.1" onchange="updateDefenseCommand()">
            </div>
        `;
    }
    
    container.innerHTML = paramsHTML;
    
    if (prevBtn) {
        prevBtn.disabled = currentIndex === 0;
        if (currentIndex === 0) {
            prevBtn.style.opacity = '0.4';
            prevBtn.style.cursor = 'not-allowed';
        } else {
            prevBtn.style.opacity = '1';
            prevBtn.style.cursor = 'pointer';
        }
    }
    if (nextBtn) {
        nextBtn.disabled = currentIndex === selectedTypes.length - 1;
        if (currentIndex === selectedTypes.length - 1) {
            nextBtn.style.opacity = '0.4';
            nextBtn.style.cursor = 'not-allowed';
        } else {
            nextBtn.style.opacity = '1';
            nextBtn.style.cursor = 'pointer';
        }
    }
}

function updateDefenseCommand() {
    const selectedTypes = getSelectedDefenseTypes();
    
    if (selectedTypes.length === 0) {
        document.getElementById('defense-command-preview').textContent = 
            'Select defense type(s) to generate command...';
        return;
    }
    
    let commands = [];
    
    selectedTypes.forEach(defenseType => {
        let command = `sudo python3 /home/sp5g/sp5g/add-on/units/actioner/defender/`;
        
        if (defenseType === 'rate_limiting') {
            const rate = document.getElementById(`defense-rate-limit-${defenseType}`)?.value || 100;
            const port = document.getElementById(`defense-port-${defenseType}`)?.value || 38472;
            command += `rate_limiter.py --rate ${rate} --port ${port}`;
        } else if (defenseType === 'ip_filtering') {
            const ips = document.getElementById(`defense-blocked-ips-${defenseType}`)?.value || '';
            command += `filter.py --block ${ips}`;
        } else if (defenseType === 'dynamic_throttling') {
            const initialRate = document.getElementById(`defense-initial-rate-${defenseType}`)?.value || 1000;
            const factor = document.getElementById(`defense-throttle-factor-${defenseType}`)?.value || 0.5;
            command += `rate_limiter.py --dynamic --initial-rate ${initialRate} --factor ${factor}`;
        } else {
            command += `filter.py --type ${defenseType}`;
        }
        
        commands.push(command);
    });
    
    document.getElementById('defense-command-preview').textContent = commands.join('\n\n');
}

async function enableDefense() {
    const selectedTypes = getSelectedDefenseTypes();
    
    if (selectedTypes.length === 0) {
        showNotification('Please select at least one defense type', 'warning');
        return;
    }
    
    const allParams = [];
    
    selectedTypes.forEach(defenseType => {
        const params = {};
        
        if (defenseType === 'rate_limiting') {
            params.rate = parseInt(document.getElementById(`defense-rate-limit-${defenseType}`)?.value || 100);
            params.port = parseInt(document.getElementById(`defense-port-${defenseType}`)?.value || 38472);
        } else if (defenseType === 'ip_filtering') {
            const ips = document.getElementById(`defense-blocked-ips-${defenseType}`)?.value;
            params.blocked_ips = ips ? ips.split(',').map(ip => ip.trim()) : [];
        } else if (defenseType === 'dynamic_throttling') {
            params.initial_rate = parseInt(document.getElementById(`defense-initial-rate-${defenseType}`)?.value || 1000);
            params.throttle_factor = parseFloat(document.getElementById(`defense-throttle-factor-${defenseType}`)?.value || 0.5);
        }
        
        allParams.push({ type: defenseType, params: params });
    });
    
    try {
        const response = await fetch('/api/defense/enable', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                types: selectedTypes,
                params_list: allParams
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`Defense enabled successfully: ${selectedTypes.join(', ')}`, 'success');
            document.getElementById('defense-status').innerHTML = `
                <p><strong>Types:</strong> ${selectedTypes.join(', ')}</p>
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
let topologyDrawTimeout = null;
let isDrawingTopology = false;

async function drawTopology() {
    if (isDrawingTopology) {
        return;
    }
    
    if (topologyDrawTimeout) {
        clearTimeout(topologyDrawTimeout);
    }
    
    topologyDrawTimeout = setTimeout(async () => {
        await _drawTopologyInternal();
    }, 100);
}

async function _drawTopologyInternal() {
    isDrawingTopology = true;
    
    const svg = document.getElementById('topology-elements');
    if (!svg) {
        isDrawingTopology = false;
        return;
    }
    
    const svgContainer = document.getElementById('topology-svg');
    if (!svgContainer) {
        isDrawingTopology = false;
        return;
    }
    
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.system) {
            const isRunning = data.system.cn5g === 'running' || data.system.gnb === 'running';
            topologyStatus = {
                'amf': isRunning ? 'online' : 'offline',
                'smf': isRunning ? 'online' : 'offline',
                'upf': isRunning ? 'online' : 'offline',
                'cu-cp': isRunning ? 'online' : 'offline',
                'cu-up1': isRunning ? 'online' : 'offline',
                'cu-up2': isRunning ? 'online' : 'offline',
                'du1': isRunning ? 'online' : 'offline',
                'du2': isRunning ? 'online' : 'offline',
                'du3': isRunning ? 'online' : 'offline',
                'rfsim1': isRunning ? 'online' : 'offline',
                'rfsim2': isRunning ? 'online' : 'offline',
                'rfsim3': isRunning ? 'online' : 'offline',
                'ue1': isRunning ? 'online' : 'offline',
                'ue2': isRunning ? 'online' : 'offline',
                'ue3': isRunning ? 'online' : 'offline',
                'ue4': isRunning ? 'online' : 'offline'
            };
        }
    } catch (error) {
        console.error('Error fetching topology status:', error);
        topologyStatus = {};
    }
    
    let width = svgContainer.clientWidth || 1400;
    const height = 1000;
    
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    
    svg.innerHTML = '';
    
    const getNodeColor = (status) => {
        if (status === 'online') return '#10b981';
        if (status === 'service_unavailable') return '#ef4444';
        return '#64748b';
    };
    
    const createNode = (id, label, ip, x, y, width = 140, height = 60) => {
        const status = topologyStatus[id] || 'offline';
        const color = getNodeColor(status);
        const isOnline = status === 'online';
        
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', `topology-node ${status}`);
        
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x - width/2);
        rect.setAttribute('y', y - height/2);
        rect.setAttribute('width', width);
        rect.setAttribute('height', height);
        rect.setAttribute('rx', '8');
        rect.setAttribute('fill', color);
        rect.setAttribute('stroke', '#fff');
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('opacity', isOnline ? '1' : '0.6');
        if (isOnline) {
            rect.style.filter = 'drop-shadow(0 0 6px ' + color + ')';
        }
        group.appendChild(rect);
        
        const titleText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        titleText.setAttribute('x', x);
        titleText.setAttribute('y', y - 10);
        titleText.setAttribute('text-anchor', 'middle');
        titleText.setAttribute('fill', '#fff');
        titleText.setAttribute('font-size', '13');
        titleText.setAttribute('font-weight', 'bold');
        titleText.textContent = label;
        group.appendChild(titleText);
        
        if (ip) {
            const ipText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            ipText.setAttribute('x', x);
            ipText.setAttribute('y', y + 10);
            ipText.setAttribute('text-anchor', 'middle');
            ipText.setAttribute('fill', '#e2e8f0');
            ipText.setAttribute('font-size', '11');
            ipText.textContent = ip;
            group.appendChild(ipText);
        }
        
        svg.appendChild(group);
        return { x, y, id, status };
    };
    
    const createInterfaceBox = (label, ip, x, y) => {
        const status = topologyStatus[label.toLowerCase().replace(/[^a-z0-9]/g, '-')] || 'online';
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x - 60);
        rect.setAttribute('y', y - 25);
        rect.setAttribute('width', 120);
        rect.setAttribute('height', 50);
        rect.setAttribute('rx', '4');
        rect.setAttribute('fill', 'rgba(59, 130, 246, 0.2)');
        rect.setAttribute('stroke', '#3b82f6');
        rect.setAttribute('stroke-width', '1.5');
        rect.setAttribute('stroke-dasharray', '4,2');
        group.appendChild(rect);
        
        const labelText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        labelText.setAttribute('x', x);
        labelText.setAttribute('y', y - 8);
        labelText.setAttribute('text-anchor', 'middle');
        labelText.setAttribute('fill', '#3b82f6');
        labelText.setAttribute('font-size', '11');
        labelText.setAttribute('font-weight', 'bold');
        labelText.textContent = label;
        group.appendChild(labelText);
        
        if (ip) {
            const ipText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            ipText.setAttribute('x', x);
            ipText.setAttribute('y', y + 8);
            ipText.setAttribute('text-anchor', 'middle');
            ipText.setAttribute('fill', '#64748b');
            ipText.setAttribute('font-size', '10');
            ipText.textContent = ip;
            group.appendChild(ipText);
        }
        
        svg.appendChild(group);
        return { x, y };
    };
    
    const createLink = (fromX, fromY, toX, toY, label = '', isActive = true) => {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', fromX);
        line.setAttribute('y1', fromY);
        line.setAttribute('x2', toX);
        line.setAttribute('y2', toY);
        line.setAttribute('stroke', isActive ? '#10b981' : '#475569');
        line.setAttribute('stroke-width', isActive ? '2' : '1.5');
        line.setAttribute('opacity', isActive ? '0.8' : '0.4');
        if (isActive && !label) {
            line.style.animation = 'pulse-line 3s infinite';
        }
        svg.appendChild(line);
        
        if (label) {
            const midX = (fromX + toX) / 2;
            const midY = (fromY + toY) / 2;
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', midX);
            text.setAttribute('y', midY - 5);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', '#94a3b8');
            text.setAttribute('font-size', '10');
            text.setAttribute('font-weight', 'bold');
            text.setAttribute('dominant-baseline', 'middle');
            text.setAttribute('paint-order', 'stroke');
            text.setAttribute('stroke', 'rgba(15, 23, 42, 0.8)');
            text.setAttribute('stroke-width', '3');
            text.setAttribute('stroke-linecap', 'round');
            text.setAttribute('stroke-linejoin', 'round');
            text.textContent = label;
            svg.appendChild(text);
        }
    };
    
    const centerX = width / 2;
    let y = 80;
    
    const amf = createNode('amf', 'AMF', '192.168.71.132', centerX - 200, y);
    const smf = createNode('smf', 'SMF', '192.168.71.133', centerX, y);
    const upf = createNode('upf', 'UPF', '192.168.71.134', centerX + 200, y);
    
    y = 220;
    const n2 = createInterfaceBox('N2', '192.168.71.X', centerX - 200, y);
    const n11 = createInterfaceBox('N11', '', centerX - 100, y);
    const n4 = createInterfaceBox('N4', '', centerX + 100, y);
    const n3_1 = createInterfaceBox('N3', '192.168.71.X', centerX + 150, y);
    const n3_2 = createInterfaceBox('N3', '192.168.71.X', centerX + 250, y);
    
    y = 320;
    const cu_cp = createNode('cu-cp', 'CU-CP', '', centerX - 200, y);
    const f1c = createInterfaceBox('F1-C', '192.168.72.2', centerX - 100, y);
    const e1_1 = createInterfaceBox('E1', '192.168.77.2', centerX, y);
    const e1_2 = createInterfaceBox('E1', '192.168.77.3', centerX + 100, y);
    const e1_3 = createInterfaceBox('E1', '192.168.77.4', centerX + 200, y);
    const cu_up1_n3 = createInterfaceBox('N3', '192.168.71.X', centerX + 50, y);
    const cu_up2_n3 = createInterfaceBox('N3', '192.168.71.X', centerX + 150, y);
    
    y = 420;
    const cu_up1 = createNode('cu-up1', 'CU-UP1', '', centerX + 50, y);
    const cu_up2 = createNode('cu-up2', 'CU-UP2', '', centerX + 150, y);
    const f1u_up1 = createInterfaceBox('F1-U', '192.168.73.2', centerX - 150, y);
    const f1u_up2_1 = createInterfaceBox('F1-U', '192.168.74.2', centerX + 50, y);
    const f1u_up2_2 = createInterfaceBox('F1-U', '192.168.74.2', centerX + 150, y);
    
    y = 520;
    const f1c_du1 = createInterfaceBox('F1-C', '192.168.72.3', centerX - 300, y);
    const f1u_du1 = createInterfaceBox('F1-U', '192.168.73.3', centerX - 200, y);
    const f1c_du2 = createInterfaceBox('F1-C', '192.168.72.4', centerX - 50, y);
    const f1u_du2 = createInterfaceBox('F1-U', '192.168.74.3', centerX + 50, y);
    const f1c_du3 = createInterfaceBox('F1-C', '192.168.72.5', centerX + 200, y);
    const f1u_du3 = createInterfaceBox('F1-U', '192.168.74.4', centerX + 300, y);
    
    y = 620;
    const du1 = createNode('du1', 'DU1', '', centerX - 250, y);
    const du2 = createNode('du2', 'DU2', '', centerX, y);
    const du3 = createNode('du3', 'DU3', '', centerX + 250, y);
    
    y = 720;
    const rfsim1 = createInterfaceBox('RFSIM', '192.168.78.2', centerX - 300, y);
    const rfsim2 = createInterfaceBox('RFSIM', '192.168.78.3', centerX - 50, y);
    const rfsim3 = createInterfaceBox('RFSIM', '192.168.78.4', centerX + 250, y);
    
    y = 820;
    const rfsim1_ue = createInterfaceBox('RFSIM', '192.168.78.5', centerX - 300, y);
    const rfsim2_ue = createInterfaceBox('RFSIM', '192.168.78.6', centerX - 50, y);
    const rfsim3_ue1 = createInterfaceBox('RFSIM', '192.168.78.7', centerX + 200, y);
    const rfsim3_ue2 = createInterfaceBox('RFSIM', '192.168.78.8', centerX + 300, y);
    
    y = 920;
    const ue1 = createNode('ue1', 'UE1', '12.1.1.2/24', centerX - 300, y, 120, 50);
    const ue2 = createNode('ue2', 'UE2', '12.1.1.3/24', centerX - 50, y, 120, 50);
    const ue3 = createNode('ue3', 'UE3', '12.1.1.4/24', centerX + 200, y, 120, 50);
    const ue4 = createNode('ue4', 'UE4', '12.1.1.5/24', centerX + 300, y, 120, 50);
    
    createLink(amf.x, amf.y + 30, n2.x, n2.y - 25, 'N2');
    createLink(smf.x, smf.y + 30, n11.x, n11.y - 25, 'N11');
    createLink(smf.x, smf.y + 30, n4.x, n4.y - 25, 'N4');
    createLink(upf.x, upf.y + 30, n3_1.x, n3_1.y - 25, 'N3');
    createLink(upf.x, upf.y + 30, n3_2.x, n3_2.y - 25, 'N3');
    
    createLink(n2.x, n2.y + 25, cu_cp.x, cu_cp.y - 30);
    createLink(n11.x, n11.y + 25, cu_cp.x, cu_cp.y - 30);
    createLink(n4.x, n4.y + 25, cu_cp.x, cu_cp.y - 30);
    createLink(cu_cp.x, cu_cp.y + 30, f1c.x, f1c.y - 25);
    createLink(cu_cp.x, cu_cp.y + 30, e1_1.x, e1_1.y - 25);
    
    createLink(e1_1.x, e1_1.y + 25, e1_2.x, e1_2.y - 25);
    createLink(e1_1.x, e1_1.y + 25, e1_3.x, e1_3.y - 25);
    createLink(n3_1.x, n3_1.y + 25, cu_up1_n3.x, cu_up1_n3.y - 25);
    createLink(n3_2.x, n3_2.y + 25, cu_up2_n3.x, cu_up2_n3.y - 25);
    
    createLink(e1_2.x, e1_2.y + 25, cu_up1.x, cu_up1.y - 30);
    createLink(cu_up1_n3.x, cu_up1_n3.y + 25, cu_up1.x, cu_up1.y - 30);
    createLink(cu_up1.x, cu_up1.y + 30, f1u_up1.x, f1u_up1.y - 25);
    
    createLink(e1_3.x, e1_3.y + 25, cu_up2.x, cu_up2.y - 30);
    createLink(cu_up2_n3.x, cu_up2_n3.y + 25, cu_up2.x, cu_up2.y - 30);
    createLink(cu_up2.x, cu_up2.y + 30, f1u_up2_1.x, f1u_up2_1.y - 25);
    createLink(cu_up2.x, cu_up2.y + 30, f1u_up2_2.x, f1u_up2_2.y - 25);
    
    createLink(f1c.x, f1c.y + 25, f1c_du1.x, f1c_du1.y - 25);
    createLink(f1c.x, f1c.y + 25, f1c_du2.x, f1c_du2.y - 25);
    createLink(f1c.x, f1c.y + 25, f1c_du3.x, f1c_du3.y - 25);
    createLink(f1u_up1.x, f1u_up1.y + 25, f1u_du1.x, f1u_du1.y - 25);
    createLink(f1u_up2_1.x, f1u_up2_1.y + 25, f1u_du2.x, f1u_du2.y - 25);
    createLink(f1u_up2_2.x, f1u_up2_2.y + 25, f1u_du3.x, f1u_du3.y - 25);
    
    createLink(f1c_du1.x, f1c_du1.y + 25, du1.x, du1.y - 30);
    createLink(f1u_du1.x, f1u_du1.y + 25, du1.x, du1.y - 30);
    createLink(f1c_du2.x, f1c_du2.y + 25, du2.x, du2.y - 30);
    createLink(f1u_du2.x, f1u_du2.y + 25, du2.x, du2.y - 30);
    createLink(f1c_du3.x, f1c_du3.y + 25, du3.x, du3.y - 30);
    createLink(f1u_du3.x, f1u_du3.y + 25, du3.x, du3.y - 30);
    
    createLink(du1.x, du1.y + 30, rfsim1.x, rfsim1.y - 25);
    createLink(du2.x, du2.y + 30, rfsim2.x, rfsim2.y - 25);
    createLink(du3.x, du3.y + 30, rfsim3.x, rfsim3.y - 25);
    
    createLink(rfsim1.x, rfsim1.y + 25, rfsim1_ue.x, rfsim1_ue.y - 25);
    createLink(rfsim2.x, rfsim2.y + 25, rfsim2_ue.x, rfsim2_ue.y - 25);
    createLink(rfsim3.x, rfsim3.y + 25, rfsim3_ue1.x, rfsim3_ue1.y - 25);
    createLink(rfsim3.x, rfsim3.y + 25, rfsim3_ue2.x, rfsim3_ue2.y - 25);
    
    createLink(rfsim1_ue.x, rfsim1_ue.y + 25, ue1.x, ue1.y - 25);
    createLink(rfsim2_ue.x, rfsim2_ue.y + 25, ue2.x, ue2.y - 25);
    createLink(rfsim3_ue1.x, rfsim3_ue1.y + 25, ue3.x, ue3.y - 25);
    createLink(rfsim3_ue2.x, rfsim3_ue2.y + 25, ue4.x, ue4.y - 25);
    
    isDrawingTopology = false;
}

let notifications = [];
let currentFilter = 'all';

function showNotification(message, type = 'info', showToast = true) {
    const timestamp = new Date();
    const notification = {
        id: Date.now(),
        message: message,
        type: type,
        timestamp: timestamp,
        read: false,
        pinned: type === 'warning' || type === 'critical',
        dismissed: false
    };
    
    notifications.unshift(notification);
    
    if (notifications.length > 50) {
        notifications = notifications.slice(0, 50);
    }
    
    updateNotificationsDisplay();
    updateNotificationBanner();
    
    if (showToast && (type === 'critical' || type === 'error')) {
        const activeTab = document.querySelector('.nav-item.active')?.dataset.tab;
        if (activeTab && activeTab !== 'overview') {
            showToastNotification(message, type);
        }
    }
}

function showToastNotification(message, type = 'info') {
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

function updateNotificationsDisplay() {
    const container = document.getElementById('notifications-container');
    if (!container) return;
    
    const active = notifications.filter(n => !n.dismissed);
    
    const filtered = currentFilter === 'all' 
        ? active 
        : active.filter(n => n.type === currentFilter);
    
    if (filtered.length === 0) {
        container.innerHTML = '<div class="no-data">No notifications</div>';
        return;
    }
    
    container.innerHTML = filtered.map(n => {
        const icons = {
            critical: 'fa-exclamation-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle',
            success: 'fa-check-circle'
        };
        
        const labels = {
            critical: 'CRITICAL',
            error: 'ERROR',
            warning: 'WARNING',
            info: 'INFO',
            success: 'SUCCESS'
        };
        
        const timeStr = n.timestamp.toLocaleTimeString();
        const dateStr = n.timestamp.toLocaleDateString();
        
        return `
            <div class="notification-item ${n.type}" data-notification-id="${n.id}">
                <div class="notification-content">
                    <i class="fas ${icons[n.type]} notification-icon"></i>
                    <div class="notification-text">
                        <div class="notification-message">${n.message}</div>
                        <div class="notification-time">${dateStr} ${timeStr}</div>
                    </div>
                </div>
                <div class="notification-actions">
                    <span class="notification-badge">${labels[n.type]}</span>
                    <button class="notification-close" onclick="removeNotification(${n.id})" title="Remove">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function filterNotifications(filter) {
    currentFilter = filter;
    
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        }
    });
    
    updateNotificationsDisplay();
    updateNotificationBanner();
}

function removeNotification(id) {
    notifications = notifications.map(n => n.id === id ? { ...n, dismissed: true, pinned: false } : n);
    updateNotificationsDisplay();
    updateNotificationBanner();
}

function clearNotifications() {
    notifications = notifications.map(n => ({ ...n, dismissed: true, pinned: false }));
    updateNotificationsDisplay();
    updateNotificationBanner();
}

function addAlert(message, type = 'info') {
    showNotification(message, type, false);
}

function updateNotificationBanner() {
    const banner = document.getElementById('notification-banner');
    if (!banner) return;
    
    const pinned = notifications.filter(n => n.pinned && !n.dismissed);
    
    if (pinned.length === 0) {
        banner.className = 'notification-banner hidden';
        banner.innerHTML = '';
        return;
    }
    
    const top = pinned[0];
    const icons = {
        critical: 'fa-exclamation-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle',
        success: 'fa-check-circle'
    };
    const labels = {
        critical: 'CRITICAL',
        error: 'ERROR',
        warning: 'WARNING',
        info: 'INFO',
        success: 'SUCCESS'
    };
    
    const timeStr = top.timestamp.toLocaleTimeString();
    const dateStr = top.timestamp.toLocaleDateString();
    
    banner.className = `notification-banner ${top.type}`;
    banner.innerHTML = `
        <div class="notification-banner-content">
            <i class="fas ${icons[top.type] || 'fa-exclamation-triangle'} notification-banner-icon"></i>
            <div>
                <div class="notification-banner-text">${top.message}</div>
                <div class="notification-banner-meta">${labels[top.type] || 'WARNING'} · ${dateStr} ${timeStr}</div>
            </div>
        </div>
        <button class="notification-close" onclick="removeNotification(${top.id})" title="Dismiss">
            <i class="fas fa-times"></i>
        </button>
    `;
}

async function updateSourceCode(category, selectedTypes) {
    if (!sourceCodeCache[category]) {
        sourceCodeCache[category] = { types: [], currentIndex: 0, data: {} };
    }
    
    const container = document.getElementById(`${category}-source-container`);
    const nav = document.getElementById(`${category}-source-nav`);
    
    if (!container || !nav) {
        console.error('Source code container or nav not found for category:', category);
        return;
    }
    
    if (sourceCodeAbortControllers[category]) {
        sourceCodeAbortControllers[category].abort();
        sourceCodeAbortControllers[category] = null;
    }
    
    if (!selectedTypes || selectedTypes.length === 0) {
        container.innerHTML = '<div class="no-data">Select type(s) to view source code</div>';
        nav.style.display = 'none';
        sourceCodeCache[category].types = [];
        sourceCodeCache[category].currentIndex = 0;
        sourceCodeCache[category].data = {};
        return;
    }
    
    const abortController = new AbortController();
    sourceCodeAbortControllers[category] = abortController;
    
    sourceCodeCache[category].types = selectedTypes;
    sourceCodeCache[category].currentIndex = 0;
    sourceCodeCache[category].data = {};
    
    container.innerHTML = '<div class="no-data">Loading source code...</div>';
    nav.style.display = 'flex';
    
    for (const type of selectedTypes) {
        if (abortController.signal.aborted) {
            console.log(`Source code loading aborted for ${category}`);
            return;
        }
        
        try {
            const response = await fetch(`/api/source/${category}/${type}`, {
                signal: abortController.signal
            });
            
            if (abortController.signal.aborted) {
                return;
            }
            
            if (response.ok) {
                const data = await response.json();
                sourceCodeCache[category].data[type] = data;
            } else {
                const errorText = await response.text();
                console.error(`Failed to load source for ${category}/${type}:`, errorText);
                sourceCodeCache[category].data[type] = { error: 'Source file not found' };
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log(`Source code fetch aborted for ${category}/${type}`);
                return;
            }
            console.error(`Error loading source for ${category}/${type}:`, error);
            if (!abortController.signal.aborted) {
                sourceCodeCache[category].data[type] = { error: error.message };
            }
        }
    }
    
    if (abortController.signal.aborted) {
        return;
    }
    
    const currentSelectedTypes = category === 'attack' ? getSelectedAttackTypes() :
                                category === 'detection' ? getSelectedDetectionTypes() :
                                getSelectedDefenseTypes();
    
    if (currentSelectedTypes.length === 0 || JSON.stringify(currentSelectedTypes.sort()) !== JSON.stringify(selectedTypes.sort())) {
        container.innerHTML = '<div class="no-data">Select type(s) to view source code</div>';
        nav.style.display = 'none';
        sourceCodeCache[category].types = [];
        sourceCodeCache[category].currentIndex = 0;
        sourceCodeCache[category].data = {};
        return;
    }
    
    displaySourceCode(category);
    sourceCodeAbortControllers[category] = null;
}

function displaySourceCode(category) {
    console.log(`displaySourceCode called for category: ${category}`);
    
    if (!sourceCodeCache[category]) {
        console.warn('Initializing sourceCodeCache for category:', category);
        sourceCodeCache[category] = { types: [], currentIndex: 0, data: {} };
    }
    
    const cache = sourceCodeCache[category];
    
    const currentSelectedTypes = category === 'attack' ? getSelectedAttackTypes() :
                                category === 'detection' ? getSelectedDetectionTypes() :
                                getSelectedDefenseTypes();
    
    if (currentSelectedTypes.length === 0) {
        const container = document.getElementById(`${category}-source-container`);
        const nav = document.getElementById(`${category}-source-nav`);
        if (container) {
            container.innerHTML = '<div class="no-data">Select type(s) to view source code</div>';
        }
        if (nav) {
            nav.style.display = 'none';
        }
        cache.types = [];
        cache.currentIndex = 0;
        cache.data = {};
        return;
    }
    
    console.log('Cache state:', {
        types: cache.types,
        currentIndex: cache.currentIndex,
        dataKeys: Object.keys(cache.data),
        currentSelected: currentSelectedTypes
    });
    
    const container = document.getElementById(`${category}-source-container`);
    const titleEl = document.getElementById(`${category}-source-title`);
    const counterEl = document.getElementById(`${category}-source-counter`);
    const prevBtn = document.getElementById(`${category}-source-prev`);
    const nextBtn = document.getElementById(`${category}-source-next`);
    
    if (!container || !titleEl || !counterEl || !prevBtn || !nextBtn) {
        console.error('Source code elements not found for category:', category, {
            container: !!container,
            titleEl: !!titleEl,
            counterEl: !!counterEl,
            prevBtn: !!prevBtn,
            nextBtn: !!nextBtn
        });
        return;
    }
    
    if (!cache.types || cache.types.length === 0) {
        console.log('No types selected');
        if (container) container.innerHTML = '<div class="no-data">Select type(s) to view source code</div>';
        return;
    }
    
    if (cache.currentIndex < 0 || cache.currentIndex >= cache.types.length) {
        console.warn('Invalid currentIndex, resetting to 0');
        cache.currentIndex = 0;
    }
    
    const currentType = cache.types[cache.currentIndex];
    console.log(`Displaying source for type: ${currentType} at index ${cache.currentIndex}`);
    const sourceData = cache.data[currentType];
    console.log('Source data:', sourceData ? 'found' : 'not found');
    
    if (sourceData && sourceData.error) {
        container.innerHTML = `<div class="no-data">Error: ${sourceData.error}</div>`;
        const displayName = currentType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        titleEl.textContent = displayName;
        counterEl.textContent = `${cache.currentIndex + 1} / ${cache.types.length}`;
        
        if (prevBtn) {
            prevBtn.disabled = cache.currentIndex === 0;
            if (cache.currentIndex === 0) {
                prevBtn.style.opacity = '0.4';
                prevBtn.style.cursor = 'not-allowed';
            } else {
                prevBtn.style.opacity = '1';
                prevBtn.style.cursor = 'pointer';
            }
        }
        if (nextBtn) {
            nextBtn.disabled = cache.currentIndex === cache.types.length - 1;
            if (cache.currentIndex === cache.types.length - 1) {
                nextBtn.style.opacity = '0.4';
                nextBtn.style.cursor = 'not-allowed';
            } else {
                nextBtn.style.opacity = '1';
                nextBtn.style.cursor = 'pointer';
            }
        }
        return;
    }
    
    if (!sourceData || !sourceData.source_code) {
        container.innerHTML = '<div class="no-data">Loading...</div>';
        return;
    }
    
    const displayName = currentType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    titleEl.textContent = displayName;
    counterEl.textContent = `${cache.currentIndex + 1} / ${cache.types.length}`;
    
    container.innerHTML = `
        <div class="source-code-header">
            <span class="source-code-file"><i class="fas fa-file-code"></i> ${sourceData.file_name}</span>
            <span class="source-code-path">${sourceData.file_path}</span>
        </div>
        <pre class="source-code-content"><code>${escapeHtml(sourceData.source_code)}</code></pre>
    `;
    
    if (prevBtn) {
        prevBtn.disabled = cache.currentIndex === 0;
        if (cache.currentIndex === 0) {
            prevBtn.style.opacity = '0.4';
            prevBtn.style.cursor = 'not-allowed';
        } else {
            prevBtn.style.opacity = '1';
            prevBtn.style.cursor = 'pointer';
        }
    }
    if (nextBtn) {
        nextBtn.disabled = cache.currentIndex === cache.types.length - 1;
        if (cache.currentIndex === cache.types.length - 1) {
            nextBtn.style.opacity = '0.4';
            nextBtn.style.cursor = 'not-allowed';
        } else {
            nextBtn.style.opacity = '1';
            nextBtn.style.cursor = 'pointer';
        }
    }
}

function navigateSourceCode(category, direction) {
    console.log(`navigateSourceCode called: category=${category}, direction=${direction}`);
    
    if (!sourceCodeCache[category]) {
        console.error('Source code cache not initialized for category:', category);
        sourceCodeCache[category] = { types: [], currentIndex: 0, data: {} };
        return;
    }
    
    const cache = sourceCodeCache[category];
    
    if (!cache.types || cache.types.length === 0) {
        console.warn('No types available for navigation', cache);
        return;
    }
    
    console.log(`Before navigation: currentIndex=${cache.currentIndex}, types.length=${cache.types.length}, types=`, cache.types);
    
    if (direction === 'prev' && cache.currentIndex > 0) {
        cache.currentIndex--;
        console.log(`Navigating to previous: new index=${cache.currentIndex}`);
        displaySourceCode(category);
    } else if (direction === 'next' && cache.currentIndex < cache.types.length - 1) {
        cache.currentIndex++;
        console.log(`Navigating to next: new index=${cache.currentIndex}`);
        displaySourceCode(category);
    } else {
        console.log(`Cannot navigate ${direction} - at boundary. Current index: ${cache.currentIndex}, Total: ${cache.types.length}`);
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

document.addEventListener('change', (e) => {
    if (e.target.name === 'attack-type') {
        updateAttackParams();
    } else if (e.target.id === 'attack-target' || e.target.id === 'attack-mode' || e.target.closest('#attack-params-container')) {
        updateAttackCommand();
    }
    
    if (e.target.name === 'detection-type') {
        updateDetectionParams();
    }
    
    if (e.target.name === 'defense-type') {
        updateDefenseParams();
    }
});

function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    
    if (!themeToggle || !themeIcon) return;
    
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme, themeIcon);
    
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme, themeIcon);
    });
}

function updateThemeIcon(theme, iconElement) {
    if (theme === 'dark') {
        iconElement.className = 'fas fa-moon';
    } else {
        iconElement.className = 'fas fa-sun';
    }
}


