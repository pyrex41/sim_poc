#!/usr/bin/env python3
"""Check API keys in production database."""
from backend.database import get_db, init_db

init_db()

with get_db() as conn:
    # Get all users
    users = conn.execute('SELECT id, username, email, is_admin FROM users').fetchall()
    print('\n=== USERS ===')
    for user in users:
        print(f'ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Admin: {user[3]}')

    # Get all API keys (we can't retrieve the actual key, only metadata)
    keys = conn.execute('''
        SELECT ak.id, ak.name, ak.user_id, u.username, ak.is_active, ak.created_at
        FROM api_keys ak
        JOIN users u ON ak.user_id = u.id
        WHERE ak.is_active = 1
    ''').fetchall()

    print('\n=== ACTIVE API KEYS ===')
    if not keys:
        print('No API keys found in database')
    else:
        for key in keys:
            print(f'Key ID: {key[0]}, Name: {key[1]}, User: {key[3]} (ID: {key[2]}), Created: {key[5]}')
