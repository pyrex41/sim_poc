# API Authentication System

This API uses a dual authentication system supporting both **JWT tokens** and **API keys** for secure access.

## Table of Contents

- [Quick Start](#quick-start)
- [Authentication Methods](#authentication-methods)
- [Setup](#setup)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Security Best Practices](#security-best-practices)

---

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Setup Script

```bash
python setup_auth.py
```

This will guide you through creating an admin user and optionally generating an API key.

### 3. Start the Server

```bash
python main.py
```

---

## Authentication Methods

### Method 1: JWT Token (Bearer Token)

- **Best for:** Frontend applications, temporary access
- **Lifetime:** 30 minutes (configurable)
- **Usage:** Add `Authorization: Bearer <token>` header

#### Login Flow

1. Login with username/password to get a token
2. Use the token in subsequent requests
3. Token expires after 30 minutes
4. Login again to get a new token

### Method 2: API Key

- **Best for:** Server-to-server, long-running processes, automation
- **Lifetime:** Configurable (can be permanent or expire after N days)
- **Usage:** Add `X-API-Key: <api-key>` header

---

## Setup

### Create Admin User & API Key

Run the setup script:

```bash
cd backend
python setup_auth.py
```

Follow the prompts to:
1. Create an admin user (username, email, password)
2. Optionally create an API key
3. Save the API key securely (shown only once!)

### Environment Variables (Optional)

Create a `.env` file in the backend directory:

```bash
# JWT Secret Key (auto-generated if not set)
SECRET_KEY=your-secret-key-here

# Token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## API Endpoints

### Authentication Endpoints

#### 1. Login (Get JWT Token)

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=your_password
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### 2. Create API Key

```http
POST /api/auth/api-keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Production Key",
  "expires_days": 365
}
```

**Response:**
```json
{
  "api_key": "sk_abc123...",
  "name": "Production Key",
  "created_at": "2025-01-14T12:00:00"
}
```

⚠️ **Important:** The API key is only shown once! Save it securely.

#### 3. List Your API Keys

```http
GET /api/auth/api-keys
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Production Key",
    "is_active": true,
    "created_at": "2025-01-14T12:00:00",
    "last_used": "2025-01-14T15:30:00",
    "expires_at": "2026-01-14T12:00:00"
  }
]
```

#### 4. Revoke API Key

```http
DELETE /api/auth/api-keys/{key_id}
Authorization: Bearer <token>
```

---

## Protected Endpoints

All endpoints except `/health` and `/api` require authentication:

- `POST /api/generate` - Generate scene
- `POST /api/validate` - Validate scene
- `POST /api/refine` - Refine scene
- `GET /api/scenes` - List scenes
- `GET /api/scenes/{id}` - Get scene
- `DELETE /api/scenes/{id}` - Delete scene
- `POST /api/run-video-model` - Generate video
- `GET /api/videos` - List videos
- `GET /api/videos/{id}` - Get video
- `POST /api/genesis/render` - Render with Genesis
- `GET /api/genesis/videos` - List Genesis videos
- `GET /api/genesis/videos/{id}` - Get Genesis video
- `DELETE /api/genesis/videos/{id}` - Delete Genesis video

---

## Usage Examples

### Using JWT Token

```bash
# 1. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=your_password' \
  | jq -r '.access_token')

# 2. Use token in requests
curl http://localhost:8000/api/videos \
  -H "Authorization: Bearer $TOKEN"
```

### Using API Key

```bash
# Direct access with API key
curl http://localhost:8000/api/videos \
  -H "X-API-Key: sk_abc123..."
```

### Python Example (JWT)

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/auth/login",
    data={
        "username": "admin",
        "password": "your_password"
    }
)
token = response.json()["access_token"]

# Use token
headers = {"Authorization": f"Bearer {token}"}
videos = requests.get(
    "http://localhost:8000/api/videos",
    headers=headers
).json()
```

### Python Example (API Key)

```python
import requests

headers = {"X-API-Key": "sk_abc123..."}

# Generate video
response = requests.post(
    "http://localhost:8000/api/run-video-model",
    headers=headers,
    json={
        "model_id": "cuuupid/cogvideox-5b",
        "collection": "text-to-video",
        "input": {"prompt": "A cat playing piano"}
    }
)
```

### JavaScript Example (Fetch API)

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    username: 'admin',
    password: 'your_password'
  })
});
const { access_token } = await loginResponse.json();

// Use token
const videosResponse = await fetch('http://localhost:8000/api/videos', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const videos = await videosResponse.json();
```

---

## Security Best Practices

### General

1. **Use HTTPS in production** - Never send credentials over HTTP
2. **Keep credentials secure** - Store API keys in environment variables
3. **Rotate API keys regularly** - Especially for production systems
4. **Use different keys for different environments** - Dev, staging, production
5. **Revoke unused keys** - Clean up old or compromised keys immediately

### Password Requirements

- Minimum 8 characters (enforced by setup script)
- Use strong, unique passwords
- Consider using a password manager
- Change default passwords immediately

### API Key Management

- **Never commit API keys to version control**
- Store in `.env` files (add to `.gitignore`)
- Use short expiration for temporary keys
- Monitor `last_used` timestamp to detect unauthorized access

### JWT Tokens

- Tokens expire after 30 minutes (default)
- Store securely in frontend (consider HttpOnly cookies)
- Don't expose in URLs or logs
- Implement token refresh if needed

---

## Troubleshooting

### "Not authenticated" Error

**Cause:** Missing or invalid authentication

**Solution:**
- Check you're sending the correct header (`Authorization` or `X-API-Key`)
- Verify token hasn't expired (JWT tokens expire after 30 minutes)
- Ensure API key is active and not expired
- Check for typos in the key/token

### "Incorrect username or password"

**Cause:** Invalid credentials

**Solution:**
- Verify username and password
- Run `setup_auth.py` to create/reset admin user
- Check for extra spaces in username/password

### "Admin privileges required"

**Cause:** Endpoint requires admin access

**Solution:**
- Ensure user has `is_admin=True` in database
- Use admin credentials or API key created by admin

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  is_active BOOLEAN DEFAULT 1,
  is_admin BOOLEAN DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP
);
```

### API Keys Table

```sql
CREATE TABLE api_keys (
  id INTEGER PRIMARY KEY,
  key_hash TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  is_active BOOLEAN DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_used TIMESTAMP,
  expires_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## Technical Details

### Authentication Flow

```
Client Request
    ↓
API Gateway
    ↓
Check Headers
    ├── X-API-Key present?
    │   ├── Valid? → Allow
    │   └── Invalid → Reject
    └── Authorization: Bearer present?
        ├── Valid JWT? → Allow
        └── Invalid → Reject
```

### Password Hashing

- Algorithm: **bcrypt**
- Automatic salt generation
- Secure password verification

### JWT Implementation

- Algorithm: **HS256**
- Claims: `sub` (username), `exp` (expiration)
- Signed with SECRET_KEY

### API Key Format

- Prefix: `sk_` (secret key)
- Length: 43 characters
- Encoding: URL-safe base64

---

## Advanced Configuration

### Custom Token Expiration

Edit `backend/auth.py`:

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
```

Or set environment variable:

```bash
export ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Custom Secret Key

Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to `.env`:

```bash
SECRET_KEY=your-generated-key-here
```

---

## Support

For issues or questions:
- Check the FastAPI docs: http://localhost:8000/docs
- Review error messages in server logs
- Run setup script again if database needs reset

---

## License

Same as the main project.
