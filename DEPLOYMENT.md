# Deployment Guide - Generation Platform V3

## Fly.io Deployment

### Prerequisites
- Fly.io account and CLI installed (`brew install flyctl`)
- Logged in: `fly auth login`

### Configuration

**App Name:** `gauntlet-gen-platform-v3`
**Region:** `dfw` (Dallas, Texas)
**URL:** `https://gauntlet-gen-platform-v3.fly.dev`

### First-Time Deployment

1. **Create the app:**
   ```bash
   fly apps create gauntlet-gen-platform-v3
   ```

2. **Create the volume for SQLite database:**
   ```bash
   fly volumes create gen_platform_v3_data --region dfw --size 1
   ```

3. **Set secrets (environment variables):**
   ```bash
   fly secrets set REPLICATE_API_KEY=your_key_here
   ```

4. **Deploy:**
   ```bash
   fly deploy
   ```

### Subsequent Deployments

```bash
fly deploy
```

### Accessing the App

- **API:** `https://gauntlet-gen-platform-v3.fly.dev/api/v3/`
- **Docs:** `https://gauntlet-gen-platform-v3.fly.dev/docs`
- **Health:** `https://gauntlet-gen-platform-v3.fly.dev/api/v3/health`
- **Web UI:** `https://gauntlet-gen-platform-v3.fly.dev/app/clients-campaigns.html`

### Environment Variables

Set via `fly secrets set`:

```bash
REPLICATE_API_KEY=your_replicate_key
```

### Resources

- **Memory:** 2GB RAM
- **CPU:** 1 shared CPU
- **Storage:** 1GB persistent volume

### Cost Optimization

- App uses auto-suspend, so it only runs when receiving requests
- Scales to zero when idle
- Estimated cost: ~$5-10/month with light usage
