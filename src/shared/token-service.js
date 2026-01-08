/**
 * TokenService - Production Token Management with IndexedDB and localStorage fallback
 * Implements pewpi shared token/wallet system for cross-repo synchronization
 */

// Import Dexie from CDN or node_modules
// For browser: <script src="https://unpkg.com/dexie@latest/dist/dexie.js"></script>
// For node: const Dexie = require('dexie');

class TokenService {
  constructor(options = {}) {
    this.dbName = options.dbName || 'pewpi-tokens';
    this.version = options.version || 1;
    this.useLocalStorageFallback = options.useLocalStorageFallback !== false;
    this.db = null;
    this.initialized = false;
    this.storage = null; // 'indexeddb' or 'localstorage'
    this.autoTrackingEnabled = false;
  }

  /**
   * Initialize the database connection
   */
  async init() {
    if (this.initialized) return;

    try {
      // Try IndexedDB first
      if (typeof Dexie !== 'undefined') {
        await this.initIndexedDB();
        this.storage = 'indexeddb';
        console.log('[TokenService] Initialized with IndexedDB');
      } else {
        throw new Error('Dexie not available');
      }
    } catch (error) {
      console.warn('[TokenService] IndexedDB initialization failed:', error);
      
      if (this.useLocalStorageFallback) {
        await this.initLocalStorage();
        this.storage = 'localstorage';
        console.log('[TokenService] Initialized with localStorage fallback');
      } else {
        throw new Error('Failed to initialize TokenService storage');
      }
    }

    this.initialized = true;
    this.emitEvent('pewpi.tokenservice.initialized', { storage: this.storage });
  }

  /**
   * Initialize IndexedDB using Dexie
   */
  async initIndexedDB() {
    this.db = new Dexie(this.dbName);
    
    this.db.version(this.version).stores({
      tokens: '++id, hash, type, value, created_at, updated_at, owner',
      wallets: '++id, address, balance, updated_at',
      events: '++id, type, timestamp, data'
    });

    await this.db.open();
  }

  /**
   * Initialize localStorage fallback
   */
  async initLocalStorage() {
    if (typeof localStorage === 'undefined') {
      throw new Error('localStorage not available');
    }
    
    // Initialize storage keys
    const keys = ['tokens', 'wallets', 'events'];
    for (const key of keys) {
      if (!localStorage.getItem(`${this.dbName}_${key}`)) {
        localStorage.setItem(`${this.dbName}_${key}`, JSON.stringify([]));
      }
    }
  }

  /**
   * Create a new token
   */
  async createToken(tokenData) {
    await this.ensureInitialized();

    const token = {
      hash: tokenData.hash || this.generateHash(tokenData),
      type: tokenData.type || 'standard',
      value: tokenData.value || 0,
      metadata: tokenData.metadata || {},
      owner: tokenData.owner || 'anonymous',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      ...tokenData
    };

    let tokenId;
    if (this.storage === 'indexeddb') {
      tokenId = await this.db.tokens.add(token);
      token.id = tokenId;
    } else {
      const tokens = this.getLocalStorageData('tokens');
      token.id = tokens.length > 0 ? Math.max(...tokens.map(t => t.id || 0)) + 1 : 1;
      tokens.push(token);
      this.setLocalStorageData('tokens', tokens);
      tokenId = token.id;
    }

    // Emit token created event
    this.emitEvent('pewpi.token.created', token);
    
    // Log event
    await this.logEvent('token_created', token);

    return token;
  }

  /**
   * Get all tokens
   */
  async getAll(filter = {}) {
    await this.ensureInitialized();

    if (this.storage === 'indexeddb') {
      let collection = this.db.tokens;
      
      // Apply filters
      if (filter.type) {
        collection = collection.where('type').equals(filter.type);
      }
      if (filter.owner) {
        collection = collection.where('owner').equals(filter.owner);
      }
      
      return await collection.toArray();
    } else {
      let tokens = this.getLocalStorageData('tokens');
      
      // Apply filters
      if (filter.type) {
        tokens = tokens.filter(t => t.type === filter.type);
      }
      if (filter.owner) {
        tokens = tokens.filter(t => t.owner === filter.owner);
      }
      
      return tokens;
    }
  }

