// Native Chat Interface for Sophia Intel AI Hub
class ChatInterface {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.messages = [];
        this.isProcessing = false;
        this.initializeUI();
        this.attachEventListeners();
    }

    initializeUI() {
        this.container.innerHTML = `
            <div class="chat-container">
                <div class="chat-header">
                    <h3>AI Assistant</h3>
                    <span class="chat-status" id="chat-status">Ready</span>
                </div>
                <div class="chat-messages" id="chat-messages">
                    <div class="chat-message assistant">
                        <div class="message-content">
                            Hello! I'm your AI assistant. How can I help you today?
                        </div>
                    </div>
                </div>
                <div class="chat-input-container">
                    <textarea
                        id="chat-input"
                        class="chat-input"
                        placeholder="Type your message here..."
                        rows="3"
                    ></textarea>
                    <div class="chat-controls">
                        <select id="model-selector" class="model-selector">
                            <option value="openai/gpt-5" selected>GPT-5</option>
                            <option value="x-ai/grok-4">Grok 4</option>
                            <option value="anthropic/claude-sonnet-4">Claude Sonnet 4</option>
                            <option value="x-ai/grok-code-fast-1">Grok Code Fast</option>
                            <option value="google/gemini-2.5-flash">Gemini 2.5 Flash</option>
                            <option value="google/gemini-2.5-pro">Gemini 2.5 Pro</option>
                            <option value="deepseek/deepseek-chat-v3-0324">DeepSeek v3.0324</option>
                            <option value="deepseek/deepseek-chat-v3.1">DeepSeek v3.1</option>
                            <option value="qwen/qwen3-30b-a3b">Qwen3 30B</option>
                            <option value="z-ai/glm-4.5-air">GLM 4.5 Air</option>
                        </select>
                        <button id="send-button" class="send-button">Send</button>
                    </div>
                </div>
            </div>
        `;

        this.messagesContainer = document.getElementById('chat-messages');
        this.inputField = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        this.statusIndicator = document.getElementById('chat-status');
        this.modelSelector = document.getElementById('model-selector');
    }

    attachEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    async sendMessage() {
        const message = this.inputField.value.trim();
        if (!message || this.isProcessing) return;

        this.isProcessing = true;
        this.setStatus('Processing...');

        // Add user message to chat
        this.addMessage(message, 'user');
        this.inputField.value = '';

        // Prepare messages for API
        const messages = [
            ...this.messages,
            { role: 'user', content: message }
        ];

        try {
            const response = await fetch('/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: this.modelSelector.value,
                    messages: messages,
                    max_tokens: 1000,
                    temperature: 0.7
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.choices && data.choices[0]) {
                const assistantMessage = data.choices[0].message.content;
                this.addMessage(assistantMessage, 'assistant');

                // Update conversation history
                this.messages.push(
                    { role: 'user', content: message },
                    { role: 'assistant', content: assistantMessage }
                );

                // Keep conversation history manageable
                if (this.messages.length > 20) {
                    this.messages = this.messages.slice(-20);
                }
            }

            this.setStatus('Ready');
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'error');
            this.setStatus('Error');
        } finally {
            this.isProcessing = false;
        }
    }

    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    setStatus(status) {
        this.statusIndicator.textContent = status;
        this.statusIndicator.className = `chat-status ${status.toLowerCase().replace(/\s+/g, '-')}`;
    }

    clear() {
        this.messages = [];
        this.messagesContainer.innerHTML = `
            <div class="chat-message assistant">
                <div class="message-content">
                    Chat cleared. How can I help you?
                </div>
            </div>
        `;
    }
}

// Export for use in hub-controller.js
window.ChatInterface = ChatInterface;
