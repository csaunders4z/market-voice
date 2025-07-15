"""
Script generator for Market Voices
Uses OpenAI to create professional financial news scripts
"""
import openai
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import re
from loguru import logger
import os
import random

from ..config.settings import get_settings
from ..content_validation.quality_controls import quality_controller

from ..data_collection.symbol_loader import symbol_loader


class ScriptGenerator:
    """Generates professional financial news scripts using OpenAI and manages host personalities and rotation schedule"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.Client(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_model
        self.max_tokens = self.settings.max_tokens
        self.temperature = self.settings.temperature
        import pytz
        self.est_tz = pytz.timezone('US/Eastern')
        # Host personalities and characteristics
        self.hosts = {
            'marcus': {
                'name': 'Marcus',
                'age': 25,
                'personality': self.settings.marcus_personality,
                'tone': 'energetic and enthusiastic',
                'style': 'fresh perspective, tech-savvy, millennial approach',
                'background': 'energetic analyst with a fresh perspective on markets',
                'speaking_patterns': [
                    "Hey everyone, Marcus here!",
                    "This is really interesting to see...",
                    "What's fascinating about this is...",
                    "I'm excited to dive into...",
                    "This could be a game-changer...",
                    "Let me break this down for you...",
                    "Here's what caught my attention..."
                ],
                'transitions': [
                    "Now, let's shift gears to...",
                    "Speaking of interesting moves...",
                    "This brings us to...",
                    "On the flip side...",
                    "Meanwhile, over in...",
                    "Let's not forget about..."
                ]
            },
            'suzanne': {
                'name': 'Suzanne',
                'age': 31,
                'personality': self.settings.suzanne_personality,
                'tone': 'professional and analytical',
                'style': 'experienced trader perspective, deep market knowledge',
                'background': 'former Wall Street trader with deep market knowledge',
                'speaking_patterns': [
                    "Good evening, I'm Suzanne.",
                    "From a trading perspective...",
                    "What we're seeing here is...",
                    "This movement suggests...",
                    "The market is telling us...",
                    "Let me analyze this for you...",
                    "This is significant because..."
                ],
                'transitions': [
                    "Moving on to...",
                    "Another notable development...",
                    "This connects to...",
                    "In contrast...",
                    "Additionally...",
                    "It's also worth noting..."
                ]
            }
        }

    def get_lead_host_for_date(self, date: Optional[datetime] = None) -> str:
        """Determine which host leads for a given date"""
        if date is None:
            date = datetime.now(self.est_tz)
        weekday = date.weekday()  # Monday = 0, Tuesday = 1, etc.
        # Suzanne leads: Monday (0), Tuesday (1), Thursday (3)
        # Marcus leads: Wednesday (2), Friday (4)
        if weekday in [0, 1, 3]:  # Mon, Tue, Thu
            return 'suzanne'
        else:  # Wed, Fri
            return 'marcus'

    def get_host_info(self, host_key: str) -> Dict:
        """Get host information and personality"""
        return self.hosts.get(host_key, {})

    def get_both_hosts_info(self) -> Tuple[Dict, Dict]:
        """Get information for both hosts"""
        lead_host = self.get_lead_host_for_date()
        supporting_host = 'marcus' if lead_host == 'suzanne' else 'suzanne'
        return self.hosts[lead_host], self.hosts[supporting_host]

    def get_host_rotation_schedule(self) -> Dict:
        """Get the weekly host rotation schedule"""
        return {
            'monday': 'suzanne',
            'tuesday': 'suzanne', 
            'wednesday': 'marcus',
            'thursday': 'suzanne',
            'friday': 'marcus'
        }

    def get_target_runtime(self, date: Optional[datetime] = None) -> int:
        """Get target runtime for a given date"""
        if date is None:
            date = datetime.now(self.est_tz)
        weekday = date.weekday()
        # Thursday and Friday: 10 minutes
        # Other days: 15 minutes
        if weekday in [3, 4]:  # Thu, Fri
            return 10
        else:
            return 15

    def get_intro_template(self, lead_host: str) -> str:
        """Get intro template for the lead host"""
        host_info = self.hosts[lead_host]
        intro_templates = {
            'marcus': (
                "Hey everyone, Marcus here! Welcome to Market Voices, your daily "
                "dive into what's moving the major US markets. I'm excited to break down "
                "today's biggest winners and losers with you."
            ),
            'suzanne': (
                "Good evening, I'm Suzanne. Welcome to Market Voices, where we "
                "analyze the day's major US market performance with the perspective "
                "of experienced market professionals."
            )
        }
        return intro_templates.get(lead_host, "")

    def get_outro_template(self, lead_host: str) -> str:
        """Get outro template for the lead host"""
        host_info = self.hosts[lead_host]
        outro_templates = {
            'marcus': (
                "That wraps up today's market analysis! Don't forget to subscribe "
                "for daily insights, and I'll see you tomorrow for more market action. "
                "This is Marcus, signing off!"
            ),
            'suzanne': (
                "Thank you for joining us today. Remember to subscribe for your "
                "daily market intelligence, and we'll be back tomorrow with more "
                "analysis. This is Suzanne, good evening."
            )
        }
        return outro_templates.get(lead_host, "")

    def get_host_transition(self, from_host: str, to_host: str, context: str = "") -> str:
        """Generate a transition between hosts"""
        from_info = self.hosts[from_host]
        to_info = self.hosts[to_host]
        transitions = [
            f"Now let me hand it over to {to_info['name']} for more analysis.",
            f"{to_info['name']}, what's your take on this?",
            f"Let me bring in {to_info['name']} for additional perspective.",
            f"{to_info['name']}, I'd love to hear your thoughts on this."
        ]
        return transitions[0]  # For now, use the first transition

    def validate_speaking_time_balance(self, script_segments: List[Dict]) -> bool:
        """Validate that speaking time is balanced between hosts"""
        marcus_time = 0
        suzanne_time = 0
        for segment in script_segments:
            if segment.get('host') == 'marcus':
                marcus_time += len(segment.get('text', '').split())
            elif segment.get('host') == 'suzanne':
                suzanne_time += len(segment.get('text', '').split())
        total_words = marcus_time + suzanne_time
        if total_words == 0:
            return True
        marcus_ratio = marcus_time / total_words
        suzanne_ratio = suzanne_time / total_words
        # Check if ratios are within tolerance (45-55% each)
        tolerance = self.settings.speaking_time_tolerance
        balanced = (0.45 <= marcus_ratio <= 0.55) and (0.45 <= suzanne_ratio <= 0.55)
        logger.info(f"Speaking time balance - Marcus: {marcus_ratio:.2%}, Suzanne: {suzanne_ratio:.2%}")
        return balanced

        
    def create_script_prompt(self, market_data: Dict, lead_host: str) -> str:
        """Create the prompt for script generation with enhanced analysis"""
        
        # Get host information
        lead_host_info = self.get_host_info(lead_host)
        supporting_host = 'marcus' if lead_host == 'suzanne' else 'suzanne'
        supporting_host_info = self.get_host_info(supporting_host)

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
        nasdaq100_count = len(symbol_loader.get_nasdaq_100_symbols())
        sp500_count = len(symbol_loader.get_sp_500_symbols())
        coverage_percentage = market_summary.get('coverage_percentage', 0)
        
        # Determine market coverage description
        sp500_coverage_val = market_summary.get('sp500_coverage', 0)
        nasdaq100_coverage_val = market_summary.get('nasdaq100_coverage', 0)
        if sp500_count > 0 and nasdaq100_count > 0:
            market_coverage_desc = f"Analyzing {sp500_count} S&P 500 and {nasdaq100_count} NASDAQ-100 stocks ({coverage_percentage:.1f}% coverage)"
        elif sp500_count > 0:
            market_coverage_desc = f"Analyzing {sp500_count} S&P 500 stocks"
        elif nasdaq100_count > 0:
            market_coverage_desc = f"Analyzing {nasdaq100_count} NASDAQ-100 stocks"
        elif sp500_coverage_val > 0 and nasdaq100_coverage_val > 0:
            market_coverage_desc = f"Analyzing {sp500_coverage_val} S&P 500 and {nasdaq100_coverage_val} NASDAQ-100 stocks (coverage from market_summary)"
        elif sp500_coverage_val > 0:
            market_coverage_desc = f"Analyzing {sp500_coverage_val} S&P 500 stocks (coverage from market_summary)"
        elif nasdaq100_coverage_val > 0:
            market_coverage_desc = f"Analyzing {nasdaq100_coverage_val} NASDAQ-100 stocks (coverage from market_summary)"
        else:
            market_coverage_desc = market_summary.get('market_coverage', 'Analyzing major US stocks including NASDAQ-100 and S&P 500')
        
        enhanced_summary = f"""
