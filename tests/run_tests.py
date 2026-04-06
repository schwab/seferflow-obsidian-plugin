#!/usr/bin/env python3
"""
Test Runner for SeferFlow API

Run all unit tests for the SeferFlow API.
"""

import sys
import os

# Change to tests directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add current directory to path
sys.path.insert(0, script_dir)

# Test modules (without pytest requirements)
test_files = [
    'test_api_endpoints',
    'test_api_authentication',
    'test_api_playback',
    'test_api_tts',
]


def run_tests():
    """Run all tests"""
    print("=" * 69)
    print("🔍 SeferFlow API Unit Tests")
    print("=" * 69)
    print()
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # Run each test module
    for module_name in test_files:
        try:
            print(f"\n📦 Running {module_name} tests...")
            print("-" * 66)
            
            # Import module
            module = __import__(module_name, fromlist=[''])
            
            # Run tests in module
            module_tests = [test for test in dir(module) if test.startswith('test_')]
            
            for test_name in module_tests:
                test_func = getattr(module, test_name)
                if callable(test_func):
                    total_tests += 1
                    
                    try:
                        test_func()
                        print(f"  ✓ {test_name}")
                        passed_tests += 1
                    
                    except Exception as e:
                        print(f"  ✗ {test_name}")
                        failed_tests += 1
        
        except Exception as e:
            print(f"  ⚠ Error: {e}")
    
    # Print summary
    print()
    print("=" * 69)
    print("📊 Test Summary")
    print("=" * 69)
    print(f"Total Tests:   {total_tests}")
    print(f"Passed:        {passed_tests} ✅")
    print(f"Failed:        {failed_tests} ❌")
    print(f"Success Rate:  {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
    print("=" * 69)
    
    if failed_tests == 0:
        print()
        print("🎉 All tests passed!")
        print()
        return 0
    else:
        print()
        print(f"⚠ {failed_tests} test(s) failed")
        print()
        return 1


# Run tests
if __name__ == "__main__":
    try:
        exit_code = run_tests()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n✗ Test runner error: {e}")
        sys.exit(1)
