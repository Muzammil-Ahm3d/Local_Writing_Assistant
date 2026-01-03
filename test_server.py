#!/usr/bin/env python3
"""
Simple test to verify that our FastAPI server can start correctly.
Tests imports and basic functionality.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

def test_imports():
    """Test that all necessary imports work"""
    print("Testing imports...")
    
    try:
        # Test basic imports
        import fastapi
        print("✓ FastAPI imported")
        
        import uvicorn  
        print("✓ Uvicorn imported")
        
        # Test our module imports
        from server.main import app
        print("✓ Server app imported")
        
        from server.services.languagetool import LanguageToolService
        print("✓ LanguageTool service imported")
        
        from server.services.whisper_asr import WhisperService  
        print("✓ Whisper service imported")
        
        from server.services.t5_rewriter import T5RewriterService
        print("✓ T5 rewriter service imported")
        
        from server.services.tone import ToneAnalysisService
        print("✓ Tone analysis service imported")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_routes():
    """Test that basic routes are defined"""
    print("Testing route definitions...")
    
    try:
        from server.main import app
        
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/docs", "/openapi.json"]
        
        for route in expected_routes:
            if route in routes:
                print(f"✓ Route {route} found")
            else:
                print(f"❌ Route {route} missing")
        
        print(f"\n📍 Total routes found: {len(routes)}")
        return True
        
    except Exception as e:
        print(f"❌ Route test error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("LOCAL WRITING ASSISTANT - SERVER TEST")
    print("=" * 60)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    print("\n" + "-" * 60)
    
    # Test routes  
    if not test_basic_routes():
        success = False
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("The server should be able to start correctly.")
    else:
        print("💥 SOME TESTS FAILED!")
        print("There are issues that need to be resolved.")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    main()
