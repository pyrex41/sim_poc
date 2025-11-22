# Property Video Generation API

## Overview

The Property Video Generation endpoint allows you to create professional luxury lodging marketing videos from crawled property photos. The system uses AI (xAI Grok) to intelligently select 7 image pairs from your property photos based on predefined scene types, then generates a 35-second video (7 scenes × 5 seconds each).

## Endpoint

```
POST /api/v3/jobs/from-property-photos
```

## Authentication

Requires bearer token authentication:

```
Authorization: Bearer YOUR_API_KEY
```

## Request Body

### PropertyVideoRequest

```typescript
{
  propertyInfo: {
    name: string;              // Property name
    location: string;          // Property location
    propertyType: string;      // e.g., "boutique hotel", "luxury resort"
    positioning: string;       // e.g., "eco-luxury", "modern minimalist"
  };
  photos: PropertyPhoto[];     // Minimum 14 photos required
  campaignId: string;          // Campaign ID to associate this job with
  clipDuration?: number;       // Duration per scene in seconds (default: 6.0)
  videoModel?: string;         // "veo3" or "hailuo-2.0" (default: "veo3")
}
```

### PropertyPhoto

```typescript
{
  id: string;                  // Unique photo identifier
  filename?: string;           // Photo filename
  url: string;                 // URL to photo (must be publicly accessible)
  tags?: string[];             // Photo tags (e.g., ["exterior", "pool", "bedroom"])
  dominantColors?: string[];   // Dominant colors in hex (e.g., ["#2A3B4C", "#F5E6D3"])
  detectedObjects?: string[];  // Detected objects (e.g., ["bed", "chair", "window"])
  composition?: string;        // Composition style (e.g., "rule_of_thirds", "symmetrical")
  lighting?: string;           // Lighting conditions (e.g., "natural", "golden_hour")
  resolution?: string;         // Image resolution (e.g., "1920x1080")
  aspectRatio?: string;        // Aspect ratio (e.g., "16:9")
}
```

## Scene Types

The system selects image pairs for 7 predefined luxury lodging scene types:

1. **Grand Arrival** (5s) - Property exterior, architectural style, welcoming entrance
2. **Refined Interiors** (5s) - Lobby/common areas, interior design excellence
3. **Guest Room Sanctuary** (5s) - Room luxury, comfort, amenities
4. **Culinary Excellence** (5s) - Dining experiences, food quality
5. **Wellness & Recreation** (5s) - Pool, spa, fitness, activities
6. **Unique Experiences** (5s) - Distinctive features, local culture
7. **Lasting Impression** (5s) - Hero shot, memorable vista

**Total Duration**: 35 seconds

## Response

### PropertyVideoJobResponse

```typescript
{
  data: {
    jobId: number;             // Job ID for progress tracking
    status: string;            // Initial status (usually "pending")
    propertyName: string;      // Property name
    totalScenes: number;       // Number of scenes (always 7)
    selectionMetadata: {
      totalPhotosAnalyzed: number;
      selectionConfidence: string;  // e.g., "high", "medium"
      aiModel: string;              // AI model used for selection
      selectionTimestamp: string;
    };
    scenePairs: SceneImagePair[];  // Details of selected image pairs
  };
  error: null;
  meta: null;
}
```

### SceneImagePair

```typescript
{
  sceneNumber: number;         // Scene number (1-7)
  sceneType: string;           // Scene type name
  firstImage: {
    id: string;                // Photo ID
    filename: string;          // Filename
    reasoning: string;         // AI reasoning for selection
    qualityScore: number;      // Quality score (1-10)
    tagMatchScore: number;     // Tag alignment score (1-10)
  };
  lastImage: {
    id: string;
    filename: string;
    reasoning: string;
    qualityScore: number;
    tagMatchScore: number;
  };
  transitionAnalysis: {
    colorCompatibility: string;      // e.g., "excellent", "good"
    lightingConsistency: string;     // e.g., "matched", "similar"
    compositionalFlow: string;       // e.g., "smooth", "establishing_to_detail"
    interpolationConfidence: number; // Confidence in smooth transition (1-10)
  };
}
```

## Example Request

### cURL Example

