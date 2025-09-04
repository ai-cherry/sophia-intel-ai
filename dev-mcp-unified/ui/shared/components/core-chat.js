/**
 * Core Chat Component Library
 * Universal chat component with WebSocket support, voice integration, and persona switching
 * Designed for both Sophia and Artemis UIs
 */

class CoreChatComponent {
    constructor(options = {}) {
        this.options = {
            containerId: 'chat-container',
            apiBaseUrl: options.apiBaseUrl || 'http://127.0.0.1:3333',
            wsUrl: options.wsUrl || 'ws://127.0.0.1:3333/ws',
            theme: options.theme || 'dark',
            enableVoice: options.enableVoice !== false,
            enablePersonas: options.enablePersonas !== false,
            maxHistory: options.maxHistory || 100,
            autoConnect: options.autoConnect !== false,
            ...options
        };

        this.state = {
            connected: false,
            currentModel: 'claude-3-5-sonnet-20241022',
            currentPersona: 'sophia',
            messages: [],
            isLoading: false,
            voiceEnabled: false,
            isRecording: false,
            isPlaying: false,
            streamingMessage: null
        };

        this.ws = null;
        this.messageQueue = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;

        // Voice synthesis setup
        this.speechSynthesis = window.speechSynthesis;
        this.currentUtterance = null;

        // Voice recording setup
        this.mediaRecorder = null;
        this.audioChunks = [];

        // Event callbacks
        this.onMessageReceived = options.onMessageReceived || (() => {});
        this.onConnectionStatusChanged = options.onConnectionStatusChanged || (() => {});
        this.onPersonaChanged = options.onPersonaChanged || (() => {});
        this.onError = options.onError || (() => {});

        this.init();
    }

    async init() {
        this.createChatUI();
        this.loadMessageHistory();
        if (this.options.autoConnect) {
            await this.connectWebSocket();
        }
        this.setupVoiceRecognition();
        this.bindEvents();
    }

