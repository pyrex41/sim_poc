# n8n Integration for AI Generation Platform

This directory contains everything you need to deploy n8n and create visual workflows that chain together image, video, and audio generation with your AI platform.

## What is n8n?

n8n is a workflow automation tool that lets you visually connect different services and APIs without writing code. Perfect for:
- Chaining image generation → upscaling → video creation
- Creating complex multi-step AI pipelines
- Automating content creation workflows
- Building custom AI tools for non-technical users

## Quick Start - Local Development

### 1. Start n8n with Docker Compose

```bash
cd n8n
docker-compose up -d
```

This will start n8n on `http://localhost:5678`

### 2. Access n8n

Open your browser to `http://localhost:5678`

On first launch, you'll need to create an owner account.

### 3. Import Example Workflows

1. Click "Workflows" in the top menu
2. Click "Import from File"
3. Import workflows from the `workflows/` directory:
   - `01-simple-image-generation.json` - Basic image generation
   - `02-image-to-video-pipeline.json` - Chain image → video
   - `03-image-upscale-enhance.json` - Generate → upscale → enhance

### 4. Configure API URL

Each workflow uses `http://localhost:9090` as the API endpoint. If your generation API runs on a different URL, update the HTTP Request nodes.

## Deploy to Fly.io

### Prerequisites

1. Install [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/)
2. Login: `fly auth login`

### Deployment Steps

1. **Update Configuration**

Edit `fly.toml`:
```toml
app = "your-app-n8n"  # Choose unique app name
WEBHOOK_URL = "https://your-app-n8n.fly.dev/"
GENERATION_API_URL = "https://your-generation-api.fly.dev"
```

2. **Create Fly App**

```bash
cd n8n
fly apps create your-app-n8n
```

3. **Create Volume for Data Persistence**

```bash
fly volumes create n8n_data --size 1 --region sjc
```

4. **Set Secrets**

```bash
# Set encryption key for credentials
fly secrets set N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)

# Optional: Set basic auth
fly secrets set N8N_BASIC_AUTH_ACTIVE=true
fly secrets set N8N_BASIC_AUTH_USER=admin
fly secrets set N8N_BASIC_AUTH_PASSWORD=your-secure-password
```

5. **Deploy**

```bash
fly deploy
```

6. **Open n8n**

```bash
fly open
```

## Available API Endpoints

Your generation platform exposes these endpoints for n8n workflows:

### Image Generation
```http
POST /api/v3/generate/image
Content-Type: application/json

{
  "prompt": "A serene mountain landscape",
  "model": "flux",
  "aspect_ratio": "16:9",
  "num_outputs": 1
}
```

### Video Generation
```http
POST /api/v3/generate/video
Content-Type: application/json

{
  "prompt": "Camera panning across the landscape",
  "model": "minimax",
  "image": "https://url-to-first-frame.jpg",
  "duration": 5
}
```

### Video Analysis (Video-to-Text)
```http
POST /api/v3/analyze/video
Content-Type: application/json

{
  "video": "https://url-to-video.mp4",
  "model": "qwen2-vl",
  "prompt": "Describe this video in detail"
}

# Or add captions
{
  "video": "https://url-to-video.mp4",
  "model": "tiktok-short-captions",
  "font": "Arial",
  "fontsize": 48
}
```

### Audio Generation
```http
POST /api/v3/generate/audio
Content-Type: application/json

{
  "prompt": "Upbeat electronic music with drums",
  "model": "musicgen",
  "duration": 8
}
```

### Image Processing
```http
POST /api/v3/process/utility
Content-Type: application/json

{
  "tool": "upscale",
  "image": "https://url-to-image.jpg",
  "scale": 2,
  "creativity": 0.35
}
```

**Available Tools:**
- `upscale` - AI upscaling
- `remove-background` - Background removal
- `restore-face` - Face enhancement

### Task Management
```http
# Check status
GET /api/v3/tasks/{task_id}

# Get result (when completed)
GET /api/v3/tasks/{task_id}/result

# Cancel task
POST /api/v3/tasks/{task_id}/cancel
```

## Building Workflows in n8n

### Basic Pattern

Every generation request follows this pattern:

1. **HTTP Request** - Submit generation task
   - Returns: `{id: "task-uuid", status: "pending"}`

2. **Wait** - Give the model time to process
   - Image: 5-15 seconds
   - Video: 30-120 seconds
   - Audio: 10-30 seconds

3. **HTTP Request** - Get result
   - URL: `/api/v3/tasks/{task_id}/result`
   - Returns: Image/video/audio URL and metadata

### Chaining Generations

To pass outputs between steps:

```
Generate Image
  ↓
Get Result → Store image URL
  ↓
Generate Video (use {{$json.url}} from previous step)
  ↓
Get Video Result
```

### Example: Dynamic Prompt from Previous Step

```javascript
// In HTTP Request Body
{
  "prompt": "{{$node['Set Prompt'].json.prompt}}",
  "image": "{{$node['Get Image'].json.url}}",
  "model": "minimax"
}
```

