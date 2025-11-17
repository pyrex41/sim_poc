"""
Scene Converter: JSON Scene Data → Genesis Entities

Converts the frontend JSON scene format to Genesis scene objects
with LLM-augmented properties
"""

import genesis as gs
from typing import Dict, List, Optional, Tuple


class SceneConverter:
    """Converts JSON scene data to Genesis entities"""

    def __init__(self, scene):
        self.scene = scene
        self.entities = []

    def convert_scene(self, scene_data: Dict) -> List:
        """
        Convert full scene data to Genesis entities

        Args:
            scene_data: JSON scene data with objects (list or dict)

        Returns:
            List of created Genesis entities
        """

        objects = scene_data.get("objects", [])
        # Handle both list and dict formats
        if isinstance(objects, dict):
            objects = list(objects.values())

        for obj_data in objects:
            entity = self.convert_object(obj_data)
            if entity:
                self.entities.append(entity)

        return self.entities

    def convert_object(self, obj_data: Dict):
        """
        Convert a single object to a Genesis entity

        Args:
            obj_data: Object data with transform, physics, visual, and genesis properties

        Returns:
            Genesis Entity or None if conversion fails
        """

        try:
            # Extract base properties
            transform = obj_data.get("transform", {})
            physics = obj_data.get("physicsProperties", {})
            visual = obj_data.get("visualProperties", {})
            genesis_props = obj_data.get("genesis_properties", {})

            # Create morph (geometry)
            morph = self._create_morph(visual, genesis_props)
            if not morph:
                return None

            # Create material (physics)
            material = self._create_material(physics)

            # Create surface (visual/PBR)
            # TODO: Fix - gs.surfaces.Surface has NotImplementedError in Genesis 0.3.7
            # surface = self._create_surface(visual, genesis_props)

            # Get position and rotation
            position = self._get_position(transform)
            rotation = self._get_rotation(transform)

            # Add entity to scene (without surface for now)
            entity = self.scene.add_entity(
                morph=morph,
                material=material,
                # surface=surface,  # Disabled - NotImplementedError
                pos=position,
                quat=rotation
            )

            return entity

        except Exception as e:
            print(f"Error converting object: {e}")
            print(f"Object data: {obj_data}")
            return None

    def _create_morph(
        self,
        visual: Dict,
        genesis_props: Dict
    ):
        """Create Genesis morph (geometry) from visual properties"""

        shape = visual.get("shape", "Box")

        # Get scale (use LLM-suggested dimensions if available, else use base scale)
        if genesis_props and genesis_props.get("suggested_dimensions"):
            dims = genesis_props["suggested_dimensions"]

            if shape == "Box":
                size = [
                    dims.get("length", dims.get("width", 1.0)),
                    dims.get("width", dims.get("length", 1.0)),
                    dims.get("height", 1.0)
                ]
            elif shape == "Sphere":
                size = dims.get("radius", dims.get("diameter", 1.0) / 2)
            elif shape == "Cylinder":
                size = {
                    "radius": dims.get("radius", dims.get("diameter", 1.0) / 2),
                    "height": dims.get("height", 1.0)
                }
            elif shape == "Capsule":
                size = {
                    "radius": dims.get("radius", dims.get("diameter", 1.0) / 2),
                    "length": dims.get("length", dims.get("height", 1.0))
                }
        else:
            # Use base scale with optional multiplier
            scale = visual.get("scale", {"x": 1, "y": 1, "z": 1})
            multiplier = genesis_props.get("scale_multiplier", [1.0, 1.0, 1.0]) if genesis_props else [1.0, 1.0, 1.0]

            if shape == "Box":
                size = [
                    scale.get("x", 1.0) * multiplier[0],
                    scale.get("y", 1.0) * multiplier[1],
                    scale.get("z", 1.0) * multiplier[2]
                ]
            elif shape == "Sphere":
                size = scale.get("x", 1.0) * multiplier[0] / 2  # radius
            elif shape == "Cylinder":
                size = {
                    "radius": scale.get("x", 1.0) * multiplier[0] / 2,
                    "height": scale.get("y", 1.0) * multiplier[1]
                }
            elif shape == "Capsule":
                size = {
                    "radius": scale.get("x", 1.0) * multiplier[0] / 2,
                    "length": scale.get("y", 1.0) * multiplier[1]
                }

        # Create appropriate morph
        if shape == "Box":
            return gs.morphs.Box(size=size)
        elif shape == "Sphere":
            return gs.morphs.Sphere(radius=size)
        elif shape == "Cylinder":
            return gs.morphs.Cylinder(radius=size["radius"], height=size["height"])
        elif shape == "Capsule":
            return gs.morphs.Capsule(radius=size["radius"], length=size["length"])
        else:
            print(f"Unsupported shape: {shape}, defaulting to Box")
            return gs.morphs.Box(size=[1.0, 1.0, 1.0])

    def _create_material(self, physics: Dict):
        """Create Genesis material (physics properties) from physics data"""

        return gs.materials.Rigid(
            rho=physics.get("mass", 1.0) * 1000,  # Convert to kg/m³
            friction=physics.get("friction", 0.5),
            # Note: Genesis 0.3.7 uses 'coup_restitution' instead of 'restitution'
            coup_restitution=physics.get("restitution", 0.3)
        )

    def _create_surface(
        self,
        visual: Dict,
        genesis_props: Dict
    ):
        """Create Genesis surface (PBR visual properties)"""

        # If we have LLM-augmented properties, use them
        if genesis_props:
            color = tuple(genesis_props.get("color", [0.7, 0.7, 0.7]))
            metallic = genesis_props.get("metallic", 0.2)
            roughness = genesis_props.get("roughness", 0.7)
            opacity = genesis_props.get("opacity", 1.0)
            emissive = tuple(genesis_props.get("emissive", [0.0, 0.0, 0.0]))
        else:
            # Fall back to basic visual properties
            color = self._hex_to_rgb(visual.get("color", "#B0B0B0"))
            metallic = 0.2
            roughness = 0.7
            opacity = 1.0
            emissive = (0.0, 0.0, 0.0)

        return gs.surfaces.Surface(
            color=color,
            metallic=metallic,
            roughness=roughness,
            opacity=opacity,
            emissive=emissive,
            smooth=True,  # Enable smooth shading
            double_sided=False
        )

    def _get_position(self, transform: Dict) -> Tuple[float, float, float]:
        """Extract position from transform"""
        pos = transform.get("position", {"x": 0, "y": 0, "z": 0})
        return (pos.get("x", 0), pos.get("y", 0), pos.get("z", 0))

    def _get_rotation(self, transform: Dict) -> Optional[Tuple[float, float, float, float]]:
        """Extract rotation quaternion from transform"""
        rot = transform.get("rotation")
        if rot and all(k in rot for k in ["x", "y", "z", "w"]):
            return (rot["x"], rot["y"], rot["z"], rot["w"])
        return None  # Use default rotation

    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to RGB tuple (0-1 range)"""
        hex_color = hex_color.lstrip('#')

        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return (r, g, b)
        else:
            return (0.7, 0.7, 0.7)  # Default gray

    def add_ground_plane(
        self,
        size: float = 50.0,
        height: float = 0.0,
        color: Tuple[float, float, float] = (0.3, 0.3, 0.3)
    ):
        """Add a ground plane to the scene"""

        ground = self.scene.add_entity(
            morph=gs.morphs.Plane(),
            material=gs.materials.Rigid(rho=1000, friction=0.8),
            surface=gs.surfaces.Surface(
                color=color,
                roughness=0.9,
                metallic=0.0
            ),
            pos=(0, height, 0)
        )

        self.entities.append(ground)
        return ground
