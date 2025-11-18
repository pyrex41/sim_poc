# n8n Model Blocks Guide

This guide shows you how to use pre-configured model blocks to build AI generation workflows without writing JSON.

## Quick Start

### 1. Import a Complete Workflow

The easiest way to get started is to import a complete workflow:

```bash
# Import the complete chain demo
workflows/04-complete-chain-demo.json
```

This workflow shows:
- Image generation (Flux)
- Image upscaling
- Video generation (MiniMax)
- Proper URL passing between steps

**You only need to edit the "📝 Configure Prompts" node!**

## Pre-Configured Model Blocks

Each block is a ready-to-use workflow snippet. Just import, edit prompts, and run.

### 🎨 Image Generation Blocks

#### Flux Schnell (Fast & High Quality)
- **File**: `blocks/image-flux-schnell.json`
- **Edit in "Set Image Parameters" node**:
  - `prompt`: Your image description
  - `aspect_ratio`: "16:9", "1:1", "4:3", "9:16"
  - `num_outputs`: Number of images (1-4)
- **Output**: `$json.url` contains image URL

#### Available Models:
- `flux` - Fast, high quality (recommended)
- `flux-pro` - Premium quality, more control
- `sdxl` - Stable Diffusion XL

### 🎬 Video Generation Blocks

#### MiniMax Video-01
- **File**: `blocks/video-minimax.json`
- **Edit in "Set Video Parameters" node**:
  - `prompt`: Motion/camera description
  - `image_url`: First frame (from previous step)
- **Output**: `$json.url` contains video URL

#### Luma Ray
- **File**: `blocks/video-luma.json`
- **Edit in "Set Video Parameters" node**:
  - `prompt`: Motion description
  - `image_url`: Starting image
  - `duration`: 5 or 10 seconds
  - `loop`: true/false for seamless loop
- **Output**: `$json.url` contains video URL

### ⚡ Utility Blocks

#### Upscale Image
- **File**: `blocks/utility-upscale.json`
- **Edit in "Set Upscale Parameters" node**:
  - `image_url`: Image to upscale
  - `scale`: 2 or 4x
  - `creativity`: 0-1 (higher = more AI enhancement)
  - `dynamic`: 0-10 (detail enhancement)
- **Output**: `$json.output_url` contains upscaled image

## Passing Data Between Steps

### Pattern 1: Direct Reference (Simple)

When steps are directly connected, use `$json.url`:

```json
{
  "prompt": "Your prompt",
  "image": "{{$json.url}}"
}
```

### Pattern 2: Named Node Reference (Complex Workflows)

When referencing a node that's not directly before:

```json
{
  "prompt": "{{$node['Set Prompt'].json.prompt}}",
  "image": "{{$node['Get Image'].json.url}}"
}
```

### Pattern 3: Utility Output URLs

Utilities return `output_url` instead of `url`:

```json
{
  "image": "{{$json.output_url}}"
}
```

## Building Custom Workflows

### Example: Multiple Video Variants from One Image

1. **Import**: `blocks/image-flux-schnell.json`
2. **After "Get Image URL"**, add parallel video blocks:
   - `blocks/video-minimax.json` (connected to Get Image)
   - `blocks/video-luma.json` (connected to Get Image)

Both video blocks will use the same source image but create different videos.

### Example: Batch Process Multiple Images

1. Start with a CSV file of prompts
2. Use "Split in Batches" node
3. For each batch item:
   - Generate image
   - Upscale
   - Generate video
4. Merge results

## Available Model Parameters

### Image Generation (All Models)

**Required:**
- `prompt`: Text description

**Common Optional:**
- `aspect_ratio`: "16:9", "1:1", "4:3", "9:16"
- `num_outputs`: 1-4
- `seed`: For reproducibility

**Flux Specific:**
- `go_fast`: true/false (speed vs quality)
- `megapixels`: "1" or "0.25"

