#!/usr/bin/env python3
"""
SeferFlow - Terminal-based PDF Audiobook Player
Streaming TTS generation with live buffer visualization, persistent settings - no terminal crashes.
"""

import os
import sys
import subprocess
import re
import json
import time
import tempfile
import threading
import queue
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
import numpy as np

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import soundfile as sf
except ImportError:
    print("❌ Error: soundfile not installed")
    sys.exit(1)

try:
    import sounddevice as sd
except ImportError:
    print("⚠ Warning: sounddevice not available, will use aplay")
    sd = None


# ANSI color codes
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
CYAN = '\x1b[36m'
DARK_GRAY = '\x1b[90m'
RESET = '\x1b[0m'


@dataclass
class PlaybackState:
    """Shared state between producer and consumer threads."""
    total_chunks: int = 0
    chunks_generated: int = 0
    chunks_played: int = 0
    queue_max: int = 3
    generating: bool = True
    chunk_durations: list = None  # List of durations for each chunk
    play_start_time: float = 0.0
    play_chunk_duration: float = 0.0
    play_chunk_index: int = 0
    paused: bool = False  # Whether playback is paused
    elapsed_before_pause: float = 0.0  # Accumulated time before last pause

    def __post_init__(self):
        if self.chunk_durations is None:
            self.chunk_durations = []


@dataclass
class PlayerControls:
    """Controls for playback (pause/resume, seek, chapter navigation)."""
    paused: threading.Event = field(default_factory=threading.Event)
    cmd_queue: queue.SimpleQueue = field(default_factory=queue.SimpleQueue)
    # Commands: 'seek_forward', 'seek_backward', 'next_chapter', 'prev_chapter', 'quit'


class ChapterChangeRequest(Exception):
    """Raised when user requests to skip to another chapter."""
    def __init__(self, direction: str):
        self.direction = direction  # 'next_chapter', 'prev_chapter', 'quit'
        super().__init__(f"Chapter change requested: {direction}")


# Settings persistence
CONFIG_PATH = Path.home() / ".config" / "seferflow" / "settings.json"

# Rich console for styled display
if RICH_AVAILABLE:
    _console = Console()
else:
    _console = None


def load_settings() -> Dict[str, any]:
    """Load saved settings from disk or return defaults."""
    defaults = {"voice": "en-US-AriaNeural", "speed": 1.0, "buffer_size": 6}

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                saved = json.load(f)

            # Validate values are in legal range
            if saved.get("speed") in [0.8, 0.9, 1.0, 1.1, 1.2, 1.3]:
                defaults["speed"] = saved["speed"]

            valid_voices = {
                "en-US-AriaNeural",
                "en-US-GuyNeural",
                "en-GB-LibbyNeural",
                "en-GB-RyanNeural",
            }
            if saved.get("voice") in valid_voices:
                defaults["voice"] = saved["voice"]

            valid_buffer_sizes = {3, 6, 10}
            if saved.get("buffer_size") in valid_buffer_sizes:
                defaults["buffer_size"] = saved["buffer_size"]
        except Exception:
            pass  # Silently ignore corrupt config file

    return defaults


def save_settings(speed: float, voice: str, buffer_size: int = 6) -> None:
    """Persist current settings to disk."""
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump({"voice": voice, "speed": speed, "buffer_size": buffer_size}, f, indent=2)
    except Exception:
        pass  # Non-fatal: just don't save


def clear_screen():
    """Clear terminal."""
    os.system('clear' if os.name == 'posix' else 'cls')


def clean_input(prompt: str) -> str:
    """Read input and strip ANSI escape sequences (from arrow keys, etc)."""
    raw = input(prompt)
    # Strip ANSI escape sequences like ^[[A from arrow keys
    return re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', raw).strip()


