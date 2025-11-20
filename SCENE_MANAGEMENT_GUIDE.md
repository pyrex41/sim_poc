# Scene Management Integration Guide

**Last Updated:** 2025-11-19 22:40 UTC
**Status:** ✅ Complete Implementation Guide
**Audience:** Frontend developers integrating scene management features

---

## 📋 Overview

This guide provides comprehensive documentation for integrating the AI-powered scene management system into your frontend application. The system automatically generates video scenes using AI and provides full CRUD operations for scene management.

### What You Can Do

- ✅ Automatically generate 3-7 AI-powered scenes when creating a job
- ✅ View all scenes for a job with complete details
- ✅ Update individual scene properties (description, script, duration, etc.)
- ✅ Regenerate specific scenes with AI using feedback
- ✅ Delete scenes
- ✅ Get scenes included in job status responses

---

## 🚀 Quick Start

###  Step 1: Create a Job (Scenes Generated Automatically)

When you create a job, scenes are now automatically generated using AI:

```typescript
// POST /api/v3/jobs
const response = await fetch('/api/v3/jobs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    context: {
      clientId: "client-123",
      campaignId: "campaign-456"
    },
    adBasics: {
      product: "EcoBottle - Sustainable Water Bottle",
      targetAudience: "Environmentally conscious millennials",
      keyMessage: "Stay hydrated, save the planet",
      callToAction: "Shop Now at ecobottle.com"
    },
    creative: {
      videoSpecs: {
        duration: 30,
        format: "16:9",
        aspectRatio: "horizontal"
      },
      direction: {
        style: "modern",
        tone: "inspiring",
        visualElements: ["nature", "lifestyle", "product shots"]
      },
      assets: [
        { url: "https://example.com/product.jpg", type: "image", name: "Product Shot" },
        { assetId: "existing-asset-123" }
      ]
    }
  })
});

const { data } = await response.json();
// data.scenes will contain 3-7 AI-generated scenes
// data.status will be "storyboard_ready"
```

**Response Structure:**

```typescript
{
  success: true,
  data: {
    id: "789",
    status: "storyboard_ready",
    assetIds: ["asset-001", "asset-002"],
    scenes: [
      {
        sceneNumber: 1,
        duration: 7.0,
        description: "Opening shot of pristine nature - crystal clear water flowing through mountains",
        script: "Imagine a world without plastic waste",
        shotType: "wide",
        transition: "fade",
        assets: ["asset-002"],
        metadata: {}
      },
      {
        sceneNumber: 2,
        duration: 10.0,
        description: "Product showcase in natural setting",
        script: "Meet EcoBottle, your sustainable companion",
        shotType: "close-up",
        transition: "cut",
        assets: ["asset-001"],
        metadata: {}
      },
      // ... more scenes
    ],
    createdAt: "2025-11-19T22:00:00Z",
    updatedAt: "2025-11-19T22:00:05Z"
  }
}
```

---

## 📖 API Reference

### 1. List All Scenes for a Job

Get all scenes for a specific job, ordered by scene number.

```typescript
// GET /api/v3/jobs/{jobId}/scenes
const response = await fetch(`/api/v3/jobs/${jobId}/scenes`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const { data } = await response.json();
// data.scenes = array of scene objects
```

**Response:**

```json
{
  "success": true,
  "data": {
    "scenes": [
      {
        "id": "scene-uuid-001",
        "jobId": 789,
        "sceneNumber": 1,
        "duration": 7.0,
        "description": "Opening shot...",
        "script": "Imagine a world...",
        "shotType": "wide",
        "transition": "fade",
        "assets": ["asset-001"],
        "metadata": {},
        "createdAt": "2025-11-19T22:00:00Z",
        "updatedAt": "2025-11-19T22:00:00Z"
      }
    ]
  }
}
```

### 2. Get a Specific Scene

Retrieve detailed information about a single scene.

