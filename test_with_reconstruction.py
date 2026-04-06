#!/usr/bin/env python3
"""
Test audio generation with the reconstructed sentence pipeline.
Generates and saves audio to /tmp/test_with_reconstruction.wav
"""

import sys
import subprocess
import re
sys.path.insert(0, '/home/mcstar/projects/seferflow')

# Import just what we need (avoiding sounddevice dependency issues)
import numpy as np

try:
    import soundfile as sf
except ImportError:
    print("❌ Error: soundfile not installed")
    print("   Install with: pip install soundfile")
    sys.exit(1)

try:
    import edge_tts
except ImportError:
    print("❌ Error: edge-tts not installed")
    print("   Install with: pip install edge-tts")
    sys.exit(1)

import asyncio


def reconstruct_sentences(text: str) -> str:
    """Reconstruct sentences from PDF text with display-induced line breaks."""
    lines = text.split('\n')
    reconstructed = []
    current_sentence = ""

    for line in lines:
        line = line.strip()

        if not line:
            if current_sentence:
                reconstructed.append(current_sentence)
                current_sentence = ""
            reconstructed.append("")
            continue

        if not current_sentence:
            current_sentence = line
        else:
            if (not current_sentence.endswith(('.', '!', '?', ':', ';')) or
                (line and line[0].islower())):
                current_sentence += " " + line
            else:
                reconstructed.append(current_sentence)
                current_sentence = line

    if current_sentence:
        reconstructed.append(current_sentence)

    return '\n'.join(reconstructed)


def preprocess_text(text: str) -> str:
    """Clean and reconstruct text from PDF."""
    text = reconstruct_sentences(text)
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


def split_into_chunks(text: str, max_chars: int = 2000) -> list:
    """Split text into chunks by sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if current_chunk and len(current_chunk) + len(sentence) + 1 > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = (current_chunk + " " + sentence).strip() if current_chunk else sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return [c for c in chunks if c]


async def generate_speech(text: str, voice: str = "en-US-AriaNeural", speed: float = 1.0):
    """Generate speech using edge-tts."""
    communicate = edge_tts.Communicate(text, voice, rate=f"{speed:+.0%}")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


def main():
    pdf_path = "/home/mcstar/Nextcloud/Vault/books/finney/CF The Promises of God - Charles Finney.pdf"

    print(f"📖 Extracting text from {pdf_path}")
    try:
        result = subprocess.run(
            ['pdftotext', '-f', '1', '-l', '5', pdf_path, '-'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        raw_text = result.stdout
        print(f"✓ Extracted {len(raw_text)} characters")
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    print("🔄 Preprocessing text with sentence reconstruction...")
    text = preprocess_text(raw_text)
    print(f"✓ Preprocessed: {len(text)} characters")

    print("📝 Splitting into chunks...")
    chunks = split_into_chunks(text, max_chars=2000)
    print(f"✓ Split into {len(chunks)} chunks\n")

    print("=" * 80)
    print("FIRST 3 CHUNKS:")
    print("=" * 80)
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n[CHUNK {i}] ({len(chunk)} chars)")
        print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
    print("\n")

    # Generate audio for first 2 chunks
    print("=" * 80)
    print("GENERATING AUDIO (first 2 chunks)...")
    print("=" * 80)

    all_samples = []
    sr = 24000

    for i, chunk in enumerate(chunks[:2], 1):
        print(f"\n🔊 Generating chunk {i}...")
        try:
            audio_data = asyncio.run(generate_speech(chunk, voice="en-US-AriaNeural", speed=1.0))

            # Convert MP3 bytes to numpy array
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            result = subprocess.run(
                ['ffmpeg', '-i', tmp_path, '-f', 's16', '-acodec', 'pcm_s16le', '-ar', '24000', '-'],
                capture_output=True
            )
            os.unlink(tmp_path)

            if result.returncode != 0:
                print(f"❌ ffmpeg failed: {result.stderr.decode()}")
                continue

            audio_bytes = result.stdout
            samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            all_samples.append(samples)
            print(f"✓ Generated {len(samples)} samples ({len(samples) / sr:.1f}s)")

        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    if all_samples:
        print(f"\n✓ Concatenating {len(all_samples)} chunks...")
        full_audio = np.concatenate(all_samples)

        # Normalize
        peak = np.max(np.abs(full_audio))
        if peak > 0:
            full_audio = full_audio * (0.9 / peak)

        output_file = "/tmp/test_with_reconstruction.wav"
        print(f"📁 Saving to {output_file}...")
        sf.write(output_file, full_audio, sr)
        duration = len(full_audio) / sr
        print(f"✓ Saved: {len(full_audio)} samples at {sr}Hz = {duration:.1f}s")
        print(f"\n📌 Test completed successfully!")
    else:
        print("❌ No audio generated")


if __name__ == '__main__':
    main()
