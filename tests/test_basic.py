"""Basic tests for the kodosumi-vibe-template package."""
import os
import sys
import pytest


def test_workflows_module_exists():
    """Test that the workflows module exists."""
    assert "workflows" in sys.modules or os.path.exists("workflows")


def test_crewai_flow_module_exists():
    """Test that the crewai_flow module exists."""
    assert os.path.exists(os.path.join("workflows", "crewai_flow"))


def test_main_file_exists():
    """Test that the main.py file exists."""
    assert os.path.exists(os.path.join("workflows", "crewai_flow", "main.py"))


def test_serve_file_exists():
    """Test that the serve.py file exists."""
    assert os.path.exists(os.path.join("workflows", "crewai_flow", "serve.py")) 