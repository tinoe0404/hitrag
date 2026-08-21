#!/usr/bin/env python3
"""Bootstrap script to create an ADMIN user in HITRAG.

Run this script after deployment to ensure an admin account exists.
It uses the existing registration service but forces the role to ADMIN.
"""

import sys
sys.path.insert(0, ".")  # Ensure project root is on PYTHONPATH

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.services.auth import register_user
from app.schemas.auth import UserCreate


def main():
    db = SessionLocal()
    try:
        print("Create ADMIN user")
        email = input("Admin email: ").strip()
        password = input("Password: ").strip()
        full_name = input("Full name: ").strip()
        admin_payload = UserCreate(
            email=email,
            password=password,
            full_name=full_name,
            role=UserRole.ADMIN,
        )
        register_user(db, admin_payload)
        print(f"ADMIN user {email} created successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
