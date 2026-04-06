# Changelog

All notable changes to the SeferFlow project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-04-06

### Added
- **Settings Persistence** - Voice and speed preferences saved automatically
  - Settings stored in `~/.config/seferflow/settings.json`
  - Automatically loaded on startup as defaults
  - Saved when user confirms settings before playback
  - Seamless experience with no extra UI elements
- **Project Rename to SeferFlow** - "Sefer" (ספר) means "book" in Hebrew
  - New executable: `seferflow`
  - Interactive mode: `seferflow.py`
  - Batch mode: `seferflow_batch.py`
  - Verification script: `verify.sh`
  - All documentation updated
- **Web API (v1.0.0)** - Full REST API with Swagger UI
  - Authentication (JWT tokens)
  - TTS generation with WebSocket streaming
  - Playback control endpoints (pause/resume/seek)
  - MCP interruption support
  - Rate limiting & health monitoring
  - Docker containerization with Redis/PostgreSQL

### Changed
- API documentation moved to `/home/mcstar/projects/seferflow/docs/seferflow-api-reference.md`

### Changed
- `settings_menu()` now accepts `default_speed` and `default_voice` parameters
- Added `load_settings()` function to read persisted config
- Added `save_settings()` function to write config to disk
- Config directory created automatically if missing
- Graceful handling of missing or corrupt config files

### Technical Details
- Settings stored as JSON for human readability
- Validation of loaded values ensures consistency
- Non-fatal errors (missing/corrupt files) silently use defaults
- No impact on batch mode (which uses CLI args)

---

## [1.3.0] - 2025-04-05

### Added
- **Live Buffer Visualization** during playback
  - Real-time progress bar with color-coded sections
  - Buffer fill level meter showing queue status
  - Time display (elapsed / estimated total)
  - Generation status indicator (generating / complete)
  - Updates every 400ms without blocking audio
- **Direct Settings Selection** - No more sub-menus
  - Press `[1-6]` to change speed directly
  - Press `[a-d]` to change voice directly
  - Cleaner, more intuitive settings menu
- **PlaybackState dataclass** for thread-safe state sharing
- **ANSI color support** for progress visualization
  - Green for played sections
  - Yellow for buffered sections
  - Gray for pending sections
- Display-only ANSI codes (no raw terminal mode)

### Changed
- Refactored `stream_and_play()` to use non-blocking display updates
- Replaced `sd.wait()` blocking call with 400ms polling loop
- Settings menu now shows all options directly (no nested menus)
- Display updates use cursor movement (`\x1b[NA`) for in-place rendering

### Fixed
- Settings menu bug: pressing voice letter directly now works
- Display updates no longer block audio playback
- Terminal stability: using display-only ANSI codes instead of raw mode

### Technical Notes
- Producer thread now tracks chunk durations
- Consumer thread polls display every 400ms
- Queue operations thread-safe for visualization
- Time estimation based on actual chunk durations

---

## [1.2.0] - 2025-04-05

### Added
- **Streaming TTS Generation** - Split chapters into chunks
  - Text split into ~2000-character sections at paragraph boundaries
  - First audio chunk plays ~15-20 seconds after selection
  - Rest of chapter generates in background while listening
  - Queue-based producer/consumer pattern with maxsize=3
- **Voice Selection Menu** - 4 professional neural voices
  - en-US-AriaNeural (Female, US - default)
  - en-US-GuyNeural (Male, US)
  - en-GB-LibbyNeural (Female, British)
  - en-GB-RyanNeural (Male, British)
- **Speed Adjustment** - 6 playback speed options
  - 0.8x (slower - easier to follow)
  - 0.9x, 1.0x (normal), 1.1x, 1.2x, 1.3x (faster - saves time)
- **Audio Buffer Optimization**
  - 2-chunk concatenation before playback (eliminates gaps)
  - Explicit `blocksize=2048` for 24kHz audio
  - Peak normalization with 0.9 headroom factor

### Changed
- Complete rewrite of `stream_and_play()` function
- Added `split_into_chunks()` for paragraph-aware text splitting
- Replaced single-generation TTS with streaming producer thread
- Audio playback now uses smooth 2-chunk buffering

### Fixed
- **Issue**: Long generation wait (1-2 minutes) before audio starts
  - **Solution**: Streaming chunks, first plays ~15-20 seconds
