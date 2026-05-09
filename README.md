# portfolio-insights

02/05/2026

This personal project will be to achieve a few things:

1. Create a framework for determining a location in the credit cycle - expansion, slowdown/peak, tightening and recovery.
2. Based on the findings on the current credit regime, set up an automated rebalancing mechanism in a portfolio of sectoral ETF's.
3. Backtest the rebalancing mechanism and generate performance and risk insights.

A Framework For Understanding Current Credit Conditions

There are a number of indicators that can provide insight into the state of credit conditions. Credit spreads are the most familiar and directly observable, but we can also incorporate default rates, debt issuance trends, CDS pricing, and broader macro-financial variables. The Chicago Fed National Financial Conditions Index (NFCI) provides a useful high-level summary of financial conditions, indicating whether they are loose (negative) or tight (positive) relative to historical averages.

While this will be included as part of the overall indicator set, it will not be the central driver of the framework. This is because it aggregates multiple dimensions of financial conditions into a single measure, limiting interpretability across different types of credit stress (e.g. spread widening versus liquidity tightening). In addition, it tends to smooth and confirm shifts in financial conditions rather than isolate the specific drivers or timing of regime changes. 

More information on NFCI can be found here: https://www.chicagofed.org/research/data/nfci/about

My objective is to distinguish between four distinct macro-credit regimes for portfolio rebalancing, rather than a single continuous measure of financial tightness. So, in addition to NFCI, we'll also use these inputs:

1. High-yield and investment-grade credit option-adjusted spreads.
Credit spreads are a primary market-based indicator of credit conditions. Tighter spreads reflect strong liquidity conditions, low perceived default risk, and elevated risk appetite, while widening spreads indicate deteriorating credit conditions and increased compensation demanded by investors for credit risk. "Option-adjusted" accounts for the fact that some of the corporate bonds considered in the index have embedded options, such as being callable.

2. CPI inflation
Inflation is not a direct measure of credit conditions, but it plays a key role in shaping financial conditions through its impact on real interest rates and central bank policy. It therefore acts as an important macroeconomic input into the credit cycle rather than a direct credit market signal.

3. VIX (equity implied volatility)
The VIX measures implied volatility derived from S&P 500 options, reflecting market expectations of near-term equity risk. Elevated levels are typically associated with risk-off environments and tighter financial conditions, although it is more sensitive to equity market stress than credit-specific dynamics.

4. Default rates
Corporate default rates provide a lagging but fundamental indicator of credit stress. Rising defaults confirm that prior tightening in financial conditions has transmitted into the real economy and corporate balance sheets.

5. Federal funds rate
The federal funds rate is a monetary policy instrument set by the Federal Reserve in response to macroeconomic conditions such as inflation, employment, and financial stability. While it strongly influences credit conditions, it is an endogenous policy response rather than a direct market-based indicator.

6. Yield curve (2-year vs 10-year)
The yield curve captures expectations of monetary policy and long-term economic growth. The 2-year yield is closely linked to expectations of short-term policy rates, while the 10-year yield reflects long-term growth and inflation expectations as well as term premium. Famously, a negative spread between 2Y and 10Y yields is considered a recession signal.
    
These inputs are all achieveable in Python, and to avoid any confusion further down the line, we're going to extend our analysis on monthly data from January 2016 to January 2026. Where data is received daily, we'll resample to a monthly average, and where it is quarterly (possibly for the default rates), we'll be rolling-forward intra-quarter. 

With this, the remaining step is to understand how to combine these factors into a model for credit conditions. As a baseline, we could create a naive model - one that weights all factors equally. This would be my starting point. We'd generate a monthly CCI score, and then the portfolio would rebalance monthly based on that score. As a starting framework for CCI values:

1. -0.5 <= CCI < -0.25 = recovery/loosening credit conditions
2. -0.25 <= CCI < 0 = peaking credit conditions
3. 0 <= CCI < 0.25 = downturn, tightening conditions
4. 0.25 <= CCI <= 0.5 = bottoming, into recovering conditions

My first goal is to set up this simple framework, and then to decide how it should effect portfolio rebalancing. As a note, we'll look to rebalance monthly, but extend to 6 month rebalancing too (based on a 6 month average of CCI). Just some other bits to note for my own memory:

1. Statistical tests
2. PCA
3. Could we see if the CCI has any predictive power on spreads? So, take the CCI(inputs, t), regress against HY/IG spreads only, backtest, see what it comes out with?

