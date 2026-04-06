#!/usr/bin/env python3
"""Test if the API can be imported"""

import sys
from pathlib import Path

# Add both paths
seferflow_root = Path(__file__).parent
sys.path.insert(0, str(seferflow_root))
sys.path.insert(0, str(seferflow_root / "seferflow-api"))

try:
    from seferflow_api.main import app
    print("✓ Successfully imported FastAPI app")
    print(f"✓ App has {len(app.routes)} routes")

    # Test that we can get the openapi schema
    schema = app.openapi()
    print(f"✓ OpenAPI schema generated: {len(schema.get('paths', {}))} endpoints")

except ImportError as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ Runtime error: {e}")
    import traceback
    traceback.print_exc()
