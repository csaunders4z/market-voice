"""
Script generator for Market Voices
Uses OpenAI to create professional financial news scripts
"""
import openai
from typing import Dict, List, Optional
from datetime import datetime
import json
import re
from loguru import logger
import os

from ..config.settings import get_settings
from ..content_validation.quality_controls import quality_controller
from .host_manager import host_manager


class ScriptGenerator:
    """Generates professional financial news scripts using OpenAI"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_model
        self.max_tokens = self.settings.max_tokens
        self.temperature = self.settings.temperature
        
    def create_script_prompt(self, market_data: Dict, lead_host: str) -> str:
        """Create the prompt for script generation with enhanced analysis"""
        
        # Get host information
        lead_host_info = host_manager.get_host_info(lead_host)
        supporting_host = 'marcus' if lead_host == 'suzanne' else 'suzanne'
        supporting_host_info = host_manager.get_host_info(supporting_host)
        
        # Format market data with enhanced information
        winners = market_data.get('winners', [])
        losers = market_data.get('losers', [])
        summary = market_data.get('market_summary', {})
        
        # Get news data for integration (keeping for backward compatibility)
        news_data = market_data.get('news_data', {})
        market_news = news_data.get('market_analysis', '')
        company_news = news_data.get('company_analysis', {})
        
        # Format winners and losers with enhanced data and news integration
        winners_text = ""
        for i, stock in enumerate(winners, 1):
            symbol = stock.get('symbol', '')
            company_name = stock.get('company_name', symbol)
            current_price = stock.get('current_price', 0)
            percent_change = stock.get('percent_change', 0)
            volume_ratio = stock.get('volume_ratio', 1.0)
            
            # Enhanced data
            earnings_data = stock.get('earnings_data')
            analyst_data = stock.get('analyst_data')
            insider_data = stock.get('insider_data')
            price_target = stock.get('price_target')
            
            # ENHANCED: Get news articles directly from stock data
            news_articles = stock.get('news_articles', [])
            news_analysis = stock.get('news_analysis', '')
            news_sources = stock.get('news_sources', [])
            
            # Format news information for the prompt
            news_info = ""
            if news_articles:
                news_info += f"   Recent News Articles:\n"
                for j, article in enumerate(news_articles[:3], 1):  # Top 3 articles
                    title = article.get('title', '')
                    source = article.get('source', 'Unknown')
                    published_at = article.get('published_at', '')
                    news_info += f"   {j}. {title} ({source}) - {published_at}\n"
            
            if news_analysis:
                news_info += f"   News Analysis: {news_analysis[:300]}...\n"
            
            winners_text += f"\n{i}. {symbol} ({company_name}): ${current_price} (+{percent_change:.2f}%)\n"
            winners_text += f"   Volume: {volume_ratio:.1f}x average\n"
            
            if earnings_data:
                winners_text += f"   Next Earnings: {earnings_data.get('date', 'N/A')}\n"
            
            if analyst_data:
                consensus = analyst_data.get('consensus', 'hold')
                winners_text += f"   Analyst Consensus: {consensus.upper()}\n"
            
            if price_target:
                winners_text += f"   Price Target: ${price_target:.2f}\n"
            
            if insider_data and insider_data.get('activity_level') == 'high':
                net_activity = insider_data.get('net_activity', 'neutral')
                winners_text += f"   Insider Activity: {net_activity.upper()}\n"
            
            if news_info:
                winners_text += news_info
        
        losers_text = ""
        for i, stock in enumerate(losers, 1):
            symbol = stock.get('symbol', '')
            company_name = stock.get('company_name', symbol)
            current_price = stock.get('current_price', 0)
            percent_change = stock.get('percent_change', 0)
            volume_ratio = stock.get('volume_ratio', 1.0)
            
            # Enhanced data
            earnings_data = stock.get('earnings_data')
            analyst_data = stock.get('analyst_data')
            insider_data = stock.get('insider_data')
            price_target = stock.get('price_target')
            
            # ENHANCED: Get news articles directly from stock data
            news_articles = stock.get('news_articles', [])
            news_analysis = stock.get('news_analysis', '')
            news_sources = stock.get('news_sources', [])
            
            # Format news information for the prompt
            news_info = ""
            if news_articles:
                news_info += f"   Recent News Articles:\n"
                for j, article in enumerate(news_articles[:3], 1):  # Top 3 articles
                    title = article.get('title', '')
                    source = article.get('source', 'Unknown')
                    published_at = article.get('published_at', '')
                    news_info += f"   {j}. {title} ({source}) - {published_at}\n"
            
            if news_analysis:
                news_info += f"   News Analysis: {news_analysis[:300]}...\n"
            
            losers_text += f"\n{i}. {symbol} ({company_name}): ${current_price} ({percent_change:.2f}%)\n"
            losers_text += f"   Volume: {volume_ratio:.1f}x average\n"
            
            if earnings_data:
                losers_text += f"   Next Earnings: {earnings_data.get('date', 'N/A')}\n"
            
            if analyst_data:
                consensus = analyst_data.get('consensus', 'hold')
                losers_text += f"   Analyst Consensus: {consensus.upper()}\n"
            
            if price_target:
                losers_text += f"   Price Target: ${price_target:.2f}\n"
            
            if insider_data and insider_data.get('activity_level') == 'high':
                net_activity = insider_data.get('net_activity', 'neutral')
                losers_text += f"   Insider Activity: {net_activity.upper()}\n"
            
            if news_info:
                losers_text += news_info
        
        # Get economic calendar data
        economic_calendar = market_data.get('market_summary', {}).get('economic_calendar', {})
        economic_context = ""
        
        if economic_calendar:
            fed_meetings = economic_calendar.get('fed_meetings', [])
            immediate_events = economic_calendar.get('immediate_events', [])
            
            if fed_meetings:
                next_meeting = fed_meetings[0] if fed_meetings else None
                if next_meeting:
                    days_until = next_meeting.get('days_until', 0)
                    if days_until <= 7:
                        economic_context += f"Fed meeting in {days_until} days. "
                    elif days_until <= 30:
                        economic_context += f"Fed meeting in {days_until} days. "
            
            if immediate_events:
                economic_context += f"Key events this week: {len(immediate_events)} market-moving events. "
        
        # Get enhanced news analysis (paid sources)
        enhanced_news = market_data.get('market_summary', {}).get('enhanced_news', {})
        news_analysis = ""
        if enhanced_news and enhanced_news.get('collection_success'):
            market_analysis = enhanced_news.get('market_analysis', {})
            if market_analysis.get('analysis_text'):
                news_analysis = f"\nMARKET ANALYSIS FROM NEWS SOURCES:\n{market_analysis.get('analysis_text', '')[:1500]}...\n"
            company_analysis = enhanced_news.get('company_analysis', {})
            if company_analysis:
                news_analysis += f"\nCOMPANY-SPECIFIC ANALYSIS AVAILABLE FOR: {list(company_analysis.keys())}\n"
        
        # Get free news analysis (free sources)
        free_news = market_data.get('market_summary', {}).get('free_news', {})
        free_news_text = ""
        if free_news and free_news.get('articles'):
            free_news_text = "\nFREE NEWS HEADLINES:\n"
            for article in free_news['articles'][:5]:
                free_news_text += f"- {article.get('title', '')} ({article.get('source', '')})\n"
        
        # Enhanced market summary
        market_summary = market_data.get('market_summary', {})
        
        # Get coverage statistics for both indices
        total_target_symbols = market_summary.get('total_target_symbols', 0)
        sp500_coverage = market_summary.get('sp500_coverage', 0)
        nasdaq100_coverage = market_summary.get('nasdaq100_coverage', 0)
        coverage_percentage = market_summary.get('coverage_percentage', 0)
        
        # Determine market coverage description
        if sp500_coverage > 0 and nasdaq100_coverage > 0:
            market_coverage_desc = f"Analyzing {sp500_coverage} S&P 500 and {nasdaq100_coverage} NASDAQ-100 stocks ({coverage_percentage:.1f}% coverage)"
        elif sp500_coverage > 0:
            market_coverage_desc = f"Analyzing {sp500_coverage} S&P 500 stocks"
        elif nasdaq100_coverage > 0:
            market_coverage_desc = f"Analyzing {nasdaq100_coverage} NASDAQ-100 stocks"
        else:
            market_coverage_desc = market_summary.get('market_coverage', 'Analyzing major US stocks')
        
        enhanced_summary = f"""