  /**
   * Get token by hash
   */
  async getByHash(hash) {
    await this.ensureInitialized();

    if (this.storage === 'indexeddb') {
      return await this.db.tokens.where('hash').equals(hash).first();
    } else {
      const tokens = this.getLocalStorageData('tokens');
      return tokens.find(t => t.hash === hash);
    }
  }

  /**
   * Update token
   */
  async updateToken(hash, updates) {
    await this.ensureInitialized();

    updates.updated_at = new Date().toISOString();

    if (this.storage === 'indexeddb') {
      const count = await this.db.tokens.where('hash').equals(hash).modify(updates);
      if (count === 0) throw new Error('Token not found');
    } else {
      const tokens = this.getLocalStorageData('tokens');
      const index = tokens.findIndex(t => t.hash === hash);
      if (index === -1) throw new Error('Token not found');
      tokens[index] = { ...tokens[index], ...updates };
      this.setLocalStorageData('tokens', tokens);
    }

    this.emitEvent('pewpi.token.updated', { hash, updates });
    await this.logEvent('token_updated', { hash, updates });
  }

  /**
   * Delete token by hash
   */
  async deleteToken(hash) {
    await this.ensureInitialized();

    if (this.storage === 'indexeddb') {
      await this.db.tokens.where('hash').equals(hash).delete();
    } else {
      const tokens = this.getLocalStorageData('tokens');
      const filtered = tokens.filter(t => t.hash !== hash);
      this.setLocalStorageData('tokens', filtered);
    }

    this.emitEvent('pewpi.token.deleted', { hash });
    await this.logEvent('token_deleted', { hash });
  }

  /**
   * Clear all tokens
   */
  async clearAll() {
    await this.ensureInitialized();

    if (this.storage === 'indexeddb') {
      await this.db.tokens.clear();
    } else {
      this.setLocalStorageData('tokens', []);
    }

    this.emitEvent('pewpi.tokens.cleared', {});
    await this.logEvent('tokens_cleared', {});
  }

  /**
   * Initialize auto-tracking of token changes
   */
  async initAutoTracking(callback) {
    await this.ensureInitialized();
    this.autoTrackingEnabled = true;

    // Listen for custom events
    window.addEventListener('pewpi.token.created', (event) => {
      if (callback) callback('created', event.detail);
    });

    window.addEventListener('pewpi.token.updated', (event) => {
      if (callback) callback('updated', event.detail);
    });

    window.addEventListener('pewpi.token.deleted', (event) => {
      if (callback) callback('deleted', event.detail);
    });

    console.log('[TokenService] Auto-tracking enabled');
  }

  /**
   * Get wallet balance
   */
  async getBalance(address = 'default') {
    await this.ensureInitialized();

    if (this.storage === 'indexeddb') {
      const wallet = await this.db.wallets.where('address').equals(address).first();
      return wallet ? wallet.balance : 0;
    } else {
      const wallets = this.getLocalStorageData('wallets');
      const wallet = wallets.find(w => w.address === address);
      return wallet ? wallet.balance : 0;
    }
  }

  /**
   * Update wallet balance
   */
  async updateBalance(address = 'default', balance) {
    await this.ensureInitialized();

    const walletData = {
      address,
      balance,
      updated_at: new Date().toISOString()
    };

    if (this.storage === 'indexeddb') {
      const existing = await this.db.wallets.where('address').equals(address).first();
      if (existing) {
        await this.db.wallets.update(existing.id, walletData);
      } else {
        await this.db.wallets.add(walletData);
      }
    } else {
      const wallets = this.getLocalStorageData('wallets');
      const index = wallets.findIndex(w => w.address === address);
      if (index >= 0) {
        wallets[index] = { ...wallets[index], ...walletData };
      } else {
        walletData.id = wallets.length > 0 ? Math.max(...wallets.map(w => w.id || 0)) + 1 : 1;
        wallets.push(walletData);
      }
      this.setLocalStorageData('wallets', wallets);
    }

    this.emitEvent('pewpi.wallet.updated', walletData);
  }

