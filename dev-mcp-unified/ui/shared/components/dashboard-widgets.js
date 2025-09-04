/**
 * Dashboard Widgets Component Library
 * Reusable widget components with drill-down functionality, real-time updates, and chart integrations
 * Designed for both Sophia and Artemis UIs
 */

class DashboardWidgets {
    constructor(options = {}) {
        this.options = {
            apiBaseUrl: options.apiBaseUrl || 'http://127.0.0.1:3333',
            wsUrl: options.wsUrl || 'ws://127.0.0.1:3333/ws',
            theme: options.theme || 'dark',
            enableRealTime: options.enableRealTime !== false,
            refreshInterval: options.refreshInterval || 30000,
            ...options
        };

        this.widgets = new Map();
        this.updateIntervals = new Map();
        this.ws = null;
        this.isConnected = false;

        // Chart.js instance tracking
        this.chartInstances = new Map();

        this.init();
    }

    async init() {
        await this.loadChartJS();
        if (this.options.enableRealTime) {
            await this.connectWebSocket();
        }
    }

    async loadChartJS() {
        return new Promise((resolve) => {
            if (typeof Chart !== 'undefined') {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js';
            script.onload = resolve;
            document.head.appendChild(script);
        });
    }

    async connectWebSocket() {
        try {
            this.ws = new WebSocket(this.options.wsUrl);
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.subscribeToWidgetUpdates();
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.ws.onclose = () => {
                this.isConnected = false;
                setTimeout(() => this.connectWebSocket(), 5000);
            };
        } catch (error) {
            console.error('WebSocket connection failed:', error);
        }
    }

    subscribeToWidgetUpdates() {
        if (this.isConnected) {
            this.ws.send(JSON.stringify({
                type: 'subscribe_widget_updates',
                widgets: Array.from(this.widgets.keys())
            }));
        }
    }

    handleWebSocketMessage(data) {
        if (data.type === 'widget_update' && this.widgets.has(data.widget_id)) {
            this.updateWidget(data.widget_id, data.data);
        }
    }

    // ==========================================
    // Core Widget Creation Methods
    // ==========================================

    createWidget(containerId, config) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }

        const widgetId = config.id || this.generateWidgetId();
        const widget = {
            id: widgetId,
            type: config.type,
            title: config.title || 'Widget',
            config: config,
            container: container,
            data: null,
            loading: false,
            error: null
        };

        this.widgets.set(widgetId, widget);

        // Render widget based on type
        switch (config.type) {
            case 'metric':
                this.renderMetricWidget(widget);
                break;
            case 'chart':
                this.renderChartWidget(widget);
                break;
            case 'table':
                this.renderTableWidget(widget);
                break;
            case 'progress':
                this.renderProgressWidget(widget);
                break;
            case 'status':
                this.renderStatusWidget(widget);
                break;
            case 'activity':
                this.renderActivityWidget(widget);
                break;
            case 'kpi':
                this.renderKPIWidget(widget);
                break;
            default:
                this.renderGenericWidget(widget);
        }

        // Start data loading
        this.loadWidgetData(widgetId);

        // Set up auto-refresh if enabled
        if (config.autoRefresh) {
            this.setupAutoRefresh(widgetId, config.refreshInterval || this.options.refreshInterval);
        }

