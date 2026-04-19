import os
import glob
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import folium
from folium.plugins import HeatMap
from folium import LayerControl, DivIcon, Element
from sklearn.neighbors import KNeighborsRegressor

def echelon_professional_mapper(data_folder):
    print("--- PROJECT ECHELON: PROFESSIONAL DASHBOARD INITIATED ---")
    
    csv_files = glob.glob(os.path.join(data_folder, "*.csv"))
    kml_files = glob.glob(os.path.join(data_folder, "*.kml"))
    
    if not csv_files and not kml_files:
        print("[-] FATAL: No CSV or KML files found.")
        return

    print(f"[+] INGESTING: {len(csv_files)} CSVs | {len(kml_files)} KMLs")
    
    jio_intercepts, airtel_intercepts, vodafone_intercepts, unknown_intercepts = [], [], [], []

    # ==========================================
    # 1. THE CSV EXTRACTOR 
    # ==========================================
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df.columns = df.columns.str.lower()
            if {'lat', 'lon', 'signal', 'mnc', 'cellid'}.issubset(df.columns):
                valid_data = df.dropna(subset=['lat', 'lon', 'signal', 'mnc'])
                for _, row in valid_data.iterrows():
                    lat, lon = float(row['lat']), float(row['lon'])
                    rsrp, mnc, cid = int(row['signal']), int(row['mnc']), str(row['cellid'])
                    
                    if mnc in [854, 855, 856, 857, 861, 862, 863, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874]:
                        jio_intercepts.append([lat, lon, rsrp, cid])
                    elif mnc in [10, 31, 40, 44, 45, 49, 70, 84, 90, 92, 94, 95, 97, 98, 51, 52, 53, 54, 55, 56]:
                        airtel_intercepts.append([lat, lon, rsrp, cid])
                    elif mnc in [20, 27, 43, 46, 60, 88]: 
                        vodafone_intercepts.append([lat, lon, rsrp, cid])
                    else:
                        unknown_intercepts.append([lat, lon, rsrp, cid])
        except Exception as e: pass

    # ==========================================
    # 2. THE KML EXTRACTOR
    # ==========================================
    for file in kml_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'xml')
            placemarks = soup.find_all('Placemark')
            for pm in placemarks:
                point, line = pm.find('Point'), pm.find('LineString')
                coords_text = None
                if point and point.find('coordinates'): coords_text = point.find('coordinates').text.strip()
                elif line and line.find('coordinates'): coords_text = line.find('coordinates').text.strip().split('\n')[0]
                if not coords_text: continue
                    
                coords = coords_text.split(',')
                lon, lat = float(coords[0]), float(coords[1])
                
                name_tag = pm.find('name')
                if name_tag:
                    sig_match = re.search(r'(-?\d+)dBm', name_tag.text)
                    if sig_match:
                        vodafone_intercepts.append([lat, lon, int(sig_match.group(1)), "VODAFONE_KML_NODE"])
        except Exception as e: pass

    # ==========================================
    # 3. BASE MAP SETUP
    # ==========================================
    all_data = jio_intercepts + airtel_intercepts + vodafone_intercepts + unknown_intercepts
    if not all_data: return

    center_lat = sum(d[0] for d in all_data) / len(all_data)
    center_lon = sum(d[1] for d in all_data) / len(all_data)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=18, zoom_control=False,
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                   attr='Esri World Imagery')

    # ==========================================
    # 4. BUILDING LABELS
    # ==========================================
    BUILDING_LABELS = {
        "SIT Pune Campus Area": [18.5412, 73.7280],
        "SIT Boys/Girls Hostel": [18.5398, 73.7298],
        "Main Gate / Road": [18.5408, 73.7275]
    }

    for name, coords in BUILDING_LABELS.items():
        folium.Marker(
            location=coords,
            icon=DivIcon(
                icon_size=(150,36), icon_anchor=(75,18),
                html=f'''<div style="font-size: 14pt; color: white; font-family: Arial, sans-serif; 
                         text-shadow: 2px 2px 4px #000000, -1px -1px 4px #000000; 
                         font-weight: bold; white-space: nowrap; text-align: center;">
                         {name}</div>'''
            )
        ).add_to(m)

    # ==========================================
    # 5. EXPLICIT ZONING & DATA LAYERS
    # ==========================================
    def add_network_layer(data_list, name, border_color):
        if not data_list: return
        
        heatmap_group = folium.FeatureGroup(name=f'{name} Heatmap (Blur)', show=False)
        zone_group = folium.FeatureGroup(name=f'🎯 {name} EXPLICIT ZONES (5m Radius)', show=True)
        node_group = folium.FeatureGroup(name=f'{name} Raw Data Nodes', show=False)
        deadzone_group = folium.FeatureGroup(name=f'⚠️ {name} CRITICAL DEAD ZONES', show=True) 
        
        sorted_data = sorted(data_list, key=lambda x: x[2], reverse=True)
        heat_data = []
        
        for lat, lon, rsrp, cid in sorted_data:
            if rsrp >= -75: color, opacity = '#00ff00', 0.4
            elif rsrp >= -90: color, opacity = '#ffff00', 0.4
            elif rsrp >= -105: color, opacity = '#ffa500', 0.4
            else: 
                color, opacity = '#ff0000', 0.6
                folium.CircleMarker(
                    location=[lat, lon], radius=5, color='red', fill=True, fill_color='red', 
                    fill_opacity=0.5, weight=2, popup=f"<b>⚠️ DEAD ZONE</b><br>Signal: {rsrp}dBm"
                ).add_to(deadzone_group)

            folium.Circle(
                location=[lat, lon], radius=5, color=color, weight=1,
                fill=True, fill_color=color, fill_opacity=opacity,
                popup=f"<b>Zone Boundary:</b> {rsrp}dBm"
            ).add_to(zone_group)

            heat_data.append([lat, lon, opacity])

            folium.CircleMarker(
                location=[lat, lon], radius=4, color=border_color, fill=True, fill_color=color, 
                fill_opacity=0.9, weight=1.5, popup=f"<b>{name} Tower:</b> {cid}<br><b>Signal Strength:</b> {rsrp}dBm"
            ).add_to(node_group)

        standard_gradient = {0.4: 'orange', 0.7: 'yellow', 1.0: 'lime'}
        if heat_data:
            HeatMap(heat_data, radius=20, blur=15, min_opacity=0.5, gradient=standard_gradient).add_to(heatmap_group)
        
        zone_group.add_to(m)
        heatmap_group.add_to(m)
        node_group.add_to(m)
        deadzone_group.add_to(m) 

    add_network_layer(jio_intercepts, "🟦 JIO", "blue")
    add_network_layer(airtel_intercepts, "🟥 AIRTEL", "red")
    add_network_layer(vodafone_intercepts, "🟧 VODAFONE", "orange")

    if len(all_data) > 10:
        X = np.array([[d[0], d[1]] for d in all_data])
        y = np.array([d[2] for d in all_data])
        knn = KNeighborsRegressor(n_neighbors=5, weights='distance')
        knn.fit(X, y)
        
        # Hard boundary for the general SIT Campus Area
        lat_min, lat_max = 18.5390, 18.5420
        lon_min, lon_max = 73.7265, 73.7305
        
        # Higher resolution grid to support 5-meter strict precision
        grid_lat, grid_lon = np.meshgrid(np.linspace(lat_min, lat_max, 60), np.linspace(lon_min, lon_max, 60))
        grid_points = np.c_[grid_lat.ravel(), grid_lon.ravel()]
        
        # ==========================================
        # LIMIT PREDICTION TO STRICT CAMPUS BOUNDS
        # ==========================================
        distances, _ = knn.kneighbors(grid_points, n_neighbors=1)
        # 0.00015 degrees is roughly 15-20 meters to prevent hallucination outside the walk path
        valid_mask = distances.flatten() < 0.00015
        valid_grid_points = grid_points[valid_mask]
        
        predictions = knn.predict(valid_grid_points)
        
        # Only keeping the strict 5m predictive zones, removing the blur heatmap
        ml_zone_group = folium.FeatureGroup(name='🎯 🤖 ML Predictive Coverage (5m Zones)', show=False)
        
        for point, sig in zip(valid_grid_points, predictions):
            if sig >= -75: color, opacity = '#00ff00', 0.4
            elif sig >= -90: color, opacity = '#ffff00', 0.4
            elif sig >= -105: color, opacity = '#ffa500', 0.4
            else: color, opacity = '#ff0000', 0.5
            
            folium.Circle(
                location=[point[0], point[1]], radius=5, color=color, weight=0,
                fill=True, fill_color=color, fill_opacity=opacity,
                popup=f"<b>ML Predicted Boundary:</b> {int(sig)}dBm"
            ).add_to(ml_zone_group)
            
        ml_zone_group.add_to(m)

    # Changed collapsed to True to make it a hoverable dropdown menu
    LayerControl(position='topleft', collapsed=True).add_to(m)

    # ==========================================
    # 6. TELEMETRY OS: DISCOVERY INSIGHTS & STATS
    # ==========================================
    total_pts = len(all_data)
    dead_zones = len([d for d in all_data if d[2] < -105])
    health = 100 - ((dead_zones / total_pts) * 100) if total_pts > 0 else 0

    def calc_stats(carrier_data):
        pts = len(carrier_data)
        avg = int(sum(d[2] for d in carrier_data) / pts) if pts > 0 else 0
        exc = len([d for d in carrier_data if d[2] >= -75])
        good = len([d for d in carrier_data if -75 > d[2] >= -90])
        fair = len([d for d in carrier_data if -90 > d[2] >= -105])
        dead = len([d for d in carrier_data if d[2] < -105])
        return pts, avg, exc, good, fair, dead

    j_pts, j_avg, j_e, j_g, j_f, j_d = calc_stats(jio_intercepts)
    a_pts, a_avg, a_e, a_g, a_f, a_d = calc_stats(airtel_intercepts)
    v_pts, v_avg, v_e, v_g, v_f, v_d = calc_stats(vodafone_intercepts)

    g_exc = j_e + a_e + v_e
    g_good = j_g + a_g + v_g
    g_dead = j_d + a_d + v_d

    carrier_scores = {"JIO": j_e + j_g, "AIRTEL": a_e + a_g, "VODAFONE": v_e + v_g}
    best_download_carrier = max(carrier_scores, key=carrier_scores.get) if any(carrier_scores.values()) else "N/A"

    fail_rates = {
        "JIO": (j_d / j_pts) if j_pts > 0 else 1,
        "AIRTEL": (a_d / a_pts) if a_pts > 0 else 1,
        "VODAFONE": (v_d / v_pts) if v_pts > 0 else 1
    }
    most_stable_carrier = min(fail_rates, key=fail_rates.get) if total_pts > 0 else "N/A"

    dashboard_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* Beautify Folium/Leaflet Layer Control Panel (White & Blue Dropdown Theme) */
        .leaflet-control-layers {{
            background: rgba(255, 255, 255, 0.98) !important;
            border: 2px solid #0066cc !important;
            border-radius: 8px !important;
            color: #333 !important;
            font-family: 'Segoe UI', Arial, sans-serif !important;
            box-shadow: 0 4px 15px rgba(0, 102, 204, 0.2) !important;
            backdrop-filter: blur(8px) !important;
        }}
        .leaflet-control-layers-expanded {{ padding: 12px 15px !important; }}
        .leaflet-control-layers-separator {{ border-top: 1px solid #eaeaea !important; margin: 8px 0 !important; }}
        .leaflet-control-layers label {{ font-size: 13px !important; margin-bottom: 6px !important; cursor: pointer; transition: color 0.2s ease; font-weight: 500; }}
        .leaflet-control-layers label:hover {{ color: #0066cc !important; }}
        .leaflet-control-layers input[type="checkbox"], .leaflet-control-layers input[type="radio"] {{ 
            accent-color: #0066cc !important; 
            margin-right: 8px !important; 
            cursor: pointer;
        }}

        .echelon-toggle-btn {{
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            background: rgba(10, 14, 20, 0.95); color: #33ccff; 
            border: 1px solid #33ccff; padding: 12px 20px; border-radius: 6px; 
            cursor: pointer; font-family: 'Segoe UI', Arial, sans-serif; 
            font-weight: 800; letter-spacing: 1px; box-shadow: 0 4px 15px rgba(0, 200, 255, 0.2);
            transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            backdrop-filter: blur(5px); display: flex; align-items: center; gap: 8px;
        }}
        .echelon-toggle-btn:hover {{ background: rgba(51, 204, 255, 0.1); }}
        .echelon-toggle-btn.panel-open {{ right: 400px; background: rgba(255, 0, 0, 0.1); border-color: #ff4444; color: #ff4444; }}

        .echelon-panel {{
            position: fixed; top: 0; right: 0; width: 380px; height: 100vh;
            z-index: 9999; background: rgba(10, 14, 20, 0.95);
            border-left: 2px solid #33ccff; color: #fff;
            font-family: 'Segoe UI', Arial, sans-serif;
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px); display: flex; flex-direction: column; 
            transform: translateX(100%); 
            transition: transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        }}
        .echelon-panel.open {{ transform: translateX(0); }}
        
        .echelon-header {{
            background: #080b10; padding: 20px; border-bottom: 2px solid #33ccff; 
            display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;
        }}
        .echelon-tabs {{ display: flex; background: #111; border-bottom: 1px solid #333; flex-shrink: 0; }}
        .tab-btn {{
            flex: 1; padding: 12px 0; background: none; border: none; color: #666; 
            cursor: pointer; font-size: 14px; font-weight: bold; transition: 0.3s;
        }}
        .tab-btn.active {{ color: #33ccff; border-bottom: 3px solid #33ccff; background: rgba(51, 204, 255, 0.05); }}
        .tab-content {{ padding: 20px; display: none; overflow-y: auto; flex-grow: 1; }}
        .tab-content.active {{ display: block; }}
        
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: #0a0e14; }}
        ::-webkit-scrollbar-thumb {{ background: #33ccff; border-radius: 3px; }}

        .metric-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }}
        .metric-card {{ background: #1a222e; padding: 15px; border-radius: 6px; border-left: 4px solid #33ccff; }}
        .metric-title {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
        .metric-val {{ font-size: 24px; font-weight: bold; margin-top: 5px; }}
        .chart-container {{ background: #1a222e; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #2a3647; }}
        .chart-title {{ font-size: 12px; color: #aaa; text-align: center; margin-bottom: 12px; font-weight: bold; letter-spacing: 1px; }}
        
        /* NEW: Pinned State Style */
        .leaflet-control-layers.pinned-open {{
            border: 2px solid #00cc66 !important;
            box-shadow: 0 4px 15px rgba(0, 204, 102, 0.3) !important;
        }}
    </style>

    <!-- FLOATING TOGGLE BUTTON -->
    <button id="echelonToggle" class="echelon-toggle-btn" onclick="toggleSidebar()">
        <span>☰</span> TELEMETRY OS
    </button>

    <!-- HIDDEN SLIDE-OUT PANEL -->
    <div id="echelonSidebar" class="echelon-panel">
        <div class="echelon-header">
            <span style="font-weight: 800; font-size: 20px; letter-spacing: 2px; color: #fff;">PROJECT ECHELON</span>
            <span style="font-size: 11px; color: #00ff00; background: rgba(0,255,0,0.1); padding: 4px 8px; border-radius: 4px; border: 1px solid #00ff00;">● LIVE</span>
        </div>
        
        <div class="echelon-tabs">
            <button class="tab-btn active" onclick="switchTab('legend')">ZONING LEGEND</button>
            <button class="tab-btn" onclick="switchTab('analytics')">TELEMETRY</button>
        </div>

        <div id="legend" class="tab-content active">
            <p style="margin: 0 0 15px 0; font-size: 14px; color: #aaa;">Network quality is visualized via explicit 5-meter radial buffers.</p>
            <div style="background: #1a222e; padding: 15px; border-radius: 8px; border: 1px solid #2a3647;">
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 18px; height: 18px; background: rgba(0,255,0,0.4); border: 1px solid #00ff00; margin-right: 12px; border-radius: 50%;"></div>
                    <span style="font-size: 14px; font-weight: 600;">Excellent (-65 to -75 dBm)</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 18px; height: 18px; background: rgba(255,255,0,0.4); border: 1px solid #ffff00; margin-right: 12px; border-radius: 50%;"></div>
                    <span style="font-size: 14px; font-weight: 600;">Good (-76 to -90 dBm)</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 18px; height: 18px; background: rgba(255,165,0,0.4); border: 1px solid #ffa500; margin-right: 12px; border-radius: 50%;"></div>
                    <span style="font-size: 14px; font-weight: 600;">Fair (-91 to -105 dBm)</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 18px; height: 18px; background: rgba(255,0,0,0.6); border: 1px solid #ff0000; margin-right: 12px; border-radius: 50%;"></div>
                    <span style="font-size: 14px; font-weight: 600;">Dead Zone (<-105 dBm)</span>
                </div>
            </div>

            <div style="margin-top: 20px;">
                <h4 style="font-size: 12px; color: #aaa; border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 10px; letter-spacing: 1px;">DISCOVERY INSIGHTS</h4>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                    <div style="background: #1a222e; padding: 10px; border-radius: 6px; border-left: 3px solid #00ff00;">
                        <div style="font-size: 10px; color: #888;">OPTIMAL ZONES</div>
                        <div style="font-size: 18px; font-weight: bold; color: #fff;">{g_exc + g_good}</div>
                    </div>
                    <div style="background: #1a222e; padding: 10px; border-radius: 6px; border-left: 3px solid #ff0000;">
                        <div style="font-size: 10px; color: #888;">DEAD ZONES</div>
                        <div style="font-size: 18px; font-weight: bold; color: #fff;">{g_dead}</div>
                    </div>
                </div>

                <div style="background: rgba(51, 204, 255, 0.1); border: 1px solid #33ccff; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                    <div style="font-size: 11px; color: #33ccff; font-weight: bold; margin-bottom: 4px; letter-spacing: 1px;">⬇️ BEST FOR DOWNLOADS</div>
                    <div style="font-size: 13px; color: #ddd; line-height: 1.4;"><b>{best_download_carrier}</b> has the highest density of high-speed zones on campus.</div>
                </div>

                <div style="background: rgba(255, 165, 0, 0.1); border: 1px solid #ffa500; padding: 12px; border-radius: 6px;">
                    <div style="font-size: 11px; color: #ffa500; font-weight: bold; margin-bottom: 4px; letter-spacing: 1px;">🛡️ MOST STABLE NETWORK</div>
                    <div style="font-size: 13px; color: #ddd; line-height: 1.4;"><b>{most_stable_carrier}</b> shows the lowest connection drop rate across all surveyed paths.</div>
                </div>
            </div>

            <div style="margin-top: 20px; padding: 15px; border-left: 3px solid #00ff00; background: rgba(0,255,0,0.05);">
                <p style="margin: 0; font-size: 13px;"><b>AI Engine Status:</b> Scikit-Learn interpolation bounded to a strict ~15m prediction mask is enabled via layer control.</p>
            </div>
        </div>

        <div id="analytics" class="tab-content">
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-title">Campus Health</div>
                    <div class="metric-val" style="color: {'#00ff00' if health > 80 else '#ffa500'};">{health:.1f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Dead Zones</div>
                    <div class="metric-val" style="color: #ff0000;">{dead_zones}</div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-title">AVERAGE SIGNAL (dBm)</div>
                <canvas id="avgChart" height="150"></canvas>
            </div>

            <div class="chart-container">
                <div class="chart-title">QUALITY BREAKDOWN BY CARRIER</div>
                <canvas id="qualityChart" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">NETWORK DOMINANCE (Towers)</div>
                <canvas id="shareChart" height="180"></canvas>
            </div>
            <br><br>
        </div>
    </div>

    <script>
        // Sidebar Toggle Logic
        function toggleSidebar() {{
            const panel = document.getElementById('echelonSidebar');
            const btn = document.getElementById('echelonToggle');
            
            if (panel.classList.contains('open')) {{
                panel.classList.remove('open');
                btn.classList.remove('panel-open');
                btn.innerHTML = '<span>☰</span> TELEMETRY OS';
            }} else {{
                panel.classList.add('open');
                btn.classList.add('panel-open');
                btn.innerHTML = '<span>✖</span> CLOSE PANEL';
            }}
        }}

        // Tab Switching Logic
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}

        Chart.defaults.color = '#888';
        Chart.defaults.font.family = "'Segoe UI', sans-serif";

        new Chart(document.getElementById('avgChart'), {{
            type: 'bar',
            data: {{
                labels: ['Jio', 'Airtel', 'Vodafone'],
                datasets: [{{
                    data: [{j_avg}, {a_avg}, {v_avg}],
                    backgroundColor: ['rgba(0, 102, 255, 0.7)', 'rgba(255, 0, 0, 0.7)', 'rgba(255, 153, 0, 0.7)'],
                    borderColor: ['#0066ff', '#ff0000', '#ff9900'],
                    borderWidth: 1
                }}]
            }},
            options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ max: -50, min: -120 }} }} }}
        }});

        new Chart(document.getElementById('qualityChart'), {{
            type: 'bar',
            data: {{
                labels: ['Jio', 'Airtel', 'Vodafone'],
                datasets: [
                    {{ label: 'Excellent', data: [{j_e}, {a_e}, {v_e}], backgroundColor: 'rgba(0,255,0,0.6)' }},
                    {{ label: 'Good', data: [{j_g}, {a_g}, {v_g}], backgroundColor: 'rgba(255,255,0,0.6)' }},
                    {{ label: 'Fair', data: [{j_f}, {a_f}, {v_f}], backgroundColor: 'rgba(255,165,0,0.6)' }},
                    {{ label: 'Dead Zone', data: [{j_d}, {a_d}, {v_d}], backgroundColor: 'rgba(255,0,0,0.8)' }}
                ]
            }},
            options: {{ plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10 }} }} }}, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true }} }} }}
        }});

        new Chart(document.getElementById('shareChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Jio', 'Airtel', 'Vodafone'],
                datasets: [{{
                    data: [{j_pts}, {a_pts}, {v_pts}],
                    backgroundColor: ['#0066ff', '#ff0000', '#ff9900'],
                    borderWidth: 0
                }}]
            }},
            options: {{ cutout: '75%', plugins: {{ legend: {{ position: 'right' }} }} }}
        }});

        // ==========================================
        // BULLETPROOF LEAFLET DROPDOWN LOCK (MutationObserver)
        // ==========================================
        setTimeout(() => {{
            const layerControl = document.querySelector('.leaflet-control-layers');
            const toggleBtn = document.querySelector('.leaflet-control-layers-toggle');
            
            if (layerControl && toggleBtn) {{
                let isLocked = false;
                
                toggleBtn.addEventListener('click', (e) => {{
                    e.preventDefault();
                    e.stopPropagation();
                    isLocked = !isLocked;
                    
                    if (isLocked) {{
                        layerControl.classList.add('leaflet-control-layers-expanded', 'pinned-open');
                        toggleBtn.title = "Menu Pinned (Click to Unpin)";
                    }} else {{
                        layerControl.classList.remove('leaflet-control-layers-expanded', 'pinned-open');
                        toggleBtn.title = "Click to Pin Menu";
                    }}
                }});

                // The ultimate hack: MutationObserver instantly reverts Leaflet's auto-collapse
                const observer = new MutationObserver(() => {{
                    if (isLocked && !layerControl.classList.contains('leaflet-control-layers-expanded')) {{
                        layerControl.classList.add('leaflet-control-layers-expanded');
                    }}
                }});
                
                observer.observe(layerControl, {{ attributes: true, attributeFilter: ['class'] }});
            }}
        }}, 1500);

    </script>
    """
    
    m.get_root().html.add_child(Element(dashboard_html))

    output_file = "Echelon_Professional_Map(15).html"
    m.save(output_file)
    print(f"[+] SUCCESS: Echelon OS Dashboard deployed -> {output_file}")

# Execute
echelon_professional_mapper(".")