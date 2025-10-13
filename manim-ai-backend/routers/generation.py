"""
Router for animation generation endpoints.
Handles scene generation, clip upload, and story stitching.
"""

import os
import uuid
import shutil
import logging
import ffmpeg
from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from tasks import generate_video_task, celery
from schemas import SceneRequest, UploadClipResponse, StitchRequest, JobResponse, StatusResponse
from config import TEMP_CLIP_DIR, MEDIA_DIR
from database import get_db
from models import Job




# Create the router
router = APIRouter(tags=["generation"])


@router.post("/generate-scene/", response_model=JobResponse)
async def generate_scene(request: SceneRequest, db: Session = Depends(get_db)):
    """
    Creates a job record in the database, sends the job to Celery,
    and immediately returns a job ID.
    """
    try:
        job_id = str(uuid.uuid4())
        new_job = Job(id=job_id, status="processing")
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        generate_video_task.delay(job_id, request.prompt)
        logging.info(f"✨ Job {job_id} submitted for prompt: '{request.prompt}'")
        return {"job_id": job_id, "status": "processing"}
    except Exception as e:
        logging.error(f"Failed to submit task to Celery: {e}")
        raise HTTPException(status_code=500, detail="Failed to start the video generation job.")


@router.get("/task-status/{job_id}", response_model=StatusResponse)
async def get_task_status(job_id: str, db: Session = Depends(get_db)):
    """
    Checks the status of a job by querying the database.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "job_id": job.id,
        "status": job.status,
        "video_url": job.video_path,
        "error": job.error,
    }


@router.post("/upload-clip/", response_model=UploadClipResponse)
async def upload_clip(file: UploadFile = File(...)):
    """Receives a video clip from the frontend and saves it locally."""
    try:
        file_path = os.path.join(TEMP_CLIP_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"Clip saved to: {file_path}")
        return UploadClipResponse(file_path=file_path)
    except Exception as e:
        logging.error(f"Failed to upload clip: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded clip.")


@router.post("/stitch-story/")
async def stitch_story(request: StitchRequest):
    """Receives a list of local video file paths and stitches them together."""
    file_paths = request.file_paths
    
    if not file_paths:
        raise HTTPException(status_code=400, detail="No file paths provided.")

    logging.info(f"Stitching {len(file_paths)} clips...")
    
    for path in file_paths:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Clip not found on server: {path}")

    try:
        input_streams = [ffmpeg.input(path) for path in file_paths]
        
        # Concatenate (stitch) all video streams. Assumes no audio.
        stitched_video_node = ffmpeg.concat(*input_streams, v=1, a=0).node
        
        output_filename = f"story_{uuid.uuid4()}.mp4"
        final_video_dir = os.path.join(MEDIA_DIR, "videos")
        os.makedirs(final_video_dir, exist_ok=True)
        output_path = os.path.join(final_video_dir, output_filename)
        
        # We specify the first stream (the video stream) from the node.
        ffmpeg.output(stitched_video_node[0], output_path).run(overwrite_output=True)
        
        logging.info(f"Successfully stitched story to {output_path}")
        return FileResponse(output_path, media_type="video/mp4", filename="final_story.mp4")
        
    except ffmpeg.Error as e:
        error_details = e.stderr.decode('utf8') if e.stderr else 'Unknown FFmpeg error'
        logging.error(f"FFmpeg stitching failed: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to stitch video: {error_details}")
    finally:
        # Clean up the temporary clip files after stitching
        for path in file_paths:
            if os.path.exists(path):
                os.remove(path)


@router.get("/get-video/")
async def get_video(path: str):
    """
    Safely serves a video file from the server's media directory.
    The frontend will call this to get the actual video data.
    """
    # Security Check: Ensure the requested path is within our allowed media directory
    # to prevent users from accessing arbitrary files on the server.
    if not os.path.abspath(path).startswith(os.path.abspath(MEDIA_DIR)):
        raise HTTPException(status_code=403, detail="Forbidden: Access to this path is not allowed.")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Video file not found.")

    return FileResponse(path, media_type="video/mp4", filename=os.path.basename(path))