"""
generate_recession_map.py
-------------------------
Generates a polished, dashboard-quality Folium choropleth showing cumulative
automobile sales during U.S. recession periods.

Output: assets/recession_sales_map.html  (served by the Dash app)

Run:
    python generate_recession_map.py

Author: <your name>
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

import requests
import pandas as pd
import folium
import branca.colormap as cm
from folium.features import GeoJsonTooltip


# ============================================================
# Configuration
# ============================================================

BASE_DIR   = Path(__file__).resolve().parent
DATA_FILE  = BASE_DIR / "automobile-sales.csv"
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

OUTPUT_HTML  = ASSETS_DIR / "recession_sales_map.html"
GEOJSON_URL  = (
    "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
    "IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/Data%20Files/us-states.json"
)
GEOJSON_CACHE = BASE_DIR / "us-states.json"
GEO_KEY       = "City"          # dataset column holding state names

# Brand palette (matches the Dash dashboard)
BRAND_DARK   = "#503D36"
BRAND_ACCENT = "#C0392B"
BG_CREAM     = "#FAF6F1"
BG_GRAY      = "#F4F4F6"


# ============================================================
# Step 1 — Data
# ============================================================

def load_data() -> pd.DataFrame:
    if not DATA_FILE.exists():
        sys.exit(f"[ERROR] Data file not found: {DATA_FILE}")
    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip()
    required = {"Recession", "Automobile_Sales", GEO_KEY}
    missing  = required - set(df.columns)
    if missing:
        sys.exit(f"[ERROR] CSV missing required columns: {missing}")
    return df


def load_geojson() -> dict:
    if GEOJSON_CACHE.exists():
        return json.loads(GEOJSON_CACHE.read_text(encoding="utf-8"))
    print(f"[INFO] Downloading GeoJSON ...")
    r = requests.get(GEOJSON_URL, timeout=30)
    r.raise_for_status()
    geo = r.json()
    GEOJSON_CACHE.write_text(json.dumps(geo), encoding="utf-8")
    return geo


def aggregate_sales(df: pd.DataFrame) -> pd.DataFrame:
    rec = df[df["Recession"] == 1]
    if rec.empty:
        sys.exit("[ERROR] No recession records found.")
    s = (
        rec.groupby(GEO_KEY, as_index=False)["Automobile_Sales"]
           .sum()
           .sort_values("Automobile_Sales", ascending=False)
           .reset_index(drop=True)
    )
    s["Share"] = s["Automobile_Sales"] / s["Automobile_Sales"].sum() * 100
    print("\n[INFO] Recession-period sales by state:")
    print(s.to_string(index=False))
    return s


# ============================================================
# Step 2 — Custom HTML blocks (title, legend, leaderboard)
# ============================================================

def build_title_html() -> str:
    return f"""
    <div style="
        position: fixed;
        top: 16px; left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        background: white;
        padding: 14px 30px 12px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(80, 61, 54, 0.18);
        border-top: 4px solid {BRAND_ACCENT};
        font-family: 'Segoe UI', Arial, sans-serif;
        text-align: center;
        pointer-events: none;
        min-width: 420px;
    ">
        <div style="
            font-size: 19px;
            font-weight: 700;
            color: {BRAND_DARK};
            letter-spacing: 0.3px;
            margin-bottom: 3px;
        ">Automobile Sales During Recession Periods</div>
        <div style="
            font-size: 12px;
            font-weight: 500;
            color: #8A7971;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        ">Cumulative Sales · 1980 – 2020 · Six Recessions</div>
    </div>
    """


def build_leaderboard_html(df: pd.DataFrame) -> str:
    """Floating top-right panel: top states with sales values."""
    rows = ""
    for i, row in df.iterrows():
        medal = ["🥇", "🥈", "🥉", "  "][min(i, 3)]
        rows += f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 4px;
            border-bottom: 1px solid #EFE7E0;
            font-size: 13px;
        ">
            <span style="color:{BRAND_DARK}; font-weight:600;">
                {medal} {row[GEO_KEY]}
            </span>
            <span style="
                color:{BRAND_ACCENT};
                font-weight:700;
                font-variant-numeric: tabular-nums;
            ">{row['Automobile_Sales']:,.0f}</span>
        </div>"""

    return f"""
    <div style="
        position: fixed;
        top: 100px; right: 20px;
        z-index: 9999;
        background: white;
        padding: 14px 18px 10px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(80, 61, 54, 0.15);
        font-family: 'Segoe UI', Arial, sans-serif;
        width: 220px;
        pointer-events: none;
    ">
        <div style="
            font-size: 11px;
            font-weight: 700;
            color: {BRAND_DARK};
            letter-spacing: 1.4px;
            text-transform: uppercase;
            margin-bottom: 8px;
            padding-bottom: 6px;
            border-bottom: 2px solid {BRAND_ACCENT};
        ">Top States</div>
        {rows}
        <div style="
            margin-top: 8px;
            font-size: 10px;
            color: #A69589;
            text-align: center;
            font-style: italic;
        ">4 states with recorded sales</div>
    </div>
    """


def build_footer_html() -> str:
    return f"""
    <div style="
        position: fixed;
        bottom: 20px; left: 20px;
        z-index: 9999;
        background: rgba(255,255,255,0.95);
        padding: 8px 14px;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 11px;
        color: #8A7971;
        pointer-events: none;
    ">
        <span style="color:{BRAND_DARK}; font-weight:600;">Source:</span>
        XYZAutomotives Historical Sales · Recession = 1
    </div>
    """


# ============================================================
# Step 3 — Build the polished map
# ============================================================

