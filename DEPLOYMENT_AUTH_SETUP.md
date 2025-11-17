# Deployment Authentication Setup Guide

This guide covers setting up authentication for production deployment with the team users already configured.

## Current Team Configuration

**Users Created:**
- `reuben` (Admin) - Full access
- `mike` (User) - Standard access
- `harrison` (User) - Standard access

**Password:** `bestvideoproject` (for all users)

**Token Lifetime:** 5 days (persistent login)

---

## Production Deployment Steps

### Step 1: Environment Variables

Create a `.env` file in your deployment environment:

```bash
# Required: Secret key for JWT signing (generate a strong one for production!)
SECRET_KEY=<generate-secure-key-here>

# Optional: Token expiration (default: 5 days = 7200 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=7200

# Optional: API keys
REPLICATE_API_KEY=<your-replicate-key>
OPENAI_API_KEY=<your-openai-key>
```

**Generate a secure SECRET_KEY:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

⚠️ **IMPORTANT:** Never use the default auto-generated SECRET_KEY in production! Set a fixed key in `.env`.

---

### Step 2: Database Setup

The authentication database is automatically created when the app starts. However, you need to create the team users.

**Option A: Run the setup script on deployment**

```bash
cd backend
python add_team_users.py
```

This will create the three team users and generate their API keys. **Save the API keys securely!**

**Option B: Copy the existing database**

If you already ran the script locally and want to use the same credentials:

1. Locate your local database: `backend/DATA/scenes.db`
2. Copy it to your deployment server at the same location
3. Ensure file permissions are correct:
   ```bash
   chmod 644 backend/DATA/scenes.db
   ```

---

### Step 3: API Keys for Team Members

After running `add_team_users.py`, you'll get three API keys. Distribute them securely:

**Reuben's API Key:**
```
sk_rf__PoHNp1tem7rIjZ18RfNJoiq-QvpFwX6hbbnXYgc
```

**Mike's API Key:**
```
sk_LbGyYDzR1jzdnIfzYQHX5mQ-9C-BqGvxffZWfUAlLzs
```

**Harrison's API Key:**
```
sk_D7Yh7NUQ9DeeKKXWrYRHdfLeUN5sbnenZiJ-U46kwTc
```

⚠️ **Security:**
- Share API keys via secure channels (encrypted email, password manager, etc.)
- Each team member should store their key in a password manager
- Never commit API keys to git
- Consider regenerating keys if compromised

---

### Step 4: Deployment Platforms

#### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY .env .env

# Create data directory
RUN mkdir -p /app/backend/DATA

# Expose port
EXPOSE 8000

# Run setup (optional - only on first deploy)
# RUN python backend/add_team_users.py

# Start server
CMD ["python", "backend/main.py"]
```

**Docker Compose:**

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./backend/DATA:/app/backend/DATA
    env_file:
      - .env
    restart: unless-stopped
```

#### Fly.io Deployment (Recommended!)

**1. Install Fly CLI:**
```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

**2. Create `fly.toml` in project root:**

```toml
app = "bestvideoproject-api"
primary_region = "sjc"  # Or your preferred region

[build]
  [build.args]
    NODE_VERSION = "18"

[env]
  PORT = "8000"
  ACCESS_TOKEN_EXPIRE_MINUTES = "7200"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512

[mounts]
  source = "data"
  destination = "/app/backend/DATA"
```

**3. Create Dockerfile (if not exists):**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application
COPY backend/ ./backend/

# Create data directory
RUN mkdir -p /app/backend/DATA

EXPOSE 8000

# Start server
CMD ["python", "backend/main.py"]
```

**4. Set secrets:**

```bash
# Generate a strong SECRET_KEY
fly secrets set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"

# Optional: Set other secrets
fly secrets set REPLICATE_API_KEY="your-key"
fly secrets set OPENAI_API_KEY="your-key"
```

**5. Create persistent storage:**

```bash
fly volumes create data --size 1  # 1GB volume for database
```

**6. Deploy:**

```bash
fly deploy
```

**7. Run user setup (one-time):**

```bash
# SSH into the running instance
fly ssh console

# Run the setup script
cd /app
python backend/add_team_users.py

# Exit SSH
exit
```

**8. Get your app URL:**

```bash
fly status
```

Your API will be available at `https://bestvideoproject-api.fly.dev`

**9. View logs:**

```bash
fly logs
```

**Important Notes for Fly.io:**
- ✅ Automatic HTTPS enabled by default
- ✅ Global CDN included
- ✅ Persistent volume for database (`/app/backend/DATA`)
- ✅ Secrets management built-in
- ⚠️ Database is on mounted volume - survives deployments
- ⚠️ First deployment might take 2-3 minutes

**Updating the app:**

```bash
# Make code changes, then:
git add .
git commit -m "Update backend"
fly deploy
```

#### Heroku Deployment

```bash
# 1. Create Heroku app
heroku create bestvideoproject-api

# 2. Set environment variables
heroku config:set SECRET_KEY="<your-secret-key>"
heroku config:set ACCESS_TOKEN_EXPIRE_MINUTES=7200

# 3. Add Procfile
echo "web: python backend/main.py" > Procfile

# 4. Deploy
git push heroku main

# 5. Run setup script (one-time)
heroku run python backend/add_team_users.py
```

