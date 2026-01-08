# Integration Guide

This document explains how to integrate the pewpi shared token/wallet system into other repositories (banksy, v, infinity-brain-searc, repo-dashboard-hub, etc.).

## Overview

The pewpi token/wallet system provides:
- **TokenService**: IndexedDB-backed token storage with localStorage fallback
- **LoginManager**: Passwordless magic-link authentication + optional GitHub OAuth
- **WalletUI**: Balance display, token list, and live token feed
- **Integration Events**: Cross-window event system for state synchronization
- **ClientModel**: Mongoose-style front-end models
- **Crypto Helpers**: AES-GCM encryption and ECDH key exchange for P2P

## Quick Start

### 1. Add Dependencies

Add to your `package.json`:

```json
{
  "dependencies": {
    "dexie": "^3.2.4"
  }
}
```

Or include via CDN:

```html
<script src="https://unpkg.com/dexie@latest/dist/dexie.js"></script>
```

### 2. Copy Shared Files

Copy these files to your repository:

```bash
# From z repository to your repo
cp -r z/src/shared/ your-repo/src/shared/
cp -r z/src/components/ your-repo/src/components/
```

### 3. Include in Your HTML

```html
<!-- Theme CSS -->
<link rel="stylesheet" href="/src/shared/theme.css">

<!-- Core Services -->
<script src="https://unpkg.com/dexie@latest/dist/dexie.js"></script>
<script src="/src/shared/token-service.js"></script>
<script src="/src/shared/client-model.js"></script>
<script src="/src/shared/integration-listener.js"></script>

<!-- Components -->
<script src="/src/components/login.js"></script>
<script src="/src/components/wallet.js"></script>
```

### 4. Initialize Services

```javascript
// Initialize TokenService
const tokenService = new TokenService({
  dbName: 'your-app-tokens',
  useLocalStorageFallback: true
});
await tokenService.init();

// Initialize LoginManager
const loginManager = new LoginManager({
  devMode: process.env.NODE_ENV === 'development',
  apiBase: '/api'  // Your API base URL
});
await loginManager.init();

// Initialize WalletUI (optional)
const walletUI = new WalletUI(tokenService, {
  containerId: 'wallet-container',
  feedEnabled: true,
  refreshInterval: 5000
});
await walletUI.init();

// Initialize Integration Listener
const listener = new PewpiIntegrationListener({ debug: true });
listener.init();
```

## Repository-Specific Integrations

### Banksy Repository

Banksy is an art-focused repository. Here's how to integrate:

```javascript
class BanksyIntegration {
  constructor() {
    this.tokenService = new TokenService({ dbName: 'banksy-tokens' });
    this.listener = new PewpiIntegrationListener();
  }

  async init() {
    await this.tokenService.init();
    this.listener.init();
    
    // Subscribe to token events for art pieces
    this.listener.on('tokenCreated', (token) => {
      this.addArtPieceToken(token);
    });
    
    // Subscribe to login events
    this.listener.on('loginChanged', (data) => {
      if (data.authenticated) {
        this.loadUserArtCollection();
      }
    });
  }

  async addArtPieceToken(token) {
    // Add token to Banksy's art collection UI
    const artGrid = document.getElementById('art-grid');
    if (artGrid) {
      const artCard = this.createArtCard(token);
      artGrid.appendChild(artCard);
    }
  }

  createArtCard(token) {
    const card = document.createElement('div');
    card.className = 'art-card';
    card.innerHTML = `
      <div class="art-image" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"></div>
      <h3>${token.hash.substring(0, 8)}</h3>
      <p>Value: ${this.formatValue(token.value)}</p>
    `;
    return card;
  }

  formatValue(value) {
    return value >= 1000000 ? `$${(value / 1000000).toFixed(2)}M` : `$${value.toLocaleString()}`;
  }

  async loadUserArtCollection() {
    const tokens = await this.tokenService.getAll({ type: 'art' });
    // Display user's art collection
    console.log('User art collection:', tokens);
  }
}

// Initialize
const banksy = new BanksyIntegration();
banksy.init();
```

### V Repository

V is a minimalist repository. Simple integration:

```javascript
class VIntegration {
  constructor() {
    this.tokenService = new TokenService({ dbName: 'v-tokens' });
    this.listener = new PewpiIntegrationListener();
  }

  async init() {
    await this.tokenService.init();
    this.listener.init();
    
    this.listener.on('tokenCreated', () => {
      this.updateTokenCounter();
    });
  }

  async updateTokenCounter() {
    const tokens = await this.tokenService.getAll();
    const counter = document.getElementById('token-counter');
    if (counter) {
      counter.textContent = tokens.length;
    }
  }
}

// Initialize
const v = new VIntegration();
v.init();
```

### Infinity Brain Search Repository

Advanced integration with search indexing:

