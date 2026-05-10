# ----------------------------
# Exploratory Data Analysis — Monthly Resampled Data
# ----------------------------
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

series_info = {
    "hy_spread":   ("High Yield Spread (H0A0)",      "Spread (%)"),
    "ig_spread":   ("Investment Grade Spread (C0A0)", "Spread (%)"),
    "cpi":         ("CPI MoM Inflation",              "% Change (MoM)"),
    "fed_funds":   ("Federal Funds Rate",             "Rate (%)"),
    "yield_curve": ("10Y-2Y Treasury Spread",         "Spread (%)"),
    "nfci":        ("Chicago Fed NFCI",               "Index"),
    "vix":         ("VIX Volatility Index",           "Index"),
    "default":     ("Delinquency Rate On All Loans",  "Rate (%)")
}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

df_monthly = pd.read_csv(
    os.path.join(BASE_DIR, "Data", "df_monthly.csv"),
    index_col=0,
    parse_dates=True
)

# ----------------------------
# 1. Descriptive Statistics
# ----------------------------
print("=" * 70)
print("DESCRIPTIVE STATISTICS")
print("=" * 70)

desc = df_monthly.describe().T
desc["skewness"] = df_monthly.skew()
desc["kurtosis"] = df_monthly.kurtosis()

# Jarque-Bera normality test
jb_stats, jb_pvals = [], []
for col in df_monthly.columns:
    series = df_monthly[col].dropna()
    jb_stat, jb_p = jarque_bera(series)
    jb_stats.append(round(jb_stat, 2))
    jb_pvals.append(round(jb_p, 4))

desc["JB stat"]  = jb_stats
desc["JB p-val"] = jb_pvals
desc["normal?"]  = ["Yes" if p > 0.05 else "No" for p in jb_pvals]

print(desc.to_string())

# ----------------------------
# 2. Correlation Matrix (Pearson)
# ----------------------------
print("\n" + "=" * 70)
print("PEARSON CORRELATION MATRIX")
print("=" * 70)
corr_pearson = df_monthly.corr(method="pearson")
print(corr_pearson.round(2).to_string())

# ----------------------------
# 3. Correlation Matrix (Spearman — rank-based, less sensitive to outliers)
# ----------------------------
print("\n" + "=" * 70)
print("SPEARMAN CORRELATION MATRIX")
print("=" * 70)
corr_spearman = df_monthly.corr(method="spearman")
print(corr_spearman.round(2).to_string())

# ----------------------------
# 4. Rolling 12-month correlations vs HY Spread (key stress indicator)
# ----------------------------
print("\n" + "=" * 70)
print("ROLLING 12M CORRELATION vs HY SPREAD — LATEST VALUES")
print("=" * 70)
rolling_corr = df_monthly.rolling(12).corr(df_monthly["hy_spread"]).dropna()
print(rolling_corr.drop(columns="hy_spread").iloc[-1].round(2).to_string())

# ----------------------------
# 5. Regime Analysis — split by VIX level (stress vs calm)
# ----------------------------
print("\n" + "=" * 70)
print("REGIME ANALYSIS — HIGH STRESS (VIX > 25) vs CALM (VIX <= 25)")
print("=" * 70)
high_stress = df_monthly[df_monthly["vix"] > 25]
calm        = df_monthly[df_monthly["vix"] <= 25]

regime_df = pd.DataFrame({
    "Calm Mean":        calm.mean().round(2),
    "Stress Mean":      high_stress.mean().round(2),
    "Calm Std":         calm.std().round(2),
    "Stress Std":       high_stress.std().round(2),
    "Calm Periods":     calm.count(),
    "Stress Periods":   high_stress.count(),
}).T
print(regime_df.to_string())

# ----------------------------
# 6. Percentile ranks — where are we now vs history?
# ----------------------------
print("\n" + "=" * 70)
print("CURRENT PERCENTILE RANKS (latest observation vs full history)")
print("=" * 70)
latest = df_monthly.iloc[-1]
pct_ranks = pd.DataFrame({
    "Latest Value":    latest.round(2),
    "Percentile Rank": [round(stats.percentileofscore(df_monthly[col].dropna(), latest[col]), 1)
                        if not pd.isna(latest[col]) else np.nan
                        for col in df_monthly.columns]
}, index=df_monthly.columns)
print(pct_ranks.to_string())

# ----------------------------
# 7. Peak / Trough analysis
# ----------------------------
print("\n" + "=" * 70)
print("PEAK / TROUGH ANALYSIS")
print("=" * 70)
pt = pd.DataFrame({
    "Max Value":  df_monthly.max().round(2),
    "Max Date":   df_monthly.idxmax().dt.strftime("%Y-%m"),
    "Min Value":  df_monthly.min().round(2),
    "Min Date":   df_monthly.idxmin().dt.strftime("%Y-%m"),
    "Range":      (df_monthly.max() - df_monthly.min()).round(2),
})
print(pt.to_string())

# ----------------------------
# 8. Pairwise t-tests — stress vs calm means (are they statistically different?)
# ----------------------------
print("\n" + "=" * 70)
print("T-TESTS — STRESS vs CALM MEANS (p < 0.05 = significantly different)")
print("=" * 70)
ttest_results = []
for col in df_monthly.columns:
    s1 = high_stress[col].dropna()
    s2 = calm[col].dropna()
    if len(s1) > 1 and len(s2) > 1:
        t_stat, p_val = stats.ttest_ind(s1, s2)
        ttest_results.append({
            "Series":      col,
            "T-Stat":      round(t_stat, 2),
            "P-Value":     round(p_val, 4),
            "Significant": "Yes" if p_val < 0.05 else "No"
        })
