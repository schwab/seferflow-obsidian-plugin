# Installation Guide

Complete step-by-step installation instructions for Book Reader.

## Quick Install (Recommended)

### Linux/macOS

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/book-reader.git
cd book-reader

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip and setuptools FIRST
pip install --upgrade pip setuptools

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify installation
bash verify_book_reader.sh

# 6. Run!
./book_reader
```

## Detailed Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/book-reader.git
cd book-reader
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### Step 3: Install System Dependencies

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y python3-dev poppler-utils
```

#### macOS
```bash
brew install poppler
```

#### Windows
```bash
# Install Python 3.8+ from python.org
# Install poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
# Add poppler to PATH
```

### Step 4: Upgrade pip and setuptools

**IMPORTANT**: Do this BEFORE installing requirements.txt

```bash
pip install --upgrade pip setuptools wheel
```

### Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you get errors, try:

```bash
pip install --no-cache-dir -r requirements.txt
```

### Step 6: Verify Installation

```bash
bash verify_book_reader.sh
```

This should show:
```
✓ Virtual environment found
✓ soundfile
✓ sounddevice
✓ edge-tts
✓ numpy
✓ pdftotext
✓ clear
✓ Files present
✓ Books directory with PDFs
✅ Verification complete!
```

### Step 7: Run!

```bash
./book_reader
```

## Troubleshooting Installation

### Error: "Cannot import 'setuptools.build_meta'"

**Solution**: Upgrade pip and setuptools before installing requirements:

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Error: "sounddevice not found"

**Solution**: Install from PyPI:

```bash
pip install sounddevice
```

Or use fallback playback with `aplay`:

```bash
# Linux
sudo apt-get install alsa-utils

# macOS
brew install sox
```

### Error: "No module named 'pdftotext'"

**Solution**: Install Poppler:

```bash
# Linux
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/
```

### Error: "edge-tts: No module named asyncio"

**Solution**: This shouldn't happen with Python 3.8+. Verify:

```bash
python3 --version  # Should be 3.8 or higher
```

If you're on Python 3.7 or older, upgrade Python:

```bash
# macOS
brew install python3.11

# Linux
sudo apt-get install python3.11
```

### Permission Denied on book_reader

**Solution**: Make executable:

```bash
chmod +x book_reader book_reader_simple.py
```

## Optional: Install Development Tools

For contributing:

```bash
pip install pytest pytest-cov black flake8 mypy
```

## Optional: Install Offline TTS (Kokoro)

For completely offline operation (no internet needed):

```bash
pip install kokoro-onnx
```

This downloads ~300MB of model files on first use.

## Alternative: Install as Package

If you want system-wide installation:

```bash
# After setting up venv and upgrading pip/setuptools:
pip install --upgrade pip setuptools wheel
pip install -e .
```

Then you can run from anywhere:

```bash
book-reader
```

**Note**: You may need to install the package properly. For now, the direct `./book_reader` method is recommended.

## Verify Your Installation

### Quick Test

```bash
# Test that the app runs
./book_reader

# Then:
# 1. Select any book from the file browser
# 2. Pick a chapter
# 3. Choose voice and speed
# 4. Should see visualization after ~15-20 seconds
# 5. Press Ctrl+C to stop
```

### Full Test

```bash
bash verify_book_reader.sh
```

### Individual Module Tests

```bash
python3 -c "import soundfile; print('✓ soundfile')"
python3 -c "import sounddevice; print('✓ sounddevice')"
python3 -c "import numpy; print('✓ numpy')"
python3 -c "import edge_tts; print('✓ edge-tts')"
```

## Environment Variables (Optional)

You can customize behavior with:

```bash
# Set default book directory
export BOOK_READER_HOME=/path/to/your/books

# Use specific audio device
export SOUNDDEVICE_DEVICE=2  # Device index
```

## Updating

To update to the latest version:

```bash
cd book-reader
git pull origin main
pip install --upgrade -r requirements.txt
```

## Uninstall

To remove completely:

```bash
# Deactivate venv
deactivate

# Remove directory
rm -rf ~/projects/book-reader
rm -rf ~/.virtualenvs/book-reader-lwwo  # or wherever your venv is
```

## Getting Help

- **Installation issues**: See [Troubleshooting](#troubleshooting-installation) above
- **Usage questions**: See `README.md`
- **Contributing**: See `CONTRIBUTING.md`
- **Bug reports**: GitHub Issues

---

**Next**: Run `./book_reader` and enjoy your audiobooks! 🎵
