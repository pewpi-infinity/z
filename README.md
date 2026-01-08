# Pewpi Infinity Research Portal

A production-grade research token management and visualization system with passwordless authentication, wallet management, and cross-repository token synchronization.

## 🚀 New in v2.0

- **🔐 Passwordless Login**: Magic-link authentication (no GitHub account required)
- **💼 Wallet System**: Balance tracking, token list, and live feed
- **🔄 Token Sync**: Cross-repository event system for real-time updates
- **💾 IndexedDB Storage**: Production-ready local persistence with Dexie
- **🔒 Encryption Ready**: AES-GCM helpers and ECDH key exchange for P2P
- **🧩 Client Models**: Mongoose-style models for front-end development
- **🎨 Standardized Theme**: Consistent CSS variables across all pewpi repos

## Features

### 🔐 Production Authentication

- **Magic Link (Passwordless)**: Email-based authentication without passwords
  - Dev mode: Works without SMTP for local testing
  - Production mode: Email delivery via configured SMTP
  - 15-minute token expiry with single-use tokens
  - Rate limiting: 5 requests per minute per email
- **GitHub OAuth (Optional)**: Existing GitHub login as opt-in alternative
- **Session Management**: Secure server-side sessions with auto-expiry
- **User Tracking**: Login history, token counts, and activity logs

### 💼 Wallet System

- **Balance Display**: Real-time wallet balance with formatting
- **Token List**: View all tokens with metadata and details
- **Live Token Feed**: Real-time updates when tokens are created/updated
- **Token Details**: Modal view with complete token information
- **Multi-Wallet Support**: Support for multiple wallet addresses

### 🔄 Cross-Repository Synchronization

- **Event System**: Window-level events for state synchronization
  - `pewpi.token.created` - New token created
  - `pewpi.token.updated` - Token modified
  - `pewpi.login.changed` - Authentication state changed
  - `pewpi.wallet.updated` - Balance updated
- **Integration Listener**: Simple API for subscribing to events
- **Automatic Sync**: Other repos (banksy, v, infinity-brain-searc) reflect changes
- **Example Integrations**: Ready-to-use code for all pewpi repositories

### 💾 Production Storage

- **IndexedDB (Primary)**: Fast, scalable client-side storage via Dexie
- **localStorage (Fallback)**: Automatic fallback for compatibility
- **Migration Tools**: Export/import for data migration
- **Event Logging**: Track all operations with timestamps
- **Auto-tracking**: Optional real-time change monitoring

### 🔒 Security & Encryption

- **AES-GCM Encryption**: Encrypt sensitive token data
- **ECDH Key Exchange**: Secure peer-to-peer key derivation
- **SHA-256 Hashing**: Secure hash generation
- **P2P Sync (Stub)**: WebRTC DataChannel infrastructure ready
- **Configurable TURN**: Support for production P2P deployments

### 🧩 Client-Side Models

- **Mongoose-Style API**: Familiar model interface for front-end
- **Schema Validation**: Type checking, required fields, enums
- **Query Operators**: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
- **CRUD Operations**: create, find, update, delete with full API
- **No Backend Required**: Operate entirely client-side with IndexedDB

### 🎨 Standardized Theme

- **CSS Variables**: Consistent colors, spacing, typography
- **Component Styles**: Pre-styled login, wallet, modal components
- **Dark Theme**: Modern dark UI matching pewpi brand
- **Responsive**: Mobile-first design (max-width: 480px optimized)
- **Animations**: Smooth transitions and micro-interactions

## 📦 Pewpi Shared Library

