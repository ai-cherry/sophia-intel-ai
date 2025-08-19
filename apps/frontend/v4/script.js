/**
 * SOPHIA V4 Frontend JavaScript
 * Connects Pay Ready interface to production backend APIs
 */

class SophiaV4Interface {
    constructor() {
        this.apiBase = window.location.origin;
        this.isProcessing = false;
        this.initializeInterface();
        this.bindEvents();
    }

    initializeInterface() {
        // Initialize chat interface
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        
        // Initialize status indicators
        this.updateSystemStatus();
        
        // Add welcome message
        this.addMessage("SOPHIA V4 Pay Ready is online. I can perform web research, coordinate AI swarms, create GitHub commits, and trigger deployments. How can I help you?", 'assistant');
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

        // Card interaction events
        this.bindCardEvents();
    }

    bindCardEvents() {
        // Agent Factory card
        const agentFactoryCard = document.querySelector('.card[data-card="agent-factory"]');
        if (agentFactoryCard) {
            agentFactoryCard.addEventListener('click', () => {
                this.triggerSwarm('Initialize agent factory for multi-agent coordination');
            });
        }

        // OKR Tracking card
        const okrCard = document.querySelector('.card[data-card="okr-tracking"]');
        if (okrCard) {
            okrCard.addEventListener('click', () => {
                this.performResearch('Current OKR tracking methodologies and best practices');
            });
        }

        // Bulletin Board card
        const bulletinCard = document.querySelector('.card[data-card="bulletin"]');
        if (bulletinCard) {
            bulletinCard.addEventListener('click', () => {
                this.createCommit('ai-cherry/sophia-intel', 'Update bulletin board with latest system status');
            });
        }
    }

    async sendMessage() {
        if (this.isProcessing) return;

        const message = this.chatInput.value.trim();
        if (!message) return;

        this.isProcessing = true;
        this.chatInput.value = '';
        this.updateSendButton(true);

        // Add user message
        this.addMessage(message, 'user');

        try {
            // Determine message type and route to appropriate endpoint
            const messageType = this.analyzeMessageType(message);
            let result;

            switch (messageType) {
                case 'research':
                    result = await this.performResearch(message);
                    break;
                case 'swarm':
                    result = await this.triggerSwarm(message);
                    break;
                case 'commit':
                    result = await this.createCommit('ai-cherry/sophia-intel', message);
                    break;
                case 'deploy':
                    result = await this.triggerDeployment();
                    break;
                default:
                    result = await this.performResearch(message); // Default to research
            }

            this.displayResult(result, messageType);

        } catch (error) {
            console.error('Message processing error:', error);
            this.addMessage(`Error: ${error.message}`, 'error');
        } finally {
            this.isProcessing = false;
            this.updateSendButton(false);
        }
    }

    analyzeMessageType(message) {
        const messageLower = message.toLowerCase();
        
        if (messageLower.includes('research') || messageLower.includes('find') || messageLower.includes('search')) {
            return 'research';
        }
        if (messageLower.includes('swarm') || messageLower.includes('coordinate') || messageLower.includes('agents')) {
            return 'swarm';
        }
        if (messageLower.includes('commit') || messageLower.includes('code') || messageLower.includes('github')) {
            return 'commit';
        }
        if (messageLower.includes('deploy') || messageLower.includes('release')) {
            return 'deploy';
        }
        
        return 'research'; // Default
    }

