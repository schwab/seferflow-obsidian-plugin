# SeferFlow - Terminal-Based PDF Audiobook Player

A Python terminal application that converts PDF books into natural-sounding audiobooks using neural text-to-speech (TTS). Stream chapters with real-time buffer visualization, multiple voice options, and adjustable playback speed.

**Status**: ✅ Production Ready (v1.4)

## Features

### 🎵 Core Functionality
- **PDF Chapter Detection** - Automatically detects chapters from PDF bookmarks
- **Neural Voice TTS** - Microsoft Edge TTS with 4 professional voice options
- **Streaming Playback** - First audio section plays ~15-20 seconds after selection; rest streams while listening
- **Adjustable Speed** - 6 playback speeds (0.8x - 1.3x)
- **Directory Navigation** - Browse book collections intuitively
- **Batch Mode** - Command-line automation with full feature set

### 🎨 User Interface (v1.4)
- **Live Visualization** - Real-time buffer fill, progress bar, and time tracking
- **Color-Coded Progress** - Green (played), Yellow (buffered), Gray (pending)
- **Direct Settings Selection** - Change voice/speed with single keypresses
- **Persistent Settings** - Your voice and speed preferences saved automatically
- **Clean Text Menus** - Simple, intuitive navigation
- **No Terminal Crashes** - Stable ANSI display, no raw tty mode hacks

### 🔧 Technical Features
- **Producer/Consumer Pattern** - Background TTS generation with bounded memory
- **Audio Buffering** - 2-chunk overlap for smooth transitions
- **Multiple TTS Engines** - Kokoro, Edge-TTS, espeak with automatic fallback
- **Thread-Safe Playback** - Safe concurrent generation and playback
- **Cross-Platform** - Linux, macOS (requires system dependencies)

## Installation

### Quick Start (Recommended)

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/seferflow.git
cd seferflow

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# IMPORTANT: Upgrade pip and setuptools FIRST
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Verify setup
./verify_book_reader.sh

# Run!
./book_reader
```

### Detailed Installation

For complete step-by-step instructions including system dependencies, troubleshooting, and optional features, see **[INSTALL.md](INSTALL.md)**.

This includes:
- Linux/macOS/Windows setup
- System dependency installation
- Troubleshooting common errors
- Optional offline TTS setup
- Development environment setup

### Requirements

- Python 3.8 or higher
- `pdftotext` from Poppler (installed via system package manager)
- Audio playback device (sounddevice or aplay)

## Usage

### Interactive Mode (Default)

Start the application and follow the menus:

```bash
./book_reader

# 1. Browse directories/PDFs using numbers
# 2. Select a chapter
# 3. Choose voice [a-d] and speed [1-6]
# 4. Press Enter to start
# 5. Watch real-time visualization
# 6. Press Ctrl+C to stop
```

### Settings Menu

```
Speed: 1.0x
[1] 0.8x  [2] 0.9x  [3] 1.0x ← current  [4] 1.1x  [5] 1.2x  [6] 1.3x

Voice: en-US-AriaNeural
[a] Female (US, default) ← current
[b] Male (US)
[c] Female (British)
[d] Male (British)

[Enter] Start reading  [q] Cancel
```

**Direct selection**: Just press a number or letter—no sub-menus!

### Live Playback Display

```
──────────────────────────────────────────────────────────────
▶ PLAYING   Chapter Title                     1.0x  Voice
──────────────────────────────────────────────────────────────

  Section 3 of 8    2:34 / ~23:45 est.

  Progress:  ████████████████████▓▓▓▓░░░░░░░░░░░░░░░░  37%

  Buffer:    [███▓░░░░]  2/3 ready    ↺ generating...

  Ctrl+C to stop
──────────────────────────────────────────────────────────────
```

**Color Legend**:
- 🟩 Green `█` = Sections already played
- 🟨 Yellow `▓` = Sections buffered, ready to play
- ⬜ Gray `░` = Sections not yet generated

### Batch Mode

For automation and scripting:

```bash
# Read a specific chapter
./seferflow --batch /path/to/book.pdf --chapter 3

# With custom voice and speed
./seferflow --batch /path/to/book.pdf \
  --chapter "Introduction" \
  --voice en-US-GuyNeural \
  --speed 1.2

# Save to audio file
./seferflow --batch /path/to/book.pdf \
  --chapter 3 \
  --save output.wav

# List available voices
./seferflow --batch --list-voices

# Advanced: Specific page range
./seferflow --batch /path/to/book.pdf \
  --pages 10-50 \
  --speed 0.9
```

## Architecture

### Directory Structure

```
seferflow/
├── seferflow              # Main wrapper script
├── seferflow.py    # Interactive mode (21KB)
├── seferflow_batch.py           # Batch mode (20KB)
├── verify_book_reader.sh    # Setup verification
├── README.md                # This file
├── CHANGELOG.md             # Version history
├── LICENSE                  # MIT License
└── docs/
    ├── FEATURES.md          # Detailed feature guide
    ├── ARCHITECTURE.md      # Technical design
    └── TROUBLESHOOTING.md   # Help & FAQ
