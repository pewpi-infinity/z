/**
 * Integration Listener Module
 * Demonstrates how other repositories can subscribe to pewpi token/wallet events
 * and sync state automatically
 */

class PewpiIntegrationListener {
  constructor(options = {}) {
    this.debug = options.debug !== false;
    this.callbacks = {
      tokenCreated: [],
      tokenUpdated: [],
      tokenDeleted: [],
      loginChanged: [],
      walletUpdated: [],
      tokensCleared: []
    };
  }

  /**
   * Initialize the integration listener
   */
  init() {
    this.log('Initializing Pewpi Integration Listener...');
    
    // Subscribe to all pewpi events
    this.subscribeToEvents();
    
    this.log('Integration listener ready');
    
    return this;
  }

  /**
   * Subscribe to all pewpi window events
   */
  subscribeToEvents() {
    // Token events
    window.addEventListener('pewpi.token.created', (event) => {
      this.log('Token created:', event.detail);
      this.trigger('tokenCreated', event.detail);
    });

    window.addEventListener('pewpi.token.updated', (event) => {
      this.log('Token updated:', event.detail);
      this.trigger('tokenUpdated', event.detail);
    });

    window.addEventListener('pewpi.token.deleted', (event) => {
      this.log('Token deleted:', event.detail);
      this.trigger('tokenDeleted', event.detail);
    });

    window.addEventListener('pewpi.tokens.cleared', (event) => {
      this.log('Tokens cleared:', event.detail);
      this.trigger('tokensCleared', event.detail);
    });

    // Login events
    window.addEventListener('pewpi.login.changed', (event) => {
      this.log('Login changed:', event.detail);
      this.trigger('loginChanged', event.detail);
    });

    // Wallet events
    window.addEventListener('pewpi.wallet.updated', (event) => {
      this.log('Wallet updated:', event.detail);
      this.trigger('walletUpdated', event.detail);
    });

    this.log('Subscribed to all pewpi events');
  }

  /**
   * Register a callback for a specific event type
   */
  on(eventType, callback) {
    if (!this.callbacks[eventType]) {
      console.warn(`[PewpiIntegrationListener] Unknown event type: ${eventType}`);
      return this;
    }

    this.callbacks[eventType].push(callback);
    this.log(`Registered callback for ${eventType}`);
    
    return this;
  }

  /**
   * Remove a callback for a specific event type
   */
  off(eventType, callback) {
    if (!this.callbacks[eventType]) {
      return this;
    }

    const index = this.callbacks[eventType].indexOf(callback);
    if (index > -1) {
      this.callbacks[eventType].splice(index, 1);
      this.log(`Removed callback for ${eventType}`);
    }
    
    return this;
  }

  /**
   * Trigger all callbacks for an event type
   */
  trigger(eventType, data) {
    if (!this.callbacks[eventType]) {
      return;
    }

    for (const callback of this.callbacks[eventType]) {
      try {
        callback(data);
      } catch (error) {
        console.error(`[PewpiIntegrationListener] Error in ${eventType} callback:`, error);
      }
    }
  }

  /**
   * Log message if debug is enabled
   */
  log(...args) {
    if (this.debug) {
      console.log('[PewpiIntegrationListener]', ...args);
    }
  }
}

/**
 * Example integration for other repositories
 */
class ExampleRepoIntegration {
  constructor() {
    this.listener = new PewpiIntegrationListener({ debug: true });
    this.localState = {
      tokens: [],
      user: null,
      balance: 0
    };
  }

  /**
   * Initialize integration
   */
  init() {
    this.listener.init();

    // Register callbacks for state synchronization
    this.listener
      .on('tokenCreated', (data) => this.handleTokenCreated(data))
      .on('tokenUpdated', (data) => this.handleTokenUpdated(data))
      .on('tokenDeleted', (data) => this.handleTokenDeleted(data))
      .on('loginChanged', (data) => this.handleLoginChanged(data))
      .on('walletUpdated', (data) => this.handleWalletUpdated(data))
      .on('tokensCleared', (data) => this.handleTokensCleared(data));

    console.log('[ExampleRepoIntegration] Initialized and listening for pewpi events');
  }

  /**
   * Handle token created
   */
  handleTokenCreated(token) {
    console.log('[ExampleRepoIntegration] Syncing new token to local state:', token);
    
    // Add token to local state
    this.localState.tokens.push(token);
    
    // Update UI or perform other actions
    this.updateTokenDisplay();
    
    // Optionally sync to backend
    this.syncToBackend('token_created', token);
  }

  /**
   * Handle token updated
   */
  handleTokenUpdated(data) {
    console.log('[ExampleRepoIntegration] Syncing token update to local state:', data);
    
    // Update token in local state
    const index = this.localState.tokens.findIndex(t => t.hash === data.hash);
    if (index >= 0) {
      this.localState.tokens[index] = { ...this.localState.tokens[index], ...data.updates };
      this.updateTokenDisplay();
    }
  }

