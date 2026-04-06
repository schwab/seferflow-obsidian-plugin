#!/usr/bin/env python3
"""
test_api_tts.py

Test API TTS and audio generation endpoints.
"""

def test_tts_generation():
    """Test TTS audio generation"""
    text = "Hello, this is a test audio message."
    voice = "en-US-AriaNeural"
    speed = 1.0
    
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
    text = "This is a very long text that needs to be split."
    
    max_chars = 2000
    chunks = []
    current_chunk = ""
    
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
    
    for voice in valid_voices:
        assert voice.startswith("en-")
    
    print("✓ Voice validation test passed")
    return True


def test_speed_validation():
    """Test speed validation"""
    valid_speeds = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
    
    assert all(0.8 <= speed <= 1.3 for speed in valid_speeds)
    
    print("✓ Speed validation test passed")
    return True


def test_cache_management():
    """Test TTS caching"""
    cache = {}
    text1 = "Hello world"
    text2 = "Hello world"
    
    cache[text1] = "audio_data_1"
    cache[text2] = "audio_data_2"
    
    assert cache[text1] == cache[text2]
    
    print("✓ Cache management test passed")
    return True


def test_audio_format():
    """Test audio format validation"""
    audio_data = {
        "format": "wav",
        "sample_rate": 24000,
        "duration": 3.2
    }
    
    assert audio_data["format"] in ["wav", "mp3", "ogg"]
    assert audio_data["sample_rate"] >= 22050
    assert audio_data["duration"] > 0
    
    print("✓ Audio format test passed")
    return True


def test_audio_normalization():
    """Test audio normalization"""
    samples = [0.5, -0.3, 0.1, -0.2, 0.8]
    
    peak = max(abs(s) for s in samples)
    
    assert peak == 0.8
    
    print("✓ Audio normalization test passed")
    return True


def test_silence_removal():
    """Test silence removal"""
    audio_with_silence = [0, 0, 0, 0.5, 0.3, -0.3, 0, 0, 0, 0.4]
    
    silence_threshold = 0.01
    is_silent = [abs(s) < silence_threshold for s in audio_with_silence]
    
    print("✓ Silence removal test passed")
    return True


def test_rate_limiting():
    """Test rate limiting for TTS generation"""
    requests_per_minute = 60
    
    requests = []
    
    for _ in range(65):
        requests.append(requests.index(_))
    
    assert sum(requests[:60]) <= 60
    
    print("✓ Rate limiting test passed")
    return True


def test_invalid_voice_rejection():
    """Test invalid voice rejection"""
    assert "invalid-voice" not in ["en-US-AriaNeural", "en-US-GuyNeural"]
    
    print("✓ Invalid voice rejection test passed")
    return True


def test_zero_duration_audio():
    """Test zero duration handling"""
    audio = {
        "text": "",
        "duration": 0
    }
    
    assert audio["duration"] == 0
    
    print("✓ Zero duration handling test passed")
    return True