    createChatUI() {
        const container = document.getElementById(this.options.containerId);
        if (!container) {
            console.error(`Container with id '${this.options.containerId}' not found`);
            return;
        }

        container.innerHTML = `
            <div class="core-chat-component" data-theme="${this.options.theme}">
                <!-- Chat Header -->
                <div class="chat-header">
                    <div class="chat-title">
                        <div class="persona-indicator" data-persona="${this.state.currentPersona}">
                            <div class="persona-avatar"></div>
                            <span class="persona-name">${this.getPersonaDisplayName()}</span>
                        </div>
                        <div class="connection-status ${this.state.connected ? 'connected' : 'disconnected'}">
                            <div class="status-indicator"></div>
                            <span class="status-text">${this.state.connected ? 'Connected' : 'Disconnected'}</span>
                        </div>
                    </div>
                    
                    <div class="chat-controls">
                        ${this.options.enablePersonas ? `
                            <select class="persona-selector" id="persona-selector">
                                <option value="sophia">Sophia (Intelligence Hub)</option>
                                <option value="artemis">Artemis (Research Lab)</option>
                                <option value="atlas">Atlas (Business Intelligence)</option>
                                <option value="hermes">Hermes (Communication)</option>
                                <option value="minerva">Minerva (Knowledge)</option>
                            </select>
                        ` : ''}
                        
                        <select class="model-selector" id="model-selector">
                            <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                            <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku</option>
                            <option value="gpt-4-turbo">GPT-4 Turbo</option>
                            <option value="gpt-4o">GPT-4o</option>
                            <option value="gemini-pro">Gemini Pro</option>
                        </select>
                        
                        ${this.options.enableVoice ? `
                            <button class="voice-toggle" id="voice-toggle" title="Toggle Voice">
                                <svg class="voice-icon" viewBox="0 0 24 24">
                                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                                </svg>
                            </button>
                            
                            <button class="voice-record" id="voice-record" title="Voice Input">
                                <svg class="record-icon" viewBox="0 0 24 24">
                                    <circle cx="12" cy="12" r="3"/>
                                    <path d="M12 1v6m0 10v6m11-7h-6m-10 0H1"/>
                                </svg>
                            </button>
                        ` : ''}
                        
                        <button class="settings-toggle" id="settings-toggle" title="Settings">
                            <svg class="settings-icon" viewBox="0 0 24 24">
                                <circle cx="12" cy="12" r="3"/>
                                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Chat Messages -->
                <div class="chat-messages" id="chat-messages">
                    <div class="welcome-message">
                        <div class="welcome-content">
                            <h3>Welcome to ${this.getPersonaDisplayName()}</h3>
                            <p>How can I assist you today?</p>
                        </div>
                    </div>
                </div>

                <!-- Chat Input -->
                <div class="chat-input-container">
                    <div class="input-wrapper">
                        <textarea 
                            class="chat-input" 
                            id="chat-input" 
                            placeholder="Type your message... (Shift+Enter for new line)"
                            rows="1"
                        ></textarea>
                        
                        <div class="input-actions">
                            <button class="attachment-btn" id="attachment-btn" title="Attach File">
                                <svg viewBox="0 0 24 24">
                                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                                </svg>
                            </button>
                            
                            <button class="send-btn" id="send-btn" title="Send Message" disabled>
                                <svg class="send-icon" viewBox="0 0 24 24">
                                    <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
                                </svg>
                                <div class="loading-spinner" style="display: none;">
                                    <div class="spinner"></div>
                                </div>
                            </button>
                        </div>
                    </div>
                    
                    <div class="input-status">
                        <span class="typing-indicator" style="display: none;">AI is typing...</span>
                        <span class="connection-info">Connected to ${this.state.currentModel}</span>
                    </div>
                </div>

                <!-- Voice Recording Overlay -->
                <div class="voice-recording-overlay" id="voice-recording-overlay" style="display: none;">
                    <div class="recording-content">
                        <div class="recording-animation">
                            <div class="pulse-ring"></div>
                            <div class="pulse-ring"></div>
                            <div class="pulse-ring"></div>
                            <svg class="mic-icon" viewBox="0 0 24 24">
                                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                            </svg>
                        </div>
                        <p>Listening... Speak now</p>
                        <button class="stop-recording" id="stop-recording">Stop Recording</button>
                    </div>
                </div>
            </div>
        `;

        // Set initial values for selectors
        const personaSelector = document.getElementById('persona-selector');
        const modelSelector = document.getElementById('model-selector');
        
        if (personaSelector) {
            personaSelector.value = this.state.currentPersona;
        }
        
        if (modelSelector) {
            modelSelector.value = this.state.currentModel;
        }
    }

    bindEvents() {
        const sendBtn = document.getElementById('send-btn');
        const chatInput = document.getElementById('chat-input');
        const personaSelector = document.getElementById('persona-selector');
        const modelSelector = document.getElementById('model-selector');
        const voiceToggle = document.getElementById('voice-toggle');
        const voiceRecord = document.getElementById('voice-record');
        const stopRecording = document.getElementById('stop-recording');

        // Send message events
        sendBtn?.addEventListener('click', () => this.sendMessage());
        chatInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        chatInput?.addEventListener('input', (e) => {
            const textarea = e.target;
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
            
            // Update send button state
            sendBtn.disabled = !textarea.value.trim();
        });

        // Persona and model changes
        personaSelector?.addEventListener('change', (e) => {
            this.changePersona(e.target.value);
        });

        modelSelector?.addEventListener('change', (e) => {
            this.changeModel(e.target.value);
        });

        // Voice controls
        voiceToggle?.addEventListener('click', () => {
            this.toggleVoiceOutput();
        });

        voiceRecord?.addEventListener('click', () => {
            this.startVoiceInput();
        });

        stopRecording?.addEventListener('click', () => {
            this.stopVoiceInput();
        });

        // File attachment
        const attachmentBtn = document.getElementById('attachment-btn');
        attachmentBtn?.addEventListener('click', () => {
            this.handleFileAttachment();
        });
    }

    async connectWebSocket() {
        try {
            this.ws = new WebSocket(this.options.wsUrl);
            
            this.ws.onopen = () => {
                this.state.connected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus();
                this.onConnectionStatusChanged(true);
                
                // Send any queued messages
                this.messageQueue.forEach(message => {
                    this.ws.send(JSON.stringify(message));
                });
                this.messageQueue = [];
            };

            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };

            this.ws.onclose = () => {
                this.state.connected = false;
                this.updateConnectionStatus();
                this.onConnectionStatusChanged(false);
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.onError(error);
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.onError(error);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'message_chunk':
                this.handleStreamingChunk(data);
                break;
            case 'message_complete':
                this.handleMessageComplete(data);
                break;
            case 'error':
                this.handleError(data.error);
                break;
            case 'status':
                this.handleStatusUpdate(data);
                break;
        }
    }

