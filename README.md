# SDG Goal 3 — Global Health Analytics

**Unit:** KIT718 Big Data Analytics · University of Tasmania  
**Dataset:** [Sustainable Development Report 2024](https://dashboards.sdgindex.org/)

---

## Problem Statement

SDG Goal 3 (*Good Health and Well-Being*) requires nations to dramatically reduce maternal mortality and raise life expectancy by 2030. The 2024 Sustainable Development Report shows most countries are still rated **orange** or **red** on SDG 3, with only moderate upward trends.

This project answers two questions:

1. **Can unsupervised learning cluster countries by their health trajectories** (Maternal Mortality Rate, Life Expectancy at Birth) and reveal structural groupings aligned with income level and SDR dashboard ratings?

2. **Can a supervised regression pipeline accurately forecast 2024 SDG 3 Achievement Levels** for a diverse set of ten countries, and do those predictions match the actual SDR 2024 dashboard ratings?

---

## Solution

### Phase 1 — Global Clustering (Individual Project)

| Step | Description |
|------|-------------|
| Data extraction | Filter SDR 2024 panel for `sdg3_matmort` and `sdg3_lifee`, years 2013–2022 |
| Missing value handling | Time-series forward/backward fill per country |
| Optimal k | Elbow Method — optimal k = 3 for both indicators |
| Algorithms | K-Means (`k-means++` init) and Agglomerative Hierarchical (Ward linkage) |
| Evaluation | Silhouette Score — select better algorithm per indicator |
| Cross-indicator analysis | Compare cluster membership across both indicators |

**Key finding:** Three clusters emerge, closely aligned with low / middle / high-income country groups and the red / orange / green SDR rating bands respectively.

### Phase 2 — Forecasting & Prediction

| Stage | Description |
|-------|-------------|
| Stage 1 | Linear Regression trained on historical indicators → Goal 3 Achievement Level (mean CV R² ≈ 0.97) |
| Stage 2 | Per-indicator Linear Regression extrapolates 2024 values for 10 countries |
| Stage 3 | 2024 indicator forecasts fed into Stage 1 model → predicted achievement score |
| Validation | Predictions compared against actual SDR 2024 dashboard colour ratings |

**10 Countries:** Albania · North Macedonia · Morocco · Egypt · Australia · Kazakhstan · Kyrgyz Republic · Malaysia · Thailand · Uruguay

---

## Repository Structure

```
SDG3-Health-Analytics/
├── Phase1_Individual_Clustering.ipynb   # Clustering analysis (individual)
├── Phase2_Group_Prediction.ipynb        # Forecasting & prediction
├── SDR2024-data.xlsx                    # Source data (SDR 2024)
├── SDR2025-data.xlsx                    # Reference data (SDR 2025)
└── outputs/                             # Generated plots and result CSVs
```

---

## Setup

```bash
pip install pandas numpy matplotlib seaborn scikit-learn openpyxl scipy
jupyter notebook
```

Run `Phase1_Individual_Clustering.ipynb` first, then `Phase2_Group_Prediction.ipynb`. All output files are saved to `outputs/`.

---

## Technologies

Python · Pandas · Scikit-learn · Matplotlib · Seaborn · SciPy · Jupyter
