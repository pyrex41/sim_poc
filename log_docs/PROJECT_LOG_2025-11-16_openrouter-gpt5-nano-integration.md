# Project Log: OpenRouter GPT-5-nano Integration & Creative Brief Enhancements
**Date:** 2025-11-16
**Session Focus:** OpenRouter integration, creative brief workflow fixes, and image generation feature groundwork

## Summary
This session involved integrating OpenRouter with GPT-5-nano as the primary LLM provider for the creative brief generator, fixing multiple bugs in the creative brief workflow, and beginning implementation of a brief-to-images generation feature.

---

## Changes Made

### 1. OpenRouter Integration with GPT-5-nano ✅

**Files Modified:**
- `backend/config.py`
- `backend/prompt_parser_service/core/config.py`
- `backend/prompt_parser_service/core/dependencies.py`
- `backend/prompt_parser_service/services/llm/openrouter_provider.py` (new)

**Implementation Details:**
- Created new `OpenRouterProvider` class (`openrouter_provider.py:1-97`)
  - Uses OpenAI-compatible API at `https://openrouter.ai/api/v1`
  - Configured with model `openai/gpt-5-nano-2025-08-07`
  - Implements `complete()` and `analyze_image()` methods
  - Pricing: $0.05 per 1M input tokens, $0.40 per 1M output tokens

- Added `OPENROUTER_API_KEY` configuration to both Settings classes
  - Main backend config (`config.py:21`)
  - Prompt parser config (`core/config.py:16`)

- Updated LLM provider registry (`dependencies.py:30-32`)
  - OpenRouter registered as primary provider (when API key present)
  - Fallback order: OpenRouter → OpenAI → Claude
  - Changed `DEFAULT_LLM_PROVIDER` from "openai" to "openrouter"

- Deployed API key as Fly.io secret
  - Key configured securely without exposing in codebase
  - Server successfully restarted and validated

### 2. Creative Brief Bug Fixes ✅

#### 2.1 Fixed `primary_name` NameError

**Problem:** `NameError: name 'primary_name' is not defined` occurring in parse endpoint
- Variable was defined inside `process_parse_request()` function
- Referenced in outer `parse_prompt()` function scope
- Caused 500 errors when generating creative briefs

**Solution** (`parse.py:165-168`):
```python
# Determine primary LLM provider
settings = get_settings()
default_provider = "mock" if settings.USE_MOCK_LLM else settings.DEFAULT_LLM_PROVIDER
primary_name = parse_request.options.llm_provider or default_provider
```

#### 2.2 Enhanced Scene Schema Specification

**File:** `backend/prompt_parser_service/prompts/creative_direction.py`

**Problem:** LLM was returning scenes in incorrect format:
- `id` as integer instead of string
- Missing `scene_number` field
- `visual` as string instead of object

**Solution** (`creative_direction.py:46-65`):
- Added explicit scene schema example to system prompt
- Specified required field types for each scene property
- Added `IMPORTANT` note with clear field requirements
- Model now generates correctly structured scenes matching Pydantic schema

### 3. Workflow Separation: Physics vs. Creative Briefs ✅

**File:** `backend/prompt_parser_service/api/v1/parse.py`

**Problem:** Creative brief endpoint was auto-triggering physics scene generation
- Caused `ImportError: No module named 'main'`
- Mixed concerns between creative brief generation and physics simulation
- User wanted these as separate workflows

**Solution** (`parse.py:195-198`):
```python
# NOTE: Physics scene auto-generation is disabled here
# Physics scenes should be generated separately via the /api/physics/generate endpoint
# This keeps the creative brief generation focused on prompt parsing and brief creation
# The generation_prompt in scenes can be used later for physics simulation generation
```

**Architecture Clarification:**
1. **Creative Brief Generation** (`/api/creative/parse`)
   - Parses prompts using GPT-5-nano
   - Generates structured briefs with scenes
   - Each scene includes `generation_prompt` field
   - Does NOT generate physics simulations

2. **Physics Scene Generation** (separate endpoint)
   - Takes `generation_prompt` from brief scenes
   - Generates physics simulations using Replicate
   - Triggered separately by user action

### 4. Image Generation Feature (In Progress) 🚧

**File:** `src/CreativeBriefEditor.elm`

**Started Implementation:**
- Added `imageModels`, `selectedImageModel`, `loadingImageModels`, `generatingImages` to Model (`CreativeBriefEditor.elm:36-39`)
- Created `ImageModel` type alias (`:43-47`)
- Added new Msg variants (`:148-152`):
  - `FetchImageModels`
  - `ImageModelsFetched`
  - `SelectImageModel`
  - `GenerateImages`
  - `ImagesGenerated`
- Updated init function to fetch image models on page load
- Changed default LLM provider to "openrouter" in Elm frontend

**Remaining Work:**
- Add update handlers for new messages
- Implement `fetchImageModels` HTTP request
- Implement `generateImagesFromBrief` HTTP request
- Add image model dropdown to UI
- Add "Generate Images" button
- Create backend endpoint `/api/generate-images-from-brief`
- Implement navigation to Image Gallery with generated images

---

## Deployment Status

**Platform:** Fly.io
**App:** gauntlet-video-server
**Status:** ✅ Healthy and Running

