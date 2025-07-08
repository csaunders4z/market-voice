"""
Budget Monitor for Market Voices
Tracks API costs and provides alerts when approaching budget limits
"""
import time
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config.settings import get_settings
from .cost_analyzer import cost_analyzer


class BudgetMonitor:
    """Monitors API costs and provides budget alerts"""
    
    def __init__(self):
        self.settings = get_settings()
        self.budget_data_file = Path("logs/budget_data.json")
        self.budget_data_file.parent.mkdir(exist_ok=True)
        
        # Budget configuration
        self.budget_config = {
            "monthly_budget": 50.0,  # $50/month default
            "warning_threshold": 0.8,  # 80% of budget
            "critical_threshold": 0.95,  # 95% of budget
            "daily_budget": 1.67,  # $50/30 days
            "weekly_budget": 11.67,  # $50/4.29 weeks
            "enable_alerts": True,
            "alert_email": None,  # Set via environment variable
            "alert_webhook": None  # Set via environment variable
        }
        
        # Load budget configuration from environment
        self._load_budget_config()
        
        # Alert history
        self.alert_history = []
    
    def _load_budget_config(self):
        """Load budget configuration from environment variables"""
        env_budget = os.getenv("MONTHLY_BUDGET")
        if env_budget:
            try:
                self.budget_config["monthly_budget"] = float(env_budget)
                self.budget_config["daily_budget"] = self.budget_config["monthly_budget"] / 30
                self.budget_config["weekly_budget"] = self.budget_config["monthly_budget"] / 4.29
            except ValueError:
                logger.warning(f"Invalid MONTHLY_BUDGET value: {env_budget}")
        
        env_warning = os.getenv("BUDGET_WARNING_THRESHOLD")
        if env_warning:
            try:
                self.budget_config["warning_threshold"] = float(env_warning)
            except ValueError:
                logger.warning(f"Invalid BUDGET_WARNING_THRESHOLD value: {env_warning}")
        
        env_critical = os.getenv("BUDGET_CRITICAL_THRESHOLD")
        if env_critical:
            try:
                self.budget_config["critical_threshold"] = float(env_critical)
            except ValueError:
                logger.warning(f"Invalid BUDGET_CRITICAL_THRESHOLD value: {env_critical}")
        
        # Email alerts
        self.budget_config["alert_email"] = os.getenv("BUDGET_ALERT_EMAIL")
        self.budget_config["alert_webhook"] = os.getenv("BUDGET_ALERT_WEBHOOK")
    
    def track_daily_usage(self, cost: float, api_breakdown: Dict = None):
        """Track daily API usage and costs"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Load existing budget data
        budget_data = self._load_budget_data()
        
        # Add today's usage
        if today not in budget_data["daily_usage"]:
            budget_data["daily_usage"][today] = {
                "cost": 0.0,
                "api_breakdown": {},
                "timestamp": datetime.now().isoformat()
            }
        
        budget_data["daily_usage"][today]["cost"] += cost
        if api_breakdown:
            for api, api_cost in api_breakdown.items():
                if api not in budget_data["daily_usage"][today]["api_breakdown"]:
                    budget_data["daily_usage"][today]["api_breakdown"][api] = 0.0
                budget_data["daily_usage"][today]["api_breakdown"][api] += api_cost
        
        # Update monthly totals
        current_month = datetime.now().strftime("%Y-%m")
        if current_month not in budget_data["monthly_totals"]:
            budget_data["monthly_totals"][current_month] = 0.0
        
        budget_data["monthly_totals"][current_month] += cost
        
        # Save updated data
        self._save_budget_data(budget_data)
        
        # Check for alerts
        self._check_budget_alerts(budget_data)
        
        logger.info(f"Tracked daily usage: ${cost:.2f} for {today}")
    
    def get_current_month_cost(self) -> float:
        """Get total cost for current month"""
        budget_data = self._load_budget_data()
        current_month = datetime.now().strftime("%Y-%m")
        return budget_data["monthly_totals"].get(current_month, 0.0)
    
    def get_current_day_cost(self) -> float:
        """Get total cost for current day"""
        budget_data = self._load_budget_data()
        today = datetime.now().strftime("%Y-%m-%d")
        return budget_data["daily_usage"].get(today, {}).get("cost", 0.0)
    
    def get_budget_status(self) -> Dict:
        """Get current budget status"""
        current_month_cost = self.get_current_month_cost()
        current_day_cost = self.get_current_day_cost()
        monthly_budget = self.budget_config["monthly_budget"]
        daily_budget = self.budget_config["daily_budget"]
        
        monthly_percentage = (current_month_cost / monthly_budget) * 100
        daily_percentage = (current_day_cost / daily_budget) * 100
        
        status = {
            "current_month_cost": current_month_cost,
            "current_day_cost": current_day_cost,
            "monthly_budget": monthly_budget,
            "daily_budget": daily_budget,
            "monthly_remaining": monthly_budget - current_month_cost,
            "daily_remaining": daily_budget - current_day_cost,
            "monthly_percentage": monthly_percentage,
            "daily_percentage": daily_percentage,
            "status": "normal",
            "alerts": []
        }
        
        # Check for alerts
        if monthly_percentage >= self.budget_config["critical_threshold"] * 100:
            status["status"] = "critical"
            status["alerts"].append(f"CRITICAL: Monthly budget at {monthly_percentage:.1f}%")
        elif monthly_percentage >= self.budget_config["warning_threshold"] * 100:
            status["status"] = "warning"
            status["alerts"].append(f"WARNING: Monthly budget at {monthly_percentage:.1f}%")
        
        if daily_percentage >= 100:
            status["alerts"].append(f"ALERT: Daily budget exceeded by {daily_percentage - 100:.1f}%")
        
        return status
    
    def _check_budget_alerts(self, budget_data: Dict):
        """Check if budget alerts should be triggered"""
        status = self.get_budget_status()
        
        if not status["alerts"]:
            return
        
        # Check if we've already sent an alert recently
        current_time = datetime.now()
        recent_alerts = [
            alert for alert in self.alert_history
            if (current_time - datetime.fromisoformat(alert["timestamp"])).days < 1
        ]
        
        if recent_alerts:
            logger.debug("Skipping alert - recent alert already sent")
            return
        
        # Send alerts
        for alert_message in status["alerts"]:
            self._send_alert(alert_message, status)
            
            # Record alert
            self.alert_history.append({
                "message": alert_message,
                "timestamp": current_time.isoformat(),
                "status": status
            })
    
    def _send_alert(self, message: str, status: Dict):
        """Send budget alert via email or webhook"""
        if not self.budget_config["enable_alerts"]:
            return
        
        # Email alert
        if self.budget_config["alert_email"]:
            self._send_email_alert(message, status)
        
        # Webhook alert
        if self.budget_config["alert_webhook"]:
            self._send_webhook_alert(message, status)
        
        # Log alert
        logger.warning(f"BUDGET ALERT: {message}")
    
    def _send_email_alert(self, message: str, status: Dict):
        """Send email alert"""
        try:
            # This is a simplified email implementation
            # In production, you'd want to use a proper email service
            logger.info(f"Would send email alert to {self.budget_config['alert_email']}: {message}")
            
            # Example email content
            email_content = f"""
