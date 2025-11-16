# Asset Management API Documentation

## Overview

The asset management system has been consolidated into a single, unified API that supports images, videos, audio, and documents. Assets can be associated with clients, campaigns, or both.

**Key Changes:**
- ✅ Single consolidated `assets` table (replaced `uploaded_assets`, `client_assets`, `campaign_assets`)
- ✅ Discriminated union response format for type-safe asset handling
- ✅ Automatic metadata extraction (dimensions, duration, file size)
- ✅ Automatic thumbnail generation for videos
- ✅ Flexible filtering by client, campaign, and asset type
- ❌ Deprecated: `POST /api/clients/{id}/assets` and `POST /api/campaigns/{id}/assets`

---

## Database Schema

### `assets` Table

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | TEXT | No | UUID primary key |
| `user_id` | INTEGER | Yes | Owner user ID |
| `client_id` | TEXT | Yes | Associated client ID (FK) |
| `campaign_id` | TEXT | Yes | Associated campaign ID (FK) |
| `name` | TEXT | No | Display name |
| `asset_type` | TEXT | No | Discriminator: 'image', 'video', 'audio', 'document' |
| `url` | TEXT | No | Full URL to asset |
| `size` | INTEGER | Yes | File size in bytes |
| `uploaded_at` | TIMESTAMP | No | Upload timestamp |
| `format` | TEXT | No | File format: 'png', 'mp4', 'pdf', etc. |
| `tags` | TEXT | Yes | JSON array of tags |
| `width` | INTEGER | Yes | For images/videos |
| `height` | INTEGER | Yes | For images/videos |
| `duration` | INTEGER | Yes | For videos/audio (seconds) |
| `thumbnail_url` | TEXT | Yes | For videos/documents |
| `waveform_url` | TEXT | Yes | For audio (future) |
| `page_count` | INTEGER | Yes | For documents |

---

## API Endpoints

### 1. Upload Asset

**Endpoint:** `POST /api/v2/upload-asset`

**Authentication:** Required (Bearer token)

**Content-Type:** `multipart/form-data`

**Rate Limit:** 10 uploads per minute

**Form-Data Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | The binary file to upload |
| `clientId` | String | No | Associate with a client |
| `campaignId` | String | No | Associate with a campaign |
| `name` | String | No | Custom display name (defaults to filename) |

**Supported File Types:**
- **Images:** jpg, jpeg, png, gif, webp
- **Videos:** mp4, mov
- **Audio:** mp3, wav
- **Documents:** pdf

**Max File Size:** 50MB

**Example Request (cURL):**

```bash
curl -X POST "https://api.example.com/api/v2/upload-asset" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/logo.png" \
  -F "clientId=client-uuid-123" \
  -F "name=Company Logo"
```

**Example Request (JavaScript/Fetch):**

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('clientId', 'client-uuid-123');
formData.append('name', 'Company Logo');