  /**
   * Handle token deleted
   */
  handleTokenDeleted(data) {
    console.log('[ExampleRepoIntegration] Removing token from local state:', data);
    
    // Remove token from local state
    this.localState.tokens = this.localState.tokens.filter(t => t.hash !== data.hash);
    this.updateTokenDisplay();
  }

  /**
   * Handle login changed
   */
  handleLoginChanged(data) {
    console.log('[ExampleRepoIntegration] Login state changed:', data);
    
    if (data.authenticated) {
      this.localState.user = data.user;
      this.showUserInterface();
    } else {
      this.localState.user = null;
      this.showLoginPrompt();
    }
  }

  /**
   * Handle wallet updated
   */
  handleWalletUpdated(data) {
    console.log('[ExampleRepoIntegration] Wallet balance updated:', data);
    
    this.localState.balance = data.balance;
    this.updateBalanceDisplay();
  }

  /**
   * Handle tokens cleared
   */
  handleTokensCleared(data) {
    console.log('[ExampleRepoIntegration] All tokens cleared');
    
    this.localState.tokens = [];
    this.updateTokenDisplay();
  }

  /**
   * Update token display (implement based on repo UI)
   */
  updateTokenDisplay() {
    console.log('[ExampleRepoIntegration] Token count:', this.localState.tokens.length);
    // Update your repo's UI here
  }

  /**
   * Update balance display (implement based on repo UI)
   */
  updateBalanceDisplay() {
    console.log('[ExampleRepoIntegration] Balance:', this.localState.balance);
    // Update your repo's UI here
  }

  /**
   * Show user interface
   */
  showUserInterface() {
    console.log('[ExampleRepoIntegration] User logged in:', this.localState.user);
    // Show authenticated UI
  }

  /**
   * Show login prompt
   */
  showLoginPrompt() {
    console.log('[ExampleRepoIntegration] User logged out');
    // Show login UI
  }

  /**
   * Sync to backend (optional)
   */
  async syncToBackend(action, data) {
    // Example: Send data to your repo's backend
    try {
      const response = await fetch('/api/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action, data })
      });
      
      console.log('[ExampleRepoIntegration] Synced to backend:', action);
    } catch (error) {
      console.error('[ExampleRepoIntegration] Backend sync failed:', error);
    }
  }
}

// Usage example for banksy repository
class BanksyIntegration extends ExampleRepoIntegration {
  constructor() {
    super();
    console.log('[BanksyIntegration] Initializing banksy-specific integration');
  }

  updateTokenDisplay() {
    // Banksy-specific token display logic
    const banksyTokenList = document.getElementById('banksy-token-list');
    if (banksyTokenList) {
      banksyTokenList.innerHTML = this.localState.tokens
        .map(t => `<div class="banksy-token">${t.hash} - ${t.value}</div>`)
        .join('');
    }
  }
}

// Usage example for v repository
class VIntegration extends ExampleRepoIntegration {
  constructor() {
    super();
    console.log('[VIntegration] Initializing v-specific integration');
  }

  updateTokenDisplay() {
    // V-specific token display logic
    const vTokenCounter = document.getElementById('v-token-count');
    if (vTokenCounter) {
      vTokenCounter.textContent = this.localState.tokens.length;
    }
  }
}

// Usage example for infinity-brain-searc repository
class InfinityBrainSearchIntegration extends ExampleRepoIntegration {
  constructor() {
    super();
    console.log('[InfinityBrainSearchIntegration] Initializing infinity-brain-searc integration');
  }

  handleTokenCreated(token) {
    super.handleTokenCreated(token);
    // Index token for search
    this.indexTokenForSearch(token);
  }

  indexTokenForSearch(token) {
    console.log('[InfinityBrainSearchIntegration] Indexing token for search:', token.hash);
    // Add token to search index
  }
}

// Usage example for repo-dashboard-hub repository
class RepoDashboardHubIntegration extends ExampleRepoIntegration {
  constructor() {
    super();
    console.log('[RepoDashboardHubIntegration] Initializing repo-dashboard-hub integration');
  }

  updateTokenDisplay() {
    // Dashboard-specific display logic
    this.updateDashboardMetrics();
  }

  updateDashboardMetrics() {
    console.log('[RepoDashboardHubIntegration] Updating dashboard metrics');
    // Update dashboard charts and metrics
  }
}

// Export for use in different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    PewpiIntegrationListener,
    ExampleRepoIntegration,
    BanksyIntegration,
    VIntegration,
    InfinityBrainSearchIntegration,
    RepoDashboardHubIntegration
  };
}

if (typeof window !== 'undefined') {
  window.PewpiIntegrationListener = PewpiIntegrationListener;
  window.ExampleRepoIntegration = ExampleRepoIntegration;
  window.BanksyIntegration = BanksyIntegration;
  window.VIntegration = VIntegration;
  window.InfinityBrainSearchIntegration = InfinityBrainSearchIntegration;
  window.RepoDashboardHubIntegration = RepoDashboardHubIntegration;
}
