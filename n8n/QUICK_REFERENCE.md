# n8n Model Blocks - Quick Reference

## 📋 Import These Files

### Ready-to-Use Workflows
| File | What It Does | Edit This |
|------|--------------|-----------|
| `04-complete-chain-demo.json` | Image → Upscale → Video | "📝 Configure Prompts" node |

### Individual Model Blocks (Copy/Paste into Workflows)
| Block | Model | Edit Node | Output Field |
|-------|-------|-----------|--------------|
| `blocks/image-flux-schnell.json` | Flux (fast) | "Set Image Parameters" | `$json.url` |
| `blocks/video-minimax.json` | MiniMax Video | "Set Video Parameters" | `$json.url` |
| `blocks/video-luma.json` | Luma Ray | "Set Video Parameters" | `$json.url` |
| `blocks/utility-upscale.json` | Upscale 2x/4x | "Set Upscale Parameters" | `$json.output_url` |
| `blocks/audio-musicgen.json` | Music Generation | "Set Audio Parameters" | `$json.url` |
| `blocks/video-analysis-qwen.json` | Video to Text | "Set Analysis Parameters" | `$json.text` |
| `blocks/video-captions-tiktok.json` | TikTok Captions | "Set Caption Parameters" | `$json.video_url` |

## 🔗 Passing URLs Between Steps

```javascript
// Current step's output
{{$json.url}}

// Named node's output
{{$node['Get Image'].json.url}}

// Utility outputs use different field
{{$json.output_url}}

// Multiple images (array)
{{[$node['Image 1'].json.url, $node['Image 2'].json.url]}}
```

## ⏱️ Wait Times

| Type | Recommended Wait | Why |
|------|------------------|-----|
| Image | 10 seconds | Fast models |
| Video | 60-120 seconds | Slow models |
| Upscale | 15 seconds | Depends on size |
| Audio | 20 seconds | Depends on duration |

## 📝 Common Parameters

### Image Generation
```javascript
{
  "prompt": "Your description",
  "model": "flux",              // flux, flux-pro, sdxl
  "aspect_ratio": "16:9",      // 16:9, 1:1, 4:3, 9:16
  "num_outputs": 1             // 1-4
}
```

### Video Generation
```javascript
{
  "prompt": "Motion description",
  "model": "minimax",           // minimax, luma
  "image": "{{$json.url}}",    // Starting frame
  "duration": 5                 // 5 or 10 seconds (Luma only)
}
```

### Upscale
```javascript
{
  "tool": "upscale",
  "image": "{{$json.url}}",
  "scale": 2,                   // 2 or 4
  "creativity": 0.35,          // 0-1
  "dynamic": 6                  // 0-10
}
```

### Audio
```javascript
{
  "prompt": "Music description",
  "model": "musicgen",
  "model_version": "large",     // small, medium, large, melody
  "duration": 8                 // seconds
}
```

### Video Analysis (Video-to-Text)
```javascript
{
  "video": "{{$json.url}}",     // Video URL
  "model": "qwen2-vl",          // qwen2-vl, tiktok-short-captions, autocaption
  "prompt": "Describe this video" // What to ask about the video
}
```

**Output varies by model:**
- Text description models → `$json.text`
- Caption overlay models → `$json.video_url` (video with captions)

## 🚨 Common Errors & Fixes

| Error | Fix |
|-------|-----|
| "Service refused connection" | Change `localhost:9090` to `host.docker.internal:9090` |
| "Task still processing" | Increase wait time or add retry loop |
| "Cannot read property 'url'" | Check if using `url` vs `output_url` |
| "Expression error" | Wrap expressions in `={{  }}` |

## 🎯 Model Selection

**Fast Images** → Flux Schnell
**Best Images** → Flux Pro
**Image → Video** → MiniMax or Luma
**Looping Video** → Luma (set `loop: true`)
**Upscale** → Clarity Upscaler
**Music** → MusicGen (large)
**Background Removal** → RemBG
**Face Fix** → GFPGAN
**Video Description** → Qwen2-VL
**Auto Captions** → TikTok Captions

## 🔧 Build Patterns

### Pattern 1: Simple Chain
```
Set Params → Generate → Wait → Get Result
```

### Pattern 2: Parallel Processing
```
Get Image ┬→ Upscale → Get Upscaled
          └→ Remove BG → Get Clean
```

### Pattern 3: Loop/Retry
```
Generate → Wait → Check Status → IF succeeded → Result
                                → IF failed → Wait (loop back)
```

## 📥 How to Use Blocks

1. **Open n8n** at `http://localhost:5678`
2. **Create New Workflow**
3. **Click Menu** → "Import from File"
4. **Select block** from `workflows/blocks/`
5. **Edit the "Set Parameters" node** with your values
6. **Connect** to other blocks if needed
7. **Execute** and watch it work

That's it! Start with `04-complete-chain-demo.json` to see everything working together.
