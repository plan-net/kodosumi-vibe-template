#!/usr/bin/env python
"""Setup script for backward compatibility with older Python tooling."""

from setuptools import setup

if __name__ == "__main__":
    try:
        setup(name="kodosumi-vibe-template")
    except:  # noqa
        print(
            "An error occurred during setup; please ensure that setuptools is installed."
        )
        raise 