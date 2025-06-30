"""
Quality controls for Market Voices
Validates script quality, detects repetitions, and ensures factual accuracy
"""
import re
from typing import Dict, List, Tuple, Set
from collections import Counter
from loguru import logger


class QualityController:
    """Validates and controls content quality"""
    
    def __init__(self):
        self.max_phrase_repetitions = 2
        self.max_terminology_usage = 3
        self.forbidden_phrases = [
            "as you can see",
            "it's important to note",
            "let me tell you",
            "I want to point out",
            "it's worth mentioning",
            "as we can see",
            "it's clear that",
            "obviously",
            "clearly"
        ]
        
        self.financial_terminology = [
            "earnings per share",
            "price to earnings ratio",
            "market capitalization",
            "trading volume",
            "stock price",
            "market performance",
            "financial results",
            "quarterly earnings",
            "revenue growth",
            "profit margin"
        ]
    
    def validate_script_quality(self, script_data: Dict) -> Dict:
        """Comprehensive script quality validation"""
        validation_results = {
            'overall_score': 0,
            'issues': [],
            'warnings': [],
            'passed_checks': []
        }
        
        try:
            # Extract all text from script
            all_text = self._extract_all_text(script_data)
            
            # Run quality checks
            checks = [
                self._check_phrase_repetitions,
                self._check_terminology_usage,
                self._check_forbidden_phrases,
                self._check_speaking_time_balance,
                self._check_content_length,
                self._check_transitions
            ]
            
            for check in checks:
                result = check(script_data, all_text)
                validation_results['issues'].extend(result.get('issues', []))
                validation_results['warnings'].extend(result.get('warnings', []))
                validation_results['passed_checks'].extend(result.get('passed_checks', []))
            
            # Calculate overall score
            total_checks = len(checks)
            passed_checks = len(validation_results['passed_checks'])
            validation_results['overall_score'] = (passed_checks / total_checks) * 100
            
            logger.info(f"Quality validation completed. Score: {validation_results['overall_score']:.1f}%")
            
        except Exception as e:
            logger.error(f"Error in quality validation: {str(e)}")
            validation_results['issues'].append(f"Validation error: {str(e)}")
        
        return validation_results
    
    def _extract_all_text(self, script_data: Dict) -> str:
        """Extract all text content from script"""
        text_parts = []
        
        # Add intro
        if 'intro' in script_data:
            intro_text = script_data['intro']
            if isinstance(intro_text, str):
                text_parts.append(intro_text)
        
        # Add segments
        for segment in script_data.get('segments', []):
            if isinstance(segment, dict):
                segment_text = segment.get('text', '')
                if isinstance(segment_text, str):
                    text_parts.append(segment_text)
            elif isinstance(segment, str):
                text_parts.append(segment)
        
        # Add outro
        if 'outro' in script_data:
            outro_text = script_data['outro']
            if isinstance(outro_text, str):
                text_parts.append(outro_text)
        
        return ' '.join(text_parts).lower()
    
    def _check_phrase_repetitions(self, script_data: Dict, all_text: str) -> Dict:
        """Check for repetitive phrases"""
        result = {'issues': [], 'warnings': [], 'passed_checks': []}
        
        # Find phrases of 3+ words
        words = all_text.split()
        phrases = []
        
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            phrases.append(phrase)
        
        # Count phrase occurrences
        phrase_counts = Counter(phrases)
        repeated_phrases = {phrase: count for phrase, count in phrase_counts.items() 
                          if count > self.max_phrase_repetitions}
        
        if repeated_phrases:
            result['issues'].append(f"Found {len(repeated_phrases)} phrases repeated more than {self.max_phrase_repetitions} times")
            for phrase, count in list(repeated_phrases.items())[:5]:  # Show first 5
                result['warnings'].append(f"'{phrase}' repeated {count} times")
        else:
            result['passed_checks'].append("No excessive phrase repetitions found")
        
        return result
    
    def _check_terminology_usage(self, script_data: Dict, all_text: str) -> Dict:
        """Check for overuse of financial terminology"""
        result = {'issues': [], 'warnings': [], 'passed_checks': []}
        
        overused_terms = []
        for term in self.financial_terminology:
            count = all_text.count(term.lower())
            if count > self.max_terminology_usage:
                overused_terms.append((term, count))
        
        if overused_terms:
            result['issues'].append(f"Found {len(overused_terms)} terms used more than {self.max_terminology_usage} times")
            for term, count in overused_terms:
                result['warnings'].append(f"'{term}' used {count} times")
        else:
            result['passed_checks'].append("Financial terminology usage is appropriate")
        
        return result
    
    def _check_forbidden_phrases(self, script_data: Dict, all_text: str) -> Dict:
        """Check for forbidden phrases"""
        result = {'issues': [], 'warnings': [], 'passed_checks': []}
        
        found_phrases = []
        for phrase in self.forbidden_phrases:
            if phrase.lower() in all_text:
                found_phrases.append(phrase)
        
        if found_phrases:
            result['warnings'].append(f"Found {len(found_phrases)} forbidden phrases")
            for phrase in found_phrases:
                result['warnings'].append(f"Consider replacing: '{phrase}'")
        else:
            result['passed_checks'].append("No forbidden phrases found")
        
        return result
    
    def _check_speaking_time_balance(self, script_data: Dict, all_text: str) -> Dict:
        """Check speaking time balance between hosts"""
        result = {'issues': [], 'warnings': [], 'passed_checks': []}
        
        marcus_words = 0
        suzanne_words = 0
        
        for segment in script_data.get('segments', []):
            host = segment.get('host', '')
            text = segment.get('text', '')
            word_count = len(text.split())
            
            if host == 'marcus':
                marcus_words += word_count
            elif host == 'suzanne':
                suzanne_words += word_count
        
        total_words = marcus_words + suzanne_words
        if total_words > 0:
            marcus_ratio = marcus_words / total_words
            suzanne_ratio = suzanne_words / total_words
            
            # Check if ratios are within 45-55% range
            if 0.45 <= marcus_ratio <= 0.55 and 0.45 <= suzanne_ratio <= 0.55:
                result['passed_checks'].append("Speaking time is well balanced")
            else:
                result['issues'].append(f"Speaking time imbalance: Marcus {marcus_ratio:.1%}, Suzanne {suzanne_ratio:.1%}")
        else:
            result['warnings'].append("No speaking time data available")
        
        return result
    
    def _check_content_length(self, script_data: Dict, all_text: str) -> Dict:
        """Check if content length is appropriate"""
        result = {'issues': [], 'warnings': [], 'passed_checks': []}
        
        word_count = len(all_text.split())
        target_runtime = script_data.get('estimated_runtime_minutes', 12)
        
        # New requirements: minimum 1440 words, with 70% devoted to stock coverage
        min_words = 1440
        expected_stock_coverage = min_words * 0.7  # 1000+ words for stock coverage
        
        if word_count >= min_words:
            result['passed_checks'].append(f"Content length meets minimum requirement ({word_count} words >= {min_words})")
        else:
            result['issues'].append(f"Content length below minimum: {word_count} words (required: {min_words})")
        
        # Check stock coverage (approximate - look for stock symbols and company names)
        stock_indicators = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'ADBE', 'CRM']
        stock_mentions = sum(all_text.count(indicator.lower()) for indicator in stock_indicators)
        
        # Rough estimate: if we have significant stock mentions, we likely have good coverage
        if stock_mentions >= 10:  # At least 10 stock mentions across the script
            result['passed_checks'].append("Stock coverage appears adequate")
        else:
            result['warnings'].append("Stock coverage may be insufficient - ensure 70% of content covers top 5 winners and losers")
        
        return result
    
    def _check_transitions(self, script_data: Dict, all_text: str) -> Dict:
        """Check for smooth transitions between segments"""
        result = {'issues': [], 'warnings': [], 'passed_checks': []}
        
        transition_phrases = [
            'now', 'next', 'meanwhile', 'additionally', 'furthermore',
            'on the other hand', 'in contrast', 'however', 'nevertheless',
            'speaking of', 'this brings us to', 'let\'s move on to'
        ]
        
        transition_count = sum(all_text.count(phrase) for phrase in transition_phrases)
        segment_count = len(script_data.get('segments', []))
        
        if segment_count > 0:
            transitions_per_segment = transition_count / segment_count
            
            if transitions_per_segment >= 0.5:
                result['passed_checks'].append("Good use of transition phrases")
            else:
                result['warnings'].append(f"Consider adding more transitions (current: {transitions_per_segment:.1f} per segment)")
        else:
            result['warnings'].append("No segments found to check transitions")
        
        return result
    
    def suggest_improvements(self, validation_results: Dict) -> List[str]:
        """Generate improvement suggestions based on validation results"""
        suggestions = []
        
        if validation_results['overall_score'] < 80:
            suggestions.append("Overall quality score is below target. Review all issues and warnings.")
        
        if validation_results['issues']:
            suggestions.append("Address critical issues first before proceeding.")
        
        if validation_results['warnings']:
            suggestions.append("Consider addressing warnings to improve content quality.")
        
        # Specific suggestions based on issues
        for issue in validation_results['issues']:
            if 'phrase repetition' in issue.lower():
                suggestions.append("Review and vary repetitive phrases to improve flow.")
            elif 'speaking time' in issue.lower():
                suggestions.append("Adjust script to better balance speaking time between hosts.")
            elif 'terminology' in issue.lower():
                suggestions.append("Vary financial terminology to avoid overuse.")
        
        return suggestions


# Global instance
quality_controller = QualityController() 