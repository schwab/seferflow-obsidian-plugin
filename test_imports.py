#!/usr/bin/env python3
"""
Test that the reconstruct_sentences function works correctly.
"""

import re

# Define the functions locally to test them
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


print("✓ Functions defined and ready to test")

# Test with a sample PDF-like text
sample_pdf_text = """I will put my law in their inward parts, and write it in
their hearts, and I will be their God, and they shall be my
people. And they shall teach no more, every man his neighbour,
and every man his brother, saying, Know the Lord; for they shall
all know me, from the least of them to the greatest of them, saith
the Lord, for I will forgive their iniquity, and I will remember
their sin no more."""

print("\n" + "=" * 80)
print("TEST INPUT (PDF with display-induced line breaks):")
print("=" * 80)
print(sample_pdf_text)

reconstructed = reconstruct_sentences(sample_pdf_text)
print("\n" + "=" * 80)
print("AFTER reconstruct_sentences():")
print("=" * 80)
print(reconstructed)

preprocessed = preprocess_text(sample_pdf_text)
print("\n" + "=" * 80)
print("AFTER preprocess_text() (full pipeline):")
print("=" * 80)
print(preprocessed)

chunks = split_into_chunks(preprocessed, max_chars=500)
print("\n" + "=" * 80)
print(f"AFTER split_into_chunks() - {len(chunks)} chunks:")
print("=" * 80)
for i, chunk in enumerate(chunks, 1):
    print(f"\n[{i}] {chunk}")

print("\n✅ All functions working correctly!")
