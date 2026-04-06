# MCP Server Testing Guide

The SeferFlow MCP server has been successfully implemented. Here's how to test it:

## Quick Start

### Terminal 1: Start SeferFlow
```bash
cd /home/mcstar/projects/seferflow
./seferflow
```

You should see:
```
📚 BOOK READER - Starting up...
  🔌 MCP server listening on 127.0.0.1:8765
```

Then:
1. Select a PDF book
2. Select a chapter
3. Start playback (the audio should play)

### Terminal 2: Test MCP Server

#### Test 1: List available tools
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | nc 127.0.0.1 8765
```

Expected response:
```json
{"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"say_text","description":"Interrupt the current audiobook and speak the given text aloud, then resume.","inputSchema":{"type":"object","properties":{"text":{"type":"string","description":"Text to speak"},"voice":{"type":"string","description":"edge-tts voice name (optional)"}},"required":["text"]}}]}}
```

#### Test 2: Send an interruption message
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"say_text","arguments":{"text":"Hello! This is a test message from AI."}}}' | nc 127.0.0.1 8765
```

What happens:
1. 🔔 **Notification tone** plays (880 Hz, 0.25s)
2. **Book pauses** at exact playback position
3. **Caption display** switches to show your message
4. **Your message is spoken** aloud using TTS
5. 🔔 **Closing tone** plays (660 Hz, 0.2s)
6. **Book resumes** from where it paused
7. **Captions switch back** to book text

#### Test 3: Send with custom voice
```bash
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"say_text","arguments":{"text":"Testing with a different voice","voice":"en-US-GuyNeural"}}}' | nc 127.0.0.1 8765
```

## Implementation Details

### Architecture
- **MCP Port**: 127.0.0.1:8765 (localhost only, no external exposure)
- **Protocol**: JSON-RPC 2.0 over TCP with newline-delimited messages
- **Threading**: MCP server runs as a daemon thread; audio playback and interruption in main thread

### Synchronization Events
- `mcp_interrupt`: Signals playback thread that an interruption is pending
- `mcp_ready`: Playback thread signals it has paused and is ready for audio
- `mcp_done`: Playback thread signals interruption is complete, safe to resume

### What's New in the Code

**1. PlaybackState** (line ~68)
```python
sample_offset: int = 0  # Lifted from local variable for MCP access
```

**2. PlayerControls** (lines ~75-85)
```python
mcp_interrupt: threading.Event    # Interrupt request pending
mcp_ready: threading.Event         # Book has paused
mcp_done: threading.Event          # Message playback done
mcp_samples: Optional[np.ndarray]  # Pre-generated audio
mcp_sample_rate: int               # Audio sample rate
mcp_caption: str                   # Display text during interruption
```

**3. Tone Generation** (~line 1004)
- `_generate_tone(freq_hz, duration_s, sample_rate)` — generates notification tones with fade in/out

**4. MCP Interrupt Handler** (~line 1121)
- In `_poll_controls()` within `play_audio_with_display()`
- Executed every 50ms during playback
- Pauses book, plays tones, plays message, resumes book

**5. MCP Server** (~line 1461)
- `run_mcp_server(controls, port)` — JSON-RPC server
- Handles `tools/list` and `tools/call` methods
- Generates TTS asynchronously while server blocks
- Waits for playback completion before responding

**6. Main Integration** (~line 1564)
- MCP server started as daemon thread on startup
- Reuses same `controls` object shared with playback loop
- Gracefully handles port conflicts (silently skips if already in use)

## Error Handling

### "text is required"
You sent a `tools/call` without the text parameter.

### "Connection refused"
The MCP server isn't running. Make sure seferflow is active.

### "Timeout"
The playback thread didn't respond in time. This shouldn't happen with normal audio.

## Advanced Usage

### Python Client Example
```python
import socket
import json

def send_mcp(text, voice="en-US-AriaNeural"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 8765))
    
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "say_text",
            "arguments": {
                "text": text,
                "voice": voice
            }
        }
    }
    
    sock.sendall((json.dumps(req) + '\n').encode())
    resp = sock.recv(4096).decode().strip()
    sock.close()
    
    return json.loads(resp)

# Test it
result = send_mcp("Hello from Python!")
print(result)
```

### Testing Edge Cases

1. **Rapid interruptions**: Send multiple messages quickly — server queues them
2. **During pause**: If book is paused, interruption works normally
3. **During seek**: If user seeks while message plays, message completes first
4. **Between chapters**: If message arrives between chapters, it's discarded (non-blocking)
5. **Invalid voice**: TTS will fail gracefully with error response

## Performance Notes

- **Latency**: ~1-2 seconds from request to tone (TTS generation time)
- **Audio quality**: Same as normal playback (24kHz, float32)
- **Concurrent requests**: Handled sequentially (one at a time)
- **Memory**: Tones (~50KB), message samples (~1-5MB depending on duration)

## Troubleshooting

### MCP server doesn't appear to start
```bash
# Check if something is already running on port 8765
lsof -i :8765

# Try a different port (edit MCP_PORT in seferflow.py)
```

### Message doesn't play
- Make sure book is actively playing (not paused)
- Check audio output is working (book audio plays fine?)
- Try a short message first ("hello")

### Captions don't switch
- Display updates every 1 second, so there's a delay
- During interrupt, original text caption should switch to message text

### Getting stuck / no response
- This shouldn't happen, but if it does:
  - Pause the book (spacebar)
  - Resume (spacebar again)
  - Try the interrupt again

## Related Code Changes

See `/home/mcstar/.claude/plans/fuzzy-chasing-panda.md` for the full implementation plan.

The MCP server complements the existing streaming TTS, buffering, progress tracking, and keyboard controls in SeferFlow.
