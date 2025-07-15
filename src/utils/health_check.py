"""
Health check utilities for Market Voices production deployment
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List
from pathlib import Path
import requests
from datetime import datetime

from src.config.settings import get_settings
from src.utils.budget_monitor import budget_monitor
from src.utils.cost_analyzer import cost_analyzer

logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health check system for production deployment"""
    
    def __init__(self):
        self.settings = get_settings()
        self.checks = []
        
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "warnings": [],
            "errors": []
        }
        
        check_methods = [
            ("api_keys", self._check_api_keys),
            ("system_resources", self._check_system_resources),
            ("file_permissions", self._check_file_permissions),
            ("monitoring_systems", self._check_monitoring_systems),
            ("dependencies", self._check_dependencies),
            ("configuration", self._check_configuration)
        ]
        
        for check_name, check_method in check_methods:
            try:
                check_result = check_method()
                results["checks"][check_name] = check_result
                
                if check_result["status"] == "error":
                    results["errors"].extend(check_result.get("messages", []))
                    results["overall_status"] = "unhealthy"
                elif check_result["status"] == "warning":
                    results["warnings"].extend(check_result.get("messages", []))
                    if results["overall_status"] == "healthy":
                        results["overall_status"] = "degraded"
                        
            except Exception as e:
                error_msg = f"Health check '{check_name}' failed: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["overall_status"] = "unhealthy"
                results["checks"][check_name] = {
                    "status": "error",
                    "messages": [error_msg]
                }
        
        return results
    
    def _check_api_keys(self) -> Dict[str, Any]:
        """Check API key availability and basic connectivity"""
        result = {
            "status": "healthy",
            "messages": [],
            "details": {}
        }
        
        required_keys = [
            ("OPENAI_API_KEY", self.settings.openai_api_key),
            ("ALPHA_VANTAGE_API_KEY", self.settings.alpha_vantage_api_key),
            ("FMP_API_KEY", self.settings.fmp_api_key),
            ("FINNHUB_API_KEY", self.settings.finnhub_api_key)
        ]
        
        for key_name, key_value in required_keys:
            if not key_value or key_value == "DUMMY":
                result["status"] = "error"
                result["messages"].append(f"Missing or invalid {key_name}")
                result["details"][key_name] = "missing"
            else:
                result["details"][key_name] = "present"
        
        optional_keys = [
            ("THE_NEWS_API_API_KEY", self.settings.the_news_api_api_key),
            ("NEWSAPI_API_KEY", getattr(self.settings, 'newsapi_api_key', '')),
            ("NEWSDATA_IO_API_KEY", getattr(self.settings, 'newsdata_io_api_key', '')),
            ("BIZTOC_API_KEY", getattr(self.settings, 'biztoc_api_key', ''))
        ]
        
        for key_name, key_value in optional_keys:
            if key_value and key_value != "DUMMY":
                result["details"][key_name] = "present"
            else:
                result["details"][key_name] = "missing"
                result["messages"].append(f"Optional {key_name} not configured")
                if result["status"] == "healthy":
                    result["status"] = "warning"
        
        return result
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources and disk space"""
        result = {
            "status": "healthy",
            "messages": [],
            "details": {}
        }
        
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            result["details"]["memory_percent"] = memory.percent
            result["details"]["disk_percent"] = disk.percent
            
            if memory.percent > 90:
                result["status"] = "error"
                result["messages"].append(f"High memory usage: {memory.percent}%")
            elif memory.percent > 80:
                result["status"] = "warning"
                result["messages"].append(f"Elevated memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                result["status"] = "error"
                result["messages"].append(f"High disk usage: {disk.percent}%")
            elif disk.percent > 80:
                result["status"] = "warning"
                result["messages"].append(f"Elevated disk usage: {disk.percent}%")
                
        except ImportError:
            result["status"] = "warning"
            result["messages"].append("psutil not available for system monitoring")
        except Exception as e:
            result["status"] = "warning"
            result["messages"].append(f"System resource check failed: {str(e)}")
        
        return result
    
    def _check_file_permissions(self) -> Dict[str, Any]:
        """Check file permissions for critical files"""
        result = {
            "status": "healthy",
            "messages": [],
            "details": {}
        }
        
        critical_files = [
            ".env",
            "main.py",
            "src/",
            "output/"
        ]
        
        for file_path in critical_files:
            path = Path(file_path)
            if path.exists():
                if path.is_file():
                    readable = os.access(path, os.R_OK)
                    result["details"][file_path] = "readable" if readable else "not_readable"
                    if not readable:
                        result["status"] = "error"
                        result["messages"].append(f"Cannot read {file_path}")
                elif path.is_dir():
                    readable = os.access(path, os.R_OK)
                    writable = os.access(path, os.W_OK)
                    result["details"][file_path] = f"r{'w' if writable else ''}{'x' if os.access(path, os.X_OK) else ''}"
                    if not readable:
                        result["status"] = "error"
                        result["messages"].append(f"Cannot read directory {file_path}")
            else:
                if file_path == "output/":
                    try:
                        os.makedirs(file_path, exist_ok=True)
                        result["details"][file_path] = "created"
                    except Exception as e:
                        result["status"] = "error"
                        result["messages"].append(f"Cannot create {file_path}: {str(e)}")
                else:
                    result["status"] = "warning"
                    result["messages"].append(f"File {file_path} does not exist")
                    result["details"][file_path] = "missing"
        
        return result
    
    def _check_monitoring_systems(self) -> Dict[str, Any]:
        """Check monitoring systems functionality"""
        result = {
            "status": "healthy",
            "messages": [],
            "details": {}
        }
        
        try:
            budget_status = budget_monitor.get_budget_status()
            result["details"]["budget_monitor"] = {
                "status": budget_status["status"],
                "usage_percent": budget_status.get("usage_percent", 0)
            }
            
            if budget_status["status"] == "over_budget":
                result["status"] = "error"
                result["messages"].append("Budget exceeded")
            elif budget_status["status"] == "critical":
                result["status"] = "warning"
                result["messages"].append("Budget usage critical")
                
        except Exception as e:
            result["status"] = "warning"
            result["messages"].append(f"Budget monitor check failed: {str(e)}")
            result["details"]["budget_monitor"] = "error"
        
        try:
            costs = cost_analyzer.calculate_current_costs()
            total_cost = cost_analyzer.get_total_monthly_cost(costs)
            result["details"]["cost_analyzer"] = {
                "total_monthly_cost": total_cost,
                "cost_breakdown": costs
            }
            
        except Exception as e:
            result["status"] = "warning"
            result["messages"].append(f"Cost analyzer check failed: {str(e)}")
            result["details"]["cost_analyzer"] = "error"
        
        return result
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies"""
        result = {
            "status": "healthy",
            "messages": [],
            "details": {}
        }
        
        critical_modules = [
            "openai",
            "requests",
            "pydantic",
            "dotenv",
            "yfinance"
        ]
        
        for module in critical_modules:
            try:
                __import__(module)
                result["details"][module] = "available"
            except ImportError:
                result["status"] = "error"
                result["messages"].append(f"Missing critical module: {module}")
                result["details"][module] = "missing"
        
        return result
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity"""
        result = {
            "status": "healthy",
            "messages": [],
            "details": {}
        }
        
        try:
            nasdaq_symbols = self.settings.get_nasdaq_symbols_list()
            result["details"]["nasdaq_symbols_count"] = len(nasdaq_symbols)
            
            if len(nasdaq_symbols) < 50:
                result["status"] = "warning"
                result["messages"].append(f"Low NASDAQ symbol count: {len(nasdaq_symbols)}")
            
            result["details"]["market_open_time"] = str(self.settings.market_open_time)
            result["details"]["market_close_time"] = str(self.settings.market_close_time)
            
        except Exception as e:
            result["status"] = "error"
            result["messages"].append(f"Configuration validation failed: {str(e)}")
        
        return result

def run_health_check() -> Dict[str, Any]:
    """Run comprehensive health check and return results"""
    checker = HealthChecker()
    return checker.run_all_checks()

def print_health_status(results: Dict[str, Any]) -> None:
    """Print formatted health check results"""
    status_colors = {
        "healthy": "\033[92m",
        "degraded": "\033[93m", 
        "unhealthy": "\033[91m"
    }
    reset_color = "\033[0m"
    
    status = results["overall_status"]
    color = status_colors.get(status, "")
    
    print(f"\n{color}=== Market Voices Health Check ==={reset_color}")
    print(f"Status: {color}{status.upper()}{reset_color}")
    print(f"Timestamp: {results['timestamp']}")
    
    if results["errors"]:
        print(f"\n{status_colors['unhealthy']}ERRORS:{reset_color}")
        for error in results["errors"]:
            print(f"  ❌ {error}")
    
    if results["warnings"]:
        print(f"\n{status_colors['degraded']}WARNINGS:{reset_color}")
        for warning in results["warnings"]:
            print(f"  ⚠️  {warning}")
    
    print(f"\n{color}CHECK DETAILS:{reset_color}")
    for check_name, check_result in results["checks"].items():
        status_icon = "✅" if check_result["status"] == "healthy" else "⚠️" if check_result["status"] == "warning" else "❌"
        print(f"  {status_icon} {check_name}: {check_result['status']}")
    
    print()

if __name__ == "__main__":
    results = run_health_check()
    print_health_status(results)
    
    if results["overall_status"] == "unhealthy":
        sys.exit(1)
    elif results["overall_status"] == "degraded":
        sys.exit(2)
    else:
        sys.exit(0)
