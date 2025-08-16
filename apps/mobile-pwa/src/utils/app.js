// SOPHIA Voice Command Center - Mobile PWA JavaScript
// Production-grade voice interface with streaming capabilities

class SOPHIAVoiceApp {
    constructor() {
        this.isRecording = false;
        this.isProcessing = false;
        this.isSpeaking = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.audioContext = null;
        this.analyser = null;
        this.visualizerCanvas = null;
        this.visualizerContext = null;
        this.animationFrame = null;
        this.connectionStatus = 'connected';
        this.settings = {
            sensitivity: 0.5,
            autoSend: true,
            voiceFeedback: true
        };
        
        // API endpoints
        this.apiBase = window.location.origin;
        this.voiceEndpoints = {
            health: `${this.apiBase}/voice/health`,
            command: `${this.apiBase}/voice/command`,
            speak: `${this.apiBase}/voice/speak`,
            transcribe: `${this.apiBase}/voice/transcribe`,
            info: `${this.apiBase}/voice/info`
        };
        
        this.init();
    }
    
    async init() {
        console.log('SOPHIA Voice: Initializing application...');
        
        try {
            // Initialize DOM elements
            this.initializeElements();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Initialize audio context
            await this.initializeAudio();
            
            // Check voice API connection
            await this.checkConnection();
            
            // Initialize visualizer
            this.initializeVisualizer();
            
            // Load settings
            this.loadSettings();
            
            // Hide loading screen
            this.hideLoadingScreen();
            
            // Check for install prompt
            this.setupInstallPrompt();
            
            console.log('SOPHIA Voice: Application initialized successfully');
            
        } catch (error) {
            console.error('SOPHIA Voice: Initialization failed:', error);
            this.showError('Failed to initialize SOPHIA Voice', error.message);
        }
    }
    
    initializeElements() {
        // Main elements
        this.loadingScreen = document.getElementById('loading-screen');
        this.app = document.getElementById('app');
        this.voiceButton = document.getElementById('voice-button');
        this.voiceStatus = document.getElementById('voice-status');
        this.connectionStatusEl = document.getElementById('connection-status');
        this.conversationHistory = document.getElementById('conversation-history');
        this.audioVisualizer = document.getElementById('audio-visualizer');
        this.visualizerCanvas = document.getElementById('visualizer-canvas');
        
        // Settings elements
        this.settingsButton = document.getElementById('settings-button');
        this.settingsPanel = document.getElementById('settings-panel');
        this.closeSettings = document.getElementById('close-settings');
        this.sensitivitySlider = document.getElementById('voice-sensitivity');
        this.autoSendCheckbox = document.getElementById('auto-send');
        this.voiceFeedbackCheckbox = document.getElementById('voice-feedback');
        
        // Action buttons
        this.actionButtons = document.querySelectorAll('.action-button');
        this.clearConversation = document.getElementById('clear-conversation');
        
        // Modal elements
        this.errorModal = document.getElementById('error-modal');
        this.errorMessage = document.getElementById('error-message');
        this.closeError = document.getElementById('close-error');
        this.retryConnection = document.getElementById('retry-connection');
        this.useTextMode = document.getElementById('use-text-mode');
        
        // Install prompt
        this.installPrompt = document.getElementById('install-prompt');
        this.installApp = document.getElementById('install-app');
        this.dismissInstall = document.getElementById('dismiss-install');
        
        // Get visualizer context
        if (this.visualizerCanvas) {
            this.visualizerContext = this.visualizerCanvas.getContext('2d');
        }
    }
    
    setupEventListeners() {
        // Voice button events
        this.voiceButton.addEventListener('touchstart', this.startRecording.bind(this), { passive: false });
        this.voiceButton.addEventListener('touchend', this.stopRecording.bind(this), { passive: false });
        this.voiceButton.addEventListener('mousedown', this.startRecording.bind(this));
        this.voiceButton.addEventListener('mouseup', this.stopRecording.bind(this));
        
        // Prevent context menu on long press
        this.voiceButton.addEventListener('contextmenu', (e) => e.preventDefault());
        
        // Settings
        this.settingsButton.addEventListener('click', this.openSettings.bind(this));
        this.closeSettings.addEventListener('click', this.closeSettingsPanel.bind(this));
        this.sensitivitySlider.addEventListener('input', this.updateSensitivity.bind(this));
        this.autoSendCheckbox.addEventListener('change', this.updateAutoSend.bind(this));
        this.voiceFeedbackCheckbox.addEventListener('change', this.updateVoiceFeedback.bind(this));
        
        // Action buttons
        this.actionButtons.forEach(button => {
            button.addEventListener('click', this.handleQuickAction.bind(this));
        });
        
        // Clear conversation
        this.clearConversation.addEventListener('click', this.clearConversationHistory.bind(this));
        
        // Error modal
        this.closeError.addEventListener('click', this.hideError.bind(this));
        this.retryConnection.addEventListener('click', this.retryConnection.bind(this));
        this.useTextMode.addEventListener('click', this.enableTextMode.bind(this));
        
        // Install prompt
        if (this.installApp) {
            this.installApp.addEventListener('click', this.installApplication.bind(this));
        }
        if (this.dismissInstall) {
            this.dismissInstall.addEventListener('click', this.dismissInstallPrompt.bind(this));
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboard.bind(this));
        
        // Visibility change
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
        
        // Online/offline events
        window.addEventListener('online', this.handleOnline.bind(this));
        window.addEventListener('offline', this.handleOffline.bind(this));
    }
    
    async initializeAudio() {
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100
                } 
            });
            
            // Initialize audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create analyser for visualization
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            
            // Connect microphone to analyser
            const source = this.audioContext.createMediaStreamSource(stream);
            source.connect(this.analyser);
            
            // Store stream for later use
            this.microphoneStream = stream;
            
            console.log('SOPHIA Voice: Audio initialized successfully');
            
        } catch (error) {
            console.error('SOPHIA Voice: Audio initialization failed:', error);
            throw new Error('Microphone access required for voice commands');
        }
    }
    
    async checkConnection() {
        try {
            const response = await fetch(this.voiceEndpoints.health, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('SOPHIA Voice: Connected to voice API:', data);
                this.updateConnectionStatus('connected');
                return true;
            } else {
                throw new Error(`API responded with status ${response.status}`);
            }
            
        } catch (error) {
            console.error('SOPHIA Voice: Connection check failed:', error);
            this.updateConnectionStatus('disconnected');
            return false;
        }
    }
    
    initializeVisualizer() {
        if (!this.visualizerCanvas || !this.visualizerContext) return;
        
        const canvas = this.visualizerCanvas;
        const ctx = this.visualizerContext;
        
        // Set canvas size
        canvas.width = 300;
        canvas.height = 100;
        
        // Initial draw
        this.drawVisualizer();
    }
    
    drawVisualizer() {
        if (!this.analyser || !this.visualizerContext) return;
        
        const canvas = this.visualizerCanvas;
        const ctx = this.visualizerContext;
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        this.analyser.getByteFrequencyData(dataArray);
        
        // Clear canvas
        ctx.fillStyle = 'rgba(10, 10, 10, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw frequency bars
        const barWidth = (canvas.width / bufferLength) * 2.5;
        let barHeight;
        let x = 0;
        
        for (let i = 0; i < bufferLength; i++) {
            barHeight = (dataArray[i] / 255) * canvas.height * 0.8;
            
            // Create gradient
            const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
            gradient.addColorStop(0, '#6366f1');
            gradient.addColorStop(1, '#818cf8');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            
            x += barWidth + 1;
        }
        
        // Continue animation if recording
        if (this.isRecording) {
            this.animationFrame = requestAnimationFrame(this.drawVisualizer.bind(this));
        }
    }
    
    async startRecording(event) {
        if (this.isRecording || this.isProcessing) return;
        
        event.preventDefault();
        
        try {
            console.log('SOPHIA Voice: Starting recording...');
            
            this.isRecording = true;
            this.audioChunks = [];
            
            // Update UI
            this.voiceButton.classList.add('recording');
            this.updateVoiceStatus('Listening...', 'Speak your command');
            this.audioVisualizer.classList.add('active');
            
            // Start visualizer
            this.drawVisualizer();
            
            // Create media recorder
            this.mediaRecorder = new MediaRecorder(this.microphoneStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            // Start recording
            this.mediaRecorder.start();
            
            // Haptic feedback
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
            
        } catch (error) {
            console.error('SOPHIA Voice: Failed to start recording:', error);
            this.showError('Recording failed', error.message);
            this.resetRecordingState();
        }
    }
    
    stopRecording(event) {
        if (!this.isRecording) return;
        
        event.preventDefault();
        
        console.log('SOPHIA Voice: Stopping recording...');
        
        this.isRecording = false;
        
        // Update UI
        this.voiceButton.classList.remove('recording');
        this.voiceButton.classList.add('processing');
        this.updateVoiceStatus('Processing...', 'Analyzing your command');
        this.audioVisualizer.classList.remove('active');
        
        // Stop visualizer animation
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        
        // Stop media recorder
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        
        // Haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate([50, 50, 50]);
        }
    }
    
    async processRecording() {
        if (this.audioChunks.length === 0) {
            this.resetRecordingState();
            return;
        }
        
        try {
            this.isProcessing = true;
            
            // Create audio blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            
            // Create form data
            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice-command.webm');
            
            console.log('SOPHIA Voice: Sending voice command...');
            
            // Send to voice API
            const response = await fetch(this.voiceEndpoints.command, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Voice API responded with status ${response.status}`);
            }
            
            // Handle streaming response
            await this.handleStreamingResponse(response);
            
        } catch (error) {
            console.error('SOPHIA Voice: Processing failed:', error);
            this.showError('Command processing failed', error.message);
        } finally {
            this.resetRecordingState();
        }
    }
    
    async handleStreamingResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let transcription = '';
        let responseText = '';
        
        try {
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.type === 'audio') {
                                // Play audio chunk
                                await this.playAudioChunk(data.data);
                            } else if (data.type === 'complete') {
                                transcription = data.transcription;
                                responseText = data.response_text;
                                
                                // Add to conversation
                                this.addToConversation('user', transcription);
                                this.addToConversation('assistant', responseText);
                            } else if (data.type === 'error') {
                                throw new Error(data.error);
                            }
                            
                        } catch (parseError) {
                            console.warn('SOPHIA Voice: Failed to parse streaming data:', parseError);
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('SOPHIA Voice: Streaming response failed:', error);
            throw error;
        }
    }
    
    async playAudioChunk(base64Data) {
        if (!this.settings.voiceFeedback) return;
        
        try {
            // Decode base64 audio
            const audioData = atob(base64Data);
            const audioArray = new Uint8Array(audioData.length);
            
            for (let i = 0; i < audioData.length; i++) {
                audioArray[i] = audioData.charCodeAt(i);
            }
            
            // Create audio buffer
            const audioBuffer = await this.audioContext.decodeAudioData(audioArray.buffer);
            
            // Play audio
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start();
            
            // Update UI for speaking
            if (!this.isSpeaking) {
                this.isSpeaking = true;
                this.voiceButton.classList.add('speaking');
                this.updateVoiceStatus('SOPHIA is speaking...', '');
                
                source.onended = () => {
                    this.isSpeaking = false;
                    this.voiceButton.classList.remove('speaking');
                    this.updateVoiceStatus('Tap and hold to speak', 'Release to send command');
                };
            }
            
        } catch (error) {
            console.error('SOPHIA Voice: Audio playback failed:', error);
        }
    }
    
    addToConversation(type, message) {
        const conversationItem = document.createElement('div');
        conversationItem.className = `conversation-item ${type}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = type === 'user' ? '👤' : '🤖';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const text = document.createElement('div');
        text.className = 'message-text';
        text.textContent = message;
        
        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        content.appendChild(text);
        content.appendChild(time);
        conversationItem.appendChild(avatar);
        conversationItem.appendChild(content);
        
        this.conversationHistory.appendChild(conversationItem);
        
        // Scroll to bottom
        this.conversationHistory.scrollTop = this.conversationHistory.scrollHeight;
    }
    
    resetRecordingState() {
        this.isRecording = false;
        this.isProcessing = false;
        this.audioChunks = [];
        
        // Reset UI
        this.voiceButton.classList.remove('recording', 'processing', 'speaking');
        this.updateVoiceStatus('Tap and hold to speak', 'Release to send command');
        this.audioVisualizer.classList.remove('active');
        
        // Stop visualizer
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
    }
    
    updateVoiceStatus(primary, secondary) {
        const statusText = this.voiceStatus.querySelector('.status-text');
        const statusSubtext = this.voiceStatus.querySelector('.status-subtext');
        
        if (statusText) statusText.textContent = primary;
        if (statusSubtext) statusSubtext.textContent = secondary;
    }
    
    updateConnectionStatus(status) {
        this.connectionStatus = status;
        const indicator = this.connectionStatusEl.querySelector('.status-indicator');
        const text = this.connectionStatusEl.querySelector('.status-text');
        
        indicator.className = `status-indicator ${status}`;
        
        switch (status) {
            case 'connected':
                text.textContent = 'Connected';
                break;
            case 'connecting':
                text.textContent = 'Connecting...';
                break;
            case 'disconnected':
                text.textContent = 'Disconnected';
                break;
        }
    }
    
    async handleQuickAction(event) {
        const command = event.currentTarget.dataset.command;
        if (!command) return;
        
        try {
            // Add user message
            this.addToConversation('user', command);
            
            // Send text command
            const response = await fetch(this.voiceEndpoints.speak, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: command, context: 'quick_action' })
            });
            
            if (response.ok) {
                // Handle response (simplified for quick actions)
                this.addToConversation('assistant', 'Processing your request...');
            }
            
        } catch (error) {
            console.error('SOPHIA Voice: Quick action failed:', error);
            this.addToConversation('assistant', 'Sorry, I encountered an error processing that request.');
        }
    }
    
    clearConversationHistory() {
        // Keep only the system message
        const systemMessage = this.conversationHistory.querySelector('.system-message');
        this.conversationHistory.innerHTML = '';
        if (systemMessage) {
            this.conversationHistory.appendChild(systemMessage);
        }
    }
    
    openSettings() {
        this.settingsPanel.classList.add('open');
    }
    
    closeSettingsPanel() {
        this.settingsPanel.classList.remove('open');
    }
    
    updateSensitivity(event) {
        this.settings.sensitivity = parseFloat(event.target.value);
        this.saveSettings();
    }
    
    updateAutoSend(event) {
        this.settings.autoSend = event.target.checked;
        this.saveSettings();
    }
    
    updateVoiceFeedback(event) {
        this.settings.voiceFeedback = event.target.checked;
        this.saveSettings();
    }
    
    loadSettings() {
        try {
            const saved = localStorage.getItem('sophia-voice-settings');
            if (saved) {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
            }
            
            // Apply settings to UI
            this.sensitivitySlider.value = this.settings.sensitivity;
            this.autoSendCheckbox.checked = this.settings.autoSend;
            this.voiceFeedbackCheckbox.checked = this.settings.voiceFeedback;
            
        } catch (error) {
            console.warn('SOPHIA Voice: Failed to load settings:', error);
        }
    }
    
    saveSettings() {
        try {
            localStorage.setItem('sophia-voice-settings', JSON.stringify(this.settings));
        } catch (error) {
            console.warn('SOPHIA Voice: Failed to save settings:', error);
        }
    }
    
    showError(title, message) {
        this.errorMessage.textContent = message;
        this.errorModal.style.display = 'flex';
    }
    
    hideError() {
        this.errorModal.style.display = 'none';
    }
    
    async retryConnection() {
        this.hideError();
        this.updateConnectionStatus('connecting');
        
        const connected = await this.checkConnection();
        if (!connected) {
            this.showError('Connection failed', 'Unable to connect to SOPHIA voice services. Please check your internet connection.');
        }
    }
    
    enableTextMode() {
        this.hideError();
        // Implement text mode fallback
        console.log('SOPHIA Voice: Switching to text mode');
    }
    
    hideLoadingScreen() {
        this.loadingScreen.style.display = 'none';
        this.app.style.display = 'flex';
    }
    
    setupInstallPrompt() {
        let deferredPrompt;
        
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            this.installPrompt.style.display = 'block';
        });
        
        this.installApplication = async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                console.log('SOPHIA Voice: Install prompt outcome:', outcome);
                deferredPrompt = null;
                this.installPrompt.style.display = 'none';
            }
        };
        
        this.dismissInstallPrompt = () => {
            this.installPrompt.style.display = 'none';
        };
    }
    
    handleKeyboard(event) {
        // Space bar for voice command
        if (event.code === 'Space' && !event.repeat) {
            event.preventDefault();
            if (event.type === 'keydown') {
                this.startRecording(event);
            } else if (event.type === 'keyup') {
                this.stopRecording(event);
            }
        }
        
        // Escape to close modals
        if (event.code === 'Escape') {
            this.closeSettingsPanel();
            this.hideError();
        }
    }
    
    handleVisibilityChange() {
        if (document.hidden && this.isRecording) {
            this.stopRecording(new Event('visibilitychange'));
        }
    }
    
    handleOnline() {
        console.log('SOPHIA Voice: Back online');
        this.checkConnection();
    }
    
    handleOffline() {
        console.log('SOPHIA Voice: Gone offline');
        this.updateConnectionStatus('disconnected');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.sophiaVoiceApp = new SOPHIAVoiceApp();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.sophiaVoiceApp && window.sophiaVoiceApp.isRecording) {
        window.sophiaVoiceApp.stopRecording(new Event('beforeunload'));
    }
});

