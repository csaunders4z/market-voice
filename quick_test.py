#!/usr/bin/env python3
"""
Quick Test Script for Market Voices
Run this after any major changes to verify core functionality
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import get_settings
from src.config.security import security_config
from src.config.logging_config import secure_logging
from src.utils.logger import get_logger
from src.script_generation.host_manager import host_manager
from src.content_validation.quality_controls import quality_controller


def test_imports():
    """Test that all critical modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test core imports
        from src.data_collection.stock_data import stock_collector
        from src.script_generation.script_generator import script_generator
        from src.data_collection.unified_data_collector import unified_collector
        from src.data_collection.news_collector import news_collector
        from src.data_collection.free_news_sources import free_news_collector
        
        print("✅ All core modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False


def test_configuration():
    """Test configuration loading"""
    print("⚙️  Testing configuration...")
    
    try:
        settings = get_settings()
        
        # Check critical settings
        required_settings = [
            'openai_api_key', 'openai_model', 'max_tokens', 'temperature',
            'target_runtime_minutes', 'output_directory'
        ]
        
        for setting in required_settings:
            if not hasattr(settings, setting):
                print(f"❌ Missing required setting: {setting}")
                return False
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False


def test_security():
    """Test security configuration"""
    print("🔒 Testing security configuration...")
    
    try:
        # Run security audit
        audit_results = security_config.run_security_audit()
        
        if audit_results['recommendations']:
            print(f"⚠️  Security warnings found: {len(audit_results['recommendations'])}")
            for rec in audit_results['recommendations']:
                print(f"   - {rec}")
            return False
        else:
            print("✅ Security audit passed")
            return True
    except Exception as e:
        print(f"❌ Security test failed: {str(e)}")
        return False


def test_logging():
    """Test logging configuration"""
    print("📝 Testing logging configuration...")
    
    try:
        # Setup secure logging
        secure_logging.setup_logging(log_level="INFO", enable_file_logging=False)
        
        # Test logger
        logger = get_logger("QuickTest")
        logger.info("Test log message")
        
        # Get log stats
        stats = secure_logging.get_log_stats()
        
        print("✅ Logging configuration working")
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {str(e)}")
        return False


def test_host_manager():
    """Test host manager functionality"""
    print("🎭 Testing host manager...")
    
    try:
        # Test host info retrieval
        marcus_info = host_manager.get_host_info('marcus')
        suzanne_info = host_manager.get_host_info('suzanne')
        
        if not marcus_info or not suzanne_info:
            print("❌ Host info retrieval failed")
            return False
        
        # Test lead host determination
        lead_host = host_manager.get_lead_host_for_date()
        if lead_host not in ['marcus', 'suzanne']:
            print(f"❌ Invalid lead host: {lead_host}")
            return False
        
        print("✅ Host manager working correctly")
        return True
    except Exception as e:
        print(f"❌ Host manager test failed: {str(e)}")
        return False


def test_quality_controller():
    """Test quality controller with sample data"""
    print("📊 Testing quality controller...")
    
    try:
        # Create sample script data
        sample_script = {
            'intro': 'Test intro',
            'segments': [
                {
                    'host': 'marcus',
                    'text': 'Test segment 1',
                    'topic': 'Test Topic',
                    'word_count': 100
                },
                {
                    'host': 'suzanne',
                    'text': 'Test segment 2',
                    'topic': 'Test Topic 2',
                    'word_count': 100
                }
            ],
            'outro': 'Test outro',
            'estimated_runtime_minutes': 12,
            'speaking_time_balance': {
                'marcus_percentage': 50,
                'suzanne_percentage': 50
            }
        }
        
        # Run quality validation
        results = quality_controller.validate_script_quality(sample_script)
        
        if 'overall_score' not in results:
            print("❌ Quality validation failed")
            return False
        
        print(f"✅ Quality controller working (score: {results['overall_score']:.1f}%)")
        return True
    except Exception as e:
        print(f"❌ Quality controller test failed: {str(e)}")
        return False


def test_dependencies():
    """Test critical dependencies"""
    print("📦 Testing dependencies...")
    
    try:
        # Test OpenAI
        import openai
        print("✅ OpenAI package available")
        
        # Test pandas
        import pandas as pd
        print("✅ Pandas package available")
        
        # Test yfinance
        import yfinance as yf
        print("✅ YFinance package available")
        
        # Test loguru
        from loguru import logger
        print("✅ Loguru package available")
        
        # Test pydantic
        from pydantic import BaseModel
        print("✅ Pydantic package available")
        
        return True
    except ImportError as e:
        print(f"❌ Dependency test failed: {str(e)}")
        return False


def main():
    """Run all quick tests"""
    print("🚀 MARKET VOICES - QUICK TEST")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Security", test_security),
        ("Logging", test_logging),
        ("Host Manager", test_host_manager),
        ("Quality Controller", test_quality_controller),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY:")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review before production.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 