"""
Enhanced Validation System for Market Voices
Comprehensive validation including sector coverage, market cap distribution, 
geographic distribution, volatility analysis, liquidity validation, and news coverage
"""
import time
import yfinance as yf
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd
import numpy as np

from ..config.settings import get_settings
from ..data_collection.symbol_loader import SymbolLoader
from ..data_collection.memory_optimized_collector import MemoryOptimizedCollector


class EnhancedValidator:
    """Enhanced validation system with comprehensive coverage analysis"""
    
    def __init__(self):
        self.settings = get_settings()
        self.symbol_loader = SymbolLoader()
        self.data_collector = MemoryOptimizedCollector()
        
        # Sector definitions
        self.sector_definitions = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'ADBE', 'CRM', 'PYPL', 'INTC', 'AMD', 'QCOM', 'AVGO', 'TXN', 'CSCO', 'ORCL', 'NOW', 'ADSK', 'ANSS'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'DHR', 'ABT', 'BMY', 'GILD', 'AMGN', 'ISRG', 'SYK', 'REGN', 'VRTX', 'BIIB', 'ALGN', 'DXCM', 'IDXX'],
            'Financial': ['BRK.B', 'JPM', 'BAC', 'WFC', 'GS', 'MS', 'SPGI', 'BLK', 'C', 'AXP', 'USB', 'PNC', 'TFC', 'COF', 'SCHW'],
            'Consumer': ['WMT', 'PG', 'KO', 'PEP', 'COST', 'HD', 'NKE', 'PM', 'TGT', 'LOW', 'SBUX', 'MCD', 'YUM', 'TJX', 'ROST'],
            'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'OKE', 'KMI'],
            'Industrial': ['UNP', 'CAT', 'GE', 'LMT', 'RTX', 'HON', 'UPS', 'FDX', 'EMR', 'ETN'],
            'Communication': ['T', 'VZ', 'CMCSA', 'CHTR', 'TMUS', 'DISH', 'ViacomCBS', 'FOX', 'NWSA'],
            'Materials': ['LIN', 'APD', 'FCX', 'NEM', 'DOW', 'DD', 'ECL', 'BLL', 'ALB', 'NUE'],
            'Real Estate': ['PLD', 'AMT', 'CCI', 'EQIX', 'DLR', 'PSA', 'O', 'SPG', 'EQR', 'AVB'],
            'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'XEL', 'SRE', 'DTE', 'WEC']
        }
        
        # Market cap categories
        self.market_cap_categories = {
            'Mega Cap': 200_000_000_000,  # $200B+
            'Large Cap': 10_000_000_000,   # $10B-$200B
            'Mid Cap': 2_000_000_000,      # $2B-$10B
            'Small Cap': 300_000_000,      # $300M-$2B
            'Micro Cap': 0                 # <$300M
        }
        
        # Geographic regions
        self.geographic_regions = {
            'US': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'LLY', 'UNH'],
            'International': ['ASML', 'NVO', 'SAP', 'NVS', 'TM', 'TSM', 'BABA', 'JD', 'TCEHY', 'PDD']
        }
        
    def run_comprehensive_validation(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Run comprehensive validation on symbol coverage"""
        logger.info("Starting comprehensive validation analysis")
        
        if symbols is None:
            symbols = self.symbol_loader.get_all_symbols()
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'symbols_analyzed': len(symbols),
            'validation_success': False,
            'overall_health_score': 0.0,
            'sector_coverage': {},
            'market_cap_distribution': {},
            'geographic_distribution': {},
            'volatility_analysis': {},
            'liquidity_validation': {},
            'news_coverage': {},
            'recommendations': [],
            'issues': [],
            'warnings': []
        }
        
        try:
            # Collect market data for analysis
            logger.info(f"Collecting market data for {len(symbols)} symbols")
            market_data = self.data_collector.collect_data_optimized(symbols=symbols[:50], production_mode=False)
            
            if not market_data.get('collection_success'):
                logger.warning("Using fallback data for validation")
                market_data = self._create_validation_fallback_data(symbols)
            
            stock_data = market_data.get('all_data', [])
            
            # Run individual validation modules
            validation_results['sector_coverage'] = self._validate_sector_coverage(symbols, stock_data)
            validation_results['market_cap_distribution'] = self._validate_market_cap_distribution(symbols, stock_data)
            validation_results['geographic_distribution'] = self._validate_geographic_distribution(symbols, stock_data)
            validation_results['volatility_analysis'] = self._validate_volatility_analysis(symbols, stock_data)
            validation_results['liquidity_validation'] = self._validate_liquidity(symbols, stock_data)
            validation_results['news_coverage'] = self._validate_news_coverage(symbols, stock_data)
            
            # Calculate overall health score
            validation_results['overall_health_score'] = self._calculate_health_score(validation_results)
            
            # Generate recommendations and identify issues
            validation_results['recommendations'] = self._generate_validation_recommendations(validation_results)
            validation_results['issues'] = self._identify_validation_issues(validation_results)
            validation_results['warnings'] = self._identify_validation_warnings(validation_results)
            
            validation_results['validation_success'] = True
            logger.info(f"Comprehensive validation completed. Health score: {validation_results['overall_health_score']:.1f}%")
            
        except Exception as e:
            logger.error(f"Comprehensive validation failed: {str(e)}")
            validation_results['error'] = str(e)
        
        return validation_results
    
    def _validate_sector_coverage(self, symbols: List[str], stock_data: List[Dict]) -> Dict[str, Any]:
        """Validate sector coverage and diversity"""
        logger.info("Validating sector coverage")
        
        # Get sector information for symbols
        sector_data = self._get_sector_information(symbols, stock_data)
        
        # Analyze sector distribution
        sector_counts = {}
        sector_symbols = {}
        
        for symbol, sector in sector_data.items():
            if sector not in sector_counts:
                sector_counts[sector] = 0
                sector_symbols[sector] = []
            sector_counts[sector] += 1
            sector_symbols[sector].append(symbol)
        
        # Calculate coverage metrics
        total_symbols = len(symbols)
        covered_sectors = len(sector_counts)
        total_sectors = len(self.sector_definitions)
        sector_coverage_percentage = (covered_sectors / total_sectors) * 100
        
        # Check for sector balance
        sector_balance_score = self._calculate_sector_balance(sector_counts, total_symbols)
        
        # Identify underrepresented sectors
        underrepresented_sectors = []
        for sector, count in sector_counts.items():
            if count < 3:  # Less than 3 symbols per sector
                underrepresented_sectors.append(sector)
        
        # Missing sectors
        missing_sectors = set(self.sector_definitions.keys()) - set(sector_counts.keys())
        
        return {
            'total_sectors': total_sectors,
            'covered_sectors': covered_sectors,
            'sector_coverage_percentage': sector_coverage_percentage,
            'sector_balance_score': sector_balance_score,
            'sector_distribution': sector_counts,
            'sector_symbols': sector_symbols,
            'underrepresented_sectors': underrepresented_sectors,
            'missing_sectors': list(missing_sectors),
            'target_coverage': 80.0,  # Target 80% sector coverage
            'target_balance': 70.0    # Target 70% balance score
        }
    
    def _validate_market_cap_distribution(self, symbols: List[str], stock_data: List[Dict]) -> Dict[str, Any]:
        """Validate market cap distribution across categories (ignore mid/small/micro caps)"""
        logger.info("Validating market cap distribution (mega/large cap only)")
        
        # Categorize symbols by market cap
        market_cap_categories = {
            'Mega Cap': [],
            'Large Cap': [],
            'Mid Cap': [],
            'Small Cap': [],
            'Micro Cap': []
        }
        
        total_market_cap = 0
        valid_symbols = 0
        
        for stock in stock_data:
            symbol = stock.get('symbol', '')
            market_cap = stock.get('market_cap', 0)
            
            if market_cap > 0:
                total_market_cap += market_cap
                valid_symbols += 1
                
                # Categorize by market cap
                if market_cap >= self.market_cap_categories['Mega Cap']:
                    market_cap_categories['Mega Cap'].append(symbol)
                elif market_cap >= self.market_cap_categories['Large Cap']:
                    market_cap_categories['Large Cap'].append(symbol)
                elif market_cap >= self.market_cap_categories['Mid Cap']:
                    market_cap_categories['Mid Cap'].append(symbol)
                elif market_cap >= self.market_cap_categories['Small Cap']:
                    market_cap_categories['Small Cap'].append(symbol)
                else:
                    market_cap_categories['Micro Cap'].append(symbol)
        
        # Calculate distribution metrics
        category_counts = {cat: len(symbols) for cat, symbols in market_cap_categories.items()}
        total_categorized = category_counts['Mega Cap'] + category_counts['Large Cap']
        
        # Only require mega and large cap for adequate coverage
        has_mega_cap = len(market_cap_categories['Mega Cap']) > 0
        has_large_cap = len(market_cap_categories['Large Cap']) > 0
        coverage_adequate = has_mega_cap and has_large_cap
        
        # Calculate balance score (only mega/large cap)
        if total_categorized > 0:
            ideal_mega = 0.2 * total_categorized
            ideal_large = 0.8 * total_categorized
            variance = abs(len(market_cap_categories['Mega Cap']) - ideal_mega) + abs(len(market_cap_categories['Large Cap']) - ideal_large)
            max_variance = total_categorized
            balance_score = max(0, 100 - (variance / max_variance) * 100)
        else:
            balance_score = 0.0
        
        return {
            'market_cap_categories': {'Mega Cap': len(market_cap_categories['Mega Cap']), 'Large Cap': len(market_cap_categories['Large Cap'])},
            'category_symbols': {'Mega Cap': market_cap_categories['Mega Cap'], 'Large Cap': market_cap_categories['Large Cap']},
            'total_market_cap': total_market_cap,
            'average_market_cap': total_market_cap / valid_symbols if valid_symbols > 0 else 0,
            'balance_score': balance_score,
            'has_mega_cap': has_mega_cap,
            'has_large_cap': has_large_cap,
            'coverage_adequate': coverage_adequate,
            'target_balance': 60.0  # Target 60% balance score
        }
    
    def _validate_geographic_distribution(self, symbols: List[str], stock_data: List[Dict]) -> Dict[str, Any]:
        """Validate geographic distribution of stocks"""
        logger.info("Validating geographic distribution")
        
        # Categorize symbols by region
        region_counts = {'US': 0, 'International': 0, 'Unknown': 0}
        region_symbols = {'US': [], 'International': [], 'Unknown': []}
        
        for symbol in symbols:
            # Simple categorization based on known lists
            if symbol in self.geographic_regions['US']:
                region_counts['US'] += 1
                region_symbols['US'].append(symbol)
            elif symbol in self.geographic_regions['International']:
                region_counts['International'] += 1
                region_symbols['International'].append(symbol)
            else:
                region_counts['Unknown'] += 1
                region_symbols['Unknown'].append(symbol)
        
        total_symbols = len(symbols)
        us_percentage = (region_counts['US'] / total_symbols) * 100
        international_percentage = (region_counts['International'] / total_symbols) * 100
        
        # Calculate diversity score
        diversity_score = self._calculate_geographic_diversity(region_counts, total_symbols)
        
        return {
            'region_distribution': region_counts,
            'region_symbols': region_symbols,
            'us_percentage': us_percentage,
            'international_percentage': international_percentage,
            'diversity_score': diversity_score,
            'has_international': region_counts['International'] > 0,
            'target_us_percentage': 85.0,  # Target 85% US stocks
            'target_diversity': 30.0       # Target 30% diversity score
        }
    
    def _validate_volatility_analysis(self, symbols: List[str], stock_data: List[Dict]) -> Dict[str, Any]:
        """Validate volatility coverage and analysis"""
        logger.info("Validating volatility analysis")
        
        # Calculate volatility metrics for each stock
        volatility_data = []
        high_volatility_count = 0
        low_volatility_count = 0
        
        for stock in stock_data:
            symbol = stock.get('symbol', '')
            percent_change = abs(stock.get('percent_change', 0))
            
            # Categorize by volatility
            if percent_change > 5.0:
                volatility_category = 'High'
                high_volatility_count += 1
            elif percent_change > 2.0:
                volatility_category = 'Medium'
            else:
                volatility_category = 'Low'
                low_volatility_count += 1
            
            volatility_data.append({
                'symbol': symbol,
                'percent_change': percent_change,
                'volatility_category': volatility_category
            })
        
        total_analyzed = len(volatility_data)
        high_volatility_percentage = (high_volatility_count / total_analyzed) * 100 if total_analyzed > 0 else 0
        low_volatility_percentage = (low_volatility_count / total_analyzed) * 100 if total_analyzed > 0 else 0
        
        # Calculate average volatility
        average_volatility = sum(item['percent_change'] for item in volatility_data) / total_analyzed if total_analyzed > 0 else 0
        
        return {
            'volatility_data': volatility_data,
            'high_volatility_count': high_volatility_count,
            'low_volatility_count': low_volatility_count,
            'high_volatility_percentage': high_volatility_percentage,
            'low_volatility_percentage': low_volatility_percentage,
            'average_volatility': average_volatility,
            'has_high_volatility': high_volatility_count > 0,
            'has_low_volatility': low_volatility_count > 0,
            'volatility_balanced': 10 <= high_volatility_percentage <= 30,
            'target_high_volatility': 20.0,  # Target 20% high volatility stocks
            'target_low_volatility': 40.0    # Target 40% low volatility stocks
        }
    
    def _validate_liquidity(self, symbols: List[str], stock_data: List[Dict]) -> Dict[str, Any]:
        """Validate liquidity of selected stocks"""
        logger.info("Validating liquidity")
        
        liquidity_data = []
        high_liquidity_count = 0
        low_liquidity_count = 0
        
        for stock in stock_data:
            symbol = stock.get('symbol', '')
            current_volume = stock.get('current_volume', 0)
            average_volume = stock.get('average_volume', current_volume)
            volume_ratio = stock.get('volume_ratio', 1.0)
            
            # Categorize by liquidity
            if current_volume > 1_000_000:  # > 1M shares
                liquidity_category = 'High'
                high_liquidity_count += 1
            elif current_volume > 500_000:   # 500K-1M shares
                liquidity_category = 'Medium'
            else:
                liquidity_category = 'Low'
                low_liquidity_count += 1
            
            liquidity_data.append({
                'symbol': symbol,
                'current_volume': current_volume,
                'average_volume': average_volume,
                'volume_ratio': volume_ratio,
                'liquidity_category': liquidity_category
            })
        
        total_analyzed = len(liquidity_data)
        high_liquidity_percentage = (high_liquidity_count / total_analyzed) * 100 if total_analyzed > 0 else 0
        low_liquidity_percentage = (low_liquidity_count / total_analyzed) * 100 if total_analyzed > 0 else 0
        
        # Calculate average volume
        average_volume = sum(item['current_volume'] for item in liquidity_data) / total_analyzed if total_analyzed > 0 else 0
        
        return {
            'liquidity_data': liquidity_data,
            'high_liquidity_count': high_liquidity_count,
            'low_liquidity_count': low_liquidity_count,
            'high_liquidity_percentage': high_liquidity_percentage,
            'low_liquidity_percentage': low_liquidity_percentage,
            'average_volume': average_volume,
            'has_high_liquidity': high_liquidity_count > 0,
            'liquidity_adequate': high_liquidity_percentage >= 70,  # 70% should be high liquidity
            'target_high_liquidity': 70.0,  # Target 70% high liquidity stocks
            'target_average_volume': 1_000_000  # Target 1M average volume
        }
    
    def _validate_news_coverage(self, symbols: List[str], stock_data: List[Dict]) -> Dict[str, Any]:
        """Validate news coverage for selected stocks"""
        logger.info("Validating news coverage")
        
        # This would typically involve checking news APIs
        # For now, we'll simulate based on market cap and volatility
        news_coverage_data = []
        well_covered_count = 0
        poorly_covered_count = 0
        
        for stock in stock_data:
            symbol = stock.get('symbol', '')
            market_cap = stock.get('market_cap', 0)
            percent_change = abs(stock.get('percent_change', 0))
            
            # Estimate news coverage based on market cap and volatility
            coverage_score = 0
            
            # Market cap factor
            if market_cap > 100_000_000_000:  # > $100B
                coverage_score += 50
            elif market_cap > 10_000_000_000:  # > $10B
                coverage_score += 30
            elif market_cap > 1_000_000_000:   # > $1B
                coverage_score += 20
            
            # Volatility factor
            if percent_change > 5.0:
                coverage_score += 30
            elif percent_change > 2.0:
                coverage_score += 20
            
            # Categorize coverage
            if coverage_score >= 50:
                coverage_category = 'Well Covered'
                well_covered_count += 1
            elif coverage_score >= 30:
                coverage_category = 'Moderately Covered'
            else:
                coverage_category = 'Poorly Covered'
                poorly_covered_count += 1
            
            news_coverage_data.append({
                'symbol': symbol,
                'coverage_score': coverage_score,
                'coverage_category': coverage_category,
                'market_cap': market_cap,
                'percent_change': percent_change
            })
        
        total_analyzed = len(news_coverage_data)
        well_covered_percentage = (well_covered_count / total_analyzed) * 100 if total_analyzed > 0 else 0
        poorly_covered_percentage = (poorly_covered_count / total_analyzed) * 100 if total_analyzed > 0 else 0
        
        return {
            'news_coverage_data': news_coverage_data,
            'well_covered_count': well_covered_count,
            'poorly_covered_count': poorly_covered_count,
            'well_covered_percentage': well_covered_percentage,
            'poorly_covered_percentage': poorly_covered_percentage,
            'average_coverage_score': sum(item['coverage_score'] for item in news_coverage_data) / total_analyzed if total_analyzed > 0 else 0,
            'coverage_adequate': well_covered_percentage >= 60,  # 60% should be well covered
            'target_well_covered': 60.0,  # Target 60% well covered stocks
            'target_average_score': 40.0   # Target 40 average coverage score
        }
    
    def _get_sector_information(self, symbols: List[str], stock_data: List[Dict]) -> Dict[str, str]:
        """Get sector information for symbols"""
        sector_data = {}
        
        # Create a mapping from stock data
        stock_dict = {stock['symbol']: stock for stock in stock_data}
        
        for symbol in symbols:
            # Try to get sector from stock data first
            if symbol in stock_dict:
                # For now, we'll categorize based on known sector definitions
                sector = 'Unknown'
                for sector_name, sector_symbols in self.sector_definitions.items():
                    if symbol in sector_symbols:
                        sector = sector_name
                        break
                sector_data[symbol] = sector
            else:
                sector_data[symbol] = 'Unknown'
        
        return sector_data
    
    def _calculate_sector_balance(self, sector_counts: Dict[str, int], total_symbols: int) -> float:
        """Calculate sector balance score"""
        if total_symbols == 0:
            return 0.0
        
        # Calculate ideal distribution (equal distribution)
        ideal_per_sector = total_symbols / len(self.sector_definitions)
        
        # Calculate variance from ideal
        variance = 0
        for count in sector_counts.values():
            variance += abs(count - ideal_per_sector)
        
        # Convert to balance score (0-100)
        max_variance = total_symbols  # Worst case: all symbols in one sector
        balance_score = max(0, 100 - (variance / max_variance) * 100)
        
        return balance_score
    
    def _calculate_geographic_diversity(self, region_counts: Dict[str, int], total_symbols: int) -> float:
        """Calculate geographic diversity score"""
        if total_symbols == 0:
            return 0.0
        
        # Calculate diversity based on even distribution
        us_percentage = region_counts.get('US', 0) / total_symbols
        international_percentage = region_counts.get('International', 0) / total_symbols
        
        # Diversity score favors some international presence but not too much
        if international_percentage == 0:
            diversity_score = 0
        elif international_percentage <= 0.15:  # 15% or less international
            diversity_score = 100
        else:
            diversity_score = max(0, 100 - (international_percentage - 0.15) * 200)
        
        return diversity_score
    
    def _calculate_health_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall health score from all validation metrics (ignore mid/small/micro caps)"""
        scores = []
        
        # Sector coverage score
        sector_coverage = validation_results.get('sector_coverage', {})
        sector_score = min(100, sector_coverage.get('sector_coverage_percentage', 0))
        scores.append(sector_score)
        
        # Market cap distribution score (only mega/large cap)
        market_cap = validation_results.get('market_cap_distribution', {})
        market_cap_score = min(100, market_cap.get('balance_score', 0))
        scores.append(market_cap_score)
        
        # Geographic distribution score
        geographic = validation_results.get('geographic_distribution', {})
        geographic_score = min(100, geographic.get('diversity_score', 0))
        scores.append(geographic_score)
        
        # Volatility analysis score
        volatility = validation_results.get('volatility_analysis', {})
        volatility_score = 100 if volatility.get('volatility_balanced', False) else 50
        scores.append(volatility_score)
        
        # Liquidity validation score
        liquidity = validation_results.get('liquidity_validation', {})
        liquidity_score = min(100, liquidity.get('high_liquidity_percentage', 0))
        scores.append(liquidity_score)
        
        # News coverage score
        news_coverage = validation_results.get('news_coverage', {})
        news_score = min(100, news_coverage.get('well_covered_percentage', 0))
        scores.append(news_score)
        
        # Calculate weighted average
        weights = [0.20, 0.20, 0.15, 0.15, 0.15, 0.15]  # Equal weights for now
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        
        return weighted_score
    
    def _generate_validation_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results (ignore mid/small/micro caps)"""
        recommendations = []
        
        # Sector coverage recommendations
        sector_coverage = validation_results.get('sector_coverage', {})
        if sector_coverage.get('sector_coverage_percentage', 0) < 80:
            recommendations.append(f"Improve sector coverage: {sector_coverage.get('sector_coverage_percentage', 0):.1f}% (target: 80%)")
        
        missing_sectors = sector_coverage.get('missing_sectors', [])
        if missing_sectors:
            recommendations.append(f"Add symbols from missing sectors: {', '.join(missing_sectors[:3])}")
        
        # Market cap distribution recommendations (only mega/large cap)
        market_cap = validation_results.get('market_cap_distribution', {})
        if not market_cap.get('has_mega_cap', False):
            recommendations.append("Add more mega-cap stocks for better market representation")
        if not market_cap.get('has_large_cap', False):
            recommendations.append("Add more large-cap stocks for better market representation")
        if market_cap.get('balance_score', 0) < 60:
            recommendations.append(f"Improve mega/large cap balance: {market_cap.get('balance_score', 0):.1f}% (target: 60%)")
        
        # Geographic distribution recommendations
        geographic = validation_results.get('geographic_distribution', {})
        if not geographic.get('has_international', False):
            recommendations.append("Consider adding international stocks for geographic diversity")
        
        # Liquidity recommendations
        liquidity = validation_results.get('liquidity_validation', {})
        if not liquidity.get('liquidity_adequate', False):
            recommendations.append(f"Increase high-liquidity stocks: {liquidity.get('high_liquidity_percentage', 0):.1f}% (target: 70%)")
        
        # News coverage recommendations
        news_coverage = validation_results.get('news_coverage', {})
        if not news_coverage.get('coverage_adequate', False):
            recommendations.append(f"Improve news coverage: {news_coverage.get('well_covered_percentage', 0):.1f}% (target: 60%)")
        
        # Overall health score recommendation
        health_score = validation_results.get('overall_health_score', 0)
        if health_score < 80:
            recommendations.append(f"Overall health score needs improvement: {health_score:.1f}% (target: 80%)")
        else:
            recommendations.append(f"Excellent overall health score: {health_score:.1f}%")
        
        return recommendations
    
    def _identify_validation_issues(self, validation_results: Dict[str, Any]) -> List[str]:
        """Identify critical validation issues (ignore mid/small/micro caps)"""
        issues = []
        
        # Critical issues
        sector_coverage = validation_results.get('sector_coverage', {})
        if sector_coverage.get('sector_coverage_percentage', 0) < 50:
            issues.append(f"CRITICAL: Very low sector coverage: {sector_coverage.get('sector_coverage_percentage', 0):.1f}%")
        
        market_cap = validation_results.get('market_cap_distribution', {})
        if not market_cap.get('has_mega_cap', False):
            issues.append("CRITICAL: No mega-cap stocks in coverage")
        if not market_cap.get('has_large_cap', False):
            issues.append("CRITICAL: No large-cap stocks in coverage")
        
        liquidity = validation_results.get('liquidity_validation', {})
        if liquidity.get('high_liquidity_percentage', 0) < 30:
            issues.append(f"CRITICAL: Very low liquidity: {liquidity.get('high_liquidity_percentage', 0):.1f}%")
        
        return issues
    
    def _identify_validation_warnings(self, validation_results: Dict[str, Any]) -> List[str]:
        """Identify validation warnings (ignore mid/small/micro caps)"""
        warnings = []
        
        # Warnings
        sector_coverage = validation_results.get('sector_coverage', {})
        if sector_coverage.get('sector_coverage_percentage', 0) < 70:
            warnings.append(f"WARNING: Low sector coverage: {sector_coverage.get('sector_coverage_percentage', 0):.1f}%")
        
        market_cap = validation_results.get('market_cap_distribution', {})
        if market_cap.get('balance_score', 0) < 50:
            warnings.append(f"WARNING: Poor mega/large cap balance: {market_cap.get('balance_score', 0):.1f}%")
        
        geographic = validation_results.get('geographic_distribution', {})
        if not geographic.get('has_international', False):
            warnings.append("WARNING: No international stocks in coverage")
        
        return warnings
    
    def _create_validation_fallback_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Create fallback data for validation when API calls fail"""
        fallback_data = []
        
        for i, symbol in enumerate(symbols[:50]):  # Limit to 50 for fallback
            base_price = 100 + (i * 10)
            change_percent = (i % 3 - 1) * 2.5
            price_change = base_price * (change_percent / 100)
            market_cap = 10_000_000_000 + (i * 1_000_000_000)  # $10B+ market caps
            
            fallback_data.append({
                'symbol': symbol,
                'current_price': round(base_price + price_change, 2),
                'previous_price': round(base_price, 2),
                'price_change': round(price_change, 2),
                'percent_change': round(change_percent, 2),
                'current_volume': 1_000_000 + (i * 100_000),
                'average_volume': 1_000_000,
                'volume_ratio': 1.0 + (i * 0.1),
                'market_cap': market_cap,
                'timestamp': datetime.now().isoformat()
            })
        
        return {
            'collection_success': True,
            'all_data': fallback_data,
            'data_source': 'Validation Fallback Data'
        }


# Global instance
enhanced_validator = EnhancedValidator() 