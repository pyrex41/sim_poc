#!/bin/bash
# Test script to debug upload issues

# Create a real PNG file for testing
echo "Creating test PNG..."
python3 << 'EOF'
from PIL import Image
import io

# Create a simple 100x100 red PNG
img = Image.new('RGB', (100, 100), color='red')
img.save('test_upload.png', 'PNG')
print("✓ Created test_upload.png")

# Verify it's a real PNG
with open('test_upload.png', 'rb') as f:
    header = f.read(8)
    if header.startswith(b'\x89PNG'):
        print(f"✓ PNG magic bytes confirmed: {header.hex()}")
    else:
        print(f"✗ Invalid PNG! Magic bytes: {header.hex()}")
EOF

echo ""
echo "File info:"
file test_upload.png
xxd -l 16 test_upload.png

echo ""
echo "Testing upload to localhost..."
echo "(Make sure backend is running on localhost:8000)"

# You'll need to get a valid auth token
# Replace YOUR_TOKEN with actual token
echo ""
echo "Example curl command:"
echo ""
echo "curl -X POST http://localhost:8000/api/v2/upload-asset \\"
echo "  -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "  -F 'file=@test_upload.png' \\"
echo "  -F 'clientId=YOUR_CLIENT_ID' \\"
echo "  -F 'name=Test Upload' \\"
echo "  -F 'type=image' \\"
echo "  -F 'tags=[\"test\"]'"
