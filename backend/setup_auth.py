#!/usr/bin/env python3
"""
Setup script for creating initial admin user and API key.
Run this once to set up authentication for your API.

Usage:
    python setup_auth.py
"""

import sys
import getpass
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import create_user, get_user_by_username, create_api_key as db_create_api_key
from auth import get_password_hash, generate_api_key, hash_api_key


def main():
    print("=" * 60)
    print("Physics Simulator API - Authentication Setup")
    print("=" * 60)
    print()

    # Check if admin user already exists
    existing_admin = get_user_by_username("admin")
    if existing_admin:
        print("⚠️  Admin user already exists!")
        response = input("Do you want to create a new API key for the existing admin? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return

        user_id = existing_admin["id"]
        username = existing_admin["username"]
        print(f"\n✓ Using existing admin user: {username}")

    else:
        print("Creating a new admin user...")
        print()

        # Get admin username
        username = input("Enter admin username (default: admin): ").strip()
        if not username:
            username = "admin"

        # Get admin email
        email = input("Enter admin email: ").strip()
        while not email or "@" not in email:
            print("Please enter a valid email address.")
            email = input("Enter admin email: ").strip()

        # Get admin password
        password = getpass.getpass("Enter admin password: ")
        while len(password) < 8:
            print("Password must be at least 8 characters long.")
            password = getpass.getpass("Enter admin password: ")

        password_confirm = getpass.getpass("Confirm admin password: ")
        while password != password_confirm:
            print("Passwords do not match!")
            password = getpass.getpass("Enter admin password: ")
            password_confirm = getpass.getpass("Confirm admin password: ")

        # Create admin user
        try:
            hashed_password = get_password_hash(password)
            user_id = create_user(
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_admin=True
            )
            print(f"\n✓ Admin user created successfully! (ID: {user_id})")
        except Exception as e:
            print(f"\n✗ Failed to create admin user: {e}")
            return

    # Ask if user wants to create an API key
    print()
    create_key = input("Do you want to create an API key? (y/n): ")
    if create_key.lower() == 'y':
        key_name = input("Enter a name for this API key (e.g., 'Production Key'): ").strip()
        if not key_name:
            key_name = "Default API Key"

        expires_input = input("Should this key expire? Enter days (or press Enter for no expiration): ").strip()
        expires_at = None
        if expires_input:
            try:
                expires_days = int(expires_input)
                from datetime import datetime, timedelta
                expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat()
                print(f"Key will expire in {expires_days} days")
            except ValueError:
                print("Invalid number of days. Key will not expire.")

        # Generate API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)

        try:
            key_id = db_create_api_key(
                key_hash=key_hash,
                name=key_name,
                user_id=user_id,
                expires_at=expires_at
            )
            print()
            print("=" * 60)
            print("✓ API Key created successfully!")
            print("=" * 60)
            print()
            print("IMPORTANT: Save this API key somewhere safe!")
            print("You will NOT be able to see it again.")
            print()
            print(f"API Key: {api_key}")
            print()
            print("=" * 60)
            print()
            print("Usage:")
            print("  - Add to requests as header: X-API-Key: <your-key>")
            print("  - Or use Bearer token authentication via /api/auth/login")
            print()
        except Exception as e:
            print(f"\n✗ Failed to create API key: {e}")
            return

    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print(f"Admin username: {username}")
    if not existing_admin:
        print(f"Admin email: {email}")
    print()
    print("Next steps:")
    print("  1. Start the server: python main.py")
    print("  2. Test authentication:")
    print()
    print("     # Login to get JWT token")
    print(f"     curl -X POST http://localhost:8000/api/auth/login \\")
    print(f"       -H 'Content-Type: application/x-www-form-urlencoded' \\")
    print(f"       -d 'username={username}&password=YOUR_PASSWORD'")
    print()
    print("     # Or use API key")
    print("     curl http://localhost:8000/api/videos \\")
    print("       -H 'X-API-Key: YOUR_API_KEY'")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
