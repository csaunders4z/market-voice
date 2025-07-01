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

from ..config.settings import get_settings


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
        """Fetch current NASDAQ-100 symbols from multiple sources"""
        try:
            logger.info("Fetching current NASDAQ-100 symbols...")
            
            # Try multiple sources for NASDAQ-100
            sources = [
                self._fetch_nasdaq100_from_stockanalysis,
                self._fetch_nasdaq100_from_wikipedia,
                self._fetch_nasdaq100_from_invesco,
                self._fetch_nasdaq100_from_yahoo
            ]
            
            for source_func in sources:
                try:
                    symbols = source_func()
                    if symbols and len(symbols) >= 95:  # NASDAQ-100 should have ~100 symbols
                        logger.info(f"Successfully fetched {len(symbols)} NASDAQ-100 symbols from {source_func.__name__}")
                        logger.debug(f"First 10 NASDAQ-100 symbols: {symbols[:10]}")
                        return symbols
                except Exception as e:
                    logger.warning(f"Failed to fetch from source {source_func.__name__}: {str(e)}")
                    continue
            
            logger.error("All NASDAQ-100 sources failed")
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch NASDAQ-100 symbols: {str(e)}")
            return []
    
    def _fetch_nasdaq100_from_stockanalysis(self) -> List[str]:
        """Fetch NASDAQ-100 from StockAnalysis.com (reliable backup source)"""
        try:
            logger.info("Fetching NASDAQ-100 from StockAnalysis.com...")
            
            url = "https://stockanalysis.com/list/nasdaq-100-stocks/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML table
            tables = pd.read_html(response.text)
            
            # Find the table with NASDAQ-100 constituents
            for table in tables:
                if 'Symbol' in table.columns:
                    symbols = table['Symbol'].dropna().tolist()
                    # Clean symbols (remove any non-alphabetic characters and convert to uppercase)
                    symbols = [str(s).strip().upper() for s in symbols if str(s).strip().isalpha()]
                    if len(symbols) >= 95:  # Should have around 100 symbols
                        logger.info(f"Successfully parsed {len(symbols)} symbols from StockAnalysis.com")
                        return symbols
            
            logger.warning("Could not find NASDAQ-100 table in StockAnalysis.com")
            return []
            
        except Exception as e:
            logger.warning(f"StockAnalysis.com fetch failed: {str(e)}")
            return []
    
    def _fetch_nasdaq100_from_wikipedia(self) -> List[str]:
        """Fetch NASDAQ-100 from Wikipedia"""
        try:
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
                        return [str(s).strip() for s in symbols if str(s).strip()]
            
            return []
            
        except Exception as e:
            logger.warning(f"Wikipedia fetch failed: {str(e)}")
            return []
    
    def _fetch_nasdaq100_from_invesco(self) -> List[str]:
        """Fetch NASDAQ-100 from Invesco (QQQ holdings)"""
        try:
            # Invesco QQQ holdings page
            url = "https://www.invesco.com/us/financial-products/etfs/holdings?audienceType=Investor&ticker=QQQ"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # This would require more sophisticated parsing
            # For now, return empty to try other sources
            return []
            
        except Exception as e:
            logger.warning(f"Invesco fetch failed: {str(e)}")
            return []
    
    def _fetch_nasdaq100_from_yahoo(self) -> List[str]:
        """Fetch NASDAQ-100 from Yahoo Finance"""
        try:
            # Yahoo Finance NASDAQ-100 page
            url = "https://finance.yahoo.com/quote/%5ENDX/holdings"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # This would require more sophisticated parsing
            # For now, return empty to try other sources
            return []
            
        except Exception as e:
            logger.warning(f"Yahoo Finance fetch failed: {str(e)}")
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


# Global instance
symbol_updater = SymbolUpdater()


def main():
    """Main function to update symbols"""
    logger.info("Starting symbol update process...")
    
    try:
        # Update symbols
        symbols = symbol_updater.update_fallback_symbols()
        
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