    handleStreamingChunk(data) {
        if (!this.state.streamingMessage) {
            // Start new streaming message
            this.state.streamingMessage = {
                id: data.message_id,
                content: data.chunk,
                role: 'assistant',
                timestamp: new Date().toISOString(),
                model: this.state.currentModel,
                persona: this.state.currentPersona,
                streaming: true
            };
            this.addMessageToUI(this.state.streamingMessage);
        } else {
            // Update existing streaming message
            this.state.streamingMessage.content += data.chunk;
            this.updateStreamingMessage(this.state.streamingMessage);
        }
    }

    handleMessageComplete(data) {
        if (this.state.streamingMessage) {
            this.state.streamingMessage.streaming = false;
            this.state.streamingMessage.complete = true;
            this.finalizeMessage(this.state.streamingMessage);
            
            // Add to message history
            this.state.messages.push(this.state.streamingMessage);
            this.saveMessageHistory();
            
            // Voice synthesis if enabled
            if (this.state.voiceEnabled && this.options.enableVoice) {
                this.speakMessage(this.state.streamingMessage.content);
            }
            
            this.state.streamingMessage = null;
        }
        
        this.state.isLoading = false;
        this.updateLoadingState();
        this.onMessageReceived(data);
    }

    async sendMessage() {
        const chatInput = document.getElementById('chat-input');
        const message = chatInput.value.trim();
        
        if (!message || this.state.isLoading) return;
        
        // Clear input
        chatInput.value = '';
        chatInput.style.height = 'auto';
        document.getElementById('send-btn').disabled = true;
        
        // Create user message
        const userMessage = {
            id: this.generateMessageId(),
            content: message,
            role: 'user',
            timestamp: new Date().toISOString()
        };
        
        // Add to UI and state
        this.addMessageToUI(userMessage);
        this.state.messages.push(userMessage);
        this.saveMessageHistory();
        
        // Set loading state
        this.state.isLoading = true;
        this.updateLoadingState();
        
        // Send via WebSocket or HTTP
        const payload = {
            type: 'chat_message',
            message: message,
            model: this.state.currentModel,
            persona: this.state.currentPersona,
            stream: true,
            context: this.getRecentContext()
        };
        
        if (this.state.connected && this.ws) {
            this.ws.send(JSON.stringify(payload));
        } else {
            // Fallback to HTTP if WebSocket not available
            this.messageQueue.push(payload);
            await this.sendMessageHTTP(payload);
        }
    }

