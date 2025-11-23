# Project Log: Two-Stage Property Photo Selection - Debugging Session
**Date**: 2025-11-22
**Session Focus**: Debugging and fixing production deployment issues with two-stage property photo selection system

## Session Summary
This session focused on debugging critical production issues preventing the two-stage property photo selection feature from working. Multiple deployment issues were identified and resolved, including import path errors, API method signature mismatches, database query filtering problems, and frontend parameter formatting issues.

## Changes Made

### 1. Import Path Corrections (backend/api/v3/router.py:2110-2112)
**Issue**: ModuleNotFoundError when calling `/jobs/from-property-photos`
- Changed `from ..services` → `from ...services`
- Changed `from ..database_helpers` → `from ...database_helpers`
- Services directory is at `backend/services/`, not `backend/api/services/`
- Router at `backend/api/v3/router.py` needs three dots to reach backend root

**Commit**: `f1a4b27` - "fix: correct import paths in property photos endpoint"

### 2. Grok API Method Signature Fix (backend/services/xai_client.py:728-763)
**Issues**:
- TypeError: `_call_grok_api()` got unexpected keyword argument 'temperature'
- Missing required `image_assets` parameter

**Changes**:
- Added `temperature` parameter with default `0.7`
- Made `image_assets` optional with default `None`
- Updated call in `_select_room_types` (line 271) to pass both parameters

**Commits**:
- `77bd3db` - "fix: add temperature parameter to _call_grok_api method"
- `b516a56` - "fix: pass image_assets parameter in _select_room_types call"

### 3. Campaign Listing Database Query (backend/database_helpers.py:703-727)
**Issue**: Empty campaign list when `user_id=None` passed from API
- Old code had hardcoded `WHERE user_id = ?` which matched nothing when `user_id=None`
- SQL query was: `WHERE user_id = NULL` (matches NOTHING)

**Solution**: Dynamic query building
```python
# Build conditions dynamically - only add WHERE clauses for non-None values
if user_id is not None:
    conditions.append("user_id = ?")
if client_id:
    conditions.append("client_id = ?")
```

**Commit**: `c538e66` - "fix: allow list_campaigns to return all campaigns when user_id=None"

### 4. Client ID Whitespace Handling (backend/api/v3/router.py:332)
**Issue**: Frontend sending `client_id=%209c57cc62...` (with `%20` = space before UUID)
- Query was searching for `" 9c57cc62..."` (with leading space)
- Didn't match actual `"9c57cc62..."` in database

**Solution**: Strip whitespace from client_id before querying
```python
clean_client_id = client_id.strip() if client_id else None
```

**Commit**: `0696f29` - "fix: strip whitespace from client_id parameter in campaigns endpoint"

## Database State Verification
Production database (`/data/scenes.db`) confirmed healthy:
- **9 campaigns** exist
- **2 clients** including Wander client
- **603 images** available

## Two-Stage Selection Implementation Summary
Location: `backend/services/xai_client.py:37-336`

### Stage 1: Room Instance Selection (lines 213-296)
- Groups images by room instance (removes last number from tags)
- Example: "Bedroom 1 2" → "Bedroom 1"
- Grok AI selects which N room instances to use (e.g., 7 from 20)
- Uses lower temperature (0.3) for consistent selection

### Stage 2: Deterministic Pair Selection (lines 298-336)
- For each selected room instance: grabs first 2 images
- No LLM call - completely deterministic
- Never uses same image twice
- Ensures variety across room types

## Deployment Notes
All fixes deployed to production via Fly.io:
- App health checks: ✓ Passing
- Database migrations: ✓ Complete
- Machine status: ✓ Started

## Current Issues Remaining

### Video Generation Job Failures
**Status**: Failed jobs with status "failed"
- Jobs create successfully (ID: 155)
- Progress shows `selected_pairs: 7`
- But final status is "failed" with no error message
- `estimatedCost: 0`, `actualCost: 0`, `videoUrl: ""`

**Debug Data Available**:
```json
{
  "raw_parameters": "{'campaign_id': '680b18ae...', 'client_id': '9c57cc62...', ...}",
  "parameter_parse_success": true,
  "audio_debug": { "status": "not_requested" }
}
```

**Next Steps Needed**:
1. Check video generation logs for actual error
2. Investigate why job transitions to "failed" after pair selection
3. Verify Replicate API integration for video interpolation
4. Check sub-job processing in `process_image_pairs_to_videos`

## Testing Artifacts Created
- `test_two_stage_local.py` - Local testing script
- `test_two_stage_production.py` - Production testing script
- `test_property_photos_v3.py` - V3 API testing
- Debug logs: `log_docs/two_stage_selection.md`

## Code References
- Import fixes: `backend/api/v3/router.py:2110-2112`
- API method signature: `backend/services/xai_client.py:728-763`
- Room selection call: `backend/services/xai_client.py:271`
- Campaign list query: `backend/database_helpers.py:703-727`
- Client ID sanitization: `backend/api/v3/router.py:332`

## Next Session Priorities
1. **Critical**: Debug video generation job failure after pair selection
2. Investigate Replicate API errors in production logs
3. Test complete end-to-end property video workflow
4. Monitor Grok API usage and costs
5. Add better error messages for failed jobs

## Session Duration
Approximately 2 hours of debugging and deployment iterations
