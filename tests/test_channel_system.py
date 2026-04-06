#!/usr/bin/env python3
"""Stand-alone tests for Channel System"""

import sys
import os
from datetime import datetime
import hashlib

# Change to tests directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import models
from seferflow_api.models.channel import (
    create_device_fingerprint,
    DEVICE_FINGERPRINT_FIELDS,
    Channel,
)

print("=" * 70)
print("Testing Channel System...")
print("=" * 70)
print()

# Test 1: Basic fingerprint creation
print("Test 1: Basic fingerprint creation")
fingerprint = create_device_fingerprint(
    host_id="localhost",
    device_id="audio_001",
    version="1.0.0",
)
print(f"  Fingerprint: {fingerprint}")
print(f"  Length: {len(fingerprint)}")
assert fingerprint.startswith("ch_"), "Fingerprint should start with ch_"
assert len(fingerprint) == 32, "SHA256 should be 32 chars"
print("  ✓ PASSED")
print()

# Test 2: Fingerprint consistency
print("Test 2: Fingerprint consistency")
data1 = {
    "host_id": "server1",
    "device_id": "dev001",
    "version": "1.0.0",
    "user_agent": "Mozilla/5.0",
}
data2 = {
    "host_id": "server1",
    "device_id": "dev001",
    "version": "1.0.0",
    "user_agent": "Mozilla/5.0",
}
fp1 = create_device_fingerprint(**data1)
fp2 = create_device_fingerprint(**data2)
assert fp1 == fp2, "Same inputs should produce same fingerprint"
print(f"  Fingerprint 1: {fp1}")
assert fp2 == fp1, "Fingerprint 2 should equal fingerprint 1"
print("  ✓ PASSED")
print()

# Test 3: Different IP produces different fingerprint
print("Test 3: Different IP produces different fingerprint")
data3 = {
    "host_id": "localhost",
    "device_id": "audio_001",
    "ip_address": "192.168.1.10",
}
data4 = {
    "host_id": "localhost",
    "device_id": "audio_001",
    "ip_address": "192.168.1.11",
}
fp3 = create_device_fingerprint(**data3)
fp4 = create_device_fingerprint(**data4)
assert fp3 != fp4, "Different IPs should produce different fingerprints"
print(f"  Fingerprint 3: {fp3}")
print(f"  Fingerprint 4: {fp4}")
print("  ✓ PASSED")
print()

# Test 4: Unique fingerprints for different devices
print("Test 4: Unique fingerprints for different devices")
fingerprints = []
for i in range(100):
    fp = create_device_fingerprint(
        host_id=f"device_{i}",
        device_id=f"device_{i}",
    )
    fingerprints.append(fp)
unique_count = len(set(fingerprints))
print(f"  Unique fingerprints: {unique_count} out of {len(fingerprints)}")
assert unique_count == len(fingerprints), f"All fingerprints should be unique (got {unique_count}, expected {len(fingerprints)})"
print("  ✓ PASSED")
print()

# Test 5: Device fingerprint fields constant
print("Test 5: Device fingerprint fields constant")
print(f"  Fields: {DEVICE_FINGERPRINT_FIELDS}")
assert isinstance(DEVICE_FINGERPRINT_FIELDS, list), "Should be a list"
assert len(DEVICE_FINGERPRINT_FIELDS) >= 5, "Should have at least 5 fields"
print(f"  Number of fields: {len(DEVICE_FINGERPRINT_FIELDS)}")
print("  ✓ PASSED")
print()

# Test 6: Missing fields handling
print("Test 6: Missing fields handling")
incomplete_data = {
    "host_id": "localhost",
}
fp_incomplete = create_device_fingerprint(**incomplete_data)
print(f"  Fingerprint with incomplete data: {fp_incomplete}")
assert fp_incomplete is not None, "Should create fingerprint even with incomplete data"
print("  ✓ PASSED")
print()

# Test 7: Fingerprint with user_agent
print("Test 7: Fingerprint with user_agent")
ua_data = {
    "host_id": "localhost",
    "device_id": "audio_001",
    "version": "1.0.0",
    "user_agent": "Obsidian-Plugin/1.0.0",
    "browser": "Firefox",
}
fp_ua = create_device_fingerprint(**ua_data)
print(f"  Fingerprint with user_agent: {fp_ua[:20]}...")
assert fp_ua != fp_incomplete, "Fingerprint with user_agent should differ"
print("  ✓ PASSED")
print()

# Test 8: OS fingerprint
print("Test 8: OS fingerprint")
os_data = {
    "host_id": "localhost",
    "device_id": "audio_001",
    "version": "1.0.0",
    "os": "Ubuntu 22.04",
    "browser": "Chrome",
}
fp_os = create_device_fingerprint(**os_data)
print(f"  Fingerprint with OS: {fp_os[:20]}...")
assert fp_os is not None, "Should create fingerprint with OS field"
print("  ✓ PASSED")
print()

# Test 9: Mobile device fingerprint
print("Test 9: Mobile device fingerprint")
mobile_data = {
    "host_id": "iPhone",
    "device_id": "iPhone_device",
    "version": "1.0.0",
    "client_type": "mobile",
    "os": "iOS 17",
    "browser": "Safari",
}
fp_mobile = create_device_fingerprint(**mobile_data)
print(f"  Mobile fingerprint: {fp_mobile[:30]}...")
assert fp_mobile is not None, "Should create fingerprint for mobile"
print("  ✓ PASSED")
print()

# Test 10: Console/TUI fingerprint
print("Test 10: Console/TUI fingerprint")
tui_data = {
    "host_id": "TUI_device",
    "device_id": "null",
    "version": "1.0.0",
    "client_type": "tui",
    "os": "Linux",
}
fp_tui = create_device_fingerprint(**tui_data)
print(f"  TUI fingerprint: {fp_tui[:30]}...")
assert fp_tui is not None, "Should create fingerprint for TUI"
print("  ✓ PASSED")
print()

# Summary
print("=" * 70)
print("Test Summary")
print("=" * 70)
print("Total tests passed: 10")
print("All channel system tests PASSED! ✅")
print()
print("Tests verify:")
print("  - Device fingerprint creation")
print("  - Fingerprint consistency")
print("  - Fingerprint uniqueness")
print("  - Handling missing fields")
print("  - Support for multiple client types")
print()
print("=" * 70)
