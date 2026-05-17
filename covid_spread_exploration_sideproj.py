from scipy import stats
from scipy.stats import jarque_bera, skew, kurtosis
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import warnings
import pandas as pd
import os
import numpy as np
warnings.filterwarnings("ignore")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

df_monthly = pd.read_csv(
    os.path.join(BASE_DIR, "Data", "df_monthly.csv"),
    index_col=0,
    parse_dates=True
)

# ----------------------------
# Moody's annual default rates by rating category
# Source: Moody's Annual Default Study (various years)
# HY = speculative grade, IG = investment grade
# ----------------------------
default_rates = pd.DataFrame({
    "year": [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "hy_default_rate": [4.74, 3.15, 2.32, 3.37, 8.14, 1.72, 2.40, 4.80, 3.60],
    "ig_default_rate": [0.03, 0.00, 0.05, 0.03, 0.10, 0.00, 0.03, 0.05, 0.04],
}).set_index("year")

# Long-run average recovery rates (Moody's, senior unsecured bonds)
# Source: M&G Report, see Readme 
recovery_rates = {
    "hy_recovery": 0.3,   
    "ig_recovery": 0.4,   
}

# Expected loss = default rate * (1 - recovery rate)
default_rates["hy_expected_loss"] = (default_rates["hy_default_rate"] / 100) * (1 - recovery_rates["hy_recovery"]) * 100
default_rates["ig_expected_loss"] = (default_rates["ig_default_rate"] / 100) * (1 - recovery_rates["ig_recovery"]) * 100
default_rates["expected_loss_differential"] = default_rates["hy_expected_loss"] - default_rates["ig_expected_loss"]

# ----------------------------
# Map annual expected loss to monthly dates for alignment with df_monthly
# ----------------------------
df_monthly.index = pd.to_datetime(df_monthly.index)
default_rates.index = pd.to_datetime(default_rates.index, format="%Y")

# Forward fill annual figures to monthly — each year's figure applies for that full year
monthly_expected_loss = (
    default_rates["expected_loss_differential"]
    .resample("MS")
    .ffill()
    .reindex(
        pd.date_range(start="2016-01-01", end="2025-03-01", freq="MS"),
        method="ffill"
    )
)

# HY-IG Spread
hy_ig_spread = df_monthly["hy_spread"] - df_monthly["ig_spread"]

# ----------------------------
# Plot 1 — HY-IG Spread vs Expected Loss Differential (single axis)
# ----------------------------
fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(hy_ig_spread.index, hy_ig_spread.values,
        color="steelblue", linewidth=1.5, label="HY-IG OAS Differential")
ax.plot(monthly_expected_loss.index, monthly_expected_loss.values,
        color="darkorange", linewidth=1.8, linestyle="--",
        label="HY-IG EL Differential")
ax.fill_between(hy_ig_spread.index,
                hy_ig_spread.values,
                monthly_expected_loss.reindex(hy_ig_spread.index, method="ffill").values,
                alpha=0.15, color="green",
                label="Excess Premium (Non-Default Compensation)")

ax.set_xlabel("Date", fontsize=10)
ax.set_ylabel("Spread / Expected Loss (%)", fontsize=10)
ax.tick_params(axis="x", rotation=30)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9)

plt.title("HY-IG OAS Differential vs HY-IG EL Differential",
          fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "Data", "hy_ig_vs_expected_loss.png"), dpi=150)
plt.show()

# ----------------------------
# Plot 2 — Excess spread over expected loss (unexplained premium)
# ----------------------------
excess_spread = hy_ig_spread - monthly_expected_loss

fig, ax = plt.subplots(figsize=(14, 6))

# Fill positive (HY expensive / over-compensated) vs negative (under-compensated)
ax.plot(excess_spread.index, excess_spread.values,
        color="steelblue", linewidth=1.5, label="HY-IG - EL")
ax.fill_between(excess_spread.index, excess_spread.values, 0,
                where=(excess_spread.values >= 0),
                alpha=0.25, color="green",
                label="HY-IG > EL")
ax.fill_between(excess_spread.index, excess_spread.values, 0,
                where=(excess_spread.values < 0),
                alpha=0.25, color="red",
                label="HY-IG < EL")
ax.axhline(0, color="black", linewidth=0.9, linestyle="--")

# Annotate average
avg = excess_spread.mean()
ax.axhline(avg, color="grey", linewidth=0.9, linestyle=":",
           label=f"Period Average: {avg:.2f}%")

ax.set_xlabel("Date", fontsize=10)
ax.set_ylabel("Excess Spread (%)", fontsize=10)
ax.set_title("HY-IG Spread and Expected Loss Differential",
             fontsize=12, fontweight="bold")
ax.tick_params(axis="x", rotation=30)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "Data", "excess_spread_over_expected_loss.png"), dpi=150)
plt.show()




