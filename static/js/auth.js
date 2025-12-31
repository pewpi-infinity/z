/**
 * Authentication Handler for Infinity Research Portal
 * Handles GitHub OAuth login, session management, and user state
 */

class AuthManager {
  constructor() {
    this.user = null;
    this.authenticated = false;
    this.checkInterval = null;
  }

  /**
   * Initialize authentication system
   */
  async init() {
    // Check if user is already authenticated
    await this.checkStatus();
    
    // Set up periodic status checks (every 5 minutes)
    this.checkInterval = setInterval(() => this.checkStatus(), 300000);
    
    // Set up event listeners
    this.setupEventListeners();
  }

  /**
   * Set up event listeners for auth UI
   */
  setupEventListeners() {
    // Login button
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
      loginBtn.addEventListener('click', () => this.login());
    }

    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => this.logout());
    }
  }

  /**
   * Check current authentication status
   */
  async checkStatus() {
    try {
      const response = await fetch('/auth/status', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success && data.authenticated) {
        this.user = {
          username: data.username,
          tokenCount: data.token_count,
          tokensCreated: data.tokens_created,
          megaHashes: data.mega_hashes,
          lastLogin: data.last_login,
          createdAt: data.created_at
        };
        this.authenticated = true;
        this.updateUI(true);
      } else {
        this.user = null;
        this.authenticated = false;
        this.updateUI(false);
      }

      return this.authenticated;
    } catch (error) {
      console.error('[Auth] Status check failed:', error);
      this.user = null;
      this.authenticated = false;
      this.updateUI(false);
      return false;
    }
  }

  /**
   * Initiate login flow
   */
  login() {
    // Redirect to OAuth initiation endpoint
    window.location.href = '/auth/github';
  }

  /**
   * Logout current user
   */
  async logout() {
    try {
      const response = await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Accept': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        this.user = null;
        this.authenticated = false;
        this.updateUI(false);
        
        // Redirect to home page
        window.location.href = '/';
      } else {
        console.error('[Auth] Logout failed:', data.error);
        alert('Logout failed: ' + data.error);
      }
    } catch (error) {
      console.error('[Auth] Logout error:', error);
      alert('Logout error: ' + error.message);
    }
  }

  /**
   * Update UI based on authentication status
   */
  updateUI(authenticated) {
    const loginSection = document.getElementById('login-section');
    const userSection = document.getElementById('user-section');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const usernameDisplay = document.getElementById('username-display');
    const tokenCountDisplay = document.getElementById('token-count-display');

    if (authenticated && this.user) {
      // Show authenticated UI
      if (loginSection) loginSection.style.display = 'none';
      if (userSection) userSection.style.display = 'block';
      
      if (usernameDisplay) {
        usernameDisplay.textContent = this.user.username;
      }
      
      if (tokenCountDisplay) {
        tokenCountDisplay.textContent = this.user.tokenCount.toLocaleString();
      }
    } else {
      // Show login UI
      if (loginSection) loginSection.style.display = 'block';
      if (userSection) userSection.style.display = 'none';
    }
  }

  /**
   * Update token count after token creation
   */
  async updateTokenCount(tokenHash, tokenValue, action = 'token_build') {
    if (!this.authenticated) {
      throw new Error('Must be authenticated to update token count');
    }

    try {
      const response = await fetch('/api/user/update-tokens', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          token_hash: tokenHash,
          token_value: tokenValue,
          action: action
        })
      });

      const data = await response.json();

      if (data.success) {
        this.user.tokenCount = data.token_count;
        this.updateUI(true);
        return data;
      } else {
        console.error('[Auth] Token update failed:', data.error);
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('[Auth] Token update error:', error);
      throw error;
    }
  }

  /**
   * Check if user is authenticated (for protecting actions)
   */
  requireAuth() {
    if (!this.authenticated) {
      alert('Please log in to perform this action.');
      return false;
    }
    return true;
  }

  /**
   * Get user commit history
   */
  async getUserCommits() {
    if (!this.authenticated) {
      throw new Error('Must be authenticated to get commit history');
    }

    try {
      const response = await fetch('/api/user/commits', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        return data.commits;
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('[Auth] Failed to get commits:', error);
      throw error;
    }
  }

  /**
   * Clean up on page unload
   */
  destroy() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }
}

// Create global auth manager instance
const authManager = new AuthManager();

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => authManager.init());
} else {
  authManager.init();
}

// Clean up on page unload
window.addEventListener('beforeunload', () => authManager.destroy());

// Export for use in other scripts
window.authManager = authManager;
