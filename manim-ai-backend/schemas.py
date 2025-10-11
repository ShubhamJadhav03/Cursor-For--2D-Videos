"""
Pydantic models for data validation in the Manim AI Animation Generator.
"""

from pydantic import BaseModel
from typing import List


class SceneRequest(BaseModel):
    """Request model for generating a single Manim animation."""
    prompt: str


class UploadClipResponse(BaseModel):
    """Response model for uploaded clip."""
    file_path: str


class StitchRequest(BaseModel):
    """Request model for stitching video clips together."""
    file_paths: List[str]
