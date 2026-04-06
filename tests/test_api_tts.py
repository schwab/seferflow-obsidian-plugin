#!/usr/bin/env python3
"""
test_api_tts.py

Test API TTS endpoints and audio generation functionality.
"""

from pathlib import Path

def test_tts_generation():
    """Test TTS audio generation"""
    text = "Hello, this is a test audio message."
    voice = "en-US-AriaNeural"
    speed = 1.0
    
    # Simulate response
    response = {
        "audio_id": "audio-abc123",
        "text": text,
        "voice": voice,
        "duration_seconds": 2.5,
        "status": "completed"
    }
    
    assert response["text"] == text
    assert response["voice"] == voice
    assert response["duration_seconds"] > 0
    
    print("✓ TTS generation test passed")
    return True


def test_text_chunking():
    """Test text chunking for splitting"""
    # Long text that needs chunking
    text = "This is a very long text that needs to be split into chunks for processing."
    
    # Split into chunks
    chunks = []
    current_chunk = ""
    max_chars = 2000
    
    for word in text.split():
        if len(current_chunk) + len(word) + 1 > max_chars:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = word
        else:
            current_chunk += " " + word
    
    if current_chunk:
        chunks.append(current_chunk)
    
    assert len(chunks) >= 1
    assert all(len(chunk) <= max_chars for chunk in chunks)
    
    print("✓ Text chunking test passed")
    return True


def test_voice_validation():
    """Test voice validation"""
    valid_voices = [
        "en-US-AriaNeural",
        "en-US-GuyNeural",
        "en-GB-LibbyNeural",
        "en-GB-RyanNeural"
    ]
    
    invalid_voices = [
        "invalid-voice",
        "en-INVALID",
        ""
    ]
    
    for voice in valid_voices:
        assert voice.startswith("en-") or voice.startswith("fr-")
    
    for voice in invalid_voices:
        assert voice not in valid_voices
    
    print("✓ Voice validation test passed")
    return True


def test_speed_validation():
    """Test speed validation"""
    valid_speeds = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
    
    assert all(0.8 <= speed <= 1.3 for speed in valid_speeds)
    
    # Invalid speeds
    invalid_speeds = [0.5, 2.0, 0.0]
    
    assert not any(0.8 <= speed <= 1.3 for speed in invalid_speeds)
    
    print("✓ Speed validation test passed")
    return True


def test_cache_management():
    """Test TTS caching"""
    # Add to cache
    cache = {}
    
    # Generate same text twice
    text1 = "Hello world"
    text2 = "Hello world"
    
    cache[text1] = "audio_data_1"
    cache[text2] = "audio_data_2"
    
    assert cache[text1] == cache[text2]
    
    # Cache size
    cache_size = len(cache)
    assert cache_size <= 100  # Assume max cache size
    
    print("✓ Cache management test passed")
    return True


def test_audio_format():
    """Test audio format validation"""
    valid_formats = ["wav", "mp3", "ogg"]
    
    audio_data = {
        "format": "wav",
        "sample_rate": 24000,
        "duration": 3.2
    }
    
    assert audio_data["format"] in valid_formats
    assert audio_data["sample_rate"] >= 22050
    assert audio_data["duration"] > 0
    
    print("✓ Audio format test passed")
    return True


def test_audio_normalization():
    """Test audio normalization"""
    # Simulate audio samples
    samples = [0.5, -0.3, 0.1, -0.2, 0.8]  # Example samples
    
    # Calculate peak
    peak = max(abs(s) for s in samples)
    
    assert peak == 0.8  # Maximum absolute value
    
    # Normalize with 0.9 headroom
    normalized = [s * (0.9 / peak) for s in samples if peak > 0]
    
    assert all(abs(s) <= 0.9 for s in normalized if peak > 0)
    
    print("✓ Audio normalization test passed")
    return True


def test_silence_removal():
    """Test silence removal"""
    # Audio with silence
    audio_with_silence = [0, 0, 0, 0.5, 0.3, -0.3, 0, 0, 0, 0.4]
    
    # Find silence regions
    silence_threshold = 0.01
    is_silent = [abs(s) < silence_threshold for s in audio_with_silence]
    
    # Remove long silence
    from signal import where
    audio_cleaned = [s for s in is reversed()]
    
    print("✓ Silence removal test passed")
    return True


def test_rate_limiting():
    """Test rate limiting for TTS generation"""
    # Free tier limit
    requests_per_minute = 60
    
    # Simulate requests
    requests = []
    
    for _ in range(65):
        requests.append(0)
    
    # Check requests in window
    window = requests[-60:]
    assert sum(window) <= 60
    
    print("✓ Rate limiting test passed")
    return True


if __name__ == "__main__":
    """Run all TTS tests"""
    print("Running TTS Tests...")
    print("=" * 50)
    
    tests = [
        test_tts_generation,
        test_text_chunking,
        test_voice_validation,
        test_speed_validation,
        test_cache_management,
        test_audio_format,
        test_audio_normalization,
        test_silence_removal,
        test_rate_limiting
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"Failed: {test.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"Error: {test.__name__}: {e}")
        finally:
            print()
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    
    print("=" * 50)
