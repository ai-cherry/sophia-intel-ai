/**
 * Unified API Client
 * Comprehensive API communication, WebSocket management, error handling, and authentication
 * Designed for both Sophia and Artemis UIs
 */

class ApiClient {
    constructor(options = {}) {
        this.options = {
            baseURL: options.baseURL || 'http://127.0.0.1:3333',
            wsURL: options.wsURL || 'ws://127.0.0.1:3333/ws',
            timeout: options.timeout || 30000,
            retryAttempts: options.retryAttempts || 3,
            retryDelay: options.retryDelay || 1000,
            enableWebSocket: options.enableWebSocket !== false,
            enableSSE: options.enableSSE !== false,
            enableAuth: options.enableAuth !== false,
            enableCache: options.enableCache !== false,
            cacheTimeout: options.cacheTimeout || 300000, // 5 minutes
            enableRateLimit: options.enableRateLimit !== false,
            rateLimit: options.rateLimit || { requests: 100, period: 60000 }, // 100 req/min
            ...options
        };

        // Core state
        this.state = {
            connected: false,
            authenticated: false,
            user: null,
            connectionAttempts: 0,
            maxConnectionAttempts: 5,
            isOnline: navigator.onLine
        };

        // Authentication state
        this.auth = {
            token: null,
            refreshToken: null,
            expiresAt: null,
            user: null
        };

        // WebSocket management
        this.ws = null;
        this.wsReconnectTimer = null;
        this.wsHeartbeatTimer = null;
        this.wsSubscriptions = new Map();
        this.wsMessageQueue = [];

        // Request management
        this.activeRequests = new Map();
        this.requestCache = new Map();
        this.rateLimiter = {
            requests: [],
            blocked: false
        };

        // Event emitters
        this.eventListeners = new Map();
        
        this.init();
    }

    async init() {
        this.loadAuthFromStorage();
        this.setupNetworkListeners();
        this.setupRateLimiter();
        
        if (this.options.enableWebSocket) {
            await this.connectWebSocket();
        }
        
        if (this.auth.token) {
            await this.validateToken();
        }
    }

    // ==========================================
    // Authentication Methods
    // ==========================================

    async login(credentials) {
        try {
            const response = await this.post('/auth/login', credentials, { skipAuth: true });
            
            if (response.success) {
                this.auth.token = response.data.access_token;
                this.auth.refreshToken = response.data.refresh_token;
                this.auth.expiresAt = new Date(Date.now() + response.data.expires_in * 1000);
                this.auth.user = response.data.user;
                
                this.state.authenticated = true;
                this.state.user = response.data.user;
                
                this.saveAuthToStorage();
                this.emit('auth:login', this.auth.user);
                
                return { success: true, user: this.auth.user };
            } else {
                throw new Error(response.error || 'Login failed');
            }
        } catch (error) {
            this.emit('auth:error', error);
            throw error;
        }
    }

    async logout() {
        try {
            if (this.auth.token) {
                await this.post('/auth/logout', {}, { skipRetry: true });
            }
        } catch (error) {
            console.warn('Logout request failed:', error);
        } finally {
            this.clearAuth();
            this.emit('auth:logout');
        }
    }

    async refreshAccessToken() {
        if (!this.auth.refreshToken) {
            throw new Error('No refresh token available');
        }

        try {
            const response = await this.post('/auth/refresh', {
                refresh_token: this.auth.refreshToken
            }, { skipAuth: true });

            if (response.success) {
                this.auth.token = response.data.access_token;
                this.auth.expiresAt = new Date(Date.now() + response.data.expires_in * 1000);
                
                this.saveAuthToStorage();
                this.emit('auth:refresh', this.auth.token);
                
                return this.auth.token;
            } else {
                throw new Error(response.error || 'Token refresh failed');
            }
        } catch (error) {
            this.clearAuth();
            this.emit('auth:expired');
            throw error;
        }
    }

    async validateToken() {
        if (!this.auth.token) return false;

        try {
            const response = await this.get('/auth/validate');
            if (response.success) {
                this.state.authenticated = true;
                this.state.user = response.data.user;
                return true;
            } else {
                this.clearAuth();
                return false;
            }
        } catch (error) {
            this.clearAuth();
            return false;
        }
    }

