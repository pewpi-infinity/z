/**
 * Chat Terminal for Mongoose OS Integration
 * Provides terminal-style interface for device communication
 */

class ChatTerminal {
  constructor(containerId = 'chat-terminal') {
    this.container = document.getElementById(containerId);
    this.messageHistory = [];
    this.commandHistory = [];
    this.historyIndex = -1;
    this.initialized = false;
  }

  /**
   * Initialize the chat terminal
   */
  init() {
    if (this.initialized) return;

    if (!this.container) {
      console.error('[ChatTerminal] Container not found');
      return;
    }

    this.render();
    this.setupEventListeners();
    this.addSystemMessage('Mongoose OS Chat Terminal initialized. Type "help" for commands.');
    this.initialized = true;
  }

  /**
   * Render the terminal UI
   */
  render() {
    this.container.innerHTML = `
      <div class="chat-terminal-wrapper">
        <div class="chat-header">
          <span class="chat-title">∞ Mongoose OS Terminal</span>
          <button class="chat-close-btn" id="chat-close-btn">×</button>
        </div>
        <div class="chat-messages" id="chat-messages"></div>
        <div class="chat-input-wrapper">
          <span class="chat-prompt">mongoose&gt;</span>
          <input 
            type="text" 
            class="chat-input" 
            id="chat-input" 
            placeholder="Type 'help' for commands..."
            autocomplete="off"
          />
        </div>
      </div>
    `;
  }

  /**
   * Set up event listeners
   */
  setupEventListeners() {
    const input = document.getElementById('chat-input');
    const closeBtn = document.getElementById('chat-close-btn');

    if (input) {
      input.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }
  }

  /**
   * Handle keyboard input
   */
  handleKeyDown(event) {
    const input = event.target;

    switch (event.key) {
      case 'Enter':
        event.preventDefault();
        this.handleCommand(input.value);
        input.value = '';
        this.historyIndex = -1;
        break;

      case 'ArrowUp':
        event.preventDefault();
        this.navigateHistory('up');
        break;

      case 'ArrowDown':
        event.preventDefault();
        this.navigateHistory('down');
        break;

      case 'Tab':
        event.preventDefault();
        this.autoComplete(input);
        break;
    }
  }

  /**
   * Navigate command history
   */
  navigateHistory(direction) {
    const input = document.getElementById('chat-input');
    if (!input) return;

    if (this.commandHistory.length === 0) return;

    if (direction === 'up') {
      this.historyIndex = Math.min(
        this.historyIndex + 1,
        this.commandHistory.length - 1
      );
    } else if (direction === 'down') {
      this.historyIndex = Math.max(this.historyIndex - 1, -1);
    }

    if (this.historyIndex >= 0) {
      input.value = this.commandHistory[this.historyIndex];
    } else {
      input.value = '';
    }
  }

  /**
   * Auto-complete command
   */
  autoComplete(input) {
    const commands = ['status', 'help', 'info', 'clear'];
    const value = input.value.toLowerCase();

    const matches = commands.filter(cmd => cmd.startsWith(value));

    if (matches.length === 1) {
      input.value = matches[0];
    } else if (matches.length > 1) {
      this.addSystemMessage(`Possible commands: ${matches.join(', ')}`);
    }
  }

  /**
   * Handle user command
   */
  async handleCommand(command) {
    command = command.trim();

    if (!command) return;

    // Add to history
    this.commandHistory.unshift(command);
    if (this.commandHistory.length > 50) {
      this.commandHistory.pop();
    }

    // Display user command
    this.addUserMessage(command);

    // Handle local commands
    if (command.toLowerCase() === 'clear') {
      this.clearMessages();
      return;
    }

    // Check authentication
    if (!window.authManager || !window.authManager.authenticated) {
      this.addErrorMessage('Authentication required. Please log in to use the chat terminal.');
      return;
    }

    // Send to backend
    try {
      const response = await fetch('/api/mongoose/chat', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ message: command })
      });

      const data = await response.json();

      if (data.success) {
        if (data.commands) {
          // Help command response
          this.addSystemMessage('Available commands:');
          data.commands.forEach(cmd => {
            this.addSystemMessage(`  ${cmd.command} - ${cmd.description}`);
            this.addSystemMessage(`    Usage: ${cmd.usage}`);
          });
        } else if (data.response) {
          // Device response
          this.addSuccessMessage(JSON.stringify(data.response, null, 2));
        } else {
          // General success message
          this.addSuccessMessage(data.message || 'Command executed successfully');
        }
      } else {
        this.addErrorMessage(data.message || data.error || 'Command failed');
      }
    } catch (error) {
      console.error('[ChatTerminal] Command error:', error);
      this.addErrorMessage(`Error: ${error.message}`);
    }
  }

  /**
   * Add user message to terminal
   */
  addUserMessage(message) {
    this.addMessage(message, 'user');
  }

  /**
   * Add system message to terminal
   */
  addSystemMessage(message) {
    this.addMessage(message, 'system');
  }

  /**
   * Add success message to terminal
   */
  addSuccessMessage(message) {
    this.addMessage(message, 'success');
  }

  /**
   * Add error message to terminal
   */
  addErrorMessage(message) {
    this.addMessage(message, 'error');
  }

  /**
   * Add message to terminal
   */
  addMessage(content, type = 'system') {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const messageEl = document.createElement('div');
    messageEl.className = `chat-message chat-message-${type}`;

    const timestamp = new Date().toLocaleTimeString();
    
    if (type === 'user') {
      messageEl.innerHTML = `
        <span class="chat-timestamp">[${timestamp}]</span>
        <span class="chat-prompt">mongoose&gt;</span>
        <span class="chat-text">${this.escapeHtml(content)}</span>
      `;
    } else {
      const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
      messageEl.innerHTML = `
        <span class="chat-timestamp">[${timestamp}]</span>
        <span class="chat-prefix">${prefix}</span>
        <span class="chat-text">${this.escapeHtml(content)}</span>
      `;
    }

    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    this.messageHistory.push({ content, type, timestamp });
  }

  /**
   * Clear all messages
   */
  clearMessages() {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.innerHTML = '';
      this.messageHistory = [];
      this.addSystemMessage('Terminal cleared.');
    }
  }

  /**
   * Close the terminal
   */
  close() {
    if (this.container) {
      this.container.style.display = 'none';
    }
  }

  /**
   * Open the terminal
   */
  open() {
    if (this.container) {
      this.container.style.display = 'block';
      const input = document.getElementById('chat-input');
      if (input) {
        input.focus();
      }
    }
  }

  /**
   * Toggle terminal visibility
   */
  toggle() {
    if (this.container) {
      if (this.container.style.display === 'none') {
        this.open();
      } else {
        this.close();
      }
    }
  }

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Create global chat terminal instance
const chatTerminal = new ChatTerminal('chat-terminal');

// Export for use in other scripts
window.chatTerminal = chatTerminal;