```typescript
// GET /api/v3/jobs/{jobId}/scenes/{sceneId}
const response = await fetch(`/api/v3/jobs/${jobId}/scenes/${sceneId}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const { data } = await response.json();
// data = scene object
```

### 3. Update a Scene

Update scene properties. All fields are optional - only include fields you want to change.

```typescript
// PUT /api/v3/jobs/{jobId}/scenes/{sceneId}
const response = await fetch(`/api/v3/jobs/${jobId}/scenes/${sceneId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    description: "Enhanced opening shot with dramatic lighting",
    script: "Imagine a world where nature thrives",
    duration: 8.0,
    shotType: "medium",
    transition: "dissolve",
    assets: ["asset-001", "asset-003"],
    metadata: {
      mood: "dramatic",
      colorPalette: "warm tones",
      musicCue: "uplifting-strings"
    }
  })
});

const { data } = await response.json();
// data = updated scene object
```

**Partial Updates:**

You can update just one field:

```typescript
// Update only the script
await fetch(`/api/v3/jobs/${jobId}/scenes/${sceneId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    script: "New script text only"
  })
});
```

### 4. Regenerate a Scene with AI

Use AI to regenerate a scene with optional feedback and constraints.

```typescript
// POST /api/v3/jobs/{jobId}/scenes/{sceneId}/regenerate
const response = await fetch(`/api/v3/jobs/${jobId}/scenes/${sceneId}/regenerate`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    feedback: "Make this scene more emotional and impactful. Add focus on environmental benefits.",
    constraints: {
      duration: 10.0,  // Keep duration at 10 seconds
      style: "cinematic"
    }
  })
});

const { data } = await response.json();
// data = regenerated scene object
```

**Use Cases for Regeneration:**

- User doesn't like the generated script
- Scene needs different tone or style
- Scene description isn't specific enough
- Need to emphasize different aspects

**Example Feedback Prompts:**

```typescript
// Make it more emotional
{ feedback: "Add more emotional appeal and connect with viewer's feelings about sustainability" }

// Change the focus
{ feedback: "Focus more on the product features rather than environmental messaging" }

// Adjust tone
{ feedback: "Make the tone more playful and fun, less serious" }

// Add specificity
{ feedback: "Include specific product dimensions and features in the description" }
```

### 5. Delete a Scene

Remove a scene from the job. Remaining scenes maintain their scene numbers.

```typescript
// DELETE /api/v3/jobs/{jobId}/scenes/{sceneId}
const response = await fetch(`/api/v3/jobs/${jobId}/scenes/${sceneId}`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});

const { data } = await response.json();
// data.message = "Scene deleted successfully"
```

**Note:** Deleting a scene doesn't renumber remaining scenes. Scene numbers stay as originally generated.

### 6. Get Job Status (Includes Scenes)

The job status endpoint now automatically includes all scenes:

```typescript
// GET /api/v3/jobs/{jobId}
const response = await fetch(`/api/v3/jobs/${jobId}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const { data } = await response.json();
// data.scenes = array of scenes
// data.status = job status (e.g., "storyboard_ready")
```

### 7. Job Actions - Regenerate Scene

Alternative way to regenerate a scene using the job actions endpoint:

```typescript
// POST /api/v3/jobs/{jobId}/actions
const response = await fetch(`/api/v3/jobs/${jobId}/actions`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: "REGENERATE_SCENE",
    sceneId: "scene-uuid-001",
    feedback: "Make it more dramatic",
    constraints: { duration: 8.0 }
  })
});
```

---

## 🎨 Frontend Integration Examples

### React Component Example

```tsx
import { useState, useEffect } from 'react';

interface Scene {
  id: string;
  sceneNumber: number;
  duration: number;
  description: string;
  script: string;
  shotType: string;
  transition: string;
  assets: string[];
  metadata: Record<string, any>;
}

function SceneManager({ jobId, authToken }: { jobId: string; authToken: string }) {
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);

  // Load scenes
  useEffect(() => {
    loadScenes();
  }, [jobId]);

  const loadScenes = async () => {
    const response = await fetch(`/api/v3/jobs/${jobId}/scenes`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    const { data } = await response.json();
    setScenes(data.scenes);
    setLoading(false);
  };

  // Update a scene
  const updateScene = async (sceneId: string, updates: Partial<Scene>) => {
    const response = await fetch(`/api/v3/jobs/${jobId}/scenes/${sceneId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });

    if (response.ok) {
      await loadScenes(); // Reload scenes
    }
  };

  // Regenerate with AI
  const regenerateScene = async (sceneId: string, feedback: string) => {
    setLoading(true);
    const response = await fetch(`/api/v3/jobs/${jobId}/scenes/${sceneId}/regenerate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ feedback })
    });

    if (response.ok) {
      await loadScenes();
    }
    setLoading(false);
  };

  // Delete scene
  const deleteScene = async (sceneId: string) => {
    if (!confirm('Delete this scene?')) return;

    await fetch(`/api/v3/jobs/${jobId}/scenes/${sceneId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${authToken}` }
    });

    await loadScenes();
  };

  if (loading) return <div>Loading scenes...</div>;

  return (
    <div className="scene-manager">
      <h2>Storyboard - {scenes.length} Scenes</h2>
      {scenes.map((scene) => (
        <div key={scene.id} className="scene-card">
          <div className="scene-header">
            <h3>Scene {scene.sceneNumber}</h3>
            <span>{scene.duration}s | {scene.shotType}</span>
          </div>

          <div className="scene-content">
            <p><strong>Description:</strong> {scene.description}</p>
            <p><strong>Script:</strong> "{scene.script}"</p>
            <p><strong>Transition:</strong> {scene.transition}</p>
          </div>

          <div className="scene-actions">
            <button onClick={() => {
              const newScript = prompt('Enter new script:', scene.script);
              if (newScript) updateScene(scene.id, { script: newScript });
            }}>
              Edit Script
            </button>

            <button onClick={() => {
              const feedback = prompt('Enter feedback for AI regeneration:');
              if (feedback) regenerateScene(scene.id, feedback);
            }}>
              Regenerate with AI
            </button>

            <button onClick={() => deleteScene(scene.id)}>
              Delete Scene
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default SceneManager;
```

### Vue.js Example

```vue
<template>
  <div class="scene-manager">
    <h2>Storyboard - {{ scenes.length }} Scenes</h2>

    <div v-for="scene in scenes" :key="scene.id" class="scene-card">
      <div class="scene-header">
        <h3>Scene {{ scene.sceneNumber }}</h3>
        <span>{{ scene.duration }}s | {{ scene.shotType }}</span>
      </div>

      <div class="scene-content">
        <p><strong>Description:</strong> {{ scene.description }}</p>
        <p><strong>Script:</strong> "{{ scene.script }}"</p>
      </div>

      <div class="scene-actions">
        <button @click="editScene(scene)">Edit</button>
        <button @click="regenerateScene(scene)">Regenerate with AI</button>
        <button @click="deleteScene(scene.id)">Delete</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const props = defineProps<{
  jobId: string;
  authToken: string;
}>();

const scenes = ref<Scene[]>([]);

onMounted(() => {
  loadScenes();
});

async function loadScenes() {
  const response = await fetch(`/api/v3/jobs/${props.jobId}/scenes`, {
    headers: { 'Authorization': `Bearer ${props.authToken}` }
  });
  const { data } = await response.json();
  scenes.value = data.scenes;
}

async function regenerateScene(scene: Scene) {
  const feedback = prompt('Enter feedback for AI regeneration:');
  if (!feedback) return;

  await fetch(`/api/v3/jobs/${props.jobId}/scenes/${scene.id}/regenerate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${props.authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ feedback })
  });

  await loadScenes();
}

