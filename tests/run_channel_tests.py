#!/usr/bin/env python3
"""
Simple test runner for channel system
"""

import sys
sys.path.insert(0, '/home/mcstar/projects/seferflow')

print("=" * 70)
print("Channel System Unit Tests")
print("=" * 70)
print()

# Run tests
try:
    from seferflow_api.models.channel import (
        create_device_fingerprint,
        DEVICE_FINGERPRINT_FIELDS,
    )
    
    # Test 1
    print("Test 1: Create fingerprint...")
    fp = create_device_fingerprint(
        host_id="localhost",
        device_id="audio_001",
        version="1.0.0",
    )
    assert fp.startswith("ch_")
    assert len(fp) == 32
    print("  ✓ PASSED")
    print()
    
    # Test 2
    print("Test 2: Consistency...")
    fp1 = create_device_fingerprint(host_id="s1", device_id="d1", version="1.0")
    fp2 = create_device_fingerprint(host_id="s1", device_id="d1", version="1.0")
    assert fp1 == fp2
    print("  ✓ PASSED")
    print()
    
    # Test 3
    print("Test 3: Uniqueness...")
    fps = [create_device_fingerprint(host_id=f"h{i}", device_id=f"d{i}") for i in range(10)]
    assert len(fps) == len(set(fps))
    print("  ✓ PASSED")
    print()
    
    # Test 4
    print("Test 4: Empty data...")
    fp_empty = create_device_fingerprint(host_id="localhost")
    assert fp_empty is not None
    print("  ✓ PASSED")
    print()
    
    # Test 5
    print("Test 5: Fingerprint fields...")
    assert isinstance(DEVICE_FINGERPRINT_FIELDS, list)
    assert len(DEVICE_FINGERPRINT_FIELDS) >= 5
    print(f"  Fields: {len(DEVICE_FINGERPRINT_FIELDS)}")
    print("  ✓ PASSED")
    print()
    
    print("=" * 70)
    print("All tests PASSED! ✅")
    print("=" * 70)
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    print()
    print("=" * 70)
    print("Tests FAILED! ❌")
    print("=" * 70)
