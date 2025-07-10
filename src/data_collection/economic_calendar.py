"""
Economic calendar for Market Voices
Provides Fed meeting dates, economic data releases, and market-moving events
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import os

from src.config.settings import get_settings


class EconomicCalendar:
    """Provides economic calendar data for market analysis"""
    
    def __init__(self):
        self.settings = get_settings()
        self.fred_api_key = os.getenv("FRED_API_KEY", "")
        
    def get_fed_meeting_dates(self) -> List[Dict]:
        """Get upcoming Federal Reserve meeting dates"""
        # 2024 Fed meeting schedule (hardcoded for now, could be API-driven)
        fed_meetings_2024 = [
            {"date": "2024-01-31", "type": "FOMC Meeting", "description": "Federal Open Market Committee Meeting"},
            {"date": "2024-03-20", "type": "FOMC Meeting", "description": "Federal Open Market Committee Meeting"},
            {"date": "2024-05-01", "type": "FOMC Meeting", "description": "Federal Open Market Committee Meeting"},
            {"date": "2024-06-12", "type": "FOMC Meeting", "description": "Federal Open Market Committee Meeting"},
            {"date": "2024-07-31", "type": "FOMC Meeting", "description": "Federal Open Market Committee Meeting"},
            {"date": "2024-09-18", "type": "FOMC Meeting", "description": "Federal Open Market Committee Meeting"},
            {"date": "2024-11-07", "type": "FOMC Meeting", "description": "Federal Open Market Committee Meeting"},
            {"date": "2024-12-18", "type": "FOMC Meeting", "description": "Federal Open Market Committee Meeting"}
        ]
        
        # Filter for upcoming meetings
        today = datetime.now().date()
        upcoming_meetings = []
        
        for meeting in fed_meetings_2024:
            meeting_date = datetime.strptime(meeting["date"], "%Y-%m-%d").date()
            if meeting_date >= today:
                days_until = (meeting_date - today).days
                meeting["days_until"] = days_until
                meeting["is_this_week"] = days_until <= 7
                upcoming_meetings.append(meeting)
        
        return upcoming_meetings[:3]  # Return next 3 meetings
    
    def get_comprehensive_calendar(self) -> Dict:
        """Get comprehensive economic calendar data"""
        try:
            fed_meetings = self.get_fed_meeting_dates()
            
            # Find immediate market movers (this week)
            immediate_events = []
            
            for meeting in fed_meetings:
                if meeting.get("is_this_week"):
                    immediate_events.append({
                        "type": "Fed Meeting",
                        "date": meeting["date"],
                        "description": meeting["description"],
                        "impact": "Very High"
                    })
            
            return {
                "fed_meetings": fed_meetings,
                "immediate_events": immediate_events,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive calendar: {str(e)}")
            return {
                "fed_meetings": [],
                "immediate_events": [],
                "timestamp": datetime.now().isoformat()
            }


# Global instance
economic_calendar = EconomicCalendar()
