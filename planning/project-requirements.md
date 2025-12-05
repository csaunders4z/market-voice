# Market Voices Project Requirements - MoSCoW Prioritization

## Overview
This document outlines the complete requirements for the Market Voices automated stock market video generation system, organized using the MoSCoW prioritization framework.

## MUST HAVE (Critical for MVP)

### Core Data Collection
- **Automated NASDAQ-100 data collection** after market close on weekdays
- **Top 5 winners and bottom 5 losers identification** with price, % change, volume data
- **Fallback mechanisms** when primary data sources are unavailable
- **Timestamped data** to ensure information freshness
- **Error handling and logging** for all data collection processes

### Script Generation System
- **Automated script creation** using collected market data
- **Two-host format** with Marcus (25, energetic analyst) and Suzanne (31, former Wall Street trader)
- **Character consistency** - Suzanne leads Mon/Tue/Thu, Marcus leads Wed/Fri
- **10-15 minute runtime** (10 min Thu/Fri, 15 min other days)
- **Professional financial news tone** matching cable TV standards
- **Daily intro/outro** with subscription calls-to-action

### Basic Content Standards
- **Factual accuracy** - no provably incorrect information
- **Causal explanations** for stock movements from credible sources
- **College/MBA-level audience** assumption
- **No obvious AI-generated patterns** or repetitive phrases
- **Company context** without over-explaining well-known companies

## SHOULD HAVE (Important for Quality)

### Enhanced Data Collection
- **News integration** for stocks with >2% movement
- **Technical indicators** (RSI >70/<30, MACD crossovers, volume >2x average)
- **Multiple data source validation** for moves >5%
- **Sector/industry context** when relevant
- **24-hour news recency** requirement

### Advanced Script Features
- **Natural speaking patterns** with appropriate pauses
- **Varied transition phrases** between segments
- **Balanced speaking time** (45-55% split between hosts)
- **Logical stock connections** when possible (sector trends, opposing moves)
- **Host personality distinctions** (Suzanne businesslike, Marcus lighter)
- **Occasional appropriate humor** from Marcus on notable days

### Content Quality Controls
- **No phrase repetition** (>3 words max twice per episode)
- **Stock terminology limits** (e.g., "earnings per share" max 3x per episode)
- **Smooth transitions** with max 2 seconds silence between segments
- **Conflicting news acknowledgment** with source preference hierarchy

## COULD HAVE (Nice to Have Features)

### Video Production
- **Automated voiceover generation** using ElevenLabs or similar
- **Basic video editing** with stock footage and charts
- **Professional intro/outro music** and sound effects
- **Auto-generated captions** for accessibility
- **Thumbnail creation** with company logos and price movements
- **10-25 minute video length** with visual variety

### Technical Enhancements
- **Caching mechanism** to avoid repeated API calls
- **AlphaVantage integration** as additional data source
- **Historical data storage** for trend analysis
- **Weekend/holiday handling** with alternative content
- **Automated scheduling** for YouTube uploads

### Content Expansion
- **Weekly market wrap videos** on Fridays
- **Market preview content** for upcoming weeks
- **Holiday/non-trading day** alternative content
- **Extended commentary** on major market events

## WON'T HAVE (Future Considerations)

### Advanced Monetization
- **Sponsorship integration automation**
- **Affiliate link management** in video descriptions
- **Advanced SEO optimization** with VidIQ/TubeBuddy
- **Multiple channel scaling** infrastructure

### Premium Features
- **Real-time market alerts** during trading hours
- **Interactive viewer engagement** features
- **Paid newsletter integration**
- **Advanced technical analysis** (moving averages, support/resistance)

### Enterprise Capabilities
- **Multi-language support** for international markets
- **Custom branding** for white-label solutions
- **Advanced analytics dashboard** for performance tracking
- **A/B testing framework** for content optimization

## Success Metrics

### Technical KPIs
- **Data collection success rate**: >95% for NASDAQ-100 tickers
- **Script generation time**: <5 minutes after market close
- **System uptime**: >99% during trading days
- **API cost efficiency**: <$200/month for data sources

### Content Quality KPIs
- **Factual accuracy**: Zero provably false statements
- **Speaking time balance**: 45-55% split between hosts
- **Content freshness**: All news <24 hours old
- **Runtime consistency**: 10-15 minutes per episode

### Business KPIs (Future)
- **YouTube monetization**: Achieve 1,000 subscribers + 4,000 watch hours
- **Engagement rate**: >5% average across videos
- **Revenue target**: $500-$5,000/month within 6 months
- **Content velocity**: Daily uploads with <10 minutes manual intervention

