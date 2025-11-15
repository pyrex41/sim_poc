#!/usr/bin/env python3
"""Check if users exist in the database."""
import sys
sys.path.insert(0, '/app')

from database import get_db

with get_db() as conn:
    users = conn.execute("SELECT id, username, is_active FROM users").fetchall()
    if users:
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  - ID: {user[0]}, Username: {user[1]}, Active: {user[2]}")
    else:
        print("No users found in database!")
