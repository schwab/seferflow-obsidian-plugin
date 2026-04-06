#!/usr/bin/env python3
"""
Test the full pipeline: reconstruct -> split into chunks.
"""

import re
import subprocess

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


def split_into_chunks(text: str, max_chars: int = 2000) -> list:
    """Split text into chunks by sentences, staying within max_chars per chunk."""
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


# Extract from Finney PDF
pdf_path = "/home/mcstar/Nextcloud/Vault/books/finney/CF The Promises of God - Charles Finney.pdf"

try:
    result = subprocess.run(
        ['pdftotext', '-f', '1', '-l', '10', pdf_path, '-'],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        exit(1)

    raw_text = result.stdout

    # Reconstruct
    reconstructed = reconstruct_sentences(raw_text)

    # Split into chunks
    chunks = split_into_chunks(reconstructed, max_chars=2000)

    print("=" * 80)
    print(f"TOTAL CHUNKS: {len(chunks)}")
    print("=" * 80)
    print()

    # Show first 5 chunks
    for i, chunk in enumerate(chunks[:5], 1):
        print(f"[CHUNK {i}] ({len(chunk)} chars)")
        print(chunk)
        print()
        print("-" * 80)
        print()

except Exception as e:
    print(f"Error: {e}")
    exit(1)