04/05/2026

The main task today is to begin. We want to load our data from FREDAPI and yfinance, clean and resample and then produce some plots of the data. This isn't a huge task, but getting it right is key to the rest of the project running smoothly. Producing plots of the data in the first instance is important too, as it allows us to quickly identify any issues with our data process.

I've produced a subplot of the raw data using matplotlib, and immediately, some issues are apparent, hence the importance of plotting:

1. Our OAS data doesn't extend back to 2010. Its bad luck, but it seems FRED started only reporting 3 years back in time for these indices in April 2026. I checked indices.ice.com and found that the indices go all the way back to the 90's. We can actually view this data in grid format back to 2016. My thinking is that the inclusion of OAS's is important for my analysis - its a market-driven indicator of credit stress and underpins a lot of institutional financing decisions. Because of this, I'm going to extract the OAS's manually from indices.ice.com for both indices, starting from 01/06/2016 (ICE only lets you have exactly max 10 years...annoying!) up to 31/12/2025, and then shift the time ranges of the whole project to be between those dates.

2. Our CPI figures are the actual index values - we want rolling 12-month changes, so we'll need to add that into our code.

3. Our loan delinquency rate is skewed towards 2010, which makes sense as its post-GFC. Given in point 1 we're shifting our time dimension forward, I think we'll be able to remove this skew when we start at 2016.

4. Similar point to 3, but the federal funds rate data is skewed towards more recent years. We can makes sense of that as the post-GFC era ushered in a period of ultra-low interest rates. Again, once we switch the time period forward, we should remove these issues.


06/05/2026

To do:
- Shift time period forward to begin at 01/01/2016
- Extract OAS's from ICE, store in an Excel and load to Python. The OAS's we want are from the indices with codes H0A0 (high yield) and C0A0, which FRED usefully includes in the reference code for the API.
- Convert CPI to rolling 12-month figures.
- Convert all other data to be monthly figures, averaging for daily data and rolling intra-quarter for quarterly data.
- Once finalised here, we want to do some standard exploratory data analysis on our cleaned, monthly data.

Extracting the ICE indices has proven very hard on the ICE website. While they show you the data in chart and grid format, they don't let you copy and paste it onto a CSV. Its very annoying, but I guess its to encourage buying their service. 

We have a final workaround though - the wayback machine! I've discovered that the FRED pages with the indices we want were snapped in 2025 such that the latest spreads data we can get for both indices, while mainintaing a lookback to 01/01/2016, is 31/03/2025. Given this, we'll once again shift our data range to fit that...hopefully the last time. I think its important we get this spread data into our analysis though. Once we've completed this, the next phase of the project is to do some standard EDA and make sense of it all.

To recap where we are:

1. We've set out a goal for this project, which is to synthesise a bunch of economic/market data into an indicator for credit stress in the current market/economy. Of course - this is US-oriented data, as its most accessible. There is clear shortfalls to that, as the US economy/market isn't representative of the world economy/market, however a large amount of countries depend highly on the US for credit/capital/savings so its reasonable to assume credit stress in the US implies credit stress mostly elsewhere. We're going to link the values of the indicator to locations in the textbook credit cycle.
2. A key goal here is to use this indicator and its value to rebalance a portfolio of ETF's. Off the top of my head, this will look something like considering small cap vs large cap, growth vs value, bonds vs equities... but we need to read some literature on this.
4. Loaded in the economic/market data from FRED - that includes spreads, which we struggled to get from ICE. We used the waybackmachine to achieve that - pretty creative.

07/05/2026

- Get a handle on the exploratory data analysis, off the top of my head, some key things we'll want to look at:
  1. Correlations between series
  2. Main descriptive statistics; percentiles, standard deviations, averages, skews/kurtosis
  3. Consider how each series is distributed too
  4. May want to decipher whether some series are lagging or leading indicators of eachother......
 
- With the exploratory data analysis, I'll also look to understand and comment on the behaviour of the series and how that linked to events at the time.

- Read literature on credit cycle and implications for portfolio allocation.
- Another idea to note is the frequency of the credit cycle. Of course, our data is over c.10 years: 2016 - 2025. Where does our analysis begin in the credit cycle and how long do credit cycles last? Of course, these questions have no concrete answer. 



08/05/2026

Notes on literature: https://info.loomissayles.com/hubfs/Unlocking%20the%20Credit%20Cycle_2024.pdf

