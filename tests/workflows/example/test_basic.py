"""Basic tests for the example workflow."""

import os
import pytest


def test_example_module_exists():
    """Test that the example module exists."""
    assert os.path.exists(os.path.join("workflows", "example"))


def test_main_exists():
    """Test that main.py exists."""
    assert os.path.exists(os.path.join("workflows", "example", "main.py"))


def test_serve_exists():
    """Test that serve.py exists."""
    assert os.path.exists(os.path.join("workflows", "example", "serve.py")) 