#!/bin/bash
# Verify Book Reader setup
set -e

echo "📚 Book Reader Setup Verification"
echo "=================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"

# Use venv Python if available
if [ -x "$VENV_PYTHON" ]; then
    PYTHON_CMD="$VENV_PYTHON"
    echo "✓ Virtual environment found at venv/"
else
    PYTHON_CMD="python3"
    echo "⚠ Using system Python (no venv found)"
fi

echo ""
echo "Checking Python dependencies..."
echo ""

# Check each dependency
check_module() {
    local module=$1
    local package=$2
    if "$PYTHON_CMD" -c "import $module" 2>/dev/null; then
        echo "  ✓ $module"
    else
        echo "  ✗ $module (install with: pip install $package)"
        return 1
    fi
}

check_module "soundfile" "soundfile"
check_module "sounddevice" "sounddevice"
check_module "edge_tts" "edge-tts"
check_module "numpy" "numpy"

echo ""
echo "Checking system utilities..."
echo ""

# Check system utilities
check_command() {
    local cmd=$1
    if command -v "$cmd" &>/dev/null; then
        echo "  ✓ $cmd"
    else
        echo "  ✗ $cmd (install it or use --batch mode)"
        return 1
    fi
}

check_command "pdftotext"
check_command "clear"

echo ""
echo "Checking files..."
echo ""

check_file() {
    local f=$1
    if [ -f "$f" ]; then
        echo "  ✓ $(basename $f)"
    else
        echo "  ✗ $(basename $f) - missing!"
        return 1
    fi
}

check_file "$SCRIPT_DIR/book_reader"
check_file "$SCRIPT_DIR/book_reader_simple.py"
check_file "$SCRIPT_DIR/book_reader.py"

echo ""
echo "Checking book directory..."
echo ""

if [ -d "/home/mcstar/Nextcloud/Vault/books" ]; then
    count=$(find "/home/mcstar/Nextcloud/Vault/books" -name "*.pdf" 2>/dev/null | wc -l)
    echo "  ✓ Books directory: $count PDF files found"
else
    echo "  ⚠ Books directory not found at /home/mcstar/Nextcloud/Vault/books"
fi

echo ""
echo "✅ Verification complete!"
echo ""
echo "To start the book reader, run:"
echo "  /home/mcstar/.openclaw/workspace-dev/book_reader"
echo ""
