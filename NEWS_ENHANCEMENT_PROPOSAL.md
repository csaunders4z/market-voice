# Proposal: Enhanced News Content Integration for Increased Script Length

## Current State
- **News summaries**: Only created for stocks with >3% moves
- **Content used**: Only headlines (titles), not article descriptions
- **News per company**: 3-5 headlines, but descriptions not included
- **Result**: Scripts are 545 words vs 1200-1500 target

## Proposed Solution

### 1. Create Comprehensive News Summaries for ALL Stocks
**Current**: Only stocks with >3% moves get news summaries  
**Proposed**: Generate rich news summaries for ALL winners and losers

**Implementation**:
- Create new method: `create_comprehensive_news_summary(symbol, articles)`
- Combine 3-5 most relevant articles per stock
- Include both titles AND descriptions
- Create a structured summary format

### 2. Enhanced News Summary Format
**Current Format**:
```
News Summary: "Article Title (via Source)"
Recent Headlines:
- Headline 1
- Headline 2
- Headline 3
```

**Proposed Format**:
```
COMPREHENSIVE NEWS SUMMARY:
Recent Developments:
1. [Article Title] (Source: [Source])
   Summary: [Article description - 2-3 sentences]
   
2. [Article Title] (Source: [Source])
   Summary: [Article description - 2-3 sentences]
   
3. [Article Title] (Source: [Source])
   Summary: [Article description - 2-3 sentences]

Key Themes: [Extracted themes from all articles]
Market Context: [How this relates to the stock movement]
```

### 3. New Method: `create_comprehensive_news_summary()`

**Location**: `src/data_collection/news_collector.py`

**Functionality**:
- Takes symbol and list of articles
- Selects top 3-5 most relevant articles
- Extracts and formats:
  - Article titles
  - Article descriptions (full, not truncated)
  - Sources
  - Publication dates
- Identifies common themes across articles
- Creates market context linking news to stock movement

### 4. Update News Collection for Winners/Losers

**Current**: News summaries only for >3% moves  
**Proposed**: Generate comprehensive summaries for ALL top 5 winners and top 5 losers

**Implementation**:
- In `get_market_news()`, after collecting company news:
  - For each winner/loser stock:
    - Get all collected articles for that symbol
    - Call `create_comprehensive_news_summary()` 
    - Store in `news_summaries[symbol]` with rich format

### 5. Enhanced Prompt Integration

**Current**: News shown as simple list  
**Proposed**: Rich, structured news context section

**New Prompt Section**:
```
DETAILED NEWS CONTEXT FOR EACH STOCK:

[Stock Name] ([Symbol]):
COMPREHENSIVE NEWS SUMMARY:
[Full formatted summary with descriptions]

USE THIS NEWS CONTENT TO:
- Expand your segment to 200-300 words
- Discuss specific developments mentioned in articles
- Reference article sources when relevant
- Connect news themes to stock price movement
- Provide context and analysis based on these developments
```

### 6. Prompt Instructions Update

Add explicit requirement:
```
CRITICAL: For each stock segment, you MUST:
1. Reference at least 2-3 specific news developments from the provided summaries
2. Discuss article descriptions in detail (not just mention headlines)
3. Connect news themes to the stock's price movement
4. Use this content to reach 200-300 words per stock segment
5. If news is available, it should be the PRIMARY content for expanding the segment
```

## Expected Impact

### Content Length Increase
- **Current**: ~70 words per stock segment
- **Target**: 200-300 words per stock segment
- **Method**: Using article descriptions (typically 50-150 words each) × 3-5 articles = 150-750 words of source material per stock

### Quality Improvements
- More substantive analysis using actual news content
- Better causal explanations (from article descriptions)
- More professional content (real news sources)
- Natural content expansion

## Implementation Steps

1. **Add `create_comprehensive_news_summary()` method** to `NewsCollector`
2. **Update `get_market_news()`** to generate summaries for all winners/losers
3. **Modify `create_script_prompt()`** to include rich news format
4. **Update prompt instructions** to emphasize using news descriptions
5. **Test with production run** to verify word count increase

## Code Structure

```python
def create_comprehensive_news_summary(self, symbol: str, company_name: str, 
                                      articles: List[Dict], 
                                      percent_change: float) -> str:
    """Create a comprehensive news summary combining multiple articles"""
    if not articles:
        return ""
    
    # Select top 3-5 most relevant articles
    sorted_articles = sorted(articles, 
                            key=lambda x: x.get('relevance_score', 0), 
                            reverse=True)[:5]
    
    summary_parts = []
    summary_parts.append(f"COMPREHENSIVE NEWS SUMMARY FOR {company_name} ({symbol}):\n")
    summary_parts.append(f"Stock Movement: {percent_change:+.2f}%\n")
    summary_parts.append("\nRecent Developments:\n")
    
    for i, article in enumerate(sorted_articles, 1):
        title = article.get('title', '')
        description = article.get('description', '')
        source = article.get('source', 'Unknown')
        published = article.get('published_at', '')
        
        summary_parts.append(f"{i}. {title}\n")
        summary_parts.append(f"   Source: {source}\n")
        if description:
            # Use full description, not truncated
            summary_parts.append(f"   Summary: {description}\n")
        summary_parts.append("\n")
    
    # Extract common themes
    themes = self._extract_themes(sorted_articles)
    if themes:
        summary_parts.append(f"Key Themes: {', '.join(themes)}\n")
    
    return "".join(summary_parts)
```

## Benefits

1. **Significant content expansion**: 3-5 article descriptions per stock = 150-750 words of source material
2. **Better quality**: Real news content vs generic statements
3. **More professional**: References to actual sources and developments
4. **Natural expansion**: AI has rich content to discuss in detail
5. **Target achievement**: Should easily reach 200-300 words per segment

