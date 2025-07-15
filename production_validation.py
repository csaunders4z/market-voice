#!/usr/bin/env python3
"""
Production validation script for Market Voices deployment
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import get_settings
from src.utils.health_check import run_health_check, print_health_status
from src.utils.budget_monitor import budget_monitor
from src.utils.cost_analyzer import cost_analyzer
from main import MarketVoicesApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionValidator:
    """Comprehensive production validation system"""
    
    def __init__(self):
        self.settings = get_settings()
        self.validation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "pass",
            "tests": {},
            "errors": [],
            "warnings": []
        }
    
    def run_all_validations(self) -> dict:
        """Run all production validation tests"""
        print("=" * 60)
        print("MARKET VOICES PRODUCTION VALIDATION")
        print("=" * 60)
        
        validation_tests = [
            ("health_check", self._validate_health_check),
            ("api_connectivity", self._validate_api_connectivity),
            ("monitoring_systems", self._validate_monitoring_systems),
            ("script_generation", self._validate_script_generation),
            ("cost_tracking", self._validate_cost_tracking),
            ("file_operations", self._validate_file_operations),
            ("configuration", self._validate_configuration)
        ]
        
        for test_name, test_method in validation_tests:
            print(f"\n🔍 Running {test_name} validation...")
            try:
                result = test_method()
                self.validation_results["tests"][test_name] = result
                
                if result["status"] == "fail":
                    self.validation_results["overall_status"] = "fail"
                    self.validation_results["errors"].extend(result.get("messages", []))
                    print(f"❌ {test_name}: FAILED")
                elif result["status"] == "warning":
                    self.validation_results["warnings"].extend(result.get("messages", []))
                    print(f"⚠️  {test_name}: WARNING")
                else:
                    print(f"✅ {test_name}: PASSED")
                    
            except Exception as e:
                error_msg = f"{test_name} validation failed: {str(e)}"
                logger.error(error_msg)
                self.validation_results["errors"].append(error_msg)
                self.validation_results["overall_status"] = "fail"
                self.validation_results["tests"][test_name] = {
                    "status": "fail",
                    "messages": [error_msg]
                }
                print(f"❌ {test_name}: ERROR - {str(e)}")
        
        return self.validation_results
    
    def _validate_health_check(self) -> dict:
        """Validate health check system"""
        health_results = run_health_check()
        
        if health_results["overall_status"] == "unhealthy":
            return {
                "status": "fail",
                "messages": health_results["errors"],
                "details": health_results
            }
        elif health_results["overall_status"] == "degraded":
            return {
                "status": "warning", 
                "messages": health_results["warnings"],
                "details": health_results
            }
        else:
            return {
                "status": "pass",
                "messages": ["Health check system operational"],
                "details": health_results
            }
    
    def _validate_api_connectivity(self) -> dict:
        """Validate API connectivity"""
        result = {
            "status": "pass",
            "messages": [],
            "details": {}
        }
        
        required_apis = [
            ("OpenAI", self.settings.openai_api_key),
            ("Alpha Vantage", self.settings.alpha_vantage_api_key),
            ("FMP", self.settings.fmp_api_key),
            ("Finnhub", self.settings.finnhub_api_key)
        ]
        
        for api_name, api_key in required_apis:
            if not api_key or api_key == "DUMMY":
                result["status"] = "fail"
                result["messages"].append(f"Missing {api_name} API key")
                result["details"][api_name] = "missing"
            else:
                result["details"][api_name] = "configured"
        
        try:
            import requests
            
            response = requests.get("https://httpbin.org/status/200", timeout=10)
            if response.status_code == 200:
                result["details"]["internet_connectivity"] = "available"
            else:
                result["status"] = "warning"
                result["messages"].append("Internet connectivity issues")
                result["details"]["internet_connectivity"] = "limited"
                
        except Exception as e:
            result["status"] = "fail"
            result["messages"].append(f"Network connectivity failed: {str(e)}")
            result["details"]["internet_connectivity"] = "failed"
        
        return result
    
    def _validate_monitoring_systems(self) -> dict:
        """Validate monitoring systems"""
        result = {
            "status": "pass",
            "messages": [],
            "details": {}
        }
        
        try:
            budget_status = budget_monitor.get_budget_status()
            result["details"]["budget_monitor"] = budget_status
            
            if budget_status["status"] == "over_budget":
                result["status"] = "fail"
                result["messages"].append("Budget exceeded")
            elif budget_status["status"] == "critical":
                result["status"] = "warning"
                result["messages"].append("Budget usage critical")
            
        except Exception as e:
            result["status"] = "fail"
            result["messages"].append(f"Budget monitor failed: {str(e)}")
        
        try:
            costs = cost_analyzer.calculate_current_costs()
            total_cost = cost_analyzer.get_total_monthly_cost(costs)
            result["details"]["cost_analyzer"] = {
                "total_monthly_cost": total_cost,
                "cost_breakdown": costs
            }
            
        except Exception as e:
            result["status"] = "fail"
            result["messages"].append(f"Cost analyzer failed: {str(e)}")
        
        return result
    
    def _validate_script_generation(self) -> dict:
        """Validate script generation capability"""
        result = {
            "status": "pass",
            "messages": [],
            "details": {}
        }
        
        try:
            from src.script_generation.script_generator import ScriptGenerator
            script_generator = ScriptGenerator()
            
            requirements_path = Path("planning/script_generation_requirements.md")
            if requirements_path.exists():
                result["details"]["requirements_file"] = "available"
            else:
                result["status"] = "warning"
                result["messages"].append("Script generation requirements file missing")
                result["details"]["requirements_file"] = "missing"
            
            from src.script_generation.host_manager import HostManager
            host_manager = HostManager()
            lead_host = host_manager.get_lead_host_for_date(datetime.now().date())
            result["details"]["host_system"] = f"lead_host_{lead_host}"
            
        except Exception as e:
            result["status"] = "fail"
            result["messages"].append(f"Script generation validation failed: {str(e)}")
        
        return result
    
    def _validate_cost_tracking(self) -> dict:
        """Validate cost tracking functionality"""
        result = {
            "status": "pass",
            "messages": [],
            "details": {}
        }
        
        try:
            costs = cost_analyzer.calculate_current_costs()
            total_cost = cost_analyzer.get_total_monthly_cost(costs)
            
            result["details"]["current_costs"] = costs
            result["details"]["total_monthly_cost"] = total_cost
            
            budget_status = budget_monitor.get_budget_status()
            result["details"]["budget_status"] = budget_status
            
            cost_files = [
                "cost_data.json",
                "budget_alerts.json"
            ]
            
            for file_name in cost_files:
                if Path(file_name).exists():
                    result["details"][f"{file_name}_exists"] = True
                else:
                    result["details"][f"{file_name}_exists"] = False
            
        except Exception as e:
            result["status"] = "fail"
            result["messages"].append(f"Cost tracking validation failed: {str(e)}")
        
        return result
    
    def _validate_file_operations(self) -> dict:
        """Validate file operations"""
        result = {
            "status": "pass",
            "messages": [],
            "details": {}
        }
        
        output_dir = Path("output")
        try:
            output_dir.mkdir(exist_ok=True)
            result["details"]["output_directory"] = "created"
            
            test_file = output_dir / "test_write.txt"
            test_file.write_text("test")
            test_file.unlink()
            result["details"]["write_permissions"] = "ok"
            
        except Exception as e:
            result["status"] = "fail"
            result["messages"].append(f"File operations failed: {str(e)}")
        
        critical_files = [".env", "main.py", "requirements.txt"]
        for file_name in critical_files:
            if Path(file_name).exists():
                result["details"][f"{file_name}_exists"] = True
            else:
                result["status"] = "fail"
                result["messages"].append(f"Critical file missing: {file_name}")
                result["details"][f"{file_name}_exists"] = False
        
        return result
    
    def _validate_configuration(self) -> dict:
        """Validate configuration"""
        result = {
            "status": "pass",
            "messages": [],
            "details": {}
        }
        
        try:
            nasdaq_symbols = self.settings.get_nasdaq_symbols_list()
            result["details"]["nasdaq_symbols_count"] = len(nasdaq_symbols)
            
            if len(nasdaq_symbols) < 50:
                result["status"] = "warning"
                result["messages"].append(f"Low NASDAQ symbol count: {len(nasdaq_symbols)}")
            
            result["details"]["market_hours"] = {
                "open": str(self.settings.market_open_time),
                "close": str(self.settings.market_close_time)
            }
            
        except Exception as e:
            result["status"] = "fail"
            result["messages"].append(f"Configuration validation failed: {str(e)}")
        
        return result
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        status_colors = {
            "pass": "\033[92m",
            "fail": "\033[91m",
            "warning": "\033[93m"
        }
        reset_color = "\033[0m"
        
        status = self.validation_results["overall_status"]
        color = status_colors.get(status, "")
        
        print(f"Overall Status: {color}{status.upper()}{reset_color}")
        print(f"Timestamp: {self.validation_results['timestamp']}")
        
        if self.validation_results["errors"]:
            print(f"\n{status_colors['fail']}ERRORS:{reset_color}")
            for error in self.validation_results["errors"]:
                print(f"  ❌ {error}")
        
        if self.validation_results["warnings"]:
            print(f"\n{status_colors['warning']}WARNINGS:{reset_color}")
            for warning in self.validation_results["warnings"]:
                print(f"  ⚠️  {warning}")
        
        print(f"\n{color}TEST RESULTS:{reset_color}")
        for test_name, test_result in self.validation_results["tests"].items():
            status_icon = "✅" if test_result["status"] == "pass" else "⚠️" if test_result["status"] == "warning" else "❌"
            print(f"  {status_icon} {test_name}: {test_result['status']}")
        
        print("\n" + "=" * 60)
    
    def save_results(self, filename: str = None):
        """Save validation results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"production_validation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        print(f"Validation results saved to {filename}")

def main():
    """Main validation entry point"""
    validator = ProductionValidator()
    
    try:
        results = validator.run_all_validations()
        validator.print_summary()
        validator.save_results()
        
        if results["overall_status"] == "fail":
            print("\n❌ Production validation FAILED")
            return 1
        elif results["overall_status"] == "warning":
            print("\n⚠️  Production validation completed with WARNINGS")
            return 2
        else:
            print("\n✅ Production validation PASSED")
            return 0
            
    except Exception as e:
        print(f"\n❌ Production validation ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
