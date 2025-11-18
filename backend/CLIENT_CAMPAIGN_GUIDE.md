# Client & Campaign Management Guide

## Overview

The v3 API now includes complete client and campaign management functionality. This allows you to organize your generated content by clients and campaigns.

## Database Schema

### Clients Table
- `id` (TEXT): Unique client identifier (UUID)
- `user_id` (INTEGER): User who owns this client
- `name` (TEXT): Client name
- `description` (TEXT): Optional client description
- `brand_guidelines` (TEXT): Optional brand guidelines/style information
- `created_at` (TIMESTAMP): Creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Campaigns Table
- `id` (TEXT): Unique campaign identifier (UUID)
- `client_id` (TEXT): Associated client
- `user_id` (INTEGER): User who owns this campaign
- `name` (TEXT): Campaign name
- `goal` (TEXT): Campaign goal/objective
- `status` (TEXT): Status (active/archived/draft)
- `brief` (TEXT): Optional campaign brief
- `created_at` (TIMESTAMP): Creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

## API Endpoints

### Client Management

#### Create Client
```http
POST /api/v3/clients
Content-Type: application/json

{
  "name": "Acme Corporation",
  "description": "Our main enterprise client",
  "brand_guidelines": "Use blue color scheme, modern minimalist style"
}
```

#### List Clients
```http
GET /api/v3/clients?page=1&page_size=50&sort_by=created_at&sort_order=desc&search=Acme
```

#### Get Client
```http
GET /api/v3/clients/{client_id}
```

#### Update Client
```http
PATCH /api/v3/clients/{client_id}
Content-Type: application/json

{
  "name": "Acme Corporation Inc.",
  "description": "Updated description"
}
```

#### Delete Client
```http
DELETE /api/v3/clients/{client_id}
```

### Campaign Management

#### Create Campaign
```http
POST /api/v3/campaigns
Content-Type: application/json

{
  "client_id": "uuid-of-client",
  "name": "Summer 2024 Launch",
  "goal": "Promote new product line",
  "status": "active",
  "brief": "Create engaging video content for social media"
}
```

#### List Campaigns
```http
GET /api/v3/campaigns?page=1&client_id=uuid&status=active&search=Summer
```

#### Get Campaign
```http
GET /api/v3/campaigns/{campaign_id}
```

#### Update Campaign
```http
PATCH /api/v3/campaigns/{campaign_id}
Content-Type: application/json

{
  "status": "archived",
  "brief": "Updated campaign brief"
}
```

#### Delete Campaign
```http
DELETE /api/v3/campaigns/{campaign_id}
```

#### List Campaigns for a Client (Nested)
```http
GET /api/v3/clients/{client_id}/campaigns?status=active
```

#### Create Campaign for a Client (Nested)
```http
POST /api/v3/clients/{client_id}/campaigns
Content-Type: application/json

{
  "client_id": "same-as-path",
  "name": "Winter Campaign",
  "goal": "Holiday season promotion",
  "status": "draft"
}
```

## Integration with Generation Tasks

When creating generation tasks (images, videos, audio), you can now associate them with clients and campaigns:

```http
POST /api/v3/generate/image
Content-Type: application/json

{
  "prompt": "A futuristic cityscape",
  "client_id": "uuid-of-client",
  "campaign_id": "uuid-of-campaign",
  "provider": "fal",
  "model": "fal-ai/flux-pro"
}
```

All generated content will be linked to the specified client and campaign, making it easy to:
- Track content per client
- Organize content by campaign
- Generate reports
- Apply client-specific brand guidelines

## Response Format

All list endpoints return paginated responses:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "has_more": true
}
```

## Error Handling

- `400 Bad Request`: Invalid input data
- `404 Not Found`: Client or campaign not found
- `500 Internal Server Error`: Database or server error

## Authentication

Currently uses a placeholder user ID (1). In production, this should be replaced with actual authentication middleware that extracts the user ID from JWT tokens or session data.

## Features

### Client Management
- ✅ Create clients
- ✅ List clients with pagination and search
- ✅ Get client details
- ✅ Update client information
- ✅ Delete clients (cascades to campaigns and sets NULL on tasks)

### Campaign Management
- ✅ Create campaigns
- ✅ List campaigns with filters (client, status, search)
- ✅ Get campaign details
- ✅ Update campaign information
- ✅ Delete campaigns (sets NULL on tasks)
- ✅ Nested campaign endpoints under clients

### Data Integrity
- ✅ Foreign key constraints
- ✅ Cascade deletes for clients → campaigns
- ✅ SET NULL on delete for campaigns → tasks
- ✅ User-based access control (scoped to user_id)
- ✅ Input validation

## Next Steps

1. Add authentication middleware to replace placeholder user ID
2. Add role-based access control (RBAC)
3. Add client/campaign sharing between users
4. Add analytics/reporting endpoints
5. Add bulk operations
