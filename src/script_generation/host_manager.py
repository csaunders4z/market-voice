

        
        
        # Host personalities and characteristics
        self.hosts = {
            'marcus': {
                'name': 'Marcus',
                'age': 25,
                'personality': get_settings().marcus_personality,
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
                'personality': get_settings().suzanne_personality,
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
        tolerance = get_settings().speaking_time_tolerance
        balanced = (0.45 <= marcus_ratio <= 0.55) and (0.45 <= suzanne_ratio <= 0.55)
        
        logger.info(f"Speaking time balance - Marcus: {marcus_ratio:.2%}, Suzanne: {suzanne_ratio:.2%}")
        
        return balanced


# Global instance
host_manager = HostManager() 