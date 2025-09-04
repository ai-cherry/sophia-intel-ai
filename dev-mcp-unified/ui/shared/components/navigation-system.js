/**
 * Navigation System Component
 * 7-tab navigation structure with active state management and responsive design
 * Designed for both Sophia and Artemis UIs
 */

class NavigationSystem {
    constructor(options = {}) {
        this.options = {
            containerId: 'navigation-container',
            theme: options.theme || 'dark',
            enableBadges: options.enableBadges !== false,
            enableIcons: options.enableIcons !== false,
            enableSearch: options.enableSearch !== false,
            enableKeyboardNav: options.enableKeyboardNav !== false,
            defaultTab: options.defaultTab || 'dashboard',
            persistActiveTab: options.persistActiveTab !== false,
            ...options
        };

        this.state = {
            activeTab: this.loadActiveTab() || this.options.defaultTab,
            tabHistory: [],
            badges: new Map(),
            searchTerm: '',
            collapsedSidebar: false
        };

        this.tabs = this.getDefaultTabs();
        this.callbacks = {
            onTabChange: options.onTabChange || (() => {}),
            onTabInit: options.onTabInit || (() => {}),
            onSearchChange: options.onSearchChange || (() => {})
        };

        this.init();
    }

    getDefaultTabs() {
        return [
            {
                id: 'dashboard',
                label: 'Dashboard',
                icon: `<svg viewBox="0 0 24 24"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>`,
                description: 'System overview and key metrics',
                hasSubMenu: false,
                enabled: true,
                badge: null
            },
            {
                id: 'chat',
                label: 'Chat',
                icon: `<svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
                description: 'AI conversation interface',
                hasSubMenu: true,
                subMenuItems: [
                    { id: 'chat-sophia', label: 'Sophia', icon: '🧠' },
                    { id: 'chat-artemis', label: 'Artemis', icon: '🔬' },
                    { id: 'chat-atlas', label: 'Atlas', icon: '📊' },
                    { id: 'chat-hermes', label: 'Hermes', icon: '📨' },
                    { id: 'chat-minerva', label: 'Minerva', icon: '📚' }
                ],
                enabled: true,
                badge: null
            },
            {
                id: 'intelligence',
                label: 'Intelligence Hub',
                icon: `<svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`,
                description: 'Data analysis and insights',
                hasSubMenu: true,
                subMenuItems: [
                    { id: 'intelligence-analytics', label: 'Analytics', icon: '📈' },
                    { id: 'intelligence-reports', label: 'Reports', icon: '📄' },
                    { id: 'intelligence-insights', label: 'AI Insights', icon: '💡' },
                    { id: 'intelligence-predictions', label: 'Predictions', icon: '🔮' }
                ],
                enabled: true,
                badge: null
            },
            {
                id: 'swarms',
                label: 'Agent Swarms',
                icon: `<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>`,
                description: 'Multi-agent coordination and deployment',
                hasSubMenu: true,
                subMenuItems: [
                    { id: 'swarms-active', label: 'Active Swarms', icon: '🚀' },
                    { id: 'swarms-templates', label: 'Templates', icon: '📋' },
                    { id: 'swarms-monitor', label: 'Monitor', icon: '👁️' },
                    { id: 'swarms-logs', label: 'Logs', icon: '📊' }
                ],
                enabled: true,
                badge: null
            },
            {
                id: 'business',
                label: 'Business Intelligence',
                icon: `<svg viewBox="0 0 24 24"><path d="M7 2v11h3v9l7-12h-4l3-8z"/></svg>`,
                description: 'Sales, marketing, and business analytics',
                hasSubMenu: true,
                subMenuItems: [
                    { id: 'business-sales', label: 'Sales Dashboard', icon: '💰' },
                    { id: 'business-marketing', label: 'Marketing', icon: '📢' },
                    { id: 'business-crm', label: 'CRM Integration', icon: '👥' },
                    { id: 'business-forecasting', label: 'Forecasting', icon: '📊' }
                ],
                enabled: true,
                badge: null
            },
            {
                id: 'training',
                label: 'Brain Training',
                icon: `<svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`,
                description: 'Model training and fine-tuning',
                hasSubMenu: true,
                subMenuItems: [
                    { id: 'training-datasets', label: 'Datasets', icon: '🗃️' },
                    { id: 'training-models', label: 'Models', icon: '🧠' },
                    { id: 'training-jobs', label: 'Training Jobs', icon: '⚙️' },
                    { id: 'training-evaluation', label: 'Evaluation', icon: '📏' }
                ],
                enabled: true,
                badge: null
            },
            {
                id: 'settings',
                label: 'Settings',
                icon: `<svg viewBox="0 0 24 24"><path d="M12 15.5A3.5 3.5 0 0 1 8.5 12A3.5 3.5 0 0 1 12 8.5a3.5 3.5 0 0 1 3.5 3.5 3.5 3.5 0 0 1-3.5 3.5m7.43-2.53c.04-.32.07-.64.07-.97 0-.33-.03-.66-.07-1l2.11-1.63c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.31-.61-.22l-2.49 1c-.52-.39-1.06-.73-1.69-.98l-.37-2.65A.506.506 0 0 0 14 2h-4c-.25 0-.46.18-.5.42l-.37 2.65c-.63.25-1.17.59-1.69.98l-2.49-1c-.22-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64L4.57 11c-.04.34-.07.67-.07 1 0 .33.03.65.07.97l-2.11 1.66c-.19.15-.25.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1.01c.52.4 1.06.74 1.69.99l.37 2.65c.04.24.25.42.5.42h4c.25 0 .46-.18.5-.42l.37-2.65c.63-.26 1.17-.59 1.69-.99l2.49 1.01c.22.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.66Z"/></svg>`,
                description: 'System configuration and preferences',
                hasSubMenu: true,
                subMenuItems: [
                    { id: 'settings-general', label: 'General', icon: '⚙️' },
                    { id: 'settings-api', label: 'API Keys', icon: '🔑' },
                    { id: 'settings-users', label: 'User Management', icon: '👤' },
                    { id: 'settings-security', label: 'Security', icon: '🔒' },
                    { id: 'settings-integrations', label: 'Integrations', icon: '🔌' }
                ],
                enabled: true,
                badge: null
            }
        ];
    }

    init() {
        this.createNavigationUI();
        this.bindEvents();
        this.setActiveTab(this.state.activeTab);
        
        if (this.options.enableKeyboardNav) {
            this.setupKeyboardNavigation();
        }

        // Load collapsed state
        const collapsed = localStorage.getItem('sophia_sidebar_collapsed');
        if (collapsed === 'true') {
            this.toggleSidebar();
        }
    }

    createNavigationUI() {
        const container = document.getElementById(this.options.containerId);
        if (!container) {
            console.error(`Navigation container '${this.options.containerId}' not found`);
            return;
        }

        container.innerHTML = `
            <nav class="navigation-system" data-theme="${this.options.theme}">
                <!-- Mobile Header -->
                <div class="mobile-header">
                    <button class="mobile-menu-toggle" id="mobile-menu-toggle">
                        <svg viewBox="0 0 24 24">
                            <path d="M3 12h18M3 6h18M3 18h18"/>
                        </svg>
                    </button>
                    <div class="mobile-title">
                        <span class="active-tab-label">${this.getTabLabel(this.state.activeTab)}</span>
                    </div>
                    ${this.options.enableSearch ? `
                        <button class="mobile-search-toggle" id="mobile-search-toggle">
                            <svg viewBox="0 0 24 24">
                                <circle cx="11" cy="11" r="8"/>
                                <path d="m21 21-4.35-4.35"/>
                            </svg>
                        </button>
                    ` : ''}
                </div>

                <!-- Sidebar -->
                <div class="navigation-sidebar ${this.state.collapsedSidebar ? 'collapsed' : ''}" id="navigation-sidebar">
                    <!-- Sidebar Header -->
                    <div class="sidebar-header">
                        <div class="brand-logo">
                            <div class="logo-icon">🧠</div>
                            <div class="brand-text">
                                <div class="brand-name">Sophia Intel AI</div>
                                <div class="brand-tagline">Unified Intelligence Platform</div>
                            </div>
                        </div>
                        <button class="sidebar-collapse" id="sidebar-collapse" title="Collapse sidebar">
                            <svg viewBox="0 0 24 24">
                                <path d="M15 18l-6-6 6-6"/>
                            </svg>
                        </button>
                    </div>

                    ${this.options.enableSearch ? `
                        <!-- Search -->
                        <div class="navigation-search">
                            <div class="search-wrapper">
                                <svg class="search-icon" viewBox="0 0 24 24">
                                    <circle cx="11" cy="11" r="8"/>
                                    <path d="m21 21-4.35-4.35"/>
                                </svg>
                                <input 
                                    type="search" 
                                    class="search-input" 
                                    id="navigation-search"
                                    placeholder="Search..."
                                    autocomplete="off"
                                >
                                <button class="search-clear" id="search-clear" style="display: none;">
                                    <svg viewBox="0 0 24 24">
                                        <line x1="18" y1="6" x2="6" y2="18"/>
                                        <line x1="6" y1="6" x2="18" y2="18"/>
                                    </svg>
                                </button>
                            </div>
                            <div class="search-results" id="search-results" style="display: none;"></div>
                        </div>
                    ` : ''}

                    <!-- Navigation Tabs -->
                    <div class="navigation-tabs" id="navigation-tabs">
                        ${this.renderTabs()}
                    </div>

                    <!-- Sidebar Footer -->
                    <div class="sidebar-footer">
                        <div class="connection-status">
                            <div class="status-indicator connected"></div>
                            <span class="status-text">Connected</span>
                        </div>
                        <div class="version-info">v1.0.0</div>
                    </div>
                </div>

                <!-- Mobile Menu Overlay -->
                <div class="mobile-overlay" id="mobile-overlay"></div>
            </nav>
        `;
    }

    renderTabs() {
        return this.tabs.map(tab => this.renderTab(tab)).join('');
    }

    renderTab(tab) {
        const isActive = tab.id === this.state.activeTab;
        const badge = this.state.badges.get(tab.id);
        
        return `
            <div class="nav-tab ${isActive ? 'active' : ''} ${!tab.enabled ? 'disabled' : ''}" 
                 data-tab-id="${tab.id}" 
                 data-has-submenu="${tab.hasSubMenu}">
                <div class="tab-main" role="button" tabindex="${tab.enabled ? '0' : '-1'}">
                    ${this.options.enableIcons ? `<div class="tab-icon">${tab.icon}</div>` : ''}
                    <div class="tab-content">
                        <div class="tab-label">${tab.label}</div>
                        <div class="tab-description">${tab.description}</div>
                    </div>
                    ${badge ? `<div class="tab-badge" data-badge-type="${badge.type}">${badge.count}</div>` : ''}
                    ${tab.hasSubMenu ? `
                        <div class="submenu-toggle">
                            <svg viewBox="0 0 24 24">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </div>
                    ` : ''}
                </div>
                ${tab.hasSubMenu ? `
                    <div class="submenu ${isActive ? 'expanded' : ''}" id="submenu-${tab.id}">
                        ${tab.subMenuItems ? tab.subMenuItems.map(item => `
                            <div class="submenu-item" data-tab-id="${item.id}">
                                <div class="submenu-icon">${item.icon}</div>
                                <div class="submenu-label">${item.label}</div>
                            </div>
                        `).join('') : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }

    bindEvents() {
        // Tab click events
        const tabElements = document.querySelectorAll('.tab-main');
        tabElements.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabId = tab.closest('.nav-tab').dataset.tabId;
                if (tab.closest('.nav-tab').classList.contains('disabled')) return;
                
                this.handleTabClick(tabId, e);
            });

            // Keyboard support for tabs
            tab.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const tabId = tab.closest('.nav-tab').dataset.tabId;
                    if (!tab.closest('.nav-tab').classList.contains('disabled')) {
                        this.handleTabClick(tabId, e);
                    }
                }
            });
        });

        // Submenu item clicks
        const submenuItems = document.querySelectorAll('.submenu-item');
        submenuItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const tabId = item.dataset.tabId;
                this.setActiveTab(tabId);
                e.stopPropagation();
            });
        });

        // Sidebar collapse toggle
        const collapseBtn = document.getElementById('sidebar-collapse');
        collapseBtn?.addEventListener('click', () => {
            this.toggleSidebar();
        });

        // Mobile menu toggle
        const mobileToggle = document.getElementById('mobile-menu-toggle');
        const mobileOverlay = document.getElementById('mobile-overlay');
        
        mobileToggle?.addEventListener('click', () => {
            this.toggleMobileMenu();
        });

        mobileOverlay?.addEventListener('click', () => {
            this.closeMobileMenu();
        });

        // Search functionality
        if (this.options.enableSearch) {
            this.bindSearchEvents();
        }

        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    bindSearchEvents() {
        const searchInput = document.getElementById('navigation-search');
        const searchClear = document.getElementById('search-clear');
        const searchResults = document.getElementById('search-results');

        searchInput?.addEventListener('input', (e) => {
            const searchTerm = e.target.value;
            this.handleSearch(searchTerm);
            
            if (searchTerm) {
                searchClear.style.display = 'block';
                searchResults.style.display = 'block';
            } else {
                searchClear.style.display = 'none';
                searchResults.style.display = 'none';
            }
        });

        searchClear?.addEventListener('click', () => {
            searchInput.value = '';
            searchClear.style.display = 'none';
            searchResults.style.display = 'none';
            this.handleSearch('');
        });

        // Mobile search toggle
        const mobileSearchToggle = document.getElementById('mobile-search-toggle');
        mobileSearchToggle?.addEventListener('click', () => {
            this.toggleMobileSearch();
        });
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Alt + 1-7 for quick tab navigation
            if (e.altKey && !e.ctrlKey && !e.shiftKey) {
                const num = parseInt(e.key);
                if (num >= 1 && num <= this.tabs.length) {
                    e.preventDefault();
                    const tab = this.tabs[num - 1];
                    if (tab.enabled) {
                        this.setActiveTab(tab.id);
                    }
                }
            }

            // Alt + / for search focus
            if (e.altKey && e.key === '/' && this.options.enableSearch) {
                e.preventDefault();
                const searchInput = document.getElementById('navigation-search');
                searchInput?.focus();
            }

            // Escape to close mobile menu or clear search
            if (e.key === 'Escape') {
                this.closeMobileMenu();
                this.clearSearch();
            }
        });
    }

    handleTabClick(tabId, event) {
        const tab = this.getTab(tabId);
        if (!tab || !tab.enabled) return;

        // Handle submenu toggle
        if (tab.hasSubMenu && !event.target.closest('.submenu')) {
            this.toggleSubmenu(tabId);
        }

        // Set active tab
        this.setActiveTab(tabId);
    }

    toggleSubmenu(tabId) {
        const submenu = document.getElementById(`submenu-${tabId}`);
        const tabElement = document.querySelector(`[data-tab-id="${tabId}"]`);
        
        if (submenu && tabElement) {
            const isExpanded = submenu.classList.contains('expanded');
            
            // Close all other submenus first
            document.querySelectorAll('.submenu.expanded').forEach(menu => {
                if (menu !== submenu) {
                    menu.classList.remove('expanded');
                }
            });
            
            // Toggle current submenu
            submenu.classList.toggle('expanded', !isExpanded);
            tabElement.setAttribute('data-submenu-expanded', !isExpanded);
        }
    }

    setActiveTab(tabId, skipCallback = false) {
        if (this.state.activeTab === tabId) return;

        // Remove active class from all tabs
        document.querySelectorAll('.nav-tab.active').forEach(tab => {
            tab.classList.remove('active');
        });

        // Add active class to current tab
        const activeTabElement = document.querySelector(`[data-tab-id="${tabId}"]`);
        if (activeTabElement) {
            activeTabElement.classList.add('active');
            
            // Expand parent submenu if this is a submenu item
            const submenu = activeTabElement.closest('.submenu');
            if (submenu) {
                submenu.classList.add('expanded');
                const parentTab = submenu.closest('.nav-tab');
                if (parentTab) {
                    parentTab.classList.add('active');
                    parentTab.setAttribute('data-submenu-expanded', 'true');
                }
            }
        }

        // Update state
        const previousTab = this.state.activeTab;
        this.state.activeTab = tabId;
        
        // Update tab history
        if (previousTab && previousTab !== tabId) {
            this.state.tabHistory.unshift(previousTab);
            if (this.state.tabHistory.length > 10) {
                this.state.tabHistory.pop();
            }
        }

        // Update mobile title
        const mobileTitle = document.querySelector('.active-tab-label');
        if (mobileTitle) {
            mobileTitle.textContent = this.getTabLabel(tabId);
        }

        // Save active tab
        if (this.options.persistActiveTab) {
            this.saveActiveTab(tabId);
        }

        // Close mobile menu if open
        this.closeMobileMenu();

        // Trigger callback
        if (!skipCallback) {
            this.callbacks.onTabChange(tabId, previousTab);
        }
    }

    handleSearch(searchTerm) {
        this.state.searchTerm = searchTerm;
        const results = this.searchTabs(searchTerm);
        this.renderSearchResults(results);
        this.callbacks.onSearchChange(searchTerm, results);
    }

    searchTabs(searchTerm) {
        if (!searchTerm) return [];

        const results = [];
        const term = searchTerm.toLowerCase();

        this.tabs.forEach(tab => {
            // Search main tab
            if (tab.label.toLowerCase().includes(term) || 
                tab.description.toLowerCase().includes(term)) {
                results.push({
                    type: 'tab',
                    tab: tab,
                    matches: this.getSearchMatches(tab, term)
                });
            }

            // Search submenu items
            if (tab.subMenuItems) {
                tab.subMenuItems.forEach(item => {
                    if (item.label.toLowerCase().includes(term)) {
                        results.push({
                            type: 'submenu',
                            tab: tab,
                            item: item,
                            matches: this.getSearchMatches(item, term)
                        });
                    }
                });
            }
        });

        return results;
    }

    getSearchMatches(item, term) {
        const matches = [];
        if (item.label.toLowerCase().includes(term)) {
            matches.push('label');
        }
        if (item.description && item.description.toLowerCase().includes(term)) {
            matches.push('description');
        }
        return matches;
    }

    renderSearchResults(results) {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;

        if (results.length === 0) {
            searchResults.innerHTML = `
                <div class="search-no-results">
                    <div class="no-results-icon">🔍</div>
                    <div class="no-results-text">No results found</div>
                </div>
            `;
            return;
        }

        searchResults.innerHTML = results.map(result => `
            <div class="search-result" data-tab-id="${result.type === 'submenu' ? result.item.id : result.tab.id}">
                <div class="result-icon">
                    ${result.type === 'submenu' ? result.item.icon : result.tab.icon}
                </div>
                <div class="result-content">
                    <div class="result-title">
                        ${result.type === 'submenu' ? result.item.label : result.tab.label}
                    </div>
                    <div class="result-path">
                        ${result.type === 'submenu' ? `${result.tab.label} > ${result.item.label}` : result.tab.description}
                    </div>
                </div>
                <div class="result-type">${result.type}</div>
            </div>
        `).join('');

        // Bind click events to search results
        searchResults.querySelectorAll('.search-result').forEach(result => {
            result.addEventListener('click', () => {
                const tabId = result.dataset.tabId;
                this.setActiveTab(tabId);
                this.clearSearch();
            });
        });
    }

    clearSearch() {
        const searchInput = document.getElementById('navigation-search');
        const searchClear = document.getElementById('search-clear');
        const searchResults = document.getElementById('search-results');

        if (searchInput) searchInput.value = '';
        if (searchClear) searchClear.style.display = 'none';
        if (searchResults) searchResults.style.display = 'none';
        
        this.state.searchTerm = '';
    }

    toggleSidebar() {
        const sidebar = document.getElementById('navigation-sidebar');
        if (!sidebar) return;

        this.state.collapsedSidebar = !this.state.collapsedSidebar;
        sidebar.classList.toggle('collapsed', this.state.collapsedSidebar);

        // Update collapse button icon
        const collapseBtn = document.getElementById('sidebar-collapse');
        if (collapseBtn) {
            const svg = collapseBtn.querySelector('svg path');
            if (this.state.collapsedSidebar) {
                svg.setAttribute('d', 'M9 18l6-6-6-6'); // Right arrow
            } else {
                svg.setAttribute('d', 'M15 18l-6-6 6-6'); // Left arrow
            }
        }

        // Save state
        localStorage.setItem('sophia_sidebar_collapsed', this.state.collapsedSidebar.toString());

        // Emit event
        const event = new CustomEvent('sidebar-toggle', {
            detail: { collapsed: this.state.collapsedSidebar }
        });
        document.dispatchEvent(event);
    }

    toggleMobileMenu() {
        const sidebar = document.getElementById('navigation-sidebar');
        const overlay = document.getElementById('mobile-overlay');
        
        if (sidebar && overlay) {
            sidebar.classList.add('mobile-open');
            overlay.classList.add('active');
            document.body.classList.add('mobile-menu-open');
        }
    }

    closeMobileMenu() {
        const sidebar = document.getElementById('navigation-sidebar');
        const overlay = document.getElementById('mobile-overlay');
        
        if (sidebar && overlay) {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
            document.body.classList.remove('mobile-menu-open');
        }
    }

    toggleMobileSearch() {
        const sidebar = document.getElementById('navigation-sidebar');
        const searchInput = document.getElementById('navigation-search');
        
        if (sidebar) {
            sidebar.classList.add('search-focused');
            searchInput?.focus();
        }
    }

    handleResize() {
        // Close mobile menu on resize to desktop
        if (window.innerWidth > 768) {
            this.closeMobileMenu();
        }
    }

    // ==========================================
    // Public API Methods
    // ==========================================

    getTab(tabId) {
        return this.tabs.find(tab => tab.id === tabId);
    }

    getTabLabel(tabId) {
        const tab = this.getTab(tabId);
        if (!tab) return 'Unknown';

        // Check if it's a submenu item
        for (const mainTab of this.tabs) {
            if (mainTab.subMenuItems) {
                const subItem = mainTab.subMenuItems.find(item => item.id === tabId);
                if (subItem) {
                    return `${mainTab.label} > ${subItem.label}`;
                }
            }
        }

        return tab.label;
    }

    addTab(tab, position = -1) {
        if (position === -1) {
            this.tabs.push(tab);
        } else {
            this.tabs.splice(position, 0, tab);
        }
        this.refreshTabs();
    }

    removeTab(tabId) {
        this.tabs = this.tabs.filter(tab => tab.id !== tabId);
        
        // Switch to another tab if the active tab was removed
        if (this.state.activeTab === tabId) {
            const fallbackTab = this.tabs.find(tab => tab.enabled);
            if (fallbackTab) {
                this.setActiveTab(fallbackTab.id);
            }
        }
        
        this.refreshTabs();
    }

    updateTab(tabId, updates) {
        const tab = this.getTab(tabId);
        if (tab) {
            Object.assign(tab, updates);
            this.refreshTabs();
        }
    }

    enableTab(tabId) {
        const tab = this.getTab(tabId);
        if (tab) {
            tab.enabled = true;
            this.updateTabElement(tabId);
        }
    }

    disableTab(tabId) {
        const tab = this.getTab(tabId);
        if (tab) {
            tab.enabled = false;
            
            // Switch away if this was the active tab
            if (this.state.activeTab === tabId) {
                const fallbackTab = this.tabs.find(tab => tab.enabled);
                if (fallbackTab) {
                    this.setActiveTab(fallbackTab.id);
                }
            }
            
            this.updateTabElement(tabId);
        }
    }

    setBadge(tabId, badge) {
        if (badge) {
            this.state.badges.set(tabId, badge);
        } else {
            this.state.badges.delete(tabId);
        }
        this.updateTabBadge(tabId);
    }

    clearBadge(tabId) {
        this.setBadge(tabId, null);
    }

    getCurrentTab() {
        return this.state.activeTab;
    }

    getTabHistory() {
        return [...this.state.tabHistory];
    }

    goToPreviousTab() {
        if (this.state.tabHistory.length > 0) {
            const previousTab = this.state.tabHistory[0];
            this.setActiveTab(previousTab);
        }
    }

    refreshTabs() {
        const tabsContainer = document.getElementById('navigation-tabs');
        if (tabsContainer) {
            tabsContainer.innerHTML = this.renderTabs();
            this.bindTabEvents();
        }
    }

    bindTabEvents() {
        // Rebind events after refresh
        const tabElements = document.querySelectorAll('.tab-main');
        tabElements.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabId = tab.closest('.nav-tab').dataset.tabId;
                if (tab.closest('.nav-tab').classList.contains('disabled')) return;
                this.handleTabClick(tabId, e);
            });
        });

        const submenuItems = document.querySelectorAll('.submenu-item');
        submenuItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const tabId = item.dataset.tabId;
                this.setActiveTab(tabId);
                e.stopPropagation();
            });
        });
    }

    updateTabElement(tabId) {
        const tabElement = document.querySelector(`[data-tab-id="${tabId}"]`);
        const tab = this.getTab(tabId);
        
        if (tabElement && tab) {
            tabElement.classList.toggle('disabled', !tab.enabled);
            const tabMain = tabElement.querySelector('.tab-main');
            if (tabMain) {
                tabMain.setAttribute('tabindex', tab.enabled ? '0' : '-1');
            }
        }
    }

    updateTabBadge(tabId) {
        const tabElement = document.querySelector(`[data-tab-id="${tabId}"]`);
        if (!tabElement) return;

        const existingBadge = tabElement.querySelector('.tab-badge');
        const badge = this.state.badges.get(tabId);

        if (badge) {
            if (existingBadge) {
                existingBadge.textContent = badge.count;
                existingBadge.setAttribute('data-badge-type', badge.type);
            } else {
                const badgeElement = document.createElement('div');
                badgeElement.className = 'tab-badge';
                badgeElement.setAttribute('data-badge-type', badge.type);
                badgeElement.textContent = badge.count;
                
                const tabContent = tabElement.querySelector('.tab-content');
                if (tabContent) {
                    tabContent.after(badgeElement);
                }
            }
        } else if (existingBadge) {
            existingBadge.remove();
        }
    }

    // Storage methods
    saveActiveTab(tabId) {
        try {
            localStorage.setItem('sophia_active_tab', tabId);
        } catch (error) {
            console.warn('Failed to save active tab:', error);
        }
    }

    loadActiveTab() {
        try {
            return localStorage.getItem('sophia_active_tab');
        } catch (error) {
            console.warn('Failed to load active tab:', error);
            return null;
        }
    }

    // Cleanup
    destroy() {
        // Remove event listeners
        window.removeEventListener('resize', this.handleResize);
        document.removeEventListener('keydown', this.setupKeyboardNavigation);
        
        // Clear state
        this.state.badges.clear();
        this.tabs = [];
        
        // Clear container
        const container = document.getElementById(this.options.containerId);
        if (container) {
            container.innerHTML = '';
        }
    }
}

// Export for module systems or make globally available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NavigationSystem;
} else {
    window.NavigationSystem = NavigationSystem;
}