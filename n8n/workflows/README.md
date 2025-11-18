# n8n Workflows Directory

This directory contains pre-configured n8n workflows for AI generation.

## 📁 Directory Structure

```
workflows/
├── 01-simple-image-generation.json       # Learning: Basic image generation
├── 02-image-to-video-pipeline.json       # Learning: Chaining models
├── 03-image-upscale-enhance.json         # Learning: Parallel processing
├── 04-complete-chain-demo.json           # ⭐ START HERE - Complete pipeline
│
└── blocks/                                # Building blocks (copy/paste)
    ├── image-flux-schnell.json           # Fast image generation
    ├── video-minimax.json                # Image to video
    ├── video-luma.json                   # Image to video (with loop)
    ├── audio-musicgen.json               # Music generation
    └── utility-upscale.json              # Image upscaling
```

## 🚀 How to Use

### Option 1: Use Complete Workflow (Easiest)
1. Import `04-complete-chain-demo.json`
2. Click on "📝 Configure Prompts" node
3. Edit `image_prompt` and `video_prompt`
4. Click "Execute Workflow"
5. Done! You get image → upscaled → video

### Option 2: Build Custom Workflow
1. Create new workflow in n8n
2. Import blocks from `blocks/` directory
3. Connect them together
4. Edit the "Set Parameters" nodes
5. Run your custom pipeline

## 📚 Documentation

- **[QUICK_REFERENCE.md](../QUICK_REFERENCE.md)** - Cheat sheet for parameters
- **[BLOCKS_GUIDE.md](../BLOCKS_GUIDE.md)** - Detailed guide
- **[README.md](../README.md)** - Main n8n documentation

## 🎯 What Each File Does

### Complete Workflows

**04-complete-chain-demo.json** ⭐
- Generates image from prompt
- Upscales it 2x
- Creates video from upscaled image
- **Edit only**: "📝 Configure Prompts" node

**01-simple-image-generation.json**
- Shows status polling pattern
- Has retry logic with IF nodes
- Good for learning the basics

**02-image-to-video-pipeline.json**
- Image generation → Video generation
- Shows how to pass image URLs between steps

**03-image-upscale-enhance.json**
- Parallel processing demo
- Image → [Upscale | Face Restore] simultaneously

### Building Blocks

All blocks follow same pattern:
```
Set Parameters → Generate/Process → Wait → Get Result
```

You only edit the "Set Parameters" node!

## 🔗 Connecting Blocks

To pass image URLs between blocks:

```javascript
// For direct connections
{{$json.url}}

// For utilities (upscale, etc)
{{$json.output_url}}

// From named node
{{$node['Get Image'].json.url}}
```

## ⚡ Quick Examples

### Parallel Video Generation
```
Generate Image → Get Image URL ┬→ MiniMax Video
                               └→ Luma Video
```
Create two different video styles from one image!

### Batch Upscaling
```
Split Images → For Each ┬→ Upscale
                        └→ Get Result → Merge
```

### Music Video Creation
```
Generate Audio → Get Audio URL
                      ↓
Generate Image → Get Image URL
                      ↓
          Generate Video
```

## 🎨 Available Models

**Images**: flux, flux-pro, sdxl
**Video**: minimax, luma
**Audio**: musicgen, bark
**Utilities**: upscale, remove-background, restore-face

See [BLOCKS_GUIDE.md](../BLOCKS_GUIDE.md) for full parameter lists.
