#!/usr/bin/env python3
"""
Diagnostic script to test app startup
"""
import sys
import traceback
from pathlib import Path

# Add the hr directory to path
hr_dir = Path(__file__).parent
sys.path.insert(0, str(hr_dir))

print(f"Python version: {sys.version}")
print(f"Working directory: {hr_dir}")
print()

# Test 1: Check environment
print("=" * 60)
print("TEST 1: Loading .env file...")
print("=" * 60)
try:
    from pathlib import Path
    import os
    
    env_path = hr_dir / ".env"
    print(f".env file exists: {env_path.exists()}")
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
            print(f".env size: {len(env_content)} bytes")
            print(".env variables:")
            for line in env_content.split('\n')[:5]:
                if line.strip() and not line.startswith('#'):
                    key = line.split('=')[0].strip()
                    print(f"  - {key}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

print()

# Test 2: Test Flask import
print("=" * 60)
print("TEST 2: Importing Flask...")
print("=" * 60)
try:
    import flask
    print(f"✓ Flask version: {flask.__version__}")
except ImportError as e:
    print(f"✗ Flask not installed: {e}")
    traceback.print_exc()

print()

# Test 3: Test app import
print("=" * 60)
print("TEST 3: Importing app.py...")
print("=" * 60)
try:
    import app
    print(f"✓ app imported successfully")
    print(f"  - app.app exists: {hasattr(app, 'app')}")
    print(f"  - app.create_app exists: {hasattr(app, 'create_app')}")
except Exception as e:
    print(f"✗ Failed to import app: {e}")
    traceback.print_exc()

print()

# Test 4: Test create_app()
print("=" * 60)
print("TEST 4: Testing create_app()...")
print("=" * 60)
try:
    from app import create_app
    flask_app = create_app()
    print(f"✓ create_app() succeeded")
    print(f"  - app.name: {flask_app.name}")
    print(f"  - debug: {flask_app.debug}")
except Exception as e:
    print(f"✗ create_app() failed: {e}")
    traceback.print_exc()

print()
print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
