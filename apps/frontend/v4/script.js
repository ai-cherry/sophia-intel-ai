/**
 * SOPHIA V4 Frontend JavaScript - FIXED VERSION
 * Connects Pay Ready interface to production backend APIs
 */

class SophiaV4Interface {
    constructor() {
        this.apiBase = window.location.origin;
        this.isProcessing = false;
        this.userId = 'patrick_001'; // Real user ID for Patrick
        this.initializeInterface();
        this.bindEvents();
    }

    initializeInterface() {
        // Get actual DOM elements from the page
        this.chatMessages = document.querySelector('.chat-area') || document.querySelector('#chat-messages');
        this.chatInput = document.querySelector('input[placeholder*="SOPHIA"]') || document.querySelector('#chat-input');
        this.sendButton = document.querySelector('button') || document.querySelector('#send-button');
        
        console.log('DOM elements found:', {
            chatMessages: !!this.chatMessages,
            chatInput: !!this.chatInput, 
            sendButton: !!this.sendButton
        });
        
        // Add welcome message to chat area
        if (this.chatMessages) {
            this.addMessage("🤠 Howdy! SOPHIA V4 is locked and loaded with real autonomous capabilities. I can research, coordinate swarms, commit code, and deploy apps. What's the mission, partner?", 'assistant');
        }
    }

    bindEvents() {
        // Chat input events
        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }
    }

    async sendMessage() {
        if (this.isProcessing) return;

        const message = this.chatInput?.value?.trim();
        if (!message) return;

        this.isProcessing = true;
        if (this.chatInput) this.chatInput.value = '';
        this.updateSendButton(true);

        // Add user message
        this.addMessage(message, 'user');

        try {
            // Use persona endpoint for all interactions to get SOPHIA's personality
            const result = await this.chatWithSophia(message);
            this.displayPersonaResult(result);

        } catch (error) {
            console.error('Message processing error:', error);
            this.addMessage(`Error: ${error.message}`, 'error');
        } finally {
            this.isProcessing = false;
            this.updateSendButton(false);
        }
    }

    async chatWithSophia(query) {
        const response = await fetch(`${this.apiBase}/api/v1/persona`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                user_id: this.userId
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`SOPHIA chat failed: ${response.status} - ${errorText}`);
        }

        return await response.json();
    }

    async performResearch(query) {
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
            throw new Error(`Research failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    async triggerSwarm(task) {
        const response = await fetch(`${this.apiBase}/api/v1/swarm/trigger`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                task: task,
                agents: ['research', 'analysis'],
                objective: `Complete task: ${task}`
            })
        });

        if (!response.ok) {
            throw new Error(`Swarm coordination failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    async createCommit(repo, changes) {
        const response = await fetch(`${this.apiBase}/api/v1/code/commit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repo: repo,
                changes: changes,
                file_path: `frontend_interaction_${Date.now()}.txt`
            })
        });

        if (!response.ok) {
            throw new Error(`Commit creation failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    displayPersonaResult(result) {
        let message = '';
        
        if (result.response) {
            message = result.response;
        } else if (result.persona && result.persona.name) {
            message = `🤠 ${result.persona.name} here! ${result.persona.tone}`;
        } else {
            message = 'SOPHIA V4 received your message!';
        }

        this.addMessage(message, 'assistant');
    }

    addMessage(content, type) {
        if (!this.chatMessages) {
            console.warn('Chat messages container not found');
            return;
        }

        // Clear the default message if it exists
        const defaultMsg = this.chatMessages.querySelector('.default-message');
        if (defaultMsg) {
            defaultMsg.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.style.cssText = `
            margin: 10px 0;
            padding: 12px;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
            ${type === 'user' ? 
                'background: #007bff; color: white; margin-left: auto; text-align: right;' : 
                'background: #f8f9fa; color: #333; margin-right: auto;'
            }
            ${type === 'error' ? 'background: #dc3545; color: white;' : ''}
        `;
        
        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div style="font-size: 14px; line-height: 1.4;">
                ${this.formatMessageContent(content)}
            </div>
            <div style="font-size: 11px; opacity: 0.7; margin-top: 5px;">
                ${timestamp}
            </div>
        `;

        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    formatMessageContent(content) {
        // Convert markdown-style formatting to HTML and preserve line breaks
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code style="background: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 3px;">$1</code>')
            .replace(/🔗 \[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: #007bff;">🔗 $1</a>')
            .replace(/\n/g, '<br>');
    }

    updateSendButton(processing) {
        if (!this.sendButton) return;

        if (processing) {
            this.sendButton.textContent = 'Processing...';
            this.sendButton.disabled = true;
            this.sendButton.style.opacity = '0.6';
        } else {
            this.sendButton.textContent = 'Send';
            this.sendButton.disabled = false;
            this.sendButton.style.opacity = '1';
        }
    }
}

// Initialize interface when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing SOPHIA V4 interface...');
    window.sophiaInterface = new SophiaV4Interface();
    console.log('SOPHIA V4 Pay Ready interface initialized');
});

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    if (window.sophiaInterface) {
        window.sophiaInterface.addMessage(`System error: ${event.error.message}`, 'error');
    }
});

