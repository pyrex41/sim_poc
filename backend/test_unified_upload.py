#!/usr/bin/env python3
"""
Test script for unified asset upload functionality
Tests basic functionality without complex imports
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))


def test_imports():
    """Test that all our modified modules can be imported"""
    print("Testing imports...")

    try:
        from api.v3.models import UnifiedAssetUploadInput
        from schemas.assets import AssetDB, BaseAsset

        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_model_validation():
    """Test that our new models work correctly"""
    print("Testing model validation...")

    try:
        from api.v3.models import UnifiedAssetUploadInput

        # Test file upload input
        file_input = UnifiedAssetUploadInput(
            uploadType="file",
            name="test-image.jpg",
            type="image",
            clientId="test-client",
            generateThumbnail=True,
        )
        print("✓ File upload input validation passed")

        # Test URL upload input
        url_input = UnifiedAssetUploadInput(
            uploadType="url",
            name="test-image.jpg",
            type="image",
            sourceUrl="https://example.com/image.jpg",
            clientId="test-client",
            generateThumbnail=True,
        )
        print("✓ URL upload input validation passed")

        return True
    except Exception as e:
        print(f"✗ Model validation failed: {e}")
        return False


def test_database_schema():
    """Test that database schema includes our new fields"""
    print("Testing database schema...")

    try:
        import sqlite3

        conn = sqlite3.connect("backend/DATA/scenes.db")
        cursor = conn.cursor()

        # Check if thumbnail_blob_id column exists
        cursor.execute("PRAGMA table_info(assets)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        required_columns = [
            "id",
            "name",
            "asset_type",
            "url",
            "thumbnail_url",
            "thumbnail_blob_id",
            "source_url",
        ]
        missing_columns = [col for col in required_columns if col not in column_names]

        if missing_columns:
            print(f"✗ Missing columns: {missing_columns}")
            return False

        print("✓ All required columns present in assets table")
        conn.close()
        return True

    except Exception as e:
        print(f"✗ Database schema test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("Running unified asset upload tests...\n")

    tests = [
        test_imports,
        test_model_validation,
        test_database_schema,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}\n")

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