#### AWS/GCP/DigitalOcean

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export SECRET_KEY="<your-secret-key>"
   export ACCESS_TOKEN_EXPIRE_MINUTES=7200
   ```

3. **Run setup:**
   ```bash
   python add_team_users.py
   ```

4. **Start service:**
   ```bash
   # Using systemd
   sudo cp bestvideoproject.service /etc/systemd/system/
   sudo systemctl enable bestvideoproject
   sudo systemctl start bestvideoproject
   ```

**Example systemd service file** (`bestvideoproject.service`):

```ini
[Unit]
Description=Best Video Project API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/bestvideoproject
Environment="SECRET_KEY=<your-secret-key>"
Environment="ACCESS_TOKEN_EXPIRE_MINUTES=7200"
ExecStart=/usr/bin/python3 backend/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### Step 5: HTTPS/SSL Setup

⚠️ **CRITICAL:** Always use HTTPS in production!

**Option A: Use a reverse proxy (Nginx)**

```nginx
server {
    listen 80;
    server_name api.bestvideoproject.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.bestvideoproject.com;

    ssl_certificate /etc/letsencrypt/live/api.bestvideoproject.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.bestvideoproject.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Option B: Use Cloudflare or similar CDN** (automatic HTTPS)

---

### Step 6: Frontend Configuration

Update your frontend to point to the production API:

```javascript
// config.js
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://api.bestvideoproject.com'
  : 'http://localhost:8000';

export { API_BASE_URL };
```

---

## User Management

### Adding New Users

To add more team members later:

1. **SSH into your server**

2. **Run Python script:**
   ```python
   from database import create_user, create_api_key
   from auth import get_password_hash, generate_api_key, hash_api_key

   # Create user
   user_id = create_user(
       username="newuser",
       email="newuser@bestvideoproject.com",
       hashed_password=get_password_hash("their_password"),
       is_admin=False
   )

   # Generate API key
   api_key = generate_api_key()
   create_api_key(
       key_hash=hash_api_key(api_key),
       name="newuser's API Key",
       user_id=user_id
   )

   print(f"API Key: {api_key}")
   ```

### Changing Passwords

```python
from database import get_user_by_username, get_db
from auth import get_password_hash

user = get_user_by_username("reuben")
new_hash = get_password_hash("new_password_here")

with get_db() as conn:
    conn.execute(
        "UPDATE users SET hashed_password = ? WHERE id = ?",
        (new_hash, user["id"])
    )
    conn.commit()
```

### Revoking API Keys

```bash
# Via API (requires authentication)
curl -X DELETE https://api.bestvideoproject.com/api/auth/api-keys/{key_id} \
  -H "Authorization: Bearer <admin-token>"

# Or via database
sqlite3 backend/DATA/scenes.db "UPDATE api_keys SET is_active = 0 WHERE id = <key_id>;"
```

---

## Monitoring & Security

### Monitor API Key Usage

```sql
-- Check last used timestamps
SELECT
    u.username,
    ak.name,
    ak.last_used,
    ak.created_at
FROM api_keys ak
JOIN users u ON ak.user_id = u.id
WHERE ak.is_active = 1
ORDER BY ak.last_used DESC;
```

### Security Checklist

- [ ] SECRET_KEY set to a strong, unique value (not auto-generated)
- [ ] HTTPS enabled for all traffic
- [ ] API keys stored securely by team members
- [ ] `.env` file excluded from git (in `.gitignore`)
- [ ] Database file backed up regularly
- [ ] Firewall configured (only ports 80/443 open)
- [ ] Strong passwords used (consider requiring password changes)
- [ ] Monitor failed login attempts
- [ ] Set up rate limiting (optional but recommended)

---

## Backup & Recovery

### Backup Database

```bash
# Automated daily backup
0 2 * * * cp /var/www/bestvideoproject/backend/DATA/scenes.db \
  /backup/scenes_$(date +\%Y\%m\%d).db
```

### Restore from Backup

```bash
cp /backup/scenes_20250114.db backend/DATA/scenes.db
chmod 644 backend/DATA/scenes.db
```

---

## Troubleshooting

### "Invalid credentials" on deployment

**Cause:** Users not created or database not copied

**Solution:**
```bash
python backend/add_team_users.py
```

### "SECRET_KEY changed, tokens invalid"

**Cause:** SECRET_KEY changed between deployments

**Solution:** Set a fixed SECRET_KEY in `.env`:
```bash
export SECRET_KEY="<same-key-as-before>"
```

### Tokens expiring too quickly

**Cause:** ACCESS_TOKEN_EXPIRE_MINUTES not set

**Solution:**
```bash
export ACCESS_TOKEN_EXPIRE_MINUTES=7200  # 5 days
```

---

## Quick Reference

### Team Credentials
| User | Role | Password |
|------|------|----------|
| reuben | Admin | bestvideoproject |
| mike | User | bestvideoproject |
| harrison | User | bestvideoproject |

### Environment Variables
```bash
SECRET_KEY=<64-char-random-string>
ACCESS_TOKEN_EXPIRE_MINUTES=7200
```

### Important Files
```
backend/DATA/scenes.db          # Database (includes users & API keys)
backend/.env                    # Environment variables (create this!)
backend/add_team_users.py       # User setup script
```

### Useful Commands
```bash
# Check if users exist
sqlite3 backend/DATA/scenes.db "SELECT username, email, is_admin FROM users;"

# List API keys
sqlite3 backend/DATA/scenes.db "SELECT u.username, ak.name, ak.is_active FROM api_keys ak JOIN users u ON ak.user_id = u.id;"

# Test authentication
curl -X POST https://your-domain.com/api/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=reuben&password=bestvideoproject'
```

---

## Support

For deployment issues:
- Check server logs: `tail -f /var/log/bestvideoproject/api.log`
- Verify environment variables: `printenv | grep -E '(SECRET_KEY|ACCESS_TOKEN)'`
- Test database connection: `sqlite3 backend/DATA/scenes.db ".tables"`
