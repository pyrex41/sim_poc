# Image Pairing Debug Logging - Implementation Summary

**Date:** November 22, 2025
**Purpose:** Add comprehensive logging to debug image pairing input/output and tag associations

---

## Issues Identified

### 1. **Duplicate Name/Description Bug** ✅ FIXED
- **Location:** `backend/api/v3/router.py:1956`
- **Problem:** Description was set to the same value as name
  ```python
  "description": getattr(asset, "name", ""),  # Use name as description
  ```
- **Impact:** Grok received identical name and description, reducing context quality
- **Fix:** Now creates meaningful descriptions from name + tags:
  ```python
  description_parts = [name]
  if tags:
      description_parts.append(f"Tags: {', '.join(tags)}")
  description = " | ".join(description_parts)
  ```

### 2. **Tags Not Properly Parsed**
- **Problem:** Tags stored as JSON string in DB might not be deserialized
- **Fix:** Added proper JSON parsing with fallback:
  ```python
  tags = getattr(asset, "tags", [])
  if isinstance(tags, str):
      try:
          tags = json.loads(tags)
      except:
          tags = []
  ```

### 3. **No Visibility into AI Workflow**
- **Problem:** Couldn't see what Grok received or returned
- **Fix:** Added comprehensive logging at every stage

---

## Logging Added

### Stage 1: Asset Data Preparation (`router.py:1952-1992`)

**What it logs:**
- Number of assets being processed
- Each asset's ID, name, and tags
- Summary of how many assets have tags

**Example output:**
```
[IMAGE PAIRING] Preparing asset data for 23 images
[IMAGE PAIRING] Asset 1/23: id=abc123def456... name='pool-sunset.jpg' tags=['exterior', 'pool', 'water']
[IMAGE PAIRING] Asset 2/23: id=def789abc012... name='bedroom-view.jpg' tags=['bedroom', 'interior', 'windows']
...
[IMAGE PAIRING] Asset data summary: 23 assets with tags=23
```

### Stage 2: Prompt Construction (`xai_client.py:405-431`)

**What it logs:**
- How each asset is formatted in the prompt
- Full list of images with their metadata

**Example output:**
```
[PROMPT BUILDER] Building image list for 23 assets
[PROMPT BUILDER] Image 1: id=abc123def456... name='pool-sunset.jpg' tags=[exterior, pool, water]
[PROMPT BUILDER] Image 2: id=def789abc012... name='bedroom-view.jpg' tags=[bedroom, interior, windows]
...
```

### Stage 3: Full Prompt to Grok (`xai_client.py:74-78`)

**What it logs:**
- Complete prompt sent to Grok (including all scene requirements)
- Prompt character count

**Example output:**
```
[GROK PROMPT] ===== FULL PROMPT START =====
You are an expert luxury real estate cinematographer...

SCENE 1: THE HOOK (Exterior Feature) - Duration: 1.5s
...

AVAILABLE IMAGES (23 total photos from property):
Image 1:
  ID: abc123def456...
  Name: pool-sunset.jpg
  Tags: exterior, pool, water
  Description: pool-sunset.jpg | Tags: exterior, pool, water
...
[GROK PROMPT] ===== FULL PROMPT END =====
[GROK PROMPT] Prompt length: 12847 characters
```

### Stage 4: Raw Grok Response (`xai_client.py:543-554`)

**What it logs:**
- Full API response from Grok
- Parsed JSON structure
- Response content length

**Example output:**
```
[GROK RAW RESPONSE] ===== FULL API RESPONSE START =====
{
  "id": "chatcmpl-...",
  "choices": [
    {
      "message": {
        "content": "{\"pairs\": [{\"image1_id\": \"...\", ...}]}"
      }
    }
  ]
}
[GROK RAW RESPONSE] ===== FULL API RESPONSE END =====
[GROK RAW RESPONSE] Content length: 3421 characters

[GROK PARSED JSON] ===== PARSED JSON START =====
{
  "pairs": [
    {
      "image1_id": "abc123...",
      "image2_id": "def456...",
      "score": 0.92,
      "scene_number": 1,
      "scene_name": "The Hook (Exterior Feature)",
      "reasoning": "Wide pool shot to close-up..."
    },
    ...
  ]
}
[GROK PARSED JSON] ===== PARSED JSON END =====
```

### Stage 5: Pair Validation (`xai_client.py:568-610`)

**What it logs:**
- Available asset IDs for validation
- Each pair being processed
- Validation decision (ACCEPTED/REJECTED) with reasons
- Why rejected pairs failed

