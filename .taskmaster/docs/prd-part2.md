# Physics Sim → Veo 3.1 Pipeline

Perfect! Veo 3.1 is arguably the best model for this. Let me show you the actual integration.

---

## 1. Veo 3.1 API Integration

### 1.1 Setup (Google Vertex AI)

```python
# backend/integrations/veo.py

from google.cloud import aiplatform
from google.oauth2 import service_account
import base64
from typing import Optional, List
import asyncio

class Veo31Client:
    def __init__(
        self, 
        project_id: str,
        location: str = "us-central1",
        credentials_path: Optional[str] = None
    ):
        self.project_id = project_id
        self.location = location
        
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            aiplatform.init(
                project=project_id,
                location=location,
                credentials=credentials
            )
        else:
            aiplatform.init(project=project_id, location=location)
        
        self.client = aiplatform.gapic.PredictionServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )
    
    async def generate_from_reference(
        self,
        prompt: str,
        reference_video_path: Optional[str] = None,
        reference_image_path: Optional[str] = None,
        duration: int = 5,
        resolution: str = "1080p",
        aspect_ratio: str = "16:9",
        motion_strength: float = 0.8,
        style_strength: float = 0.7
    ) -> dict:
        """
        Generate video with Veo 3.1
        
        Args:
            prompt: Text description
            reference_video_path: Path to physics sim video (for motion reference)
            reference_image_path: Path to style reference image
            duration: Duration in seconds (up to 20s with Veo 3.1)
            resolution: "480p", "720p", "1080p"
            motion_strength: 0.0-1.0, how much to preserve reference motion
            style_strength: 0.0-1.0, how much to preserve reference style
        """
        
        # Prepare inputs
        instances = [{
            "prompt": prompt,
            "parameters": {
                "duration": duration,
                "resolution": resolution,
                "aspect_ratio": aspect_ratio,
                "fps": 30,  # Veo 3.1 outputs at 30fps
            }
        }]
        
        # Add reference video if provided
        if reference_video_path:
            with open(reference_video_path, 'rb') as f:
                video_bytes = f.read()
                video_b64 = base64.b64encode(video_bytes).decode('utf-8')
            
            instances[0]["reference_video"] = {
                "video_bytes": video_b64,
                "motion_guidance_strength": motion_strength
            }
        
        # Add reference image if provided (for style)
        if reference_image_path:
            with open(reference_image_path, 'rb') as f:
                image_bytes = f.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            instances[0]["reference_image"] = {
                "image_bytes": image_b64,
                "style_strength": style_strength
            }
        
        # Call Veo 3.1 API
        endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/veo-003"
        
        response = await asyncio.to_thread(
            self.client.predict,
            endpoint=endpoint,
            instances=instances
        )
        
        # Parse response
        result = response.predictions[0]
        
        return {
            "video_url": result.get("gcs_uri"),  # GCS path to output
            "video_bytes": result.get("video_bytes"),  # Or direct bytes
            "generation_id": result.get("generation_id")
        }
    
    async def generate_with_keyframes(
        self,
        prompt: str,
        keyframes: List[dict],
        duration: int = 5
    ) -> dict:
        """
        Generate video using keyframe guidance
        
        Keyframes: List of {"timestamp": float, "image_path": str}
        """
        
        keyframe_inputs = []
        for kf in keyframes:
            with open(kf["image_path"], 'rb') as f:
                img_bytes = f.read()
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            
            keyframe_inputs.append({
                "timestamp_seconds": kf["timestamp"],
                "image_bytes": img_b64
            })
        
        instances = [{
            "prompt": prompt,
            "keyframes": keyframe_inputs,
            "parameters": {
                "duration": duration,
                "resolution": "1080p"
            }
        }]
        
        endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/veo-003"
        
        response = await asyncio.to_thread(
            self.client.predict,
            endpoint=endpoint,
            instances=instances
        )
        
        result = response.predictions[0]
        return {
            "video_url": result.get("gcs_uri"),
            "video_bytes": result.get("video_bytes")
        }
```

