# Asset Upload API - Usage Examples

## Quick Start

### 1. Upload an Asset

```bash
# Upload an image
curl -X POST http://localhost:8000/api/v2/upload-asset \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/image.jpg"

# Response:
{
  "success": true,
  "url": "http://localhost:8000/api/v2/assets/098a4f86-fbc5-4507-99c3-2723e6e79399",
  "asset_id": "098a4f86-fbc5-4507-99c3-2723e6e79399",
  "filename": "image.jpg",
  "size_bytes": 245890
}
```

### 2. List Your Assets

```bash
curl http://localhost:8000/api/v2/assets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response:
{
  "success": true,
  "assets": [
    {
      "asset_id": "098a4f86-fbc5-4507-99c3-2723e6e79399",
      "filename": "image.jpg",
      "file_type": "image/jpeg",
      "size_bytes": 245890,
      "uploaded_at": "2025-11-15T12:34:56",
      "url": "http://localhost:8000/api/v2/assets/098a4f86-fbc5-4507-99c3-2723e6e79399"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

### 3. Get an Asset (Public URL)

```bash
# Anyone can access this (no auth required)
curl http://localhost:8000/api/v2/assets/098a4f86-fbc5-4507-99c3-2723e6e79399 \
  --output downloaded_image.jpg
```

### 4. Delete an Asset

```bash
curl -X DELETE http://localhost:8000/api/v2/assets/098a4f86-fbc5-4507-99c3-2723e6e79399 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response:
{
  "success": true,
  "message": "Asset 098a4f86-fbc5-4507-99c3-2723e6e79399 deleted successfully"
}
```

## Python Client Example

```python
import requests

class AssetClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def upload(self, file_path):
        """Upload an asset and return its URL"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/api/v2/upload-asset",
                files=files,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def list_assets(self, limit=50, offset=0):
        """List user's assets"""
        response = requests.get(
            f"{self.base_url}/api/v2/assets",
            params={"limit": limit, "offset": offset},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def delete(self, asset_id):
        """Delete an asset"""
        response = requests.delete(
            f"{self.base_url}/api/v2/assets/{asset_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = AssetClient("http://localhost:8000", "your_jwt_token")

# Upload
result = client.upload("image.jpg")
print(f"Uploaded: {result['url']}")

# List
assets = client.list_assets()
print(f"Total assets: {len(assets['assets'])}")

# Delete
client.delete(result['asset_id'])
print("Deleted")
```

## JavaScript/TypeScript Example

```typescript
class AssetClient {
  constructor(
    private baseUrl: string,
    private token: string
  ) {}

  async upload(file: File): Promise<AssetUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/v2/upload-asset`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async listAssets(limit = 50, offset = 0): Promise<AssetListResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v2/assets?limit=${limit}&offset=${offset}`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );

    if (!response.ok) {
      throw new Error(`List failed: ${response.statusText}`);
    }

    return response.json();
  }

  async delete(assetId: string): Promise<DeleteResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v2/assets/${assetId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );

    if (!response.ok) {
      throw new Error(`Delete failed: ${response.statusText}`);
    }

    return response.json();
  }
}

// Types
interface AssetUploadResponse {
  success: boolean;
  url: string;
  asset_id: string;
  filename: string;
  size_bytes: number;
}

interface AssetListResponse {
  success: boolean;
  assets: Asset[];
  limit: number;
  offset: number;
}

interface Asset {
  asset_id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  uploaded_at: string;
  url: string;
}

interface DeleteResponse {
  success: boolean;
  message: string;
}

// Usage
const client = new AssetClient('http://localhost:8000', 'your_jwt_token');

// Upload from file input
const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
const file = fileInput.files?.[0];
if (file) {
  const result = await client.upload(file);
  console.log('Uploaded:', result.url);
}

// List assets
const assets = await client.listAssets();
console.log('Total assets:', assets.assets.length);

// Delete
await client.delete('asset-id-here');
console.log('Deleted');
```

## Integration with Video Generation

### Image-to-Video Workflow

```python
import requests

base_url = "http://localhost:8000"
token = "your_jwt_token"
headers = {"Authorization": f"Bearer {token}"}

# Step 1: Upload image asset
with open("source_image.jpg", "rb") as f:
    upload_response = requests.post(
        f"{base_url}/api/v2/upload-asset",
        files={"file": f},
        headers=headers
    )
    upload_response.raise_for_status()
    asset_url = upload_response.json()["url"]

print(f"Image uploaded: {asset_url}")