```bash
curl -X POST http://localhost:8001/api/v3/jobs/from-property-photos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key-12345" \
  -d '{
    "propertyInfo": {
      "name": "The Emerald Bay Resort",
      "location": "Maldives",
      "propertyType": "luxury resort",
      "positioning": "eco-luxury overwater bungalows"
    },
    "photos": [
      {
        "id": "photo_001",
        "filename": "exterior_sunset.jpg",
        "url": "https://example.com/photos/exterior_sunset.jpg",
        "tags": ["exterior", "sunset", "architecture", "ocean"],
        "dominantColors": ["#FF6B35", "#004E89", "#F7B32B"],
        "detectedObjects": ["building", "palm_tree", "ocean", "sky"],
        "composition": "rule_of_thirds",
        "lighting": "golden_hour",
        "resolution": "4096x2160",
        "aspectRatio": "16:9"
      },
      {
        "id": "photo_002",
        "filename": "lobby_interior.jpg",
        "url": "https://example.com/photos/lobby_interior.jpg",
        "tags": ["interior", "lobby", "lounge", "design"],
        "dominantColors": ["#2C3E50", "#ECF0F1", "#95A5A6"],
        "detectedObjects": ["sofa", "chandelier", "plants", "artwork"],
        "composition": "symmetrical",
        "lighting": "natural",
        "resolution": "3840x2160",
        "aspectRatio": "16:9"
      }
      // ... minimum 14 photos total required
    ],
    "campaignId": "campaign_123",
    "clipDuration": 5.0,
    "videoModel": "veo3"
  }'
```

### JavaScript/TypeScript Example

```typescript
const response = await fetch('http://localhost:8001/api/v3/jobs/from-property-photos', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_API_KEY'
  },
  body: JSON.stringify({
    propertyInfo: {
      name: "The Emerald Bay Resort",
      location: "Maldives",
      propertyType: "luxury resort",
      positioning: "eco-luxury overwater bungalows"
    },
    photos: [
      // ... your photos array (minimum 14 photos)
    ],
    campaignId: "campaign_123",
    clipDuration: 5.0,
    videoModel: "veo3"
  })
});

const result = await response.json();
console.log(`Job created with ID: ${result.data.jobId}`);
```

## Tracking Job Progress

After creating the job, track its progress using the sub-jobs endpoint:

```bash
curl -X GET "http://localhost:8001/api/v3/jobs/{jobId}/sub-jobs" \
  -H "Authorization: Bearer test-key-12345"
```

### Sub-Job Statuses

- `pending` - Waiting to start
- `processing` - Video generation in progress
- `completed` - Video ready
- `failed` - Generation failed

## Workflow

1. **Crawl Property Website** - Extract photos and metadata
2. **Prepare Photo Data** - Format photos with tags, colors, objects, etc.
3. **Create Job** - POST to `/api/v3/jobs/from-property-photos`
4. **AI Selection** - Grok analyzes all photos and selects optimal pairs
5. **Asset Storage** - Photos stored as assets in database
6. **Video Generation** - 7 parallel video generations (one per scene)
7. **Poll Progress** - Track sub-job status
8. **Video Ready** - Download completed videos from sub-job `videoUrl`

## Image Selection Criteria

The AI uses the following weighted criteria to select image pairs:

### 1. Visual Quality (30%)
- High resolution and sharpness
- Professional composition (rule of thirds, leading lines, symmetry)
- Optimal lighting (natural light preferred, golden hour highly valued)
- Color harmony and aesthetic appeal

### 2. Tag Alignment (25%)
- Strong match with scene type's ideal tags
- Relevant detected objects for scene narrative
- Appropriate setting and context

### 3. Transition Potential (25%)
- Similar lighting conditions between first/last image
- Compatible color palettes (smooth gradient possible)
- Compositional flow (wide → medium, or establishing → detail)
- Avoid jarring jumps in perspective or subject matter

### 4. Brand Consistency (20%)
- Aligns with property positioning and target market
- Represents property's unique character
- Appeals to luxury hospitality audience
- Authentic representation

## Requirements

- **Minimum Photos**: 14 photos required (7 scenes × 2 images per scene)
- **Recommended Photos**: 20-30 photos for better AI selection
- **Image Format**: JPG, PNG, or WebP
- **Image Resolution**: Minimum 1920×1080 recommended
- **URL Accessibility**: All photo URLs must be publicly accessible
- **Campaign**: Must have valid campaign ID associated with a client

