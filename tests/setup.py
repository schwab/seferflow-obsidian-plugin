"""
SeferFlow API - Test Coverage Setup
"""

# Coverage configuration
COVERAGE_CONFIG = {
    "include": ["seferflow_api/*"],
    "omit": ["*/__init__.py", "*/tests/*"],
    "show_missing": True,
}

# Test discovery configuration
TEST_CONFIG = {
    "min_coverage": 80,
    "targets": [
        "seferflow_api/main.py",
        "seferflow_api/api/*",
        "seferflow_api/core/*",
        "seferflow_api/services/*",
    ],
}
