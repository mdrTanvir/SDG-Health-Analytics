# Global Health Analytics

An analysis of maternal mortality and life expectancy using the [Sustainable Development Report 2026](https://dashboards.sdgindex.org/downloads/) historical dataset.

## Notebooks

| Notebook | Purpose |
|---|---|
| `Clustering_Analysis.ipynb` | Groups 208 countries by their current health outcomes and recent trajectories. |
| `Health_Prediction.ipynb` | Tests short-horizon forecast methods using a time-aware, per-country holdout. |

Both notebooks download the official SDR 2026 workbook when first run; the source workbook is deliberately not committed to this repository.

## What changed in the 2026 refresh

- Replaced the SDR 2024 source with the current SDR 2026 historical release (2000–2025).
- Updated country names and source columns to the current `All Raw Data` sheet.
- Improved clustering inputs by combining latest maternal mortality, life expectancy, and recent trends. Maternal mortality is log-transformed before standardisation to limit the influence of very large values.
- Compared K-Means with Ward hierarchical clustering using silhouette score. K-Means is selected (0.393 vs 0.381).
- Replaced the random train/test split in the forecasting notebook with a realistic out-of-time holdout: each country's final observed value is withheld.
- Benchmarked persistence, recent linear trend, and full-history linear trend models. Persistence is selected for one-step estimates because it has the lowest held-out error for both indicators.

## Key findings

The clustering analysis identifies three interpretable patterns:

1. **Highest pressure** — high maternal mortality and lower life expectancy.
2. **Transitioning outcomes** — middle-range outcomes with mixed progress.
3. **Strong health outcomes** — low maternal mortality and higher life expectancy.

Forecasting results should be read as short-horizon planning estimates, not clinical predictions. The model-selection step is intentionally conservative: a simple last-observation forecast beats the linear-trend alternatives on the latest withheld observations.

## Run locally

```bash
pip install -r requirements.txt
jupyter notebook
```

Open either notebook and run all cells. `refresh_notebooks.py` is included to rebuild and execute both notebooks after an SDR data refresh.

## Tools

Python · Pandas · Scikit-learn · Matplotlib · Seaborn · SciPy · Jupyter
