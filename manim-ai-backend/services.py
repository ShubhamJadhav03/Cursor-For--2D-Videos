"""
Service classes for the Manim AI Animation Generator.
Contains CodeValidator and ManimRunner classes.
"""

import os
import re
import sys
import ast
import uuid
import shutil
import subprocess
import logging
import requests
from fastapi import HTTPException

from config import (
    OLLAMA_API_URL,
    OLLAMA_MODEL,
    PROJECT_ROOT,
    MEDIA_DIR,
    TEMP_SCENES_DIR,
    TEMP_CLIP_DIR,
    SYSTEM_PROMPT,
    EXAMPLE_1_USER,
    EXAMPLE_1_ASSISTANT,
    EXAMPLE_2_USER,
    EXAMPLE_2_ASSISTANT,
    EXAMPLE_3_USER,
    EXAMPLE_3_ASSISTANT,
    EXAMPLE_4_USER,
    EXAMPLE_4_ASSISTANT,
)

# Ensure directories exist
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(TEMP_SCENES_DIR, exist_ok=True)
os.makedirs(TEMP_CLIP_DIR, exist_ok=True)


class CodeValidator:
    """Validates and auto-fixes AI-generated Manim code."""
    
    def __init__(self, raw_code: str):
        self.code = raw_code or ""
        self.fixes_applied = []

    def _strip_markdown(self):
        self.code = re.sub(r"```(?:python)?\n?|```", "", self.code).strip()

    def _apply_regex_fixes(self):
        # Replace deprecated GrowArrow with Create(Arrow(...)) usage assumption
        if "GrowArrow" in self.code:
            self.code = self.code.replace("GrowArrow", "Create")
            self.fixes_applied.append("Replaced GrowArrow with Create")

        # Remove hallucinated self.create() calls
        if "self.create(" in self.code:
            self.code = re.sub(r"self\.create\((.*?)\)", r"\1", self.code)
            self.fixes_applied.append("Removed hallucinated self.create()")

        # Fix incorrect f-string formatting e.g., {var.1f} -> {var:.1f}
        if "{" in self.code and ".f}" in self.code:
            self.code = re.sub(r"\{(\w+)\.(\d+)f\}", r"{\1:.\2f}", self.code)
            self.fixes_applied.append("Fixed f-string format")

        # Remove common newer args that break older Manim versions (safe to drop)
        # node_scale_factor, layout_scale, layout_config are introduced in newer versions.
        self.code, n1 = re.subn(r"\bnode_scale_factor\s*=\s*[^,)\n]+,?", "", self.code)
        self.code, n2 = re.subn(r"\blayout_scale\s*=\s*[^,)\n]+,?", "", self.code)
        self.code, n3 = re.subn(r"\blayout_config\s*=\s*[^,)\n]+,?", "", self.code)
        if n1 + n2 + n3:
            self.fixes_applied.append("Removed unsupported Graph kwargs (node_scale_factor/layout_scale/layout_config)")

        # If Graph(...) contains vertex_config or node_config as dicts with newer keys
        # we keep them but ensure they don't break syntax (basic sanitize).
        # Remove trailing commas before closing parens caused by previous removals
        self.code = re.sub(r",\s*\)", ")", self.code)

    def _auto_inject_imports(self):
        if "from manim import *" not in self.code:
            self.code = "from manim import *\n" + self.code
            self.fixes_applied.append("Auto-injected 'from manim import *'")

        if "np." in self.code and "import numpy as np" not in self.code:
            self.code = self.code.replace("from manim import *", "from manim import *\nimport numpy as np")
            self.fixes_applied.append("Auto-injected 'import numpy as np'")

    def _validate_syntax(self):
        try:
            ast.parse(self.code)
        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            logging.error(f"❌ Final code has a Syntax Error: {error_msg}")
            logging.error(f"--- FAILED CODE ---\n{self.code}\n---")
            raise HTTPException(status_code=500, detail=f"AI generated invalid Python code: {error_msg}")

    def run(self) -> str:
        if not self.code.strip():
            raise HTTPException(status_code=500, detail="AI returned an empty response.")

        self._strip_markdown()
        self._apply_regex_fixes()
        self._auto_inject_imports()
        self._validate_syntax()

        if self.fixes_applied:
            logging.warning(f"🔧 AUTO-FIXES APPLIED: {', '.join(self.fixes_applied)}")

        return self.code


