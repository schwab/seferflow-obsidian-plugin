#!/usr/bin/env python3
"""
Simple script to generate audio from a PDF chapter and save to WAV.
Bypasses the player entirely to inspect the raw audio data.
"""

import sys
import os
sys.path.insert(0, '/home/mcstar/projects/seferflow')

from seferflow import (
    browse_books, get_chapters, select_chapter, extract_pdf_text,
    preprocess_text, split_into_chunks, generate_speech, trim_silence,
    remove_silence_gaps
)
import numpy as np
import soundfile as sf

def main():
    print("📚 Audio Generation Tool (No Player)\n")

    # Step 1: Browse and select book
    pdf_path = browse_books()
    if not pdf_path:
        return

    # Step 2: Get chapters
    chapters = get_chapters(pdf_path)
    if not chapters:
        chapters = [{'num': 1, 'title': 'Full Book', 'start_page': 1, 'end_page': None}]

    # Step 3: Select chapter
    chapter = select_chapter(chapters)
    if not chapter:
        return

    # Step 4: Extract text
    print(f"\n📄 Extracting text from {chapter['title']}...")
    text = extract_pdf_text(pdf_path, chapter['start_page'], chapter['end_page'])
    text = preprocess_text(text)

    word_count = len(text.split())
    print(f"✓ Extracted {word_count} words")

    # Step 5: Get voice and speed
    voice = "en-US-AriaNeural"
    speed = 1.0
    print(f"Using: {voice} at {speed}x speed")

    # Step 6: Split into chunks
    chunks = split_into_chunks(text)
    print(f"\n🔄 Generating {len(chunks)} audio chunks...")

    # Step 7: Generate and concatenate all chunks
    all_samples = []
    sr = 24000

    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}/{len(chunks)}...", end=' ', flush=True)
        try:
            samples, sr = generate_speech(chunk, voice, speed)
            # DO NOT trim silence - we want to see what edge-tts actually generates
            all_samples.append(samples)
            print(f"OK ({len(samples)} samples)")
        except Exception as e:
            print(f"FAILED: {e}")
            return

    # Concatenate all samples
    print(f"\n✓ Concatenating {len(all_samples)} chunks...")
    full_audio = np.concatenate(all_samples)

    # Remove silence gaps introduced by edge-tts MP3 concatenation
    print("🔧 Removing silence gaps...")
    full_audio = remove_silence_gaps(full_audio, sr, silence_threshold=0.001, min_silence_duration=0.3)

    # Normalize
    peak = np.max(np.abs(full_audio))
    if peak > 0:
        full_audio = full_audio * (0.9 / peak)

    # Save to file
    output_file = f"/tmp/{chapter['title'].replace(' ', '_')}_raw.wav"
    print(f"📁 Saving to {output_file}...")
    sf.write(output_file, full_audio, sr)

    duration = len(full_audio) / sr
    print(f"✓ Saved: {len(full_audio)} samples at {sr}Hz = {duration:.1f}s")
    print(f"\nOpen in Audacity: audacity {output_file}")
    print("Look for complete silence (flat line) between audio sections.")

if __name__ == '__main__':
    main()
