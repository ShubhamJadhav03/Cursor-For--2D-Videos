#!/bin/bash
set -e

echo "🚀 Starting Manim AI Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
python -c "
import psycopg2
import os
import time

max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_URL', 'postgresql://postgres:admin@localhost:5433/manim_jobs').split('@')[1].split('/')[0].split(':')[0],
            port=int(os.getenv('DATABASE_URL', 'postgresql://postgres:admin@localhost:5433/manim_jobs').split('@')[1].split('/')[0].split(':')[1]) if ':' in os.getenv('DATABASE_URL', 'postgresql://postgres:admin@localhost:5433/manim_jobs').split('@')[1].split('/')[0] else 5432,
            user='postgres',
            password='admin',
            database='manim_jobs'
        )
        conn.close()
        print('✅ Database is ready!')
        break
    except psycopg2.OperationalError:
        attempt += 1
        print(f'Attempt {attempt}/{max_attempts}: Database not ready, waiting...')
        time.sleep(2)
else:
    print('❌ Database connection failed after maximum attempts')
    exit(1)
"

# Initialize database
echo "🔧 Initializing database..."
python init_db.py

# Start the application
echo "🎬 Starting FastAPI server..."
exec "$@"
