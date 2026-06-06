#!/usr/bin/env python3
"""
Quick test script to check if app.py has import errors
"""
import sys
sys.path.insert(0, '/c/Users/PC/hr')

try:
    print("Testing imports...")
    from app import app
    print("✓ App imported successfully")
    print(f"✓ App initialized: {app}")
    print(f"✓ Debug mode: {app.debug}")
except Exception as e:
    print(f"✗ Error importing app: {e}")
    import traceback
    traceback.print_exc()
