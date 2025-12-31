# Infinity Research Portal - Setup Guide

## Overview

This is a comprehensive mobile-optimized research portal with GitHub OAuth authentication, article reader, and Mongoose OS integration.

## Features

- 🔐 **GitHub OAuth Authentication**: Secure login with GitHub
- 📱 **Mobile-First Design**: Optimized for Android devices (max-width: 480px)
- 📚 **Article Reader**: Browse and filter research articles by category
- 🎨 **Color-Coded System**: Visual categorization of content
- 💬 **Chat Terminal**: Mongoose OS device communication
- 🔢 **Token System**: Build and value research tokens with user attribution
- 📊 **User Tracking**: Track token creation and login activity

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure GitHub OAuth

1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. Create a new OAuth App with:
   - Homepage URL: `http://localhost:5000`
   - Authorization callback URL: `http://localhost:5000/auth/callback`
3. Copy the Client ID and Client Secret

### 3. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your GitHub OAuth credentials:

```env
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:5000/auth/callback
SESSION_SECRET=your_random_secret_key_here
```

### 4. Build Research Index

Generate the article index from existing tokens:

```bash
python3 build_research_index.py
```

### 5. Start the Server

```bash
python3 auth_server.py
```

The server will start on `http://localhost:5000`

## Usage

### Web Interface

1. Open `http://localhost:5000` in your browser
2. Click "Login with GitHub" to authenticate
3. Browse articles by filtering by category
4. Click the chat button (💬) to open Mongoose OS terminal

### Creating Tokens

Tokens can be created via:

1. **Web API** (requires authentication):
```bash
curl -X POST http://localhost:5000/api/token/build \
  -H "Content-Type: application/json" \
  -d '{"text": "Your research content here", "source_type": "text"}'
```

2. **CLI** (for local development):
```bash
python3 build_token.py
```

### Mongoose OS Chat Terminal

The chat terminal provides commands for interacting with Mongoose OS devices:

- `status` - Get connector status
- `help` - Show available commands
- `info <device_ip>` - Get device information
- `clear` - Clear terminal
- `/rpc/Sys.GetInfo <device_ip>` - Make RPC call to device

## Architecture

### Backend Components

- **auth_server.py**: Flask server handling OAuth, authentication, and API endpoints
- **mongoose_connector.py**: Mongoose OS device communication interface
- **build_token.py**: Token creation and valuation system
- **build_research_index.py**: Research index generator
- **pewpi_login.py**: User authentication and token management

### Frontend Components

- **index.html**: Mobile-optimized main page
- **static/css/index.css**: Responsive styling
- **static/js/auth.js**: Authentication handler
- **static/js/chat.js**: Chat terminal interface
- **static/js/index.js**: Article reader and filtering

### Data Files

- **users.json**: User accounts and sessions
- **login_commits.json**: User activity tracking
- **research_index.json**: Article index
- **tokens/**: Token storage directory
- **mongoose/mongoose.json**: Mongoose OS configuration

## Security Features

- ✅ GitHub OAuth authentication
- ✅ CSRF protection with state tokens
- ✅ Session management with secure tokens
- ✅ Rate limiting on authentication endpoints
- ✅ Input sanitization and validation
- ✅ XSS prevention with HTML escaping
- ✅ Path traversal prevention
- ✅ Environment variable configuration

## Color Coding System

Each research category has a distinct color:

- **Engineering**: Green (#22c55e)
- **CEO**: Orange (#f97316)
- **Import**: Blue (#3b82f6)
- **Investigate**: Pink (#ec4899)
- **Routes**: Red (#ef4444)
- **Data**: Yellow (#eab308)
- **Assimilation**: Purple (#a855f7)

## API Endpoints

### Authentication

- `GET /auth/github` - Initiate GitHub OAuth flow
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/status` - Get authentication status
- `POST /auth/logout` - Log out current user

### User Management

- `GET /api/user/commits` - Get user's activity history
- `POST /api/user/update-tokens` - Update user's token count

### Token Building

- `POST /api/token/build` - Create a new token (requires authentication)

### Mongoose OS

- `GET /api/mongoose/status` - Get Mongoose OS status
- `GET /api/mongoose/commands` - Get available commands
- `POST /api/mongoose/chat` - Process chat command (requires authentication)

### Utility

- `GET /health` - Health check endpoint
- `GET /research_index.json` - Get research article index

## Development

### Running Tests

```bash
python3 -m pytest test_pewpi_login.py
```

### Rebuilding Index

After adding new tokens, rebuild the research index:

```bash
python3 build_research_index.py
```

### Local Development Without OAuth

For local development without OAuth, you can use the CLI tools directly:

```bash
# Create tokens
python3 build_token.py

# Manage users
python3 pewpi_login.py
```

## Troubleshooting

### OAuth Not Working

1. Check that `.env` file exists with correct credentials
2. Verify callback URL matches GitHub OAuth App settings
3. Check server logs for error messages

### Articles Not Loading

1. Run `python3 build_research_index.py` to rebuild index
2. Check that `research_index.json` exists and is valid JSON
3. Verify token files exist in `tokens/` or `infinity_tokens/` directories

### Chat Terminal Not Connecting

1. Verify Mongoose OS device IP is correct
2. Check network connectivity to device
3. Ensure device is running and accessible on port 80

## Production Deployment

For production deployment:

1. Set `FLASK_DEBUG=False` in `.env`
2. Use a production WSGI server (e.g., Gunicorn):
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 auth_server:app
   ```
3. Set up HTTPS with a reverse proxy (nginx, Apache)
4. Use a proper database instead of JSON files
5. Implement proper session storage (Redis, database)
6. Set strong `SESSION_SECRET` value
7. Configure proper CORS settings

## Contributing

Please ensure all code:
- Follows existing style conventions
- Includes security considerations
- Has proper error handling
- Is documented with comments

## License

See repository license file for details.
