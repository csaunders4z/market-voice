# Market Voices Production Fixes Plan

**Updated:** July 15, 2025  
**Status:** Ready for implementation  
**Priority:** Immediate fixes for production blockers  

## User Requirements (Logged from Session)

### Critical Requirements
1. **Script Phrase Repetition**: "It is critical for the script to have no repeated phrases"
   - Current issue: "No 4-word phrase should appear more than twice" validation failed
   - User open to suggestions on detection and mitigation
   - **Priority**: BLOCKING - Must be fixed before production

2. **API Rate Limiting**: User "open to suggestions on API rate limiting strategies"
   - Current issue: 100+ Finnhub 422 "Unprocessable Entity" errors during 516-symbol collection
   - System works for 50 symbols but fails at production scale
   - **Priority**: BLOCKING - Prevents reliable data collection

3. **Focus**: "please focus on immediate fixes" rather than comprehensive analysis

## Immediate Fix Plan

### Phase 1: Script Phrase Repetition (Critical)
**Problem**: Script generation completes but fails final validation due to repeated phrases

**Solutions to Implement**:
1. **Enhanced Detection Logic**
   - Improve current "No 4-word phrase should appear more than twice" validation
   - Add detection for 3-word and 5-word phrases as well
   - Implement case-insensitive matching

2. **Pre-Generation Prevention**
   - Add explicit OpenAI prompt instructions to avoid repetition
   - Include examples of what constitutes repetitive phrasing
   - Request varied sentence structures

3. **Post-Processing Mitigation**
   - Implement automatic phrase replacement for detected repetitions
   - Add synonym substitution for repeated phrases
   - Trigger re-generation if repetition threshold exceeded

4. **Testing Strategy**
   - Create test cases with known repetitive content
   - Validate detection accuracy before deployment
   - Test mitigation strategies effectiveness

### Phase 2: API Rate Limiting Strategy (Critical)
**Problem**: Finnhub API fails with 100+ 422 errors during production workflow

**Solutions to Implement**:
1. **Intelligent Batching**
   - Reduce batch sizes from current levels
   - Implement dynamic batch sizing based on API response times
   - Add per-API batch size configuration

2. **Rate Limiting & Delays**
   - Implement exponential backoff between API calls
   - Add configurable delays per API provider
   - Respect documented rate limits for each service

3. **Data Source Prioritization**
   - Use Yahoo Finance for bulk data collection (proven reliable)
   - Reserve premium APIs (Finnhub, FMP) for specific analysis
   - Implement smart fallback ordering

4. **Circuit Breaker Enhancement**
   - Add automatic re-enabling after cooldown periods
   - Implement gradual recovery (start with smaller requests)
   - Add monitoring for API health status

### Phase 3: News API Optimization (Performance)
**Problem**: NewsAPI 401 errors under concurrent load despite real API keys

**Solutions to Implement**:
1. **Authentication Optimization**
   - Implement request queuing for news APIs
   - Add retry logic with authentication refresh
   - Optimize concurrent request handling

2. **Fallback Strategy**
   - Prioritize working news sources
   - Implement graceful degradation for news coverage
   - Add RSS feed fallbacks for critical news

### Phase 4: Monitoring & Recovery (Reliability)
**Solutions to Implement**:
1. **Real-time Monitoring**
   - Add alerts for API failures and rate limiting
   - Implement dashboard for production workflow health
   - Track success rates per API provider

2. **Automatic Recovery**
   - Add self-healing mechanisms for failed APIs
   - Implement automatic workflow restart on failure
   - Add data quality validation checkpoints

## Implementation Strategy

### Testing Approach
1. **Tight Testing Loops**: Test individual fixes in isolation before integration
2. **Production Simulation**: Test with full 516-symbol dataset
3. **Error Reproduction**: Create test cases that reproduce current failures
4. **Validation**: Ensure fixes don't break existing functionality

### Git Strategy
1. **Branch**: Create `devin/{timestamp}-production-fixes` branch
2. **Commits**: Separate commits for each fix category
3. **Testing**: Validate each fix before moving to next phase
4. **PR**: Single PR with all immediate fixes

### Success Criteria
1. **Script Generation**: No phrase repetition validation failures
2. **Data Collection**: 516 symbols processed without API circuit breaker triggering
3. **News Integration**: Reduced authentication errors under load
4. **End-to-End**: Complete production workflow succeeds without critical errors

## Next Session Actions
1. Implement Phase 1 (Script phrase repetition fixes)
2. Implement Phase 2 (API rate limiting strategy)
3. Test fixes with production workflow
4. Deploy and validate improvements

---

*Plan updated based on user feedback prioritizing immediate fixes for production blockers.*
