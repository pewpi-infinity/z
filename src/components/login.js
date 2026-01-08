/**
 * Production Login Component
 * Supports magic-link (passwordless) authentication and optional GitHub OAuth
 * Works in dev-mode without SMTP for local testing
 */

class LoginManager {
  constructor(options = {}) {
    this.devMode = options.devMode !== false; // Default to dev mode
    this.apiBase = options.apiBase || '';
    this.onLoginSuccess = options.onLoginSuccess || null;
    this.onLogoutSuccess = options.onLogoutSuccess || null;
    this.user = null;
    this.authenticated = false;
  }

  /**
   * Initialize login manager
   */
  async init() {
    // Check if user is already authenticated
    await this.checkAuthStatus();
    
    // Set up event listeners
    this.setupEventListeners();
    
    console.log('[LoginManager] Initialized in', this.devMode ? 'dev' : 'production', 'mode');
  }

  /**
   * Set up event listeners
   */
  setupEventListeners() {
    // Magic link login form
    const magicLinkForm = document.getElementById('magic-link-form');
    if (magicLinkForm) {
      magicLinkForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('magic-link-email').value;
        this.sendMagicLink(email);
      });
    }

    // GitHub OAuth button
    const githubLoginBtn = document.getElementById('github-login-btn');
    if (githubLoginBtn) {
      githubLoginBtn.addEventListener('click', () => this.loginWithGitHub());
    }

    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => this.logout());
    }

    // Dev mode magic link verification
    if (this.devMode) {
      const devVerifyBtn = document.getElementById('dev-verify-btn');
      if (devVerifyBtn) {
        devVerifyBtn.addEventListener('click', () => {
          const token = document.getElementById('dev-token-input').value;
          this.verifyMagicLinkDev(token);
        });
      }
    }
  }

  /**
   * Send magic link (passwordless authentication)
   */
  async sendMagicLink(email) {
    if (!email || !this.isValidEmail(email)) {
      this.showError('Please enter a valid email address');
      return;
    }

    try {
      const response = await fetch(`${this.apiBase}/auth/magic-link`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      });

      const data = await response.json();

      if (data.success) {
        if (this.devMode && data.devToken) {
          // In dev mode, show the token directly
          this.showDevMagicLink(email, data.devToken);
        } else {
          this.showSuccess(`Magic link sent to ${email}. Please check your inbox.`);
        }
      } else {
        this.showError(data.error || 'Failed to send magic link');
      }
    } catch (error) {
      console.error('[LoginManager] Magic link error:', error);
      this.showError('Failed to send magic link. Please try again.');
    }
  }

  /**
   * Verify magic link token
   */
  async verifyMagicLink(token) {
    try {
      const response = await fetch(`${this.apiBase}/auth/magic-link/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ token })
      });

      const data = await response.json();

      if (data.success) {
        this.user = data.user;
        this.authenticated = true;
        this.updateUI(true);
        this.emitEvent('pewpi.login.changed', { authenticated: true, user: this.user });
        
        if (this.onLoginSuccess) {
          this.onLoginSuccess(this.user);
        }
        
        this.showSuccess('Login successful!');
      } else {
        this.showError(data.error || 'Invalid or expired magic link');
      }
    } catch (error) {
      console.error('[LoginManager] Verification error:', error);
      this.showError('Failed to verify magic link. Please try again.');
    }
  }

  /**
   * Dev mode: verify magic link token
   */
  async verifyMagicLinkDev(token) {
    await this.verifyMagicLink(token);
  }

  /**
   * Login with GitHub OAuth
   */
  loginWithGitHub() {
    window.location.href = `${this.apiBase}/auth/github`;
  }

  /**
   * Check authentication status
   */
  async checkAuthStatus() {
    try {
      const response = await fetch(`${this.apiBase}/auth/status`, {
        method: 'GET',
        credentials: 'include'
      });

      const data = await response.json();

      if (data.success && data.authenticated) {
        this.user = {
          email: data.email,
          username: data.username,
          provider: data.provider,
          tokenCount: data.token_count || 0
        };
        this.authenticated = true;
        this.updateUI(true);
        this.emitEvent('pewpi.login.changed', { authenticated: true, user: this.user });
      } else {
        this.user = null;
        this.authenticated = false;
        this.updateUI(false);
      }
    } catch (error) {
      console.error('[LoginManager] Status check failed:', error);
      this.user = null;
      this.authenticated = false;
      this.updateUI(false);
    }
  }

  /**
   * Logout user
   */
  async logout() {
    try {
      const response = await fetch(`${this.apiBase}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });

      const data = await response.json();

      if (data.success) {
        this.user = null;
        this.authenticated = false;
        this.updateUI(false);
        this.emitEvent('pewpi.login.changed', { authenticated: false, user: null });
        
        if (this.onLogoutSuccess) {
          this.onLogoutSuccess();
        }
        
        this.showSuccess('Logged out successfully');
      } else {
        this.showError(data.error || 'Logout failed');
      }
    } catch (error) {
      console.error('[LoginManager] Logout error:', error);
      this.showError('Logout failed. Please try again.');
    }
  }

  /**
   * Update UI based on authentication status
   */
  updateUI(authenticated) {
    const loginSection = document.getElementById('login-section');
    const userSection = document.getElementById('user-section');
    const usernameDisplay = document.getElementById('username-display');
    const emailDisplay = document.getElementById('email-display');
    const tokenCountDisplay = document.getElementById('token-count-display');

    if (authenticated && this.user) {
      // Show authenticated UI
      if (loginSection) loginSection.style.display = 'none';
      if (userSection) userSection.style.display = 'block';
      
      if (usernameDisplay) {
        usernameDisplay.textContent = this.user.username || this.user.email;
      }
      
      if (emailDisplay) {
        emailDisplay.textContent = this.user.email || '';
      }
      
      if (tokenCountDisplay) {
        tokenCountDisplay.textContent = (this.user.tokenCount || 0).toLocaleString();
      }
    } else {
      // Show login UI
      if (loginSection) loginSection.style.display = 'block';
      if (userSection) userSection.style.display = 'none';
    }
  }

  /**
   * Show dev mode magic link
   */
  showDevMagicLink(email, token) {
    const devLinkSection = document.getElementById('dev-magic-link-section');
    if (devLinkSection) {
      devLinkSection.style.display = 'block';
      const tokenInput = document.getElementById('dev-token-input');
      if (tokenInput) {
        tokenInput.value = token;
      }
    }
    
    this.showSuccess(`DEV MODE: Magic link token for ${email}: ${token}`);
  }

  /**
   * Validate email format
   */
  isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  /**
   * Show error message
   */
  showError(message) {
    const errorDiv = document.getElementById('auth-error');
    if (errorDiv) {
      errorDiv.textContent = message;
      errorDiv.style.display = 'block';
      setTimeout(() => {
        errorDiv.style.display = 'none';
      }, 5000);
    } else {
      console.error('[LoginManager]', message);
      alert(message);
    }
  }

  /**
   * Show success message
   */
  showSuccess(message) {
    const successDiv = document.getElementById('auth-success');
    if (successDiv) {
      successDiv.textContent = message;
      successDiv.style.display = 'block';
      setTimeout(() => {
        successDiv.style.display = 'none';
      }, 5000);
    } else {
      console.log('[LoginManager]', message);
    }
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
   * Get current user
   */
  getUser() {
    return this.user;
  }

  /**
   * Check if authenticated
   */
  isAuthenticated() {
    return this.authenticated;
  }

  /**
   * Require authentication for an action
   */
  requireAuth() {
    if (!this.authenticated) {
      this.showError('Please log in to perform this action');
      return false;
    }
    return true;
  }
}

// Export for use in different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LoginManager;
}
if (typeof window !== 'undefined') {
  window.LoginManager = LoginManager;
}
