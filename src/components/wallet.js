/**
 * Wallet UI Component
 * Displays balance, token list, and live token feed with real-time updates
 */

class WalletUI {
  constructor(tokenService, options = {}) {
    this.tokenService = tokenService;
    this.containerId = options.containerId || 'wallet-container';
    this.feedEnabled = options.feedEnabled !== false;
    this.refreshInterval = options.refreshInterval || 5000;
    this.walletAddress = options.walletAddress || 'default';
    this.balance = 0;
    this.tokens = [];
    this.initialized = false;
  }

  /**
   * Initialize wallet UI
   */
  async init() {
    if (this.initialized) return;

    await this.tokenService.init();
    
    // Load initial data
    await this.refreshBalance();
    await this.refreshTokens();
    
    // Render UI
    this.render();
    
    // Set up auto-refresh
    if (this.refreshInterval > 0) {
      setInterval(() => this.refresh(), this.refreshInterval);
    }
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Enable live feed
    if (this.feedEnabled) {
      this.enableLiveFeed();
    }
    
    this.initialized = true;
    console.log('[WalletUI] Initialized');
  }

  /**
   * Set up event listeners
   */
  setupEventListeners() {
    // Listen for token created events
    window.addEventListener('pewpi.token.created', (event) => {
      this.handleTokenCreated(event.detail);
    });

    // Listen for token updated events
    window.addEventListener('pewpi.token.updated', (event) => {
      this.handleTokenUpdated(event.detail);
    });

    // Listen for wallet updated events
    window.addEventListener('pewpi.wallet.updated', (event) => {
      this.handleWalletUpdated(event.detail);
    });
  }

  /**
   * Refresh wallet balance
   */
  async refreshBalance() {
    this.balance = await this.tokenService.getBalance(this.walletAddress);
  }

  /**
   * Refresh token list
   */
  async refreshTokens() {
    this.tokens = await this.tokenService.getAll();
    // Sort by created_at descending
    this.tokens.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }

  /**
   * Refresh all data
   */
  async refresh() {
    await this.refreshBalance();
    await this.refreshTokens();
    this.render();
  }

  /**
   * Render wallet UI
   */
  render() {
    const container = document.getElementById(this.containerId);
    if (!container) {
      console.error('[WalletUI] Container not found:', this.containerId);
      return;
    }

    container.innerHTML = `
      <div class="wallet-ui">
        ${this.renderHeader()}
        ${this.renderBalance()}
        ${this.renderTokenList()}
        ${this.feedEnabled ? this.renderLiveFeed() : ''}
      </div>
    `;

    // Re-attach event listeners after render
    this.attachUIEventListeners();
  }

  /**
   * Render header
   */
  renderHeader() {
    return `
      <div class="wallet-header">
        <h2 class="wallet-title">💼 My Wallet</h2>
        <button id="wallet-refresh-btn" class="wallet-btn wallet-btn-secondary">
          🔄 Refresh
        </button>
      </div>
    `;
  }

  /**
   * Render balance section
   */
  renderBalance() {
    return `
      <div class="wallet-balance">
        <div class="balance-label">Total Balance</div>
        <div class="balance-amount">${this.formatValue(this.balance)}</div>
        <div class="balance-tokens">
          <span class="token-count">${this.tokens.length}</span> tokens
        </div>
      </div>
    `;
  }

  /**
   * Render token list
   */
  renderTokenList() {
    if (this.tokens.length === 0) {
      return `
        <div class="wallet-section">
          <h3 class="section-title">Token List</h3>
          <div class="empty-state">
            <p>No tokens yet. Create your first token!</p>
          </div>
        </div>
      `;
    }

    return `
      <div class="wallet-section">
        <h3 class="section-title">Token List (${this.tokens.length})</h3>
        <div class="token-list">
          ${this.tokens.map(token => this.renderTokenCard(token)).join('')}
        </div>
      </div>
    `;
  }

  /**
   * Render individual token card
   */
  renderTokenCard(token) {
    return `
      <div class="token-card" data-hash="${this.escapeHtml(token.hash)}">
        <div class="token-card-header">
          <span class="token-type">${this.escapeHtml(token.type || 'standard')}</span>
          <span class="token-value">${this.formatValue(token.value || 0)}</span>
        </div>
        <div class="token-hash">
          <code>${this.escapeHtml(token.hash.substring(0, 16))}...</code>
        </div>
        <div class="token-metadata">
          <span class="token-owner">👤 ${this.escapeHtml(token.owner || 'anonymous')}</span>
          <span class="token-date">📅 ${this.formatDate(token.created_at)}</span>
        </div>
        <button class="token-detail-btn" data-hash="${this.escapeHtml(token.hash)}">
          View Details
        </button>
      </div>
    `;
  }

