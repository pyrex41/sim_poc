# V3 API Integration Guide

## Overview

The V3 API provides a modern, frontend-aligned interface for the video generation platform. It replaces the legacy V2 endpoints with a clean, typed API that matches Next.js/React expectations.

### Key Improvements

- **Pydantic Models**: Strict typing with automatic validation
- **Standardized Responses**: Consistent `APIResponse` envelope
- **Enum-Based Status**: Clean state management for jobs
- **Simplified Endpoints**: CRUD operations for clients, campaigns, assets
- **Background Job Management**: Proper async workflow handling

### Base URL

```
https://your-domain.com/api/v3
```

## Authentication

All endpoints require authentication via the existing auth system.

```javascript
// Example: Include auth token in headers
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

## Response Format

All responses follow the `APIResponse` envelope:

```typescript
interface APIResponse {
  data?: any;
  error?: string;
  meta?: {
    timestamp: string;
    page?: number;
    total?: number;
  };
}
```

### Success Response
```json
{
  "data": { /* your data */ },
  "meta": {
    "timestamp": "2025-11-18T12:00:00.000Z"
  }
}
```

### Error Response
```json
{
  "error": "Failed to fetch clients: Database connection error",
  "meta": {
    "timestamp": "2025-11-18T12:00:00.000Z"
  }
}
```

## API Endpoints

### Clients

#### GET /api/v3/clients
Get all clients for the authenticated user.

**Query Parameters:**
- `limit` (optional): Number of results (1-1000, default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```typescript
{
  data: Client[],
  meta: {
    timestamp: string;
    page: number;
    total: number;
  }
}
```

#### GET /api/v3/clients/{client_id}
Get a specific client by ID.

#### POST /api/v3/clients
Create a new client.

**Request Body:**
```typescript
{
  name: string;
  description?: string;
  brandGuidelines?: {
    colors?: string[];
    fonts?: string[];
    tone?: string;
    restrictions?: string[];
    examples?: string[];
  };
}
```

#### PUT /api/v3/clients/{client_id}
Update an existing client.

#### DELETE /api/v3/clients/{client_id}
Delete a client.

### Campaigns

#### GET /api/v3/campaigns
Get campaigns, optionally filtered by client.

**Query Parameters:**
- `client_id` (optional): Filter by client ID
- `limit` (optional): Number of results (1-1000, default: 100)
- `offset` (optional): Pagination offset (default: 0)

#### GET /api/v3/campaigns/{campaign_id}
Get a specific campaign by ID.

#### POST /api/v3/campaigns
Create a new campaign.

**Request Body:**
```typescript
{
  clientId: string;
  name: string;
  goal: string;
  status: string;
  brief: string;
}
```

#### PUT /api/v3/campaigns/{campaign_id}
Update an existing campaign.

#### DELETE /api/v3/campaigns/{campaign_id}
Delete a campaign.

### Assets

#### GET /api/v3/assets
Get assets with optional filtering.

**Query Parameters:**
- `client_id` (optional): Filter by client ID
- `campaign_id` (optional): Filter by campaign ID
- `asset_type` (optional): Filter by asset type
- `limit` (optional): Number of results (1-1000, default: 100)
- `offset` (optional): Pagination offset (default: 0)

#### POST /api/v3/assets
Upload a new asset.

**Form Data:**
- `file`: The file to upload (required)
- `name`: Asset name (optional)
- `type`: Asset type (optional)
- `clientId`: Client ID (optional)
- `campaignId`: Campaign ID (optional)
- `tags`: JSON string of tags (optional)

**Response:**
```typescript
{
  data: {
    id: string;
    name: string;
    type: string;
    url: string;  // Points to /api/v2/assets/{id}/data
    format: string;
    size: number;
    tags?: string[];
    createdAt: string;
    updatedAt: string;
  }
}
```

### Jobs (Video Generation)

#### POST /api/v3/jobs
Create a new video generation job.

**Request Body:**
```typescript
{
  context: {
    clientId: string;
    campaignId?: string;
  };
  adBasics: {
    product: string;
    targetAudience: string;
    keyMessage: string;
    callToAction: string;
  };
  creative: {
    direction: {
      style: string;
    };
  };
  advanced?: {
    // Additional parameters
  };
}
```

**Response:**
```typescript
{
  data: {
    id: string;
    status: JobStatus;
    createdAt: string;
    updatedAt: string;
  }
}
```

#### GET /api/v3/jobs/{job_id}
Get job status and progress.

**Response:**
```typescript
{
  data: {
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
}
```

#### POST /api/v3/jobs/{job_id}/actions
Perform actions on a job.

**Request Body:**
```typescript
{
  action: JobAction;  // "approve" | "cancel" | "regenerate_scene"
}
```

### Cost Estimation

#### POST /api/v3/jobs/dry-run
Estimate cost for a job without creating it.

**Request Body:** Same as job creation.

**Response:**
```typescript
{
  data: {
    estimatedCost: number;
    currency: string;
    breakdown: {
      storyboard_generation: number;
      image_generation: number;
      video_rendering: number;
    };
    validUntil: string;
  }
}
```

## Data Models

### Enums

```typescript
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
```

### Interfaces

```typescript
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
  brief: string;
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

## Error Handling

The API uses standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (validation errors)
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

All errors include a descriptive message in the `error` field of the response.

## Frontend Integration Steps

### 1. Update API Client

Create or update your API client to use the V3 endpoints:

```typescript
// api/client.ts
const API_BASE = '/api/v3';

export const apiClient = {
  // Clients
  getClients: (params?: { limit?: number; offset?: number }) =>
    fetch(`${API_BASE}/clients?${new URLSearchParams(params)}`),

  createClient: (data: ClientCreateRequest) =>
    fetch(`${API_BASE}/clients`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  // Campaigns
  getCampaigns: (params?: { client_id?: string; limit?: number; offset?: number }) =>
    fetch(`${API_BASE}/campaigns?${new URLSearchParams(params)}`),

  // Jobs
  createJob: (data: JobCreateRequest) =>
    fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  getJobStatus: (jobId: string) =>
    fetch(`${API_BASE}/jobs/${jobId}`),

  approveStoryboard: (jobId: string) =>
    fetch(`${API_BASE}/jobs/${jobId}/actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'approve' })
    }),

  // Assets
  uploadAsset: (formData: FormData) =>
    fetch(`${API_BASE}/assets`, {
      method: 'POST',
      body: formData
    }),

  // Cost estimation
  estimateCost: (data: JobCreateRequest) =>
    fetch(`${API_BASE}/jobs/dry-run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
};
```

### 2. Update State Management

Update your state management to handle the new data structures:

```typescript
// types/job.ts
export interface JobState {
  jobs: Job[];
  currentJob: Job | null;
  loading: boolean;
  error: string | null;
}

// Redux slice or Zustand store
const useJobStore = create<JobState & {
  createJob: (request: JobCreateRequest) => Promise<void>;
  pollJobStatus: (jobId: string) => Promise<void>;
}>((set, get) => ({
  jobs: [],
  currentJob: null,
  loading: false,
  error: null,

  createJob: async (request) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.createJob(request);
      const result = await response.json();

      if (result.error) {
        set({ error: result.error, loading: false });
        return;
      }

      const newJob = result.data;
      set(state => ({
        jobs: [...state.jobs, newJob],
        currentJob: newJob,
        loading: false
      }));

      // Start polling for status updates
      get().pollJobStatus(newJob.id);
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  pollJobStatus: async (jobId) => {
    try {
      const response = await apiClient.getJobStatus(jobId);
      const result = await response.json();

      if (result.error) {
        set({ error: result.error });
        return;
      }

      const job = result.data;
      set(state => ({
        jobs: state.jobs.map(j => j.id === jobId ? job : j),
        currentJob: job
      }));

      // Continue polling if job is still processing
      if (['pending', 'storyboard_processing', 'video_processing'].includes(job.status)) {
        setTimeout(() => get().pollJobStatus(jobId), 2000);
      }
    } catch (err) {
      set({ error: err.message });
    }
  }
}));
```

### 3. Update UI Components

Update your components to use the new data structures:

```typescript
// components/JobStatus.tsx
interface JobStatusProps {
  job: Job;
}

export const JobStatus: React.FC<JobStatusProps> = ({ job }) => {
  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case JobStatus.COMPLETED: return 'green';
      case JobStatus.FAILED: return 'red';
      case JobStatus.CANCELLED: return 'gray';
      default: return 'blue';
    }
  };

  return (
    <div className={`status status-${getStatusColor(job.status)}`}>
      {job.status.replace('_', ' ').toUpperCase()}

      {job.progress && (
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      )}

      {job.error && (
        <div className="error-message">
          {job.error}
        </div>
      )}
    </div>
  );
};
```

### 4. Handle Asset Uploads

Update file upload handling:

```typescript
// components/AssetUpload.tsx
export const AssetUpload: React.FC = () => {
  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', file.name);
    formData.append('type', 'image'); // or 'video', 'document', etc.

    try {
      const response = await apiClient.uploadAsset(formData);
      const result = await response.json();

      if (result.error) {
        console.error('Upload failed:', result.error);
        return;
      }

      const asset = result.data;
      console.log('Asset uploaded:', asset);

      // Asset URL is immediately available for preview
      // asset.url points to /api/v2/assets/{id}/data
    } catch (err) {
      console.error('Upload error:', err);
    }
  };

  return (
    <input
      type="file"
      onChange={(e) => {
        const file = e.target.files?.[0];
        if (file) handleFileUpload(file);
      }}
    />
  );
};
```

## Migration from V2

### What Changes

1. **Endpoint URLs**: All endpoints now use `/api/v3/` prefix
2. **Response Format**: All responses wrapped in `APIResponse` envelope
3. **Job Status**: Status values changed from strings to enums
4. **Asset URLs**: Asset uploads now return valid URLs immediately
5. **Authentication**: Same auth system, but ensure tokens are included

### Migration Checklist

- [ ] Update all API calls to use `/api/v3/` endpoints
- [ ] Update response parsing to handle `APIResponse` envelope
- [ ] Update job status handling to use `JobStatus` enum
- [ ] Update asset upload to use form data instead of JSON
- [ ] Test all CRUD operations for clients and campaigns
- [ ] Test job creation, status polling, and approval workflow
- [ ] Test asset upload and URL generation
- [ ] Update error handling for new error format

### Backward Compatibility

The V2 API remains available during the migration period. You can gradually migrate endpoints:

```typescript
// Temporary compatibility layer
const apiClient = {
  // V3 endpoints
  getClientsV3: () => fetch('/api/v3/clients'),

  // Fallback to V2
  getClientsV2: () => fetch('/api/videos'),

  // Smart fallback
  getClients: async () => {
    try {
      const response = await fetch('/api/v3/clients');
      return response.json();
    } catch {
      // Fallback to V2
      const response = await fetch('/api/videos');
      const data = await response.json();
      // Transform V2 response to V3 format
      return { data };
    }
  }
};
```

## Testing

### Unit Tests

```typescript
// __tests__/apiClient.test.ts
describe('V3 API Client', () => {
  it('should create a job successfully', async () => {
    const mockResponse = {
      data: {
        id: '123',
        status: 'pending',
        createdAt: '2025-11-18T12:00:00.000Z',
        updatedAt: '2025-11-18T12:00:00.000Z'
      }
    };

    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(mockResponse)
      })
    );

    const result = await apiClient.createJob(mockJobRequest);
    expect(result.data.id).toBe('123');
    expect(result.data.status).toBe('pending');
  });
});
```

### Integration Tests

```typescript
// __tests__/JobWorkflow.test.tsx
describe('Job Creation Workflow', () => {
  it('should create job and poll for completion', async () => {
    const { result } = renderHook(() => useJobStore());

    await act(async () => {
      await result.current.createJob(mockJobRequest);
    });

    expect(result.current.currentJob?.status).toBe('pending');

    // Mock successful completion
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({
          data: { ...mockJob, status: 'completed', videoUrl: 'https://example.com/video.mp4' }
        })
      })
    );

    await act(async () => {
      await result.current.pollJobStatus('123');
    });

    expect(result.current.currentJob?.status).toBe('completed');
    expect(result.current.currentJob?.videoUrl).toBe('https://example.com/video.mp4');
  });
});
```

## Support

For questions or issues with the V3 API integration:

1. Check this document first
2. Review the API models in `backend/api/v3/models.py`
3. Test endpoints directly with curl/Postman
4. Contact the backend team for API changes

## Changelog

### V3.0.0
- Initial release of V3 API
- Added clients, campaigns, assets, and jobs endpoints
- Implemented standardized response format
- Added enum-based job status management
- Fixed asset URL generation for immediate previews</content>
<parameter name="filePath">docs/V3_API_INTEGRATION_GUIDE.md