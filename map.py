"""
generate_recession_map.py
-------------------------
Generates an interactive Folium choropleth showing cumulative automobile
sales during U.S. recession periods, and writes it to `assets/recession_sales_map.html`
so the Dash app can serve it via an <iframe>.

Run this once (or whenever the source CSV changes) before starting the dashboard:

    python generate_recession_map.py

Author: <your name>
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

import requests
import pandas as pd
import folium
from folium.features import GeoJsonTooltip


# ============================================================
# Configuration
# ============================================================

BASE_DIR   = Path(__file__).resolve().parent
DATA_FILE  = BASE_DIR / "automobile-sales.csv"
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

OUTPUT_HTML = ASSETS_DIR / "recession_sales_map.html"

GEOJSON_URL = (
    "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
    "IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/Data%20Files/us-states.json"
)
GEOJSON_CACHE = BASE_DIR / "us-states.json"

# The dataset labels this column "City", but its values are U.S. state names.
GEO_KEY = "City"


# ============================================================
# Step 1 — Load & validate the CSV
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


# ============================================================
# Step 2 — Load (or download) the US-states GeoJSON
# ============================================================

def load_geojson() -> dict:
    if GEOJSON_CACHE.exists():
        with open(GEOJSON_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"[INFO] Downloading GeoJSON from {GEOJSON_URL}")
    resp = requests.get(GEOJSON_URL, timeout=30)
    resp.raise_for_status()
    geo = resp.json()

    with open(GEOJSON_CACHE, "w", encoding="utf-8") as f:
        json.dump(geo, f)

    return geo


# ============================================================
# Step 3 — Aggregate recession-period sales by state
# ============================================================

def aggregate_sales(df: pd.DataFrame) -> pd.DataFrame:
    recession_df = df[df["Recession"] == 1].copy()

    if recession_df.empty:
        sys.exit("[ERROR] No recession records found in the dataset.")

    sales_by_state = (
        recession_df
        .groupby(GEO_KEY, as_index=False)["Automobile_Sales"]
        .sum()
        .sort_values("Automobile_Sales", ascending=False)
    )

    print("\n[INFO] Cumulative recession-period sales by state:")
    print(sales_by_state.to_string(index=False))
    return sales_by_state


# ============================================================
# Step 4 — Build the Folium choropleth
# ============================================================

def build_map(sales_by_state: pd.DataFrame, geojson: dict) -> folium.Map:
    m = folium.Map(
        location=[37.0902, -95.7129],
        zoom_start=4,
        tiles="CartoDB positron",
    )

    choropleth = folium.Choropleth(
        geo_data=geojson,
        data=sales_by_state,
        columns=[GEO_KEY, "Automobile_Sales"],
        key_on="feature.properties.name",
        fill_color="YlOrRd",
        fill_opacity=0.75,
        line_opacity=0.25,
        nan_fill_color="lightgray",
        nan_fill_opacity=0.4,
        legend_name="Automobile Sales During Recession",
        highlight=True,
    ).add_to(m)

    # Hover tooltips for state name + value
    sales_lookup = dict(
        zip(sales_by_state[GEO_KEY], sales_by_state["Automobile_Sales"])
    )

    choropleth.geojson.add_child(
        GeoJsonTooltip(
            fields=["name"],
            aliases=["State:"],
            labels=True,
            sticky=False,
            style=(
                "background-color: white; color: #333; "
                "font-family: Arial; font-size: 12px; padding: 6px;"
            ),
        )
    )

    # Optional: add a numeric label per state using folium.features.GeoJson
    folium.GeoJson(
        geojson,
        style_function=lambda _: {"fillOpacity": 0, "color": "transparent"},
        tooltip=folium.GeoJsonTooltip(
            fields=["name"],
            aliases=["State:"],
            labels=True,
            sticky=True,
        ),
    ).add_to(m)

    # Title overlay
    title_html = """
    <div style="
        position: fixed;
        top: 10px; left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        background: rgba(255,255,255,0.9);
        padding: 8px 20px;
        border-radius: 6px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        font-family: Arial, sans-serif;
        font-size: 16px;
        font-weight: 600;
        color: #503D36;">
        Automobile Sales During Recession Periods (1980 – 2020)
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    return m


# ============================================================
# Main
# ============================================================

def main() -> None:
    print("[INFO] Loading automobile sales data ...")
    df = load_data()

    print("[INFO] Loading U.S. states GeoJSON ...")
    geojson = load_geojson()

    print("[INFO] Aggregating sales by state ...")
    sales_by_state = aggregate_sales(df)

    print("[INFO] Building Folium map ...")
    m = build_map(sales_by_state, geojson)

    m.save(str(OUTPUT_HTML))
    print(f"\n[SUCCESS] Map saved to: {OUTPUT_HTML}")
    print("          The Dash app will serve it at /assets/recession_sales_map.html")


if __name__ == "__main__":
    main()