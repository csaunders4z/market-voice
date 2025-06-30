#!/usr/bin/env python3
"""
Symbol Coverage Maintenance Script for Market Voices
Run this script daily/weekly to validate symbol coverage and ensure future-proofing
"""
import os
import sys
import json
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import modules
from src.data_collection.symbol_loader import symbol_loader


def run_daily_maintenance():
    """Run daily symbol coverage maintenance"""
    logger.info("=" * 80)
    logger.info("DAILY SYMBOL COVERAGE MAINTENANCE")
    logger.info("=" * 80)
    logger.info(f"Maintenance timestamp: {datetime.now().isoformat()}")
    
    try:
        # Force refresh and validate
        logger.info("\n🔄 FORCING SYMBOL REFRESH AND VALIDATION")
        logger.info("-" * 50)
        
        maintenance_result = symbol_loader.force_refresh_and_validate()
        
        if not maintenance_result.get('validation_success'):
            logger.error(f"❌ Maintenance failed: {maintenance_result.get('error', 'Unknown error')}")
            return False
        
        # Display maintenance summary
        nasdaq_validation = maintenance_result.get('nasdaq_100_validation', {})
        sp500_validation = maintenance_result.get('sp_500_validation', {})
        market_cap_validation = maintenance_result.get('market_cap_validation', {})
        
        logger.info("\n📊 MAINTENANCE SUMMARY")
        logger.info("-" * 50)
        
        # Calculate health scores
        nasdaq_score = nasdaq_validation.get('coverage_percentage', 0)
        sp500_score = sp500_validation.get('coverage_percentage', 0)
        market_cap_score = market_cap_validation.get('coverage_percentage', 0)
        overall_score = (nasdaq_score + sp500_score + market_cap_score) / 3
        
        logger.info(f"Overall Health Score: {overall_score:.1f}%")
        logger.info(f"NASDAQ-100 Health: {nasdaq_score:.1f}% ({nasdaq_validation.get('total_symbols', 0)} symbols)")
        logger.info(f"S&P 500 Health: {sp500_score:.1f}% ({sp500_validation.get('total_symbols', 0)} symbols)")
        logger.info(f"Market Cap Health: {market_cap_score:.1f}%")
        
        # Display issues and recommendations
        issues = maintenance_result.get('coverage_issues', [])
        recommendations = maintenance_result.get('recommendations', [])
        
        if issues:
            logger.warning(f"\n⚠️  COVERAGE ISSUES ({len(issues)}):")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info(f"\n✅ NO COVERAGE ISSUES FOUND!")
        
        if recommendations:
            logger.info(f"\n💡 RECOMMENDATIONS ({len(recommendations)}):")
            for rec in recommendations:
                logger.info(f"  - {rec}")
        
        # Save maintenance report
        logger.info("\n💾 SAVING MAINTENANCE REPORT")
        logger.info("-" * 50)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        maintenance_file = f"output/maintenance_report_{timestamp}.json"
        
        # Add maintenance metadata
        maintenance_result['maintenance_metadata'] = {
            'maintenance_type': 'daily_symbol_validation',
            'timestamp': datetime.now().isoformat(),
            'overall_health_score': overall_score,
            'health_status': get_health_status(overall_score),
            'action_required': len(issues) > 0
        }
        
        os.makedirs("output", exist_ok=True)
        with open(maintenance_file, 'w', encoding='utf-8') as f:
            json.dump(maintenance_result, f, indent=2, default=str)
        
        logger.info(f"✅ Maintenance report saved to: {maintenance_file}")
        
        # Generate action items
        action_items = generate_action_items(maintenance_result)
        
        if action_items:
            logger.info(f"\n🎯 ACTION ITEMS ({len(action_items)}):")
            for item in action_items:
                logger.info(f"  - {item}")
        
        # Final status
        logger.info("\n" + "=" * 80)
        if overall_score >= 95:
            logger.info("🟢 EXCELLENT: Symbol coverage is comprehensive and healthy")
        elif overall_score >= 90:
            logger.info("🟡 GOOD: Symbol coverage is adequate with minor issues")
        elif overall_score >= 80:
            logger.info("🟠 FAIR: Symbol coverage needs attention")
        else:
            logger.info("🔴 POOR: Symbol coverage needs immediate attention")
        
        logger.info(f"Maintenance completed successfully at {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Daily maintenance failed: {str(e)}")
        return False


