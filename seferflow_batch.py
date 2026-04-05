#!/usr/bin/env python3
"""
Natural-Voice PDF/Text Book Reader
Reads books aloud using neural TTS with streaming playback.

Supports multiple TTS engines with automatic fallback:
  1. Kokoro-ONNX (local, high quality, ~300MB)
  2. Edge-TTS (cloud, excellent quality, free)
  3. pyttsx3 + espeak-ng (fallback, offline)

Usage:
  book_reader book.pdf                          # Interactive chapter selection
  book_reader book.pdf --chapter 3              # Read chapter by number
  book_reader book.pdf --chapter "Introduction" # Read chapter by name
  book_reader book.pdf --pages 10-20            # Read page range
  book_reader book.pdf --chapter 3 --save out.wav
  book_reader --list-voices
"""

import os
import sys
import argparse
import subprocess
import re
import tempfile
import threading
import time
import queue
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

import numpy as np

# Text processing
try:
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    from nltk.tokenize import sent_tokenize
except ImportError:
    # Fallback: simple regex sentence splitting
    def sent_tokenize(text):
        return re.split(r'(?<=[.!?])\s+', text)

# Audio playback
try:
    import sounddevice as sd
    import soundfile as sf
    HAVE_SOUNDDEVICE = True
except ImportError:
    HAVE_SOUNDDEVICE = False

# TTS Engines
try:
    from kokoro_onnx import Kokoro
    HAVE_KOKORO = True
except ImportError:
    HAVE_KOKORO = False

try:
    import edge_tts
    import asyncio
    HAVE_EDGE_TTS = True
except ImportError:
    HAVE_EDGE_TTS = False

try:
    import pyttsx3
    HAVE_PYTTSX3 = True
except ImportError:
    HAVE_PYTTSX3 = False


@dataclass
class TTSVoice:
    """Voice configuration for TTS engines."""
    engine: str           # 'kokoro', 'edge', 'espeak'
    name: str             # Voice identifier
    display_name: str     # Human-readable name
    language: str         # 'en-US', 'en-GB', etc.
    quality: int          # 1-5 stars


class TTSBackend:
    """Abstract TTS backend interface."""
    def generate(self, text: str, voice: str, speed: float = 1.0) -> Tuple[np.ndarray, int]:
        """Generate audio from text. Returns (samples, sample_rate)."""
        raise NotImplementedError

    def list_voices(self) -> List[TTSVoice]:
        """List available voices."""
        raise NotImplementedError


