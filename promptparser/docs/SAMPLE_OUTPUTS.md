# Sample Parser Outputs

These examples capture real response shapes returned by `/v1/parse`. Each sample highlights a different multimodal path (text-only, image-primary, video-primary) and includes the required metadata (confidence scores, cost estimates, provider used).

> **Note:** Example payloads are trimmed for readability; ellipses (`…`) indicate additional unchanged fields that match the documented schema.

---

## 1. Text-Only Prompt — Luxury Watch Instagram Ad

**Request**

```json
POST /v1/parse
{
  "prompt": {
    "text": "Create a 30 second Instagram ad for a luxury gold watch with dramatic lighting."
  },
  "options": {
    "include_cost_estimate": true
  }
}
```

**Response (excerpt)**

```json
{
  "status": "success",
  "creative_direction": {
    "product": {
      "name": "luxury gold chronograph",
      "category": "accessories_jewelry",
      "price_tier": "luxury"
    },
    "technical_specs": {
      "duration": 30,
      "aspect_ratio": "9:16",
      "platform": "instagram",
      "resolution": "1080x1920",
      "fps": 30
    },
    "visual_direction": {
      "aesthetic": "modern_luxury",
      "style_source": "text",
      "color_palette": [
        {"hex": "#D4AF37", "role": "primary"},
        {"hex": "#111111", "role": "background"},
        {"hex": "#FFFFFF", "role": "accent"}
      ],
      "lighting_style": "dramatic_soft_shadows",
      "camera_style": "smooth_gimbal_cinematic"
    },
    "audio_direction": {
      "music_genre": "neo_classical",
      "mood": ["aspirational", "confident"]
    },
    "text_strategy": {
      "overlays": [
        {
          "text": "Timeless Precision",
          "start_time": 0.0,
          "end_time": 3.0,
          "position": "bottom_third",
          "animation": "fade_in"
        }
      ]
    }
  },
  "scenes": [
    {
      "id": "scene_1_hook",
      "scene_number": 1,
      "purpose": "hook",
      "duration": 3.0,
      "visual": {
        "shot_type": "extreme_close_up",
        "generation_prompt": "macro shot of gold watch gears…"
      }
    },
    {
      "id": "scene_5_cta",
      "scene_number": 5,
      "purpose": "cta",
      "duration": 6.0,
      "text_overlay": {
        "text": "SHOP NOW",
        "style": "bold_cta"
      }
    }
  ],
  "metadata": {
    "confidence_score": 0.87,
    "confidence_breakdown": {
      "product_understanding": 0.95,
      "style_clarity": 0.8,
      "technical_feasibility": 0.86
    },
    "warnings": [],
    "defaults_used": ["resolution", "fps"],
    "llm_provider_used": "openai",
    "cache_hit": false
  },
  "cost_estimate": {
    "total_usd": 1.6,
    "breakdown": {
      "video_generation": 1.5,
      "audio_generation": 0.1
    },
    "confidence": "medium"
  }
}
```

---

## 2. Image-Primary Prompt — Athletic Shoe Launch

**Request**

```json
POST /v1/parse
{
  "prompt": {
    "text": "Match this reference sneaker photo and make a 20s TikTok hype spot.",
    "image_url": "https://cdn.example.com/refs/sneaker-drop.jpg"
  },
  "options": {
    "include_cost_estimate": true,
    "target_category": "ad_creative"
  }
}
```

**Response (excerpt)**