**Deployments This Session:**
1. Initial OpenRouter integration
2. Settings cache fix (added OPENROUTER_API_KEY to prompt parser config)
3. Scene validation fix (updated system prompt)
4. Physics auto-generation removal
5. Final deployment with all fixes

**Server Details:**
- URL: `https://gauntlet-video-server.fly.dev`
- Health endpoint: `/health` returning `{"status":"healthy"}`
- Last restart: 03:50:41 UTC
- No errors in recent logs

---

## Task-Master Status

**Issue:** Task-master JSON file corrupted
- Error: "Property name must be a string literal"
- Located at: `.taskmaster/tasks/tasks.json`
- **Action Required:** Manual JSON validation and repair needed

---

## Current Todo List

1. ✅ OpenRouter with GPT-5-nano integration
2. ✅ Fix creative brief scene validation
3. ✅ Separate physics generation from creative brief workflow
4. 🚧 Add image model dropdown to Creative Brief Editor (Elm)
5. ⏳ Implement brief-to-images generation workflow

---

## Next Steps

### Immediate (In Progress)
1. Complete Elm implementation for image generation:
   - Add update handlers for new messages
   - Implement HTTP request functions
   - Add UI components (dropdown, button)

2. Create backend endpoint for batch image generation:
   - `/api/generate-images-from-brief`
   - Accept array of prompts with model IDs
   - Queue background tasks for each image
   - Return array of image IDs

3. Implement navigation to Image Gallery:
   - Navigate to `/images` route after generation
   - Display generated images
   - Filter by collection or brief ID

### Future Enhancements
1. Add loading states and progress indicators
2. Link generated images back to source brief
3. Allow editing generation prompts before creating images
4. Add batch regeneration capability
5. Implement image-to-video workflow (already exists for single images)

---

## Code References

### Key Files Modified
- `backend/prompt_parser_service/services/llm/openrouter_provider.py` - New OpenRouter LLM provider
- `backend/prompt_parser_service/api/v1/parse.py:165-168` - Fixed primary_name scope issue
- `backend/prompt_parser_service/prompts/creative_direction.py:46-65` - Enhanced scene schema
- `backend/prompt_parser_service/api/v1/parse.py:195-198` - Removed physics auto-gen
- `src/CreativeBriefEditor.elm:22-47` - Added image generation model fields

### Deployment Commands Used
```bash
./deploy.sh
fly secrets set OPENROUTER_API_KEY="..."
fly machine restart 28675d0b499498
fly logs --app gauntlet-video-server --no-tail
```

---

## Technical Notes

### OpenRouter Model Details
- **Model ID:** `openai/gpt-5-nano-2025-08-07`
- **Type:** Smallest/fastest GPT-5 variant
- **Use Case:** Developer tools, rapid interactions, ultra-low latency
- **Limitations:** Limited reasoning depth vs larger models
- **Strengths:** Fast, cost-effective, instruction-following, safety features

### Scene Validation Schema
Required fields per scene:
- `id`: String (e.g., "scene_1")
- `scene_number`: Integer (1, 2, 3, ...)
- `purpose`: String describing scene role
- `duration`: Float in seconds
- `visual`: Object with `shot_type`, `subject`, `generation_prompt`

### Provider Priority Order
1. OpenRouter (GPT-5-nano) - Primary
2. OpenAI (GPT-4o) - Fallback 1
3. Claude - Fallback 2
4. Mock - Development only

---

## Issues Encountered & Resolutions

### Issue 1: Settings Cache Problem
**Problem:** New `OPENROUTER_API_KEY` field not available in Settings object
**Cause:** Two separate Settings classes with different fields
**Solution:** Added `OPENROUTER_API_KEY` to both config files
**Files:** `backend/config.py` and `backend/prompt_parser_service/core/config.py`

### Issue 2: Import Path Error
**Problem:** `from main import` failing in parse.py
**Cause:** Incorrect relative import path
**Solution:** Changed to `from ....main import` (4 levels up)
**Note:** Ultimately removed as feature was separated

### Issue 3: LLM Response Format
**Problem:** GPT-5-nano returning old scene format
**Cause:** System prompt lacked explicit schema specification
**Solution:** Added detailed scene schema with field types to system prompt
**Result:** Model now generates correctly formatted scenes

---

## Lessons Learned

1. **Multiple Config Files:** Project has two Settings classes - main backend and prompt parser service. Both need to be updated for new env vars.

2. **LLM Prompt Specificity:** Even advanced models like GPT-5 need explicit schema examples. Generic instructions aren't sufficient for complex nested structures.

3. **Workflow Separation:** Auto-triggering features can cause unexpected dependencies. Keep workflows separate and explicit.

4. **Elm Model Complexity:** Adding fields to Elm model requires updates in multiple places (Model type, init function, update handlers, view). Plan changes carefully.

5. **Deployment Strategy:** Fly.io machines require restart to pick up new code. Health checks confirm successful deployment.

---

## Project Status

**Overall Progress:** Steady advancement on creative brief workflow
**Blockers:** None currently blocking
**Code Quality:** Good - proper error handling, separation of concerns
**Technical Debt:** Task-master JSON needs repair
**User-Facing Features:** Creative brief generation fully functional with GPT-5-nano
