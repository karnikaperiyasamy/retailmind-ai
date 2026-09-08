/**
 * RetailMind AI — Client-Side Application Engine
 * Handles tabs, KPI rendering, charts, attention center, product catalog,
 * store comparison, and the interactive Grounded AI Copilot stream.
 */

// Global State
let appData = {
    dashboard: null,
    attention: null,
    products: [],
    stores: [],
    health: null
};

let charts = {
    salesTrend: null,
    category: null,
    topProducts: null,
    store: null
};

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initApp();
});

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // Attention filters
    const attFilters = document.querySelectorAll('.att-filter-btn');
    attFilters.forEach(btn => {
        btn.addEventListener('click', () => {
            attFilters.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.getAttribute('data-filter');
            renderAttentionItems(filter);
        });
    });
}

function switchTab(tabId) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const activeNav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    if (activeNav) activeNav.classList.add('active');

    // Update panes
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
    const targetPane = document.getElementById(`tab-${tabId}`);
    if (targetPane) targetPane.classList.add('active');

    // Update titles
    const titleEl = document.getElementById('page-title');
    const subtitleEl = document.getElementById('page-subtitle');
    
    if (tabId === 'dashboard') {
        titleEl.textContent = 'Executive Dashboard';
        subtitleEl.textContent = 'Real-time sales velocity, inventory risks, and verifiable intelligence';
    } else if (tabId === 'attention') {
        titleEl.textContent = 'Needs Attention Today';
        subtitleEl.textContent = 'Immediate operational alerts requiring store manager evaluation';
    } else if (tabId === 'copilot') {
        titleEl.textContent = 'RetailMind AI Copilot';
        subtitleEl.textContent = 'Ask plain-language questions backed by verified calculations & traceable evidence';
    } else if (tabId === 'products') {
        titleEl.textContent = 'Product Catalogue & Inventory Health';
        subtitleEl.textContent = 'Complete SKU velocity, stock levels, and replenishment status';
    } else if (tabId === 'stores') {
        titleEl.textContent = 'Store Network Operations';
        subtitleEl.textContent = 'Cross-store sales benchmarks and comparative performance';
    }
}

async function initApp() {
    await fetchHealth();
    await fetchDashboard();
    await fetchAttention();
    await fetchProducts();
    await fetchStores();
}

// 1. Health & Status Check
async function fetchHealth() {
    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        appData.health = data;

        const statusText = document.getElementById('gemini-status-text');
        const pill = document.getElementById('system-status-pill');
        const ind = pill.querySelector('.status-indicator');

        if (data.gemini_available) {
            statusText.textContent = 'Gemini Active';
            ind.style.backgroundColor = '#10B981';
            ind.style.boxShadow = '0 0 8px #10B981';
        } else if (data.groq_available) {
            statusText.textContent = 'Groq Active';
            ind.style.backgroundColor = '#10B981';
            ind.style.boxShadow = '0 0 8px #10B981';
        } else {
            statusText.textContent = 'Deterministic Active';
            ind.style.backgroundColor = '#F59E0B';
            ind.style.boxShadow = '0 0 8px #F59E0B';
        }
    } catch (e) {
        console.warn('Health check fallback:', e);
        document.getElementById('gemini-status-text').textContent = 'Deterministic Mode';
    }
}

// 2. Fetch Dashboard & KPIs
async function fetchDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        if (!data.success) return;
        appData.dashboard = data;

        const m = data.metrics;
        document.getElementById('kpi-total-sales').textContent = `₹${m.total_sales_30d.toLocaleString('en-IN')}`;
        document.getElementById('kpi-units-sold').textContent = `${m.total_units_sold_30d.toLocaleString('en-IN')} units`;
        document.getElementById('kpi-total-stock').textContent = `${m.total_current_stock.toLocaleString('en-IN')} units`;
        document.getElementById('kpi-stock-val').textContent = `₹${m.inventory_retail_valuation.toLocaleString('en-IN')}`;
        document.getElementById('kpi-margin').textContent = `${m.gross_margin_pct}%`;
        document.getElementById('kpi-stockouts').textContent = `${m.stockout_risks_count} SKUs`;
        document.getElementById('kpi-overstock').textContent = `${m.overstocked_count} SKUs`;
        document.getElementById('kpi-alerts').textContent = `${m.sales_alerts_count} items`;

        renderDashboardCharts(data);
    } catch (e) {
        console.error('Error fetching dashboard:', e);
    }
}

