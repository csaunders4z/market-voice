#!/usr/bin/env python3
"""
Test script for Cost Analysis and Optimization
Demonstrates API cost calculation and optimization strategies
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.cost_analyzer import cost_analyzer
from utils.cache_manager import cache_manager
from loguru import logger

def test_cost_analysis():
    """Test the cost analysis functionality"""
    print("=" * 60)
    print("MARKET VOICES - COST ANALYSIS TEST")
    print("=" * 60)
    
    # Generate cost report
    print("\n1. GENERATING COST ANALYSIS REPORT...")
    cost_report = cost_analyzer.generate_cost_report()
    print(cost_report)
    
    # Calculate current costs
    print("\n2. CALCULATING CURRENT COSTS...")
    costs = cost_analyzer.calculate_current_costs()
    total_cost = cost_analyzer.get_total_monthly_cost(costs)
    
    print(f"Total Monthly Cost: ${total_cost:.2f}")
    print("\nBreakdown by API:")
    for api_name, cost in costs.items():
        print(f"  {cost.name}: ${cost.monthly_cost:.2f} ({cost.requests_per_month:,} requests)")
    
    # Get optimization recommendations
    print("\n3. OPTIMIZATION RECOMMENDATIONS...")
    optimizations = cost_analyzer.get_optimization_recommendations(costs)
    
    total_potential_savings = 0
    for opt in optimizations:
        print(f"  • {opt.strategy}")
        print(f"    Potential savings: ${opt.potential_savings:.2f}/month")
        print(f"    Implementation effort: {opt.implementation_effort}")
        print(f"    Quality impact: {opt.impact_on_quality}")
        print()
        total_potential_savings += opt.potential_savings
    
    print(f"Total potential savings: ${total_potential_savings:.2f}/month")
    print(f"Cost reduction: {(total_potential_savings / total_cost * 100):.1f}%")
    
    # Save cost data
    print("\n4. SAVING COST DATA...")
    cost_analyzer.save_cost_data(costs)
    print("Cost data saved to logs/api_costs.json")
    
    return costs, optimizations

def test_cache_manager():
    """Test the cache manager functionality"""
    print("\n" + "=" * 60)
    print("CACHE MANAGER TEST")
    print("=" * 60)
    
    # Test basic caching
    print("\n1. TESTING BASIC CACHING...")
    
    # Test stock data caching
    test_stock_data = {
        "symbol": "AAPL",
        "price": 150.25,
        "change": 2.50,
        "volume": 50000000
    }
    
    # Save to cache
    success = cache_manager.set("stock_data", "AAPL", test_stock_data)
    print(f"Cache save success: {success}")
    
    # Retrieve from cache
    cached_data = cache_manager.get("stock_data", "AAPL")
    print(f"Cache hit: {cached_data is not None}")
    if cached_data:
        print(f"Cached data: {cached_data}")
    
    # Test news data caching
    test_news_data = [
        {"title": "Apple Reports Strong Q4 Earnings", "source": "Reuters"},
        {"title": "AAPL Stock Rises on iPhone Sales", "source": "Bloomberg"}
    ]
    
    cache_manager.set("news_data", "AAPL_news", test_news_data)
    cached_news = cache_manager.get("news_data", "AAPL_news")
    print(f"News cache hit: {cached_news is not None}")
    
    # Test cache statistics
    print("\n2. CACHE STATISTICS...")
    stats = cache_manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test cache optimization
    print("\n3. CACHE OPTIMIZATION...")
    optimization_results = cache_manager.optimize_cache()
    print("Optimization results:")
    for key, value in optimization_results.items():
        print(f"  {key}: {value}")
    
    return stats

def test_cost_optimization_scenarios():
    """Test different cost optimization scenarios"""
    print("\n" + "=" * 60)
    print("COST OPTIMIZATION SCENARIOS")
    print("=" * 60)
    
    # Scenario 1: Switch to GPT-3.5-turbo
    print("\n1. SCENARIO: Switch to GPT-3.5-turbo")
    current_gpt4_cost = 0.03 + 0.06  # $0.03 input + $0.06 output per 1k tokens
    gpt35_cost = 0.0015 + 0.002  # $0.0015 input + $0.002 output per 1k tokens
    
    monthly_requests = 30  # 1 script per day
    tokens_per_script = 4000
    output_tokens_per_script = 2000
    
    gpt4_monthly = (tokens_per_script / 1000 * 0.03 + output_tokens_per_script / 1000 * 0.06) * monthly_requests
    gpt35_monthly = (tokens_per_script / 1000 * 0.0015 + output_tokens_per_script / 1000 * 0.002) * monthly_requests
    
    savings = gpt4_monthly - gpt35_monthly
    print(f"  GPT-4 monthly cost: ${gpt4_monthly:.2f}")
    print(f"  GPT-3.5-turbo monthly cost: ${gpt35_monthly:.2f}")
    print(f"  Potential savings: ${savings:.2f}/month")
    print(f"  Cost reduction: {(savings / gpt4_monthly * 100):.1f}%")
    
    # Scenario 2: Implement caching
    print("\n2. SCENARIO: Implement Intelligent Caching")
    # Estimate 50% reduction in news API calls through caching
    news_requests_per_month = 30 * (10 * 3 + 5)  # 30 days * (10 stocks * 3 articles + 5 market news)
    news_cost_per_request = 0.001
    current_news_cost = max(0, (news_requests_per_month - 1000)) * news_cost_per_request  # After free tier
    
    cached_news_cost = current_news_cost * 0.5  # 50% reduction
    news_savings = current_news_cost - cached_news_cost
    
    print(f"  Current news API cost: ${current_news_cost:.2f}/month")
    print(f"  With caching: ${cached_news_cost:.2f}/month")
    print(f"  Potential savings: ${news_savings:.2f}/month")
    
    # Scenario 3: Reduce news articles per stock
    print("\n3. SCENARIO: Reduce News Articles per Stock")
    current_articles = 3
    reduced_articles = 2
    
    current_requests = 30 * (10 * current_articles + 5)
    reduced_requests = 30 * (10 * reduced_articles + 5)
    
    current_cost = max(0, (current_requests - 1000)) * 0.001
    reduced_cost = max(0, (reduced_requests - 1000)) * 0.001
    
    article_savings = current_cost - reduced_cost
    print(f"  Current articles per stock: {current_articles}")
    print(f"  Reduced articles per stock: {reduced_articles}")
    print(f"  Current cost: ${current_cost:.2f}/month")
    print(f"  Reduced cost: ${reduced_cost:.2f}/month")
    print(f"  Potential savings: ${article_savings:.2f}/month")
    
    # Total scenario savings
    total_scenario_savings = savings + news_savings + article_savings
    print(f"\nTotal scenario savings: ${total_scenario_savings:.2f}/month")

def test_budget_controls():
    """Test budget control features"""
    print("\n" + "=" * 60)
    print("BUDGET CONTROL TEST")
    print("=" * 60)
    
    # Simulate monthly budget tracking
    monthly_budget = 50.0  # $50/month budget
    
    costs = cost_analyzer.calculate_current_costs()
    total_cost = cost_analyzer.get_total_monthly_cost(costs)
    
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

def main():
    """Run all cost analysis tests"""
    try:
        # Test cost analysis
        costs, optimizations = test_cost_analysis()
        
        # Test cache manager
        cache_stats = test_cache_manager()
        
        # Test optimization scenarios
        test_cost_optimization_scenarios()
        
        # Test budget controls
        test_budget_controls()
        
        print("\n" + "=" * 60)
        print("COST ANALYSIS TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        # Summary
        total_cost = cost_analyzer.get_total_monthly_cost(costs)
        total_savings = sum(opt.potential_savings for opt in optimizations)
        
        print(f"\nSUMMARY:")
        print(f"  Current monthly cost: ${total_cost:.2f}")
        print(f"  Potential savings: ${total_savings:.2f}/month")
        print(f"  Cost reduction potential: {(total_savings / total_cost * 100):.1f}%")
        print(f"  Cache hit rate: {cache_stats.get('hit_rate_percent', 0):.1f}%")
        
        if total_cost > 100:
            print(f"\n⚠️  RECOMMENDATION: Current cost (${total_cost:.2f}) exceeds $100/month target")
            print("   Implement optimizations to reduce costs")
        else:
            print(f"\n✅ Current cost (${total_cost:.2f}) is within $100/month target")
        
    except Exception as e:
        logger.error(f"Error in cost analysis test: {str(e)}")
        print(f"Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main() 