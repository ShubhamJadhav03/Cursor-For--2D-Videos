"""
Main entry point for the Manim AI Animation Generator.
Clean, minimal application setup with router integration.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.generation import router as generation_router

# --------------------------------------------------------------------------
# --- Configuration & Setup ---
# --------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="Manim AI Animation Generator",
    description="A robust backend to generate Manim animations from text prompts."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# --- Router Registration ---
# --------------------------------------------------------------------------

app.include_router(generation_router)

# --------------------------------------------------------------------------
# --- Root Endpoint ---
# --------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"status": "🚀 Manim AI Generator is running!"}