**SDXL Specific:**
- `negative_prompt`: What to avoid
- `guidance_scale`: 1-20 (prompt adherence)
- `num_inference_steps`: 20-100 (quality)

### Video Generation

**MiniMax:**
- `prompt`: Motion/camera description (required)
- `image`: First frame URL (optional)
- `prompt_optimizer`: true/false (AI prompt enhancement)

**Luma Ray:**
- `prompt`: Motion description (required)
- `image`: Starting frame URL (optional)
- `duration`: 5 or 10 seconds
- `loop`: true/false

### Utilities

**Upscale:**
- `image`: Source image URL (required)
- `scale`: 2 or 4
- `creativity`: 0.0-1.0 (AI enhancement level)
- `dynamic`: 0-10 (detail enhancement)
- `sharpen`: 0-10 (sharpening level)

**Remove Background:**
- `image`: Source image URL (required)
- `model`: "u2net", "u2netp", "u2net_human_seg"

**Restore Face:**
- `image`: Source image URL (required)
- `scale`: 1-4 (upscale factor)
- `version`: "v1.2", "v1.3", "v1.4"

## URL Extraction Pattern

All n8n workflows follow this pattern:

1. **Submit Task** → Returns `{id: "task-uuid"}`
2. **Wait** → Give model time to process
3. **Get Result** → Fetch from `/api/v3/tasks/{id}/result`

The result contains:
- Image generation: `url` field
- Video generation: `url` field
- Utilities: `output_url` field

## Tips & Best Practices

### 1. Use Set Nodes for Configuration

Always start with a "Set" node containing all your prompts and parameters:

```
Set Node → Generate → Wait → Get Result
```

This makes it easy to change prompts without editing HTTP request bodies.

### 2. Add Notes to Nodes

Click on a node → Add Note to document:
- What the node does
- What data it outputs
- Any special considerations

### 3. Adjust Wait Times

Default wait times:
- Images: 10 seconds
- Video: 60 seconds
- Upscale: 15 seconds

If tasks fail, increase wait time or add status polling (see workflow 01).

### 4. Handle Multiple Image Inputs

Some models accept multiple images. Use an array in the Set node:

```json
{
  "name": "images",
  "value": "={{[$node['Image 1'].json.url, $node['Image 2'].json.url]}}"
}
```

### 5. Error Handling

Add "IF" nodes to check status:

```
Get Result → IF (status == "succeeded") → Continue
                                        → Retry/Error
```

## Model Selection Cheat Sheet

**Need fast images?** → Flux Schnell
**Need best quality images?** → Flux Pro
**Need open source images?** → SDXL

**Need video from image?** → MiniMax or Luma
**Need seamless loop video?** → Luma (with loop=true)
**Need video from multiple images?** → SkyReels

**Need to upscale?** → Clarity Upscaler
**Need transparent background?** → Remove Background
**Need face enhancement?** → Restore Face

## Troubleshooting

### "The service refused the connection"

**Problem**: n8n can't reach the API
**Solution**: Ensure URLs use `http://host.docker.internal:9090` (not localhost)

### "Task status is still processing"

**Problem**: Wait time too short
**Solution**: Increase wait time or add retry loop

### "Image URL not found"

**Problem**: Trying to use `url` instead of `output_url` for utilities
**Solution**: Check which field the previous step returns

### "Expression error"

**Problem**: Incorrect n8n expression syntax
**Solution**:
- Use `={{}}` for expressions
- Use `$json.field` for current node data
- Use `$node['Node Name'].json.field` for other nodes

## Next Steps

1. **Import** `04-complete-chain-demo.json` to see everything working
2. **Edit** the "📝 Configure Prompts" node with your own prompts
3. **Run** the workflow and see the magic happen
4. **Customize** by adding/removing steps
5. **Build** your own workflows using the block patterns

For more advanced usage, see the main [n8n README](README.md).