```

### Design Patterns

**Streaming TTS with Producer/Consumer**:
- Main thread: UI, menus, display
- Producer thread: Generates TTS chunks in background
- Consumer (main): Plays chunks as they become ready
- Queue (size 3): Buffers chunks, bounds memory

**Display Updates**:
- ANSI color codes for progress bar
- ANSI cursor movement for in-place updates
- 400ms polling loop (doesn't block audio)
- No raw terminal mode (prevents crashes)

**Audio Buffering**:
- 2-chunk overlap before playback
- Eliminates gaps at chunk boundaries
- Blocksize optimization (2048 bytes) for 24kHz audio

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Chapter detection | <1s | PDF metadata read |
| Text extraction | 1-5s | Depends on chapter size |
| First audio plays | 15-20s | One chunk ~2000 chars TTS |
| Smooth playback | Always | 2-chunk buffering |
| Buffer updates | 400ms | Display refresh rate |

## Supported TTS Engines

### Primary: Edge-TTS (Microsoft Neural Voices)
- **Voices**: 4 professional English voices
- **Quality**: ⭐⭐⭐⭐⭐ Excellent
- **Speed**: ~15-20s per 2000-char chunk
- **Requirements**: Internet connection
- **License**: Free (no API key)

### Fallback: Kokoro-ONNX (Local, Offline)
- **Quality**: ⭐⭐⭐⭐ Very good
- **Speed**: Fast (CPU only)
- **Download**: ~300MB models
- **License**: Open source

### Last Resort: espeak (System)
- **Quality**: ⭐⭐ Basic (robotic)
- **Speed**: Very fast
- **Requirements**: Already installed
- **License**: Open source

## Keyboard Controls

### During Setup
- `[1-6]` - Direct speed selection
- `[a-d]` - Direct voice selection
- `[Enter]` - Start playback
- `[q]` - Cancel

### During Playback
- `[Ctrl+C]` - Stop cleanly (terminal remains functional)

*Future additions planned*: Pause/resume, seek forward/backward

## Troubleshooting

### "No PDFs found in directory"
- Book collections are typically in subdirectories
- Use the file browser to navigate into folders
- PDFs in root directory won't appear if subdirectories exist

### "Arrow key produces ^[[A"
- This is normal for some terminal emulators
- Use numeric selection instead (0-9)
- Arrow keys are silently stripped

### "Audio is choppy"
- Check if using fallback `aplay` (less optimized)
- Try with `sounddevice` if available
- Blocksize of 2048 is optimized for 24kHz

### "TTS takes a long time"
- Normal: First chunk is 15-20 seconds generation
- Long chapters take longer to generate
- Rest of chapter generates while you listen
- Internet connection required for Edge-TTS

### "Terminal is corrupted"
- Should not happen in v1.3+
- If it does, try: `reset` or `stty sane`
- Report issue with terminal emulator used

See `docs/TROUBLESHOOTING.md` for more help.

## Development

### Setup Development Environment

```bash
git clone https://github.com/YOUR_USERNAME/seferflow.git
cd seferflow
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install pytest pytest-cov
```

### Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=book_reader
```

### Code Quality

```bash
# Format
black book_reader*.py

# Lint
flake8 book_reader*.py

# Type check (optional)
mypy book_reader*.py
```

## Version History

- **v1.3** (Apr 2025) - Live visualization, fixed settings menu
- **v1.2** (Apr 2025) - Streaming TTS, voice selection, smooth audio
- **v1.1** (Apr 2025) - Directory navigation, arrow key handling
- **v1.0** (Apr 2025) - Initial release

See `CHANGELOG.md` for detailed changes.

## Roadmap

### Current Release (v1.3)
- ✅ Streaming TTS generation
- ✅ Live buffer/progress visualization
- ✅ Multiple voice options
- ✅ Speed adjustment
- ✅ Stable playback

### Planned (v1.4)
- [ ] Pause/resume playback
- [ ] Skip forward/backward
- [ ] Save playback position
- [ ] Chapter bookmarks
- [ ] Local Kokoro-ONNX support (offline)

### Future (v2.0)
- [ ] Web UI (Flask/React)
- [ ] Audio file library management
- [ ] Integration with Whisper (auto-transcription)
- [ ] Sync with e-readers (Kindle)
- [ ] Mobile companion app

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with clear messages
6. Push to your fork
7. Open a pull request

## License

MIT License - see LICENSE file for details.

## Author

Built with ❤️ for book lovers who want to listen while they work.

## Acknowledgments

- **Microsoft Edge TTS** - Neural voice synthesis
- **Poppler** - PDF text extraction
- **NumPy** - Audio processing
- **sounddevice** - Cross-platform audio playback

## Support

### Documentation
- [Features Guide](docs/FEATURES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

### Issues
Report bugs on [GitHub Issues](https://github.com/YOUR_USERNAME/seferflow/issues)

### Contact
- Open an issue on GitHub
- Email: (if applicable)

---

**Ready to listen? Start with**: `./book_reader`
