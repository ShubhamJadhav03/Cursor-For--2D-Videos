"""
Configuration file for the Manim AI Animation Generator.
Contains all global constants and prompt engineering templates.
"""

import os

# --- Constants ---
OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "codellama:7b"
PROJECT_ROOT = os.getcwd()
MEDIA_DIR = os.path.join(PROJECT_ROOT, "media")
TEMP_SCENES_DIR = os.path.join(PROJECT_ROOT, "temp_scenes")
TEMP_CLIP_DIR = os.path.join(MEDIA_DIR, "temp_clips")

# --- Prompt Engineering Section ---

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

# --- Examples ---
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
