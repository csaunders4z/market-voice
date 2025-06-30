#!/usr/bin/env python3
"""
Market Voices - Main Application
Automated stock market video generation system
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import setup_logging, get_logger
from src.data_collection.stock_data import stock_collector
from src.script_generation.script_generator import script_generator
from src.content_validation.quality_controls import quality_controller
from src.config.settings import get_settings
from src.config.security import security_config
from src.config.logging_config import secure_logging

# Load environment variables
load_dotenv()

class MarketVoicesApp:
    """Main application class for Market Voices"""
    
    def __init__(self):
        # Setup secure logging first
        self._setup_secure_logging()
        self.logger = get_logger("MarketVoices")
        
        # Run security audit
        self._run_security_audit()
        
        # Secure file permissions
        self._secure_file_permissions()
        
        self.output_dir = Path(get_settings().output_directory)
        self.output_dir.mkdir(exist_ok=True)
        
    def _setup_secure_logging(self):
        """Setup secure logging with rotation and filtering"""
        log_level = os.getenv("LOG_LEVEL", "INFO")
        enable_file_logging = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
        
        secure_logging.setup_logging(
            log_level=log_level,
            enable_file_logging=enable_file_logging
        )
        
    def _run_security_audit(self):
        """Run security audit before starting"""
        audit_results = security_config.run_security_audit()
        
        if audit_results['recommendations']:
            print("\n⚠️  SECURITY WARNINGS:")
            for rec in audit_results['recommendations']:
                print(f"  - {rec}")
            print()
        
        # Log audit results
        logger = get_logger("Security")
        logger.info(f"Security audit completed - {len(audit_results['recommendations'])} issues found")
        
    def _secure_file_permissions(self):
        """Secure file permissions"""
        security_config.secure_env_file()
        security_config.secure_output_directories()
        
    def run_daily_workflow(self) -> Dict:
        """Run the complete daily workflow"""
        self.logger.info("Starting Market Voices daily workflow")
        
        workflow_result = {
            'workflow_success': False,
            'timestamp': datetime.now().isoformat(),
            'steps': {}
        }
        
        try:
            # Step 1: Collect market data
            self.logger.info("Step 1: Collecting market data")
            market_data = stock_collector.run_daily_collection()
            workflow_result['steps']['data_collection'] = market_data
            
            if not market_data.get('collection_success', False):
                self.logger.error("Data collection failed")
                return workflow_result
            
            # Step 2: Generate script
            self.logger.info("Step 2: Generating script")
            script_data = script_generator.generate_script(market_data)
            workflow_result['steps']['script_generation'] = script_data
            
            if not script_data.get('generation_success', False):
                self.logger.error("Script generation failed")
                return workflow_result
            
            # Step 3: Validate quality
            self.logger.info("Step 3: Validating content quality")
            quality_results = quality_controller.validate_script_quality(script_data)
            workflow_result['steps']['quality_validation'] = quality_results
            
            # Step 4: Save outputs
            self.logger.info("Step 4: Saving outputs")
            self._save_outputs(market_data, script_data, quality_results)
            
            # Step 5: Cleanup old logs
            self.logger.info("Step 5: Cleaning up old logs")
            secure_logging.cleanup_old_logs(days=30)
            
            workflow_result['workflow_success'] = True
            self.logger.info("Daily workflow completed successfully")
            
        except Exception as e:
            self.logger.error(f"Workflow error: {str(e)}")
            workflow_result['error'] = str(e)
        
        return workflow_result
    
    def _save_outputs(self, market_data: Dict, script_data: Dict, quality_results: Dict):
        """Save all outputs to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save market data
        market_file = self.output_dir / f"market_data_{timestamp}.json"
        with open(market_file, 'w') as f:
            json.dump(market_data, f, indent=2, default=str)
        self.logger.info(f"Market data saved to {market_file}")
        
        # Save script
        script_file = self.output_dir / f"script_{timestamp}.json"
        with open(script_file, 'w') as f:
            json.dump(script_data, f, indent=2, default=str)
        self.logger.info(f"Script saved to {script_file}")
        
        # Save formatted script
        formatted_script = script_generator.format_script_for_output(script_data)
        formatted_file = self.output_dir / f"script_formatted_{timestamp}.txt"
        with open(formatted_file, 'w') as f:
            f.write(formatted_script)
        self.logger.info(f"Formatted script saved to {formatted_file}")
        
        # Save quality results
        quality_file = self.output_dir / f"quality_report_{timestamp}.json"
        with open(quality_file, 'w') as f:
            json.dump(quality_results, f, indent=2, default=str)
        self.logger.info(f"Quality report saved to {quality_file}")
        
        # Save summary
        summary = self._create_summary(market_data, script_data, quality_results)
        summary_file = self.output_dir / f"daily_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(summary)
        self.logger.info(f"Daily summary saved to {summary_file}")
    
    def _create_summary(self, market_data: Dict, script_data: Dict, quality_results: Dict) -> str:
        """Create a human-readable summary of the daily run"""
        summary_lines = []
        summary_lines.append("=" * 80)
        summary_lines.append("MARKET VOICES - DAILY SUMMARY")
        summary_lines.append("=" * 80)
        summary_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        
        # Market data summary
        market_summary = market_data.get('market_summary', {})
        summary_lines.append("MARKET DATA:")
        summary_lines.append(f"- Total stocks analyzed: {market_summary.get('total_stocks', 0)}")
        summary_lines.append(f"- Advancing stocks: {market_summary.get('advancing_stocks', 0)}")
        summary_lines.append(f"- Declining stocks: {market_summary.get('declining_stocks', 0)}")
        summary_lines.append(f"- Average change: {market_summary.get('average_change', 0):.2f}%")
        summary_lines.append("")
        
        # Top movers
        winners = market_data.get('winners', [])
        losers = market_data.get('losers', [])
        
        summary_lines.append("TOP 5 WINNERS:")
        for i, winner in enumerate(winners[:5], 1):
            summary_lines.append(f"{i}. {winner['symbol']}: +{winner['percent_change']:.2f}%")
        
        summary_lines.append("")
        summary_lines.append("TOP 5 LOSERS:")
        for i, loser in enumerate(losers[:5], 1):
            summary_lines.append(f"{i}. {loser['symbol']}: {loser['percent_change']:.2f}%")
        
        summary_lines.append("")
        
        # Script summary
        summary_lines.append("SCRIPT GENERATION:")
        summary_lines.append(f"- Lead host: {script_data.get('lead_host', 'Unknown').title()}")
        summary_lines.append(f"- Estimated runtime: {script_data.get('estimated_runtime_minutes', 0)} minutes")
        summary_lines.append(f"- Segments: {len(script_data.get('segments', []))}")
        
        balance = script_data.get('speaking_time_balance', {})
        summary_lines.append(f"- Speaking balance: Marcus {balance.get('marcus_percentage', 0)}%, Suzanne {balance.get('suzanne_percentage', 0)}%")
        summary_lines.append("")
        
        # Quality summary
        summary_lines.append("QUALITY VALIDATION:")
        summary_lines.append(f"- Overall score: {quality_results.get('overall_score', 0):.1f}%")
        summary_lines.append(f"- Issues: {len(quality_results.get('issues', []))}")
        summary_lines.append(f"- Warnings: {len(quality_results.get('warnings', []))}")
        summary_lines.append(f"- Passed checks: {len(quality_results.get('passed_checks', []))}")
        
        if quality_results.get('issues'):
            summary_lines.append("")
            summary_lines.append("CRITICAL ISSUES:")
            for issue in quality_results['issues'][:3]:  # Show first 3
                summary_lines.append(f"- {str(issue)}")
        
        summary_lines.append("")
        summary_lines.append("=" * 80)
        
        return "\n".join(str(line) for line in summary_lines)
    
    def run_test_mode(self):
        """Run in test mode with sample data"""
        self.logger.info("Running in test mode")
        
        # Create sample market data
        sample_market_data = {
            'market_summary': {
                'total_stocks': 100,
                'advancing_stocks': 65,
                'declining_stocks': 35,
                'average_change': 0.85,
                'total_volume': 2500000000,
                'market_date': datetime.now().isoformat()
            },
            'winners': [
                {'symbol': 'AAPL', 'company_name': 'Apple Inc.', 'current_price': 150.25, 'percent_change': 3.2},
                {'symbol': 'MSFT', 'company_name': 'Microsoft Corporation', 'current_price': 320.50, 'percent_change': 2.8},
                {'symbol': 'GOOGL', 'company_name': 'Alphabet Inc.', 'current_price': 2800.00, 'percent_change': 2.1},
                {'symbol': 'AMZN', 'company_name': 'Amazon.com Inc.', 'current_price': 3200.75, 'percent_change': 1.9},
                {'symbol': 'NVDA', 'company_name': 'NVIDIA Corporation', 'current_price': 450.30, 'percent_change': 1.7}
            ],
            'losers': [
                {'symbol': 'TSLA', 'company_name': 'Tesla Inc.', 'current_price': 800.50, 'percent_change': -2.1},
                {'symbol': 'META', 'company_name': 'Meta Platforms Inc.', 'current_price': 280.25, 'percent_change': -1.8},
                {'symbol': 'NFLX', 'company_name': 'Netflix Inc.', 'current_price': 450.75, 'percent_change': -1.5},
                {'symbol': 'ADBE', 'company_name': 'Adobe Inc.', 'current_price': 380.00, 'percent_change': -1.2},
                {'symbol': 'CRM', 'company_name': 'Salesforce Inc.', 'current_price': 220.50, 'percent_change': -0.9}
            ],
            'collection_success': True
        }
        
        # Run workflow with sample data
        workflow_result = {
            'workflow_success': False,
            'timestamp': datetime.now().isoformat(),
            'steps': {}
        }
        
        try:
            # Step 1: Use sample market data
            workflow_result['steps']['data_collection'] = sample_market_data
            
            # Step 2: Generate script
            self.logger.info("Generating script with sample data")
            script_data = script_generator.generate_script(sample_market_data)
            workflow_result['steps']['script_generation'] = script_data
            
            if script_data.get('generation_success', False):
                # Step 3: Validate quality
                quality_results = quality_controller.validate_script_quality(script_data)
                workflow_result['steps']['quality_validation'] = quality_results
                
                # Step 4: Save outputs
                self._save_outputs(sample_market_data, script_data, quality_results)
                
                workflow_result['workflow_success'] = True
                self.logger.info("Test mode completed successfully")
            else:
                self.logger.error("Script generation failed in test mode")
                
        except Exception as e:
            self.logger.error(f"Test mode error: {str(e)}")
            workflow_result['error'] = str(e)
        
        return workflow_result


def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    logger = get_logger("Main")
    
    logger.info("Market Voices starting up")
    
    # Check if running in test mode
    test_mode = "--test" in sys.argv or "-t" in sys.argv
    
    # Create and run application
    app = MarketVoicesApp()
    
    if test_mode:
        logger.info("Running in test mode")
        result = app.run_test_mode()
    else:
        logger.info("Running in production mode")
        result = app.run_daily_workflow()
    
    # Print summary
    if result.get('workflow_success', False):
        logger.info("✅ Workflow completed successfully")
        print("\n" + "="*50)
        print("✅ MARKET VOICES COMPLETED SUCCESSFULLY")
        print("="*50)
        print(f"Outputs saved to: {get_settings().output_directory}")
        print("Check the output directory for generated files.")
    else:
        logger.error("❌ Workflow failed")
        print("\n" + "="*50)
        print("❌ MARKET VOICES FAILED")
        print("="*50)
        if 'error' in result:
            print(f"Error: {result['error']}")
        print("Check the logs for more details.")
    
    return 0 if result.get('workflow_success', False) else 1


if __name__ == "__main__":
    exit(main()) 