# ----------------------------
# Covid Implied Default Rate Analysis
# ----------------------------

# --- Step 1: Pre-Covid average HY-IG OAS and EL, compute premium --- #
pre_covid_start = "2016-01-01"
pre_covid_end   = "2019-12-31"

hy_ig_spread_pre_covid = hy_ig_spread.loc[pre_covid_start:pre_covid_end]
monthly_el_pre_covid   = monthly_expected_loss.loc[pre_covid_start:pre_covid_end]

excess_pre_covid     = hy_ig_spread_pre_covid - monthly_el_pre_covid
avg_expected_premium = excess_pre_covid.mean()

print("=" * 60)
print("PRE-COVID AVERAGE EXCESS PREMIUM (2016-2019)")
print("=" * 60)
print(f"Average HY-IG OAS:       {hy_ig_spread_pre_covid.mean():.4f}%")
print(f"Average HY-IG EL:        {monthly_el_pre_covid.mean():.4f}%")
print(f"Average Excess Premium:  {avg_expected_premium:.4f}%")

# --- Step 2: Covid period --- #
covid_start = "2020-01-01"
covid_end   = "2020-12-31"

hy_ig_spread_covid = hy_ig_spread.loc[covid_start:covid_end]

# RHS of equation — what EL investors were pricing during Covid
# EL_implied = HY-IG OAS_covid - avg_expected_premium
el_implied_covid = (hy_ig_spread_covid / 100) - (avg_expected_premium / 100)

print("\n" + "=" * 60)
print("IMPLIED EL INVESTORS WERE PRICING DURING COVID (monthly)")
print("=" * 60)
print((el_implied_covid * 100).round(4).to_string())

# --- Step 3: Recovery rate scenarios --- #
# Range from senior secured (60%) down to junior unsecured (20%)
# centred around 40% assumption +/- 10% and beyond
recovery_rate_scenarios = [0.3, 0.35, 0.40, 0.45, 0.50]

print("\n" + "=" * 60)
print("IMPLIED HY DEFAULT RATE BY RECOVERY RATE SCENARIO")
print("Approximation: IG term dropped (negligible)")
print("=" * 60)
print(f"{'Recovery Rate':<20} {'Avg Implied DR':<20} {'Realised DR':<15} {'Gap (pp)':<10}")
print("-" * 65)

scenario_results = {}

for rr in recovery_rate_scenarios:
    # HY_dr * (1 - RR) = EL_implied  =>  HY_dr = EL_implied / (1 - RR)
    implied_dr = el_implied_covid / (1 - rr) * 100  # back to percent
    avg_implied = implied_dr.mean()
    gap = 8.14 - avg_implied
    scenario_results[rr] = implied_dr
    print(f"{rr*100:.0f}%{'':<17} {avg_implied:.2f}%{'':<16} 8.14%{'':<10} {gap:.2f}pp")

# --- Step 4: Plot — implied default rate across scenarios vs realised --- #
fig, ax = plt.subplots(figsize=(14, 7))

colors = ["#d73027", "#fc8d59", "#steelblue", "#91bfdb", "#4575b4"]
colors = ["#d73027", "#fc8d59", "#74add1", "#4575b4", "#313695"]

for rr, color in zip(recovery_rate_scenarios, colors):
    implied_dr = scenario_results[rr]
    ax.plot(implied_dr.index, implied_dr.values,
            linewidth=1.5, marker="o", markersize=4,
            color=color,
            label=f"RR = {rr*100:.0f}% (Avg implied DR: {implied_dr.mean():.2f}%)")

ax.axhline(8.14, color="black", linewidth=2, linestyle="--",
           label="Realised 2020 HY Default Rate (8.14%)")

ax.set_xlabel("Date", fontsize=10)
ax.set_ylabel("Implied HY Default Rate (%)", fontsize=10)
ax.set_title(
    "Covid Implied HY Default Rate vs Realised (8.14%)\n"
    "Across Recovery Rate Scenarios (20% — 60%)\n"
    "Approximation: IG Expected Loss term dropped",
    fontsize=12, fontweight="bold"
)
ax.tick_params(axis="x", rotation=30)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9, loc="upper right")

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "Data", "covid_implied_default_rate_scenarios.png"), dpi=150)
plt.show()

# --- Step 5: Summary table — monthly implied DR for each scenario --- #
print("\n" + "=" * 60)
print("MONTHLY IMPLIED HY DEFAULT RATES BY SCENARIO (%)")
print("=" * 60)

summary_df = pd.DataFrame(
    {f"RR={int(rr*100)}%": scenario_results[rr].values
     for rr in recovery_rate_scenarios},
    index=hy_ig_spread_covid.index.strftime("%Y-%m")
)
summary_df["Realised"] = 8.14
print(summary_df.round(2).to_string())