# models.py

from sqlalchemy import Column, String, Text
from database import Base

class Job(Base):
    """Job model for tracking video generation tasks."""
    
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="processing")  # processing, completed, failed
    video_path = Column(String, nullable=True)
    error = Column(Text, nullable=True)
