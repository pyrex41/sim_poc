# Fly.io Deployment Guide

This guide walks you through deploying the Physics Simulator application to Fly.io with persistent storage for your data.

## Prerequisites

1. Install the Fly.io CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Login to Fly.io:
   ```bash
   fly auth login
   ```

3. Make sure you have your environment variables ready:
   - `REPLICATE_API_KEY` (optional, for AI scene generation)

## Initial Setup

### 1. Create the Fly.io Application

```bash
fly launch --no-deploy
```

This will:
- Create a new Fly.io app
- Generate a `fly.toml` configuration file (already provided)
- Set up your app in the Fly.io dashboard

When prompted:
- Choose an app name (or use the generated one)
- Select a region closest to your users
- Don't deploy yet - we need to set up the volume first

### 2. Create Persistent Volume

Create a volume for persistent data storage:

```bash
fly volumes create physics_data --region iad --size 1
```

Adjust:
- `--region` to match your app's region
- `--size` for the volume size in GB (1 GB minimum)

### 3. Set Environment Variables

Set your secrets/environment variables:

```bash
# Required: Set your Replicate API key for AI features
fly secrets set REPLICATE_API_KEY=your_replicate_api_key_here

# Optional: Set other environment variables
fly secrets set DATABASE_PATH=/data/scenes.db
```

### 4. Deploy

Deploy your application:

```bash
fly deploy
```

This will:
- Build the Docker image (including both frontend and backend)
- Push it to Fly.io
- Start your application
- Mount the persistent volume at `/data`

## Accessing Your Application

After deployment:

```bash
# Open in browser
fly open

# View logs
fly logs

# Check status
fly status

# SSH into the machine
fly ssh console
```

Your app will be available at: `https://your-app-name.fly.dev`

## Application Structure

### Production Mode

In production (on Fly.io):
- Frontend: Built Vite/Elm app served by FastAPI as static files
- Backend: FastAPI running on port 8080
- Data: Stored in `/data` (persistent volume)
- Database: SQLite at `/data/scenes.db`

### Development Mode

Locally:
- Frontend: Vite dev server on port 5173
- Backend: FastAPI on port 8000
- Data: Stored in `backend/DATA/`

## Scaling

### Vertical Scaling (More Resources)

Edit `fly.toml` to increase resources:

```toml
[[vm]]
  cpu_kind = "shared"
  cpus = 2           # Increase CPUs
  memory_mb = 512    # Increase RAM
```

Then deploy:
```bash
fly deploy
```

### Volume Size

To increase volume size:

```bash
fly volumes list  # Get volume ID
fly volumes extend <volume-id> --size 10  # Increase to 10GB
```

## Managing Data

### Backup Volume

```bash
# Create a snapshot
fly volumes snapshots create <volume-id>

# List snapshots
fly volumes snapshots list <volume-id>
```

### Access Data

```bash
# SSH into the machine
fly ssh console

# Navigate to data directory
cd /data
ls -la
```

## Configuration

### Port Configuration

The app runs on port 8080 (set via `PORT` env var in `fly.toml`).

### Health Checks

Fly.io monitors the `/health` endpoint:
- Interval: 30 seconds
- Timeout: 5 seconds
- Grace period: 10 seconds

### Auto-scaling

The app is configured to:
- Auto-stop when idle (saves costs)
- Auto-start on requests
- Minimum 0 machines running (cost-effective for low traffic)

Adjust in `fly.toml`:
```toml
[http_service]
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0  # Change to 1 for always-on
```

## Troubleshooting

### Check Logs

```bash
fly logs
```

### Check Health

```bash
fly checks list
```

### SSH Debug

```bash
fly ssh console
# Check if static files exist
ls -la /app/static
# Check data directory
ls -la /data
# Check running processes
ps aux
```

### Volume Issues

```bash
# List volumes
fly volumes list

# Check volume status
fly volumes show <volume-id>

# Destroy and recreate (WARNING: loses data)
fly volumes destroy <volume-id>
fly volumes create physics_data --region iad --size 1
```

### Rebuild and Deploy

```bash
# Force a fresh build
fly deploy --no-cache
```

## Cost Optimization

For a low-traffic app:
- Use `min_machines_running = 0` (auto-stop when idle)
- Use "shared" CPU kind
- Start with 256MB RAM
- 1GB volume is usually sufficient

Estimated cost: ~$5-10/month for small apps with auto-scaling.

## Updating the Application

1. Make your code changes locally
2. Test locally
3. Deploy:
   ```bash
   fly deploy
   ```

Fly.io will:
- Build new Docker image
- Deploy with zero-downtime
- Keep your data intact (persistent volume)

## DNS and Custom Domain

To use a custom domain:

```bash
fly certs add yourdomain.com
fly certs show yourdomain.com
```

Add the DNS records shown by the command to your domain provider.

## Monitoring

View metrics in the Fly.io dashboard:
- https://fly.io/apps/your-app-name

Or use the CLI:
```bash
fly dashboard
```

## Support

- Fly.io Docs: https://fly.io/docs/
- Fly.io Community: https://community.fly.io/
- This app's issues: https://github.com/your-repo/issues
