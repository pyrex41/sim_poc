# Two-Stage Image Pair Selection

**Implementation Date:** 2025-11-22
**Status:** Ready for deployment

## Overview

Completely redesigned image pairing workflow to ensure pairs are from the same room and leverage room-tagged imagery for luxury property videos.

## Problem Solved

**Previous Approach (Broken):**
- Single LLM call with all 5-100 images
- No guarantee pairs were from same room
- Selected random logical transitions (exterior → pool → kitchen)
- Not using room-based tags effectively
- Result: Pairs of different rooms, poor visual continuity

**New Approach (Two-Stage):**
- **Stage 1:** LLM selects which 7 room types to feature
- **Stage 2:** For each room, LLM selects best 2 images from that room (parallel)
- Guarantees pairs are from same room
- Reduces context per LLM call (10-25 images vs 100)
- Leverages existing tag structure perfectly

## Workflow

### Stage 1: Room Type Selection (Single LLM Call)

**Input:**
```
Available Room Types:
- Bedroom: 25 images
- Kitchen: 11 images
- Ensuite Bathroom: 10 images
- Exterior: 11 images
- Pool: 3 images
- Living Room: 4 images
- Patio: 8 images
- Dining Room: 4 images
- Tv Room: 7 images
```

**LLM Task:**
- Select 7 most compelling room types for video narrative
- Must include: 1 bedroom, 1 bathroom, 1 exterior/outdoor
- Balance public/private spaces
- Create cohesive property tour

**Output:**
```json
{
  "selected_rooms": [
    "Bedroom",
    "Ensuite Bathroom",
    "Kitchen",
    "Living Room",
    "Pool",
    "Exterior",
    "Patio"
  ]
}
```

### Stage 2: Image Pair Selection (7 Parallel LLM Calls)

**For Each Selected Room:**

**Input (Example: Bedroom):**
```
AVAILABLE BEDROOM IMAGES (25 total):
1. ID: abc-123
   Name: Master bedroom with city view
   Tags: ["Bedroom 1 1"]
2. ID: abc-124
   Name: Master bedroom close-up
   Tags: ["Bedroom 1 2"]
... (23 more)
```

**LLM Task:**
- Select best 2 images from this specific room
- Ensure visual continuity (similar lighting, colors)
- Create natural camera movement (wide → close-up)
- Maximize feature showcase

**Output:**
```json
{
  "image1_id": "abc-123",
  "image2_id": "abc-124",
  "score": 0.95,
  "reasoning": "Wide to close-up progression showcasing city view and bed details"
}
```

**All 7 rooms processed in parallel → 7 pairs in ~same time as 1**

## Implementation Details

### Files Modified

**`backend/services/xai_client.py`:**
- Added `_group_assets_by_room()` - Extracts room types from tags
- Rewrote `select_image_pairs()` - Orchestrates two-stage workflow
- Added `_single_stage_selection()` - Fallback for non-property videos
- Added `_select_room_types()` - Stage 1 implementation
- Added `_select_pair_from_room()` - Stage 2 implementation

### Room Type Extraction

Tags like `["Bedroom 1 2"]` → Extract `"Bedroom"`

Handles multi-word rooms:
- `["Ensuite Bathroom 1 1"]` → `"Ensuite Bathroom"`
- `["Dining Room 3"]` → `"Dining Room"`
- `["Half Bath 2"]` → `"Half Bath"`
- `["Tv Room 5"]` → `"Tv Room"`

### Parallel Execution

Stage 2 uses `ThreadPoolExecutor` with max 7 workers:
- All 7 room selections happen simultaneously
- Total time ≈ single LLM call (not 7x slower)
- Each worker handles one room independently

### Fallback Scenarios

**Fallback to Single-Stage if:**
1. `num_pairs != 7` (not a property video)
2. Fewer room types than pairs needed
3. Stage 1 room selection fails

**Fallback in Stage 2:**
- If room has only 1 image: duplicate it
- If Grok call fails: use first 2 images from room
- Result: Always get pairs, even with errors

## Expected Behavior

### With 100-Image Campaign

**Stage 1 Output:**
```
[TWO-STAGE STAGE 1] Grouped 100 images into 15 room types
[TWO-STAGE STAGE 1]   Bedroom: 25 images
[TWO-STAGE STAGE 1]   Kitchen: 11 images
[TWO-STAGE STAGE 1]   Ensuite Bathroom: 10 images
[TWO-STAGE STAGE 1]   Exterior: 11 images
...
[ROOM SELECTION] Asking Grok to select 7 rooms from 15 options
[TWO-STAGE STAGE 1] Selected 7 room types: ['Bedroom', 'Ensuite Bathroom', ...]
```

**Stage 2 Output:**
```
[TWO-STAGE STAGE 2] Selecting image pairs for 7 rooms (parallel)
[TWO-STAGE STAGE 2] ✓ Bedroom: Selected pair
[TWO-STAGE STAGE 2] ✓ Kitchen: Selected pair
[TWO-STAGE STAGE 2] ✓ Ensuite Bathroom: Selected pair
[TWO-STAGE STAGE 2] ✓ Living Room: Selected pair
[TWO-STAGE STAGE 2] ✓ Pool: Selected pair
[TWO-STAGE STAGE 2] ✓ Exterior: Selected pair
[TWO-STAGE STAGE 2] ✓ Patio: Selected pair
[TWO-STAGE] Successfully selected 7 pairs using two-stage approach
```

### With Small Campaign (5 images)

Falls back to single-stage selection:
```
[TWO-STAGE] Only 3 room types available, but need 7 pairs. Falling back to single-stage selection.
[SINGLE-STAGE] Prompt length: 2328 characters
[SINGLE-STAGE] Successfully selected 4 pairs
```

## Logging & Debug

All logs prefixed with:
- `[TWO-STAGE]` - Main orchestration
- `[TWO-STAGE STAGE 1]` - Room grouping and selection
- `[ROOM SELECTION]` - Grok room selection call
- `[TWO-STAGE STAGE 2]` - Parallel pair selection
- `[PAIR SELECTION {room}]` - Individual room pair selection
- `[SINGLE-STAGE]` - Fallback mode

Debug file `/data/image_pairing_debug.log` still captures all Grok prompts/responses.

## Testing Plan

1. **Deploy to production**
2. **Test with campaign:** `caff3d1a-f201-40fb-8dbe-ba922c07f2a5` (100 images, 15 room types)
3. **Expected:**
   - 7 room types selected
   - 7 pairs generated
   - All pairs from same room
   - Parallel execution visible in logs
4. **Check debug logs for:**
   - Room selection prompt/response
   - 7 individual pair selection prompts/responses
   - Final 7 pairs with room types

## Advantages

✅ **Guaranteed same-room pairs** - Images in a pair are always from same room
✅ **Intelligent room selection** - LLM chooses best rooms for narrative
✅ **Scalable** - Works with 20-100+ images equally well
✅ **Efficient** - Parallel Stage 2 = fast execution
✅ **Leverages existing tags** - Uses room structure already in DB
✅ **Fallback support** - Degrades gracefully for edge cases
✅ **Better context** - Each LLM call sees only relevant images (10-25 vs 100)

## Next Steps

1. Deploy and test with real campaign
2. Monitor logs for Stage 1/Stage 2 execution
3. Verify pairs are from same room
4. Tune prompts based on results
5. Consider caching room selections for same campaign