### Tips for n8n Workflows

1. **Use Set Nodes** - Store variables at the start
   ```
   Set Node → {prompt: "your text", style: "photorealistic"}
   ```

2. **Reference Previous Nodes**
   ```
   {{$node['Node Name'].json.fieldName}}
   ```

3. **Handle Errors**
   - Add "IF" nodes to check status == "succeeded"
   - Add error paths for failed generations

4. **Adjust Wait Times**
   - Different models have different processing times
   - Videos take longer than images
   - Add status polling loops for reliability

## Example Use Cases

### 1. Automated Social Media Posts
```
Generate Image → Upscale → Add to Buffer/Hootsuite
```

### 2. Video Ad Creation
```
Set Campaign Details
  ↓
Generate Product Image
  ↓
Upscale Image
  ↓
Generate Video Animation
  ↓
Add to Google Drive
```

### 3. Music Video Pipeline
```
Generate Audio
  ↓
Generate Images (based on audio vibe)
  ↓
Create Video from Images
  ↓
Combine Audio + Video
```

### 4. Batch Content Generation
```
Read CSV of Prompts
  ↓
Split into Items
  ↓
Generate Image for Each
  ↓
Upscale All
  ↓
Save to Storage
```

## 🚀 Quick Start with Pre-Configured Blocks

**NEW**: We've created pre-configured model blocks so you only need to edit prompts and image URLs!

### Start Here
1. **Import**: `workflows/04-complete-chain-demo.json`
2. **Edit**: Only the "📝 Configure Prompts" node
3. **Run**: Watch it generate image → upscale → create video

See **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** for a cheat sheet.

See **[BLOCKS_GUIDE.md](BLOCKS_GUIDE.md)** for detailed instructions.

## Workflow Templates

### Complete Workflows
Ready-to-use end-to-end workflows:

- **04-complete-chain-demo.json** ⭐ **Start here!**
  - Complete pipeline: Image → Upscale → Video
  - Only edit prompts in one "Set" node
  - Shows URL passing between steps

- **01-simple-image-generation.json**
  - Single image generation with status polling
  - Shows retry pattern with IF nodes

- **02-image-to-video-pipeline.json**
  - Generate image, then animate it into video
  - Shows chaining pattern

- **03-image-upscale-enhance.json**
  - Generate → Upscale → Face enhancement
  - Shows parallel processing branches

### Model Blocks (Building Blocks)
Pre-configured blocks in `workflows/blocks/` - mix and match these:

**Image Generation:**
- `image-flux-schnell.json` - Fast, high-quality images

**Video Generation:**
- `video-minimax.json` - Image to video (MiniMax)
- `video-luma.json` - Image to video with loop option (Luma)

**Audio:**
- `audio-musicgen.json` - Generate music from text

**Utilities:**
- `utility-upscale.json` - AI upscaling (2x or 4x)

**Video Analysis (Video-to-Text):**
- `video-analysis-qwen.json` - Generate text descriptions from video
- `video-captions-tiktok.json` - Add TikTok-style captions to video

## Advanced: Custom n8n Nodes

To create custom nodes for your API:

1. Create node in `custom-nodes/` directory
2. Follow [n8n node development guide](https://docs.n8n.io/integrations/creating-nodes/)
3. Mount in docker-compose:
   ```yaml
   volumes:
     - ./custom-nodes:/home/node/.n8n/custom
   ```

## Troubleshooting

### n8n can't reach API

**Local Development:**
- Use `http://host.docker.internal:9090` instead of `localhost:9090`
- Or add API service to docker-compose network

**Production:**
- Ensure API URL is correct in fly.toml
- Check firewall rules between services

### Workflows time out

- Increase wait times for video generation (60-120s)
- Add status polling loops instead of fixed waits
- Check API logs for errors

### Tasks stuck in "processing"

- Check Replicate API key is set
- Verify model names match registry
- Check API logs: `tail -f /tmp/server.log`

## Security

### Production Checklist

- [ ] Enable n8n basic auth or SSO
- [ ] Use HTTPS for all connections
- [ ] Rotate N8N_ENCRYPTION_KEY regularly
- [ ] Limit network access to n8n UI
- [ ] Review workflow permissions
- [ ] Enable audit logging

### Environment Variables

```bash
# Required
N8N_ENCRYPTION_KEY=<generate-secure-key>

# Authentication (recommended)
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure-password

# Or use advanced auth
N8N_USER_MANAGEMENT_JWT_SECRET=<jwt-secret>
```

## Resources

- [n8n Documentation](https://docs.n8n.io)
- [n8n Community Forum](https://community.n8n.io)
- [Workflow Examples](https://n8n.io/workflows)
- [Generation API Docs](../backend/README.md)

## Support

For issues with:
- n8n setup → Check [n8n docs](https://docs.n8n.io)
- API integration → Check API logs and endpoint docs
- Workflows → Import examples and modify incrementally