    isTokenExpired() {
        return this.auth.expiresAt && new Date() >= this.auth.expiresAt;
    }

    async ensureValidToken() {
        if (!this.auth.token) {
            throw new Error('No authentication token');
        }

        if (this.isTokenExpired()) {
            await this.refreshAccessToken();
        }

        return this.auth.token;
    }

    clearAuth() {
        this.auth = {
            token: null,
            refreshToken: null,
            expiresAt: null,
            user: null
        };
        this.state.authenticated = false;
        this.state.user = null;
        
        this.removeAuthFromStorage();
    }

    saveAuthToStorage() {
        try {
            const authData = {
                token: this.auth.token,
                refreshToken: this.auth.refreshToken,
                expiresAt: this.auth.expiresAt?.toISOString(),
                user: this.auth.user
            };
            localStorage.setItem('sophia_auth', JSON.stringify(authData));
        } catch (error) {
            console.warn('Failed to save auth to storage:', error);
        }
    }

    loadAuthFromStorage() {
        try {
            const authData = localStorage.getItem('sophia_auth');
            if (authData) {
                const parsed = JSON.parse(authData);
                this.auth.token = parsed.token;
                this.auth.refreshToken = parsed.refreshToken;
                this.auth.expiresAt = parsed.expiresAt ? new Date(parsed.expiresAt) : null;
                this.auth.user = parsed.user;
                
                if (this.auth.token && !this.isTokenExpired()) {
                    this.state.authenticated = true;
                    this.state.user = this.auth.user;
                }
            }
        } catch (error) {
            console.warn('Failed to load auth from storage:', error);
            this.clearAuth();
        }
    }

    removeAuthFromStorage() {
        try {
            localStorage.removeItem('sophia_auth');
        } catch (error) {
            console.warn('Failed to remove auth from storage:', error);
        }
    }

    // ==========================================
    // HTTP Request Methods
    // ==========================================

