#!/usr/bin/env python3
"""
Setup script for SeferFlow package.

NOTE: For most users, just run:
  pip install -r requirements.txt
  ./seferflow

This setup.py is optional and for advanced package installation.
"""

try:
    from setuptools import setup
except ImportError:
    print("ERROR: setuptools not found!")
    print("Install it first: pip install --upgrade pip setuptools wheel")
    exit(1)

from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    try:
        long_description = readme_file.read_text(encoding="utf-8")
    except Exception:
        pass

setup(
    name="seferflow",
    version="1.3.0",
    description="Terminal-based PDF audiobook player with neural TTS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SeferFlow Contributors",
    url="https://github.com/YOUR_USERNAME/book-reader",
    project_urls={
        "Bug Tracker": "https://github.com/YOUR_USERNAME/book-reader/issues",
        "Documentation": "https://github.com/YOUR_USERNAME/book-reader/blob/main/README.md",
        "Source Code": "https://github.com/YOUR_USERNAME/book-reader",
    },
    license="MIT",
    python_requires=">=3.8",
    install_requires=[
        "soundfile>=0.12.1",
        "sounddevice>=0.4.5",
        "numpy>=1.21.0",
        "edge-tts>=6.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
        "offline": [
            "kokoro-onnx>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "book-reader=seferflow_simple:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Office/Business",
        "Topic :: Utilities",
    ],
    keywords=[
        "audiobook",
        "pdf",
        "text-to-speech",
        "tts",
        "neural",
        "edge-tts",
        "reader",
        "terminal",
    ],
)
