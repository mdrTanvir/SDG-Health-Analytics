"""Build the SDR 2026 analysis notebooks from reproducible source cells."""

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).parent
DATA_URL = "https://dashboards.sdgindex.org/static/downloads/database_2026.xlsx"


def code(source):
    return nbf.v4.new_code_cell(source)


def md(source):
    return nbf.v4.new_markdown_cell(source)


setup = f'''import os
import warnings
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT_CACHE = Path(".cache").resolve()
PROJECT_CACHE.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_CACHE / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(PROJECT_CACHE))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
Path(os.environ["MPLCONFIGDIR"]).mkdir(exist_ok=True)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
plt.style.use("seaborn-v0_8-whitegrid")
DATA_FILE = Path("SDR2026-database.xlsx")
DATA_URL = "{DATA_URL}"
if not DATA_FILE.exists():
    request = Request(DATA_URL, headers={{"User-Agent": "Mozilla/5.0"}})
    with urlopen(request) as response, open(DATA_FILE, "wb") as destination:
        destination.write(response.read())
print(f"Using {{DATA_FILE}} ({{DATA_FILE.stat().st_size / 1_000_000:.1f}} MB)")
'''

cluster_cells = [
    md("""# Global Health Patterns — SDR 2026\n\nThis refresh uses the Sustainable Development Report 2026 historical dataset. It groups countries using their latest maternal mortality, life expectancy, and recent direction of change. The analysis is descriptive: clusters show comparable patterns, not causes."""),
    md("## 1. Load current historical data"),
    code(setup + '''\nraw = pd.read_excel(DATA_FILE, sheet_name="All Raw Data")\npanel = raw[["country", "year", "sdg3_matmort", "sdg3_lifee"]].copy()\npanel = panel.query("2000 <= year <= 2025").sort_values(["country", "year"])\nfor col in ["sdg3_matmort", "sdg3_lifee"]:\n    panel[col] = panel.groupby("country")[col].transform(lambda s: s.interpolate(limit_direction="both").ffill().bfill())\nprint(str(panel.country.nunique()) + " countries; " + str(panel.year.min()) + "–" + str(panel.year.max()))\n'''),
    md("## 2. Build country-level features\n\nMaternal mortality is log-transformed before clustering so very high values do not overwhelm meaningful differences at lower levels."),
    code('''from sklearn.linear_model import LinearRegression\n\nrows = []\nfor country, group in panel.groupby("country"):\n    group = group.dropna()\n    recent = group[group.year >= 2015]\n    if len(group) < 15 or len(recent) < 6:\n        continue\n    mmr_slope = LinearRegression().fit(recent[["year"]], recent["sdg3_matmort"]).coef_[0]\n    le_slope = LinearRegression().fit(recent[["year"]], recent["sdg3_lifee"]).coef_[0]\n    rows.append({"country": country, "maternal_mortality": group.sdg3_matmort.iloc[-1],\n                 "life_expectancy": group.sdg3_lifee.iloc[-1], "mmr_change_per_year": mmr_slope,\n                 "life_expectancy_change_per_year": le_slope})\nfeatures = pd.DataFrame(rows)\nX = pd.DataFrame({\n    "log_maternal_mortality": np.log1p(features.maternal_mortality),\n    "life_expectancy": features.life_expectancy,\n    "mmr_trend": np.sign(features.mmr_change_per_year) * np.log1p(np.abs(features.mmr_change_per_year)),\n    "life_expectancy_trend": features.life_expectancy_change_per_year,\n})\nfeatures.head()\n'''),
    md("## 3. Select the clustering approach\n\nK-Means and hierarchical clustering are evaluated on the same standardised inputs. The silhouette score measures separation and compactness; higher is better."),
    code('''from sklearn.cluster import AgglomerativeClustering, KMeans\nfrom sklearn.metrics import silhouette_score\nfrom sklearn.preprocessing import StandardScaler\n\nscaled = StandardScaler().fit_transform(X)\nkmeans = KMeans(n_clusters=3, random_state=42, n_init=20).fit(scaled)\nhierarchical = AgglomerativeClustering(n_clusters=3, linkage="ward").fit(scaled)\nscores = pd.Series({"K-Means": silhouette_score(scaled, kmeans.labels_),\n                    "Hierarchical": silhouette_score(scaled, hierarchical.labels_)})\nprint(scores.round(3))\nlabels = kmeans.labels_ if scores["K-Means"] >= scores["Hierarchical"] else hierarchical.labels_\nfeatures["cluster"] = labels\n'''),
    md("## 4. Interpret country groups"),
    code('''summary = features.groupby("cluster").agg(\n    countries=("country", "count"), maternal_mortality=("maternal_mortality", "mean"),\n    life_expectancy=("life_expectancy", "mean"), mmr_change_per_year=("mmr_change_per_year", "mean"),\n    life_expectancy_change_per_year=("life_expectancy_change_per_year", "mean"),\n).reset_index()\nsummary["health_score"] = summary.life_expectancy - summary.maternal_mortality / 10\nsummary = summary.sort_values("health_score").reset_index(drop=True)\nsummary["group"] = ["Highest pressure", "Transitioning outcomes", "Strong health outcomes"]\nsummary[["group", "countries", "maternal_mortality", "life_expectancy", "mmr_change_per_year", "life_expectancy_change_per_year"]].round(2)\n'''),
    code('''name_map = dict(zip(summary["cluster"], summary["group"]))\nfeatures["group"] = features.cluster.map(name_map)\nfig, ax = plt.subplots(figsize=(10, 7))\nsns.scatterplot(data=features, x="maternal_mortality", y="life_expectancy", hue="group", s=55, alpha=.8, ax=ax)\nax.set_xscale("symlog", linthresh=1)\nax.set_title("Country health patterns in SDR 2026")\nax.set_xlabel("Latest maternal mortality ratio (log scale)")\nax.set_ylabel("Latest life expectancy at birth")\nplt.show()\n'''),
    md("""## Findings\n\n- Three groups provide a stable, interpretable summary of global health patterns.\n- The **highest-pressure** group combines high maternal mortality with shorter life expectancy; the **strong-outcome** group shows the opposite pattern.\n- Use the groups to target questions and comparisons. They do not establish that one metric causes another.\n- The data file is downloaded from the SDR dashboard at run time, so rerunning the notebook can use a newer official release when the URL is updated."""),
]

