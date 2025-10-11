import os
import re
import sys
import ast
import uuid
import shutil
import subprocess
import logging
import requests
from fastapi import FastAPI, Body, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import ffmpeg # <-- FIXED: Added the missing ffmpeg import

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

# --- Constants ---
OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "codellama:7b"
PROJECT_ROOT = os.getcwd()
MEDIA_DIR = os.path.join(PROJECT_ROOT, "media")
TEMP_SCENES_DIR = os.path.join(PROJECT_ROOT, "temp_scenes")
TEMP_CLIP_DIR = os.path.join(MEDIA_DIR, "temp_clips")
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(TEMP_SCENES_DIR, exist_ok=True)
os.makedirs(TEMP_CLIP_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# --- Prompt Engineering Section ---
# --------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert Manim code generator. You generate ONLY Python code for Manim Community Edition v0.18.0.

VERY IMPORTANT RULES:
1.  Your response MUST BE ONLY valid Python code. No explanations or markdown.
2.  The main class MUST inherit from `Scene`.
3.  The scene background MUST be `WHITE`. Start the `construct` method with `self.camera.background_color = WHITE`.
4.  NEVER use `GrowArrow`. It is deprecated. Use `Create(Arrow(...))` instead.
5.  NEVER use `FunctionGraph`. It is deprecated. Use `Axes` and `axes.plot()` instead.
6.  Follow all style and code patterns from the examples provided.
7.  End every scene with `self.wait(2)`.
"""

# --- Examples (unchanged) ---
EXAMPLE_1_USER = "Show a blue circle turning into a red square."
EXAMPLE_1_ASSISTANT = """from manim import *
import numpy as np
class CircleToSquare(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        circle = Circle(color=BLUE)
        square = Square(color=RED)
        self.play(Create(circle), run_time=1)
        self.wait(1)
        self.play(Transform(circle, square), run_time=1)
        self.wait(2)
"""

EXAMPLE_2_USER = "Create two labeled boxes, 'Client' and 'Server', and draw an arrow between them."
EXAMPLE_2_ASSISTANT = """from manim import *
import numpy as np
class ClientServer(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        client_box = Square(color=BLACK).move_to(LEFT * 3)
        client_label = Text("Client", color=BLACK).scale(0.8).next_to(client_box, DOWN)
        server_box = Square(color=BLACK).move_to(RIGHT * 3)
        server_label = Text("Server", color=BLACK).scale(0.8).next_to(server_box, DOWN)
        arrow = Arrow(client_box.get_right(), server_box.get_left(), color=BLACK, buff=0.1)
        self.play(Create(client_box), Write(client_label), run_time=1)
        self.play(Create(server_box), Write(server_label), run_time=1)
        self.play(Create(arrow), run_time=1)
        self.wait(2)
"""

EXAMPLE_3_USER = "Visualize a stack. Animate pushing the number 3 onto the stack, then popping it off."
EXAMPLE_3_ASSISTANT = """from manim import *
import numpy as np
class StackExample(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        stack_rect = Rectangle(width=2.0, height=4.0, color=BLACK)
        stack_label = Text("Stack", color=BLACK).scale(0.8).next_to(stack_rect, UP, buff=0.3)
        element = Text("3", color=BLUE).scale(1.2).move_to(LEFT * 4)
        stack_top_pos = stack_rect.get_center() + UP * 1.5
        self.play(Create(stack_rect), Write(stack_label), run_time=1)
        self.wait(0.5)
        self.play(element.animate.move_to(stack_top_pos), run_time=1)
        self.wait(0.5)
        self.play(element.animate.move_to(RIGHT * 4), run_time=1)
        self.wait(2)
"""

EXAMPLE_4_USER = "Plot the graph of the function y = x**2 from x = -2 to x = 2."
EXAMPLE_4_ASSISTANT = """from manim import *
import numpy as np
class GraphPlot(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        axes = Axes(x_range=[-3, 3, 1], y_range=[-1, 9, 1], axis_config={"color": BLACK})
        graph = axes.plot(lambda x: x**2, color=BLUE)
        graph_label = axes.get_graph_label(graph, label='y=x^2')
        self.play(Create(axes), run_time=1)
        self.play(Create(graph), Write(graph_label), run_time=1)
        self.wait(2)
"""

# --------------------------------------------------------------------------
# --- Code Validation & Auto-Fixing Class ---
# --------------------------------------------------------------------------

class CodeValidator:
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

# --------------------------------------------------------------------------
# --- Manim Runner Class ---
# --------------------------------------------------------------------------

class ManimRunner:
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


# --------------------------------------------------------------------------
# --- API Endpoints ---
# --------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"status": "🚀 Manim AI Generator is running!"}

@app.post("/generate-scene/")
async def generate_scene(prompt: str = Body(..., embed=True)):
    """Generate a single Manim animation from a text prompt."""
    try:
        logging.info(f"📝 Sending prompt to {OLLAMA_MODEL}: '{prompt}'")
        
        # --- THIS IS THE CORRECT PAYLOAD ---
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
        raw_code = response.json().get("message", {}).get("content", "")
    except requests.RequestException as e:
        # ... (error handling remains the same)
        raise HTTPException(status_code=503, detail=f"Could not connect to the Ollama AI model: {e}")

    try:
        validator = CodeValidator(raw_code)
        clean_code = validator.run()
        runner = ManimRunner(clean_code)
        video_path = runner.run()
    except HTTPException:
        raise
    except Exception as e:
        # ... (error handling remains the same)
        raise HTTPException(status_code=500, detail=f"An unexpected internal error occurred: {e}")

    logging.info(f"🎥 Returning video file: {video_path}")
    return FileResponse(video_path, media_type="video/mp4", filename="animation.mp4")

# --------------------------------------------------------------------------
# --- Story Generation Endpoints ---
# --------------------------------------------------------------------------
@app.post("/upload-clip/")
async def upload_clip(file: UploadFile = File(...)):
    """Receives a video clip from the frontend and saves it locally."""
    try:
        file_path = os.path.join(TEMP_CLIP_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"Clip saved to: {file_path}")
        return {"file_path": file_path}
    except Exception as e:
        logging.error(f"Failed to upload clip: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded clip.")

@app.post("/stitch-story/")
async def stitch_story(file_paths: List[str] = Body(..., embed=True)):
    """Receives a list of local video file paths and stitches them together."""
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