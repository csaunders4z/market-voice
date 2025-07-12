# Script Generation Requirements for Market Voices

This document summarizes actionable requirements for the script generation module, based on project planning and quality standards. Please edit or annotate as needed; we will iterate and refine the implementation together.

---

## 1. MVP / MUST HAVE
- **Automated NASDAQ-100 data collection** after market close on weekdays
- **Top 5 winners and bottom 5 losers** identified by price, % change, volume
- **Fallback mechanisms** for data sources
- **Timestamped, fresh data** (current trading day)
- **Two-host script**: Suzanne (Mon/Tue/Thu), Marcus (Wed/Fri)
- **10-15 minute runtime** (10 min Thu/Fri, 15 min other days)
- **Professional financial news tone** (cable TV style)
- **Daily intro/outro** with subscription CTA
- **Factual accuracy**; no provably false info
- **Causal explanations** for stock moves from credible sources (at least one news source per stock, two if >5% move)
- **No obvious AI-generated patterns or repetitive phrases**
- **Company context** (without over-explaining well-known companies)
- **Balanced speaking time** (45-55% split between hosts)
- **Natural transitions** and logical connections between stocks (sector trends, opposing moves)
- **Runtime consistency**: 10-15 minutes per episode

## 2. SHOULD HAVE
- **News integration** for stocks with >2% movement
- **Technical indicators** (RSI >70/<30, MACD crossovers, volume >2x average)
- **Multiple data source validation** for moves >5%
- **Sector/industry context** when relevant
- **Natural speaking patterns, varied transitions**
- **Repetition control**: No exact phrase >3 words appears more than twice per episode
- **Host balance**: No host discusses more than 3 consecutive stocks
- **Conflicting news acknowledgment**: Prefer official sources, use balanced language

## 3. Success Metrics & Quality Standards
- **Data accuracy**: 100% factual correctness
- **Script generation time**: <5 minutes
- **Repetition score**: <2 repeated phrases per episode
- **Host balance**: 45-55% speaking time split
- **Transition smoothness**: <2 seconds silence between segments
- **Professional tone**: 100% compliance
- **Zero tolerance for factual errors**
- **Content freshness**: All news <24 hours old

## 4. Test Design Considerations
- Validate all above requirements with integration and unit tests
- Use cached data for tests to avoid unnecessary API calls
- Test for edge cases: missing data, conflicting news, extreme technical indicators, sector-wide moves
- Ensure output meets length, balance, and quality metrics

---

*Edit this file as needed. Once you have finished, let me know and I will help you update or implement the script generation logic accordingly.*
