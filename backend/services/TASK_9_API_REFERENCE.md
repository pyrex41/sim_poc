# Task 9 API Reference: Video Export and Storyboard Refinement

## Quick Reference

### 1. Export Video
```bash
GET /api/v2/jobs/{job_id}/export?format=mp4&quality=medium
```

**Authentication:** Required

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v2/jobs/123/export?format=mp4&quality=high" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o video.mp4
```

---

### 2. Refine Scene
```bash
POST /api/v2/jobs/{job_id}/refine?scene_number=2&new_image_prompt=YOUR_PROMPT
```

**Authentication:** Required

**Example - Regenerate Image:**
```bash
curl -X POST "http://localhost:8000/api/v2/jobs/123/refine" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "?scene_number=2&new_image_prompt=A%20beautiful%20sunset%20over%20mountains%20with%20dramatic%20clouds"
```

**Example - Update Description:**
```bash
curl -X POST "http://localhost:8000/api/v2/jobs/123/refine" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "?scene_number=3&new_description=The%20hero%20discovers%20a%20hidden%20treasure"
```

**Example - Both:**
```bash
curl -X POST "http://localhost:8000/api/v2/jobs/123/refine" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "?scene_number=1&new_image_prompt=Epic%20opening%20shot&new_description=Opening%20scene"
```

---

### 3. Reorder Scenes
```bash
POST /api/v2/jobs/{job_id}/reorder?scene_order=1&scene_order=3&scene_order=2&scene_order=4
```

**Authentication:** Required

**Example:**
```bash
# Original order: [1, 2, 3, 4]
# New order: [1, 3, 2, 4] (swap scenes 2 and 3)
curl -X POST "http://localhost:8000/api/v2/jobs/123/reorder" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "?scene_order=1&scene_order=3&scene_order=2&scene_order=4"
```

---

### 4. Get Metadata
```bash
GET /api/v2/jobs/{job_id}/metadata
```

**Authentication:** Not required (public)

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v2/jobs/123/metadata"
```

**Response:**
```json
{
  "job_id": 123,
  "status": "completed",
  "created_at": "2025-11-15T10:00:00",
  "updated_at": "2025-11-15T10:05:00",
  "approved": true,
  "approved_at": "2025-11-15T10:04:00",
  "scenes": {
    "total": 6,
    "completed": 6,
    "failed": 0,
    "details": [...]
  },
  "costs": {
    "estimated": 0.15,
    "actual": 0.12,
    "currency": "USD"
  },
  "metrics": {
    "refinement_count": 2,
    "download_count": 5
  },
  "video": {
    "available": true,
    "url": "/data/videos/123/final.mp4",
    "parameters": {...}
  },
  "error": null
}
```

---

## Complete Workflow Example

### 1. Create Job
```bash
curl -X POST "http://localhost:8000/api/v2/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A hero discovers a hidden treasure in ancient ruins",
    "duration": 30,
    "style": "cinematic",
    "aspect_ratio": "16:9"
  }'
```

**Response:**
```json
{
  "job_id": 123,
  "status": "pending",
  ...
}
```

---

### 2. Check Status
```bash
curl -X GET "http://localhost:8000/api/v2/jobs/123"
```

Wait until status is `storyboard_ready`.

---

### 3. Review Storyboard
```bash
curl -X GET "http://localhost:8000/api/v2/jobs/123" | jq '.storyboard'
```

**Response:**
```json
[
  {
    "scene": {
      "scene_number": 1,
      "description": "Hero enters ancient ruins",
      "duration": 5.0,
      "image_prompt": "A brave hero entering mysterious ancient ruins..."
    },
    "image_url": "https://replicate.delivery/...",
    "generation_status": "completed",
    "error": null
  },
  ...
]
```

---

### 4. Refine Scene (Optional)
```bash
# Refine scene 2 with better image prompt
curl -X POST "http://localhost:8000/api/v2/jobs/123/refine" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "?scene_number=2&new_image_prompt=Dramatic%20wide%20shot%20of%20ancient%20temple"
```

**Note:** This resets the `approved` flag, requiring re-approval.

---

### 5. Reorder Scenes (Optional)
```bash
# Swap scenes 2 and 3
curl -X POST "http://localhost:8000/api/v2/jobs/123/reorder" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "?scene_order=1&scene_order=3&scene_order=2&scene_order=4&scene_order=5&scene_order=6"
```

**Note:** This also resets the `approved` flag.

---

### 6. Approve Storyboard
```bash
curl -X POST "http://localhost:8000/api/v2/jobs/123/approve" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 7. Render Video
```bash
curl -X POST "http://localhost:8000/api/v2/jobs/123/render" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Wait until status is `completed`.

---