---

## 2. Optimized Reference Generation for Veo

### 2.1 Keyframe Extraction Strategy

**Veo 3.1 works REALLY well with keyframes** - you can give it key poses from your physics sim:

```python
# backend/veo_optimizer.py

class VeoPhysicsOptimizer:
    """Optimize physics sim output specifically for Veo 3.1"""
    
    def __init__(self):
        self.renderer = SceneRenderer(resolution=(1920, 1080))
    
    def extract_keyframes(
        self,
        scene: Scene,
        num_keyframes: int = 5,
        strategy: str = "uniform"  # uniform, critical_moments, velocity_peaks
    ) -> List[dict]:
        """
        Extract key frames from physics simulation
        
        Strategies:
        - uniform: Evenly spaced frames
        - critical_moments: Impact, apex, rest points
        - velocity_peaks: High velocity moments
        """
        
        gs_scene = self._build_genesis_scene(scene)
        
        # Simulate and track
        frames = []
        velocities = []
        
        for frame_idx in range(300):
            gs_scene.step()
            
            # Render frame
            frame = gs_scene.render(rgb=True)
            frames.append(frame)
            
            # Track velocities for critical moments
            max_vel = max(
                entity.get_vel().magnitude() 
                for entity in gs_scene.entities.values()
            )
            velocities.append(max_vel)
        
        # Select keyframes based on strategy
        if strategy == "uniform":
            indices = np.linspace(0, len(frames)-1, num_keyframes, dtype=int)
        
        elif strategy == "critical_moments":
            indices = self._find_critical_moments(velocities, num_keyframes)
        
        elif strategy == "velocity_peaks":
            indices = self._find_velocity_peaks(velocities, num_keyframes)
        
        # Extract and save keyframes
        keyframes = []
        for idx in indices:
            timestamp = idx / 60.0  # 60 fps
            keyframe_path = f"./temp/keyframe_{idx:04d}.png"
            
            # Save as high-quality PNG
            cv2.imwrite(
                keyframe_path,
                cv2.cvtColor(frames[idx], cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_PNG_COMPRESSION, 0]  # No compression
            )
            
            keyframes.append({
                "timestamp": timestamp,
                "image_path": keyframe_path,
                "frame_index": idx
            })
        
        return keyframes
    
    def _find_critical_moments(self, velocities: List[float], num_keyframes: int) -> List[int]:
        """
        Find critical moments: start, impacts, apex, end
        """
        
        critical_indices = [0]  # Start
        
        # Find impacts (sudden deceleration)
        velocity_changes = np.diff(velocities)
        impact_indices = np.where(velocity_changes < -5.0)[0]  # Threshold
        
        # Find apex (low velocity after high)
        apex_candidates = []
        for i in range(1, len(velocities)-1):
            if velocities[i-1] > 2.0 and velocities[i] < 1.0:
                apex_candidates.append(i)
        
        # Combine and sample
        candidates = sorted(set(list(impact_indices) + apex_candidates))
        
        if len(candidates) > num_keyframes - 2:
            # Sample evenly from candidates
            step = len(candidates) // (num_keyframes - 2)
            critical_indices.extend(candidates[::step][:(num_keyframes-2)])
        else:
            critical_indices.extend(candidates)
        
        critical_indices.append(len(velocities) - 1)  # End
        
        return sorted(critical_indices)[:num_keyframes]
    
    def generate_stylized_reference(
        self,
        scene: Scene,
        output_path: str,
        style: str = "clean_cgi"
    ) -> str:
        """
        Generate reference video optimized for Veo
        
        Styles:
        - clean_cgi: Clean, well-lit CGI render (best for Veo)
        - flat_color: Flat design, simple (good for understanding motion)
        - depth_enhanced: Enhanced depth cues
        """
        
        gs_scene = self._build_genesis_scene(scene)
        
        if style == "clean_cgi":
            # Use good lighting, clean materials
            self._setup_studio_lighting(gs_scene)
        
        frames = []
        for frame_idx in range(300):
            gs_scene.step()
            
            if style == "clean_cgi":
                frame = gs_scene.render(rgb=True)
            
            elif style == "flat_color":
                frame = self._render_flat(gs_scene)
            
            elif style == "depth_enhanced":
                rgb = gs_scene.render(rgb=True)
                depth = gs_scene.render(depth=True)
                frame = self._enhance_with_depth(rgb, depth)
            
            frames.append(frame)
        
        # Encode at high quality (Veo prefers good input)
        video_path = f"{output_path}_reference.mp4"
        self._encode_high_quality(frames, video_path)
        
        return video_path
    
    def _encode_high_quality(self, frames: List[np.ndarray], output_path: str):
        """Encode at high bitrate for Veo input"""
        
        h, w = frames[0].shape[:2]
        
        # Use H.264 high profile, high bitrate
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        writer = cv2.VideoWriter(
            output_path, 
            fourcc, 
            30,  # Veo prefers 30fps input
            (w, h)
        )
        
        for frame in frames:
            writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        
        writer.release()
        
        # Could also use ffmpeg for even better quality
        # subprocess.run([
        #     'ffmpeg', '-i', temp_path, '-c:v', 'libx264',
        #     '-preset', 'slow', '-crf', '18', output_path
        # ])
```