  /**
   * Render live feed section
   */
  renderLiveFeed() {
    return `
      <div class="wallet-section">
        <h3 class="section-title">🔴 Live Token Feed</h3>
        <div id="live-feed" class="live-feed">
          <div class="feed-item feed-info">
            Waiting for token updates...
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Attach UI event listeners
   */
  attachUIEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('wallet-refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.refresh());
    }

    // Token detail buttons
    const detailButtons = document.querySelectorAll('.token-detail-btn');
    detailButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const hash = e.target.dataset.hash;
        this.showTokenDetail(hash);
      });
    });
  }

  /**
   * Enable live feed
   */
  enableLiveFeed() {
    // Already set up in setupEventListeners
    console.log('[WalletUI] Live feed enabled');
  }

  /**
   * Handle token created event
   */
  async handleTokenCreated(token) {
    console.log('[WalletUI] Token created:', token);
    
    // Add to live feed
    this.addFeedItem('created', token);
    
    // Refresh data
    await this.refresh();
  }

  /**
   * Handle token updated event
   */
  async handleTokenUpdated(data) {
    console.log('[WalletUI] Token updated:', data);
    
    // Add to live feed
    this.addFeedItem('updated', data);
    
    // Refresh data
    await this.refresh();
  }

  /**
   * Handle wallet updated event
   */
  async handleWalletUpdated(data) {
    console.log('[WalletUI] Wallet updated:', data);
    
    if (data.address === this.walletAddress) {
      await this.refreshBalance();
      this.updateBalanceDisplay();
    }
  }

  /**
   * Add item to live feed
   */
  addFeedItem(type, data) {
    const feedContainer = document.getElementById('live-feed');
    if (!feedContainer) return;

    const item = document.createElement('div');
    item.className = `feed-item feed-${type}`;
    item.innerHTML = `
      <span class="feed-time">${this.formatTime(new Date())}</span>
      <span class="feed-message">
        ${type === 'created' ? '✨ New token created' : '🔄 Token updated'}:
        <code>${this.escapeHtml(data.hash?.substring(0, 12) || 'unknown')}</code>
      </span>
    `;

    feedContainer.insertBefore(item, feedContainer.firstChild);

    // Keep only last 20 items
    while (feedContainer.children.length > 20) {
      feedContainer.removeChild(feedContainer.lastChild);
    }

    // Animate
    item.style.animation = 'slideIn 0.3s ease';
  }

  /**
   * Update balance display only
   */
  updateBalanceDisplay() {
    const balanceAmount = document.querySelector('.balance-amount');
    if (balanceAmount) {
      balanceAmount.textContent = this.formatValue(this.balance);
    }

    const tokenCount = document.querySelector('.token-count');
    if (tokenCount) {
      tokenCount.textContent = this.tokens.length;
    }
  }

  /**
   * Show token detail modal/panel
   */
  async showTokenDetail(hash) {
    const token = await this.tokenService.getByHash(hash);
    if (!token) {
      alert('Token not found');
      return;
    }

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'token-detail-modal';
    modal.innerHTML = `
      <div class="modal-overlay"></div>
      <div class="modal-content">
        <button class="modal-close">×</button>
        <h3>Token Details</h3>
        <div class="token-detail">
          <div class="detail-row">
            <span class="detail-label">Hash:</span>
            <code class="detail-value">${this.escapeHtml(token.hash)}</code>
          </div>
          <div class="detail-row">
            <span class="detail-label">Type:</span>
            <span class="detail-value">${this.escapeHtml(token.type || 'standard')}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Value:</span>
            <span class="detail-value">${this.formatValue(token.value || 0)}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Owner:</span>
            <span class="detail-value">${this.escapeHtml(token.owner || 'anonymous')}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Created:</span>
            <span class="detail-value">${this.formatDate(token.created_at)}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Updated:</span>
            <span class="detail-value">${this.formatDate(token.updated_at)}</span>
          </div>
          ${token.metadata ? `
            <div class="detail-row">
              <span class="detail-label">Metadata:</span>
              <pre class="detail-value">${JSON.stringify(token.metadata, null, 2)}</pre>
            </div>
          ` : ''}
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Close handlers
    const closeBtn = modal.querySelector('.modal-close');
    const overlay = modal.querySelector('.modal-overlay');
    
    const closeModal = () => {
      document.body.removeChild(modal);
    };
    
    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', closeModal);
  }

  /**
   * Format value as currency
   */
  formatValue(value) {
    if (!value) return '$0.00';
    
    if (value >= 1_000_000_000_000) {
      return `$${(value / 1_000_000_000_000).toFixed(2)}T`;
    } else if (value >= 1_000_000_000) {
      return `$${(value / 1_000_000_000).toFixed(2)}B`;
    } else if (value >= 1_000_000) {
      return `$${(value / 1_000_000).toFixed(2)}M`;
    } else if (value >= 1_000) {
      return `$${(value / 1_000).toFixed(2)}K`;
    } else {
      return `$${value.toFixed(2)}`;
    }
  }

  /**
   * Format date
   */
  formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Invalid date';
    }
  }

  /**
   * Format time
   */
  formatTime(date) {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Destroy wallet UI
   */
  destroy() {
    // Clear any intervals
    this.initialized = false;
  }
}

// Export for use in different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = WalletUI;
}
if (typeof window !== 'undefined') {
  window.WalletUI = WalletUI;
}
