# News Collection Enhancement Plan
**Date**: July 1, 2025  
**Priority**: CRITICAL - Fixes script generation quality issues

## 🎯 **Problem Statement**

The Market Voices system has excellent technical infrastructure but poor script quality because **we collect insufficient news data to explain stock movements**. The current system:

- Only collects news for stocks moving >3%
- Provides shallow headline summaries instead of explanatory content
- Lacks stock-specific causal analysis
- Results in generic, template-based scripts instead of data-driven narratives

## 🚀 **Solution: Multi-Source News Intelligence System**

### **Phase 1: Immediate Fixes (Week 1)**

#### **1.1 Expand News Collection Coverage**
**Current**: Only stocks with >3% moves  
**New**: Collect news for ALL top 10 winners and losers

```python
# Enhanced company news collection
def get_comprehensive_stock_news(self, symbol: str, company_name: str, percent_change: float) -> Dict:
    """Get comprehensive news explaining stock movement"""
    
    # Collect from multiple timeframes
    news_sources = {
        'today': self.get_multi_source_news(symbol, hours_back=24),
        'recent': self.get_multi_source_news(symbol, hours_back=168),  # 7 days
        'earnings': self.get_earnings_related_news(symbol),
        'analyst': self.get_analyst_coverage(symbol),
        'sector': self.get_sector_news(symbol)
    }
    
    # Analyze and synthesize
    return self.synthesize_stock_story(symbol, news_sources, percent_change)
```

#### **1.2 Add Free News Sources**
**Problem**: Over-reliance on paid APIs  
**Solution**: Add comprehensive free sources

```python
# Free news sources to add
FREE_NEWS_SOURCES = {
    'yahoo_finance': f'https://finance.yahoo.com/quote/{symbol}/news',
    'marketwatch': f'https://www.marketwatch.com/investing/stock/{symbol}',
    'seeking_alpha': f'https://seekingalpha.com/symbol/{symbol}/news',
    'benzinga': f'https://www.benzinga.com/quote/{symbol}',
    'fool': f'https://www.fool.com/quote/nasdaq/{symbol}/',
    'finviz': f'https://finviz.com/quote.ashx?t={symbol}',
    'investing_com': f'https://www.investing.com/search/?q={symbol}',
    'reuters': f'https://www.reuters.com/companies/{symbol}',
    'bloomberg': f'https://www.bloomberg.com/quote/{symbol}',
    'cnbc': f'https://www.cnbc.com/quotes/{symbol}'
}
```

#### **1.3 Web Scraping for Stock-Specific News**
```python
class StockNewsScaper:
    """Scrape free financial news sources for stock-specific content"""
    
    def scrape_yahoo_finance_news(self, symbol: str) -> List[Dict]:
        """Scrape Yahoo Finance news for specific stock"""
        
    def scrape_seeking_alpha_articles(self, symbol: str) -> List[Dict]:
        """Scrape Seeking Alpha for detailed analysis"""
        
    def scrape_marketwatch_stories(self, symbol: str) -> List[Dict]:
        """Scrape MarketWatch for recent stories"""
```

### **Phase 2: Intelligence Layer (Week 2)**

#### **2.1 News Analysis Engine**
```python
class NewsIntelligenceEngine:
    """Analyze news to extract stock movement catalysts"""
    
    def identify_catalysts(self, symbol: str, news_articles: List[Dict]) -> Dict:
        """Identify specific catalysts driving stock movement"""
        return {
            'earnings_surprise': self.analyze_earnings_impact(news_articles),
            'analyst_actions': self.extract_analyst_changes(news_articles),
            'product_announcements': self.find_product_news(news_articles),
            'regulatory_news': self.identify_regulatory_impacts(news_articles),
            'partnership_deals': self.find_partnership_news(news_articles),
            'guidance_changes': self.extract_guidance_updates(news_articles),
            'sector_trends': self.analyze_sector_momentum(news_articles)
        }
    
    def generate_movement_explanation(self, symbol: str, catalysts: Dict, percent_change: float) -> str:
        """Generate detailed explanation of why stock moved"""
```

#### **2.2 Market Context Engine**
```python
class MarketContextAnalyzer:
    """Provide broader market context for stock movements"""
    
    def analyze_sector_rotation(self, symbol: str) -> Dict:
        """Analyze if move is part of broader sector rotation"""
        
    def identify_market_themes(self, all_movers: List[Dict]) -> List[str]:
        """Identify common themes across market movers"""
        # Examples: "AI momentum", "Rate cut anticipation", "Earnings season"
        
    def connect_macro_events(self, movement_date: str) -> Dict:
        """Connect stock moves to macro events (Fed meetings, economic data)"""
```

### **Phase 3: Content Generation Enhancement (Week 3)**

#### **3.1 Story Templates Based on Catalysts**
```python
CATALYST_TEMPLATES = {
    'earnings_beat': "{symbol} surged {percent_change}% following a {metric} earnings beat. The company reported {actual} vs {expected} expected, with {key_metric} driving the outperformance. {analyst_quote}",
    
    'analyst_upgrade': "{symbol} jumped {percent_change}% after {analyst_firm} upgraded the stock from {old_rating} to {new_rating}, citing {reasoning}. The new price target of ${target} represents {upside}% upside.",
    
    'product_launch': "{symbol} gained {percent_change}% on news of {product_announcement}. The {product_category} is expected to {impact_description} and could contribute ${revenue_estimate} in additional revenue.",
    
    'regulatory_approval': "{symbol} spiked {percent_change}% after {regulatory_body} approved {product/service}. This opens up a ${market_size} market opportunity for the company."
}
```

