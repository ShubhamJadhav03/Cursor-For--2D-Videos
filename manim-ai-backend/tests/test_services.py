# manim-ai-backend/tests/test_services.py

import pytest
import sys
import os

# Add the parent directory to the Python path so we can import from it
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import CodeValidator # Make sure to import the class to be tested

def test_code_validator_strips_markdown():
    """
    Tests if the CodeValidator correctly removes markdown fences.
    """
    # Input: Code with markdown fences
    raw_code = """```python
from manim import *

class MyScene(Scene):
    def construct(self):
        self.play(Write(Text("Hello")))
```"""

    # Expected Output: Clean code without fences
    expected_code = """from manim import *

class MyScene(Scene):
    def construct(self):
        self.play(Write(Text("Hello")))"""

    # Action: Run the validator
    validator = CodeValidator(raw_code)
    cleaned_code = validator.run()

    # Assert: Check if the output matches what we expect
    assert cleaned_code == expected_code

def test_code_validator_handles_empty_input():
    """
    Tests if the validator handles empty or whitespace-only input gracefully.
    """
    # Pytest's way of checking for an expected error
    with pytest.raises(Exception):
        validator = CodeValidator("   ")
        validator.run()