- Factors driving cycle; who is borrowing/spending, financial intermediary balance sheets, risk appetite, profits, incomes and liquidity
  Should we be including some of these factors into my analysis? Relate to bank balance sheets / profits?
- Countries go through different phases of credit cycle at different times  - this creates relative value opportunities. Relative value opps are investment strategies profiting off pricing inconsistencies between related assets (go long / short, market neutral, arbitrage and pairs trading)
- Are companies currently managing their balance sheets to entice equity holders or credit holders? Key question
  a. When savings are high in an economy, borrowing is easier, equity shareholders hold sway on balance sheets - investment spending is favoured and asset prices inflate, more risk-taking
  b. Eventually, excess capacity from investment (thought: AI build out, data centers, excess capacity there?) can lead to weak cashflow, earnings collapse, asset prices fall, savings decline - debt holders hold sway on balance sheets now, as companies look to enforce capital discipline

- So we have a sway of who companies favour between equity holders and debt holders. In risk-taking, high profit time, its the equity-holders, during bad times, its the debt holders (makes sense).
- Tracking global savings rates, we can see how it tracks financial crises - savings peak at zenith of the 2008 boom (equity shareholders favoured), then crashes down during the crisis (debt holders favoured)
- Financial intermediaries are the engine of credit creation - we need data on those. When debt funding conditions are good, they lend, fuel investment spending, high asset prices, and vice versa.
- Financial intermediary balance sheets are procyclical with the credit cycle; they move in step. A boom phase of the credit cycle is of course driven by the choices of financial intermediaries to lend more.
  
- Downturn:
  a. Interest rates rise, recessions in economies (tracking interest rates)
  b. Investors seek safety, especially those with illiquid, risky assets (shift to value, real estate too possibly, utilities, large cap)
  c. Profits/incomes collapse, lending tightens, low debt growth (can we track these somehow?)
  d. Spreads blow out, financial intermediaries shrink balance sheets (credit spreads tracked, but possibly need bank lending stats)
  e. Eventually, interest rates are cut to stimulate growth, and liquidity measures introduced by central bank too, such as QE or possibly swap lines to other countries (tracking interest rates, could we also look at central bank QE/QT, or other measures?)

- Credit Repair:
  a. Companies now seeking to improve balance sheets, so favouring debt holders
  b. Layoffs, cost-cuts, build up cash, cut capex, sell assets (deleveraging)
  c. Credit spreads could begin to tighten, given liqudity is rising and getting high due to investors exiting risky/illiquids in favour of safe havens, liquid assets + central bank measures
  d. Credit spread tightening would support corporate bond returns, so a shift into corporates here could work

- Recovery:
  a. Profits start to increase faster than debt
  b. Credit are tighter and equities begin to outperform
  c. Corporate deleveraging underway
  d. Lending standards ease, central banks ease off, liquidity rises 