```json
{
  "creative_direction": {
    "technical_specs": {
      "duration": 20,
      "aspect_ratio": "9:16",
      "platform": "tiktok",
      "fps": 30
    },
    "visual_direction": {
      "aesthetic": "high_energy_streetwear",
      "style_source": "image",
      "color_palette": [
        {"hex": "#FF0044", "role": "accent"},
        {"hex": "#0A0A0A", "role": "background"},
        {"hex": "#F7F7F7", "role": "secondary"}
      ],
      "lighting_style": "neon_rim",
      "scene_types": ["urban_track", "studio_product_spin"]
    },
    "audio_direction": {
      "music_genre": "trap_edm",
      "tempo": 132,
      "mood": ["amped", "confident"]
    }
  },
  "scenes": [
    {
      "id": "scene_1_flash",
      "purpose": "hook",
      "duration": 2.5,
      "visual": {
        "shot_type": "wide_shot",
        "generation_prompt": "urban rooftop night race with neon streaks…"
      },
      "text_overlay": {
        "text": "DROP DAY",
        "position": "top_third",
        "animation": "glitch"
      }
    },
    {
      "id": "scene_4_macro",
      "purpose": "product_showcase",
      "duration": 4.0,
      "visual": {
        "shot_type": "extreme_close_up",
        "generation_prompt": "macro spin on sneaker sole with glowing edges…"
      }
    }
  ],
  "extracted_references": {
    "images": [
      {
        "source": "user_upload",
        "analysis": {
          "dominant_colors": ["#FF0044", "#0A0A0A", "#F7F7F7"],
          "lighting": "neon_edge",
          "mood": "high_voltage"
        }
      }
    ]
  },
  "metadata": {
    "confidence_score": 0.9,
    "confidence_breakdown": {
      "product_understanding": 0.82,
      "style_clarity": 0.95,
      "technical_feasibility": 0.88
    },
    "llm_provider_used": "openai",
    "cache_hit": false
  },
  "cost_estimate": {
    "total_usd": 1.05,
    "breakdown": {
      "video_generation": 0.9,
      "audio_generation": 0.15
    },
    "confidence": "high"
  }
}
```

---

## 3. Video-Primary Prompt — Skincare Routine Explainer

**Request**

```json
POST /v1/parse
{
  "prompt": {
    "text": "Mirror this competitor video vibe for my skincare duo. Keep it calm and premium.",
    "video_url": "https://cdn.example.com/refs/skincare-routine.mp4"
  },
  "options": {
    "include_cost_estimate": true,
    "llm_provider": "openai"
  }
}
```

**Response (excerpt)**

```json
{
  "creative_direction": {
    "product": {
      "name": "LumaSkin Radiance Duo",
      "category": "beauty_skincare"
    },
    "technical_specs": {
      "duration": 45,
      "aspect_ratio": "16:9",
      "platform": "youtube"
    },
    "visual_direction": {
      "aesthetic": "spa_grade_minimalism",
      "style_source": "video",
      "color_palette": [
        {"hex": "#F4EDE5", "role": "background"},
        {"hex": "#A7D1C9", "role": "accent"},
        {"hex": "#2F2F2F", "role": "text"}
      ],
      "lighting_style": "soft_diffused",
      "camera_style": "slider_macro"
    },
    "audio_direction": {
      "music_genre": "ambient_chill",
      "tempo": 78,
      "intensity_curve": "sustained"
    }
  },
  "scenes": [
    {
      "id": "scene_2_steps",
      "purpose": "context",
      "duration": 12.0,
      "visual": {
        "shot_type": "medium_shot",
        "generation_prompt": "model applying serum in sunlit bathroom…",
        "reference_image_index": 0
      }
    },
    {
      "id": "scene_4_cta",
      "purpose": "cta",
      "duration": 8.0,
      "text_overlay": {
        "text": "GLOW IN 2 STEPS",
        "style": "minimal_badge",
        "position": "bottom_third"
      }
    }
  ],
  "extracted_references": {
    "images": [
      {
        "source": "video_frame",
        "frame_type": "first",
        "analysis": {
          "dominant_colors": ["#F4EDE5", "#A7D1C9"],
          "lighting": "soft_diffused",
          "composition": "rule_of_thirds"
        }
      },
      {
        "source": "video_frame",
        "frame_type": "last",
        "analysis": {
          "dominant_colors": ["#E8F2EF", "#2F2F2F"],
          "lighting": "studio_soft",
          "mood": "calming"
        }
      }
    ]
  },
  "metadata": {
    "confidence_score": 0.92,
    "confidence_breakdown": {
      "product_understanding": 0.88,
      "style_clarity": 0.97,
      "technical_feasibility": 0.9
    },
    "llm_provider_used": "openai",
    "warnings": [
      "Scene 3 overlay might require >3s for readability"
    ]
  },
  "cost_estimate": {
    "total_usd": 2.4,
    "breakdown": {
      "video_generation": 2.1,
      "audio_generation": 0.2,
      "text_to_speech": 0.1
    },
    "confidence": "medium"
  }
}
```

---

### How to Reproduce Locally

1. Start the API (`uvicorn app.main:app --reload`).
2. Ensure Redis is running (`docker run -p 6379:6379 redis:7-alpine`).
3. Use the accompanying `tests/test_parse_endpoint.py` fixtures or the example curl commands above.
4. Capture JSON responses and store them under `docs/SAMPLE_OUTPUTS.md` for future demos or judge packets.