def run_weekly_maintenance():
    """Run weekly symbol coverage maintenance with enhanced checks"""
    logger.info("=" * 80)
    logger.info("WEEKLY SYMBOL COVERAGE MAINTENANCE")
    logger.info("=" * 80)
    logger.info(f"Maintenance timestamp: {datetime.now().isoformat()}")
    
    try:
        # Run daily maintenance first
        daily_ok = run_daily_maintenance()
        
        if not daily_ok:
            logger.error("❌ Daily maintenance failed, skipping weekly checks")
            return False
        
        # Additional weekly checks
        logger.info("\n📈 WEEKLY ENHANCED CHECKS")
        logger.info("-" * 50)
        
        # Check symbol list consistency
        logger.info("Checking symbol list consistency...")
        nasdaq_symbols = set(symbol_loader.get_nasdaq_100_symbols())
        sp500_symbols = set(symbol_loader.get_sp_500_symbols())
        all_symbols = set(symbol_loader.get_all_symbols())
        
        # Check for duplicates
        duplicates = nasdaq_symbols.intersection(sp500_symbols)
        if duplicates:
            logger.info(f"Found {len(duplicates)} symbols in both NASDAQ-100 and S&P 500 (expected)")
        
        # Check for missing critical symbols
        critical_symbols = {
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
            "BRK.B", "LLY", "UNH", "V", "XOM", "JNJ", "WMT", "JPM"
        }
        
        missing_critical = critical_symbols - all_symbols
        if missing_critical:
            logger.warning(f"Missing critical symbols: {missing_critical}")
        else:
            logger.info("✅ All critical symbols present")
        
        # Check symbol count trends
        logger.info("Checking symbol count trends...")
        logger.info(f"Total unique symbols: {len(all_symbols)}")
        logger.info(f"NASDAQ-100 symbols: {len(nasdaq_symbols)}")
        logger.info(f"S&P 500 symbols: {len(sp500_symbols)}")
        
        # Weekly recommendations
        weekly_recommendations = []
        
        if len(nasdaq_symbols) < 90:
            weekly_recommendations.append("Consider expanding NASDAQ-100 coverage")
        
        if len(sp500_symbols) < 450:
            weekly_recommendations.append("Consider expanding S&P 500 coverage")
        
        if len(all_symbols) < 200:
            weekly_recommendations.append("Consider expanding overall symbol coverage")
        
        if weekly_recommendations:
            logger.info(f"\n📋 WEEKLY RECOMMENDATIONS:")
            for rec in weekly_recommendations:
                logger.info(f"  - {rec}")
        else:
            logger.info("\n✅ No weekly recommendations")
        
        logger.info("\n🎉 Weekly maintenance completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Weekly maintenance failed: {str(e)}")
        return False


def get_health_status(score):
    """Get health status based on score"""
    if score >= 95:
        return "EXCELLENT"
    elif score >= 90:
        return "GOOD"
    elif score >= 80:
        return "FAIR"
    else:
        return "POOR"


def generate_action_items(maintenance_result):
    """Generate actionable items based on maintenance results"""
    action_items = []
    
    nasdaq_validation = maintenance_result.get('nasdaq_100_validation', {})
    sp500_validation = maintenance_result.get('sp_500_validation', {})
    issues = maintenance_result.get('coverage_issues', [])
    
    # Count issues
    if not nasdaq_validation.get('count_valid', False):
        action_items.append("Investigate NASDAQ-100 symbol count discrepancy")
    
    if not sp500_validation.get('count_valid', False):
        action_items.append("Investigate S&P 500 symbol count discrepancy")
    
    if nasdaq_validation.get('coverage_percentage', 0) < 95:
        action_items.append("Review NASDAQ-100 critical symbol coverage")
    
    if sp500_validation.get('coverage_percentage', 0) < 95:
        action_items.append("Review S&P 500 critical symbol coverage")
    
    # Missing symbols
    missing_nasdaq = nasdaq_validation.get('missing_critical', [])
    missing_sp500 = sp500_validation.get('missing_critical', [])
    
    if missing_nasdaq:
        action_items.append(f"Add missing NASDAQ-100 symbols: {', '.join(missing_nasdaq[:3])}")
    
    if missing_sp500:
        action_items.append(f"Add missing S&P 500 symbols: {', '.join(missing_sp500[:3])}")
    
    # If no issues, add positive action
    if not action_items:
        action_items.append("Continue monitoring symbol coverage (all systems healthy)")
    
    return action_items


def main():
    """Main maintenance function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Symbol Coverage Maintenance')
    parser.add_argument('--weekly', action='store_true', help='Run weekly maintenance')
    parser.add_argument('--daily', action='store_true', help='Run daily maintenance (default)')
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    if args.weekly:
        logger.info("Running WEEKLY symbol coverage maintenance")
        success = run_weekly_maintenance()
    else:
        logger.info("Running DAILY symbol coverage maintenance")
        success = run_daily_maintenance()
    
    if success:
        logger.info("\n✅ Maintenance completed successfully!")
        return 0
    else:
        logger.error("\n❌ Maintenance failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 