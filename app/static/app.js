/**
 * ASK AI Skills Builder - Frontend Application
 *
 * Handles WebSocket communication, message rendering,
 * agent status updates, and voice input via Web Speech API.
 */

class AskAIApp {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.isRecording = false;
        this.recognition = null;
        this.statusHistory = [];
        this.completedStates = new Set();
        this.currentActiveState = null;

        // DOM elements
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.voiceBtn = document.getElementById('voiceBtn');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.activityLog = document.getElementById('activityLog');
        this.voiceStatus = document.getElementById('voiceStatus');

        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.setupVoiceRecognition();
    }

    // ─── WebSocket ─────────────────────────────────────────

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.updateConnectionStatus('connecting');
        this.addLogEntry('Connecting to agent...', 'info');

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.isConnected = true;
            this.updateConnectionStatus('connected');
            this.addLogEntry('Connected to agent', 'success');
            this.enableInput();
            // Clear welcome hint
            const hint = this.messagesContainer.querySelector('.welcome-hint');
            if (hint) hint.remove();
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        };

        this.ws.onclose = () => {
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            this.addLogEntry('Disconnected from agent', 'error');
            this.disableInput();
            // Attempt reconnect after 3 seconds
            setTimeout(() => this.setupWebSocket(), 3000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.addLogEntry('Connection error', 'error');
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'message':
                this.addChatMessage(data.sender, data.content);
                break;
            case 'status':
                this.updateAgentStatus(data.status, data.detail);
                break;
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    sendMessage(content) {
        if (!this.isConnected || !content.trim()) return;

        this.ws.send(JSON.stringify({
            type: 'message',
            content: content.trim()
        }));

        this.messageInput.value = '';
    }

    // ─── Event Listeners ───────────────────────────────────

    setupEventListeners() {
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage(this.messageInput.value);
        });

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage(this.messageInput.value);
            }
        });

        this.voiceBtn.addEventListener('click', () => {
            this.toggleVoiceRecognition();
        });
    }

    // ─── Voice Recognition ─────────────────────────────────

    setupVoiceRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            this.voiceStatus.textContent = 'Voice: not supported';
            this.voiceStatus.className = 'unavailable';
            this.voiceBtn.disabled = true;
            this.voiceBtn.title = 'Voice input not supported in this browser';
            return;
        }

        this.voiceStatus.textContent = 'Voice: available';
        this.voiceStatus.className = 'available';

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join('');

            this.messageInput.value = transcript;

            // If final result, auto-send
            if (event.results[event.results.length - 1].isFinal) {
                setTimeout(() => {
                    this.sendMessage(transcript);
                    this.stopVoiceRecognition();
                }, 500);
            }
        };

        this.recognition.onend = () => {
            this.stopVoiceRecognition();
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.addLogEntry(`Voice error: ${event.error}`, 'warning');
            this.stopVoiceRecognition();
        };
    }

    toggleVoiceRecognition() {
        if (this.isRecording) {
            this.stopVoiceRecognition();
        } else {
            this.startVoiceRecognition();
        }
    }

    startVoiceRecognition() {
        if (!this.recognition) return;
        this.isRecording = true;
        this.voiceBtn.classList.add('recording');
        this.voiceBtn.title = 'Recording... Click to stop';
        this.messageInput.placeholder = 'Listening...';
        this.addLogEntry('Voice recording started', 'info');
        try {
            this.recognition.start();
        } catch (e) {
            this.stopVoiceRecognition();
        }
    }

    stopVoiceRecognition() {
        this.isRecording = false;
        this.voiceBtn.classList.remove('recording');
        this.voiceBtn.title = 'Click to speak (Web Speech API)';
        this.messageInput.placeholder = 'Type your message...';
        if (this.recognition) {
            try { this.recognition.stop(); } catch (e) {}
        }
    }

    // ─── Chat Messages ─────────────────────────────────────

    addChatMessage(sender, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        const header = document.createElement('div');
        header.className = 'message-header';
        header.innerHTML = `<span class="message-sender">${sender === 'agent' ? 'Agent' : 'You'}</span>
                           <span class="message-time">${this.getTimeString()}</span>`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = this.renderMarkdown(content);

        msgDiv.appendChild(header);
        msgDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(msgDiv);
        this.scrollToBottom();
    }

    renderMarkdown(text) {
        if (!text) return '';

        let html = text
            // Escape HTML
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')

            // Headings (### only for chat)
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')

            // Horizontal rules
            .replace(/^---$/gm, '<hr>')

            // Bold
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

            // Italic
            .replace(/_(.+?)_/g, '<em>$1</em>')

            // Inline code
            .replace(/`([^`]+)`/g, '<code>$1</code>')

            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')

            // Ordered list items
            .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')

            // Unordered list items (lines starting with - or *)
            .replace(/^[\-\*]\s+(.+)$/gm, '<li>$1</li>')

            // Paragraphs (double newline)
            .replace(/\n\n/g, '</p><p>')

            // Single newlines
            .replace(/\n/g, '<br>');

        // Wrap in paragraph
        html = '<p>' + html + '</p>';

        // Clean up empty paragraphs
        html = html.replace(/<p><\/p>/g, '');
        html = html.replace(/<p><br><\/p>/g, '');

        return html;
    }

    // ─── Agent Status ──────────────────────────────────────

    updateAgentStatus(status, detail) {
        this.addLogEntry(detail || status, this.getStatusLogType(status));

        // Map status to state machine items
        const stateMap = {
            'ready': 'ready',
            'searching': 'searching',
            'deep_search': 'searching',
            'results_found': 'results_found',
            'site_selected': 'results_found',
            'checking_docs': 'checking_docs',
            'docs_found': 'checking_docs',
            'no_docs': 'checking_docs',
            'checking_ask_ai': 'checking_ask_ai',
            'ask_ai_found': 'checking_ask_ai',
            'no_ask_ai': 'checking_ask_ai',
            'interacting': 'interacting',
            'extracting': 'interacting',
            'complete': 'complete',
            'error': null,
            'ended': null,
            'no_results': 'searching',
        };

        const targetState = stateMap[status];

        // Mark previous active state as completed
        if (this.currentActiveState && this.currentActiveState !== targetState) {
            const prevEl = document.querySelector(`.state-item[data-state="${this.currentActiveState}"]`);
            if (prevEl) {
                prevEl.classList.remove('active');
                // Mark as completed if it's a success status
                if (!['error', 'no_docs', 'no_ask_ai', 'no_results'].includes(status)) {
                    prevEl.classList.add('completed');
                    this.completedStates.add(this.currentActiveState);
                }
            }
        }

        // Set new active state
        if (targetState) {
            const el = document.querySelector(`.state-item[data-state="${targetState}"]`);
            if (el) {
                el.classList.remove('completed');
                el.classList.add('active');
                this.currentActiveState = targetState;
            }
        }

        // Handle terminal states
        if (status === 'complete') {
            // Mark all states as completed
            document.querySelectorAll('.state-item').forEach(el => {
                el.classList.remove('active');
                el.classList.add('completed');
            });
            this.currentActiveState = null;
        }

        if (status === 'error') {
            if (this.currentActiveState) {
                const el = document.querySelector(`.state-item[data-state="${this.currentActiveState}"]`);
                if (el) {
                    el.classList.remove('active');
                    el.classList.add('error');
                }
            }
        }

        if (status === 'ended') {
            document.querySelectorAll('.state-item.active').forEach(el => {
                el.classList.remove('active');
                el.classList.add('completed');
            });
        }
    }

    getStatusLogType(status) {
        const types = {
            'ready': 'info',
            'searching': 'info',
            'deep_search': 'info',
            'results_found': 'success',
            'site_selected': 'success',
            'checking_docs': 'info',
            'docs_found': 'success',
            'no_docs': 'warning',
            'checking_ask_ai': 'info',
            'ask_ai_found': 'success',
            'no_ask_ai': 'warning',
            'interacting': 'info',
            'extracting': 'info',
            'complete': 'success',
            'error': 'error',
            'ended': 'info',
            'no_results': 'warning',
        };
        return types[status] || 'info';
    }

    // ─── Activity Log ──────────────────────────────────────

    addLogEntry(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `<span class="log-time">${this.getTimeString()}</span>
                          <span class="log-msg">${message}</span>`;

        // Remove initial placeholder
        const placeholder = this.activityLog.querySelector('.log-entry:first-child');
        if (placeholder && placeholder.querySelector('.log-msg').textContent === 'Waiting for connection...') {
            placeholder.remove();
        }

        this.activityLog.appendChild(entry);
        this.activityLog.scrollTop = this.activityLog.scrollHeight;
    }

    // ─── UI Helpers ────────────────────────────────────────

    updateConnectionStatus(state) {
        const dot = this.connectionStatus.querySelector('.status-dot');
        const text = this.connectionStatus.querySelector('.status-text');

        dot.className = `status-dot ${state}`;
        text.textContent = state.charAt(0).toUpperCase() + state.slice(1);
    }

    enableInput() {
        this.messageInput.disabled = false;
        this.sendBtn.disabled = false;
        if (this.recognition) {
            this.voiceBtn.disabled = false;
        }
        this.messageInput.focus();
    }

    disableInput() {
        this.messageInput.disabled = true;
        this.sendBtn.disabled = true;
        this.voiceBtn.disabled = true;
    }

    scrollToBottom() {
        requestAnimationFrame(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        });
    }

    getTimeString() {
        const now = new Date();
        return now.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.askAIApp = new AskAIApp();
});
