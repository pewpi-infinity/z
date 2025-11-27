# pewpi_login — User Authentication with IP Verification

A Python 3 tool for managing user credentials and authenticating users based on their IP address.

## Features

- **User Management**: Add users with passwords and allowed IP addresses via CLI
- **HTTP Server**: Run a login server that verifies credentials and client IP
- **IP Verification**: Only allow logins from pre-approved IP addresses
- **Secure Password Storage**: Uses bcrypt for password hashing (falls back to SHA256 if bcrypt is not available)
- **Embedded Credentials** (optional): Write credentials directly into the script file for isolated/testing environments

## Installation

```bash
# Install dependencies (optional but recommended)
pip install -r requirements.txt
```

If you cannot install `bcrypt` (e.g., missing build tools), the script will fall back to SHA256 hashing. This is less secure but functional.

## Usage

### Adding Users

Add a user with allowed IP addresses:

```bash
python pewpi_login.py add-user <username> <password> --ips <comma-separated-ips>
```

Example:
```bash
python pewpi_login.py add-user admin mypassword --ips 192.168.1.1,10.0.0.1,127.0.0.1
```

This stores the credential in `credentials.json` with:
- Username
- Password hash (bcrypt or SHA256)
- Allowed IP list
- Created timestamp

### Running the Server

Start the HTTP login server:

```bash
python pewpi_login.py run --host 0.0.0.0 --port 8080
```

Default values:
- `--host`: `0.0.0.0` (all interfaces)
- `--port`: `8080`

### API Endpoints

#### POST /login

Authenticate a user.

**Request:**
```json
{
  "username": "admin",
  "password": "mypassword"
}
```

**Success Response (HTTP 200):**
```json
{
  "ok": true,
  "message": "authenticated"
}
```

**Failure Response (HTTP 403):**
```json
{
  "ok": false,
  "message": "authentication failed"
}
```

The server checks:
1. Username exists
2. Password matches
3. Client IP is in the allowed list

#### GET /health

Health check endpoint.

**Response (HTTP 200):**
```json
{
  "ok": true,
  "message": "healthy"
}
```

### IP Address Detection

The server determines client IP in this order:
1. `X-Forwarded-For` header (first IP if multiple)
2. Direct remote address

When behind a reverse proxy, ensure it sets `X-Forwarded-For`.

⚠️ **Security Note**: The `X-Forwarded-For` header can be spoofed by clients. This implementation trusts the header when present, which is appropriate when running behind a trusted reverse proxy. If exposed directly to the internet without a trusted proxy, attackers could spoof their IP address.

## Embedding Credentials (Optional)

⚠️ **SECURITY WARNING** ⚠️

The `--embed` option writes credentials directly into the `pewpi_login.py` script file. **This is INSECURE** and should only be used in:
- Isolated testing environments
- Development setups
- Situations where the script file won't be committed to version control

### How Embedding Works

```bash
python pewpi_login.py add-user admin mypassword --ips 127.0.0.1 --embed
```

This:
1. Saves credentials to `credentials.json` (always)
2. Also writes credentials into the `EMBEDDED_CREDENTIALS` dictionary in the script

When the script loads credentials:
1. First checks `EMBEDDED_CREDENTIALS` in the script
2. Falls back to `credentials.json` if embedded credentials are empty

### Why This Exists

Some users need to distribute a single-file script with baked-in credentials for isolated environments. The `--embed` option supports this use case while:
- Making it opt-in (not default behavior)
- Providing clear warnings
- Still maintaining the safer `credentials.json` as the default

**Recommended approach**: Use `credentials.json` and add it to `.gitignore`.

## Security Considerations

1. **Default Storage**: Credentials are stored in `credentials.json` by default
2. **Git Ignore**: Add `scripts/credentials.json` to `.gitignore` to prevent accidental commits
3. **Password Hashing**: 
   - Prefers bcrypt (secure)
   - Falls back to SHA256 if bcrypt unavailable (less secure)
4. **IP Verification**: Adds a layer of security but can be bypassed with spoofed headers if not behind a trusted proxy
5. **Embedded Credentials**: INSECURE - use only when necessary

## Credential Storage Format

`credentials.json` structure:
```json
{
  "username": {
    "password_hash": "$2b$12$...",
    "allowed_ips": ["192.168.1.1", "10.0.0.1"],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

## Examples

### Full Workflow

```bash
# 1. Add a user
python pewpi_login.py add-user testuser testpass --ips 127.0.0.1,192.168.1.100

# 2. Start the server
python pewpi_login.py run --port 8080

# 3. Test login (from allowed IP)
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# 4. Test with X-Forwarded-For header
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 192.168.1.100" \
  -d '{"username": "testuser", "password": "testpass"}'
```

### Testing IP Restriction

```bash
# This should fail if your IP is not in the allowed list
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# This should succeed if 127.0.0.1 is in the allowed list
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.1" \
  -d '{"username": "testuser", "password": "testpass"}'
```

## Troubleshooting

### "bcrypt not available, falling back to SHA256"
Install bcrypt: `pip install bcrypt`

If installation fails, the script will work with SHA256 but is less secure.

### "No credentials found"
Run `add-user` command first to create credentials.

### Authentication always fails
1. Check the username exists in `credentials.json`
2. Verify the password is correct
3. Check your client IP is in the allowed list
4. If behind a proxy, ensure `X-Forwarded-For` is set

## License

Part of the pewpi-infinity/z repository.