Budget Alert: {message}

Current Status:
- Monthly Cost: ${status['current_month_cost']:.2f} / ${status['monthly_budget']:.2f}
- Daily Cost: ${status['current_day_cost']:.2f} / ${status['daily_budget']:.2f}
- Monthly Remaining: ${status['monthly_remaining']:.2f}
- Daily Remaining: ${status['daily_remaining']:.2f}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            logger.info(f"Email alert content:\n{email_content}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
    
    def _send_webhook_alert(self, message: str, status: Dict):
        """Send webhook alert"""
        try:
            import requests
            
            webhook_data = {
                "message": message,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                self.budget_config["alert_webhook"],
                json=webhook_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Webhook alert sent successfully")
            else:
                logger.warning(f"Webhook alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {str(e)}")
    
    def _load_budget_data(self) -> Dict:
        """Load budget data from file"""
        if not self.budget_data_file.exists():
            return {
                "daily_usage": {},
                "monthly_totals": {},
                "created": datetime.now().isoformat()
            }
        
        try:
            with open(self.budget_data_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load budget data: {str(e)}")
            return {
                "daily_usage": {},
                "monthly_totals": {},
                "created": datetime.now().isoformat()
            }
    
    def _save_budget_data(self, budget_data: Dict):
        """Save budget data to file"""
        try:
            with open(self.budget_data_file, 'w') as f:
                json.dump(budget_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save budget data: {str(e)}")
    
    def get_cost_forecast(self, days: int = 30) -> Dict:
        """Forecast costs for the next N days based on current usage patterns"""
        budget_data = self._load_budget_data()
        current_month_cost = self.get_current_month_cost()
        
        # Calculate average daily cost from current month
        current_month = datetime.now().strftime("%Y-%m")
        days_elapsed = len([d for d in budget_data["daily_usage"].keys() 
                           if d.startswith(current_month)])
        
        if days_elapsed == 0:
            avg_daily_cost = 0.0
        else:
            avg_daily_cost = current_month_cost / days_elapsed
        
        # Forecast
        forecasted_cost = avg_daily_cost * days
        total_forecasted = current_month_cost + forecasted_cost
        
        return {
            "current_month_cost": current_month_cost,
            "avg_daily_cost": avg_daily_cost,
            "forecasted_cost": forecasted_cost,
            "total_forecasted": total_forecasted,
            "forecast_days": days,
            "budget_remaining": self.budget_config["monthly_budget"] - current_month_cost,
            "will_exceed_budget": total_forecasted > self.budget_config["monthly_budget"]
        }
    
    def get_usage_summary(self) -> Dict:
        """Get usage summary for reporting"""
        budget_data = self._load_budget_data()
        status = self.get_budget_status()
        
        # Calculate usage statistics
        daily_costs = list(budget_data["daily_usage"].values())
        if daily_costs:
            avg_daily_cost = sum(day["cost"] for day in daily_costs) / len(daily_costs)
            max_daily_cost = max(day["cost"] for day in daily_costs)
            min_daily_cost = min(day["cost"] for day in daily_costs)
        else:
            avg_daily_cost = max_daily_cost = min_daily_cost = 0.0
        
        return {
            "current_status": status,
            "usage_stats": {
                "avg_daily_cost": avg_daily_cost,
                "max_daily_cost": max_daily_cost,
                "min_daily_cost": min_daily_cost,
                "total_days_tracked": len(daily_costs)
            },
            "budget_config": self.budget_config,
            "alert_history_count": len(self.alert_history)
        }


# Global budget monitor instance
budget_monitor = BudgetMonitor() 