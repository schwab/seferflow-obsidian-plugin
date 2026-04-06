#!/usr/bin/env python3
"""
Debug script to extract and split sentences from a PDF.
Helps diagnose why the audio sounds odd.
"""

import sys
import re
sys.path.insert(0, '/home/mcstar/projects/seferflow')

from seferflow import extract_pdf_text, preprocess_text, split_into_chunks

# Extract first chapter only (pages 1-10 as a guess)
pdf_path = "/home/mcstar/Nextcloud/Vault/books/finney/CF The Promises of God - Charles Finney.pdf"

print(f"📖 Extracting text from: {pdf_path}")
try:
    # Try first 20 pages to get a full chapter
    text = extract_pdf_text(pdf_path, start_page=1, end_page=20)
    print(f"✓ Extracted {len(text)} characters")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Preprocess
text = preprocess_text(text)
print(f"✓ Preprocessed: {len(text)} characters")

# Split into chunks (sentences)
chunks = split_into_chunks(text, max_chars=2000)
print(f"✓ Split into {len(chunks)} sentence groups\n")

# Save to file
output_file = "/tmp/sentences_from_finney.txt"
with open(output_file, 'w') as f:
    f.write(f"Extracted from: {pdf_path}\n")
    f.write(f"Total sentence groups: {len(chunks)}\n")
    f.write(f"Total characters: {len(text)}\n")
    f.write("=" * 80 + "\n\n")

    for i, chunk in enumerate(chunks, 1):
        f.write(f"[CHUNK {i}] ({len(chunk)} chars)\n")
        f.write(chunk)
        f.write("\n\n")
        f.write("-" * 80 + "\n\n")

print(f"✓ Saved to: {output_file}")
print(f"\nFirst 3 chunks (preview):\n")
print("=" * 80)
for i, chunk in enumerate(chunks[:3], 1):
    print(f"\n[CHUNK {i}] ({len(chunk)} chars)")
    print(chunk)
    print("\n" + "-" * 80)