  /**
   * Log an event
   */
  async logEvent(type, data) {
    await this.ensureInitialized();

    const event = {
      type,
      timestamp: new Date().toISOString(),
      data
    };

    if (this.storage === 'indexeddb') {
      await this.db.events.add(event);
    } else {
      const events = this.getLocalStorageData('events');
      event.id = events.length > 0 ? Math.max(...events.map(e => e.id || 0)) + 1 : 1;
      events.push(event);
      // Keep only last 1000 events
      if (events.length > 1000) {
        events.splice(0, events.length - 1000);
      }
      this.setLocalStorageData('events', events);
    }
  }

  /**
   * Get events log
   */
  async getEvents(filter = {}) {
    await this.ensureInitialized();

    if (this.storage === 'indexeddb') {
      let collection = this.db.events;
      if (filter.type) {
        collection = collection.where('type').equals(filter.type);
      }
      return await collection.reverse().limit(filter.limit || 100).toArray();
    } else {
      let events = this.getLocalStorageData('events');
      if (filter.type) {
        events = events.filter(e => e.type === filter.type);
      }
      return events.slice(-1 * (filter.limit || 100)).reverse();
    }
  }

  /**
   * Generate hash for token
   */
  generateHash(data) {
    const str = JSON.stringify(data) + Date.now();
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(16, '0');
  }

  /**
   * Emit custom event
   */
  emitEvent(eventName, detail) {
    if (typeof window !== 'undefined' && window.dispatchEvent) {
      const event = new CustomEvent(eventName, { detail });
      window.dispatchEvent(event);
    }
  }

  /**
   * Ensure service is initialized
   */
  async ensureInitialized() {
    if (!this.initialized) {
      await this.init();
    }
  }

  /**
   * Get data from localStorage
   */
  getLocalStorageData(key) {
    try {
      const data = localStorage.getItem(`${this.dbName}_${key}`);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error(`[TokenService] Failed to read ${key} from localStorage:`, error);
      return [];
    }
  }

  /**
   * Set data in localStorage
   */
  setLocalStorageData(key, data) {
    try {
      localStorage.setItem(`${this.dbName}_${key}`, JSON.stringify(data));
    } catch (error) {
      console.error(`[TokenService] Failed to write ${key} to localStorage:`, error);
    }
  }

  /**
   * Export all data (for migration)
   */
  async exportAll() {
    await this.ensureInitialized();

    return {
      tokens: await this.getAll(),
      wallets: this.storage === 'indexeddb' 
        ? await this.db.wallets.toArray() 
        : this.getLocalStorageData('wallets'),
      events: await this.getEvents({ limit: 1000 }),
      metadata: {
        storage: this.storage,
        exported_at: new Date().toISOString()
      }
    };
  }

  /**
   * Import data (for migration)
   */
  async importAll(data) {
    await this.ensureInitialized();

    if (data.tokens) {
      for (const token of data.tokens) {
        await this.createToken(token);
      }
    }

    if (data.wallets) {
      for (const wallet of data.wallets) {
        await this.updateBalance(wallet.address, wallet.balance);
      }
    }

    console.log('[TokenService] Import completed');
  }

  /**
   * Get storage info
   */
  async getStorageInfo() {
    await this.ensureInitialized();

    const info = {
      storage: this.storage,
      dbName: this.dbName,
      initialized: this.initialized,
      autoTracking: this.autoTrackingEnabled
    };

    if (this.storage === 'indexeddb') {
      info.tokenCount = await this.db.tokens.count();
      info.walletCount = await this.db.wallets.count();
      info.eventCount = await this.db.events.count();
    } else {
      info.tokenCount = this.getLocalStorageData('tokens').length;
      info.walletCount = this.getLocalStorageData('wallets').length;
      info.eventCount = this.getLocalStorageData('events').length;
    }

    return info;
  }

  /**
   * Close database connection
   */
  async close() {
    if (this.db && this.storage === 'indexeddb') {
      await this.db.close();
    }
    this.initialized = false;
  }
}

// Export for use in different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TokenService;
}
if (typeof window !== 'undefined') {
  window.TokenService = TokenService;
}
