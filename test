#!/usr/bin/env python3
"""
Simple test to verify MCP server code integration without running full app.
"""
import sys
import os
import threading
import time

# Add seferflow to path
sys.path.insert(0, '/home/mcstar/projects/seferflow')

# We'll patch the imports that require heavy dependencies
class MockSoundFile:
    pass

class MockSoundDevice:
    def play(self, *args, **kwargs):
        pass
    def stop(self):
        pass
    def wait(self):
        pass
    def get_stream(self):
        return type('Stream', (), {'active': False})()

# Patch before import
sys.modules['soundfile'] = MockSoundFile()
sys.modules['sounddevice'] = MockSoundDevice()

# Now we can do a basic structural check without soundfile error
print("Testing MCP integration structure...")

# Read the file directly and check structure
with open('/home/mcstar/projects/seferflow/seferflow.py', 'r') as f:
    content = f.read()

checks = [
    ('MCP_PORT = 8765' in content, "MCP_PORT = 8765 constant defined"),
    ('mcp_interrupt: threading.Event = field(default_factory=threading.Event)' in content, "mcp_interrupt event in PlayerControls"),
    ('mcp_ready: threading.Event = field(default_factory=threading.Event)' in content, "mcp_ready event in PlayerControls"),
    ('mcp_done: threading.Event = field(default_factory=threading.Event)' in content, "mcp_done event in PlayerControls"),
    ('mcp_samples: Optional[np.ndarray] = None' in content, "mcp_samples field in PlayerControls"),
    ('mcp_sample_rate: int = 24000' in content, "mcp_sample_rate field in PlayerControls"),
    ('mcp_caption: str = ""' in content, "mcp_caption field in PlayerControls"),
    ('sample_offset: int = 0' in content, "sample_offset in PlaybackState"),
    ('def _generate_tone(freq_hz: float, duration_s: float, sample_rate: int)' in content, "_generate_tone function defined"),
    ('def run_mcp_server(controls: PlayerControls, port: int = MCP_PORT):' in content, "run_mcp_server function defined"),
    ('state.sample_offset = 0' in content, "sample_offset lifted to state"),
    ('state.sample_offset =' in content, "sample_offset accessed via state"),
    ('if controls.mcp_interrupt.is_set() and controls.mcp_samples is not None:' in content, "MCP interrupt handler added"),
    ('controls.mcp_ready.set()' in content, "mcp_ready.set() in interrupt handler"),
    ('controls.mcp_done.set()' in content, "mcp_done.set() in interrupt handler"),
    ('_generate_tone(880, 0.25, sample_rate)' in content, "Notification tone in interrupt"),
    ('_generate_tone(660, 0.2, sample_rate)' in content, "Closing tone in interrupt"),
    ('mcp_thread = threading.Thread' in content, "MCP thread started in main()"),
    ('🔌 MCP server listening' in content, "MCP startup message"),
    ('display_text = controls.mcp_caption if controls.mcp_interrupt.is_set()' in content, "Caption display switching"),
]

print("\n" + "="*70)
print("MCP IMPLEMENTATION VERIFICATION")
print("="*70)

failed = []
for passed, desc in checks:
    status = "✅" if passed else "❌"
    print(f"{status} {desc}")
    if not passed:
        failed.append(desc)

print("="*70)
if failed:
    print(f"\n❌ {len(failed)} checks failed:")
    for desc in failed:
        print(f"  - {desc}")
    sys.exit(1)
else:
    print(f"\n✅ All {len(checks)} checks passed!")
    print("\nMCP Server Implementation Summary:")
    print("  • 3 new threading.Event fields for coordination")
    print("  • 2 audio data fields (samples, sample_rate)")
    print("  • 1 caption text field for display")
    print("  • PlaybackState extended with sample_offset")
    print("  • _generate_tone() for notification sounds")
    print("  • run_mcp_server() listening on port 8765")
    print("  • Interrupt handler in _poll_controls()")
    print("  • MCP thread started in main()")
    print("  • Captions switch during interruption")
    sys.exit(0)
