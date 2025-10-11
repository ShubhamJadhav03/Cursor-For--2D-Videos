from manim import *
import numpy as np

class GeneratedScene(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        
        # 1. Create the nodes
        node_a = Dot(color=BLUE).move_to(LEFT * 3)
        node_b = Dot(color=RED).next_to(node_a, RIGHT)
        node_c = Dot(color=GREEN).next_to(node_b, RIGHT)
        
        # 2. Create the labels
        label_a = Text("A", color=BLUE).scale(0.8).move_to(node_a)
        label_b = Text("B", color=RED).scale(0.8).next_to(node_b, DOWN)
        label_c = Text("C", color=GREEN).scale(0.8).next_to(node_c, DOWN)
        
        # 3. Create the edges
        edge_ab = Line(node_a, node_b, color=BLACK)
        edge_bc = Line(node_b, node_c, color=BLACK)
        
        # 4. Animate the edges
        self.play(Create(node_a), Create(node_b), Create(node_c), run_time=1)
        self.wait(0.5)
        self.play(Write(label_a), Write(label_b), Write(label_c), run_time=1)
        self.wait(0.5)
        self.play(GrowArrow(edge_ab), GrowArrow(edge_bc), run_time=1)
        self.wait(2)