# 📡 Project Echelon

> Macro-Level Cellular RF Spatial Analysis of SIT Pune Campus

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange?logo=jupyter&logoColor=white)
![Colab](https://img.shields.io/badge/Platform-Google%20Colab-yellow?logo=googlecolab&logoColor=white)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Domain](https://img.shields.io/badge/Domain-Telecom%20%7C%20RF%20%7C%20GeoSpatial-green)

!> 🌍 **Live Deployment:** [Explore the Interactive Echelon Map Here](https://project-echelon-sitpune.netlify.app/)

---

## Overview

Your phone shows full bars — but you still can't load a page. The call drops the moment you walk into a corridor. This is not a network outage. It is **physics**.

Reinforced concrete, metal window frames, and dense building layouts act as RF shields, creating invisible cellular dead zones that no carrier infrastructure can fix from the outside. **Project Echelon** set out to prove this empirically.

We walked the entire SIT Pune campus with our phones acting as scientific instruments — logging GPS coordinates, signal strength, and cell tower data every few seconds — then built a complete data pipeline to process, analyse, and spatially visualise that data.

**The system has two parts:**

| Part | File | Purpose |
|---|---|---|
| EDA Notebook | `Project_Echlon.ipynb` | Cleans raw data and proves dead zones mathematically via graphs |
| Mapper Script | `mapper/check_10.py` | Deploys data as a live interactive satellite heatmap |
| Machine Leanring Model | `ml/Check_15` | Deploys an interactive DashBoard via K-neighbour model |


---

## Table of Contents

- [Team](#team)
- [Pipeline Overview](#pipeline-overview)
- [Phase 1 — Data Collection](#phase-1--data-collection)
- [Phase 2 — Data Sanitization](#phase-2--data-sanitization)
- [Phase 3 — EDA & Graphing](#phase-3--eda--graphing)
- [Phase 4 — Geospatial Deployment](#phase-4--geospatial-deployment)
- [How to Run](#how-to-run)
- [Key Findings](#key-findings)
- [Tech Stack](#tech-stack)
- [Limitations & Future Scope](#limitations--future-scope)

---

## Team

| Name | Roll No | Program |
|---|---|---|
| **Bedang Das** | 25070123031 | B.Tech Electronics & Telecommunication Engineering |
| **Arjit Ujjawal** | 25070123142 | B.Tech Electronics & Telecommunication Engineering |

**Institution:** Symbiosis Institute of Technology (SIT), Pune  
**Semester:** 1 · **Batch:** A2 · **Subject:** Exploratory Data Analysis (EDA) in Python

---


> **Note:** Raw CSV and KML files are not committed due to file size. Collect your own telemetry using the apps described in Phase 1, or contact the team for the original dataset.

---

## Pipeline Overview

```
Phase 1          Phase 2              Phase 3            Phase 4
──────────       ──────────────       ──────────────     ──────────────────
Data             Ingestion &          Statistical        Geospatial
Collection  ──►  Sanitization    ──►  EDA & Graphing ──► Deployment
(Real World)     (Notebook)           (Notebook)         (Mapper Script)
```

---

## Phase 1 — Data Collection

We used personal Android phones to log cellular RF telemetry across SIT campus. The primary metric is **RSRP (Reference Signal Received Power)** — the telecom industry standard for LTE/5G signal strength, measured in dBm.

| RSRP Value | Meaning |
|---|---|
| `-65 dBm` | Excellent |
| `-105 dBm` | Dead zone — calls drop, data stalls |

**Paths covered:** Main academic block · Building corridors · Hostel zone · Campus perimeter · Main gate road

### Fields Logged per GPS Ping

| Field | Description |
|---|---|
| `lat` / `lon` | GPS coordinates at time of reading |
| `signal` | RSRP in dBm |
| `mnc` | Mobile Network Code — identifies the serving ISP tower |
| `cellid` | Unique identifier of the connected cell tower |
| `time` | Unix millisecond timestamp |

**Total data points collected: 1,363** across Jio, Airtel, and Vodafone simultaneously — allowing not just a coverage map, but a competitive network audit across carriers.

---

## Phase 2 — Data Sanitization

**File:** `Project_Echlon.ipynb` · **Platform:** Google Colab

A 7-step pipeline transforms noisy, multi-source CSV files into a clean, validated dataset.

| Step | Action |
|---|---|
| 1. Ingestion | `glob` discovers and concatenates all CSVs into one `DataFrame` |
| 2. Standardization | Column headers normalized to lowercase across all sources |
| 3. Feature Selection | Strips to the 7 required columns: `lat`, `lon`, `signal`, `mnc`, `cellid`, `alt`, `time` |
| 4. Null Sanitization | Drops any row with missing GPS or signal values |
| 5. Duplicate Filtering | Removes repeated location-timestamp pairs from stationary readings |
| 6. Physical Validation | Enforces negative signal values; rejects `0,0` coordinates |
| 7. Type Casting | Casts to strict numerical types; converts Unix timestamps to IST `DateTime` |

**Output:** `Echelon_Cleaned_Telemetry.csv` — ready for analysis and mapping.

---

## Phase 3 — EDA & Graphing

**File:** `Project_Echlon.ipynb`

### Feature Engineering

**MNC → ISP Mapping**

| ISP | MNC Codes |
|---|---|
| Jio | 854–874 |
| Airtel | 10, 31, 40, 44, 45, 49, 51–56, 70, 84, 90–98 |
| Vodafone (Vi) | 20, 27, 43, 46, 60, 88 |
| BSNL | All others (fallback) |

**RSRP → Signal Quality Tiers**

| Category | Threshold | Meaning |
|---|---|---|
| 🟢 Excellent | ≥ -75 dBm | Strong, reliable connection |
| 🟡 Good | -76 to -90 dBm | Normal usability |
| 🟠 Fair | -91 to -105 dBm | Slow data, occasional buffering |
| 🔴 Dead Zone | < -105 dBm | Call drops, no throughput |

### The Four Graphs

**1 · Campus RF Signal Distribution (Histogram)**  
All RSRP values overlaid with a KDE curve. A dashed line marks the -105 dBm threshold. A statistically significant tail past this line mathematically proves dead zones exist.

**2 · Signal Quality Classification Count (Bar Chart)**  
Data points counted per quality tier, colour-coded green to red. The Dead Zone to Excellent ratio quantifies exactly what percentage of campus is failing.

**3 · Top 10 Most Active Cell Towers (Bar Chart)**  
A skewed distribution here reveals the campus is served by a few overloaded macro cells — an infrastructure bottleneck explaining poor performance even in areas with acceptable signal.

**4 · "Walk of Frustration" Signal Volatility (Line Plot)**  
RSRP across the first 150 GPS pings of a continuous walk, with the sub -105 dBm region shaded red. Sharp drops into the red zone mark the exact moments a real user would experience a call drop.

---

## Phase 4 — Geospatial Deployment

**File:** `mapper/check_10.py`

Where Phase 3 proved dead zones statistically, Phase 4 proves them geographically — on real **Esri World Imagery** satellite tiles (the same data used by ArcGIS and Apple Maps).

### The Dead Zone Override Protocol

A standard heatmap blends all signal values together — a cluster of -110 dBm readings gets absorbed into the surrounding gradient and becomes invisible.

To fix this: any point below -105 dBm is **not** added to the heatmap. Instead it is rendered as a hard red `CircleMarker` on its own dedicated layer (`⚠️ [ISP] CRITICAL DEAD ZONES`), sitting on top of everything and impossible to wash out.

### Layer Architecture

Each ISP gets three independent, toggleable layers:

| Layer | Default | Description |
|---|---|---|
| `[ISP] Heatmap` | ✅ On | Smooth density gradient (green → yellow → orange) |
| `[ISP] Raw Data Nodes` | ☐ Off | Precision dot at each GPS ping |
| `⚠️ [ISP] Critical Dead Zones` | ✅ On | Hard red circles at all < -105 dBm locations |

The map also includes permanent campus landmark labels and a fixed dashboard panel showing total point count and the signal quality legend.

---

## How to Run

### Prerequisites

```bash
pip install pandas numpy matplotlib seaborn folium beautifulsoup4 lxml
```

### Part 1 — Notebook (EDA + Graphs)

1. Open `Project_Echlon.ipynb` in Google Colab or Jupyter
2. Run **Cell 1** — installs dependencies and opens a file picker
3. Upload your raw telemetry CSV files
4. Run all remaining cells top-to-bottom

**Outputs generated:**
- `Echelon_Cleaned_Telemetry.csv`
- `echelon_call_drop_analysis.png`
- All four inline graphs

### Part 2 — Mapper Script (Heatmap)

Place `check_10.py` in the same folder as your CSV/KML files, then run:

```bash
python check_10.py
```

Open the output in any browser:

```bash
# Windows
start Echelon_Professional_Map.html

# macOS
open Echelon_Professional_Map.html

# Linux
xdg-open Echelon_Professional_Map.html
```

> The output is a **fully self-contained HTML file** — no internet connection, server, or runtime dependencies needed after generation.

**Expected console output:**

```
--- PROJECT ECHELON: PROFESSIONAL DASHBOARD INITIATED ---
[+] INGESTING: 3 CSVs | 1 KMLs
[+] SUCCESS: Professional Dashboard deployed -> Echelon_Professional_Map.html
```

---

## Key Findings

From 1,363 data points across SIT Pune campus:

- **Dead zones are structurally caused.** The RSRP histogram shows a significant tail past -105 dBm, concentrated in building interiors and enclosed corridors — confirming campus architecture attenuates RF in predictable patterns.
- **Coverage is ISP-dependent and spatially uneven.** Jio shows the broadest campus coverage. Vodafone is considerably sparser, particularly in the hostel zone. No single ISP covers the entire campus uniformly.
- **Cell tower load is heavily concentrated.** The campus is predominantly served by a small number of macro cells, creating handover overhead and load bottlenecks during peak hours.
- **The main gate road zone has the best signal across all ISPs.** Open-air, unobstructed, close to road-facing tower infrastructure — consistent with RF propagation theory.
- **Building interiors are the primary failure zone.** Virtually all hard dead-zone markers cluster around building interiors, stairwells, and ground-floor zones — consistent with RF attenuation through reinforced concrete.

---

## Tech Stack

| Tool / Library | Used In | Role |
|---|---|---|
| `pandas` | Both | Data ingestion, cleaning, feature engineering |
| `numpy` | Notebook | Numerical operations |
| `matplotlib` | Notebook | Static plot generation |
| `seaborn` | Notebook | Statistical visualization |
| `folium` | Mapper | Interactive Leaflet.js map engine |
| `folium.plugins.HeatMap` | Mapper | Signal density heatmap rendering |
| `beautifulsoup4` + `lxml` | Mapper | KML file parsing |
| `glob` / `os` / `re` | Both | File discovery and regex extraction |
| Google Colab | Notebook | Cloud execution + file I/O |
| Esri World Imagery | Mapper | Satellite basemap tiles |

---

## Limitations & Future Scope

**Current Limitations**
- Single survey session — multi-day collection would improve statistical confidence
- No indoor/outdoor distinction — a key variable for attenuation analysis
- Building labels are manually geocoded rather than derived from OpenStreetMap polygons
- No CLI interface — paths and output filename are hardcoded

**Future Extensions**
- **5G NR Metrics** — Add RSRQ and SINR for a complete RF picture beyond RSRP
- **Temporal Analysis** — Plot signal vs. time-of-day to detect peak-hour congestion patterns
- **Predictive Modelling** — Train a spatial ML model to predict dead zones from building geometry alone
- **CLI Interface** — Add `argparse` support for `--folder`, `--zoom`, and `--output` flags

---

<p align="center">
  Made with caffeine and actual science.<br><br>
  <b>Arjit Ujjawal & Bedang Das</b><br>
  B.Tech EnTC Sem 2 — Symbiosis Institute of Technology, Pune
</p>