#### **3.2 Enhanced Script Generator Integration**
```python
def create_enhanced_script_prompt(self, market_data: Dict, detailed_news: Dict) -> str:
    """Create script prompt with comprehensive news integration"""
    
    # For each stock, include:
    # - Specific movement catalyst
    # - Supporting news sources
    # - Analyst opinions
    # - Market context
    # - Forward-looking statements
    
    for stock in winners:
        catalyst_analysis = detailed_news.get(symbol, {})
        prompt += f"""
        {symbol} Analysis (Host: {host}):
        Movement: {percent_change}% ({explain_magnitude})
        Primary Catalyst: {catalyst_analysis.get('primary_catalyst')}
        Supporting Evidence: {catalyst_analysis.get('evidence')}
        Market Context: {catalyst_analysis.get('market_context')}
        Analyst Perspective: {catalyst_analysis.get('analyst_view')}
        What to Watch: {catalyst_analysis.get('forward_looking')}
        Sources: {catalyst_analysis.get('sources')}
        """
```

## 📊 **Implementation Timeline**

### **Week 1: Foundation (July 1-7)**
- [ ] **Day 1-2**: Implement free news source scraping
- [ ] **Day 3-4**: Expand news collection to all top movers
- [ ] **Day 5**: Test enhanced news collection
- [ ] **Day 6-7**: Integrate with script generator

### **Week 2: Intelligence (July 8-14)**
- [ ] **Day 1-3**: Build news analysis engine
- [ ] **Day 4-5**: Implement catalyst identification
- [ ] **Day 6-7**: Add market context analysis

### **Week 3: Integration (July 15-21)**
- [ ] **Day 1-3**: Enhance script generation with detailed news
- [ ] **Day 4-5**: Create story templates
- [ ] **Day 6-7**: Full system testing

## 🎯 **Expected Outcomes**

### **Content Quality Improvements**
- **Script Quality Score**: 50% → 85%+
- **Content Length**: 655 words → 1440+ words
- **Explanatory Depth**: Template-based → Data-driven narratives
- **News Integration**: Headlines only → Comprehensive catalyst analysis

### **Script Content Enhancement**
Instead of: *"Apple gained 2.8% today as tech stocks performed well."*

We'll have: *"Apple surged 2.8% following its stronger-than-expected iPhone 15 sales data released this morning. Wedbush analysts raised their price target from $200 to $220, citing robust demand in China and the upcoming AI integration features. The move comes as the broader tech sector rotates into hardware plays ahead of the holiday season, with Apple's ecosystem advantage positioning it well for the AI revolution. Trading volume was 2.3x normal, suggesting institutional accumulation. Watch for management commentary on AI monetization during next week's earnings call."*

## 🛠 **Technical Implementation**

### **New Files to Create**
```
src/data_collection/
├── stock_news_scraper.py        # Free news source scraping
├── news_intelligence.py         # Catalyst analysis engine
├── market_context_analyzer.py   # Broader market themes
└── story_synthesizer.py         # Generate explanatory narratives

src/script_generation/
├── catalyst_templates.py        # Story templates by catalyst type
└── enhanced_prompt_builder.py   # Build detailed prompts with news
```

### **Modified Files**
```
src/data_collection/
├── news_collector.py           # Add comprehensive stock news collection
└── unified_data_collector.py   # Integrate enhanced news data

src/script_generation/
└── script_generator.py         # Use detailed news in prompt creation
```

## 🚨 **Risk Mitigation**

### **Technical Risks**
- **Web Scraping Stability**: Implement robust error handling and fallbacks
- **Rate Limiting**: Respect robots.txt and implement delays
- **Data Quality**: Validate news content relevance and accuracy

### **Legal Considerations**
- **Fair Use**: Only extract headlines and brief summaries
- **Attribution**: Always cite original sources
- **Robots.txt Compliance**: Respect website scraping policies

## 📈 **Success Metrics**

### **Immediate (Week 1)**
- [ ] News collection for 100% of top movers (vs current ~30%)
- [ ] Average 3+ news sources per stock (vs current 0-1)
- [ ] 200+ words of explanatory content per stock (vs current ~20)

### **Short-term (Week 2-3)**
- [ ] Script quality score >80% (vs current 50%)
- [ ] Content length >1440 words (vs current 655)
- [ ] Specific catalyst identification for 90% of moves

### **Medium-term (Month 1)**
- [ ] Automated daily news intelligence reports
- [ ] Market theme identification and tracking
- [ ] Predictive catalyst monitoring

## 💰 **Cost Analysis**

### **Current Costs**
- News APIs: ~$50/month
- Limited coverage and depth

### **Enhanced System Costs**
- Free news scraping: $0
- Additional processing: ~$10/month compute
- **Total**: ~$60/month (20% increase for 300%+ content improvement)

## 🎯 **Conclusion**

This enhancement plan addresses the root cause of script quality issues by:

1. **Collecting comprehensive news** for all significant movers
2. **Analyzing news to identify movement catalysts**
3. **Providing detailed explanatory content** instead of generic templates
4. **Integrating market context** and forward-looking analysis

**Priority**: Implement Phase 1 immediately to fix the 50% script quality score blocking production deployment.

---

**Next Steps**: 
1. Approve this enhancement plan
2. Begin implementation of free news source scraping
3. Test enhanced news collection with current script generator
4. Measure improvement in script quality scores

**Timeline**: 3 weeks to transform script generation quality from 50% to 85%+