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

I've produced a subplot of the raw data using matplotlib, see below: 

<img width="2100" height="1800" alt="image" src="https://github.com/user-attachments/assets/a2f157ba-93fe-4a72-bb77-bfa9fece0cce" />


And immediately, some issues are apparent, hence the importance of plotting:

1. Our OAS data doesn't extend back to 2010. Its bad luck, but it seems FRED started only reporting 3 years back in time for these indices in April 2026. I checked indices.ice.com and found that the indices go all the way back to the 90's. We can actually view this data in grid format back to 2016. My thinking is that the inclusion of OAS's is important for my analysis - its a market-driven indicator of credit stress and underpins a lot of institutional financing decisions. Because of this, I'm going to extract the OAS's manually from indices.ice.com for both indices, starting from 01/06/2016 (ICE only lets you have exactly max 10 years...annoying!) up to 31/12/2025, and then shift the time ranges of the whole project to be between those dates.

2. Our CPI figures are the actual index values - we want rolling 12-month changes, so we'll need to add that into our code.

3. Our loan delinquency rate is skewed towards 2010, which makes sense as its post-GFC. Given in point 1 we're shifting our time dimension forward, I think we'll be able to remove this skew when we start at 2016.

4. Similar point to 3, but the federal funds rate data is skewed towards more recent years. We can makes sense of that as the post-GFC era ushered in a period of ultra-low interest rates. Again, once we switch the time period forward, we should remove these issues.


06/05/2026

To do:
- Shift time period forward to begin at 01/01/2016
- Extract OAS's from ICE, store in an Excel and load to Python
- Convert CPI to rolling 12-month figures.
- Convert all other data to be monthly figures, averaging for daily data and rolling intra-quarter for quarterly data.











