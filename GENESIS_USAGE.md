# Genesis Photorealistic Rendering - Usage Guide

## Overview

Your simulation platform now supports **LLM-augmented photorealistic rendering** with Genesis! This hybrid architecture lets you:

1. **Interactively edit scenes** with simple shapes (boxes, spheres, cylinders) using Rapier.js in the browser
2. **Describe objects semantically** with text (e.g., "blue corvette", "light pole")
3. **Render photorealistic videos** using Genesis ray-tracer with LLM property augmentation
4. **Optionally stylize** the output further with Veo 3.1

## Architecture

```
Browser (Rapier.js + Three.js)
   ↓ User manipulates simple shapes + adds descriptions
Scene JSON with Text Annotations
   ↓
Backend LLM (Claude Sonnet 4.5)
   → Interprets descriptions
   → Generates PBR properties (materials, colors, scales)
   ↓
Genesis Ray-Tracer
   → Applies augmented properties
   → Renders photorealistic video
   ↓
MP4 Output → (Optional: Veo 3.1 stylization)
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `genesis-world==0.3.7` - Physics simulation and ray-tracing
- `anthropic>=0.18.0` - LLM for semantic augmentation

**Requirements:**
- Python 3.9+
- CUDA-capable GPU (for ray-tracing)
- Ubuntu 22.04 recommended (or Docker)

### 2. Set Environment Variables

Create/update `.env` file:

```bash
ANTHROPIC_API_KEY=your_claude_api_key_here
REPLICATE_API_KEY=your_replicate_key_here  # Optional, for Veo
```

### 3. Start the Backend

```bash
cd backend
python main.py
```

The server starts on `http://127.0.0.1:8000`

### 4. Use the Frontend

```bash
npm run dev
```

Open `http://localhost:5173`

## Workflow Example

### Step 1: Create Simple Scene

1. Open the browser UI
2. Add objects (boxes, spheres, cylinders)
3. Position and scale them with Rapier.js physics controls
4. Test physics interactions in real-time

### Step 2: Add Semantic Descriptions

For each object, add a text description in the **"Description (for Genesis)"** field:

**Examples:**
- Box → `"blue corvette sports car"`
- Cylinder → `"street light pole"`
- Sphere → `"soccer ball with black and white pattern"`
- Box → `"wooden coffee table with dark walnut finish"`
- Cylinder → `"fire hydrant, red and weathered"`

**Tips:**
- Be specific about colors, materials, and details
- Include texture info ("metallic", "glossy", "weathered")
- Mention key features ("car wheels", "light bulb", "wood grain")

### Step 3: Render with Genesis

Call the Genesis API endpoint:

```typescript
// Frontend example (add to your Elm port or JS)
const renderWithGenesis = async (scene) => {
  const response = await fetch('http://127.0.0.1:8000/api/genesis/render', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scene: scene,
      duration: 5.0,        // Video duration in seconds
      fps: 60,              // Frames per second
      resolution: [1920, 1080],
      quality: 'high',      // 'draft', 'high', or 'ultra'
      scene_context: 'urban street scene at sunset'  // Optional context
    })
  });

  const result = await response.json();
  console.log('Video ready:', result.video_url);

  // Display video
  videoElement.src = result.video_url;
};
```

Or use curl:

```bash
curl -X POST http://127.0.0.1:8000/api/genesis/render \
  -H "Content-Type: application/json" \
  -d @scene.json
```

### Step 4: Results

You'll receive:

```json
{
  "success": true,
  "video_path": "./backend/DATA/genesis_videos/genesis_render_1234567890.mp4",
  "video_url": "/data/genesis_videos/genesis_render_1234567890.mp4",
  "quality": "high",
  "duration": 5.0,
  "fps": 60
}
```

The video will show:
- Your physics simulation with accurate motion
- Photorealistic appearance based on text descriptions
- Professional lighting and materials

## Quality Presets

### Draft (SPP=64)
- **Use case:** Quick previews
- **Speed:** ~30 seconds/frame
- **Quality:** Some noise, but fast

### High (SPP=256) ⭐ Default
- **Use case:** Production rendering
- **Speed:** ~2 minutes/frame
- **Quality:** Clean, photorealistic

### Ultra (SPP=512)
- **Use case:** Final export, maximum quality
- **Speed:** ~4 minutes/frame
- **Quality:** Pristine, minimal noise

**Example:**

```json
{
  "quality": "draft"  // For quick iteration
}
```

## LLM Semantic Augmentation

The LLM interpreter (Claude Sonnet 4.5) generates:

### PBR Properties
- **Color:** RGB values based on description
- **Metallic:** 0.0 (wood) to 1.0 (chrome)
- **Roughness:** 0.0 (mirror) to 1.0 (concrete)
- **Opacity:** For glass, transparent materials

### Geometry Adjustments
- **Scale multipliers:** Adjust proportions (e.g., car is wider, lower, longer)
- **Suggested dimensions:** Real-world sizes in meters

### Material Types
- Metal (car body, light pole)
- Plastic (chairs, toys)
- Wood (furniture)
- Glass (windows, bottles)
- Fabric (upholstery)
- Concrete (building materials)

### Detail Annotations
The LLM notes what details to emphasize:
- Car: "wheels", "headlights", "spoiler"
- Light pole: "light_bulb", "base_plate", "electrical_box"
- Table: "wood_grain", "table_legs", "surface_reflection"