MARKET OVERVIEW:
- Market Analysis: {market_coverage_desc}
- Stocks analyzed: {market_summary.get('total_stocks_analyzed', 0)} out of {total_target_symbols} total target stocks
- S&P 500 coverage: {sp500_coverage} stocks
- NASDAQ-100 coverage: {nasdaq100_coverage} stocks
- Advancing: {market_summary.get('advancing_stocks', 0)}, Declining: {market_summary.get('declining_stocks', 0)}
- Average change: {market_summary.get('average_change', 0):.2f}%
- Market sentiment: {market_summary.get('market_sentiment', 'Mixed')}
- Data source: {market_summary.get('data_source', 'Unknown')}
- Economic context: {economic_context}
{news_analysis}
{free_news_text}
"""
        
        prompt = f"""
You are writing a professional financial news script for "Market Voices," a daily analysis show covering major US stocks including NASDAQ-100 and S&P 500 companies. Create a comprehensive, engaging script that explains market movements with specific details and analysis.

HOSTS:
- {lead_host_info['name']} ({lead_host_info['age']}): {lead_host_info['personality']}
- {supporting_host_info['name']} ({supporting_host_info['age']}): {supporting_host_info['personality']}

TODAY'S MARKET DATA:
{enhanced_summary}

TOP 5 WINNERS (with detailed analysis):
{winners_text}

TOP 5 LOSERS (with detailed analysis):
{losers_text}

