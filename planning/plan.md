# Market Voice Project Plan

## Current Status
**Production system validated and .env protection implemented via PR #16 on July 16, 2025**
- System successfully running in production with real API keys
- .env protection mechanisms prevent API key overwrites during all operations
- Full production workflow validated: data collection, script generation, and output creation
- Enhanced news collection system validated with 83.3% quality score
- Script generation requirements loaded dynamically from planning/script_generation_requirements.md

## Active Tasks

### Script Quality Enhancement (NEXT PRIORITY)
- [ ] **Fine-tune script generation quality and content structure**
- [ ] Improve speaking time balance between hosts Marcus and Suzanne
- [ ] Enhance script flow and reduce repetitive phrases
- [ ] Optimize content quality scoring (current: 33.3% needs improvement)
- [ ] Refine host personality differentiation and dialogue quality

### News & Catalyst Enhancement
- [x] **Integrate Finnhub news/sentiment in NewsCollector (phase 2)** - ✅ **COMPLETED**
- [ ] Tune "today" logic for news (time zones, late-night/overnight articles)
- [ ] Enhance catalyst detection (earnings, upgrades, M&A, etc.)
- [ ] Add more news sources or robust fallback for low-news days

### Testing & Automation
- [ ] Analyze and fix any remaining slow or flaky tests
- [ ] Use CI/CD for linting, testing, and deployment (optional for solo dev, but recommended)

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

### .env Protection & Production Validation ✅ **COMPLETED & MERGED (PR #16)** - July 16, 2025
- [x] **Fixed critical .env overwrite issue across all setup scripts**
- [x] Implemented has_real_api_keys() function in setup_ubuntu.sh with backup protection
- [x] Enhanced setup.bat and setup.ps1 with API key protection warnings
- [x] Updated documentation (VM_SETUP_GUIDE.md, SETUP_GUIDE.md) with safer practices
- [x] **Executed successful full production runs with real API keys**
- [x] Verified .env protection works during actual production execution
- [x] Validated complete workflow: data collection, script generation, output creation
- [x] Confirmed API cost tracking ($7.85/month) and budget monitoring
- [x] Generated real market analysis content with OpenAI integration

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