// 3. Render Dashboard Charts (using Chart.js if available, with pure SVG fallback)
function renderDashboardCharts(data) {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded, rendering lightweight SVG visual graphs.');
        renderSvgFallbacks(data);
        return;
    }

    Chart.defaults.color = '#9CA3AF';
    Chart.defaults.font.family = 'Inter, sans-serif';

    // Chart 1: 90-day Sales Trend
    const ctxTrend = document.getElementById('salesTrendChart');
    if (ctxTrend && data.sales_trend_90d) {
        if (charts.salesTrend) charts.salesTrend.destroy();
        const labels = data.sales_trend_90d.map(d => d.date_str.slice(5)); // MM-DD
        const revenues = data.sales_trend_90d.map(d => d.revenue);

        charts.salesTrend = new Chart(ctxTrend, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Daily Gross Revenue (₹)',
                    data: revenues,
                    borderColor: '#6366F1',
                    backgroundColor: 'rgba(99, 102, 241, 0.12)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `Revenue: ₹${ctx.parsed.y.toLocaleString('en-IN')}`
                        }
                    }
                },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.04)' } },
                    y: { 
                        grid: { color: 'rgba(255,255,255,0.06)' },
                        ticks: {
                            callback: (val) => `₹${(val / 1000).toFixed(0)}k`
                        }
                    }
                }
            }
        });
    }

    // Chart 2: Category Breakdown
    const ctxCat = document.getElementById('categoryChart');
    if (ctxCat && data.category_performance) {
        if (charts.category) charts.category.destroy();
        charts.category = new Chart(ctxCat, {
            type: 'doughnut',
            data: {
                labels: data.category_performance.map(c => c.category),
                datasets: [{
                    data: data.category_performance.map(c => c.revenue_30d),
                    backgroundColor: ['#4F46E5', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6', '#06B6D4'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } }
                }
            }
        });
    }

    // Chart 3: Top 5 Products
    const ctxTop = document.getElementById('topProductsChart');
    if (ctxTop && data.top_products) {
        if (charts.topProducts) charts.topProducts.destroy();
        charts.topProducts = new Chart(ctxTop, {
            type: 'bar',
            data: {
                labels: data.top_products.map(p => p.product_name.length > 18 ? p.product_name.slice(0, 18) + '...' : p.product_name),
                datasets: [{
                    label: '30-Day Sales (₹)',
                    data: data.top_products.map(p => p.revenue_30d),
                    backgroundColor: '#3B82F6',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { grid: { display: false } }
                }
            }
        });
    }

    // Chart 4: Store Distribution
    const ctxStore = document.getElementById('storeChart');
    if (ctxStore && data.store_performance) {
        if (charts.store) charts.store.destroy();
        charts.store = new Chart(ctxStore, {
            type: 'bar',
            data: {
                labels: data.store_performance.map(s => s.store_name),
                datasets: [{
                    label: 'Revenue (₹)',
                    data: data.store_performance.map(s => s.revenue_30d),
                    backgroundColor: ['#6366F1', '#10B981', '#F59E0B'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }
}

// Resilient SVG fallback when Chart.js CDN is unavailable
function renderSvgFallbacks(data) {
    const trendWrap = document.getElementById('salesTrendChart')?.parentElement;
    if (trendWrap && data.sales_trend_90d) {
        const trend = data.sales_trend_90d;
        const maxVal = Math.max(...trend.map(d => d.revenue));
        const pts = trend.map((d, i) => {
            const x = (i / (trend.length - 1)) * 500;
            const y = 140 - (d.revenue / maxVal) * 110;
            return `${x},${y}`;
        }).join(' ');
        trendWrap.innerHTML = `
            <svg viewBox="0 0 500 160" style="width:100%; height:100%; overflow:visible;">
                <polyline fill="none" stroke="#6366F1" stroke-width="2.5" points="${pts}"/>
                <text x="10" y="20" fill="#9CA3AF" font-size="11">Peak: ₹${Math.round(maxVal).toLocaleString('en-IN')}</text>
                <text x="10" y="155" fill="#6B7280" font-size="10">90-Day Trendline (SVG Fallback Active)</text>
            </svg>
        `;
    }
}

// 4. Fetch Attention Center Data
async function fetchAttention() {
    try {
        const res = await fetch('/api/attention');
        const data = await res.json();
        if (!data.success) return;
        appData.attention = data;

        const s = data.summary;
        document.getElementById('nav-alert-badge').textContent = s.total_alerts;
        document.getElementById('count-all-att').textContent = s.total_alerts;
        document.getElementById('count-stockouts-att').textContent = s.stockout_risk_count;
        document.getElementById('count-overstock-att').textContent = s.overstock_count;
        document.getElementById('count-slow-att').textContent = s.slow_moving_count;
        document.getElementById('count-spikes-att').textContent = s.sales_spikes_count;
        document.getElementById('count-drops-att').textContent = s.sales_drops_count;

        renderAttentionItems('all');
    } catch (e) {
        console.error('Error fetching attention:', e);
    }
}

// Render dynamic attention cards with 4-part grounded sections
function renderAttentionItems(filter) {
    const container = document.getElementById('attention-items-container');
    if (!container || !appData.attention) return;

    let items = [];

    if (filter === 'all' || filter === 'stockouts') {
        (appData.attention.stockouts || []).forEach(item => {
            items.push({
                kind: 'stockout',
                cssClass: 'att-stockout',
                badgeText: 'Stock-Out Risk',
                badgeClass: 'status-stockout',
                title: `${item.product_name} (${item.product_id})`,
                store: item.store_name,
                data: `Current Stock: ${item.current_stock} units | 7d Velocity: ${item.average_daily_sales} units/day | Reorder Threshold: ${item.reorder_level} units`,
                calc: item.calculation,
                assume: item.assumption,
                rec: item.recommendation,
                action: item.action,
                raw: item
            });
        });
    }

    if (filter === 'all' || filter === 'overstock') {
        (appData.attention.overstocked || []).forEach(item => {
            items.push({
                kind: 'overstock',
                cssClass: 'att-overstock',
                badgeText: 'Overstocked',
                badgeClass: 'status-overstock',
                title: `${item.product_name} (${item.product_id})`,
                store: item.store_name,
                data: `Current Stock: ${item.current_stock} units | Days of Inventory: ${item.days_of_inventory.toFixed(1)} days | Excess: ${item.estimated_excess_units} units | Tied Capital: ₹${item.tied_up_capital.toLocaleString('en-IN')}`,
                calc: item.calculation,
                assume: item.assumption,
                rec: item.recommendation,
                action: item.action,
                raw: item
            });
        });
    }

    if (filter === 'all' || filter === 'slow') {
        (appData.attention.slow_moving || []).forEach(item => {
            items.push({
                kind: 'slow',
                cssClass: 'att-slow',
                badgeText: 'Slow Moving',
                badgeClass: 'status-slow',
                title: `${item.product_name} (${item.product_id})`,
                store: item.store_name,
                data: `Units Sold (60d): ${item.units_sold} units | Stock Holding: ${item.current_inventory} units | Locked Capital: ₹${item.capital_locked.toLocaleString('en-IN')}`,
                calc: item.calculation,
                assume: item.assumption,
                rec: item.recommendation,
                action: item.reason,
                raw: item
            });
        });
    }

    if (filter === 'all' || filter === 'spikes') {
        (appData.attention.spikes || []).forEach(item => {
            items.push({
                kind: 'spike',
                cssClass: 'att-spike',
                badgeText: `Sales Surge (+${item.percentage_change}%)`,
                badgeClass: 'status-healthy',
                title: `${item.product_name} (${item.product_id})`,
                store: item.store_name,
                data: `Recent 7d Daily Avg: ${item.recent_average} units/day | Baseline 30d Avg: ${item.baseline_average} units/day`,
                calc: item.calculation,
                assume: item.assumption,
                rec: item.recommendation,
                action: 'Check supplier inventory to sustain surge demand without stockout.',
                raw: item
            });
        });
    }

    if (filter === 'all' || filter === 'drops') {
        (appData.attention.drops || []).forEach(item => {
            items.push({
                kind: 'drop',
                cssClass: 'att-drop',
                badgeText: `Sales Drop (${item.percentage_change}%)`,
                badgeClass: 'status-stockout',
                title: `${item.product_name} (${item.product_id})`,
                store: item.store_name,
                data: `Recent 7d Daily Avg: ${item.recent_average} units/day | Baseline 30d Avg: ${item.baseline_average} units/day`,
                calc: item.calculation,
                assume: item.assumption,
                rec: item.recommendation,
                action: 'Inspect on-shelf availability and pause upcoming automated restocks.',
                raw: item
            });
        });
    }

    if (items.length === 0) {
        container.innerHTML = `<div class="kpi-card"><p>No alerts in this category.</p></div>`;
        return;
    }

    container.innerHTML = items.map((item, idx) => `
        <div class="att-card ${item.cssClass}">
            <div class="att-header">
                <div class="att-title-group">
                    <span class="status-pill-badge ${item.badgeClass}">${item.badgeText}</span>
                    <span class="att-title">${item.title}</span>
                </div>
                <span class="att-store-tag">${item.store}</span>
            </div>

            <!-- Grounded 4-Part Block -->
            <div class="grounded-sections">
                <div class="g-box">
                    <div class="g-label g-label-data">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                        DATA (Raw Verified Facts)
                    </div>
                    <div class="g-content">${item.data}</div>
                </div>

                <div class="g-box">
                    <div class="g-label g-label-calc">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="4" y="2" width="16" height="20" rx="2"></rect><line x1="8" y1="6" x2="16" y2="6"></line><line x1="16" y1="14" x2="16" y2="18"></line><path d="M16 10h.01"></path><path d="M12 10h.01"></path><path d="M8 10h.01"></path><path d="M12 14h.01"></path><path d="M8 14h.01"></path><path d="M12 18h.01"></path><path d="M8 18h.01"></path></svg>
                        CALCULATION
                    </div>
                    <div class="g-content"><span class="g-calc-code">${item.calc}</span></div>
                </div>

                <div class="g-box">
                    <div class="g-label g-label-assume">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                        ASSUMPTION
                    </div>
                    <div class="g-content">${item.assume}</div>
                </div>

                <div class="g-box">
                    <div class="g-label g-label-rec">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
                        RECOMMENDATION
                    </div>
                    <div class="g-content">${item.rec}</div>
                </div>

                <div class="human-note" style="display:flex; justify-content:space-between; align-items:center; grid-column:span 2; margin-top:8px;">
                    <span>Human-in-the-Loop Safeguard: This recommendation requires store manager approval before any operational action.</span>
                    <button class="btn-detail" onclick="askCopilot('What is the inventory situation for ${item.title.replace(/'/g, '')}?')">
                        Investigate with AI Copilot &rarr;
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// 5. Fetch Products Catalog
async function fetchProducts() {
    try {
        const res = await fetch('/api/products');
        const data = await res.json();
        if (!data.success) return;
        appData.products = data.products;
        renderProductsTable(data.products);
    } catch (e) {
        console.error('Error fetching products:', e);
    }
}

function renderProductsTable(products) {
    const tbody = document.getElementById('productsTableBody');
    if (!tbody) return;

    tbody.innerHTML = products.map(p => {
        let badgeClass = 'status-healthy';
        if (p.status === 'Stockout Risk') badgeClass = 'status-stockout';
        else if (p.status === 'Overstocked') badgeClass = 'status-overstock';
        else if (p.status === 'Slow Moving') badgeClass = 'status-slow';

        const doiText = p.days_of_inventory >= 900 ? '999+ d' : `${p.days_of_inventory} d`;

        return `
            <tr>
                <td><code style="font-family: var(--font-mono); color: #818CF8;">${p.product_id}</code></td>
                <td><strong>${p.product_name}</strong></td>
                <td>${p.category}</td>
                <td>₹${p.selling_price.toLocaleString('en-IN')}</td>
                <td><strong>${p.stock_quantity}</strong></td>
                <td>${p.avg_daily_sales_30d} / day</td>
                <td><strong>${doiText}</strong></td>
                <td>₹${p.revenue_30d.toLocaleString('en-IN')} (${p.units_30d} u)</td>
                <td><span class="status-pill-badge ${badgeClass}">${p.status}</span></td>
                <td>
                    <button class="btn-detail" onclick="openProductModal('${p.product_id}')">Inspect</button>
                </td>
            </tr>
        `;
    }).join('');
}

function filterProducts() {
    const query = (document.getElementById('productSearch').value || '').toLowerCase();
    const cat = document.getElementById('categoryFilter').value;
    const status = document.getElementById('statusFilter').value;

    const filtered = appData.products.filter(p => {
        const matchesQuery = p.product_name.toLowerCase().includes(query) || p.product_id.toLowerCase().includes(query);
        const matchesCat = cat === 'all' || p.category === cat;
        const matchesStatus = status === 'all' || p.status === status;
        return matchesQuery && matchesCat && matchesStatus;
    });

    renderProductsTable(filtered);
}

// 6. Fetch Stores & Comparison
async function fetchStores() {
    try {
        const res = await fetch('/api/stores');
        const data = await res.json();
        if (!data.success) return;
        appData.stores = data.stores;

        const container = document.getElementById('storesContainer');
        if (container) {
            container.innerHTML = data.stores.map(s => `
                <div class="store-card">
                    <div class="store-card-header">
                        <span class="store-code">${s.store_id}</span>
                        <div class="store-name">${s.store_name}</div>
                        <div class="store-loc">${s.location}</div>
                    </div>
                    <div class="store-metric-row">
                        <span class="label">30-Day Revenue:</span>
                        <span class="store-metric-val">₹${s.revenue_30d.toLocaleString('en-IN')}</span>
                    </div>
                    <div class="store-metric-row">
                        <span class="label">30-Day Volume:</span>
                        <span class="store-metric-val">${s.units_30d.toLocaleString('en-IN')} units</span>
                    </div>
                    <div class="store-metric-row">
                        <span class="label">Current Stock:</span>
                        <span class="store-metric-val">${s.stock_quantity.toLocaleString('en-IN')} units</span>
                    </div>
                    <div class="store-metric-row">
                        <span class="label">Revenue Share:</span>
                        <span class="store-metric-val">${s.revenue_share_pct}%</span>
                    </div>
                </div>
            `).join('');
        }

        renderStoreComparison();
    } catch (e) {
        console.error('Error fetching stores:', e);
    }
}

function renderStoreComparison() {
    const s1Id = document.getElementById('compareStore1').value;
    const s2Id = document.getElementById('compareStore2').value;
    const container = document.getElementById('storeComparisonContent');
    if (!container || !appData.stores.length) return;

    const s1 = appData.stores.find(s => s.store_id === s1Id) || appData.stores[0];
    const s2 = appData.stores.find(s => s.store_id === s2Id) || appData.stores[1];

    const revDiff = s1.revenue_30d - s2.revenue_30d;
    const revDiffPct = s2.revenue_30d > 0 ? ((revDiff / s2.revenue_30d) * 100).round ? ((revDiff / s2.revenue_30d) * 100).toFixed(1) : ((revDiff / s2.revenue_30d) * 100).toFixed(1) : 'N/A';

    container.innerHTML = `
        <div class="data-table-card">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>${s1.store_name} (${s1.store_id})</th>
                        <th>${s2.store_name} (${s2.store_id})</th>
                        <th>Variance</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>30-Day Gross Revenue</td>
                        <td><strong>₹${s1.revenue_30d.toLocaleString('en-IN')}</strong></td>
                        <td><strong>₹${s2.revenue_30d.toLocaleString('en-IN')}</strong></td>
                        <td><span class="badge ${revDiff >= 0 ? 'status-healthy' : 'status-stockout'}">${revDiff >= 0 ? '+' : ''}${revDiffPct}% (₹${revDiff.toLocaleString('en-IN')})</span></td>
                    </tr>
                    <tr>
                        <td>30-Day Units Sold</td>
                        <td>${s1.units_30d.toLocaleString('en-IN')} units</td>
                        <td>${s2.units_30d.toLocaleString('en-IN')} units</td>
                        <td>${s1.units_30d - s2.units_30d >= 0 ? '+' : ''}${(s1.units_30d - s2.units_30d).toLocaleString('en-IN')} units</td>
                    </tr>
                    <tr>
                        <td>Current Physical Inventory</td>
                        <td>${s1.stock_quantity.toLocaleString('en-IN')} units</td>
                        <td>${s2.stock_quantity.toLocaleString('en-IN')} units</td>
                        <td>${(s1.stock_quantity - s2.stock_quantity).toLocaleString('en-IN')} units</td>
                    </tr>
                    <tr>
                        <td>Network Revenue Contribution</td>
                        <td><strong>${s1.revenue_share_pct}%</strong></td>
                        <td><strong>${s2.revenue_share_pct}%</strong></td>
                        <td>--</td>
                    </tr>
                    <tr>
                        <td>Store Location & Format</td>
                        <td>${s1.location}</td>
                        <td>${s2.location}</td>
                        <td>--</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
}

// 7. AI Copilot Integration
function askCopilot(question) {
    switchTab('copilot');
    const input = document.getElementById('copilotInput');
    if (input) input.value = question;
    handleCopilotSubmit(new Event('submit'));
}

async function handleCopilotSubmit(e) {
    if (e && e.preventDefault) e.preventDefault();
    const input = document.getElementById('copilotInput');
    const question = (input ? input.value : '').trim();
    if (!question) return;

    input.value = '';
    appendUserMessage(question);

    const chatStream = document.getElementById('chatStream');
    const loadingId = 'loading-' + Date.now();
    appendLoadingMessage(loadingId);
    chatStream.scrollTop = chatStream.scrollHeight;

    try {
        const response = await fetch('/api/copilot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });

        const contentType = response.headers.get('content-type') || '';
        let data;
        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            // HTML error received (e.g. cold start worker timeout or 502/504)
            data = {
                answer: "The AI service is warming up or reconnecting. Our deterministic analytics engine is ready.",
                evidence: ["System recovered gracefully from server cold start."],
                calculations: [],
                recommendation: "Please try asking again or click one of the suggested query chips above.",
                assumptions: ["Server instance spinning up."],
                limitations: ["Temporary connection delay."],
                intent: "warmup_retry",
                grounded: true
            };
        }

        removeLoadingMessage(loadingId);
        appendCopilotResponse(data);
    } catch (err) {
        removeLoadingMessage(loadingId);
        appendCopilotResponse({
            answer: "The copilot experienced a temporary connection interruption while reaching the server.",
            evidence: ["Deterministic data layer remains operational."],
            calculations: [],
            recommendation: "Please verify the server is running on port 8000 and try again.",
            assumptions: [],
            limitations: [err.message || "Connection timed out."],
            intent: "error",
            grounded: false
        });
    }

    chatStream.scrollTop = chatStream.scrollHeight;
}

function appendUserMessage(text) {
    const stream = document.getElementById('chatStream');
    const row = document.createElement('div');
    row.className = 'chat-row-user';
    row.innerHTML = `<div class="user-bubble">${escapeHtml(text)}</div>`;
    stream.appendChild(row);
}

function appendLoadingMessage(id) {
    const stream = document.getElementById('chatStream');
    const row = document.createElement('div');
    row.className = 'chat-row-bot';
    row.id = id;
    row.innerHTML = `
        <div class="bot-avatar">RM</div>
        <div class="bot-bubble" style="display:flex; align-items:center; gap: 8px;">
            <span class="dot-live"></span>
            <span>Synthesizing python metrics and grounding evidence...</span>
        </div>
    `;
    stream.appendChild(row);
}

function removeLoadingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendCopilotResponse(res) {
    const stream = document.getElementById('chatStream');
    const row = document.createElement('div');
    row.className = 'chat-row-bot';

    const evidenceList = (res.evidence || []).map(e => `<li>${escapeHtml(String(e))}</li>`).join('');
    const calcList = (res.calculations || []).map(c => `<div><span class="g-calc-code">${escapeHtml(String(c))}</span></div>`).join('');
    const assumeList = (res.assumptions || []).map(a => `<li>${escapeHtml(String(a))}</li>`).join('');
    const limitList = (res.limitations || []).map(l => `<li>${escapeHtml(String(l))}</li>`).join('');

    const drawerId = 'drawer-' + Date.now();
    const rawDataJson = escapeHtml(JSON.stringify(res, null, 2));

    row.innerHTML = `
        <div class="bot-avatar">RM</div>
        <div class="copilot-response-card">
            <div class="resp-answer-box">
                ${formatMarkdownAnswer(res.answer || 'No answer generated.')}
            </div>

            <div class="resp-grid">
                <div class="resp-box">
                    <div class="resp-box-title g-label-data">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                        SUPPORTING EVIDENCE
                    </div>
                    <div class="resp-box-content">
                        ${evidenceList ? `<ul>${evidenceList}</ul>` : '<em>No explicit evidence points.</em>'}
                    </div>
                </div>

                <div class="resp-box">
                    <div class="resp-box-title g-label-calc">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="4" y="2" width="16" height="20" rx="2"></rect><line x1="8" y1="6" x2="16" y2="6"></line></svg>
                        DETERMINISTIC CALCULATIONS
                    </div>
                    <div class="resp-box-content">
                        ${calcList || '<em>Direct metric lookup (no intermediate calculation).</em>'}
                    </div>
                </div>

                <div class="resp-box">
                    <div class="resp-box-title g-label-rec">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
                        RECOMMENDED ACTION
                    </div>
                    <div class="resp-box-content">
                        ${escapeHtml(res.recommendation || 'No immediate action required.')}
                    </div>
                </div>

                <div class="resp-box">
                    <div class="resp-box-title g-label-assume">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line></svg>
                        ASSUMPTIONS & UNCERTAINTIES
                    </div>
                    <div class="resp-box-content">
                        ${assumeList ? `<ul>${assumeList}</ul>` : '<em>Standard operational assumptions.</em>'}
                        ${limitList ? `<div style="margin-top:6px; color:#FCA5A5;"><strong>Limitations:</strong><ul>${limitList}</ul></div>` : ''}
                    </div>
                </div>
            </div>

            <!-- Expandable Evidence Inspector Drawer -->
            <button class="evidence-drawer-toggle" onclick="toggleEvidenceDrawer('${drawerId}')">
                <span>View Raw Evidence & Grounding Traceability</span>
                <span id="icon-${drawerId}">▼</span>
            </button>
            <div class="evidence-drawer-content" id="${drawerId}">
                <pre>${rawDataJson}</pre>
            </div>
        </div>
    `;

    stream.appendChild(row);
}

function toggleEvidenceDrawer(id) {
    const el = document.getElementById(id);
    const icon = document.getElementById('icon-' + id);
    if (!el) return;
    if (el.classList.contains('open')) {
        el.classList.remove('open');
        if (icon) icon.textContent = '▼';
    } else {
        el.classList.add('open');
        if (icon) icon.textContent = '▲';
    }
}

// Modal
function openProductModal(productId) {
    const prod = appData.products.find(p => p.product_id === productId);
    if (!prod) return;

    document.getElementById('modalSku').textContent = prod.product_id;
    document.getElementById('modalTitle').textContent = prod.product_name;

    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px;">
            <div class="g-box">
                <div class="g-label">Category & Supplier</div>
                <div><strong>${prod.category}</strong> (Supplier: ${prod.supplier})</div>
            </div>
            <div class="g-box">
                <div class="g-label">Financial Margins</div>
                <div>Cost: ₹${prod.cost_price} | Price: ₹${prod.selling_price} (Margin: ${Math.round((prod.selling_price - prod.cost_price)/prod.selling_price * 100)}%)</div>
            </div>
            <div class="g-box">
                <div class="g-label">Current Physical Stock</div>
                <div><strong style="font-size:1.2rem;">${prod.stock_quantity} units</strong> (Reorder Level: ${prod.reorder_level})</div>
            </div>
            <div class="g-box">
                <div class="g-label">Inventory Run Rate</div>
                <div>${prod.avg_daily_sales_30d} units/day &rarr; <strong>${prod.days_of_inventory >= 900 ? '999+' : prod.days_of_inventory} days</strong></div>
            </div>
        </div>
        <div class="g-box">
            <div class="g-label">Sales Performance (Past 30 & 90 Days)</div>
            <div>30-Day Revenue: ₹${prod.revenue_30d.toLocaleString('en-IN')} (${prod.units_30d} units sold)</div>
            <div style="color:var(--text-secondary); font-size:0.8rem; margin-top:4px;">90-Day Cumulative: ₹${prod.revenue_90d.toLocaleString('en-IN')} (${prod.units_90d} units sold)</div>
        </div>
        <div style="margin-top:16px; text-align:right;">
            <button class="btn-send" onclick="askCopilot('How did ${prod.product_name} perform this month?'); closeModalDirect();">
                Ask Copilot About This SKU
            </button>
        </div>
    `;

    document.getElementById('productModal').classList.add('open');
}

function closeModalDirect() {
    document.getElementById('productModal').classList.remove('open');
}

function closeModal(e) {
    if (e.target.id === 'productModal') closeModalDirect();
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatMarkdownAnswer(text) {
    let clean = escapeHtml(text);
    // Convert bold **text** to <strong>text</strong>
    clean = clean.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Convert newlines to breaks
    clean = clean.replace(/\n/g, '<br>');
    return clean;
}