**Example output:**
```
[GROK VALIDATION] Available asset IDs: 23 total
[GROK VALIDATION] Sample IDs: ['abc123...', 'def456...', 'ghi789...']

[GROK VALIDATION] Processing pair 1/7
[GROK VALIDATION] Pair data: {
  "image1_id": "abc123...",
  "image2_id": "def456...",
  "score": 0.92,
  "scene_number": 1,
  "scene_name": "The Hook (Exterior Feature)"
}
[GROK VALIDATION] Pair 1: scene=1 (The Hook (Exterior Feature)) img1=abc123def456... img2=def789abc012... score=0.92
[GROK VALIDATION] ACCEPTED Pair 1

[GROK VALIDATION] Processing pair 2/7
[GROK VALIDATION] REJECTED Pair 2: Invalid image1_id: xyz999..., not in asset list
```

### Stage 6: Final Selected Pairs (`xai_client.py:85-92`)

**What it logs:**
- Number of successfully selected pairs
- Each pair's IDs, score, and reasoning (truncated)

**Example output:**
```
[GROK RESPONSE] Successfully selected 7 image pairs
[GROK RESPONSE] Pair 1: abc123def456...→def789abc012... score=0.92 reason='Wide pool shot to close-up of water edge. Perfect for dolly forward with glistening wat...'
[GROK RESPONSE] Pair 2: ghi789jkl012...→mno345pqr678... score=0.88 reason='Master bedroom photos from slightly different lateral positions. Clear foreground (bed) an...'
...
```

---

## How to Use This Logging

### Running a Test

1. **Start local backend:**
   ```bash
   uv run uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
   ```

2. **Trigger image pair selection:**
   ```bash
   curl -X POST http://localhost:8001/api/v3/videos/generate-from-image-pairs \
     -H "X-API-Key: YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{"campaignId": "YOUR_CAMPAIGN_ID", "numPairs": 7}'
   ```

3. **Watch the logs** for the prefixed output:
   - `[IMAGE PAIRING]` - Asset preparation in router
   - `[PROMPT BUILDER]` - Prompt construction
   - `[GROK PROMPT]` - Full prompt to Grok
   - `[GROK RAW RESPONSE]` - Raw API response
   - `[GROK PARSED JSON]` - Parsed JSON structure
   - `[GROK VALIDATION]` - Pair validation logic
   - `[GROK RESPONSE]` - Final selected pairs

### What to Look For

#### ✅ Good Signs:
- All assets have tags: `[IMAGE PAIRING] Asset data summary: 23 assets with tags=23`
- Descriptions include tags: `Description: pool-sunset.jpg | Tags: exterior, pool, water`
- All 7 pairs accepted: `[GROK VALIDATION] ACCEPTED Pair 1` through `ACCEPTED Pair 7`
- No rejected pairs

#### ⚠️ Warning Signs:
- Assets missing tags: `tags=[]` or `tags=0`
- Duplicate name/description (should be fixed now)
- REJECTED pairs with reasons

#### 🚨 Red Flags:
- `No pairs found in response` - Grok didn't return pairs
- `No valid pairs after validation` - All pairs rejected
- `Invalid image1_id` / `Invalid image2_id` - Grok returning wrong IDs
- Same image used twice in a pair

---

## Files Modified

1. **`backend/api/v3/router.py`** (lines 1951-1992)
   - Fixed duplicate name/description bug
   - Added tag JSON parsing
   - Added comprehensive asset logging

2. **`backend/services/xai_client.py`** (multiple locations)
   - Added prompt logging (lines 74-78)
   - Added raw response logging (lines 543-554)
   - Added parsed JSON logging (lines 550-554)
   - Added validation logging (lines 562-610)
   - Added final pairs logging (lines 85-92)
   - Enhanced prompt builder logging (lines 405-431)

---

## Next Steps

1. **Test with real data** to verify:
   - Tags are correctly associated with images
   - Descriptions are meaningful (not just duplicate names)
   - Grok is receiving and using the tag information
   - Pairs are logically grouped by scene requirements

2. **Analyze Grok's reasoning** from logs:
   - Does it mention the tags in its reasoning?
   - Is it selecting images that match the scene requirements?
   - Are the confidence scores reasonable (0.7-1.0)?

3. **Optimize if needed:**
   - Adjust prompt if Grok ignores tags
   - Add more metadata to descriptions if helpful
   - Refine scene requirements based on actual images

---

**Status:** ✅ Ready for testing
**Expected Impact:** 10x better visibility into AI image pairing workflow