MARKET OVERVIEW:
- Market Analysis: {market_coverage_desc}
- Stocks analyzed: {market_summary.get('total_stocks_analyzed', 0)} out of {total_target_symbols} total target stocks
- S&P 500 coverage: {sp500_count} stocks
- NASDAQ-100 coverage: {nasdaq100_count} stocks
- Advancing: {market_summary.get('advancing_stocks', 0)}, Declining: {market_summary.get('declining_stocks', 0)}
- Average change: {market_summary.get('average_change', 0):.2f}%
- Market sentiment: {market_summary.get('market_sentiment', 'Mixed')}
- Data source: {market_summary.get('data_source', 'Unknown')}
- Economic context: {economic_context}
{news_analysis}
{free_news_text}
"""
        
        # Foundational Prompt Approach:
        # Load the foundational script generation prompt from planning/script_generation_requirements.md.
        # This file defines the style, tone, and overall rules for script generation.
        # At runtime, we amend this foundational prompt with current market data, news, and analysis.
        foundational_prompt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../planning/script_generation_requirements.md'))
        try:
            with open(foundational_prompt_path, 'r', encoding='utf-8') as prompt_file:
                base_prompt = prompt_file.read()
                logger.info(f"Loaded foundational prompt from {foundational_prompt_path}")
        except Exception as e:
            logger.warning(f"Could not load foundational prompt from {foundational_prompt_path}: {e}. Using fallback prompt.")
            base_prompt = (
                "You are writing a professional financial news script for Market Voices. "
                "The script must include both hosts, top 5 gainers and losers, and be natural, engaging, and data-driven. "
                "Alternate hosts, use provided data only, and maintain a professional tone."
            )
        # Amend the foundational prompt with daily market data and analysis
        # (This logic can be further refined as needed)
        prompt = f"""{base_prompt}\n\n---\n\nTODAY'S MARKET DATA:\n{enhanced_summary}\n\nTOP 5 WINNERS:\n{winners_text}\n\nTOP 5 LOSERS:\n{losers_text}\n\n(Use all provided data and follow the foundational prompt above. Do not invent information. Write a natural, flowing script alternating hosts as described.)\n"""
        # Calculate coverage for S&P 500 and NASDAQ-100
        sp500_expected = len(symbol_loader.get_sp_500_symbols())
        nasdaq100_expected = len(symbol_loader.get_nasdaq_100_symbols())
        sp500_coverage = market_summary.get('sp500_coverage', 0)
        nasdaq100_coverage = market_summary.get('nasdaq100_coverage', 0)
        # Fallback: if market_summary does not have coverage, use analyzed counts
        if not sp500_coverage:
            sp500_coverage = market_summary.get('sp500_analyzed', 0) or 0
        if not nasdaq100_coverage:
            nasdaq100_coverage = market_summary.get('nasdaq100_analyzed', 0) or 0
        # Error handling for insufficient coverage
        if sp500_coverage < sp500_expected or nasdaq100_coverage < nasdaq100_expected:
            logger.warning(f'Insufficient index coverage for script generation. S&P 500: {sp500_coverage}/{sp500_expected}, NASDAQ-100: {nasdaq100_coverage}/{nasdaq100_expected}')
        return prompt

    def _create_structured_script(self, script_text: str, lead_host: str) -> Dict:
        lead_host_info = self.get_host_info(lead_host)
        supporting_host = 'marcus' if lead_host == 'suzanne' else 'suzanne'
        supporting_host_info = self.get_host_info(supporting_host)
        
        # Define segment topics
        segment_topics = [
            "Market Overview",
            "Top Performers Analysis", 
            "Decliners Analysis",
            "Market Sentiment & Outlook"
        ]
        
        paragraphs = [p.strip() for p in script_text.split('\n\n') if p.strip()]
        
        # Check anti-repetition: no phrase >3 words appears more than twice
        import re
        words = script_text.split()
        ngrams = [" ".join(words[i:i+4]) for i in range(len(words)-3)]
        ngram_counts = {}
        for ng in ngrams:
            ngram_counts[ng] = ngram_counts.get(ng,0)+1
        repeats = [ng for ng, count in ngram_counts.items() if count > 2]
        print(f"Repeated 4-word phrases: {repeats}")

        if repeats:
            print("[Prototype] Would call OpenAI to rewrite problematic sentences/segments.")
            self.rewrite_problematic_sentences_with_openai(script_text, repeats, paragraphs)

        assert not repeats, "No 4-word phrase should appear more than twice"
        
        segments = []
        current_host = lead_host
        
        # Create intro with natural opening
        intro = f"{lead_host_info['name']}: Good morning, I'm {lead_host_info['name']}, and welcome to today's market analysis!"
        
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
            "estimated_runtime_minutes": self.get_target_runtime(),
            "speaking_time_balance": {
                "marcus_percentage": marcus_percentage,
                "suzanne_percentage": suzanne_percentage
            }
        }

    def rewrite_problematic_sentences_with_openai(self, script_text, repeated_phrases, paragraphs):
        """
        For each problematic sentence/segment, call OpenAI to rewrite it to avoid the repeated phrases.
        Replace the sentence in the script with the OpenAI response. Log errors and fall back to the original if needed.
        """
        import re
        for phrase in repeated_phrases:
            # Find all paragraphs containing the repeated phrase
            hits = [p for p in paragraphs if phrase in p]
            for hit in hits:
                prompt = (
                    f"Rewrite the following sentence or segment to avoid the phrase: '{phrase}'.\n"
                    f"Other phrases to avoid: {repeated_phrases}.\n"
                    f"Context: {hit}\n"
                    f"Instructions: Keep the meaning and style appropriate for a professional financial news broadcast."
                )
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a financial news script editor."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=256,
                        temperature=0.7
                    )
                    new_text = response.choices[0].message.content.strip()
                    print(f"[OpenAI] Rewriting segment.\nOld: {hit}\nNew: {new_text}")
                    # Replace the old segment in script_text (or paragraphs) with the new one
                    idx = paragraphs.index(hit)
                    paragraphs[idx] = new_text
                except Exception as e:
                    print(f"[OpenAI ERROR] Failed to rewrite segment: {e}. Keeping original.")
    
    def _validate_and_enhance_script(self, script_data: Dict, market_data: Dict, lead_host: str) -> Dict:
        
        # Ensure required fields exist
        if 'segments' not in script_data:
            script_data['segments'] = []
        
        if 'intro' not in script_data:
            script_data['intro'] = self.get_intro_template(lead_host)
        
        if 'outro' not in script_data:
            script_data['outro'] = self.get_outro_template(lead_host)
        
        # Validate speaking time balance
        if not self.validate_speaking_time_balance(script_data['segments']):
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
        market_summary = market_data.get('market_summary', {})
        if 'market_date' in market_summary:
            script_data['market_date'] = market_summary['market_date']
        else:
            script_data['market_date'] = datetime.now().isoformat()
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
        """Count unique news sources referenced in the script."""
        sources = set()
        # Check for a top-level 'news_sources' field
        news_sources = script_data.get('news_sources', [])
        if isinstance(news_sources, list):
            for entry in news_sources:
                if isinstance(entry, str):
                    sources.add(entry.strip())
                elif isinstance(entry, dict) and 'source' in entry:
                    sources.add(str(entry['source']).strip())
        # Scan winner and loser segments for 'source' keys
        for segment in script_data.get('winner_segments', []):
            if isinstance(segment, dict) and 'source' in segment:
                sources.add(str(segment['source']).strip())
        for segment in script_data.get('loser_segments', []):
            if isinstance(segment, dict) and 'source' in segment:
                sources.add(str(segment['source']).strip())
        # Optionally scan a top-level 'news' field if present
        for news_item in script_data.get('news', []):
            if isinstance(news_item, dict) and 'source' in news_item:
                sources.add(str(news_item['source']).strip())
            elif isinstance(news_item, str):
                sources.add(news_item.strip())
        return len([s for s in sources if s])

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

    def generate_script(self, market_data: Dict) -> Dict:
        """
        Main entry point for script generation
        """
        try:
            lead_host = self.get_lead_host_for_date()
            
            # Create script prompt with market data
            script_prompt = self.create_script_prompt(market_data, lead_host)
            
            # Generate script using OpenAI
            logger.info(f"Generating script with OpenAI model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional financial news script writer."},
                    {"role": "user", "content": script_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            script_text = response.choices[0].message.content.strip()
            
            # Create structured script
            structured_script = self._create_structured_script(script_text, lead_host)
            
            # Validate and enhance script
            enhanced_script = self._validate_and_enhance_script(structured_script, market_data, lead_host)
            
            # Add metadata
            enhanced_script.update({
                "generation_success": True,
                "lead_host": lead_host,
                "market_date": market_data.get('market_date', datetime.now().strftime('%Y-%m-%d')),
                "generation_timestamp": datetime.now().isoformat()
            })
            
            logger.info("Script generation completed successfully")
            return enhanced_script
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return {
                "generation_success": False,
                "error": str(e),
                "lead_host": self.get_lead_host_for_date(),
                "market_date": market_data.get('market_date', datetime.now().strftime('%Y-%m-%d')),
                "generation_timestamp": datetime.now().isoformat()
            }

    def format_script_for_output(self, script_data: Dict) -> str:
        """
        Format the script for human-readable output.
        """
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
        
        # All Segments (market overview, winners, losers, sentiment)
        segments = script_data.get('segments', [])
        if segments:
            output.append("SEGMENTS:")
            for i, segment in enumerate(segments, 1):
                host = segment.get('host', 'Unknown').title()
                topic = segment.get('topic', 'Unknown')
                output.append(f"Segment {i} ({topic}) by {host}:")
                output.append(segment.get('text', ''))
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


script_generator = ScriptGenerator()