    async sendMessageHTTP(payload) {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Handle streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this.handleWebSocketMessage(data);
                        } catch (e) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Failed to send message via HTTP:', error);
            this.handleError(error.message);
        }
    }

    addMessageToUI(message) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageElement = this.createMessageElement(message);
        
        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        messageDiv.dataset.messageId = message.id;
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <div class="message-meta">
                    <span class="message-role">${message.role === 'user' ? 'You' : this.getPersonaDisplayName()}</span>
                    ${message.model ? `<span class="message-model">${message.model}</span>` : ''}
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-actions">
                    <button class="copy-btn" title="Copy message">
                        <svg viewBox="0 0 24 24">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                        </svg>
                    </button>
                    ${message.role === 'assistant' ? `
                        <button class="speak-btn" title="Speak message">
                            <svg viewBox="0 0 24 24">
                                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                                <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                            </svg>
                        </button>
                    ` : ''}
                </div>
            </div>
            <div class="message-content">
                ${message.streaming ? `
                    <div class="streaming-content">${this.formatMessageContent(message.content)}</div>
                    <div class="typing-cursor"></div>
                ` : this.formatMessageContent(message.content)}
            </div>
        `;
        
        // Bind action events
        this.bindMessageActions(messageDiv, message);
        
        return messageDiv;
    }

    bindMessageActions(messageElement, message) {
        const copyBtn = messageElement.querySelector('.copy-btn');
        const speakBtn = messageElement.querySelector('.speak-btn');
        
        copyBtn?.addEventListener('click', () => {
            this.copyMessageToClipboard(message.content);
        });
        
        speakBtn?.addEventListener('click', () => {
            this.speakMessage(message.content);
        });
    }

    formatMessageContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/\n/g, '<br>');
    }

    updateStreamingMessage(message) {
        const messageElement = document.querySelector(`[data-message-id="${message.id}"]`);
        if (messageElement) {
            const contentElement = messageElement.querySelector('.streaming-content');
            if (contentElement) {
                contentElement.innerHTML = this.formatMessageContent(message.content);
            }
        }
    }

    finalizeMessage(message) {
        const messageElement = document.querySelector(`[data-message-id="${message.id}"]`);
        if (messageElement) {
            const contentDiv = messageElement.querySelector('.message-content');
            contentDiv.innerHTML = this.formatMessageContent(message.content);
            messageElement.classList.add('complete');
        }
    }

    changePersona(persona) {
        if (this.state.currentPersona === persona) return;
        
        this.state.currentPersona = persona;
        this.updatePersonaIndicator();
        this.onPersonaChanged(persona);
        
        // Save preference
        localStorage.setItem('sophia_current_persona', persona);
    }

    changeModel(model) {
        if (this.state.currentModel === model) return;
        
        this.state.currentModel = model;
        this.updateConnectionInfo();
        
        // Save preference
        localStorage.setItem('sophia_current_model', model);
    }

    getPersonaDisplayName() {
        const personas = {
            sophia: 'Sophia',
            artemis: 'Artemis',
            atlas: 'Atlas',
            hermes: 'Hermes',
            minerva: 'Minerva'
        };
        return personas[this.state.currentPersona] || 'Assistant';
    }

    updatePersonaIndicator() {
        const indicator = document.querySelector('.persona-indicator');
        if (indicator) {
            indicator.dataset.persona = this.state.currentPersona;
            indicator.querySelector('.persona-name').textContent = this.getPersonaDisplayName();
        }
    }

    updateConnectionStatus() {
        const statusElement = document.querySelector('.connection-status');
        if (statusElement) {
            statusElement.className = `connection-status ${this.state.connected ? 'connected' : 'disconnected'}`;
            statusElement.querySelector('.status-text').textContent = 
                this.state.connected ? 'Connected' : 'Disconnected';
        }
    }

    updateConnectionInfo() {
        const infoElement = document.querySelector('.connection-info');
        if (infoElement) {
            infoElement.textContent = `Connected to ${this.state.currentModel}`;
        }
    }

    updateLoadingState() {
        const sendBtn = document.getElementById('send-btn');
        const typingIndicator = document.querySelector('.typing-indicator');
        const spinner = document.querySelector('.loading-spinner');
        const sendIcon = document.querySelector('.send-icon');
        
        if (this.state.isLoading) {
            sendBtn.disabled = true;
            typingIndicator.style.display = 'inline';
            spinner.style.display = 'inline-block';
            sendIcon.style.display = 'none';
        } else {
            const chatInput = document.getElementById('chat-input');
            sendBtn.disabled = !chatInput?.value.trim();
            typingIndicator.style.display = 'none';
            spinner.style.display = 'none';
            sendIcon.style.display = 'inline-block';
        }
    }

    // Voice functionality
    async setupVoiceRecognition() {
        if (!this.options.enableVoice || !('webkitSpeechRecognition' in window)) {
            return;
        }
        
        this.recognition = new webkitSpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        
        this.recognition.onresult = (event) => {
            const result = event.results[event.results.length - 1];
            if (result.isFinal) {
                const chatInput = document.getElementById('chat-input');
                chatInput.value = result[0].transcript;
                chatInput.dispatchEvent(new Event('input'));
                this.stopVoiceInput();
            }
        };
        
        this.recognition.onerror = (error) => {
            console.error('Speech recognition error:', error);
            this.stopVoiceInput();
        };
    }

    startVoiceInput() {
        if (!this.recognition) return;
        
        this.state.isRecording = true;
        document.getElementById('voice-recording-overlay').style.display = 'flex';
        this.recognition.start();
    }

    stopVoiceInput() {
        if (!this.recognition) return;
        
        this.state.isRecording = false;
        document.getElementById('voice-recording-overlay').style.display = 'none';
        this.recognition.stop();
    }

    toggleVoiceOutput() {
        this.state.voiceEnabled = !this.state.voiceEnabled;
        const voiceToggle = document.getElementById('voice-toggle');
        if (voiceToggle) {
            voiceToggle.classList.toggle('active', this.state.voiceEnabled);
        }
        
        // Save preference
        localStorage.setItem('sophia_voice_enabled', this.state.voiceEnabled.toString());
    }

    speakMessage(text) {
        if (!this.state.voiceEnabled || !this.speechSynthesis) return;
        
        // Stop current utterance
        this.speechSynthesis.cancel();
        
        // Create new utterance
        this.currentUtterance = new SpeechSynthesisUtterance(text);
        this.currentUtterance.rate = 0.9;
        this.currentUtterance.pitch = 1;
        this.currentUtterance.volume = 0.8;
        
        this.currentUtterance.onstart = () => {
            this.state.isPlaying = true;
        };
        
        this.currentUtterance.onend = () => {
            this.state.isPlaying = false;
        };
        
        this.speechSynthesis.speak(this.currentUtterance);
    }

    // Utility methods
    generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    getRecentContext(limit = 5) {
        return this.state.messages.slice(-limit).map(msg => ({
            role: msg.role,
            content: msg.content
        }));
    }

    async copyMessageToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            // Show brief success feedback
            this.showToast('Message copied to clipboard');
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
        }
    }

    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    saveMessageHistory() {
        try {
            const history = this.state.messages.slice(-this.options.maxHistory);
            localStorage.setItem('sophia_chat_history', JSON.stringify(history));
        } catch (error) {
            console.error('Failed to save message history:', error);
        }
    }

    loadMessageHistory() {
        try {
            const savedHistory = localStorage.getItem('sophia_chat_history');
            if (savedHistory) {
                this.state.messages = JSON.parse(savedHistory);
                this.state.messages.forEach(message => {
                    this.addMessageToUI(message);
                });
            }
            
            // Load preferences
            const savedPersona = localStorage.getItem('sophia_current_persona');
            if (savedPersona) {
                this.state.currentPersona = savedPersona;
            }
            
            const savedModel = localStorage.getItem('sophia_current_model');
            if (savedModel) {
                this.state.currentModel = savedModel;
            }
            
            const savedVoiceEnabled = localStorage.getItem('sophia_voice_enabled');
            if (savedVoiceEnabled) {
                this.state.voiceEnabled = savedVoiceEnabled === 'true';
            }
        } catch (error) {
            console.error('Failed to load message history:', error);
        }
    }

    handleFileAttachment() {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.accept = '.txt,.pdf,.doc,.docx,.md,.json,.csv,.png,.jpg,.jpeg,.gif';
        
        input.onchange = async (event) => {
            const files = Array.from(event.target.files);
            for (const file of files) {
                await this.processFile(file);
            }
        };
        
        input.click();
    }

    async processFile(file) {
        // File processing logic would go here
        // This is a placeholder for file upload and processing
        console.log('Processing file:', file.name);
        this.showToast(`File "${file.name}" uploaded successfully`);
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.warn('Max reconnection attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        setTimeout(() => {
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            this.connectWebSocket();
        }, delay);
    }

    handleError(error) {
        console.error('Chat error:', error);
        this.state.isLoading = false;
        this.updateLoadingState();
        this.showToast(`Error: ${error}`, 'error');
        this.onError(error);
    }

    handleStatusUpdate(data) {
        // Handle various status updates from the server
        console.log('Status update:', data);
    }

    // Public API methods
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.state.connected = false;
        this.updateConnectionStatus();
    }

    reconnect() {
        this.disconnect();
        return this.connectWebSocket();
    }

    clearHistory() {
        this.state.messages = [];
        localStorage.removeItem('sophia_chat_history');
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-content">
                    <h3>Welcome to ${this.getPersonaDisplayName()}</h3>
                    <p>How can I assist you today?</p>
                </div>
            </div>
        `;
    }

    destroy() {
        this.disconnect();
        if (this.recognition) {
            this.recognition.abort();
        }
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }
    }
}

// Export for module systems or make globally available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CoreChatComponent;
} else {
    window.CoreChatComponent = CoreChatComponent;
}