const response = await fetch('/api/v2/upload-asset', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const asset = await response.json();
```

**Response (201 Created):**

Returns the full Asset object as a discriminated union. The exact fields depend on the `type` discriminator:

**Image Asset:**
```json
{
  "id": "asset-uuid-789",
  "userId": 1,
  "clientId": "client-uuid-123",
  "campaignId": null,
  "name": "logo.png",
  "url": "https://api.example.com/api/v2/assets/asset-uuid-789",
  "size": 51200,
  "uploadedAt": "2025-11-16T19:43:00Z",
  "tags": null,
  "type": "image",
  "format": "png",
  "width": 800,
  "height": 600
}
```

**Video Asset:**
```json
{
  "id": "asset-uuid-abc",
  "userId": 1,
  "clientId": null,
  "campaignId": "campaign-uuid-456",
  "name": "product_demo.mp4",
  "url": "https://api.example.com/api/v2/assets/asset-uuid-abc",
  "size": 12345678,
  "uploadedAt": "2025-11-16T19:43:00Z",
  "tags": null,
  "type": "video",
  "format": "mp4",
  "width": 1920,
  "height": 1080,
  "duration": 30,
  "thumbnailUrl": "https://api.example.com/api/v2/assets/asset-uuid-abc/thumbnail"
}
```

**Audio Asset:**
```json
{
  "id": "asset-uuid-def",
  "userId": 1,
  "clientId": null,
  "campaignId": "campaign-uuid-456",
  "name": "voiceover.mp3",
  "url": "https://api.example.com/api/v2/assets/asset-uuid-def",
  "size": 2048000,
  "uploadedAt": "2025-11-16T19:43:00Z",
  "tags": null,
  "type": "audio",
  "format": "mp3",
  "duration": 60,
  "waveformUrl": null
}
```

**Document Asset:**
```json
{
  "id": "asset-uuid-ghi",
  "userId": 1,
  "clientId": "client-uuid-123",
  "campaignId": null,
  "name": "brand_guidelines.pdf",
  "url": "https://api.example.com/api/v2/assets/asset-uuid-ghi",
  "size": 1024000,
  "uploadedAt": "2025-11-16T19:43:00Z",
  "tags": null,
  "type": "document",
  "format": "pdf",
  "pageCount": null,
  "thumbnailUrl": null
}
```

---

### 2. List Assets

**Endpoint:** `GET /api/v2/assets`

**Authentication:** Required (Bearer token)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `clientId` | String | No | Filter by client ID |
| `campaignId` | String | No | Filter by campaign ID |
| `asset_type` | String | No | Filter by type: 'image', 'video', 'audio', 'document' |
| `limit` | Integer | No | Max results (default: 50, max: 100) |
| `offset` | Integer | No | Pagination offset (default: 0) |

**Example Requests:**

```bash
# Get all assets for current user
GET /api/v2/assets

# Get all assets for a specific client
GET /api/v2/assets?clientId=client-uuid-123

# Get all video assets for a campaign
GET /api/v2/assets?campaignId=campaign-uuid-456&asset_type=video

# Get images with pagination
GET /api/v2/assets?asset_type=image&limit=20&offset=0
```

**Response (200 OK):**

Returns an array of Asset objects (discriminated union):

```json
[
  {
    "id": "asset-uuid-abc",
    "userId": 1,
    "clientId": "client-uuid-123",
    "campaignId": null,
    "name": "logo.png",
    "url": "https://api.example.com/api/v2/assets/asset-uuid-abc",
    "size": 51200,
    "uploadedAt": "2025-11-16T18:00:00Z",
    "tags": null,
    "type": "image",
    "format": "png",
    "width": 800,
    "height": 600
  },
  {
    "id": "asset-uuid-xyz",
    "userId": 1,
    "clientId": "client-uuid-123",
    "campaignId": "campaign-uuid-456",
    "name": "product_video.mp4",
    "url": "https://api.example.com/api/v2/assets/asset-uuid-xyz",
    "size": 10485760,
    "uploadedAt": "2025-11-16T19:00:00Z",
    "tags": null,
    "type": "video",
    "format": "mp4",
    "width": 1920,
    "height": 1080,
    "duration": 45,
    "thumbnailUrl": "https://api.example.com/api/v2/assets/asset-uuid-xyz/thumbnail"
  }
]
```

---

### 3. Get Asset File

**Endpoint:** `GET /api/v2/assets/{asset_id}`

**Authentication:** None (public endpoint for file serving)

**Description:** Serves the actual asset file (image, video, audio, or document).

**Example:**

```bash
GET /api/v2/assets/asset-uuid-abc
# Returns the actual file with appropriate Content-Type
```

**Use Cases:**
- Display images: `<img src="/api/v2/assets/{asset_id}" />`
- Play videos: `<video src="/api/v2/assets/{asset_id}" />`
- Download documents: Direct link to file

---

### 4. Get Asset Thumbnail

**Endpoint:** `GET /api/v2/assets/{asset_id}/thumbnail`

**Authentication:** None (public endpoint)

**Description:** Serves the auto-generated thumbnail for video or document assets.

**Note:** Only available if the asset has a `thumbnailUrl` field.

**Example:**

```bash
GET /api/v2/assets/asset-uuid-abc/thumbnail
# Returns JPEG thumbnail
```

**Use Cases:**
- Video previews: `<img src="/api/v2/assets/{asset_id}/thumbnail" />`
- Document previews

---

### 5. Delete Asset

**Endpoint:** `DELETE /api/v2/assets/{asset_id}`

**Authentication:** Required (Bearer token, owner only)

**Description:** Deletes an asset and its associated files (including thumbnails).

**Example Request:**

```bash
curl -X DELETE "https://api.example.com/api/v2/assets/asset-uuid-abc" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Asset asset-uuid-abc deleted successfully"
}
```

**Error Responses:**
- `404 Not Found`: Asset doesn't exist
- `403 Forbidden`: User doesn't own the asset

---

## TypeScript Types

For frontend TypeScript projects, use these types:

```typescript
// Base asset fields (common to all types)
interface BaseAsset {
  id: string;
  userId: number | null;
  clientId: string | null;
  campaignId: string | null;
  name: string;
  url: string;
  size: number | null;
  uploadedAt: string;  // ISO 8601
  tags: string[] | null;
  format: string;
}

// Image asset
interface ImageAsset extends BaseAsset {
  type: 'image';
  width: number;
  height: number;
}

// Video asset
interface VideoAsset extends BaseAsset {
  type: 'video';
  width: number;
  height: number;
  duration: number;  // seconds
  thumbnailUrl: string | null;
}

// Audio asset
interface AudioAsset extends BaseAsset {
  type: 'audio';
  duration: number;  // seconds
  waveformUrl: string | null;
}

