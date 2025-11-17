#!/usr/bin/env python3
"""Test script for the new asset API endpoints."""

import requests
from io import BytesIO
from PIL import Image

BASE_URL = "http://localhost:8000"

def create_test_image():
    """Create a simple test PNG image in memory."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def test_asset_api():
    print("🚀 Testing Asset API Endpoints\n")
    print("ℹ️  Auth bypassed for local development (localhost)\n")

    # No auth needed for localhost - the backend bypasses it automatically
    headers = {}

    # Step 2: Upload an asset
    print("\n2. Uploading test image...")
    test_image = create_test_image()
    files = {"file": ("test_image.png", test_image, "image/png")}
    data = {"name": "Test Security Image"}

    response = requests.post(
        f"{BASE_URL}/api/v2/upload-asset",
        files=files,
        data=data,
        headers=headers
    )

    if response.status_code in [200, 201]:
        asset = response.json()
        print(f"✅ Asset uploaded successfully!")
        print(f"   ID: {asset.get('id')}")
        print(f"   Type: {asset.get('type')}")
        print(f"   Format: {asset.get('format')}")
        print(f"   Size: {asset.get('size')} bytes")
        print(f"   URL: {asset.get('url')}")
        asset_id = asset.get('id')
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return

    # Step 3: List assets
    print("\n3. Listing assets...")
    response = requests.get(f"{BASE_URL}/api/v2/assets", headers=headers)

    if response.status_code == 200:
        assets = response.json()
        print(f"✅ Found {len(assets)} asset(s)")
        for asset in assets[:3]:  # Show first 3
            print(f"   - {asset.get('name')} ({asset.get('type')})")
    else:
        print(f"❌ List failed: {response.status_code} - {response.text}")

    # Step 4: Get specific asset
    print(f"\n4. Retrieving asset {asset_id}...")
    response = requests.get(f"{BASE_URL}/api/v2/assets/{asset_id}", headers=headers)

    if response.status_code == 200:
        print(f"✅ Asset retrieved successfully!")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        print(f"   Size: {len(response.content)} bytes")
    else:
        print(f"❌ Get asset failed: {response.status_code} - {response.text}")

    # Step 5: Note about security
    print(f"\n5. Security note...")
    print(f"ℹ️  Auth bypassed on localhost for development")
    print(f"   In production, auth is required for all asset operations")

    # Step 6: Delete asset
    print(f"\n6. Deleting asset {asset_id}...")
    response = requests.delete(f"{BASE_URL}/api/v2/assets/{asset_id}", headers=headers)

    if response.status_code == 200:
        print(f"✅ Asset deleted successfully!")
    else:
        print(f"❌ Delete failed: {response.status_code} - {response.text}")

    print("\n✨ All tests completed!")

if __name__ == "__main__":
    try:
        test_asset_api()
    except Exception as e:
        print(f"\n❌ Error: {e}")