## Advanced Configuration

### Custom Camera Settings

```json
{
  "camera_config": {
    "position": [8, 6, 8],     // Camera position in 3D
    "lookat": [0, 2, 0],        // Look-at target
    "fov": 40,                  // Field of view (degrees)
    "aperture": 2.8             // Depth-of-field (lower = more blur)
  }
}
```

### Scene Context

Provide overall scene description for better LLM interpretation:

```json
{
  "scene_context": "urban street scene at golden hour with warm lighting"
}
```

This helps the LLM understand:
- Lighting conditions
- Environment (indoor/outdoor)
- Time of day
- Weather effects

## File Structure

```
backend/
├── genesis_renderer.py      # Main renderer orchestration
├── llm_interpreter.py        # Claude-powered semantic augmentation
├── scene_converter.py        # JSON → Genesis entity conversion
├── main.py                   # API endpoint: /api/genesis/render
└── DATA/
    └── genesis_videos/       # Rendered output videos

src/
└── Main.elm                  # Frontend with description fields
```

## API Reference

### POST /api/genesis/render

**Request Body:**

```typescript
{
  scene: {
    objects: {
      [objectId: string]: {
        id: string
        transform: { position, rotation, scale }
        physicsProperties: { mass, friction, restitution }
        visualProperties: { color, shape }
        description?: string  // ⭐ New field for semantic rendering
      }
    },
    selectedObject?: string
  },
  duration?: number = 5.0
  fps?: number = 60
  resolution?: [number, number] = [1920, 1080]
  quality?: 'draft' | 'high' | 'ultra' = 'high'
  camera_config?: {
    position?: [number, number, number]
    lookat?: [number, number, number]
    fov?: number
    aperture?: number
  }
  scene_context?: string
}
```

**Response:**

```typescript
{
  success: boolean
  video_path: string
  video_url: string
  quality: string
  duration: number
  fps: number
}
```

## Performance Tips

### 1. Use Draft for Iteration

During scene setup:
```json
{"quality": "draft"}  // Fast feedback loop
```

For final export:
```json
{"quality": "high"}   // Clean output
```

### 2. Batch Multiple Scenes

Genesis supports parallel rendering across multiple GPUs. Consider batch processing:

```bash
for scene in scenes/*.json; do
  curl -X POST ... -d @$scene &
done
wait
```

### 3. Optimize Video Length

- **Short clips (3-5s):** Better for iteration
- **Long videos (30s+):** Use lower FPS (30fps) or draft quality

### 4. GPU Memory

Ray-tracing is memory-intensive:
- **8GB VRAM:** Draft/High quality OK
- **16GB+ VRAM:** Ultra quality supported
- **Low memory?** Reduce resolution to 1280x720

## Troubleshooting

### Error: "Genesis not available"

```
pip install genesis-world==0.3.7
```

Check CUDA installation:
```bash
nvcc --version
nvidia-smi
```

### Error: "ANTHROPIC_API_KEY not set"

Update `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### Slow Rendering

- Use `quality: "draft"` for testing
- Reduce `duration` to 3 seconds
- Lower `resolution` to [1280, 720]

### Objects Look Wrong

- Improve text descriptions (more specific)
- Add `scene_context` for environment understanding
- Check that base shapes match object type (cylinder for pole, box for car)

## Integration with Veo 3.1

Genesis output can be fed into Veo for further stylization:

```
Genesis (Photorealistic Reference)
   → Physically accurate motion
   → Realistic lighting and materials
   ↓
Veo 3.1 (Stylization)
   → Artistic style transfer
   → Prompt-based modifications
   → Final output
```

**Workflow:**
1. Render with Genesis: `/api/genesis/render`
2. Use Genesis video as motion reference for Veo
3. Apply Veo prompt: "make it look like a Pixar animation"

## Example Scenes

### Car Chase Scene

```json
{
  "objects": {
    "car1": {
      "id": "car1",
      "transform": { "position": {"x": 0, "y": 1, "z": 0}, ... },
      "visualProperties": { "color": "#0047AB", "shape": "Box" },
      "description": "blue corvette sports car with chrome wheels"
    },
    "pole": {
      "id": "pole",
      "transform": { "position": {"x": 5, "y": 4, "z": 0}, ... },
      "visualProperties": { "color": "#808080", "shape": "Cylinder" },
      "description": "street light pole, galvanized steel, weathered"
    }
  }
}
```

### Living Room

```json
{
  "objects": {
    "table": {
      "visualProperties": { "color": "#8B4513", "shape": "Box" },
      "description": "wooden coffee table, walnut finish, polished"
    },
    "lamp": {
      "visualProperties": { "color": "#FFD700", "shape": "Sphere" },
      "description": "table lamp with warm yellow light bulb"
    }
  }
}
```

## Future Enhancements

- **Batch rendering UI:** Queue multiple scenes
- **Live preview:** Real-time ray-tracing preview (lower quality)
- **Asset library:** Pre-built objects (cars, furniture, etc.)
- **Genesis generative framework:** When released, add prompt-to-scene

## Support

For issues:
1. Check [Genesis documentation](https://genesis-world.readthedocs.io/)
2. Verify CUDA and GPU drivers
3. Test with simple scenes first (1-2 objects)
4. Review backend logs for detailed errors

---

**Happy rendering! 🎬✨**