def browse_books(start_dir: str = "/home/mcstar/Nextcloud/Vault/books") -> Optional[str]:
    """File browser showing both directories and PDF files."""
    current_dir = start_dir

    while True:
        clear_screen()
        print("\n" + "=" * 70)
        print("📚 SELECT A BOOK")
        print("=" * 70)
        print(f"\nDirectory: {current_dir}\n")

        try:
            all_items = sorted(os.listdir(current_dir))
        except PermissionError:
            print("❌ Permission denied")
            return None

        # Separate directories and PDFs
        entries = []
        for item in all_items:
            full_path = os.path.join(current_dir, item)
            if os.path.isdir(full_path) and not item.startswith('.'):
                entries.append((f"[DIR] {item}", full_path, 'dir'))
            elif item.lower().endswith('.pdf'):
                entries.append((item, full_path, 'pdf'))

        if not entries:
            print("No PDF files or directories found.\n")
            print("[b] Go back  [q] Quit")
            choice = clean_input("Choice: ").lower()
            if choice == 'b':
                parent = os.path.dirname(current_dir)
                if parent != current_dir:
                    current_dir = parent
                continue
            return None

        # Show entries
        for i, (display_name, _, _) in enumerate(entries, 1):
            print(f"  {i}. {display_name}")
        print(f"\n  [b] Go back  [q] Quit")

        choice = clean_input("\nEnter number or [b]/[q]: ").lower()

        if choice == 'q':
            return None
        elif choice == 'b':
            parent = os.path.dirname(current_dir)
            if parent != current_dir:
                current_dir = parent
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(entries):
                    _, path, item_type = entries[idx]
                    if item_type == 'dir':
                        current_dir = path
                    else:
                        return path
            except ValueError:
                pass


