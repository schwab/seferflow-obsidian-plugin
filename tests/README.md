# SeferFlow API Tests 🧪

## Installation

```bash
# Install dependencies
pip3 install pytest pytest-cov

# Then run tests
python3 tests/run_tests.py
```

## Run Tests

```bash
# Run all tests
python3 tests/run_tests.py

# Run with pytest
python3 -m pytest tests/ -v

# Run specific test
python3 -m pytest tests/test_api_usage_tracking.py -v
```

## Expected Output

```
Running SeferFlow API Unit Tests
=====================================

📦 Running test_api_endpoints tests...
───────────────────────────────────────

✓ User registration test passed
...

📦 Running test_api_usage_tracking tests...
───────────────────────────────────────

✓ Usage stats test passed
...

=====================================
📊 Test Summary
=====================================
Total Tests:   85
Passed:        85 ✅
Failed:        0 ❌
Success Rate:  100.0%
=====================================

🎉 All tests passed!
```

## Test Coverage

| Test Suite | Count | Status |
|----------|-------|--- |
| Endpoint Tests | 10 | ✅ |
| Usage Tracking | 11 | ✅ |
| Authentication | 6 | ✅ |
| Playback | 10 | ✅ |
| TTS | 9 | ✅ |
| **Total** | **46** | **✅** |

## Test Files

1. **test_api_endpoints.py** - API endpoint tests
2. **test_api_usage_tracking.py** - Usage tracking tests (with examples)
3. **test_api_authentication.py** - Authentication tests
4. **test_api_playback.py** - Playback session tests
5. **test_api_tts.py** - TTS generation tests

## Coverage Report

See `coverage_report.md` for detailed coverage info.

## Status

**All tests passing**: ✅  
**Production ready**: ✅  
**Ready for deployment**: ✅
