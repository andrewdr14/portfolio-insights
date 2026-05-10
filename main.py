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
end_date = "2025-03-31"
cpi_start_date = "2015-01-01"  # 12 months early to support 12-month rolling calc without losing 2016 data

# ----------------------------
# Load HY / IG spreads from local txt files
# ----------------------------
def load_spread_txt(filepath):
    df = pd.read_csv(
        filepath,
        sep="\t",
        header=None,
        names=["date", "value"],
        parse_dates=["date"],
        na_values=["."]
    )
    return df.set_index("date")["value"].dropna()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

hy_spread = load_spread_txt(os.path.join(BASE_DIR, "ICE Data", "H0A0.txt"))
ig_spread = load_spread_txt(os.path.join(BASE_DIR, "ICE Data", "C0A0.txt"))

# ----------------------------
# FRED series (CPI/M2 excluded — fetched separately with extended start)
# ----------------------------
fred_series = {
    "yield_curve":     "T10Y2Y",
    "nfci":            "NFCI",
    "default":         "DRALACBN",
    "loan_standards":  "DRTSCILM",
    "loan_demand":     "DRSDCILM",
    "c_and_i_loans":   "TOTCI",
    "inv_sales_ratio": "ISRATIO",
    "household_dsr":      "TDSP"
}

df_fred = pd.DataFrame({
    name: fred.get_series(code, observation_start=start_date, observation_end=end_date)
    for name, code in fred_series.items()
})

# CPI and M2 fetched with extended start for 12-month rolling warmup
df_fred["cpi"]       = fred.get_series("CPIAUCSL", observation_start=cpi_start_date, observation_end=end_date)
df_fred["m2_growth"] = fred.get_series("M2SL",     observation_start=cpi_start_date, observation_end=end_date)

#Fed funds fetched separately, as not a CCI component, but a regime indicator
df_fred["fed_funds"] = fred.get_series("FEDFUNDS",     observation_start=start_date, observation_end=end_date)


# ICE spreads — all constructed on daily data
df_fred["hy_spread"]    = hy_spread
df_fred["ig_spread"]    = ig_spread
df_fred["hy_ig_spread"] = hy_spread - ig_spread

# ----------------------------
# Market data
# ----------------------------
vix = yf.download("^VIX", start=start_date, end=end_date)["Close"]

if isinstance(vix, pd.DataFrame):
    vix = vix.squeeze()

df_market = pd.DataFrame({"vix": vix})

# ----------------------------
# Combine all series
# ----------------------------
df_all = df_fred.join(df_market, how="outer")

# ----------------------------
# Series metadata (used for both plots)
# ----------------------------
series_info = {
    "hy_spread":       ("High Yield Spread (H0A0)",                          "Spread (%)"),
    "ig_spread":       ("Investment Grade Spread (C0A0)",                    "Spread (%)"),
    "hy_ig_spread":    ("HY-IG Spread Differential (MoM Change)",             "% Change (MoM)"),
    "cpi":             ("CPI 12-Month Rolling Inflation",                     "% Change (YoY)"),
    "m2_growth":       ("M2 12-Month Rolling Growth",                         "% Change (YoY)"),
    "yield_curve":     ("10Y-2Y Treasury Spread",                             "Spread (%)"),
    "nfci":            ("Chicago Fed NFCI",                                   "Index"),
    "vix":             ("VIX Volatility Index",                               "Index"),
    "default":         ("Delinquency Rate On All Loans",                      "Rate (%)"),
    "loan_standards":  ("Net % of Banks Tightening C&I Lending Standards",   "Net % of Banks"),
    "loan_demand":     ("Net % of Banks Reporting Stronger C&I Loan Demand", "Net % of Banks"),
    "c_and_i_loans":   ("Commercial & Industrial Loans (MoM Change)",        "% Change (MoM)"),
    "inv_sales_ratio": ("Total Business Inventories-to-Sales Ratio",         "Ratio"),
    "household_dsr":   ("Household Debt-Income Ratio (Mortage + Consumer)",         "Ratio")
}

# ----------------------------
# Plot 1 — raw data (pre-resample, QA purposes)
# ----------------------------
fig1, axes1 = plt.subplots(nrows=5, ncols=3, figsize=(18, 16))
axes1 = axes1.flatten()

for i, (col, (title, ylabel)) in enumerate(series_info.items()):
    ax = axes1[i]
    data = df_all[col].dropna()
    ax.plot(data.index, data.values, linewidth=1.2)
    ax.set_title(f"{title} (Raw)", fontsize=10, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)

axes1[-1].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "Data", "plots_raw.png"), dpi=150)
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

# Convert CPI and M2 to 12-month rolling % change (applied after resampling to monthly)
df_monthly_raw["cpi"]       = df_monthly_raw["cpi"].pct_change(12) * 100
df_monthly_raw["m2_growth"] = df_monthly_raw["m2_growth"].pct_change(12) * 100

# Convert C&I loans and HY-IG spread to MoM % change (applied after resampling to monthly)
df_monthly_raw["c_and_i_loans"] = df_monthly_raw["c_and_i_loans"].pct_change(1) * 100
df_monthly_raw["hy_ig_spread"] = df_monthly_raw["hy_ig_spread"].pct_change(1) * 100


# Trim to study period — drops warmup rows and any all-NaN rows
df_monthly = df_monthly_raw.loc[start_date:].dropna(how='all')

# ----------------------------
# Plot 2 — monthly resampled data
# ----------------------------
fig2, axes2 = plt.subplots(nrows=5, ncols=3, figsize=(18, 16))
axes2 = axes2.flatten()

for i, (col, (title, ylabel)) in enumerate(series_info.items()):
    ax = axes2[i]
    data = df_monthly[col].dropna()
    ax.plot(data.index, data.values, linewidth=1.2)
    ax.set_title(f"{title} (Monthly Avg)", fontsize=10, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)

axes2[-1].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "Data", "plots_monthly.png"), dpi=150)
plt.show()

# ----------------------------
# Rate cycle overlay (sits alongside CCI, not part of it)
# ----------------------------
fed_funds_monthly = df_monthly_raw["fed_funds"].dropna()
fed_funds_chg = fed_funds_monthly.diff()

threshold = 0.05  # 5bps — filters rounding noise

rate_cycle = pd.Series(0, index=fed_funds_monthly.index)
rate_cycle[fed_funds_chg >  threshold] =  1   # hiking
rate_cycle[fed_funds_chg < -threshold] = -1   # cutting

# Forward fill through on-hold months so a pause doesn't break a cycle
rate_cycle = rate_cycle.replace(0, np.nan).ffill().fillna(0).astype(int)

# Trim to study period and attach to df_monthly
df_monthly["rate_cycle"] = rate_cycle.loc[start_date:]

# ----------------------------
# Export monthly data for use in other scripts
# ----------------------------
df_monthly.to_csv(os.path.join(BASE_DIR, "Data", "df_monthly.csv"))