This repository now includes the **canonical pewpi-shared library** from [GPT-Vector-Design](https://github.com/pewpi-infinity/GPT-Vector-Design), providing unified authentication, wallet, and token management across all pewpi repositories.

### Included Components

Located in **`src/pewpi-shared/`**:

- **`token-service.js`**: Production-grade token management with IndexedDB (Dexie) + localStorage fallback
- **`auth/login-component.js`**: Passwordless login (magic-link) + optional GitHub OAuth
- **`wallet/wallet-component.js`**: Wallet UI with balance, token list, and live feed
- **`integration-listener.js`**: Event-based integration for cross-repo state synchronization
- **`models/client-model.js`**: Mongoose-style client-side data models
- **`sync/p2p-sync.js`**: WebRTC-based peer-to-peer synchronization (optional)
- **`theme.css`**: Standardized CSS variables and component styles
- **`INTEGRATION.md`**: Complete integration guide and usage examples

### How to Initialize

The shared services are automatically initialized in `static/js/index.js`:

```javascript
// TokenService - auto-tracking enabled
const tokenService = new TokenService();
tokenService.initAutoTracking();

// LoginComponent - session automatically restored from storage
const loginComponent = new LoginComponent({ devMode: true });

// IntegrationListener - listens for cross-repo events
const listener = new IntegrationListener({
  onTokenCreated: (token) => console.log('Token created:', token),
  onLoginChanged: (data) => console.log('Login changed:', data)
});
listener.start();
```

### Events Emitted

The shared library emits the following window-level events for cross-repository synchronization:

- **`pewpi.token.created`** - New token created
- **`pewpi.token.updated`** - Token modified  
- **`pewpi.login.changed`** - Authentication state changed
- **`pewpi.wallet.updated`** - Balance updated

### Migration Notes

The shared library is **backward-compatible** with existing code:
- Existing `src/shared/` and `src/components/` directories remain unchanged
- Initialization is wrapped in try-catch to prevent breaking existing builds
- Services are only initialized if available (graceful fallback)
- To migrate to shared components, see `src/pewpi-shared/INTEGRATION.md`

For complete integration instructions and examples, see **[src/pewpi-shared/INTEGRATION.md](src/pewpi-shared/INTEGRATION.md)**.

### 1. JSON-Backed Token Hash Reading (`pewpi_login.py`)

- **Category Token Configuration** (`category_tokens.json`): Stores token hashes linked to research categories
- **Categories**: engineering (green), CEO (orange), import (blue), investigate (pink), routes (red), data (yellow), assimilation (purple)
- **Dynamic Association**: Tokens are automatically categorized based on keyword matching

### 2. Color-Coded Buttons

- Dynamic button generation based on categories from JSON/token data
- Each button displays research article links grouped by category
- Visual feedback with category-specific colors for quick identification

### 3. Toggle View Modes

The portal supports three view modes for displaying research content:

- **Plain Text**: Default mode, displays unformatted content
- **Word Mode**: Highlights individual keywords in their category colors
- **Sentence Mode**: Highlights entire sentences based on the most relevant category

### 4. Error Handling & Logging

- Comprehensive error handling for missing/invalid data
- Detailed logging for debugging and development
- Graceful fallbacks when data is unavailable

## Files

| File | Description |
|------|-------------|
| `pewpi_login.py` | Main module with token management, button generation, and view modes |
| `category_tokens.json` | Category configuration with token hashes and keywords |
| `research_index.json` | Research article index linked to categories |
| `index.html` | Web portal with color-coded buttons and toggle view modes |
| `test_pewpi_login.py` | Integration tests for the module |

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/pewpi-infinity/z.git
cd z

# Install Python dependencies
pip install -r requirements.txt

# Install JavaScript dependencies (for testing)
npm install

# Configure environment
cp .env.example .env
# Edit .env with your settings (GitHub OAuth optional)

# Build research index
python3 build_research_index.py

# Start server
python3 auth_server.py
# OR
./start_server.sh
```

### Access the Portal

- **Main Portal**: http://localhost:5000/
- **Demo Page**: http://localhost:5000/demo.html (Full feature demonstration)

### First Login

1. Open http://localhost:5000/demo.html
2. Enter your email address
3. In dev mode, token appears automatically
4. Click "Verify Token" to log in
5. Create test tokens and see wallet update in real-time

## Integration with Other Repositories

See [docs/INTEGRATION.md](docs/INTEGRATION.md) for complete integration guide.

### Quick Integration Example

```javascript
// Initialize services
const tokenService = new TokenService({ dbName: 'my-app-tokens' });
await tokenService.init();

const loginManager = new LoginManager({ devMode: true });
await loginManager.init();

const walletUI = new WalletUI(tokenService, {
  containerId: 'wallet-container'
});
await walletUI.init();

// Subscribe to events
const listener = new PewpiIntegrationListener();
listener.init();
listener.on('tokenCreated', (token) => {
  console.log('New token:', token);
});
```

### Supported Repositories

- ✅ **banksy**: Art collection with token integration
- ✅ **v**: Minimalist token counter
- ✅ **infinity-brain-searc**: Token search and indexing
- ✅ **repo-dashboard-hub**: Dashboard metrics and charts

See [docs/INTEGRATION.md](docs/INTEGRATION.md) for repository-specific examples.

## Usage

### Command Line

```bash
# Show status
python pewpi_login.py

# Sync tokens with research index
python pewpi_login.py --sync

# Validate configuration
python pewpi_login.py --validate

# List all categories
python pewpi_login.py --categories

# Output button data JSON
python pewpi_login.py --button-data

# Enable verbose logging
python pewpi_login.py --verbose
```

### Python API

```python
from pewpi_login import PewpiLogin

# Initialize
pewpi = PewpiLogin()

# Get all categories
categories = pewpi.get_categories()

# Sync tokens to research index
records = pewpi.sync()

# Get button data for frontend
button_data = pewpi.get_button_data()

# Generate HTML components
components = pewpi.generate_html_components()
# Returns: toggle_html, toggle_styles, toggle_script

# Validate configuration
result = pewpi.validate()
```

### Web Portal

Open `index.html` in a browser to access the research portal:

1. **Select a Category**: Click any role button to filter research by category
2. **Toggle View Mode**: Use the view mode toggle to switch between Plain Text, Word, and Sentence highlighting
3. **Open Research**: Click "Open research file" to view the full token data

## Configuration

### category_tokens.json

```json
{
  "categories": {
    "engineering": {
      "color": "green",
      "display_name": "Engineering",
      "description": "Engineering and technical research",
      "token_hashes": ["abc123..."],
      "keywords": ["quantum", "physics", "algorithm"]
    }
  },
  "color_map": {
    "green": "#22c55e",
    "orange": "#f97316"
  }
}
```

### Adding New Categories

1. Edit `category_tokens.json`
2. Add a new entry under `categories` with:
   - `color`: Color name (must be in `color_map`)
   - `display_name`: Human-readable name
   - `description`: Category description
   - `token_hashes`: Array of token hashes (can be empty)
   - `keywords`: Array of keywords for automatic categorization

## Testing

### Python Tests

Run existing Python tests:

```bash
python -m unittest test_pewpi_login -v
```

### JavaScript Tests

Run unit tests for TokenService and ClientModel:

```bash
# Install dependencies
npm install

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

### E2E Tests

See `tests/e2e-login-wallet.test.js` for end-to-end testing example.

### Manual Testing

1. Open `demo.html` in browser
2. Test magic-link login (dev mode)
3. Create test tokens
4. Verify wallet updates
5. Check live feed
6. Test event synchronization

## API Documentation

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/magic-link` | POST | Send magic link to email |
| `/auth/magic-link/verify` | POST/GET | Verify magic link token |
| `/auth/github` | GET | Initiate GitHub OAuth |
| `/auth/callback` | GET | GitHub OAuth callback |
| `/auth/status` | GET | Check authentication status |
| `/auth/logout` | POST | Log out current user |

### Magic Link Request

```javascript
POST /auth/magic-link
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Dev Mode Response:**
```json
{
  "success": true,
  "devToken": "abc123...",
  "devUrl": "http://localhost:5000/auth/magic-link/verify?token=abc123...",
  "email": "user@example.com"
}
```

### Magic Link Verification

```javascript
POST /auth/magic-link/verify
Content-Type: application/json

{
  "token": "abc123..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "username": "user",
    "email": "user@example.com",
    "provider": "magic_link",
    "token_count": 0
  }
}
```

### JavaScript API

#### TokenService

```javascript
const tokenService = new TokenService({
  dbName: 'my-tokens',
  version: 1,
  useLocalStorageFallback: true
});

await tokenService.init();

// Create token
const token = await tokenService.createToken({
  type: 'standard',
  value: 1000,
  owner: 'username',
  metadata: { custom: 'data' }
});

// Get all tokens
const tokens = await tokenService.getAll();

// Filter tokens
const filtered = await tokenService.getAll({ type: 'standard' });

// Update token
await tokenService.updateToken(hash, { value: 2000 });

// Delete token
await tokenService.deleteToken(hash);

// Wallet operations
await tokenService.updateBalance('default', 5000);
const balance = await tokenService.getBalance('default');

// Export/Import
const data = await tokenService.exportAll();
await tokenService.importAll(data);
```

#### LoginManager

```javascript
const loginManager = new LoginManager({
  devMode: true,
  apiBase: '/api'
});

await loginManager.init();

// Send magic link
await loginManager.sendMagicLink('user@example.com');

// Verify token
await loginManager.verifyMagicLink(token);

// Check auth status
if (loginManager.isAuthenticated()) {
  const user = loginManager.getUser();
}

// Logout
await loginManager.logout();
```

#### WalletUI

```javascript
const walletUI = new WalletUI(tokenService, {
  containerId: 'wallet-container',
  feedEnabled: true,
  refreshInterval: 5000,
  walletAddress: 'default'
});

await walletUI.init();

// Manual refresh
await walletUI.refresh();
```

#### Integration Listener

```javascript
const listener = new PewpiIntegrationListener({ debug: true });
listener.init();

// Subscribe to events
listener.on('tokenCreated', (token) => {
  console.log('Token created:', token);
});

listener.on('loginChanged', (data) => {
  if (data.authenticated) {
    console.log('User logged in:', data.user);
  }
});
```

## Integration with Existing Scripts

- `build_research_index.py` - Builds research index from tokens
- `cart077_infinity_research_scraper.py` - Scrapes research sources
- `cart080_infinity_research_router.py` - Routes research content
- `cart082_infinity_token_valuator.py` - Values tokens
- `cart083_frontend_router_patch.py` - Updates frontend pages

## Migration Guide

### Migrating from v1.0 to v2.0

**⚠️ Non-breaking changes**: Existing GitHub OAuth continues to work

#### Add New Dependencies

```bash
npm install dexie
```

#### Copy New Files

All new files are additive. No existing files need modification unless you want to integrate new features.

#### Enable Magic Link Auth

1. Set `DEV_MODE=true` in `.env` for local testing
2. Magic links work without SMTP configuration
3. Users can choose between magic link and GitHub OAuth

#### Data Migration

If you have existing token data in localStorage:

```javascript
// Run this once to migrate
const tokenService = new TokenService();
await tokenService.init();

// Import old data
const oldTokens = JSON.parse(localStorage.getItem('old_tokens') || '[]');
for (const token of oldTokens) {
  await tokenService.createToken(token);
}

console.log('Migration complete!');
```

### Database Migration

IndexedDB schema is automatically created on first init. No manual migration needed.

```javascript
// Automatic migration
const tokenService = new TokenService({ dbName: 'pewpi-tokens', version: 1 });
await tokenService.init(); // Creates schema automatically
```

### Rollback Instructions

If you need to rollback to v1.0:

#### 1. Remove New Files

```bash
# Remove new directories
rm -rf src/
rm -rf tests/

# Remove new config files
rm package.json jest.config.js

# Remove demo page
rm demo.html
```

#### 2. Revert Backend Changes

```bash
# Restore auth_server.py to previous version
git checkout v1.0 -- auth_server.py
```

#### 3. Clean Client Storage

```javascript
// Clear IndexedDB
indexedDB.deleteDatabase('pewpi-tokens');
indexedDB.deleteDatabase('pewpi-demo-tokens');

// Clear localStorage
localStorage.removeItem('pewpi-tokens_tokens');
localStorage.removeItem('pewpi-tokens_wallets');
localStorage.removeItem('pewpi-tokens_events');
```

#### 4. Restore Old HTML

Replace login section in HTML with:

```html
<button onclick="window.location.href='/auth/github'">
  Login with GitHub
</button>
```

#### 5. Restart Server

```bash
# Restart with old configuration
python3 auth_server.py
```

### Backup Before Migration

```bash
# Backup users and sessions
cp users.json users.json.backup
cp login_commits.json login_commits.json.backup

# Backup tokens
cp -r tokens/ tokens.backup/
cp -r infinity_tokens/ infinity_tokens.backup/
```

### Restore from Backup

```bash
# Restore users and sessions
cp users.json.backup users.json
cp login_commits.json.backup login_commits.json

# Restore tokens
cp -r tokens.backup/ tokens/
cp -r infinity_tokens.backup/ infinity_tokens/
```

## File Structure

```
z/
├── src/
│   ├── pewpi-shared/              # ⭐ Canonical shared library from GPT-Vector-Design
│   │   ├── token-service.js       # TokenService with IndexedDB
│   │   ├── integration-listener.js # Event subscription system
│   │   ├── theme.css              # Standardized theme variables
│   │   ├── INTEGRATION.md         # Complete integration guide
│   │   ├── auth/
│   │   │   └── login-component.js # LoginComponent (passwordless + OAuth)
│   │   ├── wallet/
│   │   │   └── wallet-component.js # WalletComponent (UI + balance)
│   │   ├── models/
│   │   │   └── client-model.js    # Mongoose-style models
│   │   └── sync/
│   │       └── p2p-sync.js        # P2P synchronization (WebRTC)
│   ├── shared/                    # Legacy shared utilities
│   │   ├── token-service.js       # (kept for backward compatibility)
│   │   ├── client-model.js        
│   │   ├── crypto-helpers.js      
│   │   ├── integration-listener.js 
│   │   └── theme.css              
│   └── components/                # Legacy components
│       ├── login.js               # (kept for backward compatibility)
│       └── wallet.js              
├── tests/
│   ├── setup.js                   # Jest configuration
│   ├── token-service.test.js     # TokenService unit tests
│   └── client-model.test.js      # ClientModel unit tests
├── docs/
│   └── INTEGRATION.md             # Integration guide
├── auth_server.py                 # Flask backend with magic link
├── demo.html                      # Full feature demonstration
├── package.json                   # JavaScript dependencies
├── jest.config.js                 # Test configuration
└── README.md                      # This file
```

## Security

### Production Checklist

- [ ] Set `DEV_MODE=false` in production
- [ ] Configure SMTP for magic link emails
- [ ] Set strong `SESSION_SECRET` in `.env`
- [ ] Use HTTPS for all endpoints
- [ ] Configure rate limiting (Redis recommended)
- [ ] Set up CORS properly
- [ ] Enable CSP headers
- [ ] Regular security audits
- [ ] Monitor login attempts
- [ ] Backup data regularly

### Security Features

- ✅ Magic link tokens expire after 15 minutes
- ✅ Tokens are single-use only
- ✅ Rate limiting on auth endpoints
- ✅ CSRF protection with state tokens
- ✅ Secure session management
- ✅ XSS prevention with HTML escaping
- ✅ Path traversal protection
- ✅ Input validation on all endpoints

## Support & Documentation

- **Integration Guide**: [docs/INTEGRATION.md](docs/INTEGRATION.md)
- **Design Documentation**: [DESIGN_DOCS.md](DESIGN_DOCS.md)
- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Login Documentation**: [PEWPI_LOGIN_DOCS.md](PEWPI_LOGIN_DOCS.md)

## Contributing

Contributions welcome! Please:

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Test with `demo.html` before submitting

## License

Pewpi Infinity Research Portal - Part of the Infinity Research System.
