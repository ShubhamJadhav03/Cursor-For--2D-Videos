#!/usr/bin/env python3
"""
Database initialization script for Docker.
Creates tables if they don't exist.
"""

import os
import sys
from database import engine, Base
from models import Job

def init_database():
    """Initialize the database by creating all tables."""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
