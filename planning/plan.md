# Market Voice Project Plan

## Current Status
**Production deployment completed and merged via PR #6 on July 15, 2025**
- System is ready for production use with real API keys
- Enhanced news collection system validated with 83.3% quality score
- Script generation requirements loaded dynamically from planning/script_generation_requirements.md

## Active Tasks

### News Analysis Integration Improvements - **HIGH PRIORITY** - July 18, 2025
- [ ] Fix news attachment logic in unified_data_collector.py - ensure news_articles, news_analysis, and news_sources properly populate for top movers
- [ ] Enhance script prompt integration in script_generator.py - modify prompt creation to better utilize attached news data
- [ ] Improve catalyst detection and relevance scoring in news_collector.py - strengthen news relevance scoring and catalyst identification
- [ ] Debug timezone issues in news date filtering - fix _is_today_article and _filter_today_articles methods
- [ ] Add better error handling and fallback mechanisms in get_enhanced_market_news
- [ ] Implement circuit breaker reset logic for news APIs
- [ ] Add comprehensive logging for news attachment debugging
- [ ] Create news collection failure detection test for production monitoring

### News & Catalyst Enhancement
- [x] **Integrate Finnhub news/sentiment in NewsCollector (phase 2)** - ✅ **COMPLETED**
- [x] **Tune "today" logic for news (time zones, late-night/overnight articles)** - ✅ **COMPLETED (PR #17)**
- [x] **Enhance catalyst detection (earnings, upgrades, M&A, etc.)** - ✅ **COMPLETED (PR #18)**
- [ ] Add more news sources or robust fallback for low-news days

### Testing & Automation
- [ ] Analyze and fix any remaining slow or flaky tests
- [ ] Add test to detect news collection failure: When multiple stocks (>3 out of top 10 movers) have empty news_articles arrays or only fallback news summaries, flag as news collection system failure requiring investigation
- [ ] Use CI/CD for linting, testing, and deployment(optional for solo dev, but recommended)

### Deployment & Monitoring
- [ ] Monitor logs and outputs for errors or regressions

### Cleanup & Maintenance
- [ ] Periodically review code for architectural drift and refactor as needed
- [ ] Maintain clear, concise documentation for all new modules and major changes
- [ ] Continue to enforce efficiency principle: only fetch news for top/bottom 10 stocks, not all symbols
- [ ] Scaffold Finnhub alternative data in DeepAnalysisModule/ScreeningModule (phase 3)

## System Notes
- Script generation requirements are editable by the user and changes are reflected without code changes
- If the requirements file is missing/unreadable, the script falls back to built-in requirements
- Script generation requirements and quality standards are documented in planning/project-requirements.md and planning/quality-standards.md
- Must/Should/Could features, success metrics, and test design factors are outlined in project-requirements.md and project-overview.md
- User will manually edit the generated requirements markdown file and iterate on script generation logic with the assistant
- Production script generation logic loads and applies requirements from the external markdown file at runtime

---

## Completed Tasks

### Enhanced Catalyst Detection ✅ **COMPLETED (PR #18)** - July 18, 2025
- [x] Enhanced NewsCollector._identify_news_catalysts() with 10 comprehensive catalyst categories
- [x] Added confidence scoring system (title matches: 2 points, description matches: 1 point)
- [x] Implemented individual article classification with _identify_article_catalyst() method
- [x] Updated all 5 NewsArticle creation points to populate catalyst_type field
- [x] Enhanced relevance scoring with tiered keyword system (high/medium/low impact)
- [x] Added catalyst bonus (+1.0) to relevance scoring for articles with identified catalysts
- [x] Created comprehensive test script achieving 100% accuracy on 10 catalyst types
- [x] Covers all requested catalyst types: earnings, upgrades, M&A, regulatory approvals, etc.
- [x] Improved pattern matching beyond simple keyword detection with weighted scoring

### News Timezone Handling ✅ **COMPLETED (PR #17)** - July 18, 2025
- [x] Fixed timezone handling in news collection system to use US/Eastern consistently
- [x] Updated API calls to use market timezone for date parameters instead of server time
- [x] Fixed `_is_today_article()` methods across all news collectors to use market timezone
- [x] Enhanced date parsing to handle timezone-naive dates by assuming UTC then converting to market timezone
- [x] Ensured consistent "today" logic regardless of server timezone location
- [x] Applied timezone fixes to: NewsCollector, StockNewsScraper, FreeNewsCollector, FinnhubNewsAdapter
- [x] Addresses late-night/overnight article collection issues mentioned in plan

### Finnhub Integration Phase 2 ✅ **COMPLETED & MERGED (PR #14)** - July 16, 2025
- [x] Implemented comprehensive news collection with sentiment analysis from Finnhub
- [x] Added .env protection safeguards to prevent API key overwrites during deployment
- [x] Created comprehensive testing suite with 4/4 tests passing
- [x] Fixed deploy.sh Python version check (was rejecting Python 3.12)
- [x] Validated deploy.sh functionality with .env protection - all safeguards working correctly
- [x] Added backup/restore utilities for .env files
- [x] Enhanced NewsCollector with get_comprehensive_company_news and sentiment integration

### Production Deployment ✅ **COMPLETED & MERGED (PR #6)**
- [x] Deploy system to production environment
- [x] Create production API key configuration guide
- [x] Implement production validation script
- [x] Fix system issues preventing production deployment
- [x] Document production setup process
- [x] Execute first production script generation (validated with placeholder keys)
- [x] Monitor system performance and API costs in production
- [x] Implement cost optimization (GPT-3.5-turbo switch)
- [x] Set up automated monitoring and alerting

### Requirements & Documentation
- [x] Review requirements for script generation and evaluate test design
- [x] Review script generation requirements and quality standards in planning docs
- [x] Summarize/document script generation requirements for implementation
- [x] Create requirements markdown file for user editing and iteration
- [x] Update production script generation logic to load/apply requirements from markdown file

### System Preparation
- [x] Remove test mode and prepare for production deployment
- [x] Remove TEST_MODE environment variable checks from settings.py
- [x] Remove _generate_mock_script method from script_generator.py
- [x] Update data collection to always use production mode
- [x] Verify production workflow with real API calls

### News Collection Enhancement
- [x] Enhance news collector with comprehensive fallback system
- [x] Attach company-specific and market context news to each stock for script generation
- [x] Always collect price change data for ALL S&P 500 and NASDAQ-100 stocks before script generation

### Testing Infrastructure
- [x] Add mocks for slow/external calls in tests
- [x] Use pytest-timeout to prevent hanging tests
- [x] Add mock pytest fixtures for `symbols` and `market_data` (NASDAQ-100, S&P-500)
- [x] Track orphaned/legacy files for later review
- [x] Consolidate and deduplicate all test files; maintain only one source of truth
- [x] Review and maintain efficient, realistic test coverage

### Deployment Infrastructure
- [x] Use/maintain deploy.sh and PRODUCTION_DEPLOYMENT_GUIDE.md for production runs
- [x] Periodically review flagged orphaned/legacy files for removal or integration
- [x] Remove or archive unused scripts and data

### Deliverables Created
- `PRODUCTION_SETUP.md` - Complete production setup guide
- `validate_production.py` - Pre-deployment validation script
- `production_deploy.py` - Automated deployment with systemd service
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step deployment checklist
- `README_PRODUCTION.md` - Quick start guide for production
