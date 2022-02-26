"""Tests for tmuxp.

tmuxp.tests
~~~~~~~~~~~

"""
import os

current_dir = os.path.abspath(os.path.dirname(__file__))
example_dir = os.path.abspath(os.path.join(current_dir, "..", "examples"))
fixtures_dir = os.path.realpath(os.path.join(current_dir, "fixtures"))
