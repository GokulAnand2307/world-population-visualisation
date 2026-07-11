"""Create a compact visual report from a World Bank indicator export."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def load_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path).rename(columns={"Series Name": "Series", "Country Name": "Country"})
    data = data.dropna(subset=["Country", "Series"]).copy()
    year_columns = [column for column in data if "[YR" in column]
    rename = {column: column.split()[0] for column in year_columns}
    data = data.rename(columns=rename)
    for year in rename.values():
        data[year] = pd.to_numeric(data[year], errors="coerce")
    return data


def select_years(data: pd.DataFrame) -> list[str]:
    years = sorted([column for column in data if column.isdigit()])
    return years[-5:]


def create_dashboard(data: pd.DataFrame, output: Path) -> None:
    years = select_years(data)
    latest = years[-1]
    urban_name = "Urban population growth (annual %)"
    city_name = "Population in the largest city (% of urban population)"
    rural_name = "Rural population"

    sns.set_theme(style="whitegrid")
    figure, axes = plt.subplots(2, 2, figsize=(14, 10))

    urban = data[data["Series"] == urban_name].melt(
        id_vars="Country", value_vars=years, var_name="Year", value_name="Growth"
    ).dropna()
    sns.lineplot(data=urban, x="Year", y="Growth", hue="Country", marker="o", ax=axes[0, 0])
    axes[0, 0].set_title("Urban population growth")
    axes[0, 0].set_ylabel("Annual growth (%)")

    city = data[data["Series"] == city_name].dropna(subset=[latest]).nlargest(8, latest)
    sns.barplot(data=city, y="Country", x=latest, hue="Country", legend=False, ax=axes[0, 1])
    axes[0, 1].set_title(f"Largest-city share of urban population ({latest})")
    axes[0, 1].set_xlabel("Share (%)")

    rural = data[data["Series"] == rural_name].dropna(subset=[latest]).copy()
    rural["Rural population (millions)"] = rural[latest] / 1_000_000
    sns.barplot(data=rural.nlargest(8, "Rural population (millions)"), y="Country", x="Rural population (millions)", hue="Country", legend=False, ax=axes[1, 0])
    axes[1, 0].set_title(f"Largest rural populations ({latest})")

    pivot = data.pivot_table(index="Country", columns="Series", values=latest)
    missing = pivot.isna().mean().sort_values().head(5).index
    sns.heatmap(pivot[missing].corr(), annot=True, cmap="vlag", center=0, fmt=".2f", ax=axes[1, 1])
    axes[1, 1].set_title(f"Indicator correlations ({latest})")
    axes[1, 1].tick_params(axis="x", rotation=35)

    figure.suptitle("World Population and Urbanisation", fontsize=20, fontweight="bold")
    figure.tight_layout()
    figure.savefig(output / "population_dashboard.svg", bbox_inches="tight")
    plt.close(figure)

    corr_figure, corr_axis = plt.subplots(figsize=(10, 7))
    sns.heatmap(pivot[missing].corr(), annot=True, cmap="vlag", center=0, fmt=".2f", ax=corr_axis)
    corr_axis.set_title(f"World Bank indicator correlation — {latest}")
    corr_axis.tick_params(axis="x", rotation=35)
    corr_figure.tight_layout()
    corr_figure.savefig(output / "indicator_correlation.svg", bbox_inches="tight")
    plt.close(corr_figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    create_dashboard(load_data(args.data), args.output)


if __name__ == "__main__":
    main()

