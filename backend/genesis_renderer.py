"""
Genesis Photorealistic Renderer

Main renderer that orchestrates:
1. LLM semantic augmentation
2. Scene conversion to Genesis
3. Ray-traced rendering
4. Video export
"""

import os
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import genesis as gs
from llm_interpreter import get_interpreter
from scene_converter import SceneConverter
from environment_interpreter import interpret_scene_context


class RenderQuality:
    """Predefined quality presets for rendering"""

    DRAFT = {
        "spp": 64,
        "description": "Fast preview (30 sec/frame)",
        "tracing_depth": 16
    }

    HIGH = {
        "spp": 256,
        "description": "Production quality (2 min/frame)",
        "tracing_depth": 32
    }

    ULTRA = {
        "spp": 512,
        "description": "Maximum quality (4 min/frame)",
        "tracing_depth": 48
    }


class GenesisRenderer:
    """Photorealistic renderer using Genesis ray-tracer"""

    def __init__(
        self,
        quality: str = "high",
        output_dir: str = "./backend/DATA/genesis_videos"
    ):
        """
        Initialize Genesis renderer

        Args:
            quality: "draft", "high", or "ultra"
            output_dir: Directory to save rendered videos
        """

        self.quality = self._get_quality_preset(quality)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scene = None
        self.camera = None
        self.converter = None
        self.llm_interpreter = get_interpreter()
        self.using_raytracer = False  # Track which renderer we're using
        self.environment_params = None  # Store interpreted environment parameters

    def _get_quality_preset(self, quality: str) -> Dict:
        """Get quality preset by name"""
        presets = {
            "draft": RenderQuality.DRAFT,
            "high": RenderQuality.HIGH,
            "ultra": RenderQuality.ULTRA
        }
        return presets.get(quality.lower(), RenderQuality.HIGH)

    async def render_scene(
        self,
        scene_data: Dict,
        duration: float = 5.0,
        fps: int = 60,
        resolution: Tuple[int, int] = (1920, 1080),
        camera_config: Optional[Dict] = None,
        scene_context: Optional[Dict] = None
    ) -> str:
        """
        Render a complete scene to video

        Args:
            scene_data: JSON scene data with objects
            duration: Video duration in seconds
            fps: Frames per second
            resolution: (width, height) tuple
            camera_config: Optional camera position/settings
            scene_context: Optional SceneContext dict with environment, narrative, lighting

        Returns:
            Path to rendered video file
        """

        print(f"🎬 Starting Genesis render (Quality: {self.quality['description']})")
        start_time = time.time()

        # Step 1: Interpret scene context into rendering parameters
        if scene_context:
            print("🌤️  Interpreting scene context...")
            self.environment_params = await interpret_scene_context(
                scene_context=scene_context,
                objects=scene_data.get("objects", {})
            )
            # Use narrative as LLM context for object augmentation
            llm_context = scene_context.get("narrative", "") or self.environment_params.get("description", "")
        else:
            llm_context = None

        # Step 2: Augment objects with LLM
        print("🤖 Augmenting scene with LLM...")
        augmented_objects = await self.llm_interpreter.augment_scene(
            scene_data.get("objects", []),
            scene_context=llm_context
        )
        scene_data["objects"] = augmented_objects

        # Step 3: Create Genesis scene with environment-aware settings
        print("🌍 Creating Genesis scene...")
        self._create_scene()

        # Step 3: Convert JSON to Genesis entities
        print("📦 Converting objects to Genesis entities...")
        self.converter = SceneConverter(self.scene)
        # TODO: Fix ground plane - gs.surfaces.Surface has NotImplementedError in Genesis 0.3.7
        # self.converter.add_ground_plane()
        self.converter.convert_scene(scene_data)

        # Step 4: Setup camera
        print("📸 Setting up camera...")
        self._setup_camera(resolution, camera_config)

        # Step 5: Build scene
        print("🔨 Building scene...")
        self.scene.build()

        # Step 6: Render frames
        print(f"🎥 Rendering {int(duration * fps)} frames...")
        output_path = await self._render_video(duration, fps)

        elapsed = time.time() - start_time
        print(f"✅ Rendering complete in {elapsed:.1f}s: {output_path}")

        return output_path

    def _create_scene(self):
        """Create Genesis scene with ray-tracer backend"""

        # Initialize Genesis if not already initialized
        # Try GPU backend for ray-tracing support, fall back to CPU
        try:
            if not hasattr(gs, '_initialized') or not gs._initialized:
                # Try GPU backend first (supports RayTracer)
                try:
                    gs.init(backend=gs.gpu)
                    print("✅ Genesis initialized with GPU backend")
                except Exception as gpu_err:
                    print(f"⚠️  GPU backend failed ({gpu_err}), trying CPU...")
                    gs.init(backend=gs.cpu)
                    print("✅ Genesis initialized with CPU backend")
        except:
            # If Genesis is already initialized, continue
            pass

        # Configure lighting from environment parameters or use defaults
        if self.environment_params:
            lights = self._build_lights_from_environment()
        else:
            # Default 3-point lighting setup
            lights = [
                {
                    "pos": (10.0, 20.0, 10.0),
                    "color": (1.0, 0.95, 0.9),  # Warm key light
                    "intensity": 15.0,
                    "radius": 6.0
                },
                {
                    "pos": (-10.0, 10.0, -10.0),
                    "color": (0.8, 0.9, 1.0),  # Cool fill light
                    "intensity": 5.0,
                    "radius": 4.0
                },
                {
                    "pos": (0.0, 5.0, -15.0),
                    "color": (1.0, 1.0, 1.0),  # Back light
                    "intensity": 8.0,
                    "radius": 3.0
                }
            ]

        # Create scene with renderer
        # Try RayTracer first, fall back to Rasterizer if LuisaRenderer unavailable
        print("🎨 Attempting to create scene with RayTracer...")
        try:
            renderer = gs.renderers.RayTracer(
                lights=lights,
                env_radius=1000.0,
                logging_level="warning"
            )

            # Try to create scene - this is where LuisaRenderer import happens
            self.scene = gs.Scene(
                renderer=renderer,
                show_viewer=False,
                sim_options=gs.options.SimOptions(
                    dt=1/60,
                    gravity=(0, -9.81, 0)
                )
            )
            self.using_raytracer = True
            print("✅ RayTracer scene created successfully")

        except Exception as e:
            # RayTracer failed - fall back to Rasterizer
            print(f"⚠️  RayTracer unavailable ({str(e)[:50]}...), using Rasterizer with PBR")

            # Rasterizer with default parameters
            renderer = gs.renderers.Rasterizer()

            self.scene = gs.Scene(
                renderer=renderer,
                show_viewer=False,
                sim_options=gs.options.SimOptions(
                    dt=1/60,
                    gravity=(0, -9.81, 0)
                )
            )
            self.using_raytracer = False
            print("✅ Rasterizer scene created successfully (PBR materials enabled)")

    def _build_lights_from_environment(self) -> List[Dict]:
        """Build Genesis lights from environment interpretation"""

        lighting = self.environment_params.get("lighting", {})
        directional = lighting.get("directional", {})
        ambient = lighting.get("ambient", {})

        # Convert color temperature to RGB (simplified)
        def kelvin_to_rgb(kelvin: int) -> Tuple[float, float, float]:
            """Approximate Kelvin color temperature to RGB"""
            if kelvin < 3000:
                return (1.0, 0.5, 0.2)  # Warm orange
            elif kelvin < 4000:
                return (1.0, 0.7, 0.4)  # Warm
            elif kelvin < 5000:
                return (1.0, 0.9, 0.7)  # Neutral warm
            elif kelvin < 6000:
                return (1.0, 0.95, 0.9)  # Slightly warm
            elif kelvin < 7000:
                return (1.0, 1.0, 1.0)  # Neutral
            else:
                return (0.9, 0.95, 1.0)  # Cool blue

        # Directional light (sun/moon)
        color_temp = directional.get("colorTemperature", 5500)
        intensity = directional.get("intensity", 1.0) * 15.0  # Scale for Genesis
        angle = directional.get("angle", [45, 180])

        # Convert angle to position
        import math
        altitude_rad = math.radians(angle[0])
        azimuth_rad = math.radians(angle[1])
        distance = 20.0

        pos_x = distance * math.cos(altitude_rad) * math.sin(azimuth_rad)
        pos_y = distance * math.sin(altitude_rad)
        pos_z = distance * math.cos(altitude_rad) * math.cos(azimuth_rad)

        lights = [
            {
                "pos": (pos_x, pos_y, pos_z),
                "color": kelvin_to_rgb(color_temp),
                "intensity": intensity,
                "radius": 6.0
            }
        ]

        # Add ambient fill light
        ambient_intensity = ambient.get("intensity", 0.4) * 8.0
        lights.append({
            "pos": (-pos_x * 0.5, pos_y * 0.5, -pos_z * 0.5),
            "color": (0.9, 0.95, 1.0),
            "intensity": ambient_intensity,
            "radius": 4.0
        })

        return lights

    def _setup_camera(
        self,
        resolution: Tuple[int, int],
        camera_config: Optional[Dict] = None
    ):
        """Setup camera with photorealistic settings"""

        # Default camera config
        config = camera_config or {}

        pos = config.get("position", (8, 6, 8))
        lookat = config.get("lookat", (0, 2, 0))
        fov = config.get("fov", 40)

        # Apply environment camera settings if available
        if self.environment_params:
            camera_params = self.environment_params.get("camera", {})
            exposure = camera_params.get("exposure", 0.0)
            dof_settings = camera_params.get("depthOfField", {})
        else:
            exposure = 0.0
            dof_settings = {}

        # Check if we're using RayTracer or Rasterizer
        if self.using_raytracer:
            # RayTracer supports advanced camera features
            aperture = config.get("aperture", 2.8)

            # Use depth of field settings from environment if available
            if dof_settings.get("enabled", True):
                f_stop = dof_settings.get("fStop", aperture)
                focus_dist = dof_settings.get("focusDistance", None)
            else:
                f_stop = 22.0  # High f-stop = no DOF
                focus_dist = None

            self.camera = self.scene.add_camera(
                model="thinlens",  # Enable depth-of-field
                spp=self.quality["spp"],
                aperture=f_stop,
                focus_dist=focus_dist,  # Auto-compute from pos/lookat if None
                denoise=True,  # Enable AI denoising
                res=resolution,
                fov=fov,
                pos=pos,
                lookat=lookat
            )
        else:
            # Rasterizer - simpler camera
            self.camera = self.scene.add_camera(
                res=resolution,
                fov=fov,
                pos=pos,
                lookat=lookat
            )

    async def _render_video(
        self,
        duration: float,
        fps: int
    ) -> str:
        """Render simulation to video"""

        # Generate unique output filename
        timestamp = int(time.time())
        output_filename = f"genesis_render_{timestamp}.mp4"
        output_path = str(self.output_dir / output_filename)

        # Start recording
        self.camera.start_recording()

        # Simulate and render frames
        num_frames = int(duration * fps)
        for frame_idx in range(num_frames):
            # Progress indicator
            if frame_idx % 10 == 0:
                progress = (frame_idx / num_frames) * 100
                print(f"  Progress: {progress:.1f}% ({frame_idx}/{num_frames} frames)")

            # Step physics simulation
            self.scene.step()

            # Optional: Update camera pose for dynamic shots
            # self.camera.set_pose(pos=..., lookat=...)

            # Render frame (automatically captured by recorder)
            self.camera.render(
                rgb=True,
                antialiasing=True
            )

        # Stop recording and export video
        self.camera.stop_recording(
            save_to_filename=output_path,
            fps=fps
        )

        return output_path

    def cleanup(self):
        """Clean up Genesis resources"""
        if self.scene:
            # Genesis handles cleanup automatically, but we can reset references
            self.scene = None
            self.camera = None
            self.converter = None


# Factory function for easy creation
def create_renderer(
    quality: str = "high",
    output_dir: str = "./backend/DATA/genesis_videos"
) -> GenesisRenderer:
    """
    Create a Genesis renderer with specified quality

    Args:
        quality: "draft", "high", or "ultra"
        output_dir: Output directory for videos

    Returns:
        GenesisRenderer instance
    """
    return GenesisRenderer(quality=quality, output_dir=output_dir)
