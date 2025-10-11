"""
Router for animation generation endpoints.
Handles scene generation, clip upload, and story stitching.
"""

import os
import uuid
import shutil
import logging
import ffmpeg
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse

from schemas import SceneRequest, UploadClipResponse, StitchRequest
from services import CodeValidator, ManimRunner, AIService
from config import TEMP_CLIP_DIR, MEDIA_DIR

# Create the router
router = APIRouter(tags=["generation"])


@router.post("/generate-scene/")
async def generate_scene(request: SceneRequest):
    """Generate a single Manim animation from a text prompt."""
    try:
        # Generate code using AI service
        raw_code = AIService.generate_code(request.prompt)
        
        # Validate and run the code
        validator = CodeValidator(raw_code)
        clean_code = validator.run()
        runner = ManimRunner(clean_code)
        video_path = runner.run()
        
        logging.info(f"🎥 Returning video file: {video_path}")
        return FileResponse(video_path, media_type="video/mp4", filename="animation.mp4")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in generate_scene: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected internal error occurred: {e}")


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
