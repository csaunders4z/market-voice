#!/usr/bin/env python3
"""
Test script for Market Voices
Tests the system components without requiring API keys
"""

import sys
from pathlib import Path
from src.config.settings import get_settings

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        print("✅ Settings imported successfully")
    except Exception as e:
        print(f"❌ Settings import failed: {e}")
        return False
    
    try:
        from src.data_collection.stock_data import stock_collector
        print("✅ Stock data collector imported successfully")
    except Exception as e:
        print(f"❌ Stock data collector import failed: {e}")
        return False
    
    try:
        from src.script_generation.host_manager import host_manager
        print("✅ Host manager imported successfully")
    except Exception as e:
        print(f"❌ Host manager import failed: {e}")
        return False
    
    try:
        from src.script_generation.script_generator import script_generator
        print("✅ Script generator imported successfully")
    except Exception as e:
        print(f"❌ Script generator import failed: {e}")
        return False
    
    try:
        from src.content_validation.quality_controls import quality_controller
        print("✅ Quality controller imported successfully")
    except Exception as e:
        print(f"❌ Quality controller import failed: {e}")
        return False
    
    return True

def test_host_manager():
    """Test host manager functionality"""
    print("\nTesting host manager...")
    
    try:
        from src.script_generation.host_manager import host_manager
        
        # Test host rotation
        lead_host = host_manager.get_lead_host_for_date()
        print(f"✅ Lead host for today: {lead_host}")
        
        # Test host info
        host_info = host_manager.get_host_info(lead_host)
        print(f"✅ Host info retrieved: {host_info['name']} ({host_info['age']})")
        
        # Test runtime calculation
        runtime = host_manager.get_target_runtime()
        print(f"✅ Target runtime: {runtime} minutes")
        
        return True
        
    except Exception as e:
        print(f"❌ Host manager test failed: {e}")
        return False

def test_quality_controller():
    """Test quality controller with sample data"""
    print("\nTesting quality controller...")
    
    try:
        from src.content_validation.quality_controls import quality_controller
        
        # Sample script data
        sample_script = {
            'intro': 'Welcome to Market Voices with Marcus',
            'segments': [
                {
                    'host': 'marcus',
                    'text': 'Today we saw some interesting moves in the market. Apple stock rose significantly.',
                    'topic': 'Market overview'
                },
                {
                    'host': 'suzanne',
                    'text': 'From a trading perspective, this movement suggests strong investor confidence.',
                    'topic': 'Analysis'
                }
            ],
            'outro': 'Thank you for watching Market Voices. This is Marcus, signing off.',
            'estimated_runtime_minutes': 12
        }
        
        # Test quality validation
        results = quality_controller.validate_script_quality(sample_script)
        print(f"✅ Quality validation completed. Score: {results['overall_score']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Quality controller test failed: {e}")
        return False

def test_directory_structure():
    """Test that required directories exist"""
    print("\nTesting directory structure...")
    
    required_dirs = ['src', 'src/config', 'src/data_collection', 'src/script_generation', 'src/content_validation', 'src/utils']
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path} exists")
        else:
            print(f"❌ {dir_path} missing")
            return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("MARKET VOICES - SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        test_directory_structure,
        test_imports,
        test_host_manager,
        test_quality_controller
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! System is ready for setup.")
        print("\nNext steps:")
        print("1. Copy config.env.example to .env")
        print("2. Add your API keys to .env")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Run: python main.py --test")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 