```javascript
class InfinityBrainSearchIntegration {
  constructor() {
    this.tokenService = new TokenService({ dbName: 'ibs-tokens' });
    this.searchIndex = [];
    this.listener = new PewpiIntegrationListener();
  }

  async init() {
    await this.tokenService.init();
    this.listener.init();
    
    // Index existing tokens
    await this.rebuildSearchIndex();
    
    // Subscribe to token events
    this.listener.on('tokenCreated', (token) => {
      this.indexToken(token);
    });
    
    this.listener.on('tokenUpdated', (data) => {
      this.reindexToken(data.hash);
    });
  }

  async rebuildSearchIndex() {
    const tokens = await this.tokenService.getAll();
    this.searchIndex = tokens.map(token => ({
      id: token.hash,
      content: JSON.stringify(token).toLowerCase(),
      token: token
    }));
    console.log('Search index rebuilt:', this.searchIndex.length, 'tokens');
  }

  indexToken(token) {
    this.searchIndex.push({
      id: token.hash,
      content: JSON.stringify(token).toLowerCase(),
      token: token
    });
  }

  async reindexToken(hash) {
    const token = await this.tokenService.getByHash(hash);
    if (token) {
      const index = this.searchIndex.findIndex(item => item.id === hash);
      if (index >= 0) {
        this.searchIndex[index] = {
          id: token.hash,
          content: JSON.stringify(token).toLowerCase(),
          token: token
        };
      }
    }
  }

  search(query) {
    const lowerQuery = query.toLowerCase();
    return this.searchIndex
      .filter(item => item.content.includes(lowerQuery))
      .map(item => item.token);
  }
}

// Initialize
const ibs = new InfinityBrainSearchIntegration();
ibs.init();
```

### Repo Dashboard Hub

Dashboard with metrics and charts:

```javascript
class RepoDashboardHubIntegration {
  constructor() {
    this.tokenService = new TokenService({ dbName: 'dashboard-tokens' });
    this.listener = new PewpiIntegrationListener();
    this.metrics = {
      totalTokens: 0,
      totalValue: 0,
      tokensToday: 0
    };
  }

  async init() {
    await this.tokenService.init();
    this.listener.init();
    
    // Initial metrics calculation
    await this.updateMetrics();
    
    // Subscribe to events
    this.listener.on('tokenCreated', () => {
      this.updateMetrics();
      this.animateMetricChange('totalTokens');
    });
    
    this.listener.on('walletUpdated', (data) => {
      this.updateBalanceChart(data.balance);
    });
    
    // Refresh metrics every 30 seconds
    setInterval(() => this.updateMetrics(), 30000);
  }

  async updateMetrics() {
    const tokens = await this.tokenService.getAll();
    const today = new Date().toDateString();
    
    this.metrics.totalTokens = tokens.length;
    this.metrics.totalValue = tokens.reduce((sum, t) => sum + (t.value || 0), 0);
    this.metrics.tokensToday = tokens.filter(t => 
      new Date(t.created_at).toDateString() === today
    ).length;
    
    this.renderMetrics();
  }

  renderMetrics() {
    document.getElementById('metric-total-tokens').textContent = this.metrics.totalTokens;
    document.getElementById('metric-total-value').textContent = this.formatValue(this.metrics.totalValue);
    document.getElementById('metric-tokens-today').textContent = this.metrics.tokensToday;
  }

  formatValue(value) {
    if (value >= 1000000000) return `$${(value / 1000000000).toFixed(2)}B`;
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(2)}K`;
    return `$${value.toFixed(2)}`;
  }

  animateMetricChange(metricName) {
    const element = document.getElementById(`metric-${metricName.replace(/([A-Z])/g, '-$1').toLowerCase()}`);
    if (element) {
      element.style.animation = 'pulse 0.5s ease';
      setTimeout(() => {
        element.style.animation = '';
      }, 500);
    }
  }

  updateBalanceChart(balance) {
    // Update chart with new balance
    console.log('Balance chart updated:', balance);
  }
}

// Initialize
const dashboard = new RepoDashboardHubIntegration();
dashboard.init();
```

## Event System

### Available Events

All events are dispatched on the `window` object:

| Event Name | Description | Event Detail |
|------------|-------------|--------------|
| `pewpi.token.created` | New token created | `{ hash, type, value, owner, ... }` |
| `pewpi.token.updated` | Token updated | `{ hash, updates }` |
| `pewpi.token.deleted` | Token deleted | `{ hash }` |
| `pewpi.tokens.cleared` | All tokens cleared | `{}` |
| `pewpi.login.changed` | Login state changed | `{ authenticated, user }` |
| `pewpi.wallet.updated` | Wallet balance updated | `{ address, balance }` |

### Listening to Events

```javascript
// Direct event listeners
window.addEventListener('pewpi.token.created', (event) => {
  console.log('New token:', event.detail);
});