    async performResearch(query) {
        const response = await fetch(`${this.apiBase}/api/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
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
                priority: 'high'
            })
        });

        if (!response.ok) {
            throw new Error(`Swarm coordination failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    async createCommit(repo, changes) {
        const response = await fetch(`${this.apiBase}/api/v1/code/modify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repo: repo,
                changes: changes,
                message: `SOPHIA V4 automated: ${changes}`
            })
        });

        if (!response.ok) {
            throw new Error(`Commit creation failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    async triggerDeployment() {
        const response = await fetch(`${this.apiBase}/api/v1/deploy/trigger`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                app_name: 'sophia-intel',
                environment: 'production'
            })
        });

        if (!response.ok) {
            throw new Error(`Deployment failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    displayResult(result, type) {
        let message = '';

        switch (type) {
            case 'research':
                message = this.formatResearchResult(result);
                break;
            case 'swarm':
                message = this.formatSwarmResult(result);
                break;
            case 'commit':
                message = this.formatCommitResult(result);
                break;
            case 'deploy':
                message = this.formatDeployResult(result);
                break;
            default:
                message = JSON.stringify(result, null, 2);
        }

        this.addMessage(message, 'assistant');
    }

    formatResearchResult(result) {
        if (!result.sources || result.sources.length === 0) {
            return `Research completed but no sources found for: "${result.query}"`;
        }

        let message = `🔍 **Research Results for: "${result.query}"**\n\n`;
        
        if (result.summary) {
            message += `**Summary:** ${result.summary}\n\n`;
        }

        message += `**Sources (${result.sources.length}):**\n`;
        result.sources.forEach((source, index) => {
            message += `${index + 1}. **${source.title}**\n`;
            message += `   ${source.summary}\n`;
            message += `   🔗 [View Source](${source.url})\n`;
            message += `   📊 Relevance: ${Math.round(source.relevance_score * 100)}%\n\n`;
        });

        message += `*Agent ID: ${result.agent_id}*\n`;
        message += `*Task ID: ${result.task_id}*`;

        return message;
    }

    formatSwarmResult(result) {
        let message = `🐝 **Swarm Coordination Complete**\n\n`;
        message += `**Task:** ${result.task}\n`;
        message += `**Priority:** ${result.priority}\n`;
        message += `**Coordinator ID:** ${result.coordinator_id}\n\n`;

        message += `**Agents Used:** ${result.agents_used.join(', ')}\n\n`;

        message += `**Results:**\n`;
        Object.entries(result.results).forEach(([agentType, agentResult]) => {
            message += `• **${agentType}**: ${agentResult.status}\n`;
            if (agentResult.status === 'success' && agentResult.result) {
                message += `  Agent ID: ${agentResult.agent_id}\n`;
            }
            if (agentResult.error) {
                message += `  Error: ${agentResult.error}\n`;
            }
        });

        message += `\n**Coordination Logs:**\n`;
        result.coordination_logs.forEach(log => {
            message += `• ${log}\n`;
        });

        return message;
    }

    formatCommitResult(result) {
        let message = `💻 **GitHub Commit Created**\n\n`;
        message += `**Repository:** ${result.repo}\n`;
        message += `**Commit Hash:** \`${result.commit_hash}\`\n`;
        message += `**Message:** ${result.message}\n`;
        message += `**Agent ID:** ${result.agent_id}\n\n`;
        message += `🔗 [View Commit](${result.commit_url})`;

        return message;
    }

    formatDeployResult(result) {
        let message = `🚀 **Deployment Triggered**\n\n`;
        message += `**App:** ${result.app_name}\n`;
        message += `**Environment:** ${result.environment}\n`;
        message += `**Deployment ID:** ${result.deployment_id}\n`;
        message += `**Status:** ${result.status}\n\n`;

        message += `**Deployment Logs:**\n`;
        result.logs.forEach(log => {
            message += `• ${log}\n`;
        });

        return message;
    }

    addMessage(content, type) {
        if (!this.chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">${this.formatMessageContent(content)}</div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;

        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    formatMessageContent(content) {
        // Convert markdown-style formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/🔗 \[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">🔗 $1</a>')
            .replace(/\n/g, '<br>');
    }

    updateSendButton(processing) {
        if (!this.sendButton) return;

        if (processing) {
            this.sendButton.textContent = 'Processing...';
            this.sendButton.disabled = true;
        } else {
            this.sendButton.textContent = 'Send';
            this.sendButton.disabled = false;
        }
    }

    async updateSystemStatus() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/system/stats`);
            if (response.ok) {
                const stats = await response.json();
                this.displaySystemStatus(stats);
            }
        } catch (error) {
            console.warn('Failed to fetch system status:', error);
        }
    }

    displaySystemStatus(stats) {
        // Update status indicators in the UI
        const statusElements = document.querySelectorAll('.status-indicator');
        statusElements.forEach(element => {
            element.classList.add('online');
            element.title = `SOPHIA V4 ${stats.version} - ${stats.uptime}`;
        });

        // Update version info
        const versionElements = document.querySelectorAll('.version-info');
        versionElements.forEach(element => {
            element.textContent = `v${stats.version}`;
        });
    }
}

// Initialize interface when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
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