class ManimRunner:
    """Handles the execution of Manim animations."""
    
    def __init__(self, code: str):
        self.code = code
        self.job_id = str(uuid.uuid4())
        # write script into temp_scenes directory so uvicorn reload can ignore it
        self.script_name = f"scene_{self.job_id}.py"
        self.script_path = os.path.join(TEMP_SCENES_DIR, self.script_name)

    def _detect_scene_name(self) -> str:
        match = re.search(r"class\s+(\w+)\s*\(\s*Scene\s*\):", self.code)
        if match:
            return match.group(1)
        raise HTTPException(status_code=500, detail="Could not detect Scene class name in the generated code.")

    def _write_script_to_file(self):
        with open(self.script_path, "w", encoding="utf-8") as f:
            f.write(self.code)

    def _cleanup(self):
        # Remove the generated script file
        try:
            if os.path.exists(self.script_path):
                os.remove(self.script_path)
        except Exception as e:
            logging.warning(f"Could not delete script file: {e}")

    def _find_video_file(self, scene_name: str) -> str:
        """
        Manim outputs media/videos/<script_stem>/<quality>/<scene_name>.mp4
        We'll search common qualities and fall back to scanning media dir.
        """
        script_stem = os.path.splitext(self.script_name)[0]
        qualities = ["480p15", "720p30", "1080p60", "low_quality", "default"]
        for quality in qualities:
            scene_dir = os.path.join(MEDIA_DIR, "videos", script_stem, quality)
            if os.path.exists(scene_dir):
                files = [os.path.join(scene_dir, f) for f in os.listdir(scene_dir) if f.endswith(".mp4")]
                if files:
                    return max(files, key=os.path.getmtime)

        # Fallback: scan media/videos for any file that contains our job id in path
        for root, _, files in os.walk(os.path.join(MEDIA_DIR, "videos")):
            for fname in files:
                if fname.endswith(".mp4") and self.job_id in root:
                    return os.path.join(root, fname)

        # Final fallback: return newest mp4 in media directory (if any)
        mp4s = []
        for root, _, files in os.walk(MEDIA_DIR):
            for fname in files:
                if fname.endswith(".mp4"):
                    mp4s.append(os.path.join(root, fname))
        if mp4s:
            return max(mp4s, key=os.path.getmtime)

        return ""

    def run(self) -> str:
        # write the script
        self._write_script_to_file()
        scene_name = self._detect_scene_name()

        command = [
            sys.executable, "-m", "manim",
            self.script_path, scene_name, "-ql"
        ]
        logging.info(f"🎬 Running Manim command: {' '.join(command)}")

        try:
            # Run manim; capture stdout/stderr
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,
                check=True,
                env=os.environ.copy()
            )
            logging.info("✅ Manim rendering completed successfully!")

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip() if e.stderr else (e.output or "")
            logging.error(f"❌ Manim rendering failed. Stderr:\n{stderr}")

            # Try to extract a meaningful last line
            last_line = stderr.splitlines()[-1] if stderr else "Unknown Manim error"
            raise HTTPException(status_code=500, detail=f"Manim rendering failed: {last_line}")

        except subprocess.TimeoutExpired as e:
            logging.error("❌ Manim rendering timed out.")
            raise HTTPException(status_code=504, detail="Rendering timed out after 5 minutes.")
        finally:
            # attempt cleanup of script file (we still need output in media dir)
            self._cleanup()

        # Locate the produced video file
        video_file = self._find_video_file(scene_name)
        if video_file and os.path.exists(video_file):
            return video_file

        raise HTTPException(status_code=404, detail="Video file not found after a successful render.")


class AIService:
    """Handles AI model communication for code generation."""
    
    @staticmethod
    def generate_code(prompt: str) -> str:
        """Generate Manim code using the AI model."""
        try:
            logging.info(f"📝 Sending prompt to {OLLAMA_MODEL}: '{prompt}'")
            
            # Prepare the payload with examples
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": EXAMPLE_1_USER},
                    {"role": "assistant", "content": EXAMPLE_1_ASSISTANT},
                    {"role": "user", "content": EXAMPLE_2_USER},
                    {"role": "assistant", "content": EXAMPLE_2_ASSISTANT},
                    {"role": "user", "content": EXAMPLE_3_USER},
                    {"role": "assistant", "content": EXAMPLE_3_ASSISTANT},
                    {"role": "user", "content": EXAMPLE_4_USER},
                    {"role": "assistant", "content": EXAMPLE_4_ASSISTANT},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.2, "top_p": 0.95}
            }
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=180)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
        except requests.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Could not connect to the Ollama AI model: {e}")