async function deleteScene(sceneId: string) {
  if (!confirm('Delete this scene?')) return;

  await fetch(`/api/v3/jobs/${props.jobId}/scenes/${sceneId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${props.authToken}` }
  });

  await loadScenes();
}
</script>
```

---

## 💡 Best Practices

### 1. Scene Management UX

**Do:**
- ✅ Show scenes in a clear, card-based layout
- ✅ Display scene number, duration, and shot type prominently
- ✅ Provide inline editing for quick script changes
- ✅ Show AI regeneration as a separate, deliberate action
- ✅ Include preview/thumbnail if assets are available
- ✅ Show total duration of all scenes

**Don't:**
- ❌ Allow scene number changes (they're managed by the system)
- ❌ Delete all scenes (keep at least one)
- ❌ Change duration without considering total video length

### 2. AI Regeneration Feedback

**Effective Feedback Examples:**

```typescript
// Good - Specific and actionable
"Focus more on the product's eco-friendly materials. Mention the bamboo lid and recycled steel construction."

// Good - Clear tone direction
"Make this more upbeat and energetic. Target a younger, active audience."

// Good - Specific change request
"Reduce the environmental messaging and focus on the convenience and portability features."

// Poor - Too vague
"Make it better"

// Poor - Contradictory
"Make it more serious but also fun and playful"
```

### 3. Duration Management

```typescript
// Calculate total duration
const totalDuration = scenes.reduce((sum, scene) => sum + scene.duration, 0);

// Warn if duration doesn't match target
if (Math.abs(totalDuration - targetDuration) > 1.0) {
  console.warn(`Scene duration (${totalDuration}s) doesn't match target (${targetDuration}s)`);
}