def get_chapters(pdf_path: str) -> Optional[List[Dict]]:
    """Get chapters from PDF."""
    try:
        result = subprocess.run(
            [sys.executable, '-c',
             f'''import sys; sys.path.insert(0, "/home/mcstar/.openclaw/workspace-dev"); from book_extractor import detect_chapters; chapters, source = detect_chapters("{pdf_path}"); import json; print(json.dumps([(c["num"], c["title"], c["start_page"], c["end_page"]) for c in chapters] if chapters else []))'''],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            chapters_data = json.loads(result.stdout)
            return [{"num": c[0], "title": c[1], "start_page": c[2], "end_page": c[3]}
                    for c in chapters_data]
    except Exception as e:
        print(f"⚠ Error detecting chapters: {e}")
    return None


def select_chapter(chapters: List[Dict]) -> Optional[Dict]:
    """Simple chapter selection."""
    clear_screen()
    print("\n" + "=" * 70)
    print("📖 SELECT CHAPTER")
    print("=" * 70 + "\n")

    for ch in chapters:
        print(f"  {ch['num']}. {ch['title']} (pp. {ch['start_page']}-{ch['end_page']})")

    print(f"\n  [q] Cancel\n")

    choice = clean_input("Enter chapter number or [q]: ").lower()
    if choice == 'q':
        return None

    try:
        ch_num = int(choice)
        for ch in chapters:
            if ch['num'] == ch_num:
                return ch
    except ValueError:
        pass

    print("❌ Invalid choice")
    time.sleep(1)
    return select_chapter(chapters)


def extract_pdf_text(pdf_path: str, start_page: int = 1, end_page: Optional[int] = None) -> str:
    """Extract text from PDF."""
    try:
        args = ['pdftotext', '-f', str(start_page)]
        if end_page:
            args.extend(['-l', str(end_page)])
        args.extend([pdf_path, '-'])

        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return result.stdout
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")


def reconstruct_sentences(text: str) -> str:
    """Reconstruct sentences from PDF text with display-induced line breaks.

    PDF text has lines broken for display (fixed column width), not for sentences.
    This function:
    1. Joins lines that were broken mid-sentence
    2. Preserves paragraph breaks
    3. Returns text with proper sentence structure
    """
    lines = text.split('\n')
    reconstructed = []
    current_sentence = ""

    for line in lines:
        line = line.strip()

        # Skip empty lines but mark paragraph breaks
        if not line:
            if current_sentence:
                reconstructed.append(current_sentence)
                current_sentence = ""
            reconstructed.append("")  # Preserve paragraph break
            continue

        # If current_sentence is empty, start new sentence
        if not current_sentence:
            current_sentence = line
        else:
            # Check if this line continues the previous sentence
            # If previous line didn't end with sentence-ending punctuation,
            # or this line starts with lowercase, it's a continuation

            if (not current_sentence.endswith(('.', '!', '?', ':', ';')) or
                (line and line[0].islower())):
                # This line continues the sentence - join with space
                current_sentence += " " + line
            else:
                # Previous line ended a sentence - save it and start new
                reconstructed.append(current_sentence)
                current_sentence = line

    # Don't forget the last sentence
    if current_sentence:
        reconstructed.append(current_sentence)

    # Join with newlines, preserving paragraph breaks
    return '\n'.join(reconstructed)


def preprocess_text(text: str) -> str:
    """Clean and reconstruct text from PDF.

    1. Reconstruct sentences from display-induced line breaks
    2. Remove hyphenation artifacts
    3. Normalize whitespace
    4. Expand abbreviations
    """
    # First: reconstruct sentences from PDF display breaks
    text = reconstruct_sentences(text)

    # Then: clean up
    text = re.sub(r'-\n', '', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    replacements = {
        r'\bDr\.': 'Doctor',
        r'\bMr\.': 'Mister',
        r'\bMrs\.': 'Missus',
        r'\bRev\.': 'Reverend'
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text.strip()


def split_into_chunks(text: str, max_chars: int = 2000) -> List[str]:
    """Split text into chunks by sentences, staying within max_chars per chunk.

    CRITICAL: Split by sentences (not paragraphs) so edge-tts doesn't insert
    prosody pauses in the middle of chunks. This preserves natural inflection
    without unnatural gaps.
    """
    # Split by sentence boundaries: period, exclamation, question mark
    # Use regex to split while keeping the punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If adding this sentence would exceed max, save current chunk
        if current_chunk and len(current_chunk) + len(sentence) + 1 > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = (current_chunk + " " + sentence).strip() if current_chunk else sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return [c for c in chunks if c]


def generate_speech(text: str, voice: str = "en-US-AriaNeural", speed: float = 1.0) -> Tuple[np.ndarray, int]:
    """Generate speech for a text chunk."""
    try:
        import edge_tts
        import asyncio
        import io

        async def gen():
            comm = edge_tts.Communicate(text, voice, rate=f"{int((speed - 1) * 100):+d}%")
            chunks = []
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            return b''.join(chunks)

        try:
            audio_bytes = asyncio.run(gen())
        except RuntimeError:
            # Fallback for event loop issues
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                audio_bytes = loop.run_until_complete(gen())
            finally:
                loop.close()

        with io.BytesIO(audio_bytes) as f:
            data, sr = sf.read(f, dtype=np.float32)

        return data, sr

    except Exception as e:
        print(f"❌ TTS Error: {e}")
        raise


def trim_silence(samples: np.ndarray, threshold: float = 0.01) -> np.ndarray:
    """Remove silence from start and end of audio.

    Edge-TTS streams small MP3 chunks that each have silence padding at
    the beginning and end. This silence accumulates between concatenated
    chunks, causing noticeable pauses. Trimming it eliminates the gaps.
    """
    if len(samples) == 0:
        return samples

    # Find where audio amplitude exceeds threshold
    mask = np.abs(samples) > threshold

    if not np.any(mask):
        # Entire chunk is silence
        return samples[:0]  # Return empty array

    # Find first and last non-silent sample
    nonzero = np.where(mask)[0]
    start = nonzero[0]
    end = nonzero[-1] + 1

    return samples[start:end]


def remove_silence_gaps(samples: np.ndarray, sr: int,
                       silence_threshold: float = 0.001,
                       min_silence_duration: float = 0.3) -> np.ndarray:
    """Remove long silence gaps from audio (e.g., between edge-tts MP3 chunks).

    Edge-TTS concatenates MP3 streaming chunks which create ~0.8-1.0s gaps of
    complete silence between them. This function detects and removes those gaps.

    Args:
        samples: Audio samples (numpy array)
        sr: Sample rate in Hz
        silence_threshold: Amplitude below this is considered silent (default 0.001 = very quiet)
        min_silence_duration: Minimum duration of silence to remove (seconds)

    Returns:
        Audio with long silence gaps removed
    """
    if len(samples) == 0:
        return samples

    # Detect silence: samples below threshold
    min_silence_samples = int(min_silence_duration * sr)
    is_silent = np.abs(samples) < silence_threshold

    # Find silence regions
    not_silent = ~is_silent
    changes = np.diff(not_silent.astype(int))

    # changes == -1: transition from sound to silence
    # changes == +1: transition from silence to sound
    silence_starts = np.where(changes == -1)[0] + 1
    silence_ends = np.where(changes == 1)[0] + 1

    # Handle silence at the beginning
    if is_silent[0]:
        silence_starts = np.concatenate([[0], silence_starts])

    # Handle silence at the end
    if is_silent[-1]:
        silence_ends = np.concatenate([silence_ends, [len(samples)]])

    # Keep only long silence gaps
    long_silences = []
    for start, end in zip(silence_starts, silence_ends):
        duration = (end - start) / sr
        if duration >= min_silence_duration:
            long_silences.append((start, end))

    # Remove long silence gaps by concatenating non-silent sections
    if not long_silences:
        return samples  # No long silences to remove

    # Build output by keeping everything except long silences
    output = []
    current_pos = 0

    for silence_start, silence_end in long_silences:
        # Keep audio before this silence
        if silence_start > current_pos:
            output.append(samples[current_pos:silence_start])
        current_pos = silence_end

    # Keep audio after last silence
    if current_pos < len(samples):
        output.append(samples[current_pos:])

    if output:
        return np.concatenate(output)
    else:
        return samples


def normalize_audio(samples: np.ndarray) -> np.ndarray:
    """Normalize audio with 0.9 headroom factor."""
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples * (0.9 / peak)
    return samples


def fmt_time(seconds: float) -> str:
    """Format seconds as MM:SS."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


def make_progress_bar(total: int, played: int, buffered: int, width: int = 40) -> str:
    """
    Render progress bar with colors:
    Green █ = played, Yellow ▓ = buffered, Gray ░ = pending
    """
    if total == 0:
        return "0 / 0"

    # Calculate proportional widths
    played_width = max(1, width * played // total)
    buffered_width = max(0, width * buffered // total)
    pending_width = width - played_width - buffered_width

    bar = (GREEN + '█' * played_width +
           YELLOW + '▓' * buffered_width +
           DARK_GRAY + '░' * pending_width +
           RESET)

    percent = 100 * played // total if total > 0 else 0
    return f"{bar}  {percent}%"


def make_buffer_bar(current: int, max_size: int, width: int = 15) -> str:
    """Render buffer fill level."""
    filled = min(current, max_size)
    filled_width = max(1, width * filled // max_size)
    empty_width = width - filled_width

    bar = (GREEN + '▓' * filled_width +
           DARK_GRAY + '░' * empty_width +
           RESET)

    return f"[{bar}]  {filled}/{max_size}"


def _build_display(state: PlaybackState, chapter_name: str, voice_short: str, speed: float,
                   current_offset: int = 0, total_samples: int = 0, sample_rate: int = 0) -> Panel:
    """Build a Rich Panel renderable for the player display.

    Args:
        current_offset: Current playback position in samples (for per-chunk display)
        total_samples: Total samples in current chunk (for per-chunk display)
        sample_rate: Sample rate in Hz (for per-chunk display)
    """
    if not RICH_AVAILABLE:
        # Fallback: just return empty text if Rich not available
        return Text("Playback in progress...")

    # Status indicator
    if state.paused:
        status_text = Text("⏸ PAUSED", style="bold yellow")
    elif state.generating or state.chunks_played < state.total_chunks:
        status_text = Text("▶ PLAYING", style="bold green")
    else:
        status_text = Text("✓ DONE", style="bold green")

    # Chapter and settings line
    chapter_short = chapter_name[:40]
    header_line = f"{chapter_short:<40} {speed:>4.1f}x  {voice_short}"

    # Time information - both overall progress and per-chunk
    if state.paused:
        elapsed = state.elapsed_before_pause
    else:
        elapsed = state.elapsed_before_pause + (time.time() - state.play_start_time) if state.play_start_time > 0 else state.elapsed_before_pause

    total_estimated = sum(state.chunk_durations) if state.chunk_durations else 0
    if state.chunks_played < len(state.chunk_durations):
        remaining = sum(state.chunk_durations[state.chunks_played:])
    else:
        remaining = 0
    total_est = elapsed + remaining

    # Per-chunk progress
    if total_samples > 0 and sample_rate > 0:
        chunk_elapsed = current_offset / sample_rate
        chunk_total = total_samples / sample_rate
        chunk_progress = make_progress_bar(1, int(current_offset), 0)
        chunk_line = f"Chunk:     {chunk_progress}  {fmt_time(chunk_elapsed)} / {fmt_time(chunk_total)}"
    else:
        chunk_line = ""

    time_str = f"{fmt_time(elapsed)} / ~{fmt_time(total_est)}"
    section_str = f"Section {state.chunks_played + 1} of {state.total_chunks}"
    time_line = f"{section_str:<20} {time_str:>15}"

    # Progress bar
    buffered = state.chunks_generated - state.chunks_played
    progress_bar_str = make_progress_bar(state.total_chunks, state.chunks_played, buffered)

    # Buffer meter
    buffer_bar_str = make_buffer_bar(state.chunks_generated - state.chunks_played, state.queue_max)
    gen_status = "↺ generating..." if state.generating else "✓ all generated"
    buffer_line = f"Buffer:    {buffer_bar_str}  {gen_status}"

    # Instructions
    instructions = "[Space] Pause  [←/→] ±5s  [n/p] Chapter  [q] Quit"

    # Build content
    content = Text()
    content.append(header_line + "\n\n", style="dim")
    content.append(time_line + "\n", style="dim")
    if chunk_line:
        content.append(chunk_line + "\n", style="dim")
    content.append(f"Progress:  {progress_bar_str}\n", style="dim")
    content.append(buffer_line + "\n\n", style="dim")
    content.append(instructions, style="dim")

    return Panel(content, title=status_text, expand=False)


def _render_display(state: PlaybackState, chapter_name: str, voice_short: str, speed: float,
                    current_offset: int, total_samples: int, sample_rate: int):
    """Render a multi-line formatted display. Called once per second to minimize terminal I/O."""
    WIDTH = 70

    if state.paused:
        status_icon = "⏸ PAUSED"
        status_emoji = "🟡"
    elif state.chunks_played >= state.total_chunks:
        status_icon = "✅ DONE"
        status_emoji = "🎉"
    else:
        status_icon = "▶️  PLAYING"
        status_emoji = "🔊"

    # Calculate timings
    elapsed = state.elapsed_before_pause + (time.time() - state.play_start_time) if state.play_start_time > 0 else state.elapsed_before_pause
    pct = int(100 * state.chunks_played / max(state.total_chunks, 1))
    buffered = state.chunks_generated - state.chunks_played

    # Estimate total chapter length (fixed, doesn't change as we generate more chunks)
    # Use average chunk duration × total chunks for stable estimate
    if state.chunk_durations and len(state.chunk_durations) > 0:
        avg_chunk_duration = sum(state.chunk_durations) / len(state.chunk_durations)
        total_est = avg_chunk_duration * state.total_chunks
    else:
        total_est = 0

    # Build the display
    lines = []

    # Top border
    lines.append("━" * WIDTH)

    # Status line: emoji, icon and chapter on left, speed/voice on right
    status_section = f"{status_emoji}  {status_icon}   {chapter_name[:35]}"
    voice_section = f"{speed:.1f}x  🎤 {voice_short}"
    padding = WIDTH - len(status_section) - len(voice_section) - 2
    lines.append(status_section + " " * max(padding, 1) + voice_section)

    # Border
    lines.append("━" * WIDTH)
    lines.append("")  # blank

    # Section progress
    section_str = f"📚 Section {state.chunks_played} of {state.total_chunks}"
    time_str = f"⏱️  {fmt_time(elapsed)} / ~{fmt_time(total_est)}"
    lines.append(f"  {section_str:<37} {time_str:>30}")
    lines.append("")  # blank

    # Progress bar (████████░░░░)
    bar_width = WIDTH - 14
    filled = int(bar_width * state.chunks_played / max(state.total_chunks, 1))
    bar = "▓" * filled + "░" * (bar_width - filled)
    lines.append(f"  📊 Progress:  {bar}  {pct:3d}%")
    lines.append("")  # blank

    # Buffer bar
    buf_width = 15
    buf_filled = min(buffered, state.queue_max)
    buf_bar = "▓" * buf_filled + "░" * (state.queue_max - buf_filled)
    gen_status = "⟳ generating..." if state.generating else "✅ ready"
    lines.append(f"  📦 Buffer:    [{buf_bar}]  {buffered}/{state.queue_max}  {gen_status}")
    lines.append("")  # blank

    # Help text with emojis
    lines.append("  ⌨️  Controls:  [Space] ⏯  [← →] Skip ±5s  [n/p] Chapters  [q] Quit")

    # Bottom border
    lines.append("━" * WIDTH)

    # Print all at once with carriage return at top to overwrite
    sys.stdout.write("\033[H\033[2J")  # Clear screen
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    sys.stdout.flush()


def play_audio_with_display(samples: np.ndarray, sample_rate: int, state: PlaybackState,
                            chapter_name: str, voice_short: str, speed: float,
                            controls: PlayerControls):
    """Play audio while displaying live buffer/progress updates with playback controls.

    Implements pause/resume, seek ±5s, and chapter navigation. Uses Rich Live display
    and polling loop for real-time responsiveness to user input.

    With proper sentence reconstruction, GIL contention is minimal, so we can safely
    display updates at low frequency (4 Hz) without audio stuttering.
    """
    samples = normalize_audio(samples)
    sample_offset = 0
    SEEK_FORWARD_SAMPLES = int(5 * sample_rate)  # 5-second seek
    SEEK_BACKWARD_SAMPLES = int(5 * sample_rate)

    def _current_offset() -> int:
        """Calculate current playback position in samples."""
        elapsed = (time.time() - state.play_start_time) if not state.paused else 0
        return sample_offset + int(elapsed * sample_rate)

    def _restart_from(offset: int):
        """Stop playback and restart from a new sample offset."""
        nonlocal sample_offset
        sample_offset = max(0, min(len(samples) - 1, offset))
        sd.stop()
        state.play_start_time = time.time()
        state.paused = False
        if sample_offset < len(samples):
            remaining = samples[sample_offset:]
            if len(remaining) > 0:
                sd.play(remaining, sample_rate, latency='low')

    try:
        if not sd:
            # Fallback to aplay (no playback controls)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_wav = f.name
            sf.write(temp_wav, samples, sample_rate)
            subprocess.run(['aplay', temp_wav], check=True)
            os.unlink(temp_wav)
            return

        # Start playback
        sd.play(samples, sample_rate, latency='low')
        state.play_start_time = time.time()

        def _is_playing() -> bool:
            """Check if sounddevice stream is active without raising on ended streams."""
            try:
                return sd.get_stream().active
            except Exception:
                return False

        def _poll_controls():
            """Process one round of keyboard commands and pause/resume. Returns True to continue, False to stop."""
            nonlocal sample_offset
            try:
                cmd = controls.cmd_queue.get_nowait()
                if cmd == 'seek_forward':
                    _restart_from(_current_offset() + SEEK_FORWARD_SAMPLES)
                elif cmd == 'seek_backward':
                    _restart_from(_current_offset() - SEEK_BACKWARD_SAMPLES)
                elif cmd in ('next_chapter', 'prev_chapter', 'quit'):
                    sd.stop()
                    raise ChapterChangeRequest(cmd)
            except queue.Empty:
                pass

            if controls.paused.is_set() and not state.paused:
                # Pausing: capture the exact current offset before stopping, freeze the timer
                pause_offset = sample_offset + int((time.time() - state.play_start_time) * sample_rate)
                sample_offset = pause_offset  # Save so we can resume from here
                state.elapsed_before_pause += time.time() - state.play_start_time
                state.play_start_time = 0  # Zero this so timer stops during pause
                state.paused = True
                sd.stop()
            elif not controls.paused.is_set() and state.paused:
                # Resuming: sample_offset was saved, reset play_start_time to resume timing
                state.paused = False
                state.play_start_time = time.time()
                current = _current_offset()
                if current < len(samples):
                    sd.play(samples[current:], sample_rate, latency='low')

        # Polling loop — NO Rich/Live here. Use simple print() with ANSI clear,
        # updated once per second to minimize terminal I/O and GIL contention.
        last_display_update = 0.0
        try:
            while _is_playing() or state.paused:
                _poll_controls()

                now = time.time()
                if now - last_display_update >= 1.0:
                    _render_display(state, chapter_name, voice_short, speed,
                                   _current_offset(), len(samples), sample_rate)
                    last_display_update = now

                time.sleep(0.05)
        except ChapterChangeRequest:
            sys.stdout.write('\n')
            sys.stdout.flush()
            raise
        sys.stdout.write('\n')
        sys.stdout.flush()

    except ChapterChangeRequest:
        raise  # Re-raise to be caught by stream_and_play()
    except KeyboardInterrupt:
        try:
            sd.stop()
        except:
            pass
        raise ChapterChangeRequest('quit')


def _keyboard_reader(controls: PlayerControls, stop_event: threading.Event):
    """Background thread that reads keyboard input and posts commands.

    Runs in a separate daemon thread, blocking on readchar.readkey() while waiting
    for user input. Posts commands to controls.cmd_queue or toggles controls.paused.
    """
    try:
        import readchar
    except ImportError:
        print("⚠ Warning: readchar not available, keyboard controls disabled")
        return

    while not stop_event.is_set():
        try:
            key = readchar.readkey()
        except Exception:
            break

        if key == ' ':
            # Toggle pause
            if controls.paused.is_set():
                controls.paused.clear()
            else:
                controls.paused.set()
        elif key == readchar.key.RIGHT or key == 'l':
            controls.cmd_queue.put('seek_forward')
        elif key == readchar.key.LEFT or key == 'h':
            controls.cmd_queue.put('seek_backward')
        elif key in ('n', readchar.key.DOWN):
            controls.cmd_queue.put('next_chapter')
        elif key in ('p', readchar.key.UP):
            controls.cmd_queue.put('prev_chapter')
        elif key in ('q', readchar.key.CTRL_C):
            controls.cmd_queue.put('quit')


def stream_and_play(text: str, voice: str, speed: float, chapter_name: str,
                    controls: PlayerControls, chapters: List[Dict], chapter_idx: int,
                    buffer_size: int = 6) -> str:
    """
    Split chapter into chunks, generate TTS progressively, play as ready.
    Display live buffer/progress visualization during playback.

    Args:
        buffer_size: Audio queue size in chunks (3=conservative, 6=balanced, 10=aggressive)
    """
    chunks = split_into_chunks(text)
    total_chunks = len(chunks)

    # Create shared state
    # queue_max must match the actual audio_queue maxsize for accurate buffer display
    state = PlaybackState(total_chunks=total_chunks, queue_max=buffer_size)

    print(f"\n📚 {chapter_name}")
    print(f"   {total_chunks} sections to generate and play")
    print(f"   Speed: {speed}x  Voice: {voice}  Buffer: {buffer_size} chunks")
    print(f"   Controls: [Space] Pause  [←/→] ±5s  [n/p] Chapter  [q] Quit\n")
    time.sleep(1)

    audio_queue = queue.Queue(maxsize=buffer_size)
    stop_event = threading.Event()
    error_happened = [False]
    chapter_result = 'done'  # Default result

    def producer():
        """Generate TTS for each chunk in background.

        CRITICAL: Producer MUST ALWAYS be generating to keep queue full.
        Do NOT throttle or wait for queue to drain. Edge-TTS is slow (4-6s/chunk),
        and playback can consume 2 chunks in parallel. Queue MUST stay ahead.
        """
        for i, chunk in enumerate(chunks):
            if stop_event.is_set():
                break

            try:
                # Generate immediately - do NOT wait for queue to drain!
                # The queue.put() will block if maxsize is reached, which is fine.
                samples, sr = generate_speech(chunk, voice, speed)

                # Trim silence from chunk edges (not the same as removing gaps)
                samples = trim_silence(samples)
                duration = len(samples) / sr
                state.chunk_durations.append(duration)

                # Block if queue is full - this naturally throttles to playback speed
                audio_queue.put((samples, sr))  # Blocking put
                state.chunks_generated += 1
            except Exception as e:
                print(f"\n❌ TTS generation failed for chunk {i+1}: {e}")
                error_happened[0] = True
                stop_event.set()
                break
        state.generating = False
        audio_queue.put(None)  # Sentinel

    producer_thread = threading.Thread(target=producer, daemon=True)
    producer_thread.start()

    # Start keyboard reader thread
    keyboard_stop = threading.Event()
    keyboard_thread = threading.Thread(target=_keyboard_reader, args=(controls, keyboard_stop), daemon=True)
    keyboard_thread.start()

    # Pre-buffer minimum chunks before starting playback
    print("🔄 Pre-buffering audio chunks...")
    pre_buffer_start = time.time()
    # Wait for 2-3 chunks (~10-15 seconds at 5s per chunk)
    while audio_queue.qsize() < 2 and not stop_event.is_set() and not error_happened[0]:
        time.sleep(0.1)
    pre_buffer_time = time.time() - pre_buffer_start
    print(f"✓ Pre-buffering complete ({audio_queue.qsize()} chunks), starting playback...\n")

    # Main thread plays chunks as they become available
    # CRITICAL CHANGE: Play single chunks, not concatenated pairs
    # This matches generation speed (1 chunk per 5s) with playback consumption
    # (1 chunk per 10-20s depending on text length)

    try:
        while True:
            item = audio_queue.get()  # Blocks until chunk is ready
            if item is None:
                # All chunks generated and consumed
                break

            samples, sr = item
            state.chunks_played += 1

            try:
                # Play this single chunk directly (no concatenation)
                play_audio_with_display(samples, sr, state,
                                       chapter_name, voice.split('-')[1][:4], speed,
                                       controls)
            except ChapterChangeRequest as e:
                chapter_result = e.direction
                break

            if stop_event.is_set():
                break

        if not error_happened[0] and chapter_result == 'done':
            print("\n✓ Playback complete\n")

    except KeyboardInterrupt:
        stop_event.set()
        chapter_result = 'quit'
        print("\n✓ Stopped by user")
    finally:
        # Stop all threads
        stop_event.set()
        keyboard_stop.set()
        try:
            if sd:
                sd.stop()
        except:
            pass
        keyboard_thread.join(timeout=0.5)
        producer_thread.join(timeout=0.5)

    return chapter_result


def settings_menu(default_speed: float = 1.0, default_voice: str = "en-US-AriaNeural",
                  default_buffer: int = 6) -> Tuple[Optional[float], Optional[str], Optional[int]]:
    """Show pre-generation settings menu with direct selection."""
    speeds = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
    voices = [
        ("a", "en-US-AriaNeural", "Female (US, default)"),
        ("b", "en-US-GuyNeural", "Male (US)"),
        ("c", "en-GB-LibbyNeural", "Female (British)"),
        ("d", "en-GB-RyanNeural", "Male (British)"),
    ]
    buffers = [
        ("x", 3, "Conservative (less memory, responsive)"),
        ("y", 6, "Balanced (default)"),
        ("z", 10, "Aggressive (smooth, more memory)"),
    ]

    current_speed = default_speed
    current_voice = default_voice
    current_buffer = default_buffer

    while True:
        clear_screen()
        print("\n" + "=" * 70)
        print("⚙️  PLAYBACK SETTINGS")
        print("=" * 70 + "\n")

        print(f"Speed: {current_speed}x")
        for i, spd in enumerate(speeds, 1):
            marker = " ← current" if spd == current_speed else ""
            print(f"  [{i}] {spd}x{marker}")
        print()

        print(f"Voice: {current_voice}")
        for code, voice_id, desc in voices:
            marker = " ← current" if voice_id == current_voice else ""
            print(f"  [{code}] {desc}{marker}")
        print()

        print(f"Buffer Size: {current_buffer} chunks")
        for code, size, desc in buffers:
            marker = " ← current" if size == current_buffer else ""
            print(f"  [{code}] {size:>2} chunks  {desc}{marker}")
        print()

        print("[Enter] Start reading  [q] Cancel\n")

        choice = clean_input("Enter speed [1-6], voice [a-d], buffer [x-z], or [Enter]/[q]: ").lower()

        if choice == 'q':
            return None, None, None
        elif choice == '':
            # Start reading with current settings
            return current_speed, current_voice, current_buffer
        elif choice in ('1', '2', '3', '4', '5', '6'):
            # Direct speed selection
            idx = int(choice) - 1
            current_speed = speeds[idx]
        elif choice in ('a', 'b', 'c', 'd'):
            # Direct voice selection
            for code, voice_id, _ in voices:
                if choice == code:
                    current_voice = voice_id
                    break
        elif choice in ('x', 'y', 'z'):
            # Direct buffer selection
            for code, size, _ in buffers:
                if choice == code:
                    current_buffer = size
                    break
        # Otherwise loop back


def main():
    """Main program flow."""
    print("\n" + "=" * 70)
    print("📚 BOOK READER - Starting up...".center(70))
    print("=" * 70)
    time.sleep(1)

    try:
        # Step 1: Browse and select book
        pdf_path = browse_books()
        if not pdf_path:
            print("\nCancelled.")
            return 0

        book_name = os.path.basename(pdf_path)
        print(f"\n📖 Selected: {book_name}")

        # Step 2: Detect chapters
        print("🔍 Detecting chapters...")
        chapters = get_chapters(pdf_path)

        if not chapters:
            print("⚠ No chapters detected, will read entire book")
            chapters = [{
                'num': 1,
                'title': 'Full Book',
                'start_page': 1,
                'end_page': None
            }]

        # Step 3: Select chapter
        chapter = select_chapter(chapters)
        if not chapter:
            print("Cancelled.")
            return 0

        # Get chapter index
        chapter_idx = next((i for i, ch in enumerate(chapters) if ch['num'] == chapter['num']), 0)

        # Step 6: Settings menu (voice, speed, and buffer) - load saved defaults
        saved_settings = load_settings()
        speed, voice, buffer_size = settings_menu(default_speed=saved_settings["speed"],
                                                   default_voice=saved_settings["voice"],
                                                   default_buffer=saved_settings["buffer_size"])
        if speed is None:
            print("Cancelled.")
            return 0

        # Save settings for next time
        save_settings(speed, voice, buffer_size)

        # Create player controls (shared across chapter changes)
        controls = PlayerControls()

        # Step 7: Playback loop with chapter navigation
        while True:
            chapter = chapters[chapter_idx]

            # Step 4: Extract text
            print(f"\n📄 Extracting text from {chapter['title']}...")
            text = extract_pdf_text(pdf_path, chapter['start_page'], chapter['end_page'])

            word_count = len(text.split())
            print(f"✓ Extracted {word_count} words (~{word_count / 130:.0f} minutes)")

            # Step 5: Preprocess
            print("🧹 Preprocessing...")
            text = preprocess_text(text)

            if not text:
                print("❌ No text to process")
                return 1

            # Stream and play with visualization
            try:
                result = stream_and_play(text, voice, speed, chapter['title'],
                                        controls, chapters, chapter_idx, buffer_size)
            except Exception as e:
                print(f"❌ Playback failed: {e}")
                return 1

            # Handle chapter navigation
            if result == 'next_chapter' and chapter_idx < len(chapters) - 1:
                chapter_idx += 1
                continue
            elif result == 'prev_chapter' and chapter_idx > 0:
                chapter_idx -= 1
                continue
            else:
                # 'done', 'quit', or boundary reached
                break

        return 0

    except KeyboardInterrupt:
        print("\n\n✓ Cancelled by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