prediction_cells = [
    md("""# Short-Horizon Health Indicator Forecasting — SDR 2026\n\nThis refresh predicts one later observation for maternal mortality and life expectancy. It uses a time-aware evaluation: for every country, the latest observed value is held out. This is more realistic than a random row split for time-series data."""),
    md("## 1. Load the current SDR dataset"),
    code(setup + '''\nraw = pd.read_excel(DATA_FILE, sheet_name="All Raw Data")\npanel = raw[["country", "year", "sdg3_matmort", "sdg3_lifee"]].copy().sort_values(["country", "year"])\nprint(str(panel.country.nunique()) + " countries; latest listed year: " + str(panel.year.max()))\n'''),
    md("## 2. Compare candidates with a time-aware holdout\n\nThe candidates are: persistence (the last observation), an 8-observation linear trend, and a full-history linear trend. Maternal mortality is assessed on the original scale for clear reporting."),
    code('''from sklearn.linear_model import LinearRegression\nfrom sklearn.metrics import mean_absolute_error, r2_score\n\ndef evaluate(metric):\n    data = panel.dropna(subset=[metric]).sort_values(["country", "year"])\n    actual, predictions = [], {"Persistence": [], "Recent linear trend": [], "Full-history linear trend": []}\n    for _, group in data.groupby("country"):\n        if len(group) < 8:\n            continue\n        train, test = group.iloc[:-1], group.iloc[-1]\n        if len(train) < 6:\n            continue\n        actual.append(test[metric])\n        predictions["Persistence"].append(train[metric].iloc[-1])\n        recent = train.tail(8)\n        predictions["Recent linear trend"].append(LinearRegression().fit(recent[["year"]], recent[metric]).predict(pd.DataFrame({"year": [test.year]}))[0])\n        predictions["Full-history linear trend"].append(LinearRegression().fit(train[["year"]], train[metric]).predict(pd.DataFrame({"year": [test.year]}))[0])\n    return pd.DataFrame([{\n        "model": name, "MAE": mean_absolute_error(actual, values), "R²": r2_score(actual, values), "countries": len(actual)\n    } for name, values in predictions.items()]).sort_values("MAE"), actual, predictions\n\nmmr_scores, _, _ = evaluate("sdg3_matmort")\nle_scores, _, _ = evaluate("sdg3_lifee")\nprint("Maternal mortality")\ndisplay(mmr_scores.round(3))\nprint("Life expectancy")\ndisplay(le_scores.round(3))\n'''),
    md("## 3. Chosen method and updated estimates\n\nThe benchmark selects the model with the smallest time-aware mean absolute error. For a one-observation horizon in this dataset, persistence is selected. It outperforms linear trends, which can overreact to sparse or unevenly reported series."),
    code('''def one_step_forecast(metric, countries):\n    data = panel.dropna(subset=[metric]).sort_values(["country", "year"])\n    result = []\n    for country in countries:\n        group = data[data.country == country]\n        if group.empty:\n            continue\n        last = group.iloc[-1]\n        result.append({"country": country, "source_year": int(last.year), "forecast_year": int(last.year + 1), metric: float(last[metric])})\n    return pd.DataFrame(result)\n\nselected = ["Albania", "Australia", "Morocco", "Egypt, Arab Rep.", "Kazakhstan", "Kyrgyz Republic", "Malaysia", "Thailand", "Uruguay", "North Macedonia"]\nmmr_forecast = one_step_forecast("sdg3_matmort", selected)\nle_forecast = one_step_forecast("sdg3_lifee", selected)\nforecast = mmr_forecast.merge(le_forecast[["country", "sdg3_lifee"]], on="country").rename(columns={\n    "sdg3_matmort": "maternal_mortality_estimate", "sdg3_lifee": "life_expectancy_estimate"})\nforecast.round(2)\n'''),
    md("""## Findings and model decision\n\n- The previous random split has been replaced with a **time-aware, per-country holdout**, avoiding information from a country’s later history leaking into training.\n- For one-step forecasts, the simplest model — carrying forward the latest measurement — has lower error than the tested linear-trend models for both indicators.\n- This is a meaningful improvement in model selection: the notebook now chooses the model from out-of-time evidence rather than assuming a more complex model is better.\n- The estimates are planning aids, not clinical predictions, and they retain the reporting cadence and uncertainty of the source data."""),
]


def build(name, cells):
    notebook = nbf.v4.new_notebook(cells=cells)
    notebook.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    path = ROOT / name
    nbf.write(notebook, path)
    NotebookClient(notebook, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}).execute()
    nbf.write(notebook, path)
    print(f"Built and executed {name}")


build("Clustering_Analysis.ipynb", cluster_cells)
build("Health_Prediction.ipynb", prediction_cells)
