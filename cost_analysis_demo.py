#!/usr/bin/env python3
"""
Cost Analysis Demo for Market Voices
Standalone script to demonstrate cost analysis and optimization
"""
import json
from datetime import datetime
from pathlib import Path

def calculate_api_costs():
    """Calculate current API costs based on usage patterns"""
    
    # Usage patterns
    usage = {
        "daily_runs": 1,  # Scripts per day
        "symbols_per_run": 516,  # Total symbols (NASDAQ-100 + S&P-500)
        "top_movers_per_run": 10,  # Top movers selected for script
        "news_articles_per_stock": 3,  # News articles per stock
        "market_news_articles": 5,  # General market news
        "openai_tokens_per_script": 4000,  # Average tokens per script
        "openai_output_tokens_per_script": 2000  # Average output tokens
    }
    
    # API costs (as of 2025)
    api_costs = {
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
    
    # Calculate costs
    costs = {}
    
    # OpenAI costs
    openai_requests_per_month = usage["daily_runs"] * 30
    openai_input_cost = (usage["openai_tokens_per_script"] / 1000) * api_costs["openai"]["gpt-4"]["cost_per_1k_tokens"]
    openai_output_cost = (usage["openai_output_tokens_per_script"] / 1000) * api_costs["openai"]["gpt-4"]["cost_per_1k_output_tokens"]
    openai_cost_per_request = openai_input_cost + openai_output_cost
    openai_monthly_cost = openai_cost_per_request * openai_requests_per_month
    
    costs["openai"] = {
        "name": "OpenAI GPT-4",
        "cost_per_request": openai_cost_per_request,
        "requests_per_month": openai_requests_per_month,
        "monthly_cost": openai_monthly_cost,
        "rate_limit_per_minute": 3500,
        "rate_limit_per_day": 3500
    }
    
    # News API costs
    news_requests_per_month = usage["daily_runs"] * 30 * (
        usage["top_movers_per_run"] * usage["news_articles_per_stock"] + 
        usage["market_news_articles"]
    )
    news_monthly_cost = max(0, (news_requests_per_month - api_costs["newsapi"]["free_tier_requests"])) * api_costs["newsapi"]["cost_per_request"]
    
    costs["newsapi"] = {
        "name": "NewsAPI",
        "cost_per_request": api_costs["newsapi"]["cost_per_request"],
        "requests_per_month": news_requests_per_month,
        "monthly_cost": news_monthly_cost,
        "rate_limit_per_minute": 100,
        "rate_limit_per_day": api_costs["newsapi"]["rate_limit_per_day"],
        "free_tier_requests": api_costs["newsapi"]["free_tier_requests"]
    }
    
    # Alpha Vantage costs (free tier)
    av_requests_per_month = usage["daily_runs"] * 30 * usage["symbols_per_run"]
    av_monthly_cost = 0.0  # Free tier
    
    costs["alpha_vantage"] = {
        "name": "Alpha Vantage",
        "cost_per_request": 0.0,
        "requests_per_month": av_requests_per_month,
        "monthly_cost": av_monthly_cost,
        "rate_limit_per_minute": api_costs["alpha_vantage"]["rate_limit_per_minute"],
        "rate_limit_per_day": api_costs["alpha_vantage"]["rate_limit_per_day"],
        "free_tier_requests": api_costs["alpha_vantage"]["free_tier_requests"]
    }
    
    # FMP costs (free tier)
    fmp_requests_per_month = usage["daily_runs"] * 30 * usage["symbols_per_run"]
    fmp_monthly_cost = 0.0  # Free tier
    
    costs["fmp"] = {
        "name": "Financial Modeling Prep",
        "cost_per_request": 0.0,
        "requests_per_month": fmp_requests_per_month,
        "monthly_cost": fmp_monthly_cost,
        "rate_limit_per_minute": api_costs["fmp"]["rate_limit_per_minute"],
        "rate_limit_per_day": api_costs["fmp"]["rate_limit_per_day"],
        "free_tier_requests": api_costs["fmp"]["free_tier_requests"]
    }
    
    # RapidAPI Biztoc costs
    biztoc_requests_per_month = usage["daily_runs"] * 30 * usage["top_movers_per_run"]
    biztoc_monthly_cost = max(0, (biztoc_requests_per_month - api_costs["rapidapi_biztoc"]["free_tier_requests"])) * api_costs["rapidapi_biztoc"]["cost_per_request"]
    
    costs["rapidapi_biztoc"] = {
        "name": "RapidAPI Biztoc",
        "cost_per_request": api_costs["rapidapi_biztoc"]["cost_per_request"],
        "requests_per_month": biztoc_requests_per_month,
        "monthly_cost": biztoc_monthly_cost,
        "rate_limit_per_minute": api_costs["rapidapi_biztoc"]["rate_limit_per_minute"],
        "rate_limit_per_day": api_costs["rapidapi_biztoc"]["rate_limit_per_day"],
        "free_tier_requests": api_costs["rapidapi_biztoc"]["free_tier_requests"]
    }
    
    # NewsData.io costs
    newsdata_requests_per_month = usage["daily_runs"] * 30 * usage["top_movers_per_run"]
    newsdata_monthly_cost = max(0, (newsdata_requests_per_month - api_costs["newsdata_io"]["free_tier_requests"])) * api_costs["newsdata_io"]["cost_per_request"]
    
    costs["newsdata_io"] = {
        "name": "NewsData.io",
        "cost_per_request": api_costs["newsdata_io"]["cost_per_request"],
        "requests_per_month": newsdata_requests_per_month,
        "monthly_cost": newsdata_monthly_cost,
        "rate_limit_per_minute": api_costs["newsdata_io"]["rate_limit_per_minute"],
        "rate_limit_per_day": api_costs["newsdata_io"]["rate_limit_per_day"],
        "free_tier_requests": api_costs["newsdata_io"]["free_tier_requests"]
    }
    
    # The News API costs
    the_news_requests_per_month = usage["daily_runs"] * 30 * usage["top_movers_per_run"]
    the_news_monthly_cost = max(0, (the_news_requests_per_month - api_costs["the_news_api"]["free_tier_requests"])) * api_costs["the_news_api"]["cost_per_request"]
    
    costs["the_news_api"] = {
        "name": "The News API",
        "cost_per_request": api_costs["the_news_api"]["cost_per_request"],
        "requests_per_month": the_news_requests_per_month,
        "monthly_cost": the_news_monthly_cost,
        "rate_limit_per_minute": api_costs["the_news_api"]["rate_limit_per_minute"],
        "rate_limit_per_day": api_costs["the_news_api"]["rate_limit_per_day"],
        "free_tier_requests": api_costs["the_news_api"]["free_tier_requests"]
    }
    
    return costs, usage

def generate_cost_report(costs, usage):
    """Generate a comprehensive cost report"""
    total_cost = sum(cost["monthly_cost"] for cost in costs.values())
    
    report = []
    report.append("=" * 60)
    report.append("MARKET VOICES - API COST ANALYSIS")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Usage Pattern: {usage['daily_runs']} script(s) per day")
    report.append(f"Symbol Coverage: {usage['symbols_per_run']} symbols")
    report.append("")
    
    # API breakdown
    report.append("API COST BREAKDOWN:")
    report.append("-" * 40)
    
    for api_name, cost in costs.items():
        report.append(f"{cost['name']}:")
        report.append(f"  Requests/month: {cost['requests_per_month']:,}")
        report.append(f"  Cost/request: ${cost['cost_per_request']:.4f}")
        if cost.get('free_tier_requests', 0) > 0:
            report.append(f"  Free tier: {cost['free_tier_requests']:,} requests")
        report.append(f"  Monthly cost: ${cost['monthly_cost']:.2f}")
        report.append("")
    
    report.append("=" * 40)
    report.append(f"TOTAL MONTHLY COST: ${total_cost:.2f}")
    report.append("=" * 40)
    
    # Rate limit analysis
    report.append("")
    report.append("RATE LIMIT ANALYSIS:")
    report.append("-" * 40)
    
    for api_name, cost in costs.items():
        daily_requests = cost["requests_per_month"] / 30
        if daily_requests > cost["rate_limit_per_day"]:
            report.append(f"⚠️  {cost['name']}: {daily_requests:.0f} daily requests exceeds {cost['rate_limit_per_day']} limit")
        else:
            report.append(f"✅ {cost['name']}: {daily_requests:.0f} daily requests within {cost['rate_limit_per_day']} limit")
    
    return "\n".join(report), total_cost

def get_optimization_recommendations(costs, total_cost):
    """Generate optimization recommendations"""
    optimizations = []
    
    # 1. OpenAI model optimization
    if costs.get("openai"):
        current_cost = costs["openai"]["monthly_cost"]
        # Switch to GPT-3.5-turbo for 50% cost reduction
        gpt35_cost_per_request = 0.0015 + 0.002  # $0.0015 input + $0.002 output per 1k tokens
        gpt35_monthly_cost = gpt35_cost_per_request * costs["openai"]["requests_per_month"]
        savings = current_cost - gpt35_monthly_cost
        
        optimizations.append({
            "strategy": "Switch to GPT-3.5-turbo for script generation",
            "potential_savings": savings,
            "implementation_effort": "low",
            "impact_on_quality": "low"
        })
    
    # 2. News API optimization
    if costs.get("newsapi") and costs["newsapi"]["monthly_cost"] > 0:
        # Reduce news articles per stock
        current_articles = 3
        if current_articles > 1:
            reduced_articles = current_articles - 1
            reduced_requests = 30 * (10 * reduced_articles + 5)
            reduced_cost = max(0, (reduced_requests - 1000)) * 0.001
            savings = costs["newsapi"]["monthly_cost"] - reduced_cost
            
            optimizations.append({
                "strategy": f"Reduce news articles per stock from {current_articles} to {reduced_articles}",
                "potential_savings": savings,
                "implementation_effort": "low",
                "impact_on_quality": "low"
            })
    
    # 3. Caching strategy
    # Estimate 50% reduction in API calls through intelligent caching
    cacheable_apis = ["newsapi", "rapidapi_biztoc", "newsdata_io", "the_news_api"]
    cacheable_cost = sum(costs.get(api, {"monthly_cost": 0})["monthly_cost"] for api in cacheable_apis)
    cache_savings = cacheable_cost * 0.5
    
    optimizations.append({
        "strategy": "Implement intelligent caching for news APIs",
        "potential_savings": cache_savings,
        "implementation_effort": "medium",
        "impact_on_quality": "none"
    })
    
    # 4. Free news sources prioritization
    if costs.get("newsapi") and costs["newsapi"]["monthly_cost"] > 0:
        # Prioritize free news sources to reduce paid API usage
        free_savings = costs["newsapi"]["monthly_cost"] * 0.3  # Estimate 30% reduction
        
        optimizations.append({
            "strategy": "Prioritize free news sources (Yahoo, MarketWatch, etc.)",
            "potential_savings": free_savings,
            "implementation_effort": "medium",
            "impact_on_quality": "none"
        })
    
    # 5. Batch processing optimization
    # Optimize batch sizes to reduce API calls
    batch_savings = total_cost * 0.1  # Estimate 10% reduction through better batching
    
    optimizations.append({
        "strategy": "Optimize batch processing to reduce API calls",
        "potential_savings": batch_savings,
        "implementation_effort": "low",
        "impact_on_quality": "none"
    })
    
    return optimizations

def main():
    """Run the cost analysis demo"""
    print("=" * 60)
    print("MARKET VOICES - COST ANALYSIS DEMO")
    print("=" * 60)
    
    # Calculate costs
    print("\n1. CALCULATING API COSTS...")
    costs, usage = calculate_api_costs()
    
    # Generate report
    print("\n2. GENERATING COST REPORT...")
    report, total_cost = generate_cost_report(costs, usage)
    print(report)
    
    # Get optimizations
    print("\n3. OPTIMIZATION RECOMMENDATIONS...")
    optimizations = get_optimization_recommendations(costs, total_cost)
    
    total_potential_savings = 0
    for opt in optimizations:
        print(f"  • {opt['strategy']}")
        print(f"    Potential savings: ${opt['potential_savings']:.2f}/month")
        print(f"    Implementation effort: {opt['implementation_effort']}")
        print(f"    Quality impact: {opt['impact_on_quality']}")
        print()
        total_potential_savings += opt['potential_savings']
    
    print(f"Total potential savings: ${total_potential_savings:.2f}/month")
    print(f"Cost reduction: {(total_potential_savings / total_cost * 100):.1f}%")
    
    # Budget analysis
    print("\n4. BUDGET ANALYSIS...")
    monthly_budget = 50.0  # $50/month budget
    
    print(f"Monthly budget: ${monthly_budget:.2f}")
    print(f"Current projected cost: ${total_cost:.2f}")
    
    if total_cost > monthly_budget:
        print(f"⚠️  WARNING: Projected cost (${total_cost:.2f}) exceeds budget (${monthly_budget:.2f})")
        print(f"   Over budget by: ${total_cost - monthly_budget:.2f}")
        
        # Suggest immediate optimizations
        print("\nImmediate optimization suggestions:")
        print("  1. Switch to GPT-3.5-turbo (saves ~$15-20/month)")
        print("  2. Enable caching (saves ~$5-10/month)")
        print("  3. Reduce news articles per stock (saves ~$2-5/month)")
    else:
        print(f"✅ Projected cost (${total_cost:.2f}) is within budget (${monthly_budget:.2f})")
        print(f"   Budget remaining: ${monthly_budget - total_cost:.2f}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Current monthly cost: ${total_cost:.2f}")
    print(f"Potential savings: ${total_potential_savings:.2f}/month")
    print(f"Cost reduction potential: {(total_potential_savings / total_cost * 100):.1f}%")
    
    if total_cost > 100:
        print(f"\n⚠️  RECOMMENDATION: Current cost (${total_cost:.2f}) exceeds $100/month target")
        print("   Implement optimizations to reduce costs")
    else:
        print(f"\n✅ Current cost (${total_cost:.2f}) is within $100/month target")
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_monthly_cost": total_cost,
        "usage_patterns": usage,
        "api_costs": costs,
        "optimizations": optimizations,
        "total_potential_savings": total_potential_savings
    }
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    with open("logs/cost_analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to logs/cost_analysis_results.json")

if __name__ == "__main__":
    main() 