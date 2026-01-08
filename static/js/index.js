/**
 * Main Index JavaScript for Infinity Research Portal
 * Handles article loading, filtering, and display
 */

class ArticleReader {
  constructor() {
    this.articles = [];
    this.filteredArticles = [];
    this.currentFilter = 'all';
    this.initialized = false;
  }

  /**
   * Initialize the article reader
   */
  async init() {
    if (this.initialized) return;

    await this.loadArticles();
    this.setupEventListeners();
    this.renderArticles();
    this.initialized = true;
  }

  /**
   * Load articles from research_index.json
   */
  async loadArticles() {
    try {
      const response = await fetch('/research_index.json');
      const data = await response.json();
      
      this.articles = data || [];
      this.filteredArticles = [...this.articles];
      
      console.log(`[ArticleReader] Loaded ${this.articles.length} articles`);
    } catch (error) {
      console.error('[ArticleReader] Failed to load articles:', error);
      this.articles = [];
      this.filteredArticles = [];
    }
  }

  /**
   * Set up event listeners
   */
  setupEventListeners() {
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const role = e.target.dataset.role;
        this.filterArticles(role);
        
        // Update active state
        filterButtons.forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
      });
    });

    // Chat terminal toggle
    const chatToggleBtn = document.getElementById('chat-toggle-btn');
    if (chatToggleBtn) {
      chatToggleBtn.addEventListener('click', () => {
        if (window.authManager && window.authManager.authenticated) {
          if (window.chatTerminal) {
            window.chatTerminal.toggle();
          }
        } else {
          alert('Please log in to access the chat terminal.');
        }
      });
    }
  }

  /**
   * Filter articles by role
   */
  filterArticles(role) {
    this.currentFilter = role;
    
    if (role === 'all') {
      this.filteredArticles = [...this.articles];
    } else {
      this.filteredArticles = this.articles.filter(
        article => article.role === role
      );
    }
    
    this.renderArticles();
  }

  /**
   * Render articles to the page
   */
  renderArticles() {
    const container = document.getElementById('articles-container');
    if (!container) return;

    if (this.filteredArticles.length === 0) {
      container.innerHTML = `
        <div class="no-articles">
          <p>No articles found.</p>
        </div>
      `;
      return;
    }

    const articlesHtml = this.filteredArticles.map(article => 
      this.renderArticleCard(article)
    ).join('');

    container.innerHTML = articlesHtml;
  }

  /**
   * Render a single article card
   */
  renderArticleCard(article) {
    const roleColors = {
      engineering: '#22c55e',
      ceo: '#f97316',
      import: '#3b82f6',
      investigate: '#ec4899',
      routes: '#ef4444',
      data: '#eab308',
      assimilation: '#a855f7'
    };

    const color = roleColors[article.role] || '#808080';
    const hash = article.hash || '';
    const title = this.escapeHtml(article.title || 'Untitled');
    const timestamp = this.formatTimestamp(article.timestamp);
    const value = this.formatValue(article.value);
    const url = article.url || '#';

    return `
      <div class="article-card" style="border-left: 4px solid ${color};">
        <div class="article-header">
          <span class="article-role" style="color: ${color};">
            ${article.role}
          </span>
          <span class="article-timestamp">${timestamp}</span>
        </div>
        <h3 class="article-title">
          <a href="${url}" target="_blank">${title}</a>
        </h3>
        <div class="article-meta">
          <span class="article-hash" title="${hash}">
            🔑 ${hash.substring(0, 12)}...
          </span>
          ${value ? `<span class="article-value">💎 ${value}</span>` : ''}
        </div>
      </div>
    `;
  }

  /**
   * Format timestamp
   */
  formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      return 'Unknown';
    }
  }

  /**
   * Format token value
   */
  formatValue(value) {
    if (!value) return '';
    
    if (typeof value === 'string') {
      return value;
    }
    
    if (value >= 1_000_000_000) {
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
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Refresh articles
   */
  async refresh() {
    await this.loadArticles();
    this.filterArticles(this.currentFilter);
  }
}

// Initialize on page load
let articleReader = null;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    articleReader = new ArticleReader();
    articleReader.init();
    
    // Initialize chat terminal if container exists
    if (document.getElementById('chat-terminal')) {
      window.chatTerminal.init();
    }
  });
} else {
  articleReader = new ArticleReader();
  articleReader.init();
  
  // Initialize chat terminal if container exists
  if (document.getElementById('chat-terminal')) {
    window.chatTerminal.init();
  }
}

// Export for use in other scripts
window.articleReader = articleReader;

/**
 * Initialize Pewpi Shared Services (Token, Auth, Wallet)
 * Wrapped in try-catch to ensure backward compatibility
 * 
 * NOTE: The pewpi-shared services are ES modules and need to be loaded via script tags
 * or dynamic imports in your HTML. This initialization checks if they're available globally.
 * 
 * To use pewpi-shared services in your pages, add to HTML:
 * <script type="module">
 *   import { TokenService } from './src/pewpi-shared/token-service.js';
 *   import { LoginComponent } from './src/pewpi-shared/auth/login-component.js';
 *   import { IntegrationListener } from './src/pewpi-shared/integration-listener.js';
 *   
 *   window.TokenService = TokenService;
 *   window.LoginComponent = LoginComponent;
 *   window.IntegrationListener = IntegrationListener;
 * </script>
 * 
 * See demo.html for a complete working example.
 */
(async function initPewpiSharedServices() {
  try {
    // Check if TokenService is available globally (from page script tags)
    if (typeof TokenService !== 'undefined') {
      console.log('[Pewpi Shared] TokenService available, initializing auto-tracking...');
      const tokenService = new TokenService();
      if (tokenService.initAutoTracking) {
        tokenService.initAutoTracking();
        console.log('[Pewpi Shared] Token auto-tracking initialized');
      }
      window.pewpiTokenService = tokenService;
    } else {
      console.log('[Pewpi Shared] TokenService not loaded. To use pewpi-shared services, see src/pewpi-shared/INTEGRATION.md');
    }
    
    // Check if LoginComponent is available globally
    if (typeof LoginComponent !== 'undefined') {
      console.log('[Pewpi Shared] LoginComponent available, restoring session...');
      const loginComponent = new LoginComponent({ devMode: true });
      // Session is automatically restored in constructor via loadUserFromStorage()
      console.log('[Pewpi Shared] Auth session restored');
      window.pewpiLoginComponent = loginComponent;
    }
    
    // Initialize integration listener for cross-repo events
    if (typeof IntegrationListener !== 'undefined') {
      console.log('[Pewpi Shared] IntegrationListener available, starting event listeners...');
      const listener = new IntegrationListener({
        onTokenCreated: (token) => {
          console.log('[Pewpi Integration] Token created:', token);
          // Optional: Update UI or trigger other actions
        },
        onLoginChanged: (data) => {
          console.log('[Pewpi Integration] Login changed:', data);
          // Optional: Update UI or trigger other actions
        },
        debug: true
      });
      listener.start();
      window.pewpiIntegrationListener = listener;
      console.log('[Pewpi Shared] Integration listener started - listening for pewpi.token.created, pewpi.token.updated, pewpi.login.changed');
    }
    
  } catch (error) {
    console.warn('[Pewpi Shared] Failed to initialize shared services (non-critical):', error);
    // Non-critical error - app continues to work normally
  }
})();
