# Team Credentials & Setup Summary

**⚠️ SENSITIVE INFORMATION - DO NOT COMMIT TO GIT**

Add this file to `.gitignore` immediately!

---

## Team Users Created ✅

All users have been successfully created with 5-day persistent tokens.

| User | Role | Password | Status |
|------|------|----------|--------|
| reuben | **Admin** | bestvideoproject | ✅ Active |
| mike | User | bestvideoproject | ✅ Active |
| harrison | User | bestvideoproject | ✅ Active |

---

## API Keys

⚠️ **SAVE THESE SECURELY - THEY CANNOT BE RETRIEVED AGAIN!**

### Local Development Keys

#### Reuben (Admin)
```
sk_rf__PoHNp1tem7rIjZ18RfNJoiq-QvpFwX6hbbnXYgc
```

#### Mike
```
sk_LbGyYDzR1jzdnIfzYQHX5mQ-9C-BqGvxffZWfUAlLzs
```

#### Harrison
```
sk_D7Yh7NUQ9DeeKKXWrYRHdfLeUN5sbnenZiJ-U46kwTc
```

### Production Keys (Fly.io) ✅ DEPLOYED

**App URL:** https://gauntlet-video-server.fly.dev

#### Reuben (Admin)
```
sk_wJaMmkmNOzBKsC3NocXkYP3eeszZShZThzfcJs8y0Ik
```

#### Mike
```
sk_HVaAtfXaEbHvh1dInoXxRTAUShk9XdnC5iNdhXqyp-Y
```

#### Harrison
```
sk_SYcfmGAtEq9LLW0nz8UTozpcpDl7yUHZb_vKEY7tLzg
```

---

## Quick Start

### Option 1: Login with Password (5-Day Token)

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=reuben&password=bestvideoproject'
```

**Response:**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 432000  // 5 days in seconds
}
```

**Store the token for 5 days:**
```javascript
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('login_time', Date.now());
```

### Option 2: Use API Key Directly

```bash
curl http://localhost:8000/api/videos \
  -H 'X-API-Key: sk_rf__PoHNp1tem7rIjZ18RfNJoiq-QvpFwX6hbbnXYgc'
```

---

## Fly.io Deployment Steps

### 1. Initial Setup

```bash
# Install Fly CLI (if not already installed)
curl -L https://fly.io/install.sh | sh
fly auth login

# Navigate to project
cd /Users/reuben/gauntlet/video/sim_poc

# Create fly.toml (already provided in DEPLOYMENT_AUTH_SETUP.md)
# Create Dockerfile (already provided in DEPLOYMENT_AUTH_SETUP.md)
```

### 2. Set Secrets

```bash
# Generate and set SECRET_KEY
fly secrets set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"

# Set your API keys
fly secrets set REPLICATE_API_KEY="your-replicate-key-here"
fly secrets set OPENAI_API_KEY="your-openai-key-here"
```

### 3. Create Volume & Deploy

```bash
# Create persistent volume for database
fly volumes create data --size 1

# Deploy!
fly deploy
```

### 4. Setup Team Users on Fly.io

```bash
# SSH into the deployed app
fly ssh console

# Run the setup script
cd /app
python backend/add_team_users.py

# Save the generated API keys (will be different from local!)

# Exit
exit
```

### 5. Test Deployment

```bash
# Get your app URL
fly status

# Test login (replace with your fly.io URL)
curl -X POST https://bestvideoproject-api.fly.dev/api/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=reuben&password=bestvideoproject'
```

---

## Frontend Integration

Update your frontend to use the deployed API:

### Production Config

```javascript
// config.js
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://bestvideoproject-api.fly.dev'  // Your actual Fly.io URL
  : 'http://localhost:8000';

export { API_BASE_URL };
```

### Login & Token Storage