// Adjust final scene to match target exactly
const adjustLastScene = async () => {
  const lastScene = scenes[scenes.length - 1];
  const currentTotal = scenes.reduce((sum, s) => sum + s.duration, 0);
  const adjustment = targetDuration - currentTotal;

  await updateScene(lastScene.id, {
    duration: lastScene.duration + adjustment
  });
};
```

### 4. Error Handling

```typescript
async function regenerateSceneWithErrorHandling(sceneId: string, feedback: string) {
  try {
    const response = await fetch(`/api/v3/jobs/${jobId}/scenes/${sceneId}/regenerate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ feedback })
    });

    const result = await response.json();

    if (!result.success) {
      // Handle API error
      showError(result.error || 'Failed to regenerate scene');
      return null;
    }

    return result.data;
  } catch (error) {
    // Handle network error
    showError('Network error. Please check your connection.');
    return null;
  }
}
```

### 5. Loading States

```typescript
const [regenerating, setRegenerating] = useState<string | null>(null);

const regenerateScene = async (sceneId: string, feedback: string) => {
  setRegenerating(sceneId);
  try {
    await fetch(/* ... */);
    await loadScenes();
  } finally {
    setRegenerating(null);
  }
};

// In UI
{regenerating === scene.id ? (
  <span>Regenerating with AI...</span>
) : (
  <button onClick={() => regenerateScene(scene.id, feedback)}>
    Regenerate
  </button>
)}
```

---

## 🔍 Scene Schema Reference

### Scene Object Structure

```typescript
interface Scene {
  // Identifiers
  id: string;              // UUID
  jobId: number;           // Parent job ID
  sceneNumber: number;     // 1-indexed scene number

  // Content
  duration: number;        // Duration in seconds (float)
  description: string;     // What happens visually in the scene
  script: string;          // Voiceover/narration text

  // Technical Details
  shotType: string;        // "wide" | "medium" | "close-up" | "extreme-close-up"
  transition: string;      // "cut" | "fade" | "dissolve" | "wipe"

  // Assets
  assets: string[];        // Array of asset IDs used in this scene

  // Custom Data
  metadata: Record<string, any>;  // Store any custom scene data

  // Timestamps
  createdAt: string;       // ISO 8601 timestamp
  updatedAt: string;       // ISO 8601 timestamp
}
```

### Common Shot Types

- **wide**: Establishes setting, shows full environment
- **medium**: Shows subject from waist up, balanced view
- **close-up**: Focuses on subject's face or product details
- **extreme-close-up**: Extreme detail (product features, emotions)

### Common Transitions

- **cut**: Instant change (most common, energetic)
- **fade**: Gradual fade to/from black (contemplative)
- **dissolve**: One scene fades into another (smooth, flowing)
- **wipe**: One scene "wipes" over another (dynamic, modern)

---

## 🧪 Testing Your Integration

### Manual Testing Checklist

1. **Job Creation**
   - [ ] Scenes are generated automatically
   - [ ] Number of scenes matches video duration (3-7 scenes)
   - [ ] All scenes have descriptions and scripts
   - [ ] Total scene duration matches target duration

2. **Scene Listing**
   - [ ] All scenes display correctly
   - [ ] Scenes are ordered by scene number
   - [ ] Scene details are complete

3. **Scene Editing**
   - [ ] Can update scene script
   - [ ] Can update scene description
   - [ ] Can adjust scene duration
   - [ ] Changes persist after reload

4. **AI Regeneration**
   - [ ] Regeneration works with feedback
   - [ ] Generated scene is different from original
   - [ ] Scene maintains same scene number
   - [ ] Duration constraints are respected

5. **Scene Deletion**
   - [ ] Can delete a scene
   - [ ] Remaining scenes still display correctly
   - [ ] Cannot delete all scenes

### Example Test Data

```json
{
  "context": {
    "clientId": "test-client-001",
    "campaignId": "test-campaign-001"
  },
  "adBasics": {
    "product": "SuperWidget Pro",
    "targetAudience": "Tech-savvy professionals",
    "keyMessage": "Productivity redefined",
    "callToAction": "Get yours today"
  },
  "creative": {
    "videoSpecs": {
      "duration": 30,
      "format": "16:9"
    },
    "direction": {
      "style": "professional",
      "tone": "confident"
    }
  }
}
```

---

## 🤝 Support & Questions

For technical support or questions:

1. Check the API documentation: `V3_DOCUMENTATION_INDEX.md`
2. Review the backend requirements: `V3_BACKEND_REQUIREMENTS.md`
3. See workflow diagrams: `V3_WORKFLOW_DIAGRAM.md`
4. Check OpenAPI docs: `http://localhost:8000/docs` (when server running)

---

**Happy integrating! 🎬**