### 8. Download Video (Original)
```bash
curl -X GET "http://localhost:8000/api/v2/jobs/123/video" \
  -o original_video.mp4
```

---

### 9. Export Video (Different Formats)
```bash
# High quality MP4
curl -X GET "http://localhost:8000/api/v2/jobs/123/export?format=mp4&quality=high" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o video_1080p.mp4

# Low quality WebM (for web)
curl -X GET "http://localhost:8000/api/v2/jobs/123/export?format=webm&quality=low" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o video_web.webm

# Medium quality MOV
curl -X GET "http://localhost:8000/api/v2/jobs/123/export?format=mov&quality=medium" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o video_720p.mov
```

---

### 10. Get Metadata
```bash
curl -X GET "http://localhost:8000/api/v2/jobs/123/metadata" | jq
```

---

## Common Use Cases

### Use Case 1: Client Wants Different Resolution
**Scenario:** Client needs a lower resolution version for social media.

**Solution:**
```bash
# Export low quality (480p) MP4
curl -X GET "http://localhost:8000/api/v2/jobs/123/export?format=mp4&quality=low" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o social_media.mp4
```

---

### Use Case 2: Scene Image Doesn't Match Vision
**Scenario:** Scene 3 image doesn't match what client envisioned.

**Solution:**
```bash
# Refine scene 3 with new prompt
curl -X POST "http://localhost:8000/api/v2/jobs/123/refine" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "?scene_number=3&new_image_prompt=Close-up%20of%20treasure%20chest%20with%20golden%20light"

# Wait for regeneration, then approve again
curl -X POST "http://localhost:8000/api/v2/jobs/123/approve" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Re-render
curl -X POST "http://localhost:8000/api/v2/jobs/123/render" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Use Case 3: Scenes in Wrong Order
**Scenario:** Client wants to swap opening and closing scenes.

**Solution:**
```bash
# Original: [1, 2, 3, 4, 5, 6]
# Desired: [6, 2, 3, 4, 5, 1]
curl -X POST "http://localhost:8000/api/v2/jobs/123/reorder" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "?scene_order=6&scene_order=2&scene_order=3&scene_order=4&scene_order=5&scene_order=1"

# Approve and re-render
curl -X POST "http://localhost:8000/api/v2/jobs/123/approve" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X POST "http://localhost:8000/api/v2/jobs/123/render" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Use Case 4: Track Video Performance
**Scenario:** Check how many times a video has been downloaded.

**Solution:**
```bash
curl -X GET "http://localhost:8000/api/v2/jobs/123/metadata" | jq '.metrics'
```

**Response:**
```json
{
  "refinement_count": 2,
  "download_count": 15
}
```

---

## Error Responses

### Export Errors
```json
// 503 - ffmpeg not available
{
  "detail": "Video export service unavailable (ffmpeg not installed)"
}

// 404 - Video not found
{
  "detail": "Source video file not found"
}

// 400 - Video not ready
{
  "detail": "Video not ready for export. Current status: rendering"
}
```

### Refinement Errors
```json
// 429 - Too many refinements
{
  "detail": "Maximum refinement limit (5) reached for this job"
}

// 400 - Invalid parameters
{
  "detail": "Must provide either new_image_prompt or new_description"
}

// 500 - Image generation failed
{
  "detail": "Failed to regenerate image: API timeout"
}
```

### Reordering Errors
```json
// 400 - Invalid scene numbers
{
  "detail": "Failed to reorder scenes. Check that all scene numbers are valid."
}

// 400 - Empty scene order
{
  "detail": "scene_order cannot be empty"
}
```

---

## Rate Limits

### Refinement Limit
- **Maximum:** 5 refinements per job
- **Scope:** Per job (not per user)
- **Enforcement:** Application level
- **Reset:** Not possible (hard limit)

### Download Tracking
- **Limit:** None (unlimited downloads)
- **Tracking:** Both `/video` and `/export` endpoints
- **Purpose:** Analytics and metrics

---

## Cost Information

### Refinement Costs
Each scene image regeneration:
- **Cost:** ~$0.02 USD
- **Added to:** `estimated_cost`
- **Applies to:** Image regeneration only (not description updates)

### Export Costs
- **Cost:** Free (local processing)
- **Resource:** CPU time for ffmpeg conversion
- **Caching:** Exports are cached and reused

---

## Notes

1. **Authentication:** All write operations (export, refine, reorder) require authentication
2. **Approval Reset:** Refinement and reordering both reset the approval flag
3. **Export Caching:** Exports are cached; same format/quality won't be regenerated
4. **ffmpeg Requirement:** Export endpoints require ffmpeg to be installed on the server
5. **Local Videos Only:** Export only works for locally stored videos (not remote URLs)
6. **Scene Numbers:** Always 1-indexed (first scene is 1, not 0)
7. **Download Tracking:** Happens automatically on every video access

