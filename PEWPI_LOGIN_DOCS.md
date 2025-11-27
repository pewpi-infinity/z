# Pewpi Login System Documentation

## Overview

The Pewpi Login System extends the Infinity Research Portal with user authentication, token counting, and a "Build Your Own Token" feature. This system allows users to create, track, and combine research tokens with dynamically calculated values.

## Features

### 1. User Authentication

#### Sign In / Sign Up
- **Sign In Button**: Opens a modal for existing users to authenticate
- **Register**: New users can create an account with username/password
- **Logout**: Clears session and terminates sign-in state

#### User Data Storage
User data is persisted in `localStorage` (browser) and `users.json` (backend):
```json
{
    "users": {
        "username": {
            "password_hash": "sha256_hash",
            "token_count": 0,
            "tokens_created": [],
            "mega_hashes": [],
            "created_at": "ISO8601_timestamp",
            "last_login": "ISO8601_timestamp"
        }
    },
    "sessions": {}
}
```

### 2. Token Counting

Each user has a token counter that tracks:
- Number of tokens created/interacted with
- List of token hashes created by the user
- Mega hashes generated

The token count is displayed in the UI when signed in and updates automatically upon token generation.

### 3. Build Your Own Token

Access the terminal-like interface by clicking "Build Your Own Token".

#### Input Methods
1. **Text Entry**: Type or paste content directly into the textarea
2. **File Upload**: Upload `.txt`, `.md`, `.json`, `.csv`, `.xml`, or `.html` files

#### Token Value Calculation

Values range from **$90** to **$964,590,650,869,860,860.97** based on:

##### Scoring Algorithm
1. **Base Score**: Character count × 0.5 + Word count × 2
2. **Keyword Bonuses** (per occurrence):
   - Tier 1 ($500+): quantum, hydrogen, fusion, einstein, relativity, infinity, etc.
   - Tier 2 ($300+): vector, tensor, gravity, reactor, thermodynamics, entropy
   - Tier 3 ($150+): ai, algorithm, compute, research, discovery, patent
   - Tier 4 ($75+): data, analysis, model, theory, experiment
   - Special ($8,000-$15,000): kris, pewpi, hydra, osprey, classified, secret

3. **Depth Bonus**: log₂(character_count) × 100 (for content > 100 chars)
4. **Complexity Bonus**: (unique_words / total_words) × 1000
5. **Structure Bonus**: Line count × 10 (for content > 5 lines)

##### Value Scaling
| Score Range | Formula |
|-------------|---------|
| < 100 | $90 + score × 0.5 |
| 100-500 | $100 + score × 2 |
| 500-2,000 | $1,000 + score × 10 |
| 2,000-10,000 | $20,000 + score × 100 |
| 10,000-100,000 | $1M + score × 5,000 |
| 100,000-1M | $500M + score × 100,000 |
| > 1M | Exponential scaling up to max |

### 4. Mega Hash Generation

Combine multiple tokens into a "Mega Hash" for aggregate high-value outcomes.

#### Requirements
- Minimum 2 tokens required
- All tokens must exist in the current session

#### Mega Hash Value Calculation
- **Base Value**: $963 Billion minimum
- **Combination Bonus**: token_count × $1,000,000
- **Synergy Bonus**: token_count³ × $10,000,000
- **Combined Score**: Sum of all component token scores + bonuses

Mega hash values typically exceed **$963B+** and can reach the maximum value of ~$964 quadrillion.

## UI Components

### Header Section
- Sign In / Logout buttons
- Build Your Own Token button
- User info display (username + token count)

### Terminal Interface
- Dark theme with green terminal aesthetic
- Real-time logging of operations
- Token result cards with hash, score, and value
- Support for sentence, word, and plain text modes

### Integration with Existing Portal
- Seamless integration with role buttons (Engineer, CEO, Import, etc.)
- Works alongside the Rogers chat interface
- Maintains existing research index functionality

## Backend Python Modules

### pewpi_login.py
Handles user authentication:
- `register_user(username, password)` - Create new user
- `sign_in(username, password)` - Authenticate user
- `logout(session_token)` - End session
- `get_user_info(session_token)` - Retrieve user data
- `update_token_count(session_token, increment)` - Update counter
- `add_user_token(session_token, token_hash)` - Record token creation
- `add_mega_hash(session_token, mega_hash, value)` - Record mega hash

### build_token.py
Handles token creation and valuation:
- `build_token(text, source_type, filename)` - Create token from content
- `score_content(text)` - Analyze and score content
- `calculate_value(score)` - Convert score to dollar value
- `generate_mega_hash(token_hashes, description)` - Combine tokens
- `process_file_upload(file_content, filename)` - Handle file input

## File Structure

```
z/
├── index.html          # Main portal with login UI
├── pewpi_login.py      # User authentication backend
├── build_token.py      # Token builder backend
├── users.json          # User data storage
├── tokens/             # Generated token files
├── session_buffer.json # Pending tokens for valuation
└── PEWPI_LOGIN_DOCS.md # This documentation
```

## Error Handling

The system provides detailed feedback:
- Authentication errors (invalid credentials, user exists)
- Token creation errors (no content, invalid input)
- Mega hash errors (insufficient tokens)
- File upload errors (read failures)

All operations are logged in the terminal interface with color-coded messages:
- **Blue**: System messages
- **Green**: Success messages
- **Red**: Error messages
- **Orange**: Value displays

## Security Notes

- Passwords are hashed before storage (SHA-256)
- Session tokens are generated with secure random values
- User data stored locally (consider server-side storage for production)
- No sensitive data transmitted externally

## Future Enhancements

1. Server-side session management
2. Token marketplace integration
3. Research collaboration features
4. Export/import token portfolios
5. Advanced analytics dashboard
