## UX Ideas for Dashboard

### Benchmark Selection
- Before running analysis, show user a summary of their holdings
- Explain what benchmark means in plain language
- Let user choose: S&P 500 (US) or TA-125 (Israel)
- Show brief explanation of WHY a certain benchmark is recommended
  based on their holdings (e.g. if most assets are Israeli → suggest TA-125)
- User must confirm before analysis runs

### ESG Filtering
- Allow user to filter out industries on ideological/ethical grounds
- Categories to exclude: weapons & defense, tobacco, gambling, alcohol
- Known in the industry as "ESG Filtering" (Environmental, Social, Governance)
- When a holding is flagged, show a warning before analysis with explanation
- Option: suggest alternative assets in the same sector but ESG-compliant

### Known Limitations
- Israeli mutual funds (קרנות נאמנות) are not supported via yfinance
  Examples: Meitav, More, Psagot, IBI, Forest funds
- Workaround to explore: Israeli mutual fund data via
  https://maya.tase.co.il or https://funder.co.il APIs
- Future feature: allow manual return input for unsupported assets

### UX Improvements (for Week 3 with Claude Design)
- Auto-focus amount field after selecting asset
- Click to clear amount field (reset to empty instead of 0.00)
- Visual confirmation card per asset after entry
- Press Enter on amount to add next asset row

## Feature Ideas
am i having fun today?
show today's performence and say what percentage of days it's better than

### Build My Portfolio (new feature)
- Separate flow from "Analyze My Portfolio"
- User answers a short questionnaire:
  - How much money do they have to invest
  - Time horizon (short/medium/long term)
  - Risk tolerance (conservative/balanced/aggressive)
  - Any sectors to avoid (ESG preferences)
- Claude API processes answers and returns 3 portfolio recommendations:
  - Conservative, Balanced, Aggressive
  - Each with exact asset tickers and weights
- Each recommendation includes full analysis tables and charts
- "Analyze This Portfolio" button runs the full risk engine on the recommendation
- No new technical infrastructure needed — reuses existing risk metrics and charts