## Implementation Priority

### Phase 1: Quality Excellence (CURRENT FOCUS) 🎯
**Priority**: Achieve consistent, high-quality output before deployment

1. **Content Quality Controls**
   - Phrase repetition detection (>3 words max twice per episode)
   - Stock terminology limits (e.g., "earnings per share" max 3x)
   - Smooth transition validation
   - Quality scoring system improvements

2. **Advanced Script Features**
   - Natural speaking patterns with appropriate pauses
   - Varied transition phrases between segments
   - Logical stock connections (sector trends, opposing moves)
   - Enhanced host personality distinctions
   - Occasional appropriate humor from Marcus

3. **Enhanced Data Collection**
   - Complete technical indicators integration (RSI, MACD)
   - Multi-source validation for moves >5%
   - Sector/industry context integration
   - 24-hour news recency enforcement

4. **Quality Validation & Testing**
   - Comprehensive quality scoring (target: >90%)
   - Iterative testing and refinement
   - Quality metrics tracking
   - Output consistency validation

**Success Criteria**: Quality score >90%, zero factual errors, consistent professional output

### Phase 2: Architecture Refactoring for Hosted Solution 🏗️
**Priority**: Refactor for cloud deployment after quality is achieved

1. **Code Organization & Modularity**
   - Refactor for cloud-native architecture
   - Environment-based configuration
   - Service-oriented design patterns

2. **Data Management**
   - Database integration for historical data
   - Caching mechanisms for API calls
   - Data persistence and retrieval

3. **Infrastructure & Deployment**
   - Cloud infrastructure setup (AWS/other)
   - Containerization optimization
   - CI/CD pipeline implementation
   - Automated scheduling system

4. **Monitoring & Operations**
   - Comprehensive logging system
   - Health checks and alerting
   - Performance monitoring
   - Error tracking and recovery

**Success Criteria**: Scalable, maintainable architecture ready for production deployment

### Phase 3: Video Production Automation 🎥
**Priority**: Complete automation pipeline

1. Video production automation
2. Technical enhancements and optimization
3. Content expansion features

### Phase 4: Advanced Features & Scaling 🚀
**Priority**: Business growth and advanced capabilities

1. Advanced monetization features
2. Premium content capabilities
3. Enterprise-level features

## Risk Assessment

### High Risk Items
- API rate limits and reliability
- Content accuracy validation
- Host personality consistency
- System uptime during market hours

### Medium Risk Items
- Video production quality
- Content freshness requirements
- Cost management for API usage
- YouTube algorithm compliance

### Low Risk Items
- Basic data collection
- Script generation framework
- Error handling implementation
- Logging and monitoring

## Dependencies

### External Dependencies
- Market data APIs (FMP, Alpha Vantage, Yahoo Finance)
- News APIs (NewsAPI, Biztoc)
- OpenAI API for script generation
- YouTube API for uploads (future)

### Internal Dependencies
- Data collection → Script generation
- Content validation → Video production
- Error handling → System reliability
- Logging → Performance monitoring

## Timeline Considerations

### Immediate (Next 2-4 weeks) - Quality Focus
- **Content Quality Controls**: Implement phrase repetition detection, terminology limits
- **Script Refinement**: Enhance host personalities, natural transitions, logical connections
- **Quality Validation**: Improve quality scoring system, target >90% quality score
- **Iterative Testing**: Generate and review multiple outputs, refine based on feedback
- **Data Quality**: Complete technical indicators, multi-source validation

### Short-term (1-2 months) - Quality Excellence
- **Quality Consistency**: Achieve consistent >90% quality scores across multiple runs
- **Host Personality**: Perfect host personality distinctions and natural speaking patterns
- **Content Standards**: Zero factual errors, professional tone, balanced speaking time
- **Testing Framework**: Comprehensive quality testing and validation

### Medium-term (2-4 months) - Architecture Refactoring
- **Code Refactoring**: Modularize for cloud deployment, service-oriented design
- **Infrastructure Setup**: Cloud provider selection and setup
- **Database Integration**: Historical data storage and caching
- **Deployment Pipeline**: CI/CD setup, containerization, automated scheduling

### Long-term (4-6 months) - Video Production & Scaling
- **Video Production**: ElevenLabs integration, video editing pipeline
- **YouTube Automation**: Upload automation, thumbnail generation
- **Content Expansion**: Weekly wraps, holiday handling
- **Monitoring & Operations**: Production monitoring, alerting, optimization 