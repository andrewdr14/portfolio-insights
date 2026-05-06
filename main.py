import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from fredapi import Fred
import yfinance as yf
import matplotlib.pyplot as plt

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")

if FRED_API_KEY is None:
    raise ValueError("FRED_API_KEY not found. Add it to your .env file.")

fred = Fred(api_key=FRED_API_KEY)

# ----------------------------
# Config
# ----------------------------
start_date = "2016-01-01"
end_date = "2026-01-01"
cpi_start_date = "2015-01-01"  # 12 months early to allow MoM rolling without losing 2016 data

# ----------------------------
# FRED series
# ----------------------------
fred_series = {
    "hy_spread": "BAMLH0A0HYM2",
    "ig_spread": "BAMLC0A0CM",
    "fed_funds": "FEDFUNDS",
    "yield_curve": "T10Y2Y",
    "nfci": "NFCI",
    "default": "DRALACBN"
}

df_fred = pd.DataFrame({
    name: fred.get_series(code, observation_start=start_date, observation_end=end_date)
    for name, code in fred_series.items()
})

# Fetch CPI separately with extended start
cpi_series = fred.get_series("CPIAUCSL", observation_start=cpi_start_date, observation_end=end_date)
df_fred["cpi"] = cpi_series

# ----------------------------
# Market data
# ----------------------------
vix = yf.download("^VIX", start=start_date, end=end_date)["Close"]

# Flatten column index if MultiIndex (yfinance sometimes returns this)
if isinstance(vix, pd.DataFrame):
    vix = vix.squeeze()

df_market = pd.DataFrame({"vix": vix})

# ----------------------------
# Combine all series
# ----------------------------
df_all = df_fred.join(df_market, how="outer")

# ----------------------------
# Plot all time series
# ----------------------------
series_info = {
    "hy_spread": ("High Yield Spread", "Spread (%)"),
    "ig_spread": ("Investment Grade Spread", "Spread (%)"),
    "cpi": ("CPI YoY Inflation", "% Change (YoY)"),
    "fed_funds": ("Federal Funds Rate", "Rate (%)"),
    "yield_curve": ("10Y-2Y Treasury Spread", "Spread (%)"),
    "nfci": ("Chicago Fed NFCI", "Index"),
    "vix": ("VIX Volatility Index", "Index"),
    "default": ("Delinquency Rate On All Loans", "Rate (%)")
}

fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(14, 12))
axes = axes.flatten()

for i, (col, (title, ylabel)) in enumerate(series_info.items()):
    ax = axes[i]
    data = df_all[col].dropna()
    ax.plot(data.index, data.values, linewidth=1.2)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=9)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("time_series_plots_true.png", dpi=150)
plt.show()

# ----------------------------
# Resample all series to monthly
# ----------------------------
df_monthly_raw = pd.DataFrame(index=pd.date_range(start=cpi_start_date, end=end_date, freq='MS'))

for col in df_all.columns:
    series = df_all[col].dropna()
    
    if len(series) < 2:
        continue
    
    gaps = series.index.to_series().diff().dt.days.dropna()
    median_gap = gaps.median()
    
    if median_gap <= 35:
        monthly = series.resample('MS').mean()
    else:
        monthly = series.resample('MS').ffill()
    
    df_monthly_raw[col] = monthly

# Convert CPI to MoM % change then trim to main start_date
df_monthly_raw["cpi"] = df_monthly_raw["cpi"].pct_change(1) * 100

# Final clean monthly dataframe trimmed to your actual study period
df_monthly = df_monthly_raw.loc[start_date:].dropna(how='all')

# ----------------------------
# Plot monthly resampled series
# ----------------------------
fig2, axes2 = plt.subplots(nrows=4, ncols=2, figsize=(14, 12))
axes2 = axes2.flatten()

for i, (col, (title, ylabel)) in enumerate(series_info.items()):
    ax = axes2[i]
    data = df_monthly[col].dropna()
    ax.plot(data.index, data.values, linewidth=1.2)
    ax.set_title(f"{title} (Monthly)", fontsize=11, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=9)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("time_series_plots_monthly.png", dpi=150)
plt.show()