```javascript
// auth.js
async function login(username, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password })
  });

  const data = await response.json();

  // Store for 5 days
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('username', username);
  localStorage.setItem('login_time', Date.now());

  return data;
}

// Use in requests
async function fetchVideos() {
  const token = localStorage.getItem('access_token');

  const response = await fetch(`${API_BASE_URL}/api/videos`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return await response.json();
}
```

See `FRONTEND_AUTH_GUIDE.md` for complete implementation details.

---

## Configuration Summary

### Token Lifetime
- **Duration:** 5 days (7200 minutes)
- **Configurable via:** `ACCESS_TOKEN_EXPIRE_MINUTES` environment variable
- **Frontend Storage:** LocalStorage (recommended) or Cookies

### Authentication Methods
1. **JWT Token** (Bearer) - For frontend web apps
   - Get token via `/api/auth/login`
   - Include as `Authorization: Bearer <token>` header
   - Expires after 5 days
   - Can be refreshed by logging in again

2. **API Key** - For scripts, automation, backend
   - Get via `/api/auth/api-keys` (after logging in)
   - Include as `X-API-Key: <key>` header
   - Never expires (unless set with `expires_days`)
   - Can be revoked anytime

---

## Security Checklist

- [ ] Add `TEAM_CREDENTIALS.md` to `.gitignore`
- [ ] Set strong `SECRET_KEY` on Fly.io (done via `fly secrets set`)
- [ ] Store API keys in password manager (1Password, LastPass, etc.)
- [ ] Share credentials via secure channels only (encrypted email, Signal, etc.)
- [ ] Enable HTTPS (automatic on Fly.io ✅)
- [ ] Configure CORS for production domain
- [ ] Backup database regularly (`/app/backend/DATA/scenes.db` on Fly.io)

---

## Useful Commands

### Local Development

```bash
# Start backend with venv
cd backend
source venv/bin/activate
python main.py

# Create new API key for a user
python -c "
from database import create_api_key, get_user_by_username
from auth import generate_api_key, hash_api_key

user = get_user_by_username('reuben')
api_key = generate_api_key()
create_api_key(hash_api_key(api_key), 'New Key', user['id'])
print(f'API Key: {api_key}')
"
```

### Fly.io Management

```bash
# View logs
fly logs

# SSH into app
fly ssh console

# Check app status
fly status

# Restart app
fly apps restart bestvideoproject-api

# View secrets (names only, not values)
fly secrets list

# Update app
git commit -am "Update"
fly deploy
```

---

## Support Resources

- **Authentication Docs:** `AUTHENTICATION.md`
- **Deployment Guide:** `DEPLOYMENT_AUTH_SETUP.md`
- **Frontend Guide:** `FRONTEND_AUTH_GUIDE.md`
- **Fly.io Docs:** https://fly.io/docs/
- **API Interactive Docs:** http://localhost:8000/docs (local) or your Fly.io URL + `/docs`

---

## Emergency Procedures

### Lost API Key

1. Login with username/password
2. Create new API key:
   ```bash
   curl -X POST https://your-app.fly.dev/api/auth/api-keys \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Replacement Key"}'
   ```

### Forgot Password

Run on server:
```python
from database import get_user_by_username, get_db
from auth import get_password_hash

user = get_user_by_username("reuben")
new_hash = get_password_hash("new_password")

with get_db() as conn:
    conn.execute(
        "UPDATE users SET hashed_password = ? WHERE id = ?",
        (new_hash, user["id"])
    )
    conn.commit()
```

### Compromised Credentials

1. **Revoke API key immediately:**
   ```bash
   curl -X DELETE https://your-app.fly.dev/api/auth/api-keys/{key_id} \
     -H "Authorization: Bearer <admin-token>"
   ```

2. **Change password** (see above)

3. **Generate new SECRET_KEY:**
   ```bash
   fly secrets set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
   ```
   ⚠️ This will invalidate all existing tokens!

---

**Last Updated:** 2025-01-14
**Created By:** Claude Code Setup Assistant
**Environment:** Development → Production (Fly.io)
