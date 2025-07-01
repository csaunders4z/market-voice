#!/usr/bin/env python3
"""
Symbol updater for Market Voices
Fetches current S&P 500 and NASDAQ-100 symbols from reliable sources
"""
import requests
import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime
from loguru import logger
import json
import os
import sys

# Add src to path
sys.path.append('src')

from src.config.settings import get_settings


class SymbolUpdater:
    """Updates symbol lists from reliable sources"""
    
    def __init__(self):
        self.settings = get_settings()
        self.output_dir = "src/data_collection/symbol_lists"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def fetch_sp500_symbols(self) -> List[str]:
        """Fetch current S&P 500 symbols from DataHub"""
        try:
            logger.info("Fetching current S&P 500 symbols from DataHub...")
            
            # Fetch from DataHub CSV
            url = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            df = pd.read_csv(url)
            symbols = df['Symbol'].tolist()
            
            logger.info(f"Successfully fetched {len(symbols)} S&P 500 symbols")
            logger.debug(f"First 10 S&P 500 symbols: {symbols[:10]}")
            
            return symbols
            
        except Exception as e:
            logger.error(f"Failed to fetch S&P 500 symbols: {str(e)}")
            return []
    
    def fetch_nasdaq100_symbols(self) -> List[str]:
        """Fetch current NASDAQ-100 symbols from Wikipedia"""
        try:
            logger.info("Fetching current NASDAQ-100 symbols from Wikipedia...")
            
            # Wikipedia table URL for NASDAQ-100
            url = "https://en.wikipedia.org/wiki/Nasdaq-100"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML table
            tables = pd.read_html(response.text)
            
            # Find the table with NASDAQ-100 constituents
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    symbol_col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                    symbols = table[symbol_col].dropna().tolist()
                    if len(symbols) >= 95:
                        symbols = [str(s).strip() for s in symbols if str(s).strip()]
                        logger.info(f"Successfully fetched {len(symbols)} NASDAQ-100 symbols")
                        logger.debug(f"First 10 NASDAQ-100 symbols: {symbols[:10]}")
                        return symbols
            
            logger.warning("Could not find NASDAQ-100 table in Wikipedia")
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch NASDAQ-100 symbols: {str(e)}")
            return []
    
    def create_comprehensive_symbol_list(self) -> Dict[str, List[str]]:
        """Create comprehensive symbol list with both indices"""
        logger.info("Creating comprehensive symbol list...")
        
        # Fetch current symbols
        sp500_symbols = self.fetch_sp500_symbols()
        nasdaq100_symbols = self.fetch_nasdaq100_symbols()
        
        # Create comprehensive list
        all_symbols = list(set(sp500_symbols + nasdaq100_symbols))
        
        # Categorize symbols
        sp500_only = [s for s in sp500_symbols if s not in nasdaq100_symbols]
        nasdaq100_only = [s for s in nasdaq100_symbols if s not in sp500_symbols]
        both_indices = [s for s in sp500_symbols if s in nasdaq100_symbols]
        
        symbol_data = {
            'all_symbols': all_symbols,
            'sp500_symbols': sp500_symbols,
            'nasdaq100_symbols': nasdaq100_symbols,
            'sp500_only': sp500_only,
            'nasdaq100_only': nasdaq100_only,
            'both_indices': both_indices,
            'last_updated': datetime.now().isoformat(),
            'total_symbols': len(all_symbols),
            'sp500_count': len(sp500_symbols),
            'nasdaq100_count': len(nasdaq100_symbols)
        }
        
        # Save to file
        self._save_symbol_data(symbol_data)
        
        logger.info(f"Comprehensive symbol list created:")
        logger.info(f"  Total unique symbols: {len(all_symbols)}")
        logger.info(f"  S&P 500 symbols: {len(sp500_symbols)}")
        logger.info(f"  NASDAQ-100 symbols: {len(nasdaq100_symbols)}")
        logger.info(f"  Symbols in both indices: {len(both_indices)}")
        
        return symbol_data
    
    def _save_symbol_data(self, symbol_data: Dict):
        """Save symbol data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comprehensive data
        comprehensive_file = f"{self.output_dir}/comprehensive_symbols_{timestamp}.json"
        with open(comprehensive_file, 'w') as f:
            json.dump(symbol_data, f, indent=2)
        
        # Save current symbols (latest)
        current_file = f"{self.output_dir}/current_symbols.json"
        with open(current_file, 'w') as f:
            json.dump(symbol_data, f, indent=2)
        
        # Save individual lists
        sp500_file = f"{self.output_dir}/sp500_symbols_{timestamp}.txt"
        with open(sp500_file, 'w') as f:
            f.write('\n'.join(symbol_data['sp500_symbols']))
        
        nasdaq100_file = f"{self.output_dir}/nasdaq100_symbols_{timestamp}.txt"
        with open(nasdaq100_file, 'w') as f:
            f.write('\n'.join(symbol_data['nasdaq100_symbols']))
        
        all_symbols_file = f"{self.output_dir}/all_symbols_{timestamp}.txt"
        with open(all_symbols_file, 'w') as f:
            f.write('\n'.join(symbol_data['all_symbols']))
        
        logger.info(f"Symbol data saved to {self.output_dir}/")
    
    def update_fallback_symbols(self) -> List[str]:
        """Update the fallback symbols in FMP collector"""
        try:
            # Get current symbols
            symbol_data = self.create_comprehensive_symbol_list()
            
            # Update the FMP collector's fallback symbols
            self._update_fmp_fallback_symbols(symbol_data['all_symbols'])
            
            logger.info("Fallback symbols updated successfully")
            return symbol_data['all_symbols']
            
        except Exception as e:
            logger.error(f"Failed to update fallback symbols: {str(e)}")
            return []
    
    def _update_fmp_fallback_symbols(self, symbols: List[str]):
        """Update the fallback symbols in the FMP collector file"""
        try:
            # Read current FMP file
            fmp_file = "src/data_collection/fmp_stock_data.py"
            with open(fmp_file, 'r') as f:
                content = f.read()
            
            # Create new fallback symbols list
            symbols_str = ',\n            '.join([f'"{s}"' for s in symbols])
            new_fallback = f'''    def _use_fallback_symbols(self):
        """Use a comprehensive fallback list of current S&P 500 and NASDAQ-100 stocks"""
        self.symbols = [
            {symbols_str}
        ]
        logger.info(f"Using comprehensive fallback list with {{len(self.symbols)}} unique S&P 500 and NASDAQ-100 symbols")'''
            
            # Replace the old fallback method
            import re
            pattern = r'def _use_fallback_symbols\(self\):.*?logger\.info\(f"Using comprehensive fallback list'
            replacement = new_fallback
            
            # Use re.DOTALL to match across multiple lines
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            # Write back to file
            with open(fmp_file, 'w') as f:
                f.write(new_content)
            
            logger.info(f"Updated fallback symbols in {fmp_file}")
            
        except Exception as e:
            logger.error(f"Failed to update FMP file: {str(e)}")


def main():
    """Main function to update symbols"""
    logger.info("Starting symbol update process...")
    
    try:
        updater = SymbolUpdater()
        
        # Update symbols
        symbols = updater.update_fallback_symbols()
        
        if symbols:
            logger.info(f"✅ Symbol update completed successfully!")
            logger.info(f"   Total symbols: {len(symbols)}")
            logger.info(f"   Files saved to: src/data_collection/symbol_lists/")
        else:
            logger.error("❌ Symbol update failed!")
            
    except Exception as e:
        logger.error(f"Symbol update failed: {str(e)}")


if __name__ == "__main__":
    main() 