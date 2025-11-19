# V3 API Quick Reference

## Getting Started

### Base URL
```
/api/v3
```

### Documentation
- **Swagger UI**: http://localhost:8000/docs
- **Full Guide**: See [V3_API_INTEGRATION_GUIDE.md](./V3_API_INTEGRATION_GUIDE.md)

## Quick Links by Feature

### 🏢 Client Management (`v3-clients`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v3/clients` | List all clients |
| `GET` | `/api/v3/clients/{id}` | Get single client |
| `GET` | `/api/v3/clients/{id}/stats` | Get client statistics ✨ |
| `POST` | `/api/v3/clients` | Create new client |
| `PUT` | `/api/v3/clients/{id}` | Update client |
| `DELETE` | `/api/v3/clients/{id}` | Delete client |

### 📢 Campaign Management (`v3-campaigns`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v3/campaigns` | List campaigns (filter by client) |
| `GET` | `/api/v3/campaigns/{id}` | Get single campaign |
| `GET` | `/api/v3/campaigns/{id}/stats` | Get campaign statistics ✨ |
| `POST` | `/api/v3/campaigns` | Create new campaign |
| `PUT` | `/api/v3/campaigns/{id}` | Update campaign |
| `DELETE` | `/api/v3/campaigns/{id}` | Delete campaign |

### 📁 Asset Management (`v3-assets`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v3/assets` | List assets (filter by client/campaign) |
| `GET` | `/api/v3/assets/{id}` | Get single asset ✨ |
| `POST` | `/api/v3/assets` | Upload new asset (multipart/form-data) |
| `DELETE` | `/api/v3/assets/{id}` | Delete asset ✨ |

### ⚙️ Job Management (`v3-jobs`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v3/jobs` | Create video generation job |
| `GET` | `/api/v3/jobs/{id}` | Get job status & progress |
| `POST` | `/api/v3/jobs/{id}/actions` | Approve/cancel/regenerate |

### 💰 Cost Estimation (`v3-cost`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v3/jobs/dry-run` | Estimate cost before creating job |

## Response Format

All V3 endpoints return the same envelope:

```typescript
interface APIResponse {
  data?: any;           // Your actual data
  error?: string;       // Error message if failed
  meta?: {
    timestamp: string;  // ISO 8601 timestamp
    page?: number;      // For paginated responses
    total?: number;     // Total count for pagination
  };
}
```

### Success Example
```json
{
  "data": {
    "id": "client-123",
    "name": "Acme Corp"
  },
  "meta": {
    "timestamp": "2025-11-19T20:00:00.000Z"
  }
}
```

### Error Example
```json
{
  "error": "Client not found",
  "meta": {
    "timestamp": "2025-11-19T20:00:00.000Z"
  }
}
```

## Common Patterns

### Creating a Client
```typescript
const response = await fetch('/api/v3/clients', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    name: 'Acme Corp',
    description: 'Tech company',
    brandGuidelines: {
      colors: ['#FF0000', '#0000FF'],
      tone: 'Professional'
    }
  })
});

const { data, error } = await response.json();
if (error) {
  console.error(error);
} else {
  console.log('Created client:', data);
}
```

### Uploading an Asset
```typescript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('name', 'Product Photo');
formData.append('type', 'image');
formData.append('clientId', 'client-123');

const response = await fetch('/api/v3/assets', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const { data, error } = await response.json();
if (!error) {
  // Use data.url to preview: /api/v2/assets/{id}/data
  console.log('Asset URL:', data.url);
}
```

### Creating a Job and Polling
```typescript
// 1. Create job
const jobResponse = await fetch('/api/v3/jobs', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    context: {
      clientId: 'client-123',
      campaignId: 'campaign-456',
      userId: 'user-789'
    },
    adBasics: {
      product: 'Smart Watch',
      targetAudience: 'Tech enthusiasts 25-40',
      keyMessage: 'Stay connected, stay active',
      callToAction: 'Buy Now'
    },
    creative: {
      direction: {
        style: 'Modern and sleek',
        tone: 'Energetic',
        visualElements: ['Product shots', 'Lifestyle'],
        musicStyle: 'Upbeat electronic'
      }
    }
  })
});

const { data: job } = await jobResponse.json();

// 2. Poll for status
const pollStatus = async (jobId: string) => {
  const response = await fetch(`/api/v3/jobs/${jobId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const { data } = await response.json();

  console.log('Job status:', data.status);

  // Continue polling if not done
  if (['pending', 'storyboard_processing', 'video_processing'].includes(data.status)) {
    setTimeout(() => pollStatus(jobId), 2000);
  } else if (data.status === 'storyboard_ready') {
    // Storyboard is ready for review
    console.log('Storyboard:', data.storyboard);
  } else if (data.status === 'completed') {
    console.log('Video URL:', data.videoUrl);
  }
};