        return widgetId;
    }

    renderMetricWidget(widget) {
        const { config } = widget;
        widget.container.innerHTML = `
            <div class="dashboard-widget metric-widget" data-widget-id="${widget.id}">
                <div class="widget-header">
                    <h3 class="widget-title">${widget.title}</h3>
                    <div class="widget-actions">
                        ${config.drillDown ? '<button class="drill-down-btn" title="Drill down"><svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg></button>' : ''}
                        <button class="refresh-btn" title="Refresh"><svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-8 3.58-8 8s3.58 8 8 8c3.74 0 6.85-2.54 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></button>
                    </div>
                </div>
                <div class="widget-content">
                    <div class="widget-loading">
                        <div class="loading-spinner"></div>
                        <span>Loading...</span>
                    </div>
                    <div class="metric-display" style="display: none;">
                        <div class="metric-value">--</div>
                        <div class="metric-label">${config.unit || ''}</div>
                        <div class="metric-change">
                            <span class="change-value">--</span>
                            <span class="change-period">${config.changePeriod || 'vs last period'}</span>
                        </div>
                    </div>
                    <div class="widget-error" style="display: none;">
                        <div class="error-icon">⚠️</div>
                        <div class="error-message">Failed to load data</div>
                        <button class="retry-btn">Retry</button>
                    </div>
                </div>
            </div>
        `;

        this.bindWidgetEvents(widget);
    }

    renderChartWidget(widget) {
        const { config } = widget;
        widget.container.innerHTML = `
            <div class="dashboard-widget chart-widget" data-widget-id="${widget.id}">
                <div class="widget-header">
                    <h3 class="widget-title">${widget.title}</h3>
                    <div class="widget-actions">
                        <select class="chart-type-selector">
                            <option value="line" ${config.chartType === 'line' ? 'selected' : ''}>Line</option>
                            <option value="bar" ${config.chartType === 'bar' ? 'selected' : ''}>Bar</option>
                            <option value="pie" ${config.chartType === 'pie' ? 'selected' : ''}>Pie</option>
                            <option value="doughnut" ${config.chartType === 'doughnut' ? 'selected' : ''}>Doughnut</option>
                        </select>
                        ${config.drillDown ? '<button class="drill-down-btn" title="Drill down"><svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg></button>' : ''}
                        <button class="refresh-btn" title="Refresh"><svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-8 3.58-8 8s3.58 8 8 8c3.74 0 6.85-2.54 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></button>
                    </div>
                </div>
                <div class="widget-content">
                    <div class="widget-loading">
                        <div class="loading-spinner"></div>
                        <span>Loading chart data...</span>
                    </div>
                    <div class="chart-container" style="display: none;">
                        <canvas id="chart-${widget.id}"></canvas>
                    </div>
                    <div class="widget-error" style="display: none;">
                        <div class="error-icon">⚠️</div>
                        <div class="error-message">Failed to load chart</div>
                        <button class="retry-btn">Retry</button>
                    </div>
                </div>
            </div>
        `;

        this.bindWidgetEvents(widget);
    }

    renderTableWidget(widget) {
        const { config } = widget;
        widget.container.innerHTML = `
            <div class="dashboard-widget table-widget" data-widget-id="${widget.id}">
                <div class="widget-header">
                    <h3 class="widget-title">${widget.title}</h3>
                    <div class="widget-actions">
                        <input type="search" class="table-search" placeholder="Search...">
                        ${config.drillDown ? '<button class="drill-down-btn" title="Drill down"><svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg></button>' : ''}
                        <button class="refresh-btn" title="Refresh"><svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-8 3.58-8 8s3.58 8 8 8c3.74 0 6.85-2.54 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></button>
                    </div>
                </div>
                <div class="widget-content">
                    <div class="widget-loading">
                        <div class="loading-spinner"></div>
                        <span>Loading table data...</span>
                    </div>
                    <div class="table-container" style="display: none;">
                        <table class="data-table">
                            <thead id="table-header-${widget.id}"></thead>
                            <tbody id="table-body-${widget.id}"></tbody>
                        </table>
                        <div class="table-pagination">
                            <button class="prev-page" disabled>Previous</button>
                            <span class="page-info">Page 1 of 1</span>
                            <button class="next-page" disabled>Next</button>
                        </div>
                    </div>
                    <div class="widget-error" style="display: none;">
                        <div class="error-icon">⚠️</div>
                        <div class="error-message">Failed to load table</div>
                        <button class="retry-btn">Retry</button>
                    </div>
                </div>
            </div>
        `;

        this.bindWidgetEvents(widget);
    }

    renderProgressWidget(widget) {
        const { config } = widget;
        widget.container.innerHTML = `
            <div class="dashboard-widget progress-widget" data-widget-id="${widget.id}">
                <div class="widget-header">
                    <h3 class="widget-title">${widget.title}</h3>
                    <div class="widget-actions">
                        ${config.drillDown ? '<button class="drill-down-btn" title="Drill down"><svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg></button>' : ''}
                        <button class="refresh-btn" title="Refresh"><svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-8 3.58-8 8s3.58 8 8 8c3.74 0 6.85-2.54 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></button>
                    </div>
                </div>
                <div class="widget-content">
                    <div class="widget-loading">
                        <div class="loading-spinner"></div>
                        <span>Loading progress data...</span>
                    </div>
                    <div class="progress-display" style="display: none;">
                        <div class="progress-items"></div>
                    </div>
                    <div class="widget-error" style="display: none;">
                        <div class="error-icon">⚠️</div>
                        <div class="error-message">Failed to load progress</div>
                        <button class="retry-btn">Retry</button>
                    </div>
                </div>
            </div>
        `;

        this.bindWidgetEvents(widget);
    }

    renderStatusWidget(widget) {
        const { config } = widget;
        widget.container.innerHTML = `
            <div class="dashboard-widget status-widget" data-widget-id="${widget.id}">
                <div class="widget-header">
                    <h3 class="widget-title">${widget.title}</h3>
                    <div class="widget-actions">
                        ${config.drillDown ? '<button class="drill-down-btn" title="Drill down"><svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg></button>' : ''}
                        <button class="refresh-btn" title="Refresh"><svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-8 3.58-8 8s3.58 8 8 8c3.74 0 6.85-2.54 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></button>
                    </div>
                </div>
                <div class="widget-content">
                    <div class="widget-loading">
                        <div class="loading-spinner"></div>
                        <span>Loading status...</span>
                    </div>
                    <div class="status-display" style="display: none;">
                        <div class="status-items"></div>
                    </div>
                    <div class="widget-error" style="display: none;">
                        <div class="error-icon">⚠️</div>
                        <div class="error-message">Failed to load status</div>
                        <button class="retry-btn">Retry</button>
                    </div>
                </div>
            </div>
        `;

        this.bindWidgetEvents(widget);
    }

    renderActivityWidget(widget) {
        const { config } = widget;
        widget.container.innerHTML = `
            <div class="dashboard-widget activity-widget" data-widget-id="${widget.id}">
                <div class="widget-header">
                    <h3 class="widget-title">${widget.title}</h3>
                    <div class="widget-actions">
                        <select class="activity-filter">
                            <option value="all">All Activities</option>
                            <option value="info">Info</option>
                            <option value="warning">Warnings</option>
                            <option value="error">Errors</option>
                        </select>
                        ${config.drillDown ? '<button class="drill-down-btn" title="Drill down"><svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg></button>' : ''}
                        <button class="refresh-btn" title="Refresh"><svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-8 3.58-8 8s3.58 8 8 8c3.74 0 6.85-2.54 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></button>
                    </div>
                </div>
                <div class="widget-content">
                    <div class="widget-loading">
                        <div class="loading-spinner"></div>
                        <span>Loading activities...</span>
                    </div>
                    <div class="activity-feed" style="display: none;">
                        <div class="activity-list"></div>
                        <div class="load-more">
                            <button class="load-more-btn">Load More</button>
                        </div>
                    </div>
                    <div class="widget-error" style="display: none;">
                        <div class="error-icon">⚠️</div>
                        <div class="error-message">Failed to load activities</div>
                        <button class="retry-btn">Retry</button>
                    </div>
                </div>
            </div>
        `;

        this.bindWidgetEvents(widget);
    }

    renderKPIWidget(widget) {
        const { config } = widget;
        widget.container.innerHTML = `
            <div class="dashboard-widget kpi-widget" data-widget-id="${widget.id}">
                <div class="widget-header">
                    <h3 class="widget-title">${widget.title}</h3>
                    <div class="widget-actions">
                        <select class="kpi-period">
                            <option value="24h">Last 24h</option>
                            <option value="7d">Last 7 days</option>
                            <option value="30d">Last 30 days</option>
                            <option value="90d">Last 90 days</option>
                        </select>
                        ${config.drillDown ? '<button class="drill-down-btn" title="Drill down"><svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg></button>' : ''}
                        <button class="refresh-btn" title="Refresh"><svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-8 3.58-8 8s3.58 8 8 8c3.74 0 6.85-2.54 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></button>
                    </div>
                </div>
                <div class="widget-content">
                    <div class="widget-loading">
                        <div class="loading-spinner"></div>
                        <span>Loading KPIs...</span>
                    </div>
                    <div class="kpi-grid" style="display: none;"></div>
                    <div class="widget-error" style="display: none;">
                        <div class="error-icon">⚠️</div>
                        <div class="error-message">Failed to load KPIs</div>
                        <button class="retry-btn">Retry</button>
                    </div>
                </div>
            </div>
        `;

        this.bindWidgetEvents(widget);
    }

    renderGenericWidget(widget) {
        widget.container.innerHTML = `
            <div class="dashboard-widget generic-widget" data-widget-id="${widget.id}">
                <div class="widget-header">
                    <h3 class="widget-title">${widget.title}</h3>
                    <div class="widget-actions">
                        <button class="refresh-btn" title="Refresh"><svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-8 3.58-8 8s3.58 8 8 8c3.74 0 6.85-2.54 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></button>
                    </div>
                </div>
                <div class="widget-content">
                    <div class="widget-loading">
                        <div class="loading-spinner"></div>
                        <span>Loading...</span>
                    </div>
                    <div class="widget-data" style="display: none;"></div>
                    <div class="widget-error" style="display: none;">
                        <div class="error-icon">⚠️</div>
                        <div class="error-message">Failed to load data</div>
                        <button class="retry-btn">Retry</button>
                    </div>
                </div>
            </div>
        `;

        this.bindWidgetEvents(widget);
    }

    bindWidgetEvents(widget) {
        const container = widget.container.querySelector('.dashboard-widget');
        
        // Refresh button
        const refreshBtn = container.querySelector('.refresh-btn');
        refreshBtn?.addEventListener('click', () => {
            this.refreshWidget(widget.id);
        });

        // Drill down button
        const drillDownBtn = container.querySelector('.drill-down-btn');
        drillDownBtn?.addEventListener('click', () => {
            this.drillDown(widget.id);
        });

        // Retry button
        const retryBtn = container.querySelector('.retry-btn');
        retryBtn?.addEventListener('click', () => {
            this.refreshWidget(widget.id);
        });

        // Widget-specific event bindings
        this.bindTypeSpecificEvents(widget, container);
    }

    bindTypeSpecificEvents(widget, container) {
        const { type } = widget;

        switch (type) {
            case 'chart':
                const chartTypeSelector = container.querySelector('.chart-type-selector');
                chartTypeSelector?.addEventListener('change', (e) => {
                    this.changeChartType(widget.id, e.target.value);
                });
                break;

            case 'table':
                const searchInput = container.querySelector('.table-search');
                searchInput?.addEventListener('input', (e) => {
                    this.filterTable(widget.id, e.target.value);
                });

                const prevBtn = container.querySelector('.prev-page');
                const nextBtn = container.querySelector('.next-page');
                prevBtn?.addEventListener('click', () => this.previousPage(widget.id));
                nextBtn?.addEventListener('click', () => this.nextPage(widget.id));
                break;

            case 'activity':
                const activityFilter = container.querySelector('.activity-filter');
                activityFilter?.addEventListener('change', (e) => {
                    this.filterActivity(widget.id, e.target.value);
                });

                const loadMoreBtn = container.querySelector('.load-more-btn');
                loadMoreBtn?.addEventListener('click', () => {
                    this.loadMoreActivity(widget.id);
                });
                break;

            case 'kpi':
                const kpiPeriod = container.querySelector('.kpi-period');
                kpiPeriod?.addEventListener('change', (e) => {
                    this.changeKPIPeriod(widget.id, e.target.value);
                });
                break;
        }
    }

    // ==========================================
    // Data Loading and Management
    // ==========================================

    async loadWidgetData(widgetId) {
        const widget = this.widgets.get(widgetId);
        if (!widget) return;

        this.setWidgetLoading(widgetId, true);

        try {
            const endpoint = widget.config.endpoint || `/api/widgets/${widget.type}`;
            const params = new URLSearchParams(widget.config.params || {});
            
            const response = await fetch(`${this.options.apiBaseUrl}${endpoint}?${params}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            widget.data = data;
            widget.error = null;

            this.renderWidgetData(widgetId, data);
            this.setWidgetLoading(widgetId, false);

        } catch (error) {
            console.error(`Failed to load widget data for ${widgetId}:`, error);
            widget.error = error.message;
            this.setWidgetError(widgetId, error.message);
            this.setWidgetLoading(widgetId, false);
        }
    }

    renderWidgetData(widgetId, data) {
        const widget = this.widgets.get(widgetId);
        if (!widget) return;

        switch (widget.type) {
            case 'metric':
                this.renderMetricData(widget, data);
                break;
            case 'chart':
                this.renderChartData(widget, data);
                break;
            case 'table':
                this.renderTableData(widget, data);
                break;
            case 'progress':
                this.renderProgressData(widget, data);
                break;
            case 'status':
                this.renderStatusData(widget, data);
                break;
            case 'activity':
                this.renderActivityData(widget, data);
                break;
            case 'kpi':
                this.renderKPIData(widget, data);
                break;
            default:
                this.renderGenericData(widget, data);
        }
    }

    renderMetricData(widget, data) {
        const container = widget.container.querySelector('.dashboard-widget');
        const metricDisplay = container.querySelector('.metric-display');
        const valueElement = metricDisplay.querySelector('.metric-value');
        const changeElement = metricDisplay.querySelector('.change-value');

        valueElement.textContent = this.formatNumber(data.value);
        
        if (data.change !== undefined) {
            const changePercent = data.changePercent || 0;
            changeElement.textContent = `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(1)}%`;
            changeElement.className = `change-value ${changePercent >= 0 ? 'positive' : 'negative'}`;
        }

        this.showWidgetContent(widget.id, '.metric-display');
    }

    renderChartData(widget, data) {
        const container = widget.container.querySelector('.dashboard-widget');
        const canvasId = `chart-${widget.id}`;
        const canvas = document.getElementById(canvasId);

        if (!canvas) return;

        // Destroy existing chart if it exists
        if (this.chartInstances.has(widget.id)) {
            this.chartInstances.get(widget.id).destroy();
        }

        const chartConfig = this.buildChartConfig(widget, data);
        const chart = new Chart(canvas, chartConfig);
        this.chartInstances.set(widget.id, chart);

        this.showWidgetContent(widget.id, '.chart-container');
    }

    buildChartConfig(widget, data) {
        const { config } = widget;
        const chartType = config.chartType || 'line';
        
        const baseConfig = {
            type: chartType,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: config.showLegend !== false,
                        position: config.legendPosition || 'top'
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: this.getScalesConfig(chartType, config),
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        };

        // Apply theme-specific styling
        this.applyChartTheme(baseConfig);

        return baseConfig;
    }

    getScalesConfig(chartType, config) {
        if (chartType === 'pie' || chartType === 'doughnut') {
            return {};
        }

        return {
            x: {
                display: config.showXAxis !== false,
                grid: {
                    display: config.showGrid !== false,
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.7)'
                }
            },
            y: {
                display: config.showYAxis !== false,
                grid: {
                    display: config.showGrid !== false,
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.7)'
                }
            }
        };
    }

    applyChartTheme(chartConfig) {
        if (this.options.theme === 'dark') {
            chartConfig.options.plugins.legend.labels = {
                color: 'rgba(255, 255, 255, 0.8)'
            };
        }
    }

    renderTableData(widget, data) {
        const container = widget.container.querySelector('.dashboard-widget');
        const header = document.getElementById(`table-header-${widget.id}`);
        const body = document.getElementById(`table-body-${widget.id}`);

        if (!data.columns || !data.rows) {
            console.error('Invalid table data format');
            return;
        }

        // Render header
        header.innerHTML = `
            <tr>
                ${data.columns.map(col => `
                    <th data-sort="${col.key}" class="sortable">
                        ${col.label}
                        <span class="sort-indicator"></span>
                    </th>
                `).join('')}
            </tr>
        `;

        // Render body
        this.renderTableRows(widget.id, data.rows);

        // Bind sorting events
        header.querySelectorAll('.sortable').forEach(th => {
            th.addEventListener('click', () => {
                this.sortTable(widget.id, th.dataset.sort);
            });
        });

        this.showWidgetContent(widget.id, '.table-container');
    }

    renderTableRows(widgetId, rows) {
        const body = document.getElementById(`table-body-${widgetId}`);
        const widget = this.widgets.get(widgetId);
        
        body.innerHTML = rows.map(row => `
            <tr>
                ${widget.data.columns.map(col => `
                    <td data-label="${col.label}">
                        ${this.formatTableCellValue(row[col.key], col.type)}
                    </td>
                `).join('')}
            </tr>
        `).join('');
    }

    formatTableCellValue(value, type) {
        if (value === null || value === undefined) return '--';

        switch (type) {
            case 'number':
                return this.formatNumber(value);
            case 'currency':
                return this.formatCurrency(value);
            case 'percentage':
                return `${(value * 100).toFixed(1)}%`;
            case 'date':
                return new Date(value).toLocaleDateString();
            case 'datetime':
                return new Date(value).toLocaleString();
            default:
                return value;
        }
    }

    renderProgressData(widget, data) {
        const container = widget.container.querySelector('.dashboard-widget');
        const progressDisplay = container.querySelector('.progress-display');
        const itemsContainer = progressDisplay.querySelector('.progress-items');

        if (!Array.isArray(data.items)) {
            console.error('Invalid progress data format');
            return;
        }

        itemsContainer.innerHTML = data.items.map(item => `
            <div class="progress-item">
                <div class="progress-header">
                    <span class="progress-label">${item.label}</span>
                    <span class="progress-value">${item.value}/${item.total}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(item.value / item.total * 100)}%"></div>
                </div>
                <div class="progress-percentage">${((item.value / item.total) * 100).toFixed(1)}%</div>
            </div>
        `).join('');

        this.showWidgetContent(widget.id, '.progress-display');
    }

    renderStatusData(widget, data) {
        const container = widget.container.querySelector('.dashboard-widget');
        const statusDisplay = container.querySelector('.status-display');
        const itemsContainer = statusDisplay.querySelector('.status-items');

        if (!Array.isArray(data.items)) {
            console.error('Invalid status data format');
            return;
        }

        itemsContainer.innerHTML = data.items.map(item => `
            <div class="status-item status-${item.status}">
                <div class="status-indicator"></div>
                <div class="status-content">
                    <div class="status-title">${item.title}</div>
                    <div class="status-description">${item.description || ''}</div>
                    ${item.lastUpdated ? `<div class="status-time">${this.formatRelativeTime(item.lastUpdated)}</div>` : ''}
                </div>
            </div>
        `).join('');

        this.showWidgetContent(widget.id, '.status-display');
    }

    renderActivityData(widget, data) {
        const container = widget.container.querySelector('.dashboard-widget');
        const activityList = container.querySelector('.activity-list');

        if (!Array.isArray(data.activities)) {
            console.error('Invalid activity data format');
            return;
        }

        const activitiesHtml = data.activities.map(activity => `
            <div class="activity-item activity-${activity.type}">
                <div class="activity-icon">
                    ${this.getActivityIcon(activity.type)}
                </div>
                <div class="activity-content">
                    <div class="activity-message">${activity.message}</div>
                    <div class="activity-meta">
                        ${activity.user ? `<span class="activity-user">${activity.user}</span>` : ''}
                        <span class="activity-time">${this.formatRelativeTime(activity.timestamp)}</span>
                    </div>
                </div>
            </div>
        `).join('');

        activityList.innerHTML = activitiesHtml;
        this.showWidgetContent(widget.id, '.activity-feed');
    }

    renderKPIData(widget, data) {
        const container = widget.container.querySelector('.dashboard-widget');
        const kpiGrid = container.querySelector('.kpi-grid');

        if (!Array.isArray(data.kpis)) {
            console.error('Invalid KPI data format');
            return;
        }

        kpiGrid.innerHTML = data.kpis.map(kpi => `
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-icon">${kpi.icon || '📊'}</div>
                    <div class="kpi-trend ${kpi.trend}">
                        ${kpi.trend === 'up' ? '↗️' : kpi.trend === 'down' ? '↘️' : '➡️'}
                    </div>
                </div>
                <div class="kpi-value">${this.formatKPIValue(kpi.value, kpi.format)}</div>
                <div class="kpi-label">${kpi.label}</div>
                <div class="kpi-change">
                    <span class="change-value ${kpi.changeDirection}">${kpi.change}</span>
                    <span class="change-period">${kpi.period}</span>
                </div>
            </div>
        `).join('');

        this.showWidgetContent(widget.id, '.kpi-grid');
    }

    renderGenericData(widget, data) {
        const container = widget.container.querySelector('.dashboard-widget');
        const dataContainer = container.querySelector('.widget-data');

        dataContainer.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        this.showWidgetContent(widget.id, '.widget-data');
    }

    // ==========================================
    // Widget Interaction Methods
    // ==========================================

    refreshWidget(widgetId) {
        this.loadWidgetData(widgetId);
    }

    drillDown(widgetId) {
        const widget = this.widgets.get(widgetId);
        if (!widget || !widget.config.drillDown) return;

        // Emit drill down event
        const event = new CustomEvent('widget-drill-down', {
            detail: { widgetId, widget, data: widget.data }
        });
        document.dispatchEvent(event);
    }

    changeChartType(widgetId, newType) {
        const widget = this.widgets.get(widgetId);
        if (!widget || widget.type !== 'chart') return;

        widget.config.chartType = newType;
        this.renderChartData(widget, widget.data);
    }

    sortTable(widgetId, sortKey) {
        const widget = this.widgets.get(widgetId);
        if (!widget || widget.type !== 'table') return;

        const { data } = widget;
        const sortDirection = widget.sortDirection === 'asc' ? 'desc' : 'asc';
        widget.sortDirection = sortDirection;
        widget.sortKey = sortKey;

        data.rows.sort((a, b) => {
            const aVal = a[sortKey];
            const bVal = b[sortKey];
            
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
            }
            
            const aStr = String(aVal).toLowerCase();
            const bStr = String(bVal).toLowerCase();
            
            if (sortDirection === 'asc') {
                return aStr.localeCompare(bStr);
            } else {
                return bStr.localeCompare(aStr);
            }
        });

        this.renderTableRows(widgetId, data.rows);
        this.updateSortIndicators(widgetId, sortKey, sortDirection);
    }

    updateSortIndicators(widgetId, sortKey, sortDirection) {
        const container = this.widgets.get(widgetId).container;
        const sortables = container.querySelectorAll('.sortable');
        
        sortables.forEach(th => {
            const indicator = th.querySelector('.sort-indicator');
            if (th.dataset.sort === sortKey) {
                indicator.textContent = sortDirection === 'asc' ? '↑' : '↓';
                th.classList.add('sorted');
            } else {
                indicator.textContent = '';
                th.classList.remove('sorted');
            }
        });
    }

    filterTable(widgetId, searchTerm) {
        const widget = this.widgets.get(widgetId);
        if (!widget || widget.type !== 'table') return;

        const { data } = widget;
        const filteredRows = searchTerm ? 
            data.rows.filter(row => 
                Object.values(row).some(value => 
                    String(value).toLowerCase().includes(searchTerm.toLowerCase())
                )
            ) : data.rows;

        this.renderTableRows(widgetId, filteredRows);
    }

    filterActivity(widgetId, filterType) {
        const widget = this.widgets.get(widgetId);
        if (!widget || widget.type !== 'activity') return;

        const { data } = widget;
        const filteredActivities = filterType === 'all' ? 
            data.activities : 
            data.activities.filter(activity => activity.type === filterType);

        this.renderActivityData(widget, { activities: filteredActivities });
    }

    loadMoreActivity(widgetId) {
        // Implementation would load more activity items
        console.log('Loading more activities for widget:', widgetId);
    }

    changeKPIPeriod(widgetId, period) {
        const widget = this.widgets.get(widgetId);
        if (!widget || widget.type !== 'kpi') return;

        widget.config.period = period;
        this.refreshWidget(widgetId);
    }

    // ==========================================
    // Utility Methods
    // ==========================================

    setWidgetLoading(widgetId, loading) {
        const widget = this.widgets.get(widgetId);
        if (!widget) return;

        widget.loading = loading;
        const container = widget.container.querySelector('.dashboard-widget');
        const loadingElement = container.querySelector('.widget-loading');
        const contentElements = container.querySelectorAll('.widget-content > :not(.widget-loading):not(.widget-error)');

        if (loading) {
            loadingElement.style.display = 'flex';
            contentElements.forEach(el => el.style.display = 'none');
        } else {
            loadingElement.style.display = 'none';
        }
    }

    setWidgetError(widgetId, error) {
        const widget = this.widgets.get(widgetId);
        if (!widget) return;

        const container = widget.container.querySelector('.dashboard-widget');
        const errorElement = container.querySelector('.widget-error');
        const errorMessage = errorElement.querySelector('.error-message');
        const contentElements = container.querySelectorAll('.widget-content > :not(.widget-error)');

        errorMessage.textContent = error;
        errorElement.style.display = 'flex';
        contentElements.forEach(el => el.style.display = 'none');
    }

    showWidgetContent(widgetId, contentSelector) {
        const widget = this.widgets.get(widgetId);
        if (!widget) return;

        const container = widget.container.querySelector('.dashboard-widget');
        const targetContent = container.querySelector(contentSelector);
        const allContent = container.querySelectorAll('.widget-content > div');

        allContent.forEach(el => el.style.display = 'none');
        if (targetContent) {
            targetContent.style.display = 'block';
        }
    }

    setupAutoRefresh(widgetId, interval) {
        if (this.updateIntervals.has(widgetId)) {
            clearInterval(this.updateIntervals.get(widgetId));
        }

        const intervalId = setInterval(() => {
            this.refreshWidget(widgetId);
        }, interval);

        this.updateIntervals.set(widgetId, intervalId);
    }

    updateWidget(widgetId, data) {
        const widget = this.widgets.get(widgetId);
        if (!widget) return;

        widget.data = { ...widget.data, ...data };
        this.renderWidgetData(widgetId, widget.data);
    }

    formatNumber(num) {
        if (typeof num !== 'number') return String(num);
        
        if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
        
        return num.toLocaleString();
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    formatKPIValue(value, format) {
        switch (format) {
            case 'number':
                return this.formatNumber(value);
            case 'currency':
                return this.formatCurrency(value);
            case 'percentage':
                return `${(value * 100).toFixed(1)}%`;
            default:
                return String(value);
        }
    }

    formatRelativeTime(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = now - time;
        
        const minutes = Math.floor(diff / (1000 * 60));
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return time.toLocaleDateString();
    }

    getActivityIcon(type) {
        const icons = {
            info: 'ℹ️',
            warning: '⚠️',
            error: '❌',
            success: '✅',
            user: '👤',
            system: '⚙️'
        };
        return icons[type] || 'ℹ️';
    }

    generateWidgetId() {
        return `widget_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    // ==========================================
    // Public API Methods
    // ==========================================

    removeWidget(widgetId) {
        const widget = this.widgets.get(widgetId);
        if (!widget) return;

        // Clear auto-refresh interval
        if (this.updateIntervals.has(widgetId)) {
            clearInterval(this.updateIntervals.get(widgetId));
            this.updateIntervals.delete(widgetId);
        }

        // Destroy chart instance
        if (this.chartInstances.has(widgetId)) {
            this.chartInstances.get(widgetId).destroy();
            this.chartInstances.delete(widgetId);
        }

        // Remove from widgets map
        this.widgets.delete(widgetId);

        // Clear container
        widget.container.innerHTML = '';
    }

    getWidget(widgetId) {
        return this.widgets.get(widgetId);
    }

    getAllWidgets() {
        return Array.from(this.widgets.values());
    }

    destroy() {
        // Clear all intervals
        this.updateIntervals.forEach(intervalId => clearInterval(intervalId));
        this.updateIntervals.clear();

        // Destroy all charts
        this.chartInstances.forEach(chart => chart.destroy());
        this.chartInstances.clear();

        // Close WebSocket
        if (this.ws) {
            this.ws.close();
        }

        // Clear widgets
        this.widgets.clear();
    }
}

// Export for module systems or make globally available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardWidgets;
} else {
    window.DashboardWidgets = DashboardWidgets;
}