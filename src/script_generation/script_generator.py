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
        
        # Format winners and losers with enhanced data
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
        enhanced_summary = f"""
MARKET OVERVIEW:
- NASDAQ-100 Market Analysis: {market_summary.get('market_coverage', 'Analyzing representative NASDAQ-100 stocks')}
- Stocks analyzed: {market_summary.get('total_stocks_analyzed', 0)} out of {market_summary.get('total_nasdaq_100_stocks', 100)} NASDAQ-100 stocks
- Advancing: {market_summary.get('advancing_stocks', 0)}, Declining: {market_summary.get('declining_stocks', 0)}
- Average change: {market_summary.get('average_change', 0):.2f}%
- Market sentiment: {market_summary.get('market_sentiment', 'Mixed')}
- Data source: {market_summary.get('data_source', 'Unknown')}
- Economic context: {economic_context}
{news_analysis}
{free_news_text}
"""
        
        prompt = f"""
You are writing a script for "Market Voices," a daily NASDAQ-100 analysis show targeting educated viewers (college graduate/MBA level).

HOSTS:
- {lead_host_info['name']} ({lead_host_info['age']}): {lead_host_info['personality']}
- {supporting_host_info['name']} ({supporting_host_info['age']}): {supporting_host_info['personality']}

TODAY'S MARKET DATA:
{enhanced_summary}

TOP 5 WINNERS (with detailed analysis):
{winners_text}

TOP 5 LOSERS (with detailed analysis):
{losers_text}

CRITICAL REQUIREMENTS:
1. The script must be at least 1440 words in total. THIS IS A HARD REQUIREMENT.
2. There must be 10 separate segments: one for each of the top 5 winners and one for each of the top 5 losers. Each of these 10 segments must be at least 120 words. DO NOT MOVE TO THE NEXT SEGMENT UNTIL THE WORD COUNT IS MET.
3. At least 70% of the script (1000+ words) must be devoted to these 10 stock segments.
4. The intro, market overview, market sentiment, and outro should fill out the rest of the word count (each 100–200 words).
5. {lead_host_info['name']} leads and speaks first, but the supporting host MUST greet the audience and participate in the intro banter. The intro must always include both hosts greeting the audience and a short exchange about the day's market mood or a headline before diving in.
6. Speaking time must be 45-55% split between hosts (strict requirement).
7. Use professional financial news tone - avoid AI-generated language patterns.
8. VARY YOUR LANGUAGE - avoid repeating the same phrases and sentence structures.

MOST IMPORTANT: EXPLAIN WHY EACH STOCK MOVED THE WAY IT DID
For each stock segment, you MUST explain:
- What specific news, events, or catalysts drove the price movement
- How market sentiment and sector trends influenced the stock
- What analysts and experts are saying about the move
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

IMPORTANT: DO NOT WRITE OUTLINES OR DESCRIPTIONS OF WHAT YOU'LL COVER. WRITE THE ACTUAL ANALYSIS CONTENT.

WORD COUNT BREAKDOWN (MINIMUM 1440 WORDS TOTAL):
- Intro: 100-200 words
- Market Overview: 100-200 words
- Top 5 Winners: 5 segments, 120+ words each (600+ words total)
- Top 5 Losers: 5 segments, 120+ words each (600+ words total)
- Market Sentiment: 100-200 words
- Outro: 100-200 words

CONTENT STRUCTURE (JSON):
{{
    "intro": "Both hosts greet and chat (100-200 words)",
    "market_overview": "Market and economic context (100-200 words)",
    "winner_segments": [
        {{"host": "{lead_host}", "stock": "WINNER1", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}},
        {{"host": "{supporting_host}", "stock": "WINNER2", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}},
        {{"host": "{lead_host}", "stock": "WINNER3", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}},
        {{"host": "{supporting_host}", "stock": "WINNER4", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}},
        {{"host": "{lead_host}", "stock": "WINNER5", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}}
    ],
    "loser_segments": [
        {{"host": "{supporting_host}", "stock": "LOSER1", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}},
        {{"host": "{lead_host}", "stock": "LOSER2", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}},
        {{"host": "{supporting_host}", "stock": "LOSER3", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}},
        {{"host": "{lead_host}", "stock": "LOSER4", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}},
        {{"host": "{supporting_host}", "stock": "LOSER5", "text": "Detailed analysis explaining WHY the stock moved (120+ words)"}}
    ],
    "market_sentiment": "Market sentiment and institutional activity (100-200 words)",
    "outro": "Closing remarks (100-200 words)",
    "estimated_runtime_minutes": {host_manager.get_target_runtime()},
    "speaking_time_balance": {{"marcus_percentage": 50, "suzanne_percentage": 50}},
    "quality_metrics": {{"total_words": 1440, "segments_count": 14}}
}}

EXAMPLES OF GOOD CONTENT WITH "WHY" ANALYSIS:

Example Winner Segment (120+ words):
"Alphabet Inc. (GOOGL) surged 2.88% today, outperforming the broader NASDAQ-100. The rally was driven by multiple catalysts: First, Reuters reported that Alphabet announced a $10 billion investment in AI infrastructure, positioning the company at the forefront of the ongoing AI arms race. This comes as investors are increasingly focused on AI leadership, with Microsoft and other tech giants also making significant AI investments. Second, the company's recent earnings report showed a 28% year-over-year jump in Google Cloud revenue, exceeding analyst expectations. Third, analysts from Benzinga and Seeking Alpha have raised their price targets, citing strong demand for AI-powered services and the company's dominant position in search advertising. Volume was 2.5 times the average, suggesting institutional investors are building positions ahead of next week's earnings. The move also reflects broader market rotation into growth stocks as the Federal Reserve signals potential rate cuts. Looking ahead, the upcoming earnings call will be a key catalyst, with analysts expecting continued momentum in cloud and AI segments."

Example Loser Segment (120+ words):
"Tesla Inc. (TSLA) declined 0.66% today, underperforming its tech peers. The drop was primarily driven by regulatory concerns: Bloomberg reported that the National Highway Traffic Safety Administration is expanding its investigation into Tesla's Autopilot system, raising concerns about potential recalls or regulatory restrictions that could impact future sales. This regulatory scrutiny comes at a critical time as Tesla prepares to launch its Cybertruck and faces increasing competition in the EV space. Despite the setback, analysts remain divided: some, like those at CNBC, see the dip as a buying opportunity given Tesla's strong fundamentals and upcoming product launches, while others warn of increased regulatory headwinds that could slow growth. Trading volume was 1.8 times the average, indicating heightened investor anxiety about regulatory risks. The company's next earnings report, scheduled for later this month, will be closely watched for updates on regulatory issues and delivery numbers. Insider activity has been neutral, but any significant buying or selling by executives could further impact sentiment."

IMPORTANT: Return ONLY valid JSON. No additional text before or after the JSON object.
"""
        
        return prompt
    
    def generate_script(self, market_data: Dict) -> Dict:
        """Generate the complete script using OpenAI"""
        logger.info("Starting script generation")
        
        try:
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
        
        # Create a realistic mock script
        mock_script = {
            "intro": f"Welcome to Market Voices! I'm {lead_host_info['name']}, and today we're breaking down the NASDAQ-100 performance with my colleague {supporting_host_info['name']}. Let's dive into today's market action.",
            "segments": [
                {
                    "host": lead_host,
                    "text": f"Today was an interesting session for the NASDAQ-100. We saw {market_data.get('market_summary', {}).get('advancing_stocks', 0)} stocks advance and {market_data.get('market_summary', {}).get('declining_stocks', 0)} decline, with an average change of {market_data.get('market_summary', {}).get('average_change', 0):.2f}%. This suggests a mixed but generally positive day for tech stocks.",
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
                    "text": "The market is showing resilience despite some volatility. Volume was healthy, and institutional buying patterns suggest continued confidence in the tech sector's long-term prospects.",
                    "topic": "Market Sentiment"
                }
            ],
            "outro": f"This wraps up today's Market Voices analysis. Thanks for joining us, and don't forget to subscribe for daily market insights. This is {lead_host_info['name']}, signing off.",
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
        
        # Create intro
        intro = f"Welcome to Market Voices! I'm {lead_host_info['name']}, and today we're breaking down the NASDAQ-100 performance with my colleague {supporting_host_info['name']}. Let's dive into today's market action."
        
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
        
        # Create outro
        outro = f"This wraps up today's Market Voices analysis. Thanks for joining us, and don't forget to subscribe for daily market insights. This is {lead_host_info['name']}, signing off."
        
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