## Cost Estimation

Each property video job consists of:
- 1 AI selection call (Grok) - ~$0.01
- 7 video generations (Veo3 or Hailuo) - ~$0.35-0.70 per video

**Estimated Total Cost**: $2.50-$5.00 per property video

## Error Handling

### Common Errors

```json
{
  "data": null,
  "error": "Need at least 14 photos to select 7 pairs, got 10",
  "meta": null
}
```

**Solution**: Ensure you provide at least 14 photos in the request.

```json
{
  "data": null,
  "error": "Campaign not found",
  "meta": null
}
```

**Solution**: Verify the `campaignId` exists and is accessible to your user.

```json
{
  "data": null,
  "error": "Grok returned no scene pairs",
  "meta": null
}
```

**Solution**: Check that your photos have sufficient metadata (tags, detected objects) to guide AI selection.

## Best Practices

### Photo Tagging
Provide rich metadata to improve AI selection:
- **Tags**: Use descriptive tags matching scene types (e.g., `["exterior", "pool", "spa", "dining"]`)
- **Detected Objects**: Include objects relevant to luxury hospitality (e.g., `["bed", "ocean_view", "infinity_pool"]`)
- **Lighting**: Specify lighting conditions (e.g., `"golden_hour"`, `"natural"`, `"ambient"`)
- **Composition**: Note composition style (e.g., `"rule_of_thirds"`, `"symmetrical"`)

### Photo Quality
- Use high-resolution images (minimum 1920×1080)
- Ensure photos are well-lit and in focus
- Avoid heavily filtered or over-processed images
- Include diverse angles and perspectives

### Photo Variety
Include photos covering all 7 scene types:
- Exterior/arrival shots
- Interior/lobby areas
- Guest rooms/suites
- Dining/restaurant spaces
- Amenities (pool, spa, fitness)
- Unique features/experiences
- Scenic views/hero shots

## Integration Example

Complete workflow from photo crawl to video generation:

```typescript
// 1. Crawl property website and extract photos
const crawledPhotos = await crawlPropertyWebsite('https://emeraldbayresort.com');

// 2. Enrich with metadata (using image analysis service)
const enrichedPhotos = await Promise.all(
  crawledPhotos.map(async (photo) => ({
    id: photo.id,
    filename: photo.filename,
    url: photo.url,
    tags: await extractTags(photo.url),
    dominantColors: await extractColors(photo.url),
    detectedObjects: await detectObjects(photo.url),
    composition: await analyzeComposition(photo.url),
    lighting: await analyzeLighting(photo.url),
    resolution: photo.resolution,
    aspectRatio: photo.aspectRatio
  }))
);

// 3. Create property video job
const jobResponse = await fetch('/api/v3/jobs/from-property-photos', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_API_KEY'
  },
  body: JSON.stringify({
    propertyInfo: {
      name: "The Emerald Bay Resort",
      location: "Maldives",
      propertyType: "luxury resort",
      positioning: "eco-luxury overwater bungalows"
    },
    photos: enrichedPhotos,
    campaignId: "campaign_123",
    clipDuration: 5.0,
    videoModel: "veo3"
  })
});

const job = await jobResponse.json();
const jobId = job.data.jobId;

// 4. Poll for completion
const checkStatus = async () => {
  const statusResponse = await fetch(`/api/v3/jobs/${jobId}/sub-jobs`, {
    headers: { 'Authorization': 'Bearer YOUR_API_KEY' }
  });

  const subJobs = await statusResponse.json();
  const allCompleted = subJobs.data.every(sj => sj.status === 'completed');

  if (allCompleted) {
    console.log('All scenes completed!');
    subJobs.data.forEach(sj => {
      console.log(`Scene ${sj.subJobNumber}: ${sj.videoUrl}`);
    });
  } else {
    setTimeout(checkStatus, 10000); // Check again in 10 seconds
  }
};

checkStatus();
```

## Support

For issues or questions:
- Check server logs: `/tmp/backend.log`
- Review AI selection reasoning in response `scenePairs[].firstImage.reasoning`
- Verify photo metadata is sufficient for scene matching
- Ensure campaign and client IDs are valid

## API Version

This endpoint is part of the v3 API. For legacy endpoints, see `/api/v2/jobs/from-image-pairs`.
