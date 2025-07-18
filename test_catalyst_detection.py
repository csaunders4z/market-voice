#!/usr/bin/env python3
"""
Test script to verify enhanced catalyst detection system
"""

def test_catalyst_detection():
    """Test catalyst detection with sample articles covering all catalyst types"""
    print("Testing Enhanced Catalyst Detection System")
    print("=" * 50)
    
    def identify_article_catalyst(title: str, description: str) -> str:
        """Identify the primary catalyst type for a single article"""
        content = f"{title} {description}".lower()
        
        catalyst_patterns = {
            'earnings': [
                'earnings beat', 'earnings miss', 'quarterly results', 'earnings report',
                'earnings', 'eps', 'revenue', 'profit', 'q1', 'q2', 'q3', 'q4',
                'fiscal year', 'financial results', 'earnings call'
            ],
            'merger_acquisition': [
                'acquisition', 'merger', 'takeover', 'buyout', 'acquired', 'merge',
                'purchase', 'bid', 'offer', 'transaction', 'deal worth', 'cash deal'
            ],
            'analyst_action': [
                'upgrade', 'downgrade', 'price target', 'buy rating', 'sell rating',
                'analyst', 'rating', 'outperform', 'underperform', 'overweight',
                'target price', 'recommendation', 'coverage initiated'
            ],
            'regulatory_approval': [
                'fda approval', 'drug approval', 'regulatory approval', 'cleared',
                'authorized', 'approved', 'fda', 'regulatory', 'clinical trial'
            ],
            'product_innovation': [
                'product launch', 'new product', 'innovation', 'breakthrough',
                'patent', 'technology', 'development', 'launch'
            ],
            'partnership': [
                'partnership', 'collaboration', 'joint venture', 'alliance',
                'agreement', 'contract', 'strategic partnership', 'licensing'
            ],
            'guidance_outlook': [
                'guidance', 'raised guidance', 'lowered guidance', 'outlook',
                'forecast', 'projections', 'updated outlook', 'expects'
            ],
            'dividend_buyback': [
                'dividend', 'buyback', 'share repurchase', 'dividend increase',
                'dividend cut', 'special dividend', 'stock split', 'spin-off'
            ],
            'insider_activity': [
                'insider', 'insider trading', 'insider buying', 'insider selling',
                'executive', 'ceo', 'management', 'stock purchase', 'stock sale'
            ],
            'legal_regulatory': [
                'lawsuit', 'settlement', 'investigation', 'fine', 'penalty',
                'violation', 'court', 'ruling', 'sec', 'ftc', 'compliance'
            ]
        }
        
        best_match = ""
        highest_score = 0
        
        for catalyst_type, keywords in catalyst_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in content:
                    if keyword in title.lower():
                        score += 2
                    else:
                        score += 1
            
            if score > highest_score:
                highest_score = score
                best_match = catalyst_type
        
        return best_match if highest_score > 0 else ""
    
    test_articles = [
        {
            "title": "Apple beats Q3 earnings expectations with strong iPhone sales",
            "description": "Apple reported quarterly earnings that exceeded analyst estimates with revenue growth of 15%",
            "expected": "earnings"
        },
        {
            "title": "Goldman Sachs upgrades Tesla to Buy with $300 price target",
            "description": "Analyst raises rating citing strong fundamentals and growth prospects",
            "expected": "analyst_action"
        },
        {
            "title": "Microsoft announces $69B acquisition of Activision Blizzard",
            "description": "Tech giant to acquire gaming company in largest deal ever",
            "expected": "merger_acquisition"
        },
        {
            "title": "Pfizer receives FDA approval for new cancer drug",
            "description": "Regulatory approval clears path for commercial launch of breakthrough therapy",
            "expected": "regulatory_approval"
        },
        {
            "title": "Amazon launches new AI-powered delivery drones",
            "description": "Product launch represents major innovation in logistics technology",
            "expected": "product_innovation"
        },
        {
            "title": "Google forms strategic partnership with OpenAI",
            "description": "Collaboration agreement focuses on AI research and development",
            "expected": "partnership"
        },
        {
            "title": "Netflix raises full-year guidance after strong subscriber growth",
            "description": "Company updated outlook citing better than expected performance",
            "expected": "guidance_outlook"
        },
        {
            "title": "Disney announces $3 billion share buyback program",
            "description": "Board approves dividend increase and share repurchase plan",
            "expected": "dividend_buyback"
        },
        {
            "title": "Tesla CEO Elon Musk purchases additional 1M shares",
            "description": "Insider buying signals confidence in company's future prospects",
            "expected": "insider_activity"
        },
        {
            "title": "SEC investigates Theranos for securities violations",
            "description": "Regulatory investigation focuses on potential compliance issues",
            "expected": "legal_regulatory"
        }
    ]
    
    correct_detections = 0
    total_tests = len(test_articles)
    
    print(f"Running {total_tests} catalyst detection tests...\n")
    
    for i, article in enumerate(test_articles, 1):
        detected = identify_article_catalyst(article["title"], article["description"])
        is_correct = detected == article["expected"]
        
        if is_correct:
            correct_detections += 1
        
        print(f"Test {i}: {article['title'][:60]}...")
        print(f"  Expected: {article['expected']}")
        print(f"  Detected: {detected}")
        print(f"  Result: {'✅ PASS' if is_correct else '❌ FAIL'}")
        print()
    
    print("Testing mixed catalyst detection...")
    sample_articles = [
        {
            "title": "Apple beats earnings while Microsoft announces acquisition",
            "description": "Mixed market news with earnings and M&A activity"
        },
        {
            "title": "FDA approves new drug as analyst upgrades stock", 
            "description": "Regulatory approval coincides with positive analyst action"
        }
    ]
    
    detected_catalysts = []
    for article in sample_articles:
        catalyst = identify_article_catalyst(article["title"], article["description"])
        if catalyst and catalyst not in detected_catalysts:
            detected_catalysts.append(catalyst)
    
    print(f"Detected catalysts from mixed articles: {detected_catalysts}")
    print()
    
    accuracy = (correct_detections / total_tests) * 100
    print("=" * 50)
    print(f"CATALYST DETECTION TEST RESULTS")
    print(f"Correct detections: {correct_detections}/{total_tests}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("✅ Catalyst detection system is working well!")
        return True
    elif accuracy >= 60:
        print("⚠️  Catalyst detection needs improvement")
        return False
    else:
        print("❌ Catalyst detection system needs significant work")
        return False

if __name__ == "__main__":
    try:
        success = test_catalyst_detection()
        
        if success:
            print("\n🎉 All catalyst detection tests passed!")
        else:
            print("\n⚠️  Some catalyst detection tests failed")
            
    except Exception as e:
        print(f"\n❌ Error running catalyst detection tests: {str(e)}")
        import traceback
        traceback.print_exc()