print(pd.DataFrame(ttest_results).set_index("Series").to_string())


# ============================================================
# PLOTS
# ============================================================

# ----------------------------
# Plot A — Correlation heatmaps (Pearson + Spearman side by side)
# ----------------------------
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

for ax, corr_mat, title in zip(
    axes,
    [corr_pearson, corr_spearman],
    ["Pearson Correlation", "Spearman Correlation"]
):
    sns.heatmap(
        corr_mat, annot=True, fmt=".2f", cmap="RdYlGn",
        center=0, vmin=-1, vmax=1,
        linewidths=0.5, ax=ax, annot_kws={"size": 9}
    )
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)

plt.tight_layout()
plt.show()

# ----------------------------
# Plot B — Distribution plots (histogram + KDE) for each series
# ----------------------------
fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(14, 14))
axes = axes.flatten()

for i, (col, (title, ylabel)) in enumerate(series_info.items()):
    if col not in df_monthly.columns:
        continue
    ax = axes[i]
    data = df_monthly[col].dropna()
    
    ax.hist(data, bins=30, density=True, alpha=0.4, color="steelblue", edgecolor="white")
    
    # KDE manually via scipy to avoid it creating a new figure
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(data)
    x_range = np.linspace(data.min(), data.max(), 200)
    ax.plot(x_range, kde(x_range), color="steelblue", linewidth=1.8)
    
    ax.axvline(data.mean(),   color="red",    linestyle="--", linewidth=1.2, label=f"Mean: {data.mean():.2f}")
    ax.axvline(data.median(), color="orange", linestyle="--", linewidth=1.2, label=f"Median: {data.median():.2f}")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel(ylabel, fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# ----------------------------
# Plot C — Rolling 12m correlations vs HY spread over time
# ----------------------------
rolling_corr_hy = df_monthly.drop(columns="hy_spread").rolling(12).corr(df_monthly["hy_spread"])

fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(14, 12))
axes = axes.flatten()

for i, col in enumerate([c for c in df_monthly.columns if c != "hy_spread"]):
    ax = axes[i]
    rolling_corr_hy[col].plot(ax=ax, linewidth=1.2, color="steelblue")
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.axhline(0.5,  color="green", linewidth=0.6, linestyle=":", alpha=0.7)
    ax.axhline(-0.5, color="red",   linewidth=0.6, linestyle=":", alpha=0.7)
    ax.set_title(f"Rolling 12m Corr: HY Spread vs {series_info[col][0]}", fontsize=10, fontweight="bold")
    ax.set_ylabel("Correlation", fontsize=9)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-1, 1)

# Hide unused subplot
axes[-1].set_visible(False)

plt.tight_layout()
plt.show()

# ----------------------------
# Plot D — Percentile rank bar chart (current positioning vs history)
# ----------------------------
fig, ax = plt.subplots(figsize=(12, 5))

pct_ranks_clean = pct_ranks["Percentile Rank"].dropna()
colors = ["red" if v > 75 else "green" if v < 25 else "steelblue" for v in pct_ranks_clean]

bars = ax.barh(pct_ranks_clean.index, pct_ranks_clean.values, color=colors, edgecolor="white", height=0.6)
ax.axvline(50,  color="black", linewidth=1,   linestyle="--", alpha=0.5, label="50th percentile")
ax.axvline(75,  color="red",   linewidth=0.8, linestyle=":",  alpha=0.5, label="75th percentile")
ax.axvline(25,  color="green", linewidth=0.8, linestyle=":",  alpha=0.5, label="25th percentile")

for bar, val in zip(bars, pct_ranks_clean.values):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
            f"{val:.0f}th", va="center", fontsize=9)

ax.set_xlabel("Percentile Rank", fontsize=10)
ax.set_title("Current Percentile Rank vs Full History (red = elevated, green = depressed)", 
             fontsize=12, fontweight="bold")
ax.set_xlim(0, 110)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, axis="x")

plt.tight_layout()
plt.show()

# ----------------------------
# Plot E — Scatter matrix (pairplot) for key stress indicators
# ----------------------------
stress_cols = ["hy_spread", "ig_spread", "vix", "nfci", "yield_curve"]
pair_data = df_monthly[stress_cols].dropna()

fig, axes = plt.subplots(len(stress_cols), len(stress_cols), figsize=(14, 14))

for i, col_y in enumerate(stress_cols):
    for j, col_x in enumerate(stress_cols):
        ax = axes[i][j]
        if i == j:
            pair_data[col_x].plot.kde(ax=ax, color="steelblue")
            ax.set_title(col_x, fontsize=8, fontweight="bold")
        else:
            ax.scatter(pair_data[col_x], pair_data[col_y], alpha=0.4, s=15, color="steelblue")
            m, b, r, p, _ = stats.linregress(pair_data[col_x], pair_data[col_y])
            x_line = np.linspace(pair_data[col_x].min(), pair_data[col_x].max(), 100)
            ax.plot(x_line, m * x_line + b, color="red", linewidth=1, alpha=0.7)
            ax.text(0.05, 0.88, f"r={r:.2f}", transform=ax.transAxes, fontsize=7, color="red")
        ax.tick_params(labelsize=6)
        if j == 0:
            ax.set_ylabel(col_y, fontsize=7)
        if i == len(stress_cols) - 1:
            ax.set_xlabel(col_x, fontsize=7)

plt.suptitle("Scatter Matrix — Key Stress Indicators", fontsize=13, fontweight="bold", y=1.01)
plt.tight_layout()
plt.show()
