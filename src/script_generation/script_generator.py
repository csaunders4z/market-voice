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
        """Create the prompt for script generation"""
        
        # Get host information
        lead_host_info = host_manager.get_host_info(lead_host)
        supporting_host = 'marcus' if lead_host == 'suzanne' else 'suzanne'
        supporting_host_info = host_manager.get_host_info(supporting_host)
        
        # Format market data with enhanced information
        winners = market_data.get('winners', [])
        losers = market_data.get('losers', [])
        summary = market_data.get('market_summary', {})
        
        # Create enhanced winners section with technical indicators
        winners_text = ""
        for i, winner in enumerate(winners[:5], 1):
            tech_indicators = []
            if winner.get('rsi', 0) > 70:
                tech_indicators.append(f"RSI: {winner['rsi']:.1f} (overbought)")
            if winner.get('volume_ratio', 0) > 2:
                tech_indicators.append(f"Volume: {winner['volume_ratio']:.1f}x average")
            if winner.get('macd_signal'):
                tech_indicators.append("MACD bullish crossover")
            
            tech_text = f" [{', '.join(tech_indicators)}]" if tech_indicators else ""
            winners_text += f"{i}. {winner['company_name']} ({winner['symbol']}): ${winner['current_price']:.2f} (+{winner['percent_change']:.2f}%){tech_text}\n"
            
            # Add news context if available
            if winner.get('news_summary'):
                winners_text += f"   News: {winner['news_summary'][:100]}...\n"
        
        # Create enhanced losers section
        losers_text = ""
        for i, loser in enumerate(losers[:5], 1):
            tech_indicators = []
            if loser.get('rsi', 0) < 30:
                tech_indicators.append(f"RSI: {loser['rsi']:.1f} (oversold)")
            if loser.get('volume_ratio', 0) > 2:
                tech_indicators.append(f"Volume: {loser['volume_ratio']:.1f}x average")
            if loser.get('macd_signal') == 'bearish':
                tech_indicators.append("MACD bearish crossover")
            
            tech_text = f" [{', '.join(tech_indicators)}]" if tech_indicators else ""
            losers_text += f"{i}. {loser['company_name']} ({loser['symbol']}): ${loser['current_price']:.2f} ({loser['percent_change']:.2f}%){tech_text}\n"
            
            # Add news context if available
            if loser.get('news_summary'):
                losers_text += f"   News: {loser['news_summary'][:100]}...\n"
        
        # Market summary with enhanced context
        market_summary = f"""
Market Summary:
- Total stocks analyzed: {summary.get('total_stocks', 0)}
- Advancing stocks: {summary.get('advancing_stocks', 0)}
- Declining stocks: {summary.get('declining_stocks', 0)}
- Average change: {summary.get('average_change', 0):.2f}%
- Market sentiment: {summary.get('market_sentiment', 'Neutral')}
"""
        
        prompt = f"""
You are writing a script for "Market Voices," a daily NASDAQ-100 analysis show targeting educated viewers (college graduate/MBA level).

HOSTS:
- {lead_host_info['name']} ({lead_host_info['age']}): {lead_host_info['personality']}
- {supporting_host_info['name']} ({supporting_host_info['age']}): {supporting_host_info['personality']}

TODAY'S MARKET DATA:
{market_summary}

TOP 5 WINNERS:
{winners_text}

TOP 5 LOSERS:
{losers_text}

QUALITY REQUIREMENTS:
1. Create a {host_manager.get_target_runtime()}-minute script (1200-1800 words)
2. {lead_host_info['name']} leads and speaks first
3. Speaking time must be 45-55% split between hosts (strict requirement)
4. Use professional financial news tone - avoid AI-generated language patterns
5. Include 6-8 distinct segments with smooth transitions
6. Each segment should be 150-250 words
7. Assume viewers understand basic company descriptions (e.g., "leading chipmaker" not detailed explanations)
8. Include sector/industry context when multiple stocks in same sector are moving
9. For moves > 5%, reference multiple news sources when available
10. Use technical indicators (RSI, MACD, volume) when they are significant
11. Avoid repetitive phrases and overused financial terminology
12. Include logical transitions between segments (sector connections, opposing moves, etc.)

CONTENT STRUCTURE:
- Intro: Market overview and agenda
- Segment 1: Market sentiment and broad trends
- Segment 2: Top performers analysis (2-3 stocks)
- Segment 3: Decliners analysis (2-3 stocks)
- Segment 4: Sector-specific movements
- Segment 5: Technical analysis highlights
- Segment 6: Market outlook and closing thoughts
- Outro: Summary and sign-off

REQUIRED JSON STRUCTURE:
{{
    "intro": "Opening with {lead_host_info['name']}",
    "segments": [
        {{
            "host": "{lead_host}",
            "text": "Segment text here",
            "topic": "Market Overview",
            "word_count": 180
        }},
        {{
            "host": "{supporting_host}",
            "text": "Segment text here", 
            "topic": "Top Performers",
            "word_count": 200
        }}
    ],
    "outro": "Closing with {lead_host_info['name']}",
    "estimated_runtime_minutes": {host_manager.get_target_runtime()},
    "speaking_time_balance": {{
        "marcus_percentage": 50,
        "suzanne_percentage": 50
    }},
    "quality_metrics": {{
        "total_words": 1500,
        "segments_count": 6,
        "technical_indicators_used": 3,
        "news_sources_referenced": 5
    }}
}}

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
            
            # Try to parse as JSON
            try:
                script_data = json.loads(script_text)
                logger.info("Successfully parsed script as JSON")
            except json.JSONDecodeError:
                logger.warning("Failed to parse as JSON, creating structured format")
                script_data = self._create_structured_script(script_text, lead_host)
            
            # Validate and enhance the script
            script_data = self._validate_and_enhance_script(script_data, market_data, lead_host)
            
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
            text_parts.append(script_data['intro'])
        
        # Add segments
        for segment in script_data.get('segments', []):
            text_parts.append(segment.get('text', ''))
        
        # Add outro
        if 'outro' in script_data:
            text_parts.append(script_data['outro'])
        
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
        
        # Quality metrics
        quality_metrics = script_data.get('quality_metrics', {})
        output.append("QUALITY METRICS:")
        output.append(f"Total Words: {quality_metrics.get('total_words', 0)}")
        output.append(f"Segments: {quality_metrics.get('segments_count', 0)}")
        output.append(f"Technical Indicators: {quality_metrics.get('technical_indicators_used', 0)}")
        output.append(f"News Sources: {quality_metrics.get('news_sources_referenced', 0)}")
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
        
        # Segments
        output.append("SEGMENTS:")
        for i, segment in enumerate(script_data.get('segments', []), 1):
            output.append(f"Segment {i} - {segment.get('host', 'Unknown').title()}:")
            output.append(f"Topic: {segment.get('topic', 'N/A')}")
            output.append(f"Words: {segment.get('word_count', 0)}")
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


# Global instance
script_generator = ScriptGenerator() 