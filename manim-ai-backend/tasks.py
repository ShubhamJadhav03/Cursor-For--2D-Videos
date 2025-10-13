# tasks.py

from celery import Celery
import requests
import logging
import traceback

# --- NEW: Import database components ---
from database import SessionLocal
from models import Job

# Import our existing modules
from config import (
    OLLAMA_API_URL, OLLAMA_MODEL, SYSTEM_PROMPT,
    EXAMPLE_1_USER, EXAMPLE_1_ASSISTANT,
    EXAMPLE_2_USER, EXAMPLE_2_ASSISTANT,
    EXAMPLE_3_USER, EXAMPLE_3_ASSISTANT,
    EXAMPLE_4_USER, EXAMPLE_4_ASSISTANT,
)
from services import CodeValidator, ManimRunner

celery = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@celery.task
def generate_video_task(job_id: str, prompt: str):
    """
    Background task that now updates a PostgreSQL database with its progress.
    """
    # --- NEW: Get a database session ---
    db = SessionLocal()
    
    try:
        logging.info(f"📝 Worker received job {job_id} for prompt: '{prompt}'")
        
        # --- (Ollama and Manim logic remains the same) ---
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": EXAMPLE_1_USER}, {"role": "assistant", "content": EXAMPLE_1_ASSISTANT},
                {"role": "user", "content": EXAMPLE_2_USER}, {"role": "assistant", "content": EXAMPLE_2_ASSISTANT},
                {"role": "user", "content": EXAMPLE_3_USER}, {"role": "assistant", "content": EXAMPLE_3_ASSISTANT},
                {"role": "user", "content": EXAMPLE_4_USER}, {"role": "assistant", "content": EXAMPLE_4_ASSISTANT},
                {"role": "user", "content": prompt}
            ],
            "stream": False, "options": {"temperature": 0.2, "top_p": 0.95}
        }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=180)
        response.raise_for_status()
        raw_code = response.json().get("message", {}).get("content", "")

        validator = CodeValidator(raw_code)
        clean_code = validator.run()
        runner = ManimRunner(clean_code)
        video_path = runner.run()
        
        # --- NEW: Update the job as COMPLETED in the database ---
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "completed"
            job.video_path = video_path
            db.commit()
            logging.info(f"✅ Worker finished job {job_id}. Video at: {video_path}")
        
    except Exception as e:
        logging.error(f"❌ Worker failed job {job_id}. Error: {e}")
        traceback.print_exc()
        
        # --- NEW: Update the job as FAILED in the database ---
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            db.commit()
    finally:
        # --- NEW: Always close the database session ---
        db.close()