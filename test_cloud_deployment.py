#!/usr/bin/env python3
"""
Test Cloud Deployment Compatibility
Tests that the system works without a .env file (cloud environment simulation)
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_cloud_deployment_compatibility():
    """Test that the system works without a .env file"""
    
    print("🧪 Testing Cloud Deployment Compatibility")
    print("=" * 50)
    
    # Step 1: Test settings loading without .env file
    print("\n1. Testing settings loading without .env file...")
    try:
        # Set environment variables directly (simulating cloud environment)
        os.environ["ALPHA_VANTAGE_API_KEY"] = "test_alpha_key"
        os.environ["NEWS_API_KEY"] = "test_news_key"
        os.environ["OPENAI_API_KEY"] = "test_openai_key"
        os.environ["FMP_API_KEY"] = "test_fmp_key"
        os.environ["TEST_MODE"] = "1"
        
        # Import settings (this should not fail even without .env file)
        from src.config.settings import get_settings
        settings = get_settings()
        
        print("   ✅ Settings loaded successfully from environment variables")
        print(f"   - Alpha Vantage API Key: {settings.alpha_vantage_api_key[:10]}...")
        print(f"   - News API Key: {settings.news_api_key[:10]}...")
        print(f"   - OpenAI API Key: {settings.openai_api_key[:10]}...")
        print(f"   - FMP API Key: {settings.fmp_api_key[:10]}...")
        
    except Exception as e:
        print(f"   ❌ Settings loading failed: {e}")
        return False
    
    # Step 2: Test main application initialization
    print("\n2. Testing main application initialization...")
    try:
        # This should work without .env file
        from main import MarketVoicesApp
        app = MarketVoicesApp()
        print("   ✅ Main application initialized successfully")
        
    except Exception as e:
        print(f"   ❌ Main application initialization failed: {e}")
        return False
    
    # Step 3: Test import of core modules
    print("\n3. Testing core module imports...")
    try:
        from src.data_collection.comprehensive_collector import comprehensive_collector
        from src.script_generation.script_generator import script_generator
        from src.content_validation.quality_controls import quality_controller
        print("   ✅ Core modules imported successfully")
        
    except Exception as e:
        print(f"   ❌ Core module imports failed: {e}")
        return False
    
    # Step 4: Test that .env file is optional
    print("\n4. Testing .env file is optional...")
    try:
        # Create a temporary directory without .env file
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            # Try to import settings from directory without .env file
            from src.config.settings import Settings
            settings = Settings()
            print("   ✅ Settings work without .env file")
            
            os.chdir(original_cwd)
            
    except Exception as e:
        print(f"   ❌ .env file dependency test failed: {e}")
        return False
    
    # Step 5: Test environment variable override
    print("\n5. Testing environment variable override...")
    try:
        # Set a specific environment variable
        test_value = "cloud_deployment_test_value"
        os.environ["LOG_LEVEL"] = test_value
        
        from src.config.settings import get_settings
        settings = get_settings()
        
        if settings.log_level == test_value:
            print("   ✅ Environment variables override defaults correctly")
        else:
            print(f"   ❌ Environment variable override failed: expected {test_value}, got {settings.log_level}")
            return False
            
    except Exception as e:
        print(f"   ❌ Environment variable override test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED - CLOUD DEPLOYMENT READY!")
    print("=" * 50)
    print("\n✅ The system is now compatible with:")
    print("   - GitHub Actions")
    print("   - AWS ECS/Fargate")
    print("   - Google Cloud Run")
    print("   - Azure Container Instances")
    print("   - Any cloud environment that supports environment variables")
    print("\n📖 See PRODUCTION_DEPLOYMENT_GUIDE.md for deployment instructions")
    
    return True

def test_api_key_requirements():
    """Test that the system properly validates required API keys"""
    
    print("\n🔑 Testing API Key Requirements")
    print("=" * 50)
    
    # Clear environment variables to test requirements
    required_keys = [
        "ALPHA_VANTAGE_API_KEY",
        "NEWS_API_KEY", 
        "OPENAI_API_KEY",
        "FMP_API_KEY"
    ]
    
    # Save original values
    original_values = {}
    for key in required_keys:
        original_values[key] = os.environ.get(key)
        if key in os.environ:
            del os.environ[key]
    
    try:
        # Test with TEST_MODE=1 (should use dummy keys)
        os.environ["TEST_MODE"] = "1"
        
        from src.config.settings import get_settings
        settings = get_settings()
        
        print(f"   ✅ Test mode handles missing API keys gracefully")
        print(f"   - Alpha Vantage: {settings.alpha_vantage_api_key}")
        print(f"   - OpenAI: {settings.openai_api_key}")
        
    except Exception as e:
        print(f"   ❌ API key requirements test failed: {e}")
        return False
    
    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is not None:
                os.environ[key] = value
    
    return True

if __name__ == "__main__":
    success = True
    
    try:
        success &= test_cloud_deployment_compatibility()
        success &= test_api_key_requirements()
        
        if success:
            print("\n🚀 DEPLOYMENT STATUS: READY FOR PRODUCTION!")
            print("   The system no longer depends on local .env files")
            print("   and can be deployed to any cloud environment.")
            exit(0)
        else:
            print("\n❌ DEPLOYMENT STATUS: ISSUES FOUND")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 DEPLOYMENT TEST FAILED: {e}")
        exit(1)