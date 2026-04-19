import os
import glob
import re
import pandas as pd
from bs4 import BeautifulSoup
import folium
from folium.plugins import HeatMap
from folium import LayerControl, DivIcon, Element

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
    # 3. BASE MAP SETUP (Standard Satellite)
    # ==========================================
    all_data = jio_intercepts + airtel_intercepts + vodafone_intercepts + unknown_intercepts
    if not all_data: return

    center_lat = sum(d[0] for d in all_data) / len(all_data)
    center_lon = sum(d[1] for d in all_data) / len(all_data)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=18,
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                   attr='Esri World Imagery')

    # ==========================================
    # 4. BUILDING LABELS (Google Maps Style)
    # ==========================================
    # I extracted these rough coordinates from your CSV files. 
    # You can easily change the text or tweak the coordinates here!
    BUILDING_LABELS = {
        "SIT Pune Campus Area": [18.5412, 73.7280],
        "SIT Boys/Girls Hostel": [18.5398, 73.7298],
        "Main Gate / Road": [18.5408, 73.7275]
    }

    # This creates the text that floats permanently over the satellite map
    for name, coords in BUILDING_LABELS.items():
        folium.Marker(
            location=coords,
            icon=DivIcon(
                icon_size=(150,36),
                icon_anchor=(75,18),
                html=f'''<div style="font-size: 14pt; color: white; font-family: Arial, sans-serif; 
                         text-shadow: 2px 2px 4px #000000, -1px -1px 4px #000000; 
                         font-weight: bold; white-space: nowrap; text-align: center;">
                         {name}</div>'''
            )
        ).add_to(m)

    # ==========================================
    # 5. DATA LAYERS (With Dead Zone Override)
    # ==========================================
    def add_network_layer(data_list, name, border_color):
        if not data_list: return
        
        heatmap_group = folium.FeatureGroup(name=f'{name} Heatmap', show=True)
        node_group = folium.FeatureGroup(name=f'{name} Raw Data Nodes', show=False)
        # NEW: A dedicated layer just for network failures
        deadzone_group = folium.FeatureGroup(name=f'⚠️ {name} CRITICAL DEAD ZONES', show=True) 
        
        # Sort so the weakest signals are plotted last (guaranteeing they sit on top of the map)
        sorted_data = sorted(data_list, key=lambda x: x[2], reverse=True)
        
        heat_data = []
        for lat, lon, rsrp, cid in sorted_data:
            
            # Standard Telecom Quality Thresholds
            if rsrp >= -75: 
                color = '#00ff00' # Green
                heat_data.append([lat, lon, 1.0])
            elif rsrp >= -90: 
                color = '#ffff00' # Yellow
                heat_data.append([lat, lon, 0.7])
            elif rsrp >= -105: 
                color = '#ffa500' # Orange
                heat_data.append([lat, lon, 0.4])
            else: 
                color = '#ff0000' # Red (Dead Zone)
                
                # OVERRIDE: Plot a massive, 12-pixel warning circle that ignores the heatmap
                folium.CircleMarker(
                    location=[lat, lon], radius=5, color='red', fill=True, fill_color='red', 
                    fill_opacity=0.5, weight=2,
                    popup=f"<b>⚠️ DEAD ZONE DETECTED</b><br>Tower: {cid}<br>Signal: {rsrp}dBm"
                ).add_to(deadzone_group)

            # Draw the standard precision dot for every point (Hidden by default)
            folium.CircleMarker(
                location=[lat, lon], radius=4, color=border_color, fill=True, fill_color=color, 
                fill_opacity=0.9, weight=1.5,
                popup=f"<b>{name} Tower:</b> {cid}<br><b>Signal Strength:</b> {rsrp}dBm"
            ).add_to(node_group)

        # We remove red from the standard gradient so the heatmap doesn't swallow the dead zones
        standard_gradient = {0.4: 'orange', 0.7: 'yellow', 1.0: 'lime'}
        if heat_data:
            HeatMap(heat_data, radius=20, blur=15, min_opacity=0.5, gradient=standard_gradient).add_to(heatmap_group)
        
        heatmap_group.add_to(m)
        node_group.add_to(m)
        deadzone_group.add_to(m) # Inject the new warning layer

        # Clean Red to Green Gradient
        standard_gradient = {0.2: 'red', 0.5: 'yellow', 1.0: 'lime'}
        HeatMap(heat_data, radius=20, blur=15, min_opacity=0.4, gradient=standard_gradient).add_to(heatmap_group)
        
        heatmap_group.add_to(m)
        node_group.add_to(m)

    add_network_layer(jio_intercepts, "🟦 JIO", "blue")
    add_network_layer(airtel_intercepts, "🟥 AIRTEL", "red")
    add_network_layer(vodafone_intercepts, "🟧 VODAFONE", "orange")

    LayerControl(position='topright', collapsed=False).add_to(m)

    # ==========================================
    # 6. PROFESSIONAL LEGEND / DASHBOARD
    # ==========================================
    legend_html = f"""
    <div style="position: fixed; bottom: 30px; left: 30px; width: 260px; z-index: 9999; 
                background: white; border: 2px solid #ccc; border-radius: 8px;
                padding: 15px; color: #333; font-family: Arial, sans-serif; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <h3 style="margin-top:0; border-bottom: 1px solid #ccc; padding-bottom: 10px; font-size: 16px;">
            Campus Network Dashboard
        </h3>
        <p style="margin: 5px 0; font-size: 13px;"><b>Total Data Points:</b> {len(all_data)}</p>
        
        <div style="margin-top: 10px;">
            <p style="margin: 0 0 5px 0; font-size: 13px; font-weight: bold;">Signal Quality Reference:</p>
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <div style="width: 15px; height: 15px; background: #00ff00; border-radius: 50%; margin-right: 8px;"></div>
                <span style="font-size: 12px;">Excellent (-65 to -75 dBm)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <div style="width: 15px; height: 15px; background: #ffff00; border-radius: 50%; margin-right: 8px;"></div>
                <span style="font-size: 12px;">Good (-76 to -90 dBm)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <div style="width: 15px; height: 15px; background: #ffa500; border-radius: 50%; margin-right: 8px;"></div>
                <span style="font-size: 12px;">Fair (-91 to -105 dBm)</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 15px; height: 15px; background: #ff0000; border-radius: 50%; margin-right: 8px;"></div>
                <span style="font-size: 12px;">Poor/Dead Zone (<-105 dBm)</span>
            </div>
        </div>
    </div>
    """
    m.get_root().html.add_child(Element(legend_html))

    output_file = "Echelon_Professional_Map.html"
    m.save(output_file)
    print(f"[+] SUCCESS: Professional Dashboard deployed -> {output_file}")

# Execute
echelon_professional_mapper(".")