---

## 3. Complete Pipeline

### 3.1 Backend API Endpoint

```python
# backend/main.py

from integrations.veo import Veo31Client
from veo_optimizer import VeoPhysicsOptimizer

veo_client = Veo31Client(
    project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
    credentials_path="./gcloud-credentials.json"
)

veo_optimizer = VeoPhysicsOptimizer()

@app.post("/api/physics-to-veo")
async def physics_to_veo(request: PhysicsToVeoRequest):
    """
    Physics simulation → Veo 3.1 video generation
    
    Strategies:
    - keyframes: Extract key poses, let Veo interpolate
    - reference_video: Full video as motion reference
    - hybrid: Keyframes + reference video
    """
    
    job_id = generate_uuid()
    
    # 1. Validate scene
    validation = validate_with_genesis(request.scene)
    if not validation["valid"]:
        raise HTTPException(400, detail=validation["error"])
    
    # Choose strategy based on request
    if request.strategy == "keyframes":
        # Extract keyframes from physics
        keyframes = veo_optimizer.extract_keyframes(
            scene=request.scene,
            num_keyframes=request.num_keyframes or 5,
            strategy=request.keyframe_strategy or "critical_moments"
        )
        
        # Generate with keyframes
        result = await veo_client.generate_with_keyframes(
            prompt=request.prompt,
            keyframes=keyframes,
            duration=request.duration or 5
        )
    
    elif request.strategy == "reference_video":
        # Generate full reference video
        reference_video = veo_optimizer.generate_stylized_reference(
            scene=request.scene,
            output_path=f"./temp/{job_id}",
            style=request.reference_style or "clean_cgi"
        )
        
        # Generate with video reference
        result = await veo_client.generate_from_reference(
            prompt=request.prompt,
            reference_video_path=reference_video,
            reference_image_path=request.style_reference,
            duration=request.duration or 5,
            motion_strength=request.motion_strength or 0.85,
            style_strength=request.style_strength or 0.7
        )
    
    elif request.strategy == "hybrid":
        # Generate reference video
        reference_video = veo_optimizer.generate_stylized_reference(
            scene=request.scene,
            output_path=f"./temp/{job_id}",
            style="clean_cgi"
        )
        
        # Extract keyframes for additional guidance
        keyframes = veo_optimizer.extract_keyframes(
            scene=request.scene,
            num_keyframes=3,
            strategy="critical_moments"
        )
        
        # Use both (Veo 3.1 can handle this)
        result = await veo_client.generate_from_reference(
            prompt=request.prompt,
            reference_video_path=reference_video,
            reference_image_path=request.style_reference,
            duration=request.duration,
            motion_strength=0.9  # High for physics accuracy
        )
    
    return {
        "job_id": job_id,
        "status": "complete",
        "video_url": result["video_url"],
        "generation_id": result.get("generation_id")
    }

@app.post("/api/generate-ad-with-veo")
async def generate_ad_with_veo(request: AdGenerationRequest):
    """
    Simplified ad generation with presets
    """
    
    # 1. Generate or load scene
    if request.scene:
        scene = request.scene
    else:
        # Generate from product description
        scene = await generate_scene_from_product(
            product_type=request.product_type,
            action=request.action
        )
    
    # 2. Build prompt with ad-specific details
    prompt = build_ad_prompt(
        base_description=request.description,
        product_type=request.product_type,
        brand_style=request.brand_style,
        shot_type=request.shot_type,
        lighting=request.lighting
    )
    
    # 3. Generate with Veo
    result = await physics_to_veo(PhysicsToVeoRequest(
        scene=scene,
        prompt=prompt,
        strategy="reference_video",  # Full video works best for ads
        reference_style="clean_cgi",
        style_reference=request.brand_reference_image,
        duration=request.duration or 5,
        motion_strength=0.85
    ))
    
    return result

def build_ad_prompt(
    base_description: str,
    product_type: str,
    brand_style: Optional[str] = None,
    shot_type: str = "product_hero",
    lighting: str = "studio"
) -> str:
    """
    Build optimized prompt for Veo 3.1
    
    Veo responds well to:
    - Cinematography terms
    - Specific camera/lens details
    - Lighting descriptions
    - Brand aesthetic cues
    """
    
    shot_descriptions = {
        "product_hero": "Hero product shot, cinematic composition",
        "lifestyle": "Lifestyle shot, natural environment",
        "close_up": "Extreme close-up, macro photography",
        "dynamic": "Dynamic tracking shot, energetic movement"
    }
    
    lighting_descriptions = {
        "studio": "Professional studio lighting, soft key light with rim light",
        "natural": "Natural daylight, soft shadows, golden hour",
        "dramatic": "Dramatic high-contrast lighting, deep shadows",
        "bright": "Bright even lighting, commercial photography"
    }
    
    # Build comprehensive prompt
    prompt_parts = [
        base_description,
        shot_descriptions.get(shot_type, ""),
        lighting_descriptions.get(lighting, ""),
        "Shot on cinema camera, 4K, professional commercial production",
    ]
    
    if brand_style:
        prompt_parts.append(f"In the style of {brand_style} advertising")
    
    prompt_parts.append(f"Premium {product_type} advertisement")
    
    return ". ".join(p for p in prompt_parts if p) + "."
```

