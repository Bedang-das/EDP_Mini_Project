# 🗺️ Project Echelon — RF Heatmap Mapper

> Part 2 of Project Echelon · Geospatial RF Dashboard for SIT Pune Campus

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-Geospatial-green)
![Map](https://img.shields.io/badge/Map-Esri%20Satellite-darkblue)
![Output](https://img.shields.io/badge/Output-Interactive%20HTML-orange)
![Part of](https://img.shields.io/badge/Part%20of-Project%20Echelon-purple)



> **This is Part 2 of Project Echelon.** The EDA and data cleaning pipeline lives in `Project_Echlon.ipynb`. This script consumes the cleaned telemetry output and deploys it as an interactive geospatial dashboard.

---

## What This Script Does

`check_10.py` takes a folder of raw CSV and KML telemetry files and outputs a single self-contained `Echelon_Professional_Map.html` — an interactive campus RF dashboard that runs in any browser with no internet or dependencies required after generation.

**Features:**
- Real **Esri World Imagery** satellite basemap
- ISP-segregated heatmap layers — Jio, Airtel, and Vodafone plotted independently with toggle controls
- **Dead Zone Override Protocol** — signal failures below -105 dBm bypass the heatmap and render as permanent red warning circles
- Google Maps-style building labels floating over satellite imagery
- Live dashboard panel with total data point count and signal quality reference

---

## Team

| Name | Roll No | Program |
|---|---|---|
| **Bedang Das** | 25070123031 | B.Tech EnTC — Sem 2, Batch A2 |
| **Arjit Ujjawal** | 25070123142 | B.Tech EnTC — Sem 2, Batch A2 |

**Institution:** Symbiosis Institute of Technology (SIT), Pune

---

## Dependencies

```bash
pip install pandas folium beautifulsoup4 lxml
```

| Library | Role |
|---|---|
| `pandas` | CSV ingestion and column normalization |
| `folium` | Interactive Leaflet.js map generation |
| `folium.plugins.HeatMap` | Signal density heatmap rendering |
| `beautifulsoup4` + `lxml` | KML file parsing for Vodafone route data |
| `glob`, `os`, `re` | File discovery and coordinate extraction |

---

## File Structure

Place `check_10.py` and all telemetry files in the **same folder:**

```
mapper/
│
├── check_10.py
├── jio_telemetry.csv
├── airtel_telemetry.csv
├── vodafone_route.kml            ← optional
├── preview.png                   ← optional, for README
│
└── Echelon_Professional_Map.html ← generated output
```

---

## How to Run

**1. Install dependencies**

```bash
pip install pandas folium beautifulsoup4 lxml
```

**2. Place your data files** in the same directory as `check_10.py`

**3. Run the script**

```bash
python check_10.py
```

The script auto-discovers all `.csv` and `.kml` files in the folder. No arguments needed.

**4. Open the map**

```bash
# Windows
start Echelon_Professional_Map.html

# macOS
open Echelon_Professional_Map.html

# Linux
xdg-open Echelon_Professional_Map.html
```

**Expected output:**

```
--- PROJECT ECHELON: PROFESSIONAL DASHBOARD INITIATED ---
[+] INGESTING: 3 CSVs | 1 KMLs
[+] SUCCESS: Professional Dashboard deployed -> Echelon_Professional_Map.html
```

---

## Input Format

### CSV Files (Jio / Airtel / BSNL)

Column names are auto-normalized to lowercase. Required columns:

| Column | Type | Description |
|---|---|---|
| `lat` | `float` | GPS Latitude |
| `lon` | `float` | GPS Longitude |
| `signal` | `int` | RSRP in dBm (negative value) |
| `mnc` | `int` | Mobile Network Code |
| `cellid` | `str` | Cell tower identifier |

### KML Files (Vodafone)

The parser reads coordinates from `<Placemark>` elements and extracts signal strength from name tags in the format `{value}dBm` (e.g. `-98dBm`). Standard exports from apps like Network Cell Info or OpenSignal work directly.

---

## ISP Routing

Each data point is classified to an ISP by its Mobile Network Code (MNC):

| ISP | MNC Codes |
|---|---|
| Jio | 854–874 |
| Airtel | 10, 31, 40, 44, 45, 49, 51–56, 70, 84, 90–98 |
| Vodafone (Vi) | 20, 27, 43, 46, 60, 88 |
| BSNL / Unknown | All others (fallback) |

---

## Signal Quality Thresholds

| Category | RSRP Range | Rendering |
|---|---|---|
| 🟢 Excellent | ≥ -75 dBm | Green heatmap |
| 🟡 Good | -76 to -90 dBm | Yellow heatmap |
| 🟠 Fair | -91 to -105 dBm | Orange heatmap |
| 🔴 Dead Zone | < -105 dBm | Forced red circle (overrides heatmap) |

**Dead Zone Override Protocol:** Points below -105 dBm are not added to the heatmap gradient. They are rendered as hard red `CircleMarker` overlays that sit on top of all other layers, making critical failures impossible to visually miss.

---

## Map Layers

Each ISP gets three independent toggleable layers (controlled via the top-right panel):

| Layer | Default | Description |
|---|---|---|
| `[ISP] Heatmap` | ✅ On | Gradient density heatmap |
| `[ISP] Raw Data Nodes` | ☐ Off | Individual dot at each GPS ping |
| `⚠️ [ISP] Critical Dead Zones` | ✅ On | Red circles at all < -105 dBm points |

---

## Customizing Building Labels

Labels are defined in the `BUILDING_LABELS` dictionary near the top of the script:

```python
BUILDING_LABELS = {
    "SIT Pune Campus Area": [18.5412, 73.7280],
    "SIT Boys/Girls Hostel": [18.5398, 73.7298],
    "Main Gate / Road":     [18.5408, 73.7275]
}
```

Edit coordinates and names to match your campus layout. Labels render as white bold text with a dark shadow, identical to Google Maps building name style.

---

## Key Results

From 1,363 data points across SIT Pune campus:

- Dead zones cluster around **building interiors and structural corridors** — confirming campus architecture attenuates RF in predictable patterns
- **Jio** shows the broadest campus coverage; **Vodafone** is sparser, particularly in the hostel zone
- The **Main Gate / Road** area shows the strongest consistent signal across all ISPs

---

## Limitations & Future Scope

- Building label coordinates are manually set — a future version could derive these from OpenStreetMap polygons
- No CLI arguments — a future version could accept `--folder`, `--zoom`, and `--output` flags
- KML parsing assumes signal values are in the `<name>` tag — apps with different schemas may need a parser extension

---

## Related

This is **Part 2** of the Project Echelon pipeline.

- 📓 [`Project_Echlon.ipynb`](../Project_Echlon.ipynb) — Full EDA, data cleaning, and statistical analysis (Part 1)

```
Raw CSVs → [Notebook: Clean + EDA] → Cleaned CSV → [This Script] → Echelon_Professional_Map.html
```

---

## License

Submitted as an academic end-semester project for B.Tech EnTC, Semester 1 at Symbiosis Institute of Technology, Pune. All telemetry data was collected on campus premises for educational purposes only.

---

<p align="center">
  <b>Arjit Ujjawal & Bedang Das</b><br>
  B.Tech EnTC Sem 2 — Symbiosis Institute of Technology, Pune
</p>