---

## Python Client Example

```python
import requests

API_BASE = "http://localhost:8000"
TOKEN = "your_auth_token"

def export_video(job_id, format="mp4", quality="medium"):
    """Export a completed video."""
    response = requests.get(
        f"{API_BASE}/api/v2/jobs/{job_id}/export",
        params={"format": format, "quality": quality},
        headers={"Authorization": f"Bearer {TOKEN}"},
        stream=True
    )

    if response.status_code == 200:
        with open(f"video_{job_id}.{format}", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Video exported to video_{job_id}.{format}")
    else:
        print(f"Export failed: {response.json()}")

def refine_scene(job_id, scene_number, new_prompt=None, new_description=None):
    """Refine a scene in the storyboard."""
    params = {"scene_number": scene_number}

    if new_prompt:
        params["new_image_prompt"] = new_prompt
    if new_description:
        params["new_description"] = new_description

    response = requests.post(
        f"{API_BASE}/api/v2/jobs/{job_id}/refine",
        params=params,
        headers={"Authorization": f"Bearer {TOKEN}"}
    )

    return response.json()

def reorder_scenes(job_id, scene_order):
    """Reorder scenes in the storyboard."""
    params = [("scene_order", scene_num) for scene_num in scene_order]

    response = requests.post(
        f"{API_BASE}/api/v2/jobs/{job_id}/reorder",
        params=params,
        headers={"Authorization": f"Bearer {TOKEN}"}
    )

    return response.json()

def get_metadata(job_id):
    """Get comprehensive job metadata."""
    response = requests.get(f"{API_BASE}/api/v2/jobs/{job_id}/metadata")
    return response.json()

# Usage examples
if __name__ == "__main__":
    job_id = 123

    # Export in multiple formats
    export_video(job_id, format="mp4", quality="high")
    export_video(job_id, format="webm", quality="low")

    # Refine scene 2
    result = refine_scene(
        job_id,
        scene_number=2,
        new_prompt="Dramatic wide shot of ancient temple with golden light"
    )
    print(f"Refinement result: {result['status']}")

    # Reorder scenes (swap 2 and 3)
    result = reorder_scenes(job_id, [1, 3, 2, 4, 5, 6])
    print(f"Reorder result: {result['status']}")

    # Get metadata
    metadata = get_metadata(job_id)
    print(f"Downloads: {metadata['metrics']['download_count']}")
    print(f"Refinements: {metadata['metrics']['refinement_count']}")
```

---

## JavaScript/Frontend Example

```javascript
const API_BASE = 'http://localhost:8000';
const TOKEN = 'your_auth_token';

// Export video
async function exportVideo(jobId, format = 'mp4', quality = 'medium') {
  const response = await fetch(
    `${API_BASE}/api/v2/jobs/${jobId}/export?format=${format}&quality=${quality}`,
    {
      headers: {
        'Authorization': `Bearer ${TOKEN}`
      }
    }
  );

  if (response.ok) {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `video_${jobId}.${format}`;
    a.click();
  } else {
    const error = await response.json();
    console.error('Export failed:', error);
  }
}

// Refine scene
async function refineScene(jobId, sceneNumber, newPrompt = null, newDescription = null) {
  const params = new URLSearchParams({ scene_number: sceneNumber });

  if (newPrompt) params.append('new_image_prompt', newPrompt);
  if (newDescription) params.append('new_description', newDescription);

  const response = await fetch(
    `${API_BASE}/api/v2/jobs/${jobId}/refine?${params}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`
      }
    }
  );

  return await response.json();
}

// Reorder scenes
async function reorderScenes(jobId, sceneOrder) {
  const params = new URLSearchParams();
  sceneOrder.forEach(num => params.append('scene_order', num));

  const response = await fetch(
    `${API_BASE}/api/v2/jobs/${jobId}/reorder?${params}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`
      }
    }
  );

  return await response.json();
}

// Get metadata
async function getMetadata(jobId) {
  const response = await fetch(`${API_BASE}/api/v2/jobs/${jobId}/metadata`);
  return await response.json();
}

// Usage
(async () => {
  const jobId = 123;

  // Export video
  await exportVideo(jobId, 'mp4', 'high');

  // Refine scene
  const refinement = await refineScene(
    jobId,
    2,
    'Dramatic wide shot of ancient temple'
  );
  console.log('Refinement:', refinement);

  // Reorder scenes
  const reorder = await reorderScenes(jobId, [1, 3, 2, 4, 5, 6]);
  console.log('Reorder:', reorder);

  // Get metadata
  const metadata = await getMetadata(jobId);
  console.log('Downloads:', metadata.metrics.download_count);
  console.log('Refinements:', metadata.metrics.refinement_count);
})();
```