// Document asset
interface DocumentAsset extends BaseAsset {
  type: 'document';
  pageCount: number | null;
  thumbnailUrl: string | null;
}

// Discriminated union
type Asset = ImageAsset | VideoAsset | AudioAsset | DocumentAsset;
```

**Type Guard Example:**

```typescript
function isVideoAsset(asset: Asset): asset is VideoAsset {
  return asset.type === 'video';
}

// Usage
if (isVideoAsset(asset)) {
  console.log(`Video duration: ${asset.duration}s`);
  console.log(`Thumbnail: ${asset.thumbnailUrl}`);
}
```

---

## Migration Guide

### If You Were Using Old Endpoints

**Before:**
```javascript
// Upload client asset
POST /api/clients/{clientId}/assets
FormData: { file }

// Upload campaign asset
POST /api/campaigns/{campaignId}/assets
FormData: { file }
```

**After:**
```javascript
// Upload asset with client association
POST /api/v2/upload-asset
FormData: { file, clientId }

// Upload asset with campaign association
POST /api/v2/upload-asset
FormData: { file, campaignId }

// Upload asset with BOTH associations
POST /api/v2/upload-asset
FormData: { file, clientId, campaignId }
```

### Retrieving Assets

**Before:** No unified way to get client/campaign assets

**After:**
```javascript
// Get all client assets
GET /api/v2/assets?clientId=client-uuid-123

// Get all campaign assets
GET /api/v2/assets?campaignId=campaign-uuid-456

// Get all video assets for a campaign
GET /api/v2/assets?campaignId=campaign-uuid-456&asset_type=video
```

---

## Frontend Workflow Examples

### 1. Upload Client Logo

```typescript
async function uploadClientLogo(clientId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('clientId', clientId);
  formData.append('name', 'Company Logo');

  const response = await fetch('/api/v2/upload-asset', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });

  const asset: Asset = await response.json();

  if (asset.type === 'image') {
    console.log(`Logo uploaded: ${asset.width}x${asset.height}`);
  }

  return asset;
}
```

### 2. Upload Campaign Video

```typescript
async function uploadCampaignVideo(campaignId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('campaignId', campaignId);

  const response = await fetch('/api/v2/upload-asset', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });

  const asset: Asset = await response.json();

  if (asset.type === 'video') {
    console.log(`Video uploaded: ${asset.duration}s`);
    console.log(`Thumbnail available at: ${asset.thumbnailUrl}`);
  }

  return asset;
}
```

### 3. Display Client Assets Gallery

```typescript
async function loadClientAssets(clientId: string) {
  const response = await fetch(
    `/api/v2/assets?clientId=${clientId}&asset_type=image`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );

  const assets: Asset[] = await response.json();

  // Render gallery
  return assets.map(asset => {
    if (asset.type === 'image') {
      return `<img src="${asset.url}" alt="${asset.name}" />`;
    }
  });
}
```

### 4. Display Campaign Video Gallery with Thumbnails

```typescript
async function loadCampaignVideos(campaignId: string) {
  const response = await fetch(
    `/api/v2/assets?campaignId=${campaignId}&asset_type=video`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );

  const assets: Asset[] = await response.json();

  return assets.map(asset => {
    if (asset.type === 'video') {
      return {
        id: asset.id,
        name: asset.name,
        duration: asset.duration,
        thumbnail: asset.thumbnailUrl,
        videoUrl: asset.url
      };
    }
  });
}
```

---

## Notes

### Automatic Metadata Extraction

When you upload an asset, the backend automatically extracts:

- **Images:** Width, height, file size
- **Videos:** Width, height, duration, generates thumbnail at 1 second
- **Audio:** Duration, file size
- **Documents:** File size, page count (planned)

### File Storage

- Assets are stored in `DATA/assets/{asset_id}.{format}`
- Thumbnails are stored in `DATA/assets/{asset_id}_thumb.jpg`
- Files are served via `/api/v2/assets/{asset_id}`

### Cascading Deletes

When a client or campaign is deleted, all associated assets are automatically deleted (cascade).

### Error Handling

Common error responses:

```json
// 400 Bad Request - Invalid file type
{
  "detail": "Invalid file type: image/bmp. Allowed: images (jpg, png, gif, webp), videos (mp4, mov), audio (mp3, wav), documents (pdf)"
}

// 400 Bad Request - File too large
{
  "detail": "File too large. Maximum size is 50.0MB"
}

// 404 Not Found - Asset doesn't exist
{
  "detail": "Asset not found"
}

// 403 Forbidden - User doesn't own asset
{
  "detail": "You don't have permission to delete this asset"
}
```

---

## Questions or Issues?

If you encounter any issues or have questions about the Asset API, please contact the backend team or file an issue in the repository.