CRITICAL REQUIREMENTS - READ CAREFULLY:
1. ABSOLUTE MINIMUM 1440 WORDS TOTAL - This is non-negotiable
2. You MUST write EXACTLY 10 stock segments (5 winners + 5 losers)
3. Each stock segment MUST be 100-120 words minimum
4. Total stock segments must be 1000-1200 words
5. Intro: 200 words, Market Overview: 150 words, Market Sentiment: 100 words, Outro: 150 words
6. Speaking time: 45-55% split between hosts
7. Use varied language - avoid repetitive phrases like "we will", "let's look at", etc.
8. Include specific data points, percentages, and technical indicators
9. Reference actual news events and analyst actions
10. Professional financial news tone

HOST INTERACTION GUIDELINES:
- DO NOT have hosts identify their jobs or backgrounds during the broadcast
- Create natural, conversational banter between hosts in the intro and transitions
- Use the hosts' personalities to create engaging dialogue
- {lead_host_info['name']}: {lead_host_info['personality']} - {lead_host_info['tone']}
- {supporting_host_info['name']}: {supporting_host_info['personality']} - {supporting_host_info['tone']}
- Include light banter about market mood, interesting moves, or observations
- Make transitions feel natural and conversational, not robotic

NEWS INTEGRATION REQUIREMENTS:
- ALWAYS reference specific news sources and events to explain stock movements
- Use the provided news data to explain WHY stocks moved, not just WHAT happened
- Reference specific articles, analyst reports, earnings news, or market events
- Connect stock movements to broader market themes and sector trends
- Use news data to provide context for volume patterns and price action
- Each stock segment MUST explain the catalyst or reason behind the price movement
- Cite specific news sources (Reuters, Bloomberg, etc.) when available
- If no specific news is available, explain the technical or market context

LANGUAGE REQUIREMENTS:
- AVOID repetitive phrases like "we will", "let's look at", "in this segment", "moving on", "next up"
- Use varied transitions: "meanwhile", "conversely", "additionally", "furthermore", "on the flip side"
- Vary sentence structure and length for natural flow
- Use specific financial terminology appropriately
- Create engaging, dynamic content that flows naturally

STOCK SEGMENT REQUIREMENTS (100-120 words each):
For each stock, you MUST include:
- Natural host introduction and stock identification
- Price movement and volume analysis with specific percentages
- SPECIFIC news catalysts (reference actual news sources provided)
- Technical analysis (RSI, MACD, support/resistance if available)
- Market context and sector impact
- Forward-looking analysis and what to watch for

MOST IMPORTANT: EXPLAIN WHY EACH STOCK MOVED THE WAY IT DID
For each stock segment, you MUST explain:
- What specific news, events, or catalysts drove the price movement (use provided news data)
- How market sentiment and sector trends influenced the stock
- What analysts and experts are saying about the move (reference specific sources)
- What the trading volume tells us about investor behavior
- How this fits into broader market themes (AI, rate cuts, earnings, etc.)
- What to watch for in the coming days/weeks

If you lack specific information about why a stock moved, use available data to make educated analysis:
- Recent earnings reports and guidance
- Sector rotation and market themes
- Technical indicators and price action
- Analyst ratings and price target changes
- Insider trading activity
- Upcoming catalysts (earnings, product launches, etc.)
- Macroeconomic factors (Fed policy, economic data, etc.)

CRITICAL: DO NOT WRITE OUTLINES OR DESCRIPTIONS. WRITE THE ACTUAL ANALYSIS CONTENT.
CRITICAL: ENSURE EACH STOCK SEGMENT IS 100-120 WORDS MINIMUM.
CRITICAL: ENSURE TOTAL SCRIPT IS 1440+ WORDS.

WORD COUNT BREAKDOWN (MINIMUM 1440 WORDS TOTAL):
- Intro: 200 words (natural host banter and market mood discussion)
- Market Overview: 150 words (brief market summary and key themes)
- Top 5 Winners: 5 segments, 100-120 words each (500-600 words total)
- Top 5 Losers: 5 segments, 100-120 words each (500-600 words total)
- Market Sentiment: 100 words (overall market sentiment analysis)
- Outro: 150 words (closing remarks and preview of next session)

CONTENT STRUCTURE (JSON):
{{
    "intro": "Natural host banter and market mood discussion (200 words)",
    "market_overview": "Market and economic context (150 words)",
    "winner_segments": [
        {{"host": "{lead_host}", "stock": "WINNER1", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}},
        {{"host": "{supporting_host}", "stock": "WINNER2", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}},
        {{"host": "{lead_host}", "stock": "WINNER3", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}},
        {{"host": "{supporting_host}", "stock": "WINNER4", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}},
        {{"host": "{lead_host}", "stock": "WINNER5", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}}
    ],
    "loser_segments": [
        {{"host": "{supporting_host}", "stock": "LOSER1", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}},
        {{"host": "{lead_host}", "stock": "LOSER2", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}},
        {{"host": "{supporting_host}", "stock": "LOSER3", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}},
        {{"host": "{lead_host}", "stock": "LOSER4", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}},
        {{"host": "{supporting_host}", "stock": "LOSER5", "text": "Detailed analysis explaining WHY the stock moved (100-120 words)"}}
    ],
    "market_sentiment": "Overall market sentiment analysis (100 words)",
    "outro": "Closing remarks and preview of next session (150 words)"
}}