- Expansion to Late Cycle
  a. Profits begin to fade, but equities still outperform and shareholders demand high RoE
  b. Interest rates rise, and central banks begin to tighten
  c. Financial intermediary balance sheets expand
  d. May see more innovative liquidity mechanisms, such as derivates, repos (at their heart, they're still methods of borrowing short and lending long, but in more opaque, illiquid ways)

This research from Loomis has given me further insight into the credit cycle and its dynamics. Not only that, it has shown that I should probably be tracking a few more metrics, some thoughts:

1. We're going to change how we track IG and HY spreads. Instead, we'll look at the differential between them and just one spread in the actual model we create. T
   HY > IG always, but the change in that differential could be useful. This differential represents the compensation for taking on the excess credit risk from HY debt. An expansion of that compensation could mean two things:
   HY spreads widen, while IG relatively stable, indicating stress in the riskiest part of the market - early late cycle?
   HY stable, IG compresses, strong balance sheets in best companies - recovery/expansion

   A compression would mean two things too: HY compress, while IG stable, again recovery/expansion. HY stable, while IG widens would mean late cycle / downturn.

2. We need some more data on financial intermediary balance sheets, corporate profits/debt/cash, and possibly some liquidity measures - could be useful to look at M1/2/3/4 in the economy data


09/05/2026

Todo/Thoughts:

1. Construct HY - IG differential as a MoM rate of change, and retain HY spread index
2. Check FRED and find what data we could use related to balance sheets, profits, liquidity etc. We need to bare in mind that some of these indicators may be used in NFCI already - so we wont want to use them twice!
3. I'm thinking to remove the federal funds rate, it probably shouldnt be in my analysis at all. Consider what I'm trying to do here - construct my own indicator of credit conditions in the US economy, and use that (with credit cycle knowledge) to rebalance a long-only ETF portfolio. The federal funds rate is not market driven, its a policy response based on the Feds mandate of stable inflation and high employment. It changes due to different reasons, not solely on credit conditions (it could be supply shocks, as relevant today). Its also not market driven, and can be a response to credit conditions, so its not an indicator of credit conditions per se. It could be useful to include in the analysis, maybe as a binary indicator, whether we're in a rate cutting or rate hiking cycle, but not within the indicator itself. If we look at a value from the indicator at a certain time, we could also consider the regime of interest rates we are in - are the fed raising them or reducing them? (the level doesnt matter). Or, we can cut our CCI readings into regimes - cutting, hiking, stable.

4. Another idea - we could look at some point whether these series are leading/lagging indicators of one another. We can do this using correlation, by lagging one index and then checking the correlation with another non-lagged index. Theres also a test called Granger Causality that is commonly used in econometrics to determine leading/lagging indicators. I'm warned the using the term causality here is dangerous, and that people prefer "predictive causality" as true causality runs into philosophical issues that I'm not qualified enough to discuss.
5. Across all the data I have, there is a clear outlier which is Covid. It caused spikes/collapses in different indices. This is a clear stressed credit scenario thats going to be baked into our model. I'm wondering how to deal with the data for this, because I'm wondering whether it makes sense to rebalance into a stressed credit event such as this - its a kneejerk reaction. We'd be selling into a panicked market, experiencing large mark downs on our ETF's. There'd be no indicator for an event like Covid in any of the financial metrics we have, as it was a shock that nobody saw coming. How do we want to deal with this? We could keep it in, and add logic for rebalancing later down the line to do no rebalancing in these stressed events. It also depends on the amount of rebalancing we want to do.. if its every month, then sure we'll be rebalancing through Covid - seems dangerous - but if its every c.6 months, then the model could choose not to rebalance upon a stress event it detects, then waits 6 months, then rebalances (this works for Covid, which was at its worst from Feb to August 2021). To not have Covid skew out distributional statistics, we'll likely need to Winsorize our data too. These are just some thoughts to dissect later on down the line.

Lets review our cleaned data anyway. Here is what we are using (all eventually resampled to be monthly)

1. High Yield Spread - US Corporates, daily data
2. Investment Grade Spread - US Corporates, daily data 
3. HY-IG Spread Differential - difference between 1) and 2) on daily data, turned into a monthly mean, then MoM % difference
4. CPI 12-Month Rolling Inflation
   a. Monthly data, then a 12 month rolling figure
   b. https://fred.stlouisfed.org/series/CPIAUCSL
   c. Seasonally adjusted, representing purchases of 88% of US population, prices of a wide ranging basket of goods/services
6. M2 12-Month Rolling Growth - monthly data, then a 12 month rolling figure
   a. Monthly data, then a 12 month rolling figure
   b. https://fred.stlouisfed.org/series/M2SL
   c. M1 = paper money and coins + deposits at banks (most liquid, convertible quickly to cash)
   d. M2 = M1 + retail money market funds + IRA's + CD's (<$100,000)
8. 10Y-2Y Treasury Spread
   a. 10 Year - 2 Year treasury yield, daily data
   b. Normally, 2 year < 10 year, as lending money for longer incurs higher interest payments
   c. But, an inversion of this yield curve is generally considered a recessionary warning. If it inverts, this means that the 2 year yield now exceeds the 10 year yield. It can be driven by a number of things - purchases of the 10 year treasury (safe haven), driving down the yield, as people fear a market selloff. The fed could be hiking rates, which increases the 2Y yield more than the 10Y yield. There could be fears about future growth/inflation, which drives the 10Y yield down in expectation of lower future rates.
10. Chicago Fed NFCI
    a. Net Financial Conditions Indicator
12. VIX Volatility Index
13. Delinquency Rate On All Loans
14. Net % of Banks Tightening C&I Lending Standards
15. Net % of Banks Reporting Stronger C&I Loan Demand
16. Commercial & Industrial Loans (MoM Change)
17. Total Business Inventories-to-Sales Ratio         





























