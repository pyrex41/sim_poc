# Two-Stage Property Photo Selection - Debugging Session Summary
**Date:** November 22, 2025
**Branch:** simple
**Status:** Pair selection working, video generation failing

---

## Session Overview

This debugging session focused on fixing multiple deployment issues preventing the two-stage property photo selection feature from working in production. While image pair selection now works correctly, video generation jobs are still failing.

---

## Fixes Deployed

### 1. Import Path Corrections
**File:** `backend/api/v3/router.py:2110-2112`
**Commit:** `f1a4b27`

```python
# Changed from ..services to ...services
from ...services.property_photo_selector import PropertyPhotoSelector
from ...services.sub_job_orchestrator import process_image_pairs_to_videos
from ...database_helpers import create_asset, get_campaign_by_id, get_client_by_id
```

### 2. Grok API Method Signature
**File:** `backend/services/xai_client.py:728-763, line 271`
**Commits:** `77bd3db`, `b516a56`

```python
# Added temperature parameter and made image_assets optional
def _call_grok_api(
    self, prompt: str, image_assets: List[Dict[str, Any]] = None, temperature: float = 0.7
) -> Dict[str, Any]:
    if image_assets is None:
        image_assets = []
```

### 3. Dynamic Database Query Building
**File:** `backend/database_helpers.py:703-727`
**Commit:** `c538e66`

```python
# Build conditions dynamically - only add WHERE clauses for non-None values
query = "SELECT * FROM campaigns"
conditions = []
params = []

if user_id is not None:
    conditions.append("user_id = ?")
    params.append(user_id)

if client_id:
    conditions.append("client_id = ?")
    params.append(client_id)

if conditions:
    query += " WHERE " + " AND ".join(conditions)
```

### 4. Client ID Sanitization
**File:** `backend/api/v3/router.py:332`
**Commit:** `0696f29`

```python
# Strip whitespace from client_id parameter
clean_client_id = client_id.strip() if client_id else None
campaigns = list_campaigns(user_id=None, client_id=clean_client_id, ...)
```

---

## Current Status

### ✅ Working
- Import paths resolved
- Grok API calls succeed
- Campaign listing returns data
- Client ID matching works
- Image pair selection completes (shows `selected_pairs: 7`)

### ❌ Failing
- Video generation jobs end with status "failed"
- No error messages captured in job metadata
- `estimatedCost: 0`, `actualCost: 0`, `videoUrl: ""`

---

## Next Steps

1. **Debug video generation failure**
   - Check production logs for actual error
   - Investigate Replicate API integration
   - Verify sub-job processing in `process_image_pairs_to_videos`

2. **Test complete end-to-end workflow**
   - Monitor Grok API usage and costs
   - Verify video output quality
   - Add better error messages for failed jobs

---

## Database State (Verified)
- **9 campaigns** exist
- **2 clients** including Wander client
- **603 images** available
- Database: `/data/scenes.db` (935MB, healthy)

---

## Two-Stage Selection Implementation

**Location:** `backend/services/xai_client.py:37-336`

**Stage 1: Room Instance Selection** (lines 213-296)
- Groups images by room instance (e.g., "Bedroom 1 2" → "Bedroom 1")
- Grok AI selects which N room instances to use
- Lower temperature (0.3) for consistent selection

**Stage 2: Deterministic Pair Selection** (lines 298-336)
- For each selected room instance: grabs first 2 images
- No LLM call - completely deterministic
- Never uses same image twice
- Ensures variety across room types

---

**Checkpoint Created:** `fe2b3bb`
**Progress Log:** `log_docs/PROJECT_LOG_2025-11-22_two-stage-property-selection-debugging.md`