class KokoroBackend(TTSBackend):
    """Kokoro local neural TTS backend."""
    def __init__(self):
        if not HAVE_KOKORO:
            raise ImportError("kokoro-onnx not installed. Run: pip install kokoro-onnx")
        try:
            # Try to load with default paths
            self.model = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
        except FileNotFoundError as e:
            raise RuntimeError(
                f"Kokoro model files not found. Download them with:\n"
                f"  wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx\n"
                f"  wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin\n"
                f"Then place them in the current directory."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Kokoro model: {e}")
        self.sample_rate = 24000

    def generate(self, text: str, voice: str = "af_heart", speed: float = 1.0) -> Tuple[np.ndarray, int]:
        """Generate audio using Kokoro."""
        try:
            samples, sr = self.model.create(text, voice=voice, speed=speed, lang="en-us")
            return np.array(samples, dtype=np.float32), sr
        except Exception as e:
            raise RuntimeError(f"Kokoro generation failed: {e}")

    def list_voices(self) -> List[TTSVoice]:
        """Return available Kokoro voices."""
        voices = [
            TTSVoice("kokoro", "af_heart", "Female (Heart)", "en-US", 5),
            TTSVoice("kokoro", "af_bella", "Female (Bella)", "en-US", 5),
            TTSVoice("kokoro", "af_sarah", "Female (Sarah)", "en-US", 5),
            TTSVoice("kokoro", "af_nicole", "Female (Nicole)", "en-US", 5),
            TTSVoice("kokoro", "am_adam", "Male (Adam)", "en-US", 5),
            TTSVoice("kokoro", "am_michael", "Male (Michael)", "en-US", 5),
            TTSVoice("kokoro", "bm_george", "Male British (George)", "en-GB", 5),
            TTSVoice("kokoro", "bf_emma", "Female British (Emma)", "en-GB", 5),
        ]
        return voices


class EdgeTTSBackend(TTSBackend):
    """Microsoft Edge TTS backend (cloud)."""
    def __init__(self):
        if not HAVE_EDGE_TTS:
            raise ImportError("edge-tts not installed. Run: pip install edge-tts")

    def generate(self, text: str, voice: str = "en-US-AriaNeural", speed: float = 1.0) -> Tuple[np.ndarray, int]:
        """Generate audio using Edge TTS (requires internet)."""
        try:
            import io

            async def generate_audio():
                communicate = edge_tts.Communicate(text, voice, rate=f"{int((speed - 1) * 100):+d}%")
                # Collect all audio chunks
                audio_chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_chunks.append(chunk["data"])
                return b''.join(audio_chunks)

            # Use asyncio.run() for clean event loop handling
            audio_bytes = asyncio.run(generate_audio())

            # Edge-tts outputs WAV; parse it
            with io.BytesIO(audio_bytes) as f:
                data, sr = sf.read(f, dtype=np.float32)
            return data, sr

        except Exception as e:
            raise RuntimeError(f"Edge TTS generation failed: {e}")

    def list_voices(self) -> List[TTSVoice]:
        """Return available Edge TTS voices."""
        voices = [
            TTSVoice("edge", "en-US-AriaNeural", "Aria (Neutral)", "en-US", 5),
            TTSVoice("edge", "en-US-GuyNeural", "Guy (Male)", "en-US", 5),
            TTSVoice("edge", "en-US-JennyNeural", "Jenny (Female)", "en-US", 5),
            TTSVoice("edge", "en-GB-LibbyNeural", "Libby (British Female)", "en-GB", 5),
            TTSVoice("edge", "en-GB-RyanNeural", "Ryan (British Male)", "en-GB", 5),
        ]
        return voices


class EspeakBackend(TTSBackend):
    """System espeak-ng fallback backend."""
    def __init__(self):
        if not HAVE_PYTTSX3:
            raise ImportError("pyttsx3 not installed. Run: pip install pyttsx3 && sudo apt-get install espeak-ng")
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.sample_rate = 22050

    def generate(self, text: str, voice: str = "default", speed: float = 1.0) -> Tuple[np.ndarray, int]:
        """Generate audio using espeak-ng via pyttsx3."""
        try:
            # Save to temp WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_file = f.name

            # Set pyttsx3 properties
            self.engine.setProperty('rate', int(150 * speed))
            self.engine.save_to_file(text, temp_file)
            self.engine.runAndWait()

            # Read back the generated audio
            import soundfile as sf
            data, sr = sf.read(temp_file, dtype=np.float32)
            os.unlink(temp_file)

            return data, sr

        except Exception as e:
            raise RuntimeError(f"espeak generation failed: {e}")

    def list_voices(self) -> List[TTSVoice]:
        """Return available espeak voices."""
        voices = [
            TTSVoice("espeak", "default", "Default (espeak-ng)", "en-US", 2),
        ]
        return voices


def get_tts_backend(engine: Optional[str] = None) -> Tuple[TTSBackend, str]:
    """
    Get available TTS backend with automatic fallback.

    Returns: (backend, engine_name)
    """
    backends = []

    if engine is None or engine == "kokoro":
        if HAVE_KOKORO:
            try:
                return KokoroBackend(), "kokoro"
            except Exception as e:
                print(f"⚠ Kokoro not available: {e}")
                if engine == "kokoro":
                    return None, None

    if engine is None or engine == "edge":
        if HAVE_EDGE_TTS:
            try:
                return EdgeTTSBackend(), "edge"
            except Exception as e:
                print(f"⚠ Edge TTS not available: {e}")
                if engine == "edge":
                    return None, None

    if engine is None or engine == "espeak":
        if HAVE_PYTTSX3:
            try:
                return EspeakBackend(), "espeak"
            except Exception as e:
                print(f"⚠ espeak-ng not available: {e}")
                if engine == "espeak":
                    return None, None

    if engine:
        print(f"❌ Error: TTS engine '{engine}' not available or not installed")
        print("\nInstall with: bash /home/mcstar/.openclaw/workspace-dev/setup_book_reader.sh")
        return None, None

    print("❌ Error: No TTS backends available")
    print("\nInstall with: bash /home/mcstar/.openclaw/workspace-dev/setup_book_reader.sh")
    return None, None


def preprocess_text(text: str) -> str:
    """
    Clean and normalize text for TTS.
    - Fix line breaks and hyphenation
    - Normalize abbreviations
    - Remove extra whitespace
    """
    # Fix hyphenated line breaks
    text = re.sub(r'-\n', '', text)

    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)

    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Common abbreviation expansions
    replacements = {
        r'\bDr\.': 'Doctor',
        r'\bMr\.': 'Mister',
        r'\bMrs\.': 'Missus',
        r'\bRev\.': 'Reverend',
        r'\bProf\.': 'Professor',
        r'\betc\.': 'et cetera',
        r'\bi\.e\.': 'that is',
        r'\be\.g\.': 'for example',
        r'\bp\.\s*m\.': 'PM',
        r'\ba\.\s*m\.': 'AM',
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text.strip()


def extract_pdf_text(pdf_path: str, start_page: int = 1, end_page: Optional[int] = None) -> str:
    """Extract text from PDF using pdftotext."""
    try:
        args = ['pdftotext', '-f', str(start_page)]
        if end_page:
            args.extend(['-l', str(end_page)])
        args.extend([pdf_path, '-'])

        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"pdftotext failed: {result.stderr}")
        return result.stdout
    except FileNotFoundError:
        raise RuntimeError("pdftotext not found. Install: sudo apt-get install poppler-utils")
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")


