import genesis as gs

# Initialize Genesis
gs.init(backend=gs.cpu)

# Create scene
scene = gs.Scene(show_viewer=False)

# Print available methods
print("Scene methods:")
print([m for m in dir(scene) if not m.startswith('_')])

# Try to see what objects/morphs are available
print("\n\nGenesis namespace:")
print([m for m in dir(gs) if not m.startswith('_') and m[0].isupper()])