# Step 2: Use asset in video generation
video_request = {
    "prompt": "Make the person in this image wave hello",
    "model_id": "minimax/video-01",
    "input": {
        "image": asset_url,  # Public URL accessible by Replicate
        "prompt": "person waving hello",
        "first_frame_image": asset_url
    }
}

video_response = requests.post(
    f"{base_url}/api/v2/generate",
    json=video_request,
    headers=headers
)
video_response.raise_for_status()
job_id = video_response.json()["job_id"]

print(f"Video generation started: job {job_id}")

# Step 3: Poll for completion
import time
while True:
    status_response = requests.get(
        f"{base_url}/api/v2/jobs/{job_id}",
        headers=headers
    )
    status_response.raise_for_status()
    job = status_response.json()

    if job["status"] == "completed":
        print(f"Video ready: {job['video_url']}")
        break
    elif job["status"] == "failed":
        print(f"Generation failed: {job.get('error_message')}")
        break

    time.sleep(2)
```

## Error Handling

### Common Errors

```python
import requests

def upload_with_error_handling(file_path, token):
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                "http://localhost:8000/api/v2/upload-asset",
                files={'file': f},
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            error = e.response.json()
            if "Invalid file type" in error.get("detail", ""):
                print("Error: File type not supported")
                print("Supported: jpg, jpeg, png, gif, webp, mp4, mov")
            elif "File too large" in error.get("detail", ""):
                print("Error: File exceeds 50MB limit")
            else:
                print(f"Error: {error.get('detail')}")

        elif e.response.status_code == 401:
            print("Error: Invalid or expired token")

        elif e.response.status_code == 429:
            print("Error: Rate limit exceeded (max 10 uploads/minute)")
            print("Please wait and try again")

        elif e.response.status_code == 500:
            print("Error: Server error during upload")
            print("Please try again or contact support")

        else:
            print(f"Error: {e.response.status_code} - {e.response.text}")

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")

    except Exception as e:
        print(f"Error: {str(e)}")

    return None
```

## Best Practices

1. **Check file size before upload**
   ```python
   import os
   file_size = os.path.getsize(file_path)
   max_size = 50 * 1024 * 1024  # 50MB
   if file_size > max_size:
       print(f"File too large: {file_size / (1024*1024):.2f}MB (max: 50MB)")
       return
   ```

2. **Validate file type before upload**
   ```python
   import mimetypes
   mime_type, _ = mimetypes.guess_type(file_path)
   allowed = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'video/mp4', 'video/quicktime'}
   if mime_type not in allowed:
       print(f"File type {mime_type} not supported")
       return
   ```

3. **Implement retry logic for uploads**
   ```python
   import time
   max_retries = 3
   for attempt in range(max_retries):
       try:
           result = upload_asset(file_path, token)
           break
       except requests.exceptions.RequestException as e:
           if attempt < max_retries - 1:
               print(f"Upload failed (attempt {attempt + 1}/{max_retries}), retrying...")
               time.sleep(2 ** attempt)  # Exponential backoff
           else:
               raise
   ```

4. **Clean up old assets**
   ```python
   def cleanup_old_assets(client, days=30):
       """Delete assets older than X days"""
       from datetime import datetime, timedelta

       assets = client.list_assets(limit=100)
       cutoff = datetime.now() - timedelta(days=days)

       for asset in assets['assets']:
           uploaded = datetime.fromisoformat(asset['uploaded_at'])
           if uploaded < cutoff:
               print(f"Deleting old asset: {asset['filename']}")
               client.delete(asset['asset_id'])
   ```

## Rate Limiting

The upload endpoint is rate-limited to **10 uploads per minute per user**.

If you hit the rate limit:
```json
{
  "detail": "Too many requests"
}
```

**Handling rate limits:**
```python
import time

def upload_with_rate_limit_handling(files, client):
    results = []
    for i, file_path in enumerate(files):
        try:
            result = client.upload(file_path)
            results.append(result)

            # Throttle to stay under rate limit
            if (i + 1) % 9 == 0:  # After 9 uploads
                print("Rate limit approaching, waiting 60 seconds...")
                time.sleep(60)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                # Retry this upload
                result = client.upload(file_path)
                results.append(result)

    return results
```

## Monitoring Upload Progress

For large files, you may want to show upload progress:

```python
import requests
from tqdm import tqdm

def upload_with_progress(file_path, token, base_url):
    """Upload with progress bar"""
    file_size = os.path.getsize(file_path)

    with open(file_path, 'rb') as f:
        with tqdm(total=file_size, unit='B', unit_scale=True, desc=file_path) as pbar:
            def monitor(monitor):
                pbar.update(len(monitor))

            files = {'file': f}
            response = requests.post(
                f"{base_url}/api/v2/upload-asset",
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()
```
