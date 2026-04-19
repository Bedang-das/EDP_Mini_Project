# 📡 Project Echelon — Telemetry OS Dashboard

> Advanced RF Heatmap + ML Predictive Coverage + Live Analytics · SIT Pune Campus

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-Geospatial-green)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange?logo=scikit-learn&logoColor=white)
![Map](https://img.shields.io/badge/Map-Esri%20Satellite-darkblue)
![Output](https://img.shields.io/badge/Output-Interactive%20HTML-purple)


> **This is the upgraded Part 2 of Project Echelon.** It builds on the basic mapper (`check_10.py`) by adding a KNN machine learning prediction layer and a full slide-out Telemetry OS analytics dashboard embedded directly in the map.

---

## What This Script Does

`c15.py` ingests raw CSV and KML cellular telemetry files, classifies every data point by ISP, and renders a fully self-contained interactive HTML dashboard on real Esri satellite imagery.

Beyond a standard heatmap, this version adds two major upgrades over the base mapper:

1. **ML Predictive Coverage Layer** — A KNN regression model interpolates signal strength across a high-resolution grid of the campus, filling in gaps between actual measurement points. Predictions are bounded to a strict ~15m mask around the real walk path to prevent fabricating data in areas never surveyed.

2. **Telemetry OS Sidebar** — A slide-out analytics panel with live Chart.js charts, carrier comparison stats, a campus health score, and discovery insights — all computed directly from the telemetry data at runtime.

---

## How It Works — Step by Step

### Step 1 · Data Ingestion

The script auto-discovers all `.csv` and `.kml` files in the working directory using `glob`. No filenames need to be hardcoded.

- **CSV files** are read with pandas. Columns are normalized to lowercase, then each row is validated for required fields (`lat`, `lon`, `signal`, `mnc`, `cellid`).
- **KML files** (Vodafone route data) are parsed with BeautifulSoup. Coordinates are extracted from `<Placemark>` elements, and signal strength is pulled from name tags in the format `-98dBm`.

---

### Step 2 · ISP Classification

Every data point is routed to one of four carrier buckets based on its **Mobile Network Code (MNC)**:

| ISP | MNC Codes |
|---|---|
| Jio | 854–874 |
| Airtel | 10, 31, 40, 44, 45, 49, 51–56, 70, 84, 90–98 |
| Vodafone (Vi) | 20, 27, 43, 46, 60, 88 |
| Unknown / BSNL | All others |

This separation means each ISP gets its own independent set of map layers with its own toggle controls.

---

### Step 3 · Base Map

A Folium map is created centered on the geographic mean of all collected data points, using real **Esri World Imagery** satellite tiles — the same imagery used by ArcGIS and Apple Maps. Zoom is fixed to campus level (zoom 18).

Google Maps-style floating text labels are placed over key campus landmarks using `DivIcon` — white bold text with a dark drop shadow, defined in the `BUILDING_LABELS` dictionary at the top of the script.

---

### Step 4 · Network Layers

For each ISP, the script creates four independent toggleable `FeatureGroup` layers:

| Layer | Default | What It Shows |
|---|---|---|
| `[ISP] Heatmap (Blur)` | ☐ Off | Standard blur gradient across all signal values |
| `🎯 [ISP] Explicit Zones (5m Radius)` | ✅ On | Colour-coded 5m circles at each GPS ping |
| `[ISP] Raw Data Nodes` | ☐ Off | Individual precision dots with tower ID popup |
| `⚠️ [ISP] Critical Dead Zones` | ✅ On | Hard red circles at all < -105 dBm points |

**Signal colour coding:**

| Colour | RSRP Range | Meaning |
|---|---|---|
| 🟢 Green | ≥ -75 dBm | Excellent |
| 🟡 Yellow | -76 to -90 dBm | Good |
| 🟠 Orange | -91 to -105 dBm | Fair |
| 🔴 Red | < -105 dBm | Dead Zone |

**Dead Zone Override Protocol:** Points below -105 dBm are excluded from the heatmap gradient entirely. Instead they are rendered as hard red `CircleMarker` overlays on their own layer, making critical failures impossible to miss regardless of surrounding signal density.

---

### Step 5 · ML Predictive Coverage Layer

This is the core upgrade over the base mapper.

A **K-Nearest Neighbours regressor** (`sklearn.neighbors.KNeighborsRegressor`, k=5, distance-weighted) is trained on all collected GPS-signal pairs. It then predicts signal strength across a 60×60 resolution grid spanning the campus bounding box.

**Hallucination prevention:** Before rendering any predictions, each grid point is checked against its distance to the nearest real measurement. Any grid point more than `0.00015°` (~15 metres) from an actual data point is masked out and not rendered. This ensures the ML layer only fills in plausible gaps between real measurements — it never fabricates coverage in areas that were never walked.

The result is a `🎯 🤖 ML Predictive Coverage (5m Zones)` layer (off by default) that shows what signal strength is estimated to be in the spaces between measurement points.

---

### Step 6 · Telemetry OS Sidebar

A slide-out panel is injected into the HTML output, toggled by a fixed button in the top-right corner. It has two tabs:

**Zoning Legend tab**
- Visual signal quality reference (colour swatches with dBm ranges)
- Discovery Insights: optimal zone count, dead zone count
- Best carrier for downloads (highest density of Excellent + Good points)
- Most stable carrier (lowest dead zone failure rate)
- AI Engine status indicator

**Telemetry tab (Chart.js charts)**
- **Average Signal (dBm)** — horizontal bar chart comparing Jio, Airtel, Vodafone average RSRP
- **Quality Breakdown by Carrier** — stacked bar chart showing Excellent / Good / Fair / Dead Zone split per ISP
- **Network Dominance** — doughnut chart of total data point share per carrier

All stats are computed at runtime from the actual ingested data — no hardcoded values.

**Campus Health Score** = percentage of all data points that are *not* dead zones. Displayed in green if above 80%, orange otherwise.

---

### Step 7 · Layer Control (Pinnable Dropdown)

The layer control panel (top-left) is styled with a white and blue theme. It can be **pinned open** by clicking — a `MutationObserver` is used to intercept and revert Leaflet's native auto-collapse behaviour, keeping the panel expanded even as the map re-renders.

---

## How to Run

### Prerequisites

```bash
pip install pandas numpy folium scikit-learn beautifulsoup4 lxml
```

### Setup

Place `c15.py` in the same folder as your telemetry files:

```
your_folder/
├── c15.py
├── jio_telemetry.csv
├── airtel_telemetry.csv
└── vodafone_route.kml
```

### Run

```bash
python c15.py
```

### Open the Output

```bash
# Windows
start Echelon_Professional_Map(15).html

# macOS
open "Echelon_Professional_Map(15).html"

# Linux
xdg-open "Echelon_Professional_Map(15).html"
```

> The output is a **fully self-contained HTML file**. No internet connection or runtime dependencies required after generation.

**Expected console output:**

```
--- PROJECT ECHELON: PROFESSIONAL DASHBOARD INITIATED ---
[+] INGESTING: 3 CSVs | 1 KMLs
[+] SUCCESS: Echelon OS Dashboard deployed -> Echelon_Professional_Map(15).html
```

---

## Customization

**Building Labels** — edit the dictionary near the top of the script:

```python
BUILDING_LABELS = {
    "SIT Pune Campus Area": [18.5412, 73.7280],
    "SIT Boys/Girls Hostel": [18.5398, 73.7298],
    "Main Gate / Road":     [18.5408, 73.7275]
}
```

**ML Prediction Bounds** — the campus bounding box for the KNN grid:

```python
lat_min, lat_max = 18.5390, 18.5420
lon_min, lon_max = 73.7265, 73.7305
```

**Hallucination Mask** — controls how far from a real data point a prediction is allowed:

```python
valid_mask = distances.flatten() < 0.00015  # ~15 metres
```

Increase this value to extrapolate further; decrease it for tighter precision.

---

## Dependencies

| Library | Role |
|---|---|
| `pandas` | CSV ingestion and column normalization |
| `numpy` | Grid generation for ML prediction |
| `folium` | Interactive Leaflet.js map engine |
| `folium.plugins.HeatMap` | Blur gradient heatmap rendering |
| `sklearn.neighbors.KNeighborsRegressor` | Signal strength interpolation |
| `beautifulsoup4` + `lxml` | KML file parsing |
| `glob`, `os`, `re` | File discovery and coordinate extraction |
| Chart.js (CDN) | Runtime analytics charts in the sidebar |

---

## How This Differs from `check_10.py`

| Feature | `check_10.py` | `c15.py` |
|---|---|---|
| Heatmap layers | ✅ | ✅ |
| Dead zone override | ✅ | ✅ |
| Explicit 5m zone circles | ✅ | ✅ |
| ML predictive layer | ❌ | ✅ |
| Telemetry OS sidebar | ❌ | ✅ |
| Live Chart.js analytics | ❌ | ✅ |
| Campus health score | ❌ | ✅ |
| Carrier comparison insights | ❌ | ✅ |
| Pinnable layer control | ❌ | ✅ |

---

## Limitations & Future Scope

- Campus bounding box and building labels are hardcoded — a future version could derive these from OpenStreetMap
- KNN interpolation does not account for building geometry — a future version could weight predictions by known wall/floor attenuation factors
- No CLI interface — folder path and output filename are hardcoded at the bottom of the script
- The ML layer requires at least 10 data points to activate

---

## License

Submitted as an academic end-semester project for B.Tech EnTC, Semester 2 at Symbiosis Institute of Technology, Pune. All telemetry data was collected on campus premises for educational purposes only.

---

<p align="center">
  <b>Arjit Ujjawal & Bedang Das</b><br>
  B.Tech EnTC Sem 2 — Symbiosis Institute of Technology, Pune
</p>