    async request(method, endpoint, data = null, options = {}) {
        const config = {
            timeout: options.timeout || this.options.timeout,
            skipAuth: options.skipAuth || false,
            skipRetry: options.skipRetry || false,
            skipCache: options.skipCache || false,
            useCache: options.useCache || false,
            retryAttempts: options.retryAttempts || this.options.retryAttempts,
            ...options
        };

        // Check rate limiting
        if (this.options.enableRateLimit && !config.skipRateLimit) {
            await this.checkRateLimit();
        }

        // Check cache
        const cacheKey = `${method}:${endpoint}:${JSON.stringify(data)}`;
        if (config.useCache && this.options.enableCache && !config.skipCache) {
            const cached = this.getFromCache(cacheKey);
            if (cached) {
                return cached;
            }
        }

        // Build URL
        const url = this.buildURL(endpoint);
        
        // Build headers
        const headers = await this.buildHeaders(config);

        // Build request configuration
        const requestConfig = {
            method: method.toUpperCase(),
            headers,
            signal: AbortSignal.timeout(config.timeout)
        };

        // Add body for non-GET requests
        if (data && method.toLowerCase() !== 'get') {
            if (data instanceof FormData) {
                requestConfig.body = data;
            } else {
                requestConfig.body = JSON.stringify(data);
            }
        }

        // Add query parameters for GET requests
        let finalUrl = url;
        if (data && method.toLowerCase() === 'get') {
            const params = new URLSearchParams();
            Object.entries(data).forEach(([key, value]) => {
                if (value !== null && value !== undefined) {
                    params.append(key, value);
                }
            });
            if (params.toString()) {
                finalUrl += `?${params.toString()}`;
            }
        }

        // Execute request with retry logic
        let lastError;
        const maxAttempts = config.skipRetry ? 1 : config.retryAttempts + 1;
        
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                const requestId = this.generateRequestId();
                this.activeRequests.set(requestId, { url: finalUrl, method, timestamp: Date.now() });

                this.emit('request:start', { requestId, url: finalUrl, method });

                const response = await fetch(finalUrl, requestConfig);
                
                this.activeRequests.delete(requestId);
                this.emit('request:complete', { requestId, url: finalUrl, method, status: response.status });

                if (!response.ok) {
                    if (response.status === 401 && !config.skipAuth && this.auth.token) {
                        // Token might be expired, try to refresh
                        try {
                            await this.refreshAccessToken();
                            // Retry request with new token
                            const newHeaders = await this.buildHeaders(config);
                            requestConfig.headers = newHeaders;
                            const retryResponse = await fetch(finalUrl, requestConfig);
                            
                            if (retryResponse.ok) {
                                const result = await this.parseResponse(retryResponse);
                                this.storeInCache(cacheKey, result, config);
                                return result;
                            }
                        } catch (refreshError) {
                            console.warn('Token refresh failed:', refreshError);
                        }
                    }

                    const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
                    error.status = response.status;
                    error.response = response;
                    throw error;
                }

                const result = await this.parseResponse(response);
                
                // Store in cache if enabled
                this.storeInCache(cacheKey, result, config);
                
                return result;

            } catch (error) {
                lastError = error;
                
                this.emit('request:error', { url: finalUrl, method, error, attempt });

                // Don't retry on certain errors
                if (error.name === 'AbortError' || error.status === 401 || error.status === 403) {
                    break;
                }

                // Don't retry on last attempt
                if (attempt === maxAttempts) {
                    break;
                }

                // Wait before retry
                await this.delay(config.retryDelay * attempt);
            }
        }

        throw lastError;
    }

    async get(endpoint, params = null, options = {}) {
        return this.request('GET', endpoint, params, { useCache: true, ...options });
    }

    async post(endpoint, data = null, options = {}) {
        return this.request('POST', endpoint, data, options);
    }

    async put(endpoint, data = null, options = {}) {
        return this.request('PUT', endpoint, data, options);
    }

    async patch(endpoint, data = null, options = {}) {
        return this.request('PATCH', endpoint, data, options);
    }

    async delete(endpoint, options = {}) {
        return this.request('DELETE', endpoint, null, options);
    }

    // ==========================================
    // Streaming and SSE Methods
    // ==========================================

    async *streamRequest(endpoint, data = null, options = {}) {
        const url = this.buildURL(endpoint);
        const headers = await this.buildHeaders(options);
        
        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            yield data;
                        } catch (error) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }

    createEventSource(endpoint, options = {}) {
        if (!this.options.enableSSE) {
            throw new Error('SSE is disabled');
        }

        const url = this.buildURL(endpoint);
        const eventSource = new EventSource(url);
        
        eventSource.addEventListener('open', () => {
            this.emit('sse:connected', endpoint);
        });

        eventSource.addEventListener('error', (error) => {
            this.emit('sse:error', { endpoint, error });
        });

        eventSource.addEventListener('message', (event) => {
            try {
                const data = JSON.parse(event.data);
                this.emit('sse:message', { endpoint, data });
            } catch (error) {
                console.warn('Failed to parse SSE message:', event.data);
            }
        });

        return eventSource;
    }

    // ==========================================
    // WebSocket Methods
    // ==========================================

    async connectWebSocket() {
        if (!this.options.enableWebSocket) return;

        try {
            // Close existing connection
            if (this.ws) {
                this.ws.close();
            }

            // Build WebSocket URL with auth if available
            let wsUrl = this.options.wsURL;
            if (this.auth.token) {
                const urlObj = new URL(wsUrl);
                urlObj.searchParams.set('token', this.auth.token);
                wsUrl = urlObj.toString();
            }

            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.state.connected = true;
                this.state.connectionAttempts = 0;
                this.emit('ws:connected');
                
                // Send queued messages
                this.wsMessageQueue.forEach(message => {
                    this.ws.send(JSON.stringify(message));
                });
                this.wsMessageQueue = [];
                
                // Start heartbeat
                this.startWebSocketHeartbeat();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.warn('Failed to parse WebSocket message:', event.data);
                }
            };

            this.ws.onclose = (event) => {
                this.state.connected = false;
                this.emit('ws:disconnected', event);
                
                this.stopWebSocketHeartbeat();
                
                // Attempt reconnection if not a clean close
                if (event.code !== 1000) {
                    this.scheduleWebSocketReconnect();
                }
            };

            this.ws.onerror = (error) => {
                this.emit('ws:error', error);
            };

        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.scheduleWebSocketReconnect();
        }
    }

    handleWebSocketMessage(data) {
        // Handle different message types
        switch (data.type) {
            case 'subscription':
                this.handleSubscriptionMessage(data);
                break;
            case 'broadcast':
                this.emit('ws:broadcast', data);
                break;
            case 'pong':
                // Heartbeat response
                break;
            default:
                this.emit('ws:message', data);
        }
    }

    handleSubscriptionMessage(data) {
        if (data.channel) {
            this.emit(`ws:${data.channel}`, data.payload);
        }
    }

    sendWebSocketMessage(message) {
        if (this.state.connected && this.ws) {
            this.ws.send(JSON.stringify(message));
        } else {
            this.wsMessageQueue.push(message);
        }
    }

    subscribe(channel, callback) {
        if (!this.options.enableWebSocket) {
            throw new Error('WebSocket is disabled');
        }

        // Store subscription
        if (!this.wsSubscriptions.has(channel)) {
            this.wsSubscriptions.set(channel, new Set());
        }
        this.wsSubscriptions.get(channel).add(callback);

        // Send subscription message
        this.sendWebSocketMessage({
            type: 'subscribe',
            channel: channel
        });

        // Add event listener
        this.on(`ws:${channel}`, callback);

        // Return unsubscribe function
        return () => {
            this.unsubscribe(channel, callback);
        };
    }

    unsubscribe(channel, callback = null) {
        if (callback) {
            // Remove specific callback
            if (this.wsSubscriptions.has(channel)) {
                this.wsSubscriptions.get(channel).delete(callback);
                
                // If no more callbacks, unsubscribe from channel
                if (this.wsSubscriptions.get(channel).size === 0) {
                    this.wsSubscriptions.delete(channel);
                    this.sendWebSocketMessage({
                        type: 'unsubscribe',
                        channel: channel
                    });
                }
            }
            this.off(`ws:${channel}`, callback);
        } else {
            // Remove all callbacks for channel
            this.wsSubscriptions.delete(channel);
            this.sendWebSocketMessage({
                type: 'unsubscribe',
                channel: channel
            });
            this.off(`ws:${channel}`);
        }
    }

    startWebSocketHeartbeat() {
        this.wsHeartbeatTimer = setInterval(() => {
            if (this.state.connected) {
                this.sendWebSocketMessage({ type: 'ping' });
            }
        }, 30000); // 30 seconds
    }

    stopWebSocketHeartbeat() {
        if (this.wsHeartbeatTimer) {
            clearInterval(this.wsHeartbeatTimer);
            this.wsHeartbeatTimer = null;
        }
    }

    scheduleWebSocketReconnect() {
        if (this.state.connectionAttempts >= this.state.maxConnectionAttempts) {
            console.error('Max WebSocket reconnection attempts reached');
            this.emit('ws:max_reconnect_attempts');
            return;
        }

        const delay = Math.min(1000 * Math.pow(2, this.state.connectionAttempts), 30000);
        this.state.connectionAttempts++;

        this.wsReconnectTimer = setTimeout(() => {
            console.log(`WebSocket reconnection attempt ${this.state.connectionAttempts}`);
            this.connectWebSocket();
        }, delay);
    }

    disconnectWebSocket() {
        if (this.wsReconnectTimer) {
            clearTimeout(this.wsReconnectTimer);
            this.wsReconnectTimer = null;
        }

        this.stopWebSocketHeartbeat();
        
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
        
        this.state.connected = false;
        this.wsSubscriptions.clear();
    }

    // ==========================================
    // Utility Methods
    // ==========================================

    buildURL(endpoint) {
        const baseURL = this.options.baseURL.replace(/\/$/, '');
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        return `${baseURL}${cleanEndpoint}`;
    }

    async buildHeaders(config = {}) {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Sophia-Intel-AI/1.0',
            ...config.headers
        };

        // Add auth header if enabled and token available
        if (this.options.enableAuth && !config.skipAuth && this.auth.token) {
            try {
                const token = await this.ensureValidToken();
                headers['Authorization'] = `Bearer ${token}`;
            } catch (error) {
                console.warn('Failed to get valid token:', error);
            }
        }

        // Remove Content-Type for FormData
        if (config.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        return headers;
    }

    async parseResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (contentType?.includes('application/json')) {
            const text = await response.text();
            try {
                // Parse JSON with proper error handling to prevent double-encoding issues
                return JSON.parse(text);
            } catch (error) {
                console.warn('Failed to parse JSON response:', text);
                return { error: 'Invalid JSON response', raw: text };
            }
        } else if (contentType?.includes('text/')) {
            return await response.text();
        } else {
            return await response.blob();
        }
    }

    generateRequestId() {
        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ==========================================
    // Cache Management
    // ==========================================

    storeInCache(key, data, config) {
        if (!this.options.enableCache || config.skipCache) return;

        const expiry = Date.now() + (config.cacheTimeout || this.options.cacheTimeout);
        this.requestCache.set(key, {
            data,
            expiry
        });
    }

    getFromCache(key) {
        if (!this.options.enableCache) return null;

        const cached = this.requestCache.get(key);
        if (cached && cached.expiry > Date.now()) {
            return cached.data;
        } else if (cached) {
            this.requestCache.delete(key);
        }
        return null;
    }

    clearCache() {
        this.requestCache.clear();
    }

    cleanExpiredCache() {
        const now = Date.now();
        for (const [key, value] of this.requestCache.entries()) {
            if (value.expiry <= now) {
                this.requestCache.delete(key);
            }
        }
    }

    // ==========================================
    // Rate Limiting
    // ==========================================

    setupRateLimiter() {
        if (!this.options.enableRateLimit) return;

        // Clean up old requests periodically
        setInterval(() => {
            const cutoff = Date.now() - this.options.rateLimit.period;
            this.rateLimiter.requests = this.rateLimiter.requests.filter(
                timestamp => timestamp > cutoff
            );
        }, this.options.rateLimit.period / 4);
    }

    async checkRateLimit() {
        if (!this.options.enableRateLimit) return;

        const now = Date.now();
        const cutoff = now - this.options.rateLimit.period;

        // Remove old requests
        this.rateLimiter.requests = this.rateLimiter.requests.filter(
            timestamp => timestamp > cutoff
        );

        // Check if we're over the limit
        if (this.rateLimiter.requests.length >= this.options.rateLimit.requests) {
            if (!this.rateLimiter.blocked) {
                this.rateLimiter.blocked = true;
                this.emit('rate_limit:blocked');
            }

            // Wait until we can make another request
            const oldestRequest = Math.min(...this.rateLimiter.requests);
            const waitTime = oldestRequest + this.options.rateLimit.period - now;
            
            if (waitTime > 0) {
                await this.delay(waitTime + 100); // Add small buffer
            }

            this.rateLimiter.blocked = false;
            this.emit('rate_limit:unblocked');
        }

        // Record this request
        this.rateLimiter.requests.push(now);
    }

    // ==========================================
    // Network Management
    // ==========================================

    setupNetworkListeners() {
        window.addEventListener('online', () => {
            this.state.isOnline = true;
            this.emit('network:online');
            
            // Reconnect WebSocket if needed
            if (this.options.enableWebSocket && !this.state.connected) {
                this.connectWebSocket();
            }
        });

        window.addEventListener('offline', () => {
            this.state.isOnline = false;
            this.emit('network:offline');
        });
    }

    // ==========================================
    // Event Management
    // ==========================================

    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, new Set());
        }
        this.eventListeners.get(event).add(callback);
    }

    off(event, callback = null) {
        if (callback) {
            this.eventListeners.get(event)?.delete(callback);
        } else {
            this.eventListeners.delete(event);
        }
    }

    emit(event, data = null) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    // ==========================================
    // Public API Methods
    // ==========================================

    getConnectionStatus() {
        return {
            http: this.state.isOnline,
            websocket: this.state.connected,
            authenticated: this.state.authenticated
        };
    }

    getCurrentUser() {
        return this.state.user;
    }

    getActiveRequests() {
        return Array.from(this.activeRequests.values());
    }

    getCacheStats() {
        return {
            size: this.requestCache.size,
            entries: Array.from(this.requestCache.keys())
        };
    }

    getRateLimitStatus() {
        if (!this.options.enableRateLimit) return null;

        const now = Date.now();
        const cutoff = now - this.options.rateLimit.period;
        const recentRequests = this.rateLimiter.requests.filter(timestamp => timestamp > cutoff);

        return {
            blocked: this.rateLimiter.blocked,
            remaining: Math.max(0, this.options.rateLimit.requests - recentRequests.length),
            resetTime: recentRequests.length > 0 ? Math.min(...recentRequests) + this.options.rateLimit.period : now
        };
    }

    // ==========================================
    // Specialized API Methods
    // ==========================================

    // Chat API
    async sendChatMessage(message, options = {}) {
        return this.post('/chat', {
            message,
            model: options.model || 'claude-3-5-sonnet-20241022',
            persona: options.persona || 'sophia',
            stream: options.stream || false,
            context: options.context || []
        });
    }

    async *streamChatMessage(message, options = {}) {
        yield* this.streamRequest('/chat/stream', {
            message,
            model: options.model || 'claude-3-5-sonnet-20241022',
            persona: options.persona || 'sophia',
            context: options.context || []
        });
    }

    // Widget Data API
    async getWidgetData(widgetType, params = {}) {
        return this.get(`/widgets/${widgetType}`, params);
    }

    // System Status API
    async getSystemStatus() {
        return this.get('/system/status');
    }

    // User Management API
    async updateUserProfile(updates) {
        return this.patch('/user/profile', updates);
    }

    async changePassword(oldPassword, newPassword) {
        return this.post('/user/change-password', {
            old_password: oldPassword,
            new_password: newPassword
        });
    }

    // File Upload API
    async uploadFile(file, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        if (options.metadata) {
            Object.entries(options.metadata).forEach(([key, value]) => {
                formData.append(key, value);
            });
        }

        return this.post('/files/upload', formData, {
            headers: {
                // Don't set Content-Type, let browser set it with boundary
            },
            timeout: options.timeout || 60000 // 1 minute for file uploads
        });
    }

    // Settings API
    async getSettings() {
        return this.get('/settings');
    }

    async updateSettings(settings) {
        return this.patch('/settings', settings);
    }

    // Business Intelligence API
    async getBusinessMetrics(period = '30d') {
        return this.get(`/business/metrics`, { period });
    }

    async getBusinessReport(reportType, params = {}) {
        return this.get(`/business/reports/${reportType}`, params);
    }

    // Agent Swarms API
    async getActiveSwarms() {
        return this.get('/swarms/active');
    }

    async createSwarm(config) {
        return this.post('/swarms', config);
    }

    async controlSwarm(swarmId, action, params = {}) {
        return this.post(`/swarms/${swarmId}/${action}`, params);
    }

    // Persona API
    async getPersonaTeam() {
        return this.get('/api/personas/team');
    }

    async chatWithPersona(personaId, message, context = null) {
        return this.post(`/api/personas/chat/${personaId}`, {
            message,
            context
        });
    }

    async getPersonaHealth() {
        return this.get('/api/personas/health');
    }

    async getPersonaInfo(personaId) {
        return this.get(`/api/personas/${personaId}/info`);
    }

    // Voice API
    getVoiceUrl(filename) {
        return this.buildURL(`/api/voice/${filename}`);
    }

    // Cleanup
    destroy() {
        // Disconnect WebSocket
        this.disconnectWebSocket();
        
        // Clear timers
        if (this.wsReconnectTimer) {
            clearTimeout(this.wsReconnectTimer);
        }
        
        // Clear caches
        this.clearCache();
        
        // Clear active requests
        this.activeRequests.clear();
        
        // Clear event listeners
        this.eventListeners.clear();
        
        // Remove network listeners
        window.removeEventListener('online', this.setupNetworkListeners);
        window.removeEventListener('offline', this.setupNetworkListeners);
    }
}

// Export for module systems or make globally available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
} else {
    window.ApiClient = ApiClient;
}

// Create a default instance for convenience
if (typeof window !== 'undefined') {
    window.apiClient = new ApiClient();
}