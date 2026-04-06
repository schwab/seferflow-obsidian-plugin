#!/usr/bin/env python3
"""
Test sentence reconstruction without importing seferflow
(which has heavy dependencies).
"""

import re

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


# Test with the Finney PDF - extract a sample
import subprocess

pdf_path = "/home/mcstar/Nextcloud/Vault/books/finney/CF The Promises of God - Charles Finney.pdf"

try:
    result = subprocess.run(
        ['pdftotext', '-f', '1', '-l', '5', pdf_path, '-'],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        exit(1)

    raw_text = result.stdout

    print("=" * 80)
    print("BEFORE RECONSTRUCTION (first 500 chars):")
    print("=" * 80)
    print(raw_text[:500])
    print("\n")

    reconstructed = reconstruct_sentences(raw_text)

    print("=" * 80)
    print("AFTER RECONSTRUCTION (first 500 chars):")
    print("=" * 80)
    print(reconstructed[:500])
    print("\n")

    # Show first few reconstructed sentences
    sentences = [s.strip() for s in reconstructed.split('\n\n') if s.strip()]
    print("=" * 80)
    print("FIRST 5 RECONSTRUCTED SENTENCES:")
    print("=" * 80)
    for i, sent in enumerate(sentences[:5], 1):
        print(f"\n[{i}] {sent}\n")
        print("-" * 80)

except Exception as e:
    print(f"Error: {e}")
    exit(1)
