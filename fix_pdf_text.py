#!/usr/bin/env python3
"""
Reconstruct sentences from PDF-extracted text that has display-induced line breaks.
"""

import re

def reconstruct_sentences(text: str) -> str:
    """
    Reconstruct sentences from PDF text with display-induced line breaks.

    PDF text has lines broken for display (fixed column width), not for sentences.
    This function:
    1. Joins lines that were broken mid-sentence
    2. Preserves paragraph breaks
    3. Returns text with proper sentence structure
    """

    lines = text.split('\n')
    reconstructed = []
    current_sentence = ""

    for i, line in enumerate(lines):
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


# Test it
test_text = """THE PROMISES OF GOD
By
Charles Finney
Text.--2 Pet. 1:4: "Whereby are given unto us exceeding great and precious
promises, that by these ye might be partakers of the divine nature, having
escaped the corruption that is in the world through lust."
I. I am to make several preliminary remarks upon the nature of the promises. 1. The promises made to the church under the old dispensation belong
emphatically to the Christian Church. Thus the promise made to Abraham was
designed more for his posterity, and for the Christian Church than for himself. That part of the promise which related to the temporal possession of Canaan
never was fulfilled to him. He lived and died "a stranger and sojourner in the
land of promise." In Heb. 11:13 we are expressly informed that Abraham did not
receive the fulfillment of the promises, but that they belonged especially to
Christians under the New Testament dispensation. "These all died in faith not
having received the promises--but having seen them afar off, and were
persuaded of them, and embraced them, and confessed that they were strangers
and pilgrims on the earth," i.e. Abraham and the patriarchs died without
receiving the fulfillment of the promises. Again, verses 39-40, -"And these all,
having obtained a good report, through faith, received not the promises; God
having provided some better thing for us, that they without us should not be
made perfect." So the New Covenant in Jer."""

print("BEFORE RECONSTRUCTION:")
print("=" * 80)
print(test_text[:500])
print("\n...\n")

reconstructed = reconstruct_sentences(test_text)

print("\nAFTER RECONSTRUCTION:")
print("=" * 80)
print(reconstructed[:500])
print("\n...\n")

print("\nFULL RECONSTRUCTED TEXT:")
print("=" * 80)
print(reconstructed)
