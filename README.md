# SDG Health Analytics

Technical analysis of global maternal mortality and life expectancy using the Sustainable Development Report (SDR) 2026 historical dataset. The repository contains two executed Jupyter notebooks: one for descriptive country clustering and one for short-horizon forecasting model selection.

The analysis is designed to be reproducible and methodologically conservative. It distinguishes descriptive patterns from causal conclusions, and evaluates forecast candidates using observations that occur after their training data.

## Objectives

1. Identify interpretable groups of countries with similar health outcomes and recent trajectories.
2. Compare simple forecasting baselines for maternal mortality and life expectancy using time-aware validation.
3. Provide a transparent, rerunnable workflow based on an official public data source.

## Data

**Source:** [Sustainable Development Report data download](https://dashboards.sdgindex.org/downloads/)

The notebooks download the SDR 2026 workbook from the official dashboard when needed:

```text
https://dashboards.sdgindex.org/static/downloads/database_2026.xlsx
```

The workflow reads the `All Raw Data` worksheet and uses:

| SDR field | Meaning | Why it is used |
|---|---|---|
| `country` | Country identifier | Defines the unit of analysis and time series. |
| `year` | Observation year | Enables trend features and time-aware validation. |
| `sdg3_matmort` | Maternal mortality ratio | Captures a severe, policy-relevant health outcome. |
| `sdg3_lifee` | Life expectancy at birth | Provides a broad complementary measure of population health. |

For clustering, the analysis uses the 2000–2025 panel and fills internal gaps within each country series with interpolation followed by forward/back filling. This keeps the feature matrix complete while preserving each country's temporal ordering.

## Repository layout

| File | Role |
|---|---|
| [`Clustering_Analysis.ipynb`](./Clustering_Analysis.ipynb) | Builds country features, compares clustering algorithms, and interprets the resulting groups. |
| [`Health_Prediction.ipynb`](./Health_Prediction.ipynb) | Benchmarks one-step forecast methods with a per-country temporal holdout. |
| [`refresh_notebooks.py`](./refresh_notebooks.py) | Regenerates and executes both notebooks from reproducible source cells. |
| [`requirements.txt`](./requirements.txt) | Core analysis dependencies. |

## Technical stack

| Tool | Used for | Why it is appropriate |
|---|---|---|
| Python | Analysis environment | Widely supported scientific-computing ecosystem and notebook workflow. |
| Pandas | Workbook ingestion and panel reshaping | Efficient tabular operations, grouped time-series handling, and Excel support. |
| NumPy | Numerical transformations | Supports stable vectorised feature construction, including log transforms. |
| Scikit-learn | Scaling, clustering, regression, and metrics | Provides standard implementations of K-Means, Ward clustering, linear regression, silhouette score, MAE, and R². |
| SciPy | Scientific-computing dependency | Supports the broader analysis ecosystem and statistical utilities. |
| Matplotlib + Seaborn | Diagnostic and explanatory charts | Used to visualise country patterns and cluster separation. |
| OpenPyXL | Excel workbook reading | Enables Pandas to read the SDR `.xlsx` source. |
| Jupyter | Executable research narrative | Keeps data preparation, method, outputs, and interpretation together. |
| `nbformat` + `nbclient` | Notebook regeneration | Used by `refresh_notebooks.py` to construct and execute notebooks programmatically. |

## Clustering workflow

### 1. Country-level features

Each eligible country needs at least 15 observations overall and six observations from 2015 onward. The workflow calculates:

- latest maternal mortality ratio;
- latest life expectancy;
- annual maternal-mortality slope from a linear regression over 2015 onward;
- annual life-expectancy slope from the same recent period.

Maternal mortality is transformed with `log1p` before scaling. Maternal mortality has a long right tail, so the log transform prevents very high values from dominating the distance calculation while retaining the ordering of countries. Trend magnitudes for maternal mortality are also log-compressed with their direction preserved.

### 2. Standardisation

All features are standardised with `StandardScaler`. This is necessary because maternal mortality, life expectancy, and their annual changes use different units and ranges. Without scaling, the largest-scale feature would dominate Euclidean-distance-based clustering.

### 3. Algorithm comparison

The notebook evaluates two three-cluster approaches on the same standardised feature matrix:

- **K-Means** — partitions countries by minimising within-cluster squared distance.
- **Ward hierarchical clustering** — greedily merges countries/groups while minimising the increase in within-cluster variance.

The **silhouette score** is used for comparison because it combines within-cluster compactness and separation from other clusters. The SDR 2026 run selects K-Means (`0.393`) over Ward hierarchical clustering (`0.381`). K-Means uses `random_state=42` and `n_init=20` for reproducible, more stable centroid selection.

### 4. Interpretation

Clusters are sorted using a transparent composite ordering (`life_expectancy - maternal_mortality / 10`) and labelled for interpretation:

1. Highest pressure
2. Transitioning outcomes
3. Strong health outcomes

These labels describe observed outcome patterns. They are not causal categories, policy rankings, or measures of health-system quality in isolation.

## Forecasting workflow

### Prediction task

The forecasting notebook estimates one subsequent observation for each indicator. It evaluates:

- **Persistence:** use the last observed value;
- **Recent linear trend:** regress the most recent eight observations on year;
- **Full-history linear trend:** regress all prior observations on year.

### Why validation is time-aware

A random train/test split is inappropriate for forecasting because later values can leak information into the training set. Instead, the notebook holds out the final observation for every country, trains only on earlier observations, and evaluates the forecast against that held-out value.

This produces a realistic one-step-ahead benchmark across countries with at least eight observed values.

### Metrics and model decision

Candidates are compared using:

- **Mean Absolute Error (MAE):** average absolute forecasting error on the original indicator scale; lower is better.
- **R²:** additional goodness-of-fit context across held-out observations.

For the current SDR data, persistence has the lowest held-out MAE for both maternal mortality and life expectancy. It is therefore selected as the one-step baseline. This result is intentional rather than a limitation: when signals are sparse, slowly changing, or irregularly reported, a more complex linear trend can overreact and produce worse out-of-time estimates.

## Results (SDR 2026 run)

### Clustering result

K-Means was selected because it achieved the higher silhouette score on the same standardised four-feature matrix:

| Method | Silhouette score |
|---|---:|
| K-Means (`k=3`) | **0.393** |
| Ward hierarchical clustering (`k=3`) | 0.381 |

The resulting groups cover 207 countries. Values below are group means for the latest available outcomes and the estimated annual change over the recent period.

| Group | Countries | Maternal mortality | Life expectancy | Maternal-mortality change/year | Life-expectancy change/year |
|---|---:|---:|---:|---:|---:|
| Highest pressure | 58 | 310.74 | 65.12 | -13.10 | 0.40 |
| Transitioning outcomes | 82 | 71.94 | 73.41 | -0.32 | 0.14 |
| Strong health outcomes | 67 | 8.22 | 80.74 | -0.03 | 0.09 |

Interpretation: the highest-pressure group has the greatest maternal-mortality burden and lowest mean life expectancy, while the strong-outcome group has the inverse pattern. The negative maternal-mortality slopes indicate improvement on average, but the groups should be used for comparison and investigation rather than causal claims.

### Forecast benchmark

The final observation for each country was held out. The table reports held-out one-step performance; lower MAE is better.

**Maternal mortality (207 countries)**

| Model | MAE | R² |
|---|---:|---:|
| Persistence | **10.922** | **0.983** |
| Full-history linear trend | 19.535 | 0.938 |
| Recent linear trend | 20.063 | 0.917 |

**Life expectancy (208 countries)**

| Model | MAE | R² |
|---|---:|---:|
| Persistence | **0.185** | **0.999** |
| Recent linear trend | 0.593 | 0.977 |
| Full-history linear trend | 0.663 | 0.967 |

Result: carrying forward the latest observed value is the selected one-step estimator for both indicators. It substantially improves on the tested trend models in held-out error and avoids assuming that a recent linear movement will continue.

## Reproduce the analysis

### Interactive notebooks

```bash
git clone https://github.com/mdrTanvir/SDG-Health-Analytics.git
cd SDG-Health-Analytics
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
pip install nbformat nbclient jupyter
jupyter notebook
```

Open either notebook and run all cells. The official SDR workbook is downloaded on first execution and is intentionally not committed to the repository.

### Rebuild both notebooks

```bash
python refresh_notebooks.py
```

The refresh script creates a local `.cache/` directory for Matplotlib and font caches, sets `LOKY_MAX_CPU_COUNT=1` to avoid constrained-environment CPU detection warnings, downloads the SDR workbook if absent, then executes both notebooks.

## Assumptions and limitations

- The analysis is descriptive: clustering identifies similarity, not causes.
- Interpolating missing values makes a complete feature matrix, but does not create new measurements.
- Maternal mortality and life expectancy are important but incomplete health indicators.
- The forecast task is deliberately short horizon; results are planning aids, not clinical or individual-level predictions.
- Re-running with a newer SDR release can change the input panel, selected model scores, and country assignments.

## License and attribution

Please cite the Sustainable Development Report data source when reusing the analysis or its outputs. Review the SDR data provider's terms before redistributing source data.