// Using Integration Listener
const listener = new PewpiIntegrationListener();
listener.init();
listener.on('tokenCreated', (token) => {
  console.log('New token:', token);
});
```

### Emitting Events

Events are automatically emitted by TokenService, LoginManager, and WalletUI. You can also emit custom events:

```javascript
const event = new CustomEvent('pewpi.custom.event', {
  detail: { myData: 'value' }
});
window.dispatchEvent(event);
```

## Backend Integration

### Magic Link Authentication

Add these endpoints to your backend:

```python
# Example Flask endpoints
@app.route('/auth/magic-link', methods=['POST'])
def send_magic_link():
    data = request.get_json()
    email = data.get('email')
    
    # Generate token
    token = secrets.token_urlsafe(32)
    
    # Store token (use Redis in production)
    magic_link_tokens[token] = {
        'email': email,
        'expiry': (datetime.now() + timedelta(minutes=15)).isoformat()
    }
    
    # In dev mode, return token directly
    if os.getenv('DEV_MODE') == 'true':
        return jsonify({
            'success': True,
            'devToken': token
        })
    
    # In production, send email
    send_email(email, f'Your magic link: {token}')
    return jsonify({'success': True})

@app.route('/auth/magic-link/verify', methods=['POST'])
def verify_magic_link():
    token = request.get_json().get('token')
    
    if token in magic_link_tokens:
        email = magic_link_tokens[token]['email']
        # Create session, log in user
        session['user_email'] = email
        return jsonify({'success': True, 'user': {'email': email}})
    
    return jsonify({'success': False, 'error': 'Invalid token'}), 400
```

## Migration Guide

### From GitHub-Only Auth to Magic Link + GitHub

1. **Keep existing GitHub OAuth** - No breaking changes
2. **Add magic link endpoints** to backend
3. **Update login UI** to show both options
4. **Existing users** continue using GitHub
5. **New users** can choose magic link (no GitHub required)

### IndexedDB Migration

If you have existing localStorage data:

```javascript
// Export from localStorage
const oldData = {
  tokens: JSON.parse(localStorage.getItem('tokens') || '[]'),
  wallets: JSON.parse(localStorage.getItem('wallets') || '[]')
};

// Initialize new TokenService
const tokenService = new TokenService();
await tokenService.init();

// Import data
await tokenService.importAll(oldData);

// Clean up old data
localStorage.removeItem('tokens');
localStorage.removeItem('wallets');

console.log('Migration complete!');
```

## Testing

### Unit Tests

```bash
# Install dependencies
npm install

# Run tests
npm test
```

### Integration Tests

See `tests/e2e-login-wallet.test.js` for example e2e test.

### Manual Testing

1. Open `demo.html` in browser
2. Test magic link login (dev mode)
3. Create test tokens
4. Verify wallet updates
5. Check live feed
6. Export/import data

## Rollback Instructions

If you need to rollback:

### 1. Remove Files

```bash
rm -rf src/shared/ src/components/
rm package.json jest.config.js
```

### 2. Revert Backend Changes

```bash
git checkout auth_server.py
```

### 3. Restore Old Login

Update your HTML to use old auth:

```html
<button onclick="window.location.href='/auth/github'">
  Login with GitHub
</button>
```

### 4. Clean Database

```javascript
// Clear IndexedDB
indexedDB.deleteDatabase('pewpi-tokens');
```

## Security Considerations

### Magic Link Tokens

- **Expiry**: Tokens expire after 15 minutes
- **Single Use**: Tokens can only be used once
- **Rate Limiting**: 5 requests per minute per email
- **Dev Mode**: Only use in development environment

### Data Storage

- **IndexedDB**: Data stored locally, not sent to server
- **Encryption**: Use CryptoHelpers for sensitive data
- **Session Management**: Sessions expire after inactivity

### P2P Sync

- **Optional**: P2P sync is opt-in, not required
- **ECDH**: Key exchange ensures only paired peers can decrypt
- **WebRTC**: Direct peer connections, no server intermediary

## Support

For issues or questions:

1. Check `PEWPI_LOGIN_DOCS.md` in z repository
2. Review `DESIGN_DOCS.md` for UI guidelines
3. See example integrations above
4. Test with `demo.html`

## Advanced Features

### Custom Token Types

```javascript
await tokenService.createToken({
  type: 'nft',
  value: 1000000,
  metadata: {
    imageUrl: 'https://example.com/art.png',
    rarity: 'legendary',
    collection: 'pewpi-genesis'
  }
});
```

### Client-Side Models

```javascript
const UserModel = ClientModel.model('User', {
  username: { type: String, required: true },
  tokenCount: { type: Number, default: 0 }
}, tokenService);

const user = await UserModel.create({
  username: 'newuser',
  tokenCount: 0
});
```

### Encrypted Tokens

```javascript
const cryptoHelpers = new CryptoHelpers();
const key = await cryptoHelpers.generateAESKey();

const encrypted = await cryptoHelpers.encryptAES({
  sensitiveData: 'secret'
}, key);

const decrypted = await cryptoHelpers.decryptAES(encrypted, key);
```

## Conclusion

The pewpi shared token/wallet system provides a complete authentication and token management solution that works across all pewpi repositories. Follow the integration examples above to add it to your repository in under 30 minutes.