### 3.2 Example Usage

```python
# Example 1: Watch ad with keyframes approach

response = await client.post("/api/generate-ad-with-veo", {
    "product_type": "watch",
    "action": "drop",
    "description": "A luxury Swiss watch falling onto a velvet cushion",
    "brand_style": "Rolex",
    "shot_type": "product_hero",
    "lighting": "dramatic",
    "duration": 5,
    "brand_reference_image": "https://example.com/rolex_ref.jpg"
})

# Veo 3.1 will:
# 1. Use physics sim for accurate fall/bounce motion
# 2. Transform into photorealistic Rolex-style imagery
# 3. Apply dramatic lighting
# 4. Output 1080p, 5-second video

# Example 2: Sneaker with reference video

scene = create_scene_with_text("Nike sneaker bouncing on concrete")
adjust_object_property("sneaker", restitution=0.7)

response = await client.post("/api/physics-to-veo", {
    "scene": scene,
    "prompt": """
        A Nike Air Jordan 1 sneaker bouncing on an urban concrete 
        basketball court. Golden hour lighting, authentic street 
        photography style. Shot on Sony FX6, 24mm lens, shallow 
        depth of field. Energetic, athletic aesthetic.
    """,
    "strategy": "reference_video",
    "duration": 5,
    "motion_strength": 0.9,  # Preserve bounce physics
    "style_strength": 0.7
})

# Example 3: Product reveal with multiple takes

base_scene = create_scene_with_text("iPhone sliding across desk")

# Generate 3 style variations with same physics
variations = []

for style in ["minimalist_apple", "dramatic_dark", "bright_studio"]:
    result = await client.post("/api/physics-to-veo", {
        "scene": base_scene,
        "prompt": STYLE_PROMPTS[style],
        "strategy": "reference_video",
        "duration": 4
    })
    variations.append(result)

# A/B test which performs better
```

