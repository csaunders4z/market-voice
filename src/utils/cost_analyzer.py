"""
Cost Analysis and Optimization for Market Voices
Calculates API costs and implements strategies to minimize usage
"""
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
import json
import os
from pathlib import Path

from src.config.settings import get_settings


@dataclass
class APICost:
    """Represents cost information for an API"""
    name: str
    cost_per_request: float
    requests_per_month: int
    monthly_cost: float
    rate_limit_per_minute: int
    rate_limit_per_day: int
    free_tier_requests: int = 0
    free_tier_cost: float = 0.0


@dataclass
class CostOptimization:
    """Represents optimization strategies"""
    strategy: str
    potential_savings: float
    implementation_effort: str  # "low", "medium", "high"
    impact_on_quality: str  # "none", "low", "medium", "high"


class CostAnalyzer:
    """Analyzes and optimizes API costs for Market Voices"""
    
    def __init__(self):
        self.settings = get_settings()
        self.cost_data_file = Path("logs/api_costs.json")
        self.cost_data_file.parent.mkdir(exist_ok=True)
        
        # API cost configurations (as of 2025)
        self.api_costs = {
            "openai": {
                "gpt-4": {"cost_per_1k_tokens": 0.03, "cost_per_1k_output_tokens": 0.06},
                "gpt-3.5-turbo": {"cost_per_1k_tokens": 0.0015, "cost_per_1k_output_tokens": 0.002}
            },
            "newsapi": {
                "cost_per_request": 0.001,  # $0.001 per request
                "free_tier_requests": 1000,
                "rate_limit_per_day": 1000
            },
            "alpha_vantage": {
                "cost_per_request": 0.0,  # Free tier
                "free_tier_requests": 500,
                "rate_limit_per_minute": 5,
                "rate_limit_per_day": 500
            },
            "fmp": {
                "cost_per_request": 0.0,  # Free tier
                "free_tier_requests": 250,
                "rate_limit_per_minute": 30,
                "rate_limit_per_day": 250
            },
            "rapidapi_biztoc": {
                "cost_per_request": 0.001,  # $0.001 per request
                "free_tier_requests": 100,
                "rate_limit_per_minute": 10,
                "rate_limit_per_day": 100
            },
            "newsdata_io": {
                "cost_per_request": 0.002,  # $0.002 per request
                "free_tier_requests": 200,
                "rate_limit_per_minute": 10,
                "rate_limit_per_day": 200
            },
            "the_news_api": {
                "cost_per_request": 0.001,  # $0.001 per request
                "free_tier_requests": 100,
                "rate_limit_per_minute": 10,
                "rate_limit_per_day": 100
            }
        }
        
        # Usage patterns based on current system
        self.usage_patterns = {
            "daily_runs": 1,  # Scripts per day
            "symbols_per_run": 516,  # Total symbols (NASDAQ-100 + S&P-500)
            "top_movers_per_run": 10,  # Top movers selected for script
            "news_articles_per_stock": 3,  # News articles per stock
            "market_news_articles": 5,  # General market news
            "openai_tokens_per_script": 4000,  # Average tokens per script
            "openai_output_tokens_per_script": 2000  # Average output tokens
        }
    
    def calculate_current_costs(self) -> Dict[str, APICost]:
        """Calculate current monthly API costs based on usage patterns"""
        logger.info("Calculating current API costs...")
        
        costs = {}
        
        # OpenAI costs
        openai_requests_per_month = self.usage_patterns["daily_runs"] * 30
        openai_input_cost = (self.usage_patterns["openai_tokens_per_script"] / 1000) * self.api_costs["openai"]["gpt-4"]["cost_per_1k_tokens"]
        openai_output_cost = (self.usage_patterns["openai_output_tokens_per_script"] / 1000) * self.api_costs["openai"]["gpt-4"]["cost_per_1k_output_tokens"]
        openai_cost_per_request = openai_input_cost + openai_output_cost
        openai_monthly_cost = openai_cost_per_request * openai_requests_per_month
        
        costs["openai"] = APICost(
            name="OpenAI GPT-4",
            cost_per_request=openai_cost_per_request,
            requests_per_month=openai_requests_per_month,
            monthly_cost=openai_monthly_cost,
            rate_limit_per_minute=3500,
            rate_limit_per_day=3500
        )
        
        # News API costs
        news_requests_per_month = self.usage_patterns["daily_runs"] * 30 * (
            self.usage_patterns["top_movers_per_run"] * self.usage_patterns["news_articles_per_stock"] + 
            self.usage_patterns["market_news_articles"]
        )
        news_monthly_cost = max(0, (news_requests_per_month - self.api_costs["newsapi"]["free_tier_requests"])) * self.api_costs["newsapi"]["cost_per_request"]
        
        costs["newsapi"] = APICost(
            name="NewsAPI",
            cost_per_request=self.api_costs["newsapi"]["cost_per_request"],
            requests_per_month=news_requests_per_month,
            monthly_cost=news_monthly_cost,
            rate_limit_per_minute=100,
            rate_limit_per_day=self.api_costs["newsapi"]["rate_limit_per_day"],
            free_tier_requests=self.api_costs["newsapi"]["free_tier_requests"]
        )
        
        # Alpha Vantage costs (free tier)
        av_requests_per_month = self.usage_patterns["daily_runs"] * 30 * self.usage_patterns["symbols_per_run"]
        av_monthly_cost = 0.0  # Free tier
        
        costs["alpha_vantage"] = APICost(
            name="Alpha Vantage",
            cost_per_request=0.0,
            requests_per_month=av_requests_per_month,
            monthly_cost=av_monthly_cost,
            rate_limit_per_minute=self.api_costs["alpha_vantage"]["rate_limit_per_minute"],
            rate_limit_per_day=self.api_costs["alpha_vantage"]["rate_limit_per_day"],
            free_tier_requests=self.api_costs["alpha_vantage"]["free_tier_requests"]
        )
        
        # FMP costs (free tier)
        fmp_requests_per_month = self.usage_patterns["daily_runs"] * 30 * self.usage_patterns["symbols_per_run"]
        fmp_monthly_cost = 0.0  # Free tier
        
        costs["fmp"] = APICost(
            name="Financial Modeling Prep",
            cost_per_request=0.0,
            requests_per_month=fmp_requests_per_month,
            monthly_cost=fmp_monthly_cost,
            rate_limit_per_minute=self.api_costs["fmp"]["rate_limit_per_minute"],
            rate_limit_per_day=self.api_costs["fmp"]["rate_limit_per_day"],
            free_tier_requests=self.api_costs["fmp"]["free_tier_requests"]
        )
        
        # RapidAPI Biztoc costs
        biztoc_requests_per_month = self.usage_patterns["daily_runs"] * 30 * self.usage_patterns["top_movers_per_run"]
        biztoc_monthly_cost = max(0, (biztoc_requests_per_month - self.api_costs["rapidapi_biztoc"]["free_tier_requests"])) * self.api_costs["rapidapi_biztoc"]["cost_per_request"]
        
        costs["rapidapi_biztoc"] = APICost(
            name="RapidAPI Biztoc",
            cost_per_request=self.api_costs["rapidapi_biztoc"]["cost_per_request"],
            requests_per_month=biztoc_requests_per_month,
            monthly_cost=biztoc_monthly_cost,
            rate_limit_per_minute=self.api_costs["rapidapi_biztoc"]["rate_limit_per_minute"],
            rate_limit_per_day=self.api_costs["rapidapi_biztoc"]["rate_limit_per_day"],
            free_tier_requests=self.api_costs["rapidapi_biztoc"]["free_tier_requests"]
        )
        
        # NewsData.io costs
        newsdata_requests_per_month = self.usage_patterns["daily_runs"] * 30 * self.usage_patterns["top_movers_per_run"]
        newsdata_monthly_cost = max(0, (newsdata_requests_per_month - self.api_costs["newsdata_io"]["free_tier_requests"])) * self.api_costs["newsdata_io"]["cost_per_request"]
        
        costs["newsdata_io"] = APICost(
            name="NewsData.io",
            cost_per_request=self.api_costs["newsdata_io"]["cost_per_request"],
            requests_per_month=newsdata_requests_per_month,
            monthly_cost=newsdata_monthly_cost,
            rate_limit_per_minute=self.api_costs["newsdata_io"]["rate_limit_per_minute"],
            rate_limit_per_day=self.api_costs["newsdata_io"]["rate_limit_per_day"],
            free_tier_requests=self.api_costs["newsdata_io"]["free_tier_requests"]
        )
        
        # The News API costs
        the_news_requests_per_month = self.usage_patterns["daily_runs"] * 30 * self.usage_patterns["top_movers_per_run"]
        the_news_monthly_cost = max(0, (the_news_requests_per_month - self.api_costs["the_news_api"]["free_tier_requests"])) * self.api_costs["the_news_api"]["cost_per_request"]
        
        costs["the_news_api"] = APICost(
            name="The News API",
            cost_per_request=self.api_costs["the_news_api"]["cost_per_request"],
            requests_per_month=the_news_requests_per_month,
            monthly_cost=the_news_monthly_cost,
            rate_limit_per_minute=self.api_costs["the_news_api"]["rate_limit_per_minute"],
            rate_limit_per_day=self.api_costs["the_news_api"]["rate_limit_per_day"],
            free_tier_requests=self.api_costs["the_news_api"]["free_tier_requests"]
        )
        
        return costs
    
    def get_total_monthly_cost(self, costs: Dict[str, APICost]) -> float:
        """Calculate total monthly cost"""
        return sum(cost.monthly_cost for cost in costs.values())
    
    def generate_cost_report(self) -> str:
        """Generate a comprehensive cost report"""
        costs = self.calculate_current_costs()
        total_cost = self.get_total_monthly_cost(costs)
        
        report = []
        report.append("=" * 60)
        report.append("MARKET VOICES - API COST ANALYSIS")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Usage Pattern: {self.usage_patterns['daily_runs']} script(s) per day")
        report.append(f"Symbol Coverage: {self.usage_patterns['symbols_per_run']} symbols")
        report.append("")
        
        # API breakdown
        report.append("API COST BREAKDOWN:")
        report.append("-" * 40)
        
        for api_name, cost in costs.items():
            report.append(f"{cost.name}:")
            report.append(f"  Requests/month: {cost.requests_per_month:,}")
            report.append(f"  Cost/request: ${cost.cost_per_request:.4f}")
            if cost.free_tier_requests > 0:
                report.append(f"  Free tier: {cost.free_tier_requests:,} requests")
            report.append(f"  Monthly cost: ${cost.monthly_cost:.2f}")
            report.append("")
        
        report.append("=" * 40)
        report.append(f"TOTAL MONTHLY COST: ${total_cost:.2f}")
        report.append("=" * 40)
        
        # Rate limit analysis
        report.append("")
        report.append("RATE LIMIT ANALYSIS:")
        report.append("-" * 40)
        
        for api_name, cost in costs.items():
            daily_requests = cost.requests_per_month / 30
            if daily_requests > cost.rate_limit_per_day:
                report.append(f"⚠️  {cost.name}: {daily_requests:.0f} daily requests exceeds {cost.rate_limit_per_day} limit")
            else:
                report.append(f"✅ {cost.name}: {daily_requests:.0f} daily requests within {cost.rate_limit_per_day} limit")
        
        # Optimization recommendations
        optimizations = self.get_optimization_recommendations(costs)
        report.append("")
        report.append("OPTIMIZATION RECOMMENDATIONS:")
        report.append("-" * 40)
        
        for opt in optimizations:
            report.append(f"• {opt.strategy}")
            report.append(f"  Potential savings: ${opt.potential_savings:.2f}/month")
            report.append(f"  Implementation: {opt.implementation_effort}")
            report.append(f"  Quality impact: {opt.impact_on_quality}")
            report.append("")
        
        return "\n".join(report)
    
    def get_optimization_recommendations(self, costs: Dict[str, APICost]) -> List[CostOptimization]:
        """Generate optimization recommendations"""
        optimizations = []
        total_cost = self.get_total_monthly_cost(costs)
        
        # 1. OpenAI model optimization
        if costs.get("openai"):
            current_cost = costs["openai"].monthly_cost
            # Switch to GPT-3.5-turbo for 50% cost reduction
            gpt35_cost_per_request = (
                (self.usage_patterns["openai_tokens_per_script"] / 1000) * self.api_costs["openai"]["gpt-3.5-turbo"]["cost_per_1k_tokens"] +
                (self.usage_patterns["openai_output_tokens_per_script"] / 1000) * self.api_costs["openai"]["gpt-3.5-turbo"]["cost_per_1k_output_tokens"]
            )
            gpt35_monthly_cost = gpt35_cost_per_request * costs["openai"].requests_per_month
            savings = current_cost - gpt35_monthly_cost
            
            optimizations.append(CostOptimization(
                strategy="Switch to GPT-3.5-turbo for script generation",
                potential_savings=savings,
                implementation_effort="low",
                impact_on_quality="low"
            ))
        
        # 2. News API optimization
        if costs.get("newsapi") and costs["newsapi"].monthly_cost > 0:
            # Reduce news articles per stock
            current_articles = self.usage_patterns["news_articles_per_stock"]
            if current_articles > 1:
                reduced_articles = current_articles - 1
                reduced_requests = self.usage_patterns["daily_runs"] * 30 * (
                    self.usage_patterns["top_movers_per_run"] * reduced_articles + 
                    self.usage_patterns["market_news_articles"]
                )
                reduced_cost = max(0, (reduced_requests - self.api_costs["newsapi"]["free_tier_requests"])) * self.api_costs["newsapi"]["cost_per_request"]
                savings = costs["newsapi"].monthly_cost - reduced_cost
                
                optimizations.append(CostOptimization(
                    strategy=f"Reduce news articles per stock from {current_articles} to {reduced_articles}",
                    potential_savings=savings,
                    implementation_effort="low",
                    impact_on_quality="low"
                ))
        
        # 3. Caching strategy
        # Estimate 50% reduction in API calls through intelligent caching
        cacheable_apis = ["newsapi", "rapidapi_biztoc", "newsdata_io", "the_news_api"]
        cacheable_cost = sum(costs.get(api, APICost("", 0, 0, 0, 0, 0)).monthly_cost for api in cacheable_apis)
        cache_savings = cacheable_cost * 0.5
        
        optimizations.append(CostOptimization(
            strategy="Implement intelligent caching for news APIs",
            potential_savings=cache_savings,
            implementation_effort="medium",
            impact_on_quality="none"
        ))
        
        # 4. Free news sources prioritization
        if costs.get("newsapi") and costs["newsapi"].monthly_cost > 0:
            # Prioritize free news sources to reduce paid API usage
            free_savings = costs["newsapi"].monthly_cost * 0.3  # Estimate 30% reduction
            
            optimizations.append(CostOptimization(
                strategy="Prioritize free news sources (Yahoo, MarketWatch, etc.)",
                potential_savings=free_savings,
                implementation_effort="medium",
                impact_on_quality="none"
            ))
        
        # 5. Batch processing optimization
        # Optimize batch sizes to reduce API calls
        batch_savings = total_cost * 0.1  # Estimate 10% reduction through better batching
        
        optimizations.append(CostOptimization(
            strategy="Optimize batch processing to reduce API calls",
            potential_savings=batch_savings,
            implementation_effort="low",
            impact_on_quality="none"
        ))
        
        return optimizations
    
    def save_cost_data(self, costs: Dict[str, APICost]):
        """Save cost data to file for tracking"""
        cost_data = {
            "timestamp": datetime.now().isoformat(),
            "total_monthly_cost": self.get_total_monthly_cost(costs),
            "usage_patterns": self.usage_patterns,
            "api_costs": {
                name: {
                    "requests_per_month": cost.requests_per_month,
                    "monthly_cost": cost.monthly_cost,
                    "rate_limit_per_day": cost.rate_limit_per_day
                }
                for name, cost in costs.items()
            }
        }
        
        # Load existing data
        existing_data = []
        if self.cost_data_file.exists():
            try:
                with open(self.cost_data_file, 'r') as f:
                    existing_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_data = []
        
        # Add new data (keep last 30 entries)
        existing_data.append(cost_data)
        if len(existing_data) > 30:
            existing_data = existing_data[-30:]
        
        # Save updated data
        with open(self.cost_data_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        logger.info(f"Cost data saved to {self.cost_data_file}")
    
    def get_cost_trends(self) -> Dict:
        """Analyze cost trends over time"""
        if not self.cost_data_file.exists():
            return {"error": "No cost data available"}
        
        try:
            with open(self.cost_data_file, 'r') as f:
                data = json.load(f)
            
            if len(data) < 2:
                return {"error": "Insufficient data for trend analysis"}
            
            # Calculate trends
            costs = [entry["total_monthly_cost"] for entry in data]
            avg_cost = sum(costs) / len(costs)
            cost_change = costs[-1] - costs[0] if len(costs) > 1 else 0
            
            return {
                "data_points": len(data),
                "average_monthly_cost": avg_cost,
                "cost_change": cost_change,
                "trend": "increasing" if cost_change > 0 else "decreasing" if cost_change < 0 else "stable",
                "latest_cost": costs[-1] if costs else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing cost trends: {str(e)}")
            return {"error": f"Failed to analyze trends: {str(e)}"}


# Global instance
cost_analyzer = CostAnalyzer() 