def play_audio(samples: np.ndarray, sample_rate: int, show_progress: bool = True) -> None:
    """Play audio samples, optionally with progress."""
    if HAVE_SOUNDDEVICE:
        try:
            # Normalize audio if needed
            if np.max(np.abs(samples)) > 1.0:
                samples = samples / np.max(np.abs(samples))

            if show_progress:
                print(f"\n🔊 Playing ({len(samples) / sample_rate:.1f}s of audio)...")
            sd.play(samples, sample_rate)
            sd.wait()
            return
        except Exception as e:
            print(f"⚠ sounddevice playback failed: {e}")

    # Fallback: save to temp WAV and use aplay
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_wav = f.name

        sf.write(temp_wav, samples, sample_rate)

        if show_progress:
            print(f"\n🔊 Playing via aplay ({len(samples) / sample_rate:.1f}s)...")

        subprocess.run(['aplay', temp_wav], check=True)
        os.unlink(temp_wav)
    except Exception as e:
        print(f"❌ Audio playback failed: {e}")


def save_audio(samples: np.ndarray, sample_rate: int, output_path: str) -> None:
    """Save audio to file."""
    try:
        sf.write(output_path, samples, sample_rate)
        file_size = os.path.getsize(output_path)
        print(f"✓ Saved to: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
    except Exception as e:
        print(f"❌ Failed to save audio: {e}")


def list_available_voices() -> None:
    """List all available TTS voices."""
    print("=" * 75)
    print("Available TTS Voices")
    print("=" * 75)

    backends_to_try = [
        ("kokoro", KokoroBackend),
        ("edge", EdgeTTSBackend),
        ("espeak", EspeakBackend),
    ]

    for backend_name, backend_class in backends_to_try:
        try:
            backend = backend_class()
            voices = backend.list_voices()
            print(f"\n📢 {backend_name.upper()} - {backend.__class__.__name__}")
            print("-" * 75)
            for voice in voices:
                stars = "⭐" * voice.quality
                print(f"  {voice.name:20} {voice.display_name:30} {stars}")
        except Exception as e:
            print(f"\n⚠ {backend_name.upper()} unavailable: {e}")

    print("\n" + "=" * 75)
    print("Usage:")
    print("  book_reader book.pdf --voice af_heart         # Kokoro voice")
    print("  book_reader book.pdf --voice en-US-GuyNeural  # Edge voice")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(
        description='Natural-Voice PDF/Text Book Reader',
        epilog='Examples:\n'
               '  %(prog)s book.pdf\n'
               '  %(prog)s book.pdf --chapter 3\n'
               '  %(prog)s book.pdf --chapter 3 --save chapter3.wav\n'
               '  %(prog)s notes.txt --voice af_heart\n'
               '  %(prog)s --list-voices',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('input_file', nargs='?',
                       help='PDF or text file to read')
    parser.add_argument('--chapter', type=str,
                       help='Chapter number or name to read')
    parser.add_argument('--pages', type=str,
                       help='Page range: "1-20" or "all"')
    parser.add_argument('--voice', default='af_heart',
                       help='Voice name (default: af_heart for Kokoro)')
    parser.add_argument('--speed', type=float, default=1.0,
                       help='Reading speed (0.5-2.0, default: 1.0)')
    parser.add_argument('--engine', choices=['kokoro', 'edge', 'espeak'],
                       help='Force specific TTS engine')
    parser.add_argument('--save', type=str,
                       help='Save to audio file instead of playing')
    parser.add_argument('--list-voices', action='store_true',
                       help='List available voices')

    args = parser.parse_args()

    # Handle list-voices
    if args.list_voices:
        list_available_voices()
        return 0

    # Validate input
    if not args.input_file:
        parser.print_help()
        return 1

    if not os.path.exists(args.input_file):
        print(f"❌ File not found: {args.input_file}")
        return 1

    # Get TTS backend
    print(f"🎤 Initializing TTS engine...")
    backend, engine_name = get_tts_backend(args.engine)
    if not backend:
        return 1

    print(f"✓ Using {engine_name} TTS engine")

    # Extract text
    print(f"📖 Reading file...")
    try:
        if args.input_file.lower().endswith('.pdf'):
            # PDF file
            start_page = 1
            end_page = None

            if args.chapter:
                # Try to extract chapter using book_extractor
                import json
                try:
                    result = subprocess.run(
                        ['python3', '-c',
                         f'''import sys; sys.path.insert(0, "/home/mcstar/.openclaw/workspace-dev"); from book_extractor import detect_chapters; chapters, source = detect_chapters("{args.input_file}"); import json; print(json.dumps([(c["num"], c["title"], c["start_page"], c["end_page"]) for c in chapters] if chapters else []))'''],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        chapters_data = json.loads(result.stdout)
                        # Find matching chapter
                        chapter_query = args.chapter.lower()
                        matching = None
                        try:
                            ch_num = int(args.chapter)
                            matching = next((c for c in chapters_data if c[0] == ch_num), None)
                        except ValueError:
                            matching = next((c for c in chapters_data if chapter_query in c[1].lower()), None)

                        if matching:
                            start_page = matching[2]
                            end_page = matching[3]
                            print(f"✓ Found chapter: {matching[1]} (pp. {start_page}-{end_page})")
                        else:
                            print(f"⚠ Chapter '{args.chapter}' not found, using default")
                except Exception:
                    print(f"⚠ Could not auto-detect chapters, reading entire PDF")

            elif args.pages:
                if args.pages.lower() == 'all':
                    # Read all pages - let pdftotext infer
                    pass
                else:
                    parts = args.pages.split('-')
                    start_page = int(parts[0])
                    end_page = int(parts[1]) if len(parts) > 1 else start_page

            text = extract_pdf_text(args.input_file, start_page, end_page)
        else:
            # Text file
            with open(args.input_file, 'r', encoding='utf-8') as f:
                text = f.read()

    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return 1

    # Preprocess text
    print(f"🧹 Preprocessing text...")
    text = preprocess_text(text)

    # Show statistics
    word_count = len(text.split())
    est_minutes = word_count / 130  # Average speech rate
    print(f"✓ {word_count} words (~{est_minutes:.0f} minutes of speech)")

    # Auto-select appropriate voice if user didn't specify and default won't work
    voice_to_use = args.voice

    # If using default voice but it's not compatible with the engine, pick a good default
    if args.voice == 'af_heart' and engine_name != 'kokoro':
        # User didn't override voice, but Kokoro isn't available
        if engine_name == 'edge':
            voice_to_use = 'en-US-AriaNeural'  # Good default for Edge-TTS
            print(f"ℹ Auto-selected voice: {voice_to_use} (for {engine_name})")
        elif engine_name == 'espeak':
            voice_to_use = 'default'
            print(f"ℹ Using system fallback voice")

    # Generate audio
    print(f"🎙️  Generating speech...")
    try:
        samples, sample_rate = backend.generate(text, voice=voice_to_use, speed=args.speed)
        print(f"✓ Generated {len(samples) / sample_rate:.1f}s of audio")
    except Exception as e:
        print(f"❌ TTS generation failed: {e}")
        return 1

    # Save or play
    if args.save:
        save_audio(samples, sample_rate, args.save)
    else:
        play_audio(samples, sample_rate)

    return 0


if __name__ == "__main__":
    sys.exit(main())
