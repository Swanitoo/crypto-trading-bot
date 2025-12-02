// Dashboard JavaScript
let balanceChart = null;
let modalChart = null;
let updateInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    loadAllData();
    startAutoRefresh();
    setupEventListeners();
    setupModalListeners();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('startBtn').addEventListener('click', () => startBot());
    document.getElementById('pauseBtn').addEventListener('click', () => pauseBot());
    document.getElementById('stopBtn').addEventListener('click', () => stopBot());

    // AI Interval Slider
    const slider = document.getElementById('aiIntervalSlider');
    const valueDisplay = document.getElementById('aiIntervalValue');

    slider.addEventListener('input', (e) => {
        const seconds = parseInt(e.target.value);
        valueDisplay.textContent = formatInterval(seconds);
    });

    slider.addEventListener('change', async (e) => {
        const seconds = parseInt(e.target.value);
        await updateAIInterval(seconds);
    });

    // Load current AI interval on startup
    loadCurrentAIInterval();
}

// Format interval display
function formatInterval(seconds) {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) {
        const minutes = seconds / 60;
        return minutes === 1 ? '1 min' : `${Math.floor(minutes)} min`;
    }
    const hours = seconds / 3600;
    return hours === 1 ? '1h' : `${hours}h`;
}

// Update AI analysis interval
async function updateAIInterval(seconds) {
    try {
        const response = await fetch('/api/config/ai-interval', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ interval: seconds })
        });

        if (response.ok) {
            console.log(`AI interval updated to ${formatInterval(seconds)}`);
            showNotification(`AI analysis interval set to ${formatInterval(seconds)}`, 'success');
        } else {
            throw new Error('Failed to update AI interval');
        }
    } catch (error) {
        console.error('Error updating AI interval:', error);
        showNotification('Failed to update AI interval', 'error');
    }
}

