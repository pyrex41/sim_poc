import genesis as gs

# Initialize
gs.init(backend=gs.cpu)

# Create scene
scene = gs.Scene(show_viewer=False)

# Try to see what the add_entity signature is
import inspect
sig = inspect.signature(scene.add_entity)
print("add_entity signature:")
print(sig)

# Try adding a simple entity
try:
    # Check if morphs exists
    print("\nChecking for morphs...")
    if hasattr(gs, 'morphs'):
        print("gs.morphs exists!")
        print(dir(gs.morphs))
    else:
        print("gs.morphs does NOT exist")

    # Check for materials
    print("\nChecking for materials...")
    if hasattr(gs, 'materials'):
        print("gs.materials exists!")
    else:
        print("gs.materials does NOT exist")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