- **Issue**: Choppy audio at chunk transitions
  - **Solution**: 2-chunk overlap + optimized blocksize
- **Issue**: No voice/speed controls in interactive mode
  - **Solution**: Settings menu with 4 voices × 6 speeds
- **Issue**: File browser crash with no PDFs in root
  - **Solution**: Directory navigation shows subdirs alongside PDFs
- **Issue**: Arrow keys producing "^[[A" gibberish
  - **Solution**: `clean_input()` strips ANSI escape sequences

### Technical Details
- Producer thread generates TTS in background
- Consumer thread buffers 2 chunks for smooth playback
- Queue-based communication with bounded memory
- Thread-safe chunk duration tracking

---

## [1.1.0] - 2025-04-05

### Added
- Directory navigation in file browser
  - Shows both directories `[DIR]` and PDF files
  - Users can navigate into subdirectories
  - `[b]` to go back up directory tree
- `clean_input()` function for ANSI escape sequence stripping
  - Arrow keys no longer produce "^[[A" gibberish
  - All numeric input works cleanly

### Changed
- Enhanced `browse_books()` to handle directories
- All menu input now uses `clean_input()` for sanitization
- Settings menu now accessible from file browser
- Better error handling for permission denied

### Fixed
- **Issue**: File browser crash (no PDFs found)
  - **Solution**: Now browses both files and directories
- **Issue**: Arrow key gibberish in menus
  - **Solution**: ANSI sequence stripping
- **Issue**: No settings menu pre-playback
  - **Solution**: Added settings_menu() with voice/speed options
- **Issue**: Settings menu with nested sub-menus
  - **Solution**: Collapsed to single-screen (improved in v1.3)

### Known Issues
- Settings menu requires `[v]` then selection (fixed in v1.3)

---

## [1.0.0] - 2025-04-05

### Added
- Initial production release
- Interactive mode with file browser
- Batch mode for automation
- PDF chapter detection from bookmarks
- Text extraction with pdftotext
- Text preprocessing (line breaks, abbreviations, etc.)
- TTS generation with Edge-TTS
- Audio playback via sounddevice
- Fallback audio playback via aplay
- Multiple TTS engine support (Kokoro, Edge-TTS, espeak)
- Error handling and graceful fallback

### Features
- ✅ PDF chapter detection
- ✅ Interactive chapter selection
- ✅ Text extraction and cleaning
- ✅ Neural voice TTS (Microsoft Edge)
- ✅ Audio playback with normalization
- ✅ Batch mode for scripting
- ✅ Multiple TTS engine fallback
- ✅ Stable terminal operation (no crashes)

### Technical
- Python 3.8+ support
- Thread-safe audio playback
- Queue-based chunk management
- Asyncio for TTS generation
- NumPy for audio processing
- Cross-platform support

### Known Issues (Fixed in later versions)
- Long generation wait before playback starts
- No visualization of progress/buffer
- Arrow keys produce gibberish
- Settings menu is confusing
- Audio choppiness between chunks
- Limited directory navigation

---

## Version Numbering

- **Major (X.0.0)**: Breaking changes, major features
- **Minor (0.X.0)**: New features, non-breaking
- **Patch (0.0.X)**: Bug fixes, minor improvements

---

## Unreleased / Planned

### v1.4.0 (Coming Soon)
- [ ] Pause/resume during playback
- [ ] Skip forward/backward controls
- [ ] Save playback position
- [ ] Chapter bookmarks
- [ ] Kokoro-ONNX offline support

### v2.0.0 (Future)
- [ ] Web UI
- [ ] Library management
- [ ] Whisper transcription
- [ ] E-reader sync
- [ ] Mobile app

---

## Migration Guide

### From v1.0 to v1.2
- Settings menu now available in interactive mode
- File browser supports directory navigation
- First audio plays much faster (15-20s vs 1-2min)
- Audio quality improved (smooth playback)

### From v1.2 to v1.3
- Settings menu now uses direct selection (no sub-menus)
- New live visualization during playback
- Display updates every 400ms (new experience)

No breaking API changes. All existing scripts and batch commands still work.

---

**Latest Version**: 1.3.0  
**Release Date**: 2025-04-05  
**Status**: Production Ready