---

## 4. Prompt Engineering for Veo + Physics

### 4.1 Prompt Templates

```python
# Best practices for Veo 3.1 prompts

VEO_PROMPT_TEMPLATES = {
    "luxury_product": """
        {product_name} falling onto {surface} in slow motion. 
        Professional studio lighting with soft key light and rim lighting. 
        Reflections on polished surfaces. Shot on Arri Alexa, 50mm lens, 
        f/2.8, shallow depth of field. Premium commercial aesthetic. 
        Clean, sophisticated, high-end production quality.
    """,
    
    "athletic_dynamic": """
        {product_name} {action} on {surface}. Dynamic camera movement, 
        handheld cinematography. Natural outdoor lighting, golden hour. 
        Authentic street energy. Shot on RED Komodo, 24mm lens. 
        High-energy commercial style. Motion blur for speed emphasis.
    """,
    
    "tech_reveal": """
        {product_name} {action} across a minimalist surface. 
        Clean studio environment, perfect white backdrop. 
        Soft diffused lighting, no harsh shadows. Shot on cinema 
        camera with macro lens. Apple keynote aesthetic. 
        Precision, innovation, modern design.
    """,
    
    "lifestyle_narrative": """
        {product_name} in a real-world environment. Natural lighting, 
        authentic setting. Documentary-style cinematography. 
        Shot on cinema camera with handheld movement. Warm, 
        approachable, human-centered. Lifestyle commercial feel.
    """
}

def create_veo_prompt(
    template: str,
    product_name: str,
    action: str = "falling",
    surface: str = "surface",
    additional_details: Optional[str] = None
) -> str:
    """Generate optimized Veo prompt"""
    
    prompt = VEO_PROMPT_TEMPLATES[template].format(
        product_name=product_name,
        action=action,
        surface=surface
    )
    
    if additional_details:
        prompt += f" {additional_details}"
    
    return prompt.strip()
```

### 4.2 Veo-Specific Optimization Tips

```python
# What works well with Veo 3.1:

VEO_BEST_PRACTICES = {
    "camera_terms": [
        "Shot on [camera model]",  # Arri Alexa, RED, Sony FX6
        "[focal length] lens",      # 24mm, 50mm, 85mm
        "f/[aperture]",             # f/1.4, f/2.8
        "shallow depth of field",
        "macro lens",
        "wide angle"
    ],
    
    "lighting_terms": [
        "studio lighting",
        "natural daylight",
        "golden hour",
        "soft key light",
        "rim lighting",
        "high-contrast",
        "diffused lighting"
    ],
    
    "motion_terms": [
        "slow motion",
        "smooth tracking shot",
        "handheld",
        "gimbal shot",
        "static shot",
        "dynamic camera movement"
    ],
    
    "style_references": [
        "Apple commercial",
        "Nike advertisement",
        "BMW commercial",
        "perfume advertisement",
        "luxury brand aesthetic"
    ]
}

# What to avoid:
# - Vague descriptions ("nice", "good", "beautiful")
# - Conflicting instructions
# - Too many objects (focus on hero product)
# - Overly complex scenes
```

---

## 5. Production Pipeline

### 5.1 Complete Workflow

