#!/usr/bin/env python3
"""
Test Java detection for LanguageTool service
"""

import sys
import os
import asyncio

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

async def test_java_detection():
    """Test the Java detection method"""
    print("=" * 50)
    print("TESTING JAVA DETECTION")
    print("=" * 50)
    
    try:
        from server.services.languagetool import LanguageToolService
        
        # Create service instance
        service = LanguageToolService()
        
        # Test Java detection
        print("Testing Java availability...")
        java_available = await service._check_java_availability()
        
        if java_available:
            print("✅ Java detection: PASSED")
            print("   Java is available and detected correctly")
        else:
            print("❌ Java detection: FAILED")
            print("   Java was not detected (but we know it's installed)")
            
        return java_available
        
    except Exception as e:
        print(f"❌ Error during Java detection test: {e}")
        return False

async def test_languagetool_init():
    """Test LanguageTool initialization"""
    print("\n" + "=" * 50)
    print("TESTING LANGUAGETOOL INITIALIZATION")
    print("=" * 50)
    
    try:
        from server.services.languagetool import LanguageToolService
        
        # Create service instance
        service = LanguageToolService()
        
        # Test initialization
        print("Initializing LanguageTool service...")
        await service.initialize()
        
        if service._is_initialized:
            print("✅ LanguageTool initialization: PASSED")
            print(f"   Language: {service._current_language}")
            
            # Test a simple check
            print("\nTesting grammar check...")
            issues = await service.check_text("This is a test sentance.")
            print(f"   Found {len(issues)} issues")
            if issues:
                print(f"   Example issue: {issues[0].message}")
            
            # Cleanup
            await service.cleanup()
            return True
        else:
            print("❌ LanguageTool initialization: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error during LanguageTool initialization: {e}")
        return False

async def main():
    """Run all tests"""
    print("LANGUAGETOOL SERVICE TESTS")
    print("=" * 50)
    
    java_ok = await test_java_detection()
    
    if java_ok:
        lt_ok = await test_languagetool_init()
        
        if lt_ok:
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED!")
            print("LanguageTool service is ready to use.")
        else:
            print("\n" + "=" * 50)
            print("⚠️  Java detected but LanguageTool initialization failed.")
    else:
        print("\n" + "=" * 50)
        print("❌ Java detection failed - LanguageTool won't work.")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