EXAMPLES OF GOOD CONTENT WITH "WHY" ANALYSIS:

Example Intro with Natural Banter (200 words):
"{lead_host_info['name']}: Hey everyone, welcome to Market Voices! What a day we've had on the NASDAQ-100. {supporting_host_info['name']}, I've got to say, I'm seeing some really interesting patterns here.

{supporting_host_info['name']}: Absolutely! You know what caught my eye? The way tech stocks are behaving today. We've got this mix of AI plays surging while some of the more traditional names are taking a breather. It's like the market is having a conversation about what's next.

{lead_host_info['name']}: Exactly! And speaking of conversations, did you see the volume on some of these moves? It's not just retail traders - we're seeing institutional money flowing in specific directions. That tells me there's real conviction behind these moves.

{supporting_host_info['name']}: No doubt about it. And with the Fed meeting coming up next week, everyone's trying to position themselves. But let's dive into the specifics - we've got some real winners and losers to talk about today."

Example Winner Segment with News Integration (120+ words):
"Alphabet Inc. (GOOGL) surged 2.88% today, outperforming the broader NASDAQ-100. The rally was driven by multiple catalysts: First, Reuters reported that Alphabet announced a $10 billion investment in AI infrastructure, positioning the company at the forefront of the ongoing AI arms race. This comes as investors are increasingly focused on AI leadership, with Microsoft and other tech giants also making significant AI investments. Second, the company's recent earnings report showed a 28% year-over-year jump in Google Cloud revenue, exceeding analyst expectations. Third, analysts from Benzinga and Seeking Alpha have raised their price targets, citing strong demand for AI-powered services and the company's dominant position in search advertising. Volume was 2.5 times the average, suggesting institutional investors are building positions ahead of next week's earnings. The move also reflects broader market rotation into growth stocks as the Federal Reserve signals potential rate cuts. Looking ahead, the upcoming earnings call will be a key catalyst, with analysts expecting continued momentum in cloud and AI segments."

Example Loser Segment with News Integration (120+ words):
"Tesla Inc. (TSLA) declined 0.66% today, underperforming its tech peers. The drop was primarily driven by regulatory concerns: Bloomberg reported that the National Highway Traffic Safety Administration is expanding its investigation into Tesla's Autopilot system, raising concerns about potential recalls or regulatory restrictions that could impact future sales. This regulatory scrutiny comes at a critical time as Tesla prepares to launch its Cybertruck and faces increasing competition in the EV space. Despite the setback, analysts remain divided: some, like those at CNBC, see the dip as a buying opportunity given Tesla's strong fundamentals and upcoming product launches, while others warn of increased regulatory headwinds that could slow growth. Trading volume was 1.8 times the average, indicating heightened investor anxiety about regulatory risks. The company's next earnings report, scheduled for later this month, will be closely watched for updates on regulatory issues and delivery numbers. Insider activity has been neutral, but any significant buying or selling by executives could further impact sentiment."

Example Natural Transition:
"{lead_host_info['name']}: That's a great point about the AI sector momentum. Meanwhile, over in the financial space, we're seeing some interesting developments that are worth discussing.

{supporting_host_info['name']}: Absolutely! The banking sector has been showing some real resilience lately, and today's moves suggest investors are positioning themselves ahead of the Fed meeting next week."