// Load current AI interval
async function loadCurrentAIInterval() {
    try {
        const response = await fetch('/api/config/ai-interval');
        if (response.ok) {
            const data = await response.json();
            const slider = document.getElementById('aiIntervalSlider');
            const valueDisplay = document.getElementById('aiIntervalValue');
            slider.value = data.interval;
            valueDisplay.textContent = formatInterval(data.interval);
        }
    } catch (error) {
        console.error('Error loading AI interval:', error);
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple console log for now, can be enhanced with toast notifications
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Start auto-refresh
function startAutoRefresh() {
    updateInterval = setInterval(() => {
        loadAllData();
    }, 10000); // Refresh every 10 seconds (optimisé)
}

// Load all data
async function loadAllData() {
    try {
        await Promise.all([
            loadBalance(),
            loadTrades(),
            loadPositions(),
            loadAIAnalysis(),
            loadPerformance(),
            loadBotStatus(),
            loadMarketOverview(),
            loadLivePnL()
        ]);
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Load bot status
async function loadBotStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        const statusBadge = document.getElementById('botStatus');

        if (data.running && !data.paused) {
            statusBadge.textContent = 'Running';
            statusBadge.className = 'status-badge running';
        } else if (data.paused) {
            statusBadge.textContent = 'Paused';
            statusBadge.className = 'status-badge paused';
        } else {
            statusBadge.textContent = 'Stopped';
            statusBadge.className = 'status-badge';
        }

        // Update risk metrics
        if (data.risk_metrics) {
            document.getElementById('openPositions').textContent = data.risk_metrics.open_positions;
            document.getElementById('dailyLoss').textContent = data.risk_metrics.daily_losses.toFixed(2) + '%';
        }
    } catch (error) {
        console.error('Error loading bot status:', error);
    }
}

// Load balance
async function loadBalance() {
    try {
        const response = await fetch('/api/balance');
        const data = await response.json();

        document.getElementById('totalBalance').textContent = data.total_balance.toFixed(2);
        document.getElementById('availableBalance').textContent = data.available_balance.toFixed(2);
        document.getElementById('inPositions').textContent = data.in_positions.toFixed(2);

        // P&L
        const pnl = data.total_profit_loss;
        const pnlPercent = data.total_profit_loss_percent;

        document.getElementById('totalPnL').textContent = Math.abs(pnl).toFixed(2);
        document.getElementById('pnlPercent').textContent = (pnl >= 0 ? '+' : '-') + Math.abs(pnlPercent).toFixed(2) + '%';

        const pnlValue = document.getElementById('pnlValue');
        const pnlPercentEl = document.getElementById('pnlPercent');

        if (pnl >= 0) {
            pnlValue.classList.add('positive');
            pnlValue.classList.remove('negative');
            pnlPercentEl.classList.add('positive');
            pnlPercentEl.classList.remove('negative');
        } else {
            pnlValue.classList.add('negative');
            pnlValue.classList.remove('positive');
            pnlPercentEl.classList.add('negative');
            pnlPercentEl.classList.remove('positive');
        }

        // Stats
        document.getElementById('totalTrades').textContent = data.total_trades;
        document.getElementById('winRate').textContent = data.win_rate.toFixed(1) + '%';

    } catch (error) {
        console.error('Error loading balance:', error);
    }
}

// Load trades
async function loadTrades() {
    try {
        const response = await fetch('/api/trades?limit=20');
        const trades = await response.json();

        const tbody = document.getElementById('tradesTableBody');

        if (trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No trades yet</td></tr>';
            return;
        }

        tbody.innerHTML = trades.map(trade => {
            const time = new Date(trade.timestamp).toLocaleString();
            const sideClass = trade.side === 'buy' ? 'trade-side-buy' : 'trade-side-sell';
            const pnlClass = trade.profit_loss >= 0 ? 'trade-pnl-positive' : 'trade-pnl-negative';
            const statusClass = trade.status === 'open' ? 'trade-status-open' : 'trade-status-closed';

            return `
                <tr>
                    <td>${time}</td>
                    <td><strong>${trade.pair}</strong></td>
                    <td class="${sideClass}">${trade.side.toUpperCase()}</td>
                    <td>$${trade.price.toFixed(2)}</td>
                    <td>${trade.amount.toFixed(6)}</td>
                    <td class="${pnlClass}">
                        ${trade.profit_loss >= 0 ? '+' : ''}$${trade.profit_loss.toFixed(2)}
                        (${trade.profit_loss_percent >= 0 ? '+' : ''}${trade.profit_loss_percent.toFixed(2)}%)
                    </td>
                    <td><span class="trade-status ${statusClass}">${trade.status}</span></td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading trades:', error);
    }
}

// Load positions
async function loadPositions() {
    try {
        const response = await fetch('/api/positions');
        const positions = await response.json();

        const container = document.getElementById('positionsList');

        if (positions.length === 0) {
            container.innerHTML = '<p class="empty-state">No open positions</p>';
            return;
        }

        container.innerHTML = positions.map(pos => {
            const pnlClass = pos.profit_loss >= 0 ? 'profit' : 'loss';

            return `
                <div class="position-item ${pnlClass}">
                    <div>
                        <div class="position-label">Pair</div>
                        <div class="position-value">${pos.pair}</div>
                    </div>
                    <div>
                        <div class="position-label">Entry</div>
                        <div class="position-value">$${pos.entry_price.toFixed(2)}</div>
                    </div>
                    <div>
                        <div class="position-label">Current</div>
                        <div class="position-value">$${pos.current_price ? pos.current_price.toFixed(2) : pos.entry_price.toFixed(2)}</div>
                    </div>
                    <div>
                        <div class="position-label">P&L</div>
                        <div class="position-value ${pos.profit_loss >= 0 ? 'trade-pnl-positive' : 'trade-pnl-negative'}">
                            ${pos.profit_loss >= 0 ? '+' : ''}$${pos.profit_loss.toFixed(2)}
                        </div>
                    </div>
                    <div>
                        <div class="position-label">P&L %</div>
                        <div class="position-value ${pos.profit_loss_percent >= 0 ? 'trade-pnl-positive' : 'trade-pnl-negative'}">
                            ${pos.profit_loss_percent >= 0 ? '+' : ''}${pos.profit_loss_percent.toFixed(2)}%
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading positions:', error);
    }
}

// Load AI analysis
async function loadAIAnalysis() {
    try {
        const response = await fetch('/api/ai_analysis?limit=5');
        const analyses = await response.json();

        const container = document.getElementById('aiAnalysisList');

        if (analyses.length === 0) {
            container.innerHTML = '<p class="empty-state">No AI analysis yet</p>';
            return;
        }

        container.innerHTML = analyses.map(analysis => {
            const recClass = analysis.recommendation;
            const time = new Date(analysis.timestamp).toLocaleString();

            return `
                <div class="ai-item ${recClass}">
                    <div class="ai-header">
                        <span class="ai-pair">${analysis.pair}</span>
                        <span class="ai-confidence">${analysis.confidence.toFixed(0)}% confidence</span>
                    </div>
                    <div class="ai-recommendation ${recClass}">
                        ${analysis.recommendation.toUpperCase()}
                    </div>
                    <div class="ai-reasoning">${analysis.reasoning}</div>
                    <div class="ai-timestamp">${time}</div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading AI analysis:', error);
    }
}

// Load performance and update chart
async function loadPerformance() {
    try {
        const response = await fetch('/api/performance');
        const data = await response.json();

        if (data.balance_history && data.balance_history.length > 0) {
            updateBalanceChart(data.balance_history);
        }

    } catch (error) {
        console.error('Error loading performance:', error);
    }
}

// Load market overview
async function loadMarketOverview() {
    try {
        const response = await fetch('/api/market_overview');
        const markets = await response.json();

        const container = document.getElementById('marketOverview');

        if (!markets || markets.length === 0 || markets.error) {
            container.innerHTML = '<p class="empty-state">Données de marché indisponibles</p>';
            return;
        }

        container.innerHTML = markets.map(market => {
            const changeClass = market.change_24h >= 0 ? 'positive' : 'negative';
            const changeSign = market.change_24h >= 0 ? '+' : '';

            return `
                <div class="market-item" onclick="openChartModal('${market.pair}')">
                    <div>
                        <div class="market-pair">${market.pair}</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="market-price">$${market.price.toLocaleString('fr-FR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                        <div class="market-change ${changeClass}">
                            ${changeSign}${market.change_24h.toFixed(2)}%
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading market overview:', error);
        const container = document.getElementById('marketOverview');
        container.innerHTML = '<p class="empty-state">Erreur de chargement</p>';
    }
}

// Initialize chart
function initializeChart() {
    const ctx = document.getElementById('balanceChart').getContext('2d');

    balanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Balance',
                data: [],
                borderColor: '#1da1f2',
                backgroundColor: 'rgba(29, 161, 242, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#38444d'
                    },
                    ticks: {
                        color: '#8899a6'
                    }
                },
                y: {
                    grid: {
                        color: '#38444d'
                    },
                    ticks: {
                        color: '#8899a6',
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

// Update balance chart
function updateBalanceChart(balanceHistory) {
    const labels = balanceHistory.map(b => {
        const date = new Date(b.timestamp);
        return date.toLocaleTimeString();
    });

    const data = balanceHistory.map(b => b.balance);

    balanceChart.data.labels = labels;
    balanceChart.data.datasets[0].data = data;
    balanceChart.update();
}

// Load live P&L
async function loadLivePnL() {
    try {
        const response = await fetch('/api/live_pnl');
        const data = await response.json();

        // Update total P&L
        const pnlAmount = document.getElementById('livePnLAmount');
        const pnlPercent = document.getElementById('livePnLPercent');
        const pnlValue = document.getElementById('livePnLValue');
        const pnlCount = document.getElementById('livePnLCount');

        pnlAmount.textContent = Math.abs(data.total_pnl).toFixed(2);

        const sign = data.total_pnl >= 0 ? '+' : '-';
        pnlPercent.textContent = sign + Math.abs(data.total_pnl_percent).toFixed(2) + '%';

        // Update colors
        if (data.total_pnl >= 0) {
            pnlValue.classList.add('positive');
            pnlValue.classList.remove('negative');
            pnlPercent.classList.add('positive');
            pnlPercent.classList.remove('negative');
        } else {
            pnlValue.classList.add('negative');
            pnlValue.classList.remove('positive');
            pnlPercent.classList.add('negative');
            pnlPercent.classList.remove('positive');
        }

        pnlCount.textContent = data.position_count;

        // Update individual positions
        const container = document.getElementById('livePnLPositions');

        if (data.positions.length === 0) {
            container.innerHTML = '<p class="empty-state">Aucune position ouverte</p>';
            return;
        }

        container.innerHTML = data.positions.map(pos => {
            const pnlClass = pos.profit_loss >= 0 ? 'profit' : 'loss';
            const pnlSign = pos.profit_loss >= 0 ? '+' : '';

            return `
                <div class="live-pnl-position ${pnlClass}">
                    <div class="live-pnl-position-header">
                        <div class="live-pnl-position-pair">${pos.pair}</div>
                        <div class="live-pnl-position-pnl ${pnlClass}">
                            ${pnlSign}$${pos.profit_loss.toFixed(2)}
                            <span style="font-size: 0.9rem;">(${pnlSign}${pos.profit_loss_percent.toFixed(2)}%)</span>
                        </div>
                    </div>
                    <div class="live-pnl-position-details">
                        <div class="live-pnl-position-detail">
                            <div class="live-pnl-position-detail-label">Prix d'entrée</div>
                            <div class="live-pnl-position-detail-value">$${pos.entry_price.toFixed(2)}</div>
                        </div>
                        <div class="live-pnl-position-detail">
                            <div class="live-pnl-position-detail-label">Prix actuel</div>
                            <div class="live-pnl-position-detail-value">$${pos.current_price.toFixed(2)}</div>
                        </div>
                        <div class="live-pnl-position-detail">
                            <div class="live-pnl-position-detail-label">Stop Loss</div>
                            <div class="live-pnl-position-detail-value" style="color: var(--danger);">$${pos.stop_loss ? pos.stop_loss.toFixed(2) : 'N/A'}</div>
                        </div>
                        <div class="live-pnl-position-detail">
                            <div class="live-pnl-position-detail-label">Take Profit</div>
                            <div class="live-pnl-position-detail-value" style="color: var(--success);">$${pos.take_profit ? pos.take_profit.toFixed(2) : 'N/A'}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading live P&L:', error);
    }
}

// Setup modal listeners
function setupModalListeners() {
    const modal = document.getElementById('chartModal');
    const closeBtn = document.querySelector('.modal-close');

    if (!modal || !closeBtn) {
        console.error('Modal elements not found');
        return;
    }

    // Close modal on X click
    closeBtn.addEventListener('click', function() {
        closeChartModal();
    });

    // Close modal on outside click
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeChartModal();
        }
    });

    // Close modal on ESC key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.classList.contains('show')) {
            closeChartModal();
        }
    });
}

// Open chart modal
async function openChartModal(pair) {
    try {
        const modal = document.getElementById('chartModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalPositionInfo = document.getElementById('modalPositionInfo');

        // Show modal
        modal.classList.add('show');
        modalTitle.textContent = `📊 ${pair}`;

        // Show loading
        modalPositionInfo.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Chargement...</p>';

        // Convert pair format for URL (BTC/USDT -> BTC-USDT)
        const pairUrl = pair.replace('/', '-');

        const response = await fetch(`/api/pair_chart/${pairUrl}`);
        const data = await response.json();

        if (data.error) {
            console.error(`Error loading chart for ${pair}:`, data.error);
            closeChartModal();
            return;
        }

        // Display position info if exists
        if (data.position) {
            const pnlClass = data.position.profit_loss >= 0 ? 'positive' : 'negative';
            const pnlSign = data.position.profit_loss >= 0 ? '+' : '';

            modalPositionInfo.innerHTML = `
                <div class="modal-position-info-item">
                    <div class="modal-position-info-label">P&L</div>
                    <div class="modal-position-info-value" style="color: var(--${pnlClass === 'positive' ? 'success' : 'danger'});">
                        ${pnlSign}$${data.position.profit_loss.toFixed(2)} (${pnlSign}${data.position.profit_loss_percent.toFixed(2)}%)
                    </div>
                </div>
                <div class="modal-position-info-item">
                    <div class="modal-position-info-label">Prix d'entrée</div>
                    <div class="modal-position-info-value">$${data.position.entry_price.toFixed(2)}</div>
                </div>
                <div class="modal-position-info-item">
                    <div class="modal-position-info-label">Prix actuel</div>
                    <div class="modal-position-info-value">$${data.position.current_price ? data.position.current_price.toFixed(2) : data.position.entry_price.toFixed(2)}</div>
                </div>
                <div class="modal-position-info-item">
                    <div class="modal-position-info-label">Stop Loss</div>
                    <div class="modal-position-info-value" style="color: var(--danger);">$${data.position.stop_loss ? data.position.stop_loss.toFixed(2) : 'N/A'}</div>
                </div>
                <div class="modal-position-info-item">
                    <div class="modal-position-info-label">Take Profit</div>
                    <div class="modal-position-info-value" style="color: var(--success);">$${data.position.take_profit ? data.position.take_profit.toFixed(2) : 'N/A'}</div>
                </div>
            `;
        } else {
            modalPositionInfo.innerHTML = `<p style="text-align: center; color: var(--text-secondary);">Aucune position ouverte sur ${pair}</p>`;
        }

        // Prepare chart data
        const labels = data.candles.map(c => {
            const date = new Date(c.timestamp);
            return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
        });
        const prices = data.candles.map(c => c.close);

        // Prepare entry/exit markers
        const entryPoints = [];
        const exitPoints = [];

        data.trades.forEach(trade => {
            const tradeDate = new Date(trade.timestamp);
            const index = data.candles.findIndex(c => new Date(c.timestamp) >= tradeDate);

            if (index !== -1) {
                if (trade.type === 'entry') {
                    entryPoints.push({ x: index, y: trade.price });
                } else if (trade.type === 'exit') {
                    exitPoints.push({ x: index, y: trade.price });
                }
            }
        });

        // Prepare datasets
        const datasets = [
            {
                label: 'Prix',
                data: prices,
                borderColor: '#1da1f2',
                backgroundColor: 'rgba(29, 161, 242, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                pointRadius: 0
            }
        ];

        // Add entry markers
        if (entryPoints.length > 0) {
            const entryData = new Array(prices.length).fill(null);
            entryPoints.forEach(point => {
                entryData[point.x] = point.y;
            });
            datasets.push({
                label: 'Entrée',
                data: entryData,
                borderColor: '#00ba88',
                backgroundColor: '#00ba88',
                pointStyle: 'circle',
                pointRadius: 8,
                pointHoverRadius: 10,
                showLine: false
            });
        }

        // Add exit markers
        if (exitPoints.length > 0) {
            const exitData = new Array(prices.length).fill(null);
            exitPoints.forEach(point => {
                exitData[point.x] = point.y;
            });
            datasets.push({
                label: 'Sortie',
                data: exitData,
                borderColor: '#f6465d',
                backgroundColor: '#f6465d',
                pointStyle: 'circle',
                pointRadius: 8,
                pointHoverRadius: 10,
                showLine: false
            });
        }

        // Add SL/TP lines if position exists
        if (data.position) {
            if (data.position.stop_loss) {
                datasets.push({
                    label: 'Stop Loss',
                    data: new Array(prices.length).fill(data.position.stop_loss),
                    borderColor: '#f6465d',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                });
            }
            if (data.position.take_profit) {
                datasets.push({
                    label: 'Take Profit',
                    data: new Array(prices.length).fill(data.position.take_profit),
                    borderColor: '#00ba88',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                });
            }
        }

        // Destroy existing chart if exists
        if (modalChart) {
            modalChart.destroy();
        }

        // Create chart
        const ctx = document.getElementById('modalChart').getContext('2d');
        modalChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += '$' + context.parsed.y.toFixed(2);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#38444d'
                        },
                        ticks: {
                            color: '#8899a6',
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        grid: {
                            color: '#38444d'
                        },
                        ticks: {
                            color: '#8899a6',
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

    } catch (error) {
        console.error(`Error opening chart modal for ${pair}:`, error);
        closeChartModal();
    }
}

// Close chart modal
function closeChartModal() {
    const modal = document.getElementById('chartModal');
    modal.classList.remove('show');

    // Destroy chart when closing
    if (modalChart) {
        modalChart.destroy();
        modalChart = null;
    }
}

// Bot control functions
async function startBot() {
    try {
        const response = await fetch('/api/bot/start', { method: 'POST' });
        const data = await response.json();
        console.log(data.message);
        loadBotStatus();
    } catch (error) {
        console.error('Error starting bot:', error);
    }
}

async function pauseBot() {
    try {
        const response = await fetch('/api/bot/pause', { method: 'POST' });
        const data = await response.json();
        console.log(data.message);
        loadBotStatus();
    } catch (error) {
        console.error('Error pausing bot:', error);
    }
}

async function stopBot() {
    try {
        const response = await fetch('/api/bot/stop', { method: 'POST' });
        const data = await response.json();
        console.log(data.message);
        loadBotStatus();
    } catch (error) {
        console.error('Error stopping bot:', error);
    }
}
