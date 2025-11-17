"""
Test file for ReplicateClient - demonstrates usage and basic validation.

Note: These are example tests. In a production environment, you would use
pytest with mocking to avoid hitting the actual Replicate API during tests.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.replicate_client import ReplicateClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_initialization():
    """Test client initialization."""
    print("\n=== Test 1: Client Initialization ===")

    # Test with environment variable
    try:
        client = ReplicateClient()
        print("✓ Client initialized successfully from environment variable")
        return True
    except ValueError as e:
        print(f"✗ Client initialization failed: {e}")
        print("  Make sure REPLICATE_API_KEY is set in your environment")
        return False


def test_cost_estimation():
    """Test cost estimation."""
    print("\n=== Test 2: Cost Estimation ===")

    try:
        client = ReplicateClient(api_key="dummy_key_for_testing")

        # Test case 1: 10 images, 20 second video
        cost1 = client.estimate_cost(num_images=10, video_duration=20)
        expected1 = 10 * 0.003 + 20 * 0.10  # $0.03 + $2.00 = $2.03
        assert abs(cost1 - expected1) < 0.001, f"Expected {expected1}, got {cost1}"
        print(f"✓ Cost for 10 images + 20s video: ${cost1:.2f}")

        # Test case 2: 5 images, 10 second video
        cost2 = client.estimate_cost(num_images=5, video_duration=10)
        expected2 = 5 * 0.003 + 10 * 0.10  # $0.015 + $1.00 = $1.015
        assert abs(cost2 - expected2) < 0.001, f"Expected {expected2}, got {cost2}"
        print(f"✓ Cost for 5 images + 10s video: ${cost2:.2f}")

        # Test case 3: No images, 30 second video
        cost3 = client.estimate_cost(num_images=0, video_duration=30)
        expected3 = 0 * 0.003 + 30 * 0.10  # $0.00 + $3.00 = $3.00
        assert abs(cost3 - expected3) < 0.001, f"Expected {expected3}, got {cost3}"
        print(f"✓ Cost for 0 images + 30s video: ${cost3:.2f}")

        print("✓ All cost estimation tests passed")
        return True

    except Exception as e:
        print(f"✗ Cost estimation test failed: {e}")
        return False


def test_error_handling():
    """Test error handling for various scenarios."""
    print("\n=== Test 3: Error Handling ===")

    try:
        # Test missing API key
        try:
            import os
            old_key = os.environ.get('REPLICATE_API_KEY')
            if 'REPLICATE_API_KEY' in os.environ:
                del os.environ['REPLICATE_API_KEY']

            client = ReplicateClient()
            print("✗ Should have raised ValueError for missing API key")
            return False
        except ValueError as e:
            print("✓ Correctly raises ValueError for missing API key")

            # Restore old key
            if old_key:
                os.environ['REPLICATE_API_KEY'] = old_key

        # Test empty image URLs for video generation
        client = ReplicateClient(api_key="dummy_key_for_testing")
        result = client.generate_video([])
        assert result['success'] is False, "Should fail with empty image URLs"
        assert "No image URLs provided" in result['error']
        print("✓ Correctly handles empty image URLs")

        print("✓ All error handling tests passed")
        return True

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def test_context_manager():
    """Test context manager support."""
    print("\n=== Test 4: Context Manager ===")

    try:
        with ReplicateClient(api_key="dummy_key_for_testing") as client:
            assert client is not None
            print("✓ Context manager entry works")

        print("✓ Context manager exit works")
        return True

    except Exception as e:
        print(f"✗ Context manager test failed: {e}")
        return False


def demonstrate_usage():
    """Demonstrate typical usage patterns."""
    print("\n=== Usage Examples ===")

    # Example 1: Basic initialization
    print("\nExample 1: Initialize client")
    print("```python")
    print("from services.replicate_client import ReplicateClient")
    print("")
    print("# Initialize with environment variable")
    print("client = ReplicateClient()")
    print("")
    print("# Or with explicit API key")
    print("client = ReplicateClient(api_key='your-api-key-here')")
    print("```")

    # Example 2: Generate image
    print("\nExample 2: Generate an image")
    print("```python")
    print("result = client.generate_image('a red sports car in a futuristic city')")
    print("if result['success']:")
    print("    print(f\"Image URL: {result['image_url']}\")")
    print("    print(f\"Prediction ID: {result['prediction_id']}\")")
    print("else:")
    print("    print(f\"Error: {result['error']}\")")
    print("```")

    # Example 3: Generate video
    print("\nExample 3: Generate a video from images")
    print("```python")
    print("image_urls = [")
    print("    'https://example.com/frame1.jpg',")
    print("    'https://example.com/frame2.jpg',")
    print("    'https://example.com/frame3.jpg'")
    print("]")
    print("")
    print("result = client.generate_video(image_urls)")
    print("if result['success']:")
    print("    print(f\"Video URL: {result['video_url']}\")")
    print("    print(f\"Duration: {result['duration_seconds']}s\")")
    print("else:")
    print("    print(f\"Error: {result['error']}\")")
    print("```")

    # Example 4: Cost estimation
    print("\nExample 4: Estimate costs")
    print("```python")
    print("# Estimate cost for 10 images and a 30-second video")
    print("cost = client.estimate_cost(num_images=10, video_duration=30)")
    print("print(f\"Estimated cost: ${cost:.2f}\")")
    print("# Output: Estimated cost: $3.03")
    print("```")

    # Example 5: Using context manager
    print("\nExample 5: Use context manager for automatic cleanup")
    print("```python")
    print("with ReplicateClient() as client:")
    print("    result = client.generate_image('a beautiful sunset')")
    print("    # Session automatically closed when exiting context")
    print("```")


def main():
    """Run all tests."""
    print("=" * 70)
    print("ReplicateClient Test Suite")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Initialization", test_initialization()))
    results.append(("Cost Estimation", test_cost_estimation()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Context Manager", test_context_manager()))

    # Show usage examples
    demonstrate_usage()

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