IMPORTANT: Return ONLY valid JSON. No additional text before or after the JSON object.
"""
        
        return prompt
    
    def generate_script(self, market_data: Dict) -> Dict:
        """Generate the complete script using OpenAI"""
        logger.info("Starting script generation")
        
        try:
            # Check if we have sufficient data for meaningful script generation
            winners = market_data.get('winners', [])
            losers = market_data.get('losers', [])
            
            if len(winners) < 3 or len(losers) < 1:
                logger.warning(f"Insufficient data for script generation: {len(winners)} winners, {len(losers)} losers")
                return {
                    'generation_success': False,
                    'error': f'Insufficient market data for script generation. Need at least 3 winners and 1 loser. Got {len(winners)} winners and {len(losers)} losers.',
                    'market_date': datetime.now().isoformat(),
                    'lead_host': 'unknown',
                    'estimated_runtime_minutes': 0
                }
            
            # Check if we're in test mode
            if os.getenv("TEST_MODE") == "1":
                logger.info("Running in test mode - generating mock script")
                return self._generate_mock_script(market_data)
            
            # Determine lead host for today
            lead_host = host_manager.get_lead_host_for_date()
            logger.info(f"Lead host for today: {lead_host}")
            
            # Create the prompt
            prompt = self.create_script_prompt(market_data, lead_host)
            
            # Generate script with OpenAI (v1.x API)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional financial news script writer with expertise in market analysis and engaging storytelling. You must return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            script_text = response.choices[0].message.content
            
            # Check if we got a valid response
            if not script_text:
                logger.error("OpenAI returned empty response")
                return {
                    "error": "OpenAI returned empty response",
                    "generation_success": False
                }
            
            # Try to parse as JSON
            try:
                script_data = json.loads(script_text)
                logger.info("Successfully parsed script as JSON")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse as JSON: {str(e)}")
                logger.warning(f"Script text: {script_text[:500]}...")
                script_data = self._create_structured_script(script_text, lead_host)
            
            # Validate and enhance the script
            try:
                script_data = self._validate_and_enhance_script(script_data, market_data, lead_host)
            except Exception as e:
                logger.error(f"Error in validation and enhancement: {str(e)}")
                logger.error(f"Script data structure: {type(script_data)}")
                if isinstance(script_data, dict):
                    logger.error(f"Script keys: {list(script_data.keys())}")
                raise
            
            # Run quality validation
            quality_results = quality_controller.validate_script_quality(script_data)
            script_data['quality_validation'] = quality_results
            
            # Log quality score
            logger.info(f"Script quality score: {quality_results.get('overall_score', 0):.1f}%")
            
            # If quality score is low, attempt to improve
            if quality_results.get('overall_score', 0) < 70:
                logger.warning("Script quality below threshold, attempting improvements")
                script_data = self._improve_script_quality(script_data, market_data, lead_host)
            
            logger.info("Script generation completed successfully")
            script_data['generation_success'] = True
            script_data['lead_host'] = lead_host
            return script_data
            
        except Exception as e:
            logger.error(f"Error generating script: {str(e)}")
            return {
                "error": str(e),
                "generation_success": False
            }
    
    def _generate_mock_script(self, market_data: Dict) -> Dict:
        """Generate a mock script for test mode"""
        lead_host = host_manager.get_lead_host_for_date()
        lead_host_info = host_manager.get_host_info(lead_host)
        supporting_host = 'marcus' if lead_host == 'suzanne' else 'suzanne'
        supporting_host_info = host_manager.get_host_info(supporting_host)
        
        # Create a realistic mock script with natural banter
        mock_script = {
            "intro": f"{lead_host_info['name']}: Hey everyone, welcome to Market Voices! What a day we've had across the major US markets. {supporting_host_info['name']}, I've got to say, I'm seeing some really interesting patterns here.\n\n{supporting_host_info['name']}: Absolutely! You know what caught my eye? The way tech stocks are behaving today. We've got this mix of AI plays surging while some of the more traditional names are taking a breather. It's like the market is having a conversation about what's next.\n\n{lead_host_info['name']}: Exactly! And speaking of conversations, did you see the volume on some of these moves? It's not just retail traders - we're seeing institutional money flowing in specific directions. That tells me there's real conviction behind these moves.\n\n{supporting_host_info['name']}: No doubt about it. And with the Fed meeting coming up next week, everyone's trying to position themselves. But let's dive into the specifics - we've got some real winners and losers to talk about today.",
            "segments": [
                {
                    "host": lead_host,
                    "text": f"Today was an interesting session across the major US indices. We saw {market_data.get('market_summary', {}).get('advancing_stocks', 0)} stocks advance and {market_data.get('market_summary', {}).get('declining_stocks', 0)} decline, with an average change of {market_data.get('market_summary', {}).get('average_change', 0):.2f}%. This suggests a mixed but generally positive day for major US stocks.",
                    "topic": "Market Overview"
                },
                {
                    "host": supporting_host,
                    "text": "Looking at the top performers, we had some impressive moves. Apple led the charge with a solid gain, followed by Microsoft and Google. These moves were driven by strong earnings expectations and positive analyst sentiment.",
                    "topic": "Top Performers Analysis"
                },
                {
                    "host": lead_host,
                    "text": "On the downside, we saw some pressure on Tesla and Meta. These moves appear to be profit-taking after recent strong performance, rather than fundamental concerns about the companies.",
                    "topic": "Decliners Analysis"
                },
                {
                    "host": supporting_host,
                    "text": "The market is showing resilience despite some volatility. Volume was healthy, and institutional buying patterns suggest continued confidence in the major US stocks' long-term prospects.",
                    "topic": "Market Sentiment"
                }
            ],
            "outro": f"{lead_host_info['name']}: That wraps up today's market analysis! Don't forget to subscribe for daily insights, and I'll see you tomorrow for more market action. This is {lead_host_info['name']}, signing off!",
            "estimated_runtime_minutes": host_manager.get_target_runtime(),
            "speaking_time_balance": {
                "marcus_percentage": 50,
                "suzanne_percentage": 50
            },
            "generation_success": True,
            "lead_host": lead_host,
            "market_date": market_data.get('market_summary', {}).get('market_date', datetime.now().isoformat()),
            "generation_timestamp": datetime.now().isoformat()
        }
        
        logger.info("Mock script generated successfully for test mode")
        return mock_script
    
    def _create_structured_script(self, script_text: str, lead_host: str) -> Dict:
        """Create structured script from plain text with better host balance"""
        lead_host_info = host_manager.get_host_info(lead_host)
        supporting_host = 'marcus' if lead_host == 'suzanne' else 'suzanne'
        supporting_host_info = host_manager.get_host_info(supporting_host)
        
        # Define segment topics
        segment_topics = [
            "Market Overview",
            "Top Performers Analysis", 
            "Decliners Analysis",
            "Market Sentiment & Outlook"
        ]
        
        # Split the text into paragraphs and create segments
        paragraphs = [p.strip() for p in script_text.split('\n\n') if p.strip()]
        
        segments = []
        current_host = lead_host
        
        # Create intro with natural banter
        intro = f"{lead_host_info['name']}: Hey everyone, welcome to Market Voices! What a day we've had across the major US markets. {supporting_host_info['name']}, I've got to say, I'm seeing some really interesting patterns here.\n\n{supporting_host_info['name']}: Absolutely! You know what caught my eye? The way tech stocks are behaving today. We've got this mix of AI plays surging while some of the more traditional names are taking a breather. It's like the market is having a conversation about what's next.\n\n{lead_host_info['name']}: Exactly! And speaking of conversations, did you see the volume on some of these moves? It's not just retail traders - we're seeing institutional money flowing in specific directions. That tells me there's real conviction behind these moves.\n\n{supporting_host_info['name']}: No doubt about it. And with the Fed meeting coming up next week, everyone's trying to position themselves. But let's dive into the specifics - we've got some real winners and losers to talk about today."
        
        # Create segments with alternating hosts
        for i, (paragraph, topic) in enumerate(zip(paragraphs[:4], segment_topics)):
            segments.append({
                "host": current_host,
                "text": paragraph,
                "topic": topic
            })
            # Alternate hosts
            current_host = supporting_host if current_host == lead_host else lead_host
        
        # If we have more paragraphs, add them as additional segments
        for i, paragraph in enumerate(paragraphs[4:], 4):
            segments.append({
                "host": current_host,
                "text": paragraph,
                "topic": f"Additional Analysis {i-3}"
            })
            current_host = supporting_host if current_host == lead_host else lead_host
        
        # Create outro with natural closing
        outro = f"{lead_host_info['name']}: That wraps up today's market analysis! Don't forget to subscribe for daily insights, and I'll see you tomorrow for more market action. This is {lead_host_info['name']}, signing off!"
        
        # Calculate speaking time balance
        marcus_segments = sum(1 for seg in segments if seg['host'] == 'marcus')
        suzanne_segments = sum(1 for seg in segments if seg['host'] == 'suzanne')
        total_segments = len(segments)
        
        marcus_percentage = (marcus_segments / total_segments) * 100 if total_segments > 0 else 50
        suzanne_percentage = (suzanne_segments / total_segments) * 100 if total_segments > 0 else 50
        
        return {
            "intro": intro,
            "segments": segments,
            "outro": outro,
            "estimated_runtime_minutes": host_manager.get_target_runtime(),
            "speaking_time_balance": {
                "marcus_percentage": marcus_percentage,
                "suzanne_percentage": suzanne_percentage
            }
        }
    
    def _validate_and_enhance_script(self, script_data: Dict, market_data: Dict, lead_host: str) -> Dict:
        """Validate and enhance the generated script"""
        
        # Ensure required fields exist
        if 'segments' not in script_data:
            script_data['segments'] = []
        
        if 'intro' not in script_data:
            script_data['intro'] = host_manager.get_intro_template(lead_host)
        
        if 'outro' not in script_data:
            script_data['outro'] = host_manager.get_outro_template(lead_host)
        
        # Validate speaking time balance
        if not host_manager.validate_speaking_time_balance(script_data['segments']):
            logger.warning("Speaking time balance validation failed")
        
        # Ensure minimum segment count
        if len(script_data.get('segments', [])) < 4:
            logger.warning("Script has fewer than 4 segments, adding more")
            script_data = self._add_missing_segments(script_data, market_data, lead_host)
        
        # Calculate and validate word counts
        total_words = 0
        for segment in script_data.get('segments', []):
            word_count = len(segment.get('text', '').split())
            segment['word_count'] = word_count
            total_words += word_count
        
        # Add quality metrics
        script_data['quality_metrics'] = {
            'total_words': total_words,
            'segments_count': len(script_data.get('segments', [])),
            'technical_indicators_used': self._count_technical_indicators(script_data),
            'news_sources_referenced': self._count_news_sources(script_data)
        }
        
        # Add metadata
        script_data['generation_timestamp'] = datetime.now().isoformat()
        script_data['lead_host'] = lead_host
        script_data['market_date'] = market_data.get('market_summary', {}).get('market_date', datetime.now().isoformat())
        script_data['generation_success'] = True
        
        return script_data
    
    def _improve_script_quality(self, script_data: Dict, market_data: Dict, lead_host: str) -> Dict:
        """Attempt to improve script quality when initial score is low"""
        logger.info("Attempting to improve script quality")
        
        try:
            # Create improvement prompt
            improvement_prompt = self._create_improvement_prompt(script_data, market_data, lead_host)
            
            # Generate improved script (OpenAI v1.x API)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional script editor. Fix the identified issues and return only valid JSON."},
                    {"role": "user", "content": improvement_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3  # Lower temperature for more focused improvements
            )
            
            improved_script_text = response.choices[0].message.content
            
            # Check if we got a valid response
            if not improved_script_text:
                logger.warning("OpenAI returned empty response for improvement")
                return script_data
            
            try:
                improved_script = json.loads(improved_script_text)
                logger.info("Successfully generated improved script")
                
                # Validate the improved script
                improved_script = self._validate_and_enhance_script(improved_script, market_data, lead_host)
                
                # Run quality validation again
                quality_results = quality_controller.validate_script_quality(improved_script)
                improved_script['quality_validation'] = quality_results
                
                logger.info(f"Improved script quality score: {quality_results.get('overall_score', 0):.1f}%")
                
                return improved_script
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse improved script as JSON, keeping original")
                return script_data
                
        except Exception as e:
            logger.error(f"Error improving script: {str(e)}")
            return script_data
    
    def _create_improvement_prompt(self, script_data: Dict, market_data: Dict, lead_host: str) -> str:
        """Create a prompt for improving the script based on quality issues"""
        
        quality_issues = script_data.get('quality_validation', {}).get('issues', [])
        quality_warnings = script_data.get('quality_validation', {}).get('warnings', [])
        
        issues_text = "\n".join([f"- {issue}" for issue in quality_issues])
        warnings_text = "\n".join([f"- {warning}" for warning in quality_warnings])
        
        return f"""
