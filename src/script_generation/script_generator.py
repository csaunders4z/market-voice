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
        """
        Create the prompt for script generation with enhanced analysis, news integration,
        and technical assessment for each stock.
        """
        # Add detailed logging of input data structure
        logger.info("=== Market Data Structure ===")
        logger.info(f"Top level keys: {list(market_data.keys())}")
        
        if 'detailed_data' in market_data and market_data['detailed_data']:
            logger.info(f"Detailed data keys: {list(market_data['detailed_data'].keys())}")
            
            if 'market_summary' in market_data['detailed_data']:
                logger.info("Market summary available")
                
            if 'enhanced_analysis' in market_data['detailed_data']:
                logger.info("Enhanced analysis available")
        
        # Get base prompt with host-specific instructions
        base_prompt = self._get_base_script_prompt(lead_host)
        
        # Get market summary and analysis
        market_summary = market_data.get('detailed_data', {}).get('market_summary', {})
        enhanced_summary = market_data.get('detailed_data', {}).get('enhanced_analysis', 'No enhanced analysis available')
        
        # Log the type and content of market summary for debugging
        logger.info(f"Market summary type: {type(market_summary)}")
        if isinstance(market_summary, dict):
            logger.info(f"Market summary keys: {list(market_summary.keys())}")
        
        # Get news data if available
        news_data = market_data.get('detailed_data', {}).get('news_data', {})
        
        # Get top winners and losers - check both root level and detailed_data
        winners = market_data.get('top_winners', [])
        losers = market_data.get('bottom_losers', [])
        
        # If not found at root, try detailed_data
        if not winners and 'detailed_data' in market_data:
            winners = market_data['detailed_data'].get('top_winners', [])
        if not losers and 'detailed_data' in market_data:
            losers = market_data['detailed_data'].get('bottom_losers', [])
        
        # Log the number of winners and losers found
        logger.info(f"Found {len(winners)} winners and {len(losers)} losers")
        
        def get_technical_analysis(stock: Dict) -> str:
            """Generate technical analysis for a stock based on available data."""
            analysis = []
            
            # Log the stock data structure for debugging
            logger.info(f"Stock data for {stock.get('symbol', 'unknown')}:")
            for key, value in stock.items():
                logger.info(f"  {key}: {value}")
            
            # Price movement
            price = stock.get('price', 0)
            prev_close = stock.get('previous_close', 0)
            if prev_close and price:
                change = price - prev_close
                pct_change = (change / prev_close) * 100 if prev_close != 0 else 0
                direction = "up" if pct_change >= 0 else "down"
                analysis.append(f"- Price moved {direction} {abs(pct_change):.2f}% from ${prev_close:.2f} to ${price:.2f}")
            
            # Volume analysis with fallback
            volume = stock.get('volume', 0)
            avg_volume = stock.get('average_volume', 0)
            
            # If volume data is missing, try to get it from alternative keys
            if not volume and 'current_volume' in stock:
                volume = stock['current_volume']
            if not avg_volume and 'avg_volume' in stock:
                avg_volume = stock['avg_volume']
                
            if volume and avg_volume and avg_volume > 0:
                volume_ratio = volume / avg_volume
                if volume_ratio > 2.0:
                    analysis.append(f"- Extremely heavy trading volume ({volume_ratio:.1f}x average)")
                elif volume_ratio > 1.5:
                    analysis.append(f"- Higher than average trading volume ({volume_ratio:.1f}x average)")
                elif volume_ratio < 0.7:
                    analysis.append(f"- Lower than average trading volume ({volume_ratio:.1f}x average)")
            
            # RSI with fallback
            rsi = stock.get('rsi')
            if rsi is None and 'technical_indicators' in stock and 'rsi' in stock['technical_indicators']:
                rsi = stock['technical_indicators']['rsi']
                
            if rsi is not None:
                rsi = float(rsi)  # Ensure it's a float
                if rsi > 70:
                    analysis.append(f"- RSI at {rsi:.1f} indicates overbought conditions")
                elif rsi < 30:
                    analysis.append(f"- RSI at {rsi:.1f} indicates oversold conditions")
                else:
                    analysis.append(f"- RSI at {rsi:.1f} shows neutral momentum")
            
            # Moving Averages with fallbacks
            ma50 = stock.get('ma_50')
            ma200 = stock.get('ma_200')
            
            # Try alternative keys if standard ones aren't found
            if ma50 is None and 'moving_averages' in stock and '50_day' in stock['moving_averages']:
                ma50 = stock['moving_averages']['50_day']
            if ma200 is None and 'moving_averages' in stock and '200_day' in stock['moving_averages']:
                ma200 = stock['moving_averages']['200_day']
            
            if ma50 and ma200 and price:
                ma50 = float(ma50)
                ma200 = float(ma200)
                if price > ma50 > ma200:
                    analysis.append(f"- Price above both 50-day (${ma50:.2f}) and 200-day (${ma200:.2f}) moving averages")
                elif price < ma50 < ma200:
                    analysis.append(f"- Price below both 50-day (${ma50:.2f}) and 200-day (${ma200:.2f}) moving averages")
                elif ma50 > price > ma200:
                    analysis.append(f"- Price between 50-day (${ma50:.2f}) and 200-day (${ma200:.2f}) moving averages")
                elif price > ma200 > ma50:
                    analysis.append(f"- Price above 200-day MA (${ma200:.2f}) with golden cross pattern")
                elif price < ma200 < ma50:
                    analysis.append(f"- Price below 200-day MA (${ma200:.2f}) with death cross pattern")
            
            return "\n".join(analysis) if analysis else "- Limited technical data available"
        
        def get_company_news_analysis(symbol: str) -> Tuple[str, str]:
            """Get news analysis for a company, returning both news items and a summary."""
            if not news_data:
                return "", ""
                
            company_news = news_data.get('company_news', {}).get(symbol, [])
            news_summary = news_data.get('news_summaries', {}).get(symbol, "")
            
            # Format individual news items
            news_items = []
            if company_news:
                for i, news in enumerate(company_news[:2], 1):  # Top 2 most recent news
                    if isinstance(news, dict):
                        source = news.get('source', {}).get('name', 'a news source') if isinstance(news.get('source'), dict) else news.get('source', 'a news source')
                        news_items.append(f"  {i}. {news.get('title', '')} (Source: {source})")
            
            return "\n".join(news_items), news_summary
        
        def format_stock_analysis(stock: Dict) -> str:
            """Format a comprehensive stock analysis including technicals and news."""
            symbol = stock.get('symbol', 'N/A')
            company_name = stock.get('company_name', stock.get('name', 'N/A'))
            percent_change = stock.get('change_percent', stock.get('percent_change', 0))
            price = stock.get('price', 0)
            
            # Get technical analysis
            technicals = get_technical_analysis(stock)
            
            # Get news items and summary
            news_items, news_summary = get_company_news_analysis(symbol)
            
            # Format the analysis
            analysis = [
                f"{symbol} ({company_name}): {float(percent_change):.2f}% to ${float(price):.2f}",
                "Technical Analysis:",
                technicals,
                ""
            ]
            
            if news_items or news_summary:
                analysis.append("Recent News:")
                if news_items:
                    analysis.append(news_items)
                if news_summary:
                    analysis.append(f"\nNews Summary: {news_summary}")
            else:
                analysis.append("No significant news found.")
            
            return "\n".join(analysis)
        
        # Format winners and losers with comprehensive analysis
        winners_analysis = "\n\n".join([format_stock_analysis(w) for w in winners if w]) or "No significant gainers today."
        losers_analysis = "\n\n".join([format_stock_analysis(l) for l in losers if l]) or "No significant losers today."
        
        # Get market news summary if available
        market_news_summary = ""
        if news_data and 'market_news' in news_data and news_data['market_news']:
            # Get top 2 most relevant market news items
            top_market_news = sorted(
                news_data['market_news'],
                key=lambda x: x.get('relevance_score', 0) if isinstance(x, dict) else 0,
                reverse=True
            )[:2]
            
            if top_market_news:
                market_news_summary = "\n\nMARKET NEWS HIGHLIGHTS:\n"
                for i, news in enumerate(top_market_news, 1):
                    if isinstance(news, dict):
                        source = news.get('source', {}).get('name', 'a news source') if isinstance(news.get('source'), dict) else news.get('source', 'a news source')
                        market_news_summary += f"{i}. {news.get('title', '')} (Source: {source})\n"
        
        # Get index coverage from collected data
        index_coverage = market_data.get('index_coverage', {})
        sp500_expected = index_coverage.get('sp500_total', 500)
        nasdaq100_expected = index_coverage.get('nasdaq100_total', 100)
        sp500_coverage = index_coverage.get('sp500_analyzed', 0)
        nasdaq100_coverage = index_coverage.get('nasdaq100_analyzed', 0)
        
        # Check for sufficient coverage - treat as fatal error if not met
        if sp500_coverage < sp500_expected * 0.8 or nasdaq100_coverage < nasdaq100_expected * 0.8:
            error_msg = (
                f"Insufficient index coverage for script generation. "
                f"S&P 500: {sp500_coverage}/{sp500_expected} ({(sp500_coverage/max(1, sp500_expected)*100):.1f}%), "
                f"NASDAQ-100: {nasdaq100_coverage}/{nasdaq100_expected} ({(nasdaq100_coverage/max(1, nasdaq100_expected)*100):.1f}%). "
                "This is a critical error. Please check data collection logs for issues."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Amend the foundational prompt with daily market data, news, and analysis
        prompt = f"""{base_prompt}

---

TODAY'S MARKET OVERVIEW:
{enhanced_summary}

TOP GAINERS ANALYSIS:
{winners_analysis}

TOP LOSERS ANALYSIS:
{losers_analysis}

{market_news_summary}

SCRIPT GENERATION INSTRUCTIONS:
1. For each stock, analyze both the technical factors and news catalysts that contributed to its movement.
2. Explain the price action in the context of both technical indicators and fundamental news.
3. For significant movers, provide a clear narrative of what happened and likely why.
4. When technicals and news align (e.g., positive news with strong volume), highlight this confluence.
5. For stocks with significant moves but no clear news, focus on technical factors and potential market sentiment.
6. Maintain a professional but engaging tone, explaining technical terms for a general audience.
7. Keep each stock analysis concise but informative (2-4 sentences).
8. Ensure smooth transitions between different stocks and market segments.

(Use all provided data and follow the foundational prompt above. Do not invent information. Write a natural, flowing script alternating hosts as described.)
"""
        
        return prompt

    def _get_base_script_prompt(self, lead_host: str) -> str:
        """
        Create a base script prompt template with host-specific instructions.
        
        Args:
            lead_host: The key for the lead host ('marcus' or 'suzanne')
            
        Returns:
            str: The base prompt template with host-specific instructions
        """
        host_info = self.get_host_info(lead_host)
        other_host = 'suzanne' if lead_host == 'marcus' else 'marcus'
        other_host_info = self.get_host_info(other_host)
        
        return f"""You are a professional financial news script writer creating a script for "Market Voices" financial news program that airs each evening after market close daily on YouTube, for investors looking for immediate market insights and analysis. 
The script should be engaging, informative, and professional, targeting retail investors. However, you can also inject moments of levity between the hosts or small, polite jokes.

HOST DETAILS:
- Lead Host: {host_info['name']} ({host_info['background']})
- Co-Host: {other_host_info['name']} ({other_host_info['background']})

HOST STYLES:
- {host_info['name']}'s Style: {host_info['style']}
- {other_host_info['name']}'s Style: {other_host_info['style']}

SCRIPT FORMAT:
1. Start with a warm greeting and brief market overview
2. Discuss key market movers and their news
3. Provide analysis of market trends
4. Include relevant technical analysis
5. End with a summary and sign-off

TONE: Professional, engaging, and conversational. Avoid financial jargon unless explained.

TARGET RUNTIME: {self.get_target_runtime()} minutes

INSTRUCTIONS:
- Keep segments casually professional in tone
- Balance speaking time between hosts
- Use natural transitions between segments
- Include relevant statistics and data points
- Maintain a professional but approachable tone
- Keep technical analysis clear and actionable
- Highlight key support/resistance levels when relevant
- Include volume analysis for significant moves
- Reference news catalysts for major price movements but do not cite individual news sources unless they are a major business publication like the Wall Street Journal or CNBC
- End with a clear call to tune in during the next business day and like or subscribe to the channel if audiences enjoy the content
"""

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

        if repeats:
            logger.warning(f"Quality warning: Repeated 4-word phrases detected: {repeats}")
        
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
1. Balancing speaking time between hosts (40-60% split)
2. Reducing repetitive phrases
3. Improving transitions between segments
4. Ensuring proper content length
5. Maintaining casually professional financial news tone
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
