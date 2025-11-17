# Asset Upload: Type and Tags Parameters

## Overview
The `/api/v2/upload-asset` endpoint now supports two additional optional parameters:
1. **`type`** - Override the automatically inferred asset type
2. **`tags`** - Add string array tags to the asset for categorization

## Usage

### Basic Upload (existing behavior)
```bash
curl -X POST http://localhost:8000/api/v2/upload-asset \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@image.jpg" \
  -F "clientId=client-uuid-123" \
  -F "name=My Image"
```

### Upload with Type Override
```bash
curl -X POST http://localhost:8000/api/v2/upload-asset \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "clientId=client-uuid-123" \
  -F "type=document" \
  -F "name=Brand Guidelines"
```

**Valid type values:** `image`, `video`, `audio`, `document`

**Behavior:**
- If `type` is provided, it overrides the automatically inferred type
- If `type` is not provided, type is inferred from the file's content type
- If type cannot be inferred, defaults to `document`

### Upload with Tags
```bash
curl -X POST http://localhost:8000/api/v2/upload-asset \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@logo.png" \
  -F "clientId=client-uuid-123" \
  -F "name=Company Logo" \
  -F 'tags=["brand", "logo", "primary"]'
```

**Tags format:**
- Must be a valid JSON array of strings
- Example: `'["brand", "logo", "primary"]'`
- All elements must be strings
- Can be empty array: `'[]'`

### Upload with Both Type and Tags
```bash
curl -X POST http://localhost:8000/api/v2/upload-asset \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@video.mp4" \
  -F "clientId=client-uuid-123" \
  -F "campaignId=campaign-uuid-456" \
  -F "type=video" \
  -F "name=Product Demo" \
  -F 'tags=["product", "demo", "2024"]'
```

## Response

The asset response now includes the tags:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "1",
  "clientId": "client-uuid-123",
  "campaignId": "campaign-uuid-456",
  "type": "video",
  "format": "mp4",
  "name": "Product Demo",
  "url": "https://api.example.com/api/v2/assets/550e8400-e29b-41d4-a716-446655440000",
  "size": 15728640,
  "uploadedAt": "2025-11-17T10:30:00Z",
  "tags": ["product", "demo", "2024"],
  "width": 1920,
  "height": 1080,
  "duration": 30,
  "thumbnailUrl": "https://api.example.com/api/v2/assets/550e8400-e29b-41d4-a716-446655440000/thumbnail"
}
```

## Python Example

```python
import requests
import json

def upload_asset_with_tags(
    file_path: str,
    client_id: str,
    auth_token: str,
    asset_type: str = None,
    tags: list = None,
    campaign_id: str = None,
    name: str = None
):
    url = "http://localhost:8000/api/v2/upload-asset"

    headers = {
        "Authorization": f"Bearer {auth_token}"
    }

    files = {
        "file": open(file_path, "rb")
    }

    data = {
        "clientId": client_id,
    }

    if campaign_id:
        data["campaignId"] = campaign_id

    if name:
        data["name"] = name

    if asset_type:
        data["type"] = asset_type

    if tags:
        data["tags"] = json.dumps(tags)

    response = requests.post(url, headers=headers, files=files, data=data)
    return response.json()

# Example usage
asset = upload_asset_with_tags(
    file_path="brand_logo.png",
    client_id="client-123",
    auth_token="your-auth-token",
    asset_type="image",
    tags=["brand", "logo", "primary"],
    name="Company Logo"
)

print(f"Uploaded asset: {asset['id']}")
print(f"Tags: {asset['tags']}")
```

## JavaScript Example

```javascript
async function uploadAssetWithTags(
  file,
  clientId,
  authToken,
  { type, tags, campaignId, name } = {}
) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('clientId', clientId);

  if (campaignId) formData.append('campaignId', campaignId);
  if (name) formData.append('name', name);
  if (type) formData.append('type', type);
  if (tags) formData.append('tags', JSON.stringify(tags));

  const response = await fetch('http://localhost:8000/api/v2/upload-asset', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`
    },
    body: formData
  });

  return await response.json();
}

// Example usage
const fileInput = document.querySelector('input[type="file"]');
const file = fileInput.files[0];

const asset = await uploadAssetWithTags(
  file,
  'client-123',
  'your-auth-token',
  {
    type: 'image',
    tags: ['brand', 'logo', 'primary'],
    name: 'Company Logo'
  }
);

console.log('Uploaded asset:', asset.id);
console.log('Tags:', asset.tags);
```

## Validation Rules

### Type Parameter
- **Optional**: If not provided, type is inferred from file content type
- **Valid values**: `image`, `video`, `audio`, `document`
- **Error**: Returns 400 if invalid type is provided

### Tags Parameter
- **Optional**: If not provided, tags will be `null`
- **Format**: JSON array of strings, e.g., `'["tag1", "tag2"]'`
- **Validation**:
  - Must be valid JSON
  - Must be an array
  - All array elements must be strings
- **Error**: Returns 400 if format is invalid

## Database Schema

Tags are stored as JSON TEXT in the `assets` table:

```sql
CREATE TABLE assets (
    -- ... other columns ...
    tags TEXT,  -- JSON array stored as text, e.g., '["brand", "logo"]'
    -- ... other columns ...
);
```

## Benefits

### Type Override
- **Use case**: When file content type doesn't accurately reflect the intended use
- **Example**: Treating a PDF as a document even if content type is ambiguous
- **Fallback**: If type inference fails, explicitly specify the correct type

### Tags
- **Search & Filter**: Easily find assets by tags (e.g., "all brand assets")
- **Organization**: Categorize assets by project, client, campaign, etc.
- **Metadata**: Add contextual information without modifying asset properties
- **Future**: Enable tag-based filtering in GET endpoints

## Migration Notes

- ✅ Database schema already includes `tags` column (TEXT)
- ✅ Pydantic models already include `tags: Optional[list[str]]`
- ✅ Backend properly serializes/deserializes tags as JSON
- ✅ No breaking changes - both parameters are optional
- ✅ Existing assets without tags will have `tags: null`

## Future Enhancements

Potential improvements for tags feature:
1. Add tag filtering to GET endpoints (`?tags=brand,logo`)
2. Tag autocomplete/suggestions based on existing tags
3. Tag management endpoints (rename, merge tags)
4. Tag analytics (most used tags, tag relationships)
5. Predefined tag categories (e.g., "brand", "product", "seasonal")