The following script has quality issues that need to be fixed:

CURRENT SCRIPT:
{json.dumps(script_data, indent=2)}

QUALITY ISSUES TO FIX:
{issues_text}

QUALITY WARNINGS TO ADDRESS:
{warnings_text}

Please fix these issues and return an improved version of the script in the same JSON format. Focus on:
1. Balancing speaking time between hosts (45-55% split)
2. Reducing repetitive phrases
3. Improving transitions between segments
4. Ensuring proper content length
5. Maintaining professional financial news tone

Return ONLY the improved JSON script.
"""
    
    def _add_missing_segments(self, script_data: Dict, market_data: Dict, lead_host: str) -> Dict:
        """Add missing segments to meet minimum requirements"""
        current_segments = script_data.get('segments', [])
        supporting_host = 'marcus' if lead_host == 'suzanne' else 'suzanne'
        
        # Define additional segment topics
        additional_topics = [
            "Sector Analysis",
            "Technical Indicators",
            "Market Sentiment",
            "Trading Volume Analysis"
        ]
        
        # Add segments until we have at least 6
        while len(current_segments) < 6:
            topic = additional_topics[len(current_segments) - len(script_data.get('segments', []))]
            host = supporting_host if len(current_segments) % 2 == 1 else lead_host
            
            new_segment = {
                "host": host,
                "text": f"This segment covers {topic.lower()}. Additional analysis will be provided here.",
                "topic": topic,
                "word_count": 150
            }
            current_segments.append(new_segment)
        
        script_data['segments'] = current_segments
        return script_data
    
    def _count_technical_indicators(self, script_data: Dict) -> int:
        """Count technical indicators mentioned in the script"""
        all_text = self._extract_all_text(script_data).lower()
        indicators = ['rsi', 'macd', 'volume', 'moving average', 'support', 'resistance', 'crossover']
        count = sum(all_text.count(indicator) for indicator in indicators)
        return count
    
    def _count_news_sources(self, script_data: Dict) -> int:
        """Count news sources referenced in the script"""
        all_text = self._extract_all_text(script_data).lower()
        sources = ['analyst', 'report', 'earnings', 'announcement', 'news', 'statement']
        count = sum(all_text.count(source) for source in sources)
        return count
    
    def _extract_all_text(self, script_data: Dict) -> str:
        """Extract all text content from script"""
        text_parts = []
        
        # Add intro
        if 'intro' in script_data:
            intro_text = script_data['intro']
            if isinstance(intro_text, str):
                text_parts.append(intro_text)
        
        # Add market overview
        if 'market_overview' in script_data:
            overview_text = script_data['market_overview']
            if isinstance(overview_text, str):
                text_parts.append(overview_text)
        
        # Add winner segments
        for segment in script_data.get('winner_segments', []):
            if isinstance(segment, dict):
                segment_text = segment.get('text', '')
                if isinstance(segment_text, str):
                    text_parts.append(segment_text)
            elif isinstance(segment, str):
                text_parts.append(segment)
        
        # Add loser segments
        for segment in script_data.get('loser_segments', []):
            if isinstance(segment, dict):
                segment_text = segment.get('text', '')
                if isinstance(segment_text, str):
                    text_parts.append(segment_text)
            elif isinstance(segment, str):
                text_parts.append(segment)
        
        # Add market sentiment
        if 'market_sentiment' in script_data:
            sentiment_text = script_data['market_sentiment']
            if isinstance(sentiment_text, str):
                text_parts.append(sentiment_text)
        
        # Add outro
        if 'outro' in script_data:
            outro_text = script_data['outro']
            if isinstance(outro_text, str):
                text_parts.append(outro_text)
        
        return ' '.join(text_parts)
    
    def format_script_for_output(self, script_data: Dict) -> str:
        """Format the script for human-readable output"""
        if not script_data.get('generation_success', False):
            return f"Script generation failed: {script_data.get('error', 'Unknown error')}"
        
        output = []
        output.append("=" * 80)
        output.append("MARKET VOICES - DAILY SCRIPT")
        output.append("=" * 80)
        output.append(f"Date: {script_data.get('market_date', 'Unknown')}")
        output.append(f"Lead Host: {script_data.get('lead_host', 'Unknown').title()}")
        output.append(f"Estimated Runtime: {script_data.get('estimated_runtime_minutes', 0)} minutes")
        output.append("")
        
        # Calculate total words from new structure
        total_words = 0
        
        # Add intro
        intro = script_data.get('intro', '')
        if intro:
            total_words += len(intro.split())
        
        # Add market overview
        market_overview = script_data.get('market_overview', '')
        if market_overview:
            total_words += len(market_overview.split())
        
        # Add winner segments
        winner_segments = script_data.get('winner_segments', [])
        for segment in winner_segments:
            text = segment.get('text', '')
            total_words += len(text.split())
        
        # Add loser segments
        loser_segments = script_data.get('loser_segments', [])
        for segment in loser_segments:
            text = segment.get('text', '')
            total_words += len(text.split())
        
        # Add market sentiment
        market_sentiment = script_data.get('market_sentiment', '')
        if market_sentiment:
            total_words += len(market_sentiment.split())
        
        # Add outro
        outro = script_data.get('outro', '')
        if outro:
            total_words += len(outro.split())
        
        # Quality metrics
        output.append("QUALITY METRICS:")
        output.append(f"Total Words: {total_words}")
        output.append(f"Segments: {len(winner_segments) + len(loser_segments)}")
        output.append(f"Technical Indicators: {self._count_technical_indicators(script_data)}")
        output.append(f"News Sources: {self._count_news_sources(script_data)}")
        output.append("")
        
        # Quality validation results
        quality_validation = script_data.get('quality_validation', {})
        if quality_validation:
            output.append("QUALITY VALIDATION:")
            output.append(f"Overall Score: {quality_validation.get('overall_score', 0):.1f}%")
            
            if quality_validation.get('issues'):
                output.append("Issues:")
                for issue in quality_validation['issues']:
                    output.append(f"  - {issue}")
            
            if quality_validation.get('warnings'):
                output.append("Warnings:")
                for warning in quality_validation['warnings']:
                    output.append(f"  - {warning}")
            
            if quality_validation.get('passed_checks'):
                output.append("Passed Checks:")
                for check in quality_validation['passed_checks']:
                    output.append(f"  ✓ {check}")
            output.append("")
        
        # Intro
        output.append("INTRO:")
        output.append(script_data.get('intro', ''))
        output.append("")
        
        # Market Overview
        if market_overview:
            output.append("MARKET OVERVIEW:")
            output.append(market_overview)
            output.append("")
        
        # Winner Segments
        if winner_segments:
            output.append("TOP 5 WINNERS:")
            for i, segment in enumerate(winner_segments, 1):
                output.append(f"Winner {i} - {segment.get('host', 'Unknown').title()}:")
                output.append(f"Stock: {segment.get('stock', 'Unknown')}")
                output.append(f"Words: {len(segment.get('text', '').split())}")
                output.append(segment.get('text', ''))
                output.append("")
        
        # Loser Segments
        if loser_segments:
            output.append("TOP 5 LOSERS:")
            for i, segment in enumerate(loser_segments, 1):
                output.append(f"Loser {i} - {segment.get('host', 'Unknown').title()}:")
                output.append(f"Stock: {segment.get('stock', 'Unknown')}")
                output.append(f"Words: {len(segment.get('text', '').split())}")
                output.append(segment.get('text', ''))
                output.append("")
        
        # Market Sentiment
        if market_sentiment:
            output.append("MARKET SENTIMENT:")
            output.append(market_sentiment)
            output.append("")
        
        # Outro
        output.append("OUTRO:")
        output.append(script_data.get('outro', ''))
        output.append("")
        
        # Speaking time balance
        balance = script_data.get('speaking_time_balance', {})
        output.append("SPEAKING TIME BALANCE:")
        output.append(f"Marcus: {balance.get('marcus_percentage', 0)}%")
        output.append(f"Suzanne: {balance.get('suzanne_percentage', 0)}%")
        output.append("")
        
        output.append("=" * 80)
        
        return "\n".join(output)


# Global instance
script_generator = ScriptGenerator() 