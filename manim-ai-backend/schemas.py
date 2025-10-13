"""
Pydantic models for data validation in the Manim AI Animation Generator.
"""

from pydantic import BaseModel
from typing import List, Optional


class SceneRequest(BaseModel):
    """Request model for generating a single Manim animation."""
    prompt: str


class UploadClipResponse(BaseModel):
    """Response model for uploaded clip."""
    file_path: str


class StitchRequest(BaseModel):
    """Request model for stitching video clips together."""
    file_paths: List[str]


class JobResponse(BaseModel):
    """Response when submitting a background generation job."""
    job_id: str
    status: str  # e.g., "processing"


class StatusResponse(BaseModel):
    """Response for checking background job status."""
    job_id: str
    status: str  # "processing" | "completed" | "failed"
    video_url: Optional[str] = None
    error: Optional[str] = None
