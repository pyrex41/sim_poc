#!/usr/bin/env python3
"""
Script to add team users with API keys.
Creates: reuben, mike, harrison with password "bestvideoproject"
"""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import create_user, get_user_by_username, create_api_key as db_create_api_key
from auth import get_password_hash, generate_api_key, hash_api_key

# Team configuration
TEAM_USERS = [
    {
        "username": "reuben",
        "email": "reuben@bestvideoproject.com",
        "is_admin": True  # Reuben as admin
    },
    {
        "username": "mike",
        "email": "mike@bestvideoproject.com",
        "is_admin": False
    },
    {
        "username": "harrison",
        "email": "harrison@bestvideoproject.com",
        "is_admin": False
    }
]

PASSWORD = "bestvideoproject"

def main():
    print("=" * 60)
    print("Best Video Project - Team User Setup")
    print("=" * 60)
    print()

    created_users = []
    api_keys_generated = {}

    # Create users
    for user_config in TEAM_USERS:
        username = user_config["username"]
        email = user_config["email"]
        is_admin = user_config["is_admin"]

        # Check if user already exists
        existing_user = get_user_by_username(username)

        if existing_user:
            print(f"⚠️  User '{username}' already exists (ID: {existing_user['id']})")
            user_id = existing_user["id"]
        else:
            try:
                hashed_password = get_password_hash(PASSWORD)
                user_id = create_user(
                    username=username,
                    email=email,
                    hashed_password=hashed_password,
                    is_admin=is_admin
                )
                print(f"✓ Created user '{username}' (ID: {user_id})")
                if is_admin:
                    print(f"  → Admin privileges granted")
                created_users.append(username)
            except Exception as e:
                print(f"✗ Failed to create user '{username}': {e}")
                continue

        # Generate API key
        try:
            api_key = generate_api_key()
            key_hash = hash_api_key(api_key)

            key_id = db_create_api_key(
                key_hash=key_hash,
                name=f"{username}'s API Key",
                user_id=user_id,
                expires_at=None  # No expiration
            )

            api_keys_generated[username] = api_key
            print(f"✓ Generated API key for '{username}' (Key ID: {key_id})")
        except Exception as e:
            print(f"✗ Failed to create API key for '{username}': {e}")

    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()

    # Display summary
    print("Team Users:")
    for user_config in TEAM_USERS:
        username = user_config["username"]
        role = "Admin" if user_config["is_admin"] else "User"
        print(f"  • {username} ({role})")

    print()
    print("Credentials:")
    print(f"  Password (all users): {PASSWORD}")
    print()

    if api_keys_generated:
        print("=" * 60)
        print("API KEYS - SAVE THESE SECURELY!")
        print("=" * 60)
        print()
        for username, api_key in api_keys_generated.items():
            print(f"{username}:")
            print(f"  {api_key}")
            print()

        print("=" * 60)
        print()
        print("Usage:")
        print("  curl http://localhost:8000/api/videos \\")
        print("    -H 'X-API-Key: <key-from-above>'")
        print()
        print("Or login with username/password:")
        print("  curl -X POST http://localhost:8000/api/auth/login \\")
        print("    -H 'Content-Type: application/x-www-form-urlencoded' \\")
        print("    -d 'username=reuben&password=bestvideoproject'")
        print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