```python
# production_pipeline.py

class AdProductionPipeline:
    """End-to-end pipeline for ad creation"""
    
    def __init__(self):
        self.veo_client = Veo31Client(...)
        self.optimizer = VeoPhysicsOptimizer()
    
    async def create_ad(
        self,
        product_brief: dict,
        creative_direction: dict
    ) -> dict:
        """
        Full pipeline from brief to final video
        
        product_brief: {
            "product_type": "watch",
            "product_name": "Rolex Submariner",
            "key_features": ["water resistant", "automatic movement"],
            "action": "falling onto surface"
        }
        
        creative_direction: {
            "brand_style": "luxury",
            "mood": "dramatic",
            "duration": 5,
            "aspect_ratio": "16:9",
            "call_to_action": "Discover perfection"
        }
        """
        
        # Step 1: Generate physics scene
        scene = await self._create_physics_scene(product_brief)
        
        # Step 2: Create prompt
        prompt = self._create_ad_prompt(product_brief, creative_direction)
        
        # Step 3: Generate reference
        reference = self.optimizer.generate_stylized_reference(
            scene=scene,
            output_path="./temp/ref",
            style="clean_cgi"
        )
        
        # Step 4: Generate with Veo
        video_result = await self.veo_client.generate_from_reference(
            prompt=prompt,
            reference_video_path=reference,
            duration=creative_direction["duration"],
            motion_strength=0.85,
            resolution="1080p",
            aspect_ratio=creative_direction["aspect_ratio"]
        )
        
        # Step 5: Add post-production (optional)
        final_video = await self._add_post_production(
            video_url=video_result["video_url"],
            call_to_action=creative_direction.get("call_to_action"),
            brand_assets=creative_direction.get("brand_assets")
        )
        
        return {
            "final_video": final_video,
            "reference_video": reference,
            "prompt_used": prompt,
            "metadata": {
                "product": product_brief,
                "creative": creative_direction
            }
        }
    
    async def _create_physics_scene(self, product_brief: dict) -> Scene:
        """Generate physics scene from product brief"""
        
        action_to_scene = {
            "falling onto surface": "object dropping onto platform",
            "sliding": "object sliding across surface",
            "bouncing": "object bouncing on ground",
            "rotating": "object spinning on turntable"
        }
        
        scene_description = action_to_scene.get(
            product_brief["action"],
            product_brief["action"]
        )
        
        # Use Claude to generate scene
        response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            messages=[{
                "role": "user",
                "content": f"Generate physics scene JSON for: {scene_description}"
            }]
        )
        
        scene = Scene(**json.loads(response.content[0].text))
        return scene
    
    def _create_ad_prompt(self, product_brief: dict, creative_direction: dict) -> str:
        """Create optimized Veo prompt"""
        
        brand_aesthetics = {
            "luxury": "Premium commercial production, sophisticated lighting, high-end aesthetic",
            "athletic": "Dynamic energy, authentic sports photography, motivational",
            "tech": "Clean, modern, innovative, Apple-style presentation",
            "lifestyle": "Natural, relatable, documentary style, warm tones"
        }
        
        mood_lighting = {
            "dramatic": "High-contrast lighting, dramatic shadows, cinematic",
            "bright": "Bright, even lighting, clean and modern",
            "warm": "Warm golden tones, sunset lighting, inviting",
            "cool": "Cool blue tones, tech aesthetic, futuristic"
        }
        
        prompt = f"""
        {product_brief['product_name']} {product_brief['action']}.
        {brand_aesthetics.get(creative_direction['brand_style'], '')}.
        {mood_lighting.get(creative_direction['mood'], '')}.
        Shot on professional cinema camera, 4K resolution, commercial quality.
        Product photography, advertising aesthetic.
        """.strip()
        
        return " ".join(prompt.split())  # Clean up whitespace
    
    async def _add_post_production(
        self,
        video_url: str,
        call_to_action: Optional[str] = None,
        brand_assets: Optional[dict] = None
    ) -> str:
        """Add overlays, CTA, branding"""
        
        # Download video from GCS
        video_path = await self._download_from_gcs(video_url)
        
        # Use ffmpeg for post-production
        if call_to_action or brand_assets:
            output_path = "./final_output.mp4"
            
            # Add text overlay, logo, etc.
            # This is simplified - you'd use proper video editing
            subprocess.run([
                'ffmpeg', '-i', video_path,
                # ... add text overlay
                # ... add logo
                output_path
            ])
            
            return output_path
        
        return video_path
```

