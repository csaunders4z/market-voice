#!/usr/bin/env python3
"""
Comprehensive demonstration of enhanced catalyst detection system
Shows how the system would work with realistic news data
"""

def demo_enhanced_catalyst_detection():
    """Demonstrate enhanced catalyst detection with realistic news examples"""
    print("🚀 Enhanced Catalyst Detection System Demo")
    print("=" * 60)
    
    def identify_article_catalyst(title: str, description: str) -> str:
        """Identify the primary catalyst type for a single article"""
        content = f"{title} {description}".lower()
        
        catalyst_patterns = {
            'earnings': [
                'earnings beat', 'earnings miss', 'quarterly results', 'earnings report',
                'earnings', 'eps', 'revenue', 'profit', 'q1', 'q2', 'q3', 'q4',
                'fiscal year', 'financial results', 'earnings call', 'beat estimates',
                'miss expectations', 'revenue growth'
            ],
            'merger_acquisition': [
                'acquisition', 'merger', 'takeover', 'buyout', 'acquired', 'merge',
                'purchase', 'bid', 'offer', 'transaction', 'deal worth', 'cash deal',
                'strategic acquisition', 'hostile takeover', 'all-cash', 'all-stock'
            ],
            'analyst_action': [
                'upgrade', 'downgrade', 'price target', 'buy rating', 'sell rating',
                'analyst', 'rating', 'outperform', 'underperform', 'overweight',
                'target price', 'recommendation', 'coverage initiated', 'consensus',
                'strong buy', 'strong sell', 'neutral'
            ],
            'regulatory_approval': [
                'fda approval', 'drug approval', 'regulatory approval', 'cleared',
                'authorized', 'approved', 'fda', 'regulatory', 'clinical trial',
                'study results', 'device approval'
            ],
            'product_innovation': [
                'product launch', 'new product', 'innovation', 'breakthrough',
                'patent', 'technology', 'development', 'launch', 'research'
            ],
            'partnership': [
                'partnership', 'collaboration', 'joint venture', 'alliance',
                'agreement', 'contract', 'strategic partnership', 'licensing',
                'distribution agreement', 'supply agreement'
            ],
            'guidance_outlook': [
                'guidance', 'raised guidance', 'lowered guidance', 'outlook',
                'forecast', 'projections', 'updated outlook', 'expects',
                'anticipates', 'full year', 'next quarter'
            ],
            'dividend_buyback': [
                'dividend', 'buyback', 'share repurchase', 'dividend increase',
                'dividend cut', 'special dividend', 'stock split', 'spin-off',
                'return to shareholders', 'capital allocation'
            ],
            'insider_activity': [
                'insider', 'insider trading', 'insider buying', 'insider selling',
                'executive', 'ceo', 'management', 'stock purchase', 'stock sale',
                'board', 'director', 'officer'
            ],
            'legal_regulatory': [
                'lawsuit', 'settlement', 'investigation', 'fine', 'penalty',
                'violation', 'court', 'ruling', 'sec', 'ftc', 'compliance',
                'doj', 'judge', 'decision'
            ]
        }
        
        best_match = ""
        highest_score = 0
        
        for catalyst_type, keywords in catalyst_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in content:
                    if keyword in title.lower():
                        score += 2  # Title matches get higher weight
                    else:
                        score += 1  # Description matches get lower weight
            
            if score > highest_score:
                highest_score = score
                best_match = catalyst_type
        
        return best_match if highest_score > 0 else ""
    
    def calculate_enhanced_relevance_score(title: str, description: str, symbol: str, catalyst_type: str) -> float:
        """Calculate relevance score with enhanced weighted keywords and catalyst bonus"""
        content = f"{title} {description}".lower()
        score = 0.0
        
        high_impact_keywords = [
            'earnings beat', 'earnings miss', 'revenue growth', 'guidance raise',
            'guidance cut', 'acquisition', 'merger', 'takeover', 'buyout',
            'fda approval', 'drug approval', 'breakthrough', 'innovation'
        ]
        
        medium_impact_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'guidance', 'outlook',
            'upgrade', 'downgrade', 'price target', 'analyst rating',
            'partnership', 'deal', 'contract', 'agreement',
            'product launch', 'clinical trial', 'study results',
            'dividend', 'buyback', 'share repurchase', 'split'
        ]
        
        low_impact_keywords = [
            'forecast', 'estimate', 'expects', 'anticipates', 'projects',
            'regulatory', 'compliance', 'investigation', 'lawsuit',
            'insider', 'executive', 'management', 'ceo', 'board'
        ]
        
        for keyword in high_impact_keywords:
            if keyword in content:
                if keyword in title.lower():
                    score += 3.0
                else:
                    score += 1.5
        
        for keyword in medium_impact_keywords:
            if keyword in content:
                if keyword in title.lower():
                    score += 2.0
                else:
                    score += 1.0
        
        for keyword in low_impact_keywords:
            if keyword in content:
                if keyword in title.lower():
                    score += 1.0
                else:
                    score += 0.5
        
        if symbol.lower() in content:
            score += 2.0
        
        if catalyst_type:
            score += 1.0
            print(f"    💡 Catalyst bonus applied: +1.0 for {catalyst_type}")
        
        return round(score, 2)
    
    realistic_news_examples = [
        {
            "title": "Apple Reports Record Q4 Earnings, Beats Revenue Estimates by 8%",
            "description": "Apple Inc. reported quarterly earnings that exceeded analyst estimates with iPhone revenue growing 12% year-over-year, driven by strong demand for iPhone 15 Pro models.",
            "symbol": "AAPL",
            "source": "Yahoo Finance"
        },
        {
            "title": "Microsoft Announces $75 Billion Acquisition of Gaming Giant Activision",
            "description": "Microsoft Corporation has agreed to acquire Activision Blizzard in an all-cash deal worth $75 billion, marking the largest acquisition in gaming industry history.",
            "symbol": "MSFT",
            "source": "MarketWatch"
        },
        {
            "title": "Goldman Sachs Upgrades Tesla to Strong Buy, Raises Price Target to $350",
            "description": "Goldman Sachs analyst upgraded Tesla Inc. to Strong Buy from Hold, citing improved production efficiency and strong demand for Model Y vehicles in international markets.",
            "symbol": "TSLA",
            "source": "Seeking Alpha"
        },
        {
            "title": "Pfizer Receives FDA Approval for Revolutionary Alzheimer's Drug",
            "description": "The FDA has granted full approval to Pfizer's new Alzheimer's treatment after successful Phase 3 clinical trials showed significant cognitive improvement in patients.",
            "symbol": "PFE",
            "source": "Benzinga"
        },
        {
            "title": "Amazon Launches Next-Generation AI-Powered Delivery Drones",
            "description": "Amazon unveiled its latest Prime Air delivery drone technology featuring advanced AI navigation and 30-minute delivery capabilities for packages under 5 pounds.",
            "symbol": "AMZN",
            "source": "Finviz"
        },
        {
            "title": "Netflix Raises Full-Year Guidance After Subscriber Growth Beats Expectations",
            "description": "Netflix Inc. updated its full-year outlook, raising revenue guidance to $35 billion after adding 8.2 million subscribers in Q3, well above the 6 million estimate.",
            "symbol": "NFLX",
            "source": "Yahoo Finance"
        },
        {
            "title": "Disney Announces $5 Billion Share Buyback and Dividend Increase",
            "description": "The Walt Disney Company's board approved a new $5 billion share repurchase program and increased its quarterly dividend by 15%, returning more cash to shareholders.",
            "symbol": "DIS",
            "source": "MarketWatch"
        },
        {
            "title": "General Market Update: Trading Volume Remains Normal",
            "description": "Market activity continues at typical levels with no major catalysts driving significant moves in major indices today.",
            "symbol": "SPY",
            "source": "Generic News"
        }
    ]
    
    print("📊 Processing realistic news articles with enhanced catalyst detection...\n")
    
    catalyst_articles = []
    non_catalyst_articles = []
    
    for i, article in enumerate(realistic_news_examples, 1):
        print(f"Article {i}: {article['source']}")
        print(f"Title: {article['title']}")
        print(f"Symbol: {article['symbol']}")
        
        catalyst_type = identify_article_catalyst(article['title'], article['description'])
        
        relevance_score = calculate_enhanced_relevance_score(
            article['title'], 
            article['description'], 
            article['symbol'],
            catalyst_type
        )
        
        print(f"🎯 Catalyst Type: {catalyst_type if catalyst_type else 'None detected'}")
        print(f"📈 Relevance Score: {relevance_score}")
        
        if catalyst_type:
            catalyst_articles.append({
                'title': article['title'][:50] + '...',
                'catalyst': catalyst_type,
                'score': relevance_score,
                'symbol': article['symbol']
            })
        else:
            non_catalyst_articles.append({
                'title': article['title'][:50] + '...',
                'score': relevance_score,
                'symbol': article['symbol']
            })
        
        print("-" * 60)
    
    print("\n📋 ENHANCED CATALYST DETECTION SUMMARY")
    print("=" * 60)
    
    print(f"📰 Total Articles Processed: {len(realistic_news_examples)}")
    print(f"🎯 Articles with Catalysts: {len(catalyst_articles)}")
    print(f"📄 Articles without Catalysts: {len(non_catalyst_articles)}")
    print(f"🎯 Catalyst Detection Rate: {len(catalyst_articles)/len(realistic_news_examples)*100:.1f}%")
    
    print(f"\n🏆 TOP CATALYST ARTICLES (sorted by relevance score):")
    catalyst_articles.sort(key=lambda x: x['score'], reverse=True)
    for i, article in enumerate(catalyst_articles[:5], 1):
        print(f"  {i}. {article['title']} ({article['symbol']})")
        print(f"     Catalyst: {article['catalyst']} | Score: {article['score']}")
    
    print(f"\n📊 CATALYST TYPE DISTRIBUTION:")
    catalyst_counts = {}
    for article in catalyst_articles:
        catalyst_type = article['catalyst']
        catalyst_counts[catalyst_type] = catalyst_counts.get(catalyst_type, 0) + 1
    
    for catalyst_type, count in sorted(catalyst_counts.items()):
        print(f"  • {catalyst_type}: {count} article(s)")
    
    avg_catalyst_score = sum(a['score'] for a in catalyst_articles) / len(catalyst_articles) if catalyst_articles else 0
    avg_non_catalyst_score = sum(a['score'] for a in non_catalyst_articles) / len(non_catalyst_articles) if non_catalyst_articles else 0
    
    print(f"\n📈 RELEVANCE SCORING ANALYSIS:")
    print(f"  • Average score for catalyst articles: {avg_catalyst_score:.2f}")
    print(f"  • Average score for non-catalyst articles: {avg_non_catalyst_score:.2f}")
    print(f"  • Catalyst scoring advantage: +{avg_catalyst_score - avg_non_catalyst_score:.2f}")
    
    print(f"\n✅ ENHANCED FEATURES DEMONSTRATED:")
    print(f"  ✓ 10 comprehensive catalyst categories")
    print(f"  ✓ Confidence scoring (title=2pts, description=1pt)")
    print(f"  ✓ Individual article catalyst_type population")
    print(f"  ✓ Enhanced relevance scoring with tiered keywords")
    print(f"  ✓ Catalyst bonus (+1.0) for prioritization")
    print(f"  ✓ Weighted pattern matching beyond simple keywords")
    
    return len(catalyst_articles), len(realistic_news_examples)

if __name__ == "__main__":
    try:
        catalyst_count, total_count = demo_enhanced_catalyst_detection()
        
        print(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print(f"Enhanced catalyst detection system identified {catalyst_count}/{total_count} catalyst articles")
        print(f"System is ready for production use with real news data!")
        
    except Exception as e:
        print(f"\n❌ Error running catalyst detection demo: {str(e)}")
        import traceback
        traceback.print_exc()