def build_map(sales_df: pd.DataFrame, geojson: dict) -> folium.Map:

    # --- Warm custom gradient (cream → deep terracotta) -----
    vmin = float(sales_df["Automobile_Sales"].min())
    vmax = float(sales_df["Automobile_Sales"].max())

    colormap = cm.LinearColormap(
        colors=["#FFF5E1", "#FFD9A0", "#F5A661", "#E07038", "#B53A2C"],
        vmin=vmin,
        vmax=vmax,
        caption="Cumulative Automobile Sales During Recession",
    )

    # --- Base map: subtle gray canvas -----------------------
    m = folium.Map(
        location=[38.5, -96],
        zoom_start=4,
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Tiles © Esri",
        zoom_control="bottomright",
        control_scale=False,
    )

    # --- Choropleth layer -----------------------------------
    folium.GeoJson(
        geojson,
        name="Recession Sales",
        style_function=lambda feature: {
            "fillColor": colormap(
                sales_df.set_index(GEO_KEY)["Automobile_Sales"]
                .get(feature["properties"]["name"], vmin)
            )
            if feature["properties"]["name"] in sales_df[GEO_KEY].values
            else "#EFEFF1",
            "fillOpacity": 0.85
            if feature["properties"]["name"] in sales_df[GEO_KEY].values
            else 0.5,
            "color": "#FFFFFF",
            "weight": 1.0,
            "opacity": 0.9,
        },
        highlight_function=lambda _: {
            "weight": 2.5,
            "color": BRAND_DARK,
            "fillOpacity": 0.95,
        },
        tooltip=GeoJsonTooltip(
            fields=["name"],
            aliases=[""],
            labels=False,
            sticky=True,
            style=(
                "background: white; color: #333; "
                "font-family: Segoe UI, Arial; font-size: 12px; "
                "padding: 8px 12px; border-radius: 6px; "
                "box-shadow: 0 2px 8px rgba(0,0,0,0.15); "
                "border: none;"
            ),
        ),
    ).add_to(m)

    # --- Value labels for states with data ------------------
    state_coords = {
        "California": (37.1, -119.7),
        "Illinois":   (40.0, -89.2),
        "New York":   (43.0, -75.5),
        "Georgia":    (32.7, -83.4),
    }

    for _, row in sales_df.iterrows():
        state = row[GEO_KEY]
        if state not in state_coords:
            continue
        lat, lon = state_coords[state]
        color = colormap(row["Automobile_Sales"])

        # Choose readable text colour based on background darkness
        text_color = "white" if row["Automobile_Sales"] > (vmin + vmax) / 2 else BRAND_DARK

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 12px;
                    font-weight: 700;
                    color: {text_color};
                    text-shadow: 0 1px 3px rgba(0,0,0,0.35);
                    background: {color};
                    padding: 3px 8px;
                    border-radius: 12px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
                    white-space: nowrap;
                    transform: translate(-50%, -50%);
                    border: 1.5px solid white;
                ">{row['Automobile_Sales']/1000:.0f}K</div>
                """,
                icon_size=(0, 0),
                icon_anchor=(0, 0),
            ),
        ).add_to(m)

    # --- Custom overlays ------------------------------------
    m.get_root().html.add_child(folium.Element(build_title_html()))
    m.get_root().html.add_child(folium.Element(build_leaderboard_html(sales_df)))
    m.get_root().html.add_child(folium.Element(build_footer_html()))

    # --- Custom colour-bar legend (bottom-right) ------------
    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 20px; right: 20px;
        z-index: 9999;
        background: white;
        padding: 12px 16px 10px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(80, 61, 54, 0.15);
        font-family: 'Segoe UI', Arial, sans-serif;
        width: 260px;
    ">
        <div style="
            font-size: 11px;
            font-weight: 700;
            color: {BRAND_DARK};
            letter-spacing: 1.4px;
            text-transform: uppercase;
            margin-bottom: 8px;
        ">Sales Scale</div>
        <div style="
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg,
                #FFF5E1 0%, #FFD9A0 25%, #F5A661 50%,
                #E07038 75%, #B53A2C 100%);
            box-shadow: inset 0 0 4px rgba(0,0,0,0.1);
        "></div>
        <div style="
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 10px;
            color: #8A7971;
            font-variant-numeric: tabular-nums;
        ">
            <span>{vmin/1000:.0f}K</span>
            <span>{(vmin+vmax)/2/1000:.0f}K</span>
            <span>{vmax/1000:.0f}K</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # --- Soft inner border for "framed" look ----------------
    frame_html = f"""
    <style>
        body {{ background: {BG_CREAM}; }}
        .leaflet-container {{
            border-radius: 0;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        .leaflet-control-attribution {{
            background: rgba(255,255,255,0.85) !important;
            font-size: 9px !important;
        }}
        .leaflet-tooltip {{
            border: none !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15) !important;
        }}
    </style>
    """
    m.get_root().header.add_child(folium.Element(frame_html))

    return m


# ============================================================
# Main
# ============================================================

def main() -> None:
    print("[INFO] Loading data ...")
    df = load_data()

    print("[INFO] Loading GeoJSON ...")
    geo = load_geojson()

    print("[INFO] Aggregating sales ...")
    sales = aggregate_sales(df)

    print("[INFO] Building styled map ...")
    m = build_map(sales, geo)
    m.save(str(OUTPUT_HTML))

    print(f"\n[SUCCESS] Map written to: {OUTPUT_HTML}")
    print("          Open in a browser, or run app_dashboard.py to view inside Dash.")


if __name__ == "__main__":
    main()