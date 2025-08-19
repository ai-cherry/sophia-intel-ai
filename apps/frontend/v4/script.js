class SophiaV4Interface {
    constructor() {
        this.apiBase = window.location.origin;
        this.userId = 'patrick_001';
        this.isProcessing = false;
        this.init();
    }

    init() {
        this.chatInput = document.querySelector('.chat-input');
        this.sendButton = document.querySelector('.send-button');
        this.chatArea = document.querySelector('.chat-area');

        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }

        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Load initial greeting
        this.loadInitialGreeting();
    }

    async loadInitialGreeting() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/persona`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: "Introduce yourself",
                    user_id: this.userId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            this.addMessage(result.response || "🤠 Howdy! SOPHIA V4 is locked and loaded with real autonomous capabilities. I can research, coordinate swarms, commit code, and deploy apps. What's the mission, partner?", 'sophia');

        } catch (error) {
            console.error('Initial greeting error:', error);
            this.addMessage("🤠 Howdy! SOPHIA V4 is locked and loaded with real autonomous capabilities. I can research, coordinate swarms, commit code, and deploy apps. What's the mission, partner?", 'sophia');
        }
    }

    async sendMessage() {
        const message = this.chatInput?.value?.trim();
        if (!message) return;

        this.isProcessing = true;
        if (this.chatInput) this.chatInput.value = '';
        this.updateSendButton(true);

        // Add user message
        this.addMessage(message, 'user');

        try {
            // Use chat endpoint for real autonomous capabilities (web search, etc.)
            const result = await this.chatWithSophia(message);
            this.displayChatResult(result);

        } catch (error) {
            console.error('Message processing error:', error);
            this.addMessage(`Error: ${error.message}`, 'error');
        } finally {
            this.isProcessing = false;
            this.updateSendButton(false);
        }
    }

    async chatWithSophia(query) {
        const response = await fetch(`${this.apiBase}/api/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                user_id: this.userId,
                sources_limit: 3
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    }

    displayChatResult(result) {
        // Display SOPHIA's response with web search results
        let message = result.message || result.response || "I'm processing your request...";
        
        // Add sources if available
        if (result.results && result.results.length > 0) {
            message += "\n\n📚 Sources:";
            result.results.forEach((source, index) => {
                message += `\n${index + 1}. ${source.title || source.url}`;
                if (source.snippet) {
                    message += ` - ${source.snippet.substring(0, 100)}...`;
                }
            });
        }

        this.addMessage(message, 'sophia');
    }

    addMessage(content, type) {
        if (!this.chatArea) return;

        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            margin-bottom: 12px;
            padding: 12px;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
            white-space: pre-wrap;
        `;

        const timestamp = new Date().toLocaleTimeString();

        if (type === 'user') {
            messageDiv.style.cssText += `
                background: #4758F1;
                color: white;
                margin-left: auto;
                text-align: right;
            `;
            messageDiv.innerHTML = `${content}<br><small style="opacity: 0.8;">${timestamp}</small>`;
        } else if (type === 'sophia') {
            messageDiv.style.cssText += `
                background: rgba(134, 208, 190, 0.1);
                border: 1px solid rgba(134, 208, 190, 0.3);
                color: #e2e8f0;
            `;
            messageDiv.innerHTML = `${content}<br><small style="opacity: 0.8; color: #86D0BE;">${timestamp}</small>`;
        } else if (type === 'error') {
            messageDiv.style.cssText += `
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: #fca5a5;
            `;
            messageDiv.innerHTML = `${content}<br><small style="opacity: 0.8;">${timestamp}</small>`;
        }

        this.chatArea.appendChild(messageDiv);
        this.chatArea.scrollTop = this.chatArea.scrollHeight;
    }

    updateSendButton(isLoading) {
        if (!this.sendButton) return;
        
        if (isLoading) {
            this.sendButton.textContent = 'Sending...';
            this.sendButton.disabled = true;
        } else {
            this.sendButton.textContent = 'Send';
            this.sendButton.disabled = false;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SophiaV4Interface();
});

// Also initialize immediately in case DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new SophiaV4Interface();
    });
} else {
    new SophiaV4Interface();
}