pollStatus(job.id);
```

### Approving a Storyboard
```typescript
const response = await fetch(`/api/v3/jobs/${jobId}/actions`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    action: 'approve'
  })
});

// Job will transition to video_processing
```

## Job Status Flow

```
pending
  ↓
storyboard_processing
  ↓
storyboard_ready ← User reviews storyboard
  ↓ (after approval)
video_processing
  ↓
completed
```

Alternative outcomes:
- `failed` - Error occurred
- `cancelled` - User cancelled

## Key Differences from V2

| Aspect | V2 | V3 |
|--------|----|----|
| Base URL | `/api/v2/*` | `/api/v3/*` |
| Response Format | Raw data | `APIResponse` envelope |
| Status Values | String literals | `JobStatus` enum |
| Asset URLs | Generated after processing | Available immediately |
| Error Format | HTTP status only | `error` field in response |
| Documentation | Mixed with legacy | Organized at top with tags |

## Migration Steps

1. **Update base URL**: Change all `/api/v2/` to `/api/v3/`
2. **Unwrap responses**: Access `response.data` instead of raw response
3. **Check errors**: Look for `response.error` field
4. **Update status checks**: Use enum values instead of strings
5. **Test in Swagger**: Visit http://localhost:8000/docs

## TypeScript Types

```typescript
// Copy these into your frontend codebase
enum JobStatus {
  PENDING = "pending",
  STORYBOARD_PROCESSING = "storyboard_processing",
  STORYBOARD_READY = "storyboard_ready",
  VIDEO_PROCESSING = "video_processing",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled"
}

enum JobAction {
  APPROVE = "approve",
  CANCEL = "cancel",
  REGENERATE_SCENE = "regenerate_scene"
}

interface APIResponse<T = any> {
  data?: T;
  error?: string;
  meta?: {
    timestamp: string;
    page?: number;
    total?: number;
  };
}

interface Client {
  id: string;
  name: string;
  description?: string;
  brandGuidelines?: {
    colors?: string[];
    fonts?: string[];
    tone?: string;
    restrictions?: string[];
    examples?: string[];
  };
  createdAt: string;
  updatedAt: string;
}

interface Campaign {
  id: string;
  clientId: string;
  name: string;
  goal: string;
  status: string;
  brief?: any;
  createdAt: string;
  updatedAt: string;
}

interface Asset {
  id: string;
  name: string;
  type: string;
  url: string;
  format: string;
  size: number;
  tags?: string[];
  clientId?: string;
  campaignId?: string;
  createdAt: string;
  updatedAt: string;
}

interface Job {
  id: string;
  status: JobStatus;
  progress?: any;
  storyboard?: {
    scenes: Array<{
      image_url: string;
      description: string;
      scene_idx: number;
    }>;
  };
  videoUrl?: string;
  error?: string;
  estimatedCost?: number;
  actualCost?: number;
  createdAt: string;
  updatedAt: string;
}
```

## Need Help?

1. **Interactive Docs**: http://localhost:8000/docs - Try endpoints directly
2. **Full Guide**: [V3_API_INTEGRATION_GUIDE.md](./V3_API_INTEGRATION_GUIDE.md)
3. **Models Reference**: `backend/api/v3/models.py` - See exact Pydantic schemas
4. **Example Code**: Full integration examples in the main guide

## Common Issues

### "Unauthorized" errors
- Include `Authorization: Bearer {token}` header on all requests
- Token must be valid and not expired

### Asset uploads failing
- Use `multipart/form-data` encoding (FormData)
- Don't set `Content-Type` header manually (browser sets it)

### Polling too aggressively
- Use 2-3 second intervals between polls
- Stop polling on terminal states (completed, failed, cancelled)

### Response parsing errors
- Always check for `response.error` first
- Then access `response.data`
- Don't assume data exists if error is present