### 5.2 Frontend Integration (Elm)

```elm
-- Add to Model
type alias Model =
    { scene : Scene
    , videoGeneration : VeoGenerationState
    , adBrief : AdBrief
    }

type alias AdBrief =
    { productName : String
    , productType : String
    , brandStyle : String
    , mood : String
    , duration : Int
    , callToAction : Maybe String
    }

type VeoGenerationState
    = NotStarted
    | SimulatingPhysics
    | GeneratingWithVeo { referenceUrl : String, progress : Float }
    | Complete { reference : String, final : String }
    | Failed String

-- View
viewAdCreator : Model -> Html Msg
viewAdCreator model =
    div [ class "ad-creator" ]
        [ div [ class "brief-panel" ]
            [ h2 [] [ text "Ad Brief" ]
            , input 
                [ placeholder "Product Name"
                , value model.adBrief.productName
                , onInput UpdateProductName
                ] []
            , select [ onInput UpdateBrandStyle ]
                [ option [ value "luxury" ] [ text "Luxury" ]
                , option [ value "athletic" ] [ text "Athletic" ]
                , option [ value "tech" ] [ text "Tech" ]
                , option [ value "lifestyle" ] [ text "Lifestyle" ]
                ]
            , select [ onInput UpdateMood ]
                [ option [ value "dramatic" ] [ text "Dramatic" ]
                , option [ value "bright" ] [ text "Bright" ]
                , option [ value "warm" ] [ text "Warm" ]
                , option [ value "cool" ] [ text "Cool" ]
                ]
            , button [ onClick GenerateAd ] [ text "Generate Ad" ]
            ]
        , div [ class "video-output" ]
            [ viewVeoGeneration model.videoGeneration ]
        ]

viewVeoGeneration : VeoGenerationState -> Html Msg
viewVeoGeneration state =
    case state of
        NotStarted ->
            text "Configure your ad and click Generate"
        
        SimulatingPhysics ->
            div []
                [ text "Step 1/2: Simulating physics..."
                , progressBar 0.5
                ]
        
        GeneratingWithVeo { referenceUrl, progress } ->
            div []
                [ text "Step 2/2: Generating with Veo 3.1..."
                , video [ src referenceUrl, autoplay True, muted True, loop True ] []
                , text "(Physics reference)"
                , progressBar progress
                ]
        
        Complete { reference, final } ->
            div [ class "results" ]
                [ div [ class "side-by-side" ]
                    [ div []
                        [ h3 [] [ text "Physics Sim" ]
                        , video [ src reference, controls True ] []
                        ]
                    , div []
                        [ h3 [] [ text "Final Ad (Veo 3.1)" ]
                        , video [ src final, controls True, autoplay True ] []
                        , button [ onClick (DownloadVideo final) ] 
                            [ text "Download Ad" ]
                        ]
                    ]
                ]
        
        Failed error ->
            div [ class "error" ] [ text error ]
```

---

## Summary

**Your Veo 3.1 + Physics Pipeline:**

1. **Design physics in UI** - Get motion exactly right
2. **Generate clean CGI reference** - High quality input for Veo
3. **Send to Veo 3.1 with optimized prompt** - Physics for motion, AI for photorealism
4. **Get broadcast-quality ad video** - 1080p, 5-20 seconds

**Key advantages with Veo 3.1:**
- Best-in-class video quality
- Excellent motion preservation
- Understands cinematic language
- Longer duration support (up to 20s)
- Good style control

**Recommended approach:** Use reference_video strategy with motion_strength=0.85 for ads. Keyframes work great for shorter clips.

Want me to build out any specific part? (e.g., the GCP setup, prompt optimization, or batch ad generation?)
