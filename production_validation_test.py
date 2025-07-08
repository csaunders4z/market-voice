#!/usr/bin/env python3
"""
Production Validation Test for Market Voices
Comprehensive end-to-end testing of the complete system
"""
import sys
import os
import time
from datetime import datetime
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.data_collection.unified_data_collector import UnifiedDataCollector
from src.script_generation.script_generator import ScriptGenerator
from src.utils.cost_analyzer import cost_analyzer
from src.utils.budget_monitor import budget_monitor
from src.config.settings import get_settings

class ProductionValidator:
    """Validates complete system functionality for production readiness"""
    
    def __init__(self):
        self.settings = get_settings()
        self.start_time = None
        self.end_time = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "performance": {},
            "costs": {},
            "quality": {},
            "errors": [],
            "warnings": [],
            "output": {}  # Ensure output is always a dict
        }
        
        # Initialize components
        self.data_collector = UnifiedDataCollector()
        self.script_generator = ScriptGenerator()
        
        # Test configuration
        self.test_config = {
            "max_symbols": 50,  # Test with 50 symbols for cost control
            "target_processing_time": 300,  # 5 minutes
            "target_quality_score": 80,
            "max_cost": 10.0  # $10 maximum for test run
        }
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "PASS":
            logger.info(f"✅ {test_name}: PASS - {details}")
        elif status == "FAIL":
            logger.error(f"❌ {test_name}: FAIL - {details}")
            self.results["errors"].append(f"{test_name}: {details}")
        elif status == "WARNING":
            logger.warning(f"⚠️ {test_name}: WARNING - {details}")
            self.results["warnings"].append(f"{test_name}: {details}")
    
    def test_api_keys(self):
        """Test API key configuration"""
        logger.info("🔑 Testing API key configuration...")
        
        # Check OpenAI API key
        if not self.settings.openai_api_key or self.settings.openai_api_key == "DUMMY":
            self.log_test("API Keys - OpenAI", "FAIL", "OpenAI API key not configured")
            return False
        
        # Check FMP API key
        if not self.settings.fmp_api_key:
            self.log_test("API Keys - FMP", "WARNING", "FMP API key not configured")
        
        # Check News API key
        if not self.settings.news_api_key:
            self.log_test("API Keys - NewsAPI", "WARNING", "NewsAPI key not configured")
        
        self.log_test("API Keys - OpenAI", "PASS", "OpenAI API key configured")
        return True
    
    def test_data_collection(self):
        """Test data collection functionality"""
        logger.info("📊 Testing data collection...")
        
        try:
            # Get symbols for testing
            from src.data_collection.symbol_loader import symbol_loader
            symbols = symbol_loader.get_all_symbols()[:self.test_config["max_symbols"]]
            
            logger.info(f"Collecting data for {len(symbols)} symbols...")
            
            # Collect data
            collection_start = time.time()
            data_result = self.data_collector.collect_data(symbols=symbols, production_mode=True)
            collection_time = time.time() - collection_start
            
            # Validate results
            if not data_result.get('collection_success', False):
                self.log_test("Data Collection", "FAIL", f"Collection failed: {data_result.get('error', 'Unknown error')}")
                return False
            
            stock_data = data_result.get('all_data', [])
            if not stock_data:
                self.log_test("Data Collection", "FAIL", "No stock data collected")
                return False
            
            # Performance validation
            if collection_time > self.test_config["target_processing_time"]:
                self.log_test("Data Collection Performance", "WARNING", 
                            f"Collection time {collection_time:.1f}s exceeds target {self.test_config['target_processing_time']}s")
            else:
                self.log_test("Data Collection Performance", "PASS", 
                            f"Collection time {collection_time:.1f}s within target")
            
            # Data quality validation
            successful_collections = len(stock_data)
            success_rate = (successful_collections / len(symbols)) * 100
            
            if success_rate < 80:
                self.log_test("Data Collection Quality", "WARNING", 
                            f"Success rate {success_rate:.1f}% below 80% target")
            else:
                self.log_test("Data Collection Quality", "PASS", 
                            f"Success rate {success_rate:.1f}% meets target")
            
            self.log_test("Data Collection", "PASS", 
                         f"Collected data for {successful_collections}/{len(symbols)} symbols in {collection_time:.1f}s")
            
            # Store results
            self.results["performance"]["data_collection_time"] = collection_time
            self.results["performance"]["data_collection_success_rate"] = success_rate
            self.results["performance"]["symbols_collected"] = successful_collections
            
            return data_result
            
        except Exception as e:
            self.log_test("Data Collection", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_news_integration(self, data_result):
        """Test news integration"""
        logger.info("📰 Testing news integration...")
        
        try:
            stock_data = data_result.get('all_data', [])
            if not stock_data:
                self.log_test("News Integration", "FAIL", "No stock data available for news testing")
                return False
            
            # Check if news data is present
            stocks_with_news = 0
            total_news_articles = 0
            
            for stock in stock_data:
                if stock.get('news_articles'):
                    stocks_with_news += 1
                    total_news_articles += len(stock['news_articles'])
            
            news_coverage = (stocks_with_news / len(stock_data)) * 100 if stock_data else 0
            
            if news_coverage < 50:
                self.log_test("News Integration", "WARNING", 
                            f"News coverage {news_coverage:.1f}% below 50% target")
            else:
                self.log_test("News Integration", "PASS", 
                            f"News coverage {news_coverage:.1f}% meets target")
            
            self.log_test("News Articles", "PASS", 
                         f"Total {total_news_articles} news articles for {stocks_with_news} stocks")
            
            # Store results
            self.results["quality"]["news_coverage"] = news_coverage
            self.results["quality"]["total_news_articles"] = total_news_articles
            
            return True
            
        except Exception as e:
            self.log_test("News Integration", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_script_generation(self, data_result):
        """Test script generation"""
        logger.info("📝 Testing script generation...")
        
        try:
            # Generate script
            generation_start = time.time()
            script_result = self.script_generator.generate_script(data_result)
            generation_time = time.time() - generation_start
            
            if not script_result.get('generation_success', False):
                self.log_test("Script Generation", "FAIL", 
                            f"Generation failed: {script_result.get('error', 'Unknown error')}")
                return False
            
            # Validate script content - extract from segments
            script_content = ""
            segments = script_result.get('segments', [])
            if segments:
                script_content = " ".join([seg.get('text', '') for seg in segments])
            
            if not script_content:
                self.log_test("Script Generation", "FAIL", "No script content generated")
                return False
            
            # Performance validation
            if generation_time > 300:  # 5 minutes
                self.log_test("Script Generation Performance", "WARNING", 
                            f"Generation time {generation_time:.1f}s exceeds 5-minute target")
            else:
                self.log_test("Script Generation Performance", "PASS", 
                            f"Generation time {generation_time:.1f}s within target")
            
            # Quality validation
            word_count = len(script_content.split())
            quality_score = script_result.get('quality_validation', {}).get('overall_score', 0)
            
            if quality_score < self.test_config["target_quality_score"]:
                self.log_test("Script Quality", "WARNING", 
                            f"Quality score {quality_score}% below {self.test_config['target_quality_score']}% target")
            else:
                self.log_test("Script Quality", "PASS", 
                            f"Quality score {quality_score}% meets target")
            
            if word_count < 500:
                self.log_test("Script Content", "WARNING", 
                            f"Script length {word_count} words below 500 target")
            else:
                self.log_test("Script Content", "PASS", 
                            f"Script length {word_count} words meets target")
            
            self.log_test("Script Generation", "PASS", 
                         f"Generated {word_count}-word script with {quality_score}% quality in {generation_time:.1f}s")
            
            # Store results
            self.results["performance"]["script_generation_time"] = generation_time
            self.results["quality"]["script_quality_score"] = quality_score
            self.results["quality"]["script_word_count"] = word_count
            self.results["output"]["script_content"] = script_content[:500] + "..." if len(script_content) > 500 else script_content
            
            return script_result
            
        except Exception as e:
            self.log_test("Script Generation", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_cost_tracking(self):
        """Test cost tracking functionality"""
        logger.info("💰 Testing cost tracking...")
        
        try:
            # Calculate projected costs
            costs = cost_analyzer.calculate_current_costs()
            total_cost = cost_analyzer.get_total_monthly_cost(costs)
            
            # Track test costs
            test_cost = total_cost / 30  # Daily cost
            budget_monitor.track_daily_usage(test_cost)
            
            if test_cost > self.test_config["max_cost"]:
                self.log_test("Cost Tracking", "WARNING", 
                            f"Test cost ${test_cost:.2f} exceeds ${self.test_config['max_cost']} limit")
            else:
                self.log_test("Cost Tracking", "PASS", 
                            f"Test cost ${test_cost:.2f} within budget")
            
            # Store results
            self.results["costs"]["projected_monthly_cost"] = total_cost
            self.results["costs"]["test_cost"] = test_cost
            self.results["costs"]["cost_breakdown"] = {
                api: {"monthly_cost": cost.monthly_cost, "requests_per_month": cost.requests_per_month}
                for api, cost in costs.items()
            }
            
            return True
            
        except Exception as e:
            self.log_test("Cost Tracking", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling and recovery"""
        logger.info("🛡️ Testing error handling...")
        
        try:
            # Test with invalid symbols
            invalid_symbols = ["INVALID1", "INVALID2", "INVALID3"]
            
            # This should not crash the system
            result = self.data_collector.collect_data(symbols=invalid_symbols, production_mode=True)
            
            if result.get('collection_success', False):
                self.log_test("Error Handling", "PASS", "System handled invalid symbols gracefully")
            else:
                self.log_test("Error Handling", "PASS", "System properly rejected invalid symbols")
            
            return True
            
        except Exception as e:
            self.log_test("Error Handling", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_output_validation(self, script_result):
        """Test output validation"""
        logger.info("📋 Testing output validation...")
        
        try:
            # Extract script content from segments
            script_content = ""
            segments = script_result.get('segments', [])
            if segments:
                script_content = " ".join([seg.get('text', '') for seg in segments])
            
            # Check for required sections
            required_sections = ['winners', 'losers', 'market']
            missing_sections = []
            
            for section in required_sections:
                if section.lower() not in script_content.lower():
                    missing_sections.append(section)
            
            if missing_sections:
                self.log_test("Output Validation", "WARNING", 
                            f"Missing sections: {', '.join(missing_sections)}")
            else:
                self.log_test("Output Validation", "PASS", "All required sections present")
            
            # Check for stock mentions
            stock_mentions = sum(1 for char in script_content if char.isupper() and len(char) <= 5)
            if stock_mentions < 5:
                self.log_test("Output Content", "WARNING", 
                            f"Only {stock_mentions} potential stock mentions found")
            else:
                self.log_test("Output Content", "PASS", 
                            f"Found {stock_mentions} potential stock mentions")
            
            # Save output
            output_file = Path("output/production_validation_script.txt")
            output_file.parent.mkdir(exist_ok=True)
            
            quality_score = script_result.get('quality_validation', {}).get('overall_score', 0)
            
            with open(output_file, 'w') as f:
                f.write(f"# Market Voices Production Validation Script\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Quality Score: {quality_score}%\n")
                f.write(f"# Word Count: {len(script_content.split())}\n\n")
                f.write(script_content)
            
            self.log_test("Output Saving", "PASS", f"Script saved to {output_file}")
            
            return True
            
        except Exception as e:
            self.log_test("Output Validation", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_full_validation(self):
        """Run complete production validation"""
        logger.info("🚀 Starting Production Validation Test")
        logger.info("=" * 60)
        
        self.start_time = time.time()
        
        # Test 1: API Keys
        if not self.test_api_keys():
            logger.error("❌ API key test failed. Cannot proceed.")
            return False
        
        # Test 2: Data Collection
        data_result = self.test_data_collection()
        if not data_result:
            logger.error("❌ Data collection test failed. Cannot proceed.")
            return False
        
        # Test 3: News Integration
        if not self.test_news_integration(data_result):
            logger.warning("⚠️ News integration test failed, but continuing...")
        
        # Test 4: Script Generation
        script_result = self.test_script_generation(data_result)
        if not script_result:
            logger.error("❌ Script generation test failed.")
            return False
        
        # Test 5: Cost Tracking
        if not self.test_cost_tracking():
            logger.warning("⚠️ Cost tracking test failed, but continuing...")
        
        # Test 6: Error Handling
        if not self.test_error_handling():
            logger.warning("⚠️ Error handling test failed, but continuing...")
        
        # Test 7: Output Validation
        if not self.test_output_validation(script_result):
            logger.warning("⚠️ Output validation test failed, but continuing...")
        
        self.end_time = time.time()
        total_time = self.end_time - self.start_time
        
        # Final validation
        self.results["performance"]["total_validation_time"] = total_time
        self.results["summary"] = self.generate_summary()
        
        # Save results
        self.save_results()
        
        # Display summary
        self.display_summary()
        
        return True
    
    def generate_summary(self):
        """Generate validation summary"""
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for test in self.results["tests"].values() if test["status"] == "PASS")
        failed_tests = sum(1 for test in self.results["tests"].values() if test["status"] == "FAIL")
        warning_tests = sum(1 for test in self.results["tests"].values() if test["status"] == "WARNING")
        
        overall_status = "PASS" if failed_tests == 0 else "FAIL"
        
        return {
            "overall_status": overall_status,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "warning_tests": warning_tests,
            "total_time": self.results["performance"]["total_validation_time"],
            "errors": len(self.results["errors"]),
            "warnings": len(self.results["warnings"])
        }
    
    def save_results(self):
        """Save validation results"""
        results_file = Path("logs/production_validation_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📄 Validation results saved to {results_file}")
    
    def display_summary(self):
        """Display validation summary"""
        summary = self.results["summary"]
        
        print("\n" + "=" * 60)
        print("           PRODUCTION VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Warnings: {summary['warning_tests']} ⚠️")
        print(f"Total Time: {summary['total_time']:.1f} seconds")
        print(f"Errors: {summary['errors']}")
        print(f"Warnings: {summary['warnings']}")
        
        if summary['overall_status'] == "PASS":
            print("\n🎉 PRODUCTION VALIDATION PASSED!")
            print("The system is ready for production deployment.")
        else:
            print("\n❌ PRODUCTION VALIDATION FAILED!")
            print("Please address the issues before deployment.")
        
        print("=" * 60)


def main():
    """Run production validation"""
    validator = ProductionValidator()
    
    try:
        success = validator.run_full_validation()
        return success
    except Exception as e:
        logger.error(f"Validation failed with exception: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 