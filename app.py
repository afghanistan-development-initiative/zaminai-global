"""
ZaminAI — Global Satellite Analysis Engine
Covers any country worldwide with multiple analysis layers
Author: Maiwand Jan Alamzoi — Afghanistan Development Initiative
"""

import ee
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from folium.plugins import Draw, LocateControl, MeasureControl
from streamlit_folium import st_folium
import json

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZaminAI — Global Satellite Analysis",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main{background:#f0f7f1}
.block-container{padding-top:1.5rem}
h1{color:#16a34a;font-family:sans-serif}
h2,h3{color:#1a5c2a}
div[data-testid="metric-container"]{background:white;border:1px solid #c8e6cc;border-radius:8px;padding:0.75rem}
.stTabs [data-baseweb="tab"]{font-size:13px;color:#3d6b47}
.stTabs [aria-selected="true"]{color:#16a34a !important;border-bottom:2px solid #16a34a !important}
.insight{background:white;border-left:3px solid #16a34a;border-radius:4px;padding:1rem;margin:0.5rem 0;font-size:13px}
.insight.water{border-left-color:#0284c7}
.insight.warn{border-left-color:#d97706}
.insight.danger{border-left-color:#dc2626}
.insight.soil{border-left-color:#92400e}
.layer-card{background:white;border:1px solid #c8e6cc;border-radius:8px;padding:1rem;margin:0.5rem 0}
</style>
""", unsafe_allow_html=True)

# ─── GEE INIT ─────────────────────────────────────────────────────────────────
@st.cache_resource
def init_gee():
    try:
        sa = st.secrets["gee"]["service_account"]
        pk = st.secrets["gee"]["private_key"]
        credentials = ee.ServiceAccountCredentials(sa, key_data=pk)
        ee.Initialize(credentials)
        return True
    except Exception as e:
        st.error(f"GEE error: {e}")
        return False

gee_ok = init_gee()

# ─── GLOBAL REGIONS DATABASE ──────────────────────────────────────────────────
REGIONS = {
    "🇦🇫 Afghanistan": {
        "provinces": {
            "Kunduz":     {"bbox":[68.55,36.55,69.05,37.05],"center":[36.73,68.87]},
            "Balkh":      {"bbox":[66.70,36.50,67.20,37.00],"center":[36.76,66.90]},
            "Helmand":    {"bbox":[63.80,31.00,64.80,31.80],"center":[31.35,64.20]},
            "Herat":      {"bbox":[61.80,34.10,62.50,34.60],"center":[34.34,62.20]},
            "Nangarhar":  {"bbox":[70.20,34.00,70.80,34.50],"center":[34.17,70.62]},
            "Kabul":      {"bbox":[69.00,34.30,69.50,34.70],"center":[34.53,69.17]},
            "Kandahar":   {"bbox":[65.40,31.50,66.00,31.90],"center":[31.63,65.71]},
            "Takhar":     {"bbox":[69.30,36.60,70.00,37.10],"center":[36.83,69.52]},
            "Baghlan":    {"bbox":[68.40,36.00,69.00,36.60],"center":[36.17,68.71]},
            "Badakhshan": {"bbox":[70.50,36.80,71.50,37.50],"center":[37.12,70.81]},
            "Logar":      {"bbox":[68.80,33.80,69.50,34.30],"center":[34.01,69.19]},
            "Ghazni":     {"bbox":[67.50,33.30,68.20,33.80],"center":[33.55,68.42]},
            "Bamyan":     {"bbox":[67.50,34.50,68.20,35.00],"center":[34.82,67.83]},
            "Farah":      {"bbox":[61.80,32.20,62.80,32.80],"center":[32.37,62.11]},
        },
        "center": [33.9, 67.7], "zoom": 6,
        "main_crops": ["Wheat","Cotton","Rice","Flax","Saffron","Vegetables"],
        "water_source": "Hindu Kush snowmelt + seasonal rain"
    },
    "🇮🇷 Iran": {
        "provinces": {
            "Isfahan":    {"bbox":[51.30,32.20,52.20,33.00],"center":[32.66,51.67]},
            "Khorasan":   {"bbox":[58.50,35.50,59.50,36.50],"center":[36.30,59.60]},
            "Fars":       {"bbox":[52.00,29.00,53.00,30.00],"center":[29.62,52.53]},
            "Kerman":     {"bbox":[56.50,30.00,57.50,31.00],"center":[30.28,57.07]},
            "Khuzestan":  {"bbox":[48.00,31.00,49.50,32.50],"center":[31.33,48.68]},
            "West Azerbaijan":{"bbox":[44.00,37.00,45.50,38.00],"center":[37.53,45.07]},
        },
        "center": [32.4, 53.7], "zoom": 5,
        "main_crops": ["Wheat","Saffron","Pistachios","Dates","Cotton","Rice"],
        "water_source": "Irrigation canals + seasonal rain"
    },
    "🇵🇰 Pakistan": {
        "provinces": {
            "Punjab":     {"bbox":[71.00,29.00,74.00,32.00],"center":[30.37,72.00]},
            "Sindh":      {"bbox":[67.00,24.00,70.00,27.00],"center":[25.89,68.53]},
            "KPK":        {"bbox":[70.00,33.00,72.00,35.00],"center":[34.00,71.50]},
            "Balochistan":{"bbox":[62.00,27.00,67.00,31.00],"center":[29.00,66.50]},
        },
        "center": [30.4, 69.3], "zoom": 5,
        "main_crops": ["Wheat","Rice","Cotton","Sugarcane","Maize"],
        "water_source": "Indus River irrigation system"
    },
    "🇹🇯 Tajikistan": {
        "provinces": {
            "Sughd":      {"bbox":[68.50,39.50,70.50,40.50],"center":[40.00,70.00]},
            "Khatlon":    {"bbox":[69.00,37.00,71.00,38.50],"center":[37.75,70.00]},
            "Dushanbe":   {"bbox":[68.50,38.30,69.00,38.70],"center":[38.56,68.77]},
        },
        "center": [38.9, 71.1], "zoom": 6,
        "main_crops": ["Cotton","Wheat","Vegetables","Fruits"],
        "water_source": "Amu Darya and Syr Darya rivers"
    },
    "🇺🇿 Uzbekistan": {
        "provinces": {
            "Fergana":    {"bbox":[70.50,40.00,72.00,41.00],"center":[40.39,71.79]},
            "Kashkadarya":{"bbox":[65.50,38.50,67.00,39.50],"center":[38.86,65.79]},
            "Khorezm":    {"bbox":[60.00,41.00,61.50,42.00],"center":[41.52,60.63]},
            "Tashkent":   {"bbox":[69.00,41.00,70.00,41.70],"center":[41.30,69.24]},
        },
        "center": [41.4, 64.6], "zoom": 5,
        "main_crops": ["Cotton","Wheat","Rice","Vegetables","Fruits"],
        "water_source": "Amu Darya irrigation canals"
    },
    "🇪🇹 Ethiopia": {
        "provinces": {
            "Oromia":     {"bbox":[36.00, 6.00,40.00,10.00],"center":[ 8.00,38.00]},
            "Amhara":     {"bbox":[36.00,10.00,40.00,13.00],"center":[11.50,38.00]},
            "Tigray":     {"bbox":[37.00,13.00,40.00,15.00],"center":[14.00,38.50]},
            "SNNPR":      {"bbox":[35.00, 4.00,38.00, 8.00],"center":[ 6.00,37.00]},
            "Sidama":     {"bbox":[38.00, 6.00,39.00, 7.00],"center":[ 6.75,38.50]},
        },
        "center": [9.1, 40.5], "zoom": 5,
        "main_crops": ["Teff","Maize","Wheat","Coffee","Sorghum","Barley"],
        "water_source": "Seasonal rain (bimodal) + Blue Nile"
    },
    "🇳🇬 Nigeria": {
        "provinces": {
            "Kano":       {"bbox":[8.00,11.50,9.50,12.50],"center":[12.00, 8.52]},
            "Kaduna":     {"bbox":[7.00,10.00,8.50,11.50],"center":[10.52, 7.44]},
            "Niger":      {"bbox":[4.00, 8.50,7.00,11.00],"center":[ 9.93, 5.60]},
            "Borno":      {"bbox":[12.00,11.00,15.00,13.50],"center":[11.85,13.16]},
        },
        "center": [9.1, 8.7], "zoom": 5,
        "main_crops": ["Cassava","Maize","Sorghum","Millet","Groundnuts","Rice"],
        "water_source": "Seasonal rain + Niger River"
    },
    "🇧🇩 Bangladesh": {
        "provinces": {
            "Dhaka":      {"bbox":[90.00,23.50,91.00,24.00],"center":[23.81,90.41]},
            "Chittagong": {"bbox":[91.50,22.00,92.50,23.00],"center":[22.35,91.83]},
            "Rajshahi":   {"bbox":[88.00,24.00,89.50,25.00],"center":[24.37,88.60]},
            "Sylhet":     {"bbox":[91.50,24.50,92.50,25.50],"center":[24.90,91.87]},
        },
        "center": [23.7, 90.4], "zoom": 6,
        "main_crops": ["Rice","Jute","Wheat","Vegetables","Tea"],
        "water_source": "Monsoon rain + Brahmaputra + Ganges"
    },
    "🇲🇱 Mali": {
        "provinces": {
            "Mopti":      {"bbox":[-4.00,14.00,-2.00,15.50],"center":[14.48,-4.18]},
            "Segou":      {"bbox":[-6.50,13.00,-4.00,14.00],"center":[13.45,-6.27]},
            "Kayes":      {"bbox":[-11.50,13.50,-9.50,14.50],"center":[14.44,-11.44]},
            "Sikasso":    {"bbox":[-7.00,10.50,-5.00,12.00],"center":[11.32,-5.67]},
        },
        "center": [17.6, -4.0], "zoom": 5,
        "main_crops": ["Millet","Sorghum","Maize","Cotton","Rice"],
        "water_source": "Niger River + Sahel rainfall"
    },
    "🇾🇪 Yemen": {
        "provinces": {
            "Sana'a":     {"bbox":[43.50,15.00,44.50,16.00],"center":[15.35,44.21]},
            "Hadramaut":  {"bbox":[48.00,15.00,50.00,16.50],"center":[15.93,48.51]},
            "Taiz":       {"bbox":[43.50,13.00,44.50,14.00],"center":[13.58,44.02]},
            "Hodeidah":   {"bbox":[42.50,14.50,43.50,15.50],"center":[14.80,42.95]},
        },
        "center": [15.6, 48.5], "zoom": 6,
        "main_crops": ["Sorghum","Millet","Coffee","Qat","Wheat"],
        "water_source": "Seasonal rain + groundwater (depleting)"
    },
    "🇮🇳 India — North": {
        "provinces": {
            "Punjab":     {"bbox":[73.50,29.50,76.00,32.50],"center":[31.15,75.34]},
            "Haryana":    {"bbox":[74.50,28.50,77.00,30.50],"center":[29.06,76.09]},
            "UP West":    {"bbox":[77.00,27.50,79.50,29.00],"center":[28.21,78.38]},
            "Rajasthan":  {"bbox":[70.00,25.00,77.00,30.00],"center":[27.02,74.22]},
        },
        "center": [28.6, 77.2], "zoom": 5,
        "main_crops": ["Wheat","Rice","Cotton","Sugarcane","Mustard"],
        "water_source": "Monsoon + canal irrigation + groundwater"
    },
    "🇰🇿 Kazakhstan": {
        "provinces": {
            "North Kazakhstan":{"bbox":[67.00,53.00,70.00,55.00],"center":[54.00,69.00]},
            "Akmola":     {"bbox":[68.00,51.00,72.00,53.00],"center":[51.18,71.45]},
            "Kostanay":   {"bbox":[61.00,52.00,65.00,54.00],"center":[53.18,63.63]},
        },
        "center": [48.0, 68.0], "zoom": 4,
        "main_crops": ["Wheat","Barley","Sunflower","Flax"],
        "water_source": "Steppe rain + Irtysh River"
    },
}

# ─── ANALYSIS LAYERS ─────────────────────────────────────────────────────────
LAYERS = {
    "NDVI — Vegetation Health": {
        "icon": "🌿",
        "desc": "Normalized Difference Vegetation Index — shows how healthy and dense the vegetation is",
        "source": "Sentinel-2",
        "palette": ["#d73027","#fc8d59","#fee08b","#d9ef8b","#91cf60","#1a9850"],
        "min": 0, "max": 0.7,
        "interpretation": {
            "low": "Below 0.15 — stressed, bare, or dry land",
            "medium": "0.15–0.35 — moderate vegetation, needs attention",
            "high": "Above 0.35 — healthy vegetation"
        }
    },
    "MNDWI — Water Index": {
        "icon": "💧",
        "desc": "Modified Normalized Difference Water Index — shows rivers, lakes, irrigation canals",
        "source": "Sentinel-2",
        "palette": ["#8B4513","#ffffcc","#0077b6"],
        "min": -0.3, "max": 0.5,
        "interpretation": {
            "low": "Below -0.1 — dry land, no water",
            "medium": "-0.1 to 0.05 — moist soil",
            "high": "Above 0.05 — water surface detected"
        }
    },
    "NDBI — Built-up Areas": {
        "icon": "🏘️",
        "desc": "Normalized Difference Built-up Index — shows urban areas, roads, buildings",
        "source": "Sentinel-2",
        "palette": ["#f0f0f0","#969696","#252525"],
        "min": -0.5, "max": 0.3,
        "interpretation": {
            "low": "Vegetation or water",
            "medium": "Bare soil or sparse buildings",
            "high": "Urban/built-up area"
        }
    },
    "Rainfall — CHIRPS": {
        "icon": "🌧️",
        "desc": "Annual rainfall from CHIRPS — shows total precipitation for the year",
        "source": "CHIRPS",
        "palette": ["#ffffcc","#a1dab4","#41b6c4","#2c7fb8","#253494"],
        "min": 50, "max": 800,
        "interpretation": {
            "low": "Below 200mm — arid, irrigation essential",
            "medium": "200-600mm — semi-arid, supplemental irrigation",
            "high": "Above 600mm — adequate rainfall for most crops"
        }
    },
    "Temperature — ERA5": {
        "icon": "🌡️",
        "desc": "Mean daily temperature — shows heat stress zones for crops",
        "source": "ERA5",
        "palette": ["#313695","#4575b4","#74add1","#fdae61","#f46d43","#d73027"],
        "min": 0, "max": 40,
        "interpretation": {
            "low": "Below 10°C — frost risk for sensitive crops",
            "medium": "10-30°C — optimal for most crops",
            "high": "Above 35°C — heat stress, yield reduction"
        }
    },
    "Snow Cover — MODIS": {
        "icon": "❄️",
        "desc": "Winter snow cover — critical for understanding spring water availability from snowmelt",
        "source": "MODIS MOD10A1",
        "palette": ["#f5f5f5","#a6cee3","#1f78b4","#ffffff"],
        "min": 0, "max": 100,
        "interpretation": {
            "low": "Below 20% — little snowmelt water expected",
            "medium": "20-60% — moderate snowmelt",
            "high": "Above 60% — good snowmelt supply for irrigation"
        }
    },
    "Forest Cover — Hansen": {
        "icon": "🌳",
        "desc": "Tree canopy cover — shows forests, orchards, and tree crops",
        "source": "Hansen GFW",
        "palette": ["#f7fcf5","#74c476","#00441b"],
        "min": 0, "max": 80,
        "interpretation": {
            "low": "Below 10% — open farmland or degraded",
            "medium": "10-40% — scattered trees or orchards",
            "high": "Above 40% — dense forest or woodland"
        }
    },
    "Soil Organic Carbon": {
        "icon": "🌍",
        "desc": "Soil organic carbon content — indicator of soil fertility and health",
        "source": "SoilGrids ISRIC",
        "palette": ["#f7f4e9","#d4b483","#8c5e1a","#3d1c00"],
        "min": 0, "max": 60,
        "interpretation": {
            "low": "Below 10 g/kg — poor fertility, needs organic matter",
            "medium": "10-30 g/kg — moderate fertility",
            "high": "Above 30 g/kg — good soil carbon, high fertility"
        }
    },
    "EVI — Enhanced Vegetation": {
        "icon": "🌱",
        "desc": "Enhanced Vegetation Index — better than NDVI in dense vegetation areas",
        "source": "MODIS MOD13Q1",
        "palette": ["#d73027","#fee08b","#1a9850"],
        "min": 0, "max": 0.8,
        "interpretation": {
            "low": "Below 0.2 — sparse or stressed vegetation",
            "medium": "0.2-0.4 — moderate vegetation",
            "high": "Above 0.4 — dense healthy vegetation"
        }
    },
    "Flood Risk — JRC Water": {
        "icon": "🌊",
        "desc": "JRC Global Surface Water — shows permanent and seasonal flooding frequency",
        "source": "JRC/GSW1_4",
        "palette": ["#ffffff","#aed6f1","#1a5276"],
        "min": 0, "max": 100,
        "interpretation": {
            "low": "0-10% — rarely flooded",
            "medium": "10-50% — seasonally flooded",
            "high": "Above 50% — frequently or permanently flooded"
        }
    },
}

# ─── GEE HELPER FUNCTIONS ─────────────────────────────────────────────────────
def get_s2(region, year, start="05-01", end="07-31"):
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(f"{year}-{start}", f"{year}-{end}")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 15))
            .median()
            .clip(region))

def get_tile_url(img, vis):
    return img.getMapId(vis)["tile_fetcher"].url_format

@st.cache_data(ttl=3600, show_spinner=False)
def analyse_region(bbox, year):
    region = ee.Geometry.Rectangle(bbox)
    s2 = get_s2(region, year)

    ndvi  = s2.normalizedDifference(["B8","B4"]).rename("NDVI")
    mndwi = s2.normalizedDifference(["B3","B11"]).rename("MNDWI")
    evi   = s2.expression(
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
        {"NIR":s2.select("B8"),"RED":s2.select("B4"),"BLUE":s2.select("B2")}
    ).rename("EVI")

    rain = (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
            .filterBounds(region)
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .select("precipitation").sum().clip(region))

    def mean(img, scale=30):
        return (img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region, scale=scale, maxPixels=1e9
        ).getInfo() or {})

    def area_km2(mask, band, scale=30):
        v = (mask.multiply(ee.Image.pixelArea())
             .reduceRegion(reducer=ee.Reducer.sum(), geometry=region,
                           scale=scale, maxPixels=1e9).getInfo() or {})
        return round((v.get(band, 0) or 0) / 1e6, 1)

    ndvi_v  = mean(ndvi).get("NDVI", 0) or 0
    mndwi_v = mean(mndwi).get("MNDWI", 0) or 0
    evi_v   = mean(evi).get("EVI", 0) or 0
    rain_v  = mean(rain, scale=5000).get("precipitation", 0) or 0

    crop_km2  = area_km2(ndvi.gt(0.35), "NDVI")
    water_km2 = area_km2(mndwi.gt(0.05), "MNDWI")

    # NDVI trend
    trend = {}
    for yr in [2019, 2020, 2021, 2022, 2023, 2024]:
        try:
            s2yr = get_s2(region, yr)
            v = s2yr.normalizedDifference(["B8","B4"]).reduceRegion(
                reducer=ee.Reducer.mean(), geometry=region,
                scale=30, maxPixels=1e9
            ).getInfo()
            trend[yr] = round((v or {}).get("nd", 0) or 0, 4)
        except:
            trend[yr] = 0

    return {
        "ndvi": round(ndvi_v, 4),
        "mndwi": round(mndwi_v, 4),
        "evi": round(evi_v, 4),
        "rain_mm": round(rain_v, 1),
        "cropland_km2": crop_km2,
        "water_km2": water_km2,
        "ndvi_trend": trend,
        "status": "success"
    }

def get_layer_image(bbox, layer_name, year):
    region = ee.Geometry.Rectangle(bbox)
    s2 = get_s2(region, year)
    lyr = LAYERS[layer_name]

    if "NDVI" in layer_name:
        img = s2.normalizedDifference(["B8","B4"])
    elif "MNDWI" in layer_name:
        img = s2.normalizedDifference(["B3","B11"])
    elif "NDBI" in layer_name:
        img = s2.normalizedDifference(["B11","B8"])
    elif "Rainfall" in layer_name:
        img = (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
               .filterBounds(region)
               .filterDate(f"{year}-01-01", f"{year}-12-31")
               .select("precipitation").sum().clip(region))
    elif "Temperature" in layer_name:
        img = (ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
               .filterBounds(region)
               .filterDate(f"{year}-06-01", f"{year}-08-31")
               .select("temperature_2m").mean()
               .subtract(273.15).clip(region))
    elif "Snow" in layer_name:
        img = (ee.ImageCollection("MODIS/061/MOD10A1")
               .filterBounds(region)
               .filterDate(f"{year-1}-12-01", f"{year}-03-31")
               .select("NDSI_Snow_Cover").mean().clip(region))
    elif "Forest" in layer_name:
        img = ee.Image("UMD/hansen/global_forest_change_v1_12_2023").select("treecover2000").clip(region)
    elif "Soil" in layer_name:
        img = ee.Image("projects/soilgrids-isric/soc_mean").select("soc_0-5cm_mean").clip(region)
    elif "EVI" in layer_name:
        img = (ee.ImageCollection("MODIS/061/MOD13Q1")
               .filterBounds(region)
               .filterDate(f"{year}-05-01", f"{year}-07-31")
               .select("EVI").mean().multiply(0.0001).clip(region))
    elif "Flood" in layer_name:
        img = (ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
               .select("occurrence").clip(region))
    else:
        img = s2.normalizedDifference(["B8","B4"])

    return get_tile_url(img, {"min":lyr["min"],"max":lyr["max"],"palette":lyr["palette"]})

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌍 ZaminAI Global")
    st.markdown("**Satellite Analysis — Worldwide**")
    st.divider()

    # Country selector
    country = st.selectbox("🌐 Country", list(REGIONS.keys()))
    country_data = REGIONS[country]

    # Province/region selector
    province = st.selectbox(
        "📍 Province / Region",
        list(country_data["provinces"].keys())
    )
    prov_data = country_data["provinces"][province]
    bbox = prov_data["bbox"]
    center = prov_data["center"]

    st.divider()

    # Analysis year
    year = st.selectbox("📅 Analysis year",
                        [2024,2023,2022,2021,2020,2019], index=0)

    # Layer selector
    st.markdown("**Map layers:**")
    selected_layers = []
    for lname, linfo in LAYERS.items():
        if st.checkbox(f"{linfo['icon']} {lname.split('—')[0].strip()}",
                       value=lname.startswith("NDVI")):
            selected_layers.append(lname)

    st.divider()
    st.markdown(f"**Crops:** {', '.join(country_data['main_crops'][:4])}")
    st.markdown(f"**Water:** {country_data['water_source']}")
    st.divider()
    st.markdown("**ADI · Afghanistan Development Initiative**")
    st.markdown("**zaminai.org**")

# ─── HEADER ──────────────────────────────────────────────────────────────────
col_t, col_s = st.columns([3,1])
with col_t:
    flag = country.split()[0]
    st.title(f"🌍 ZaminAI — Global Satellite Analysis")
    st.markdown(f"**{country} · {province}** · {year} · Sentinel-2 · 10m resolution")
with col_s:
    if st.button("🛰️ Run Full Analysis", type="primary", use_container_width=True):
        with st.spinner(f"Analysing {province}..."):
            result = analyse_region(bbox, year)
            st.session_state["analysis"] = result
            st.session_state["analysis_bbox"] = bbox
            st.session_state["analysis_prov"] = province
            st.session_state["analysis_year"] = year
            st.success("Done!")

# ─── MAIN TABS ───────────────────────────────────────────────────────────────
tab_map, tab_analysis, tab_layers, tab_compare, tab_trend, tab_data = st.tabs([
    "🗺️ Live Map",
    "📊 Analysis",
    "🔬 All Layers",
    "🔄 Compare",
    "📈 Trends",
    "📋 Data Export"
])

# ════════════════════════════ TAB 1 — MAP ═══════════════════════════════════
with tab_map:
    st.subheader(f"Live Satellite Map — {country} · {province} · {year}")

    col1, col2 = st.columns([3,1])
    with col2:
        load_map = st.button("🗺️ Load Map", type="primary", use_container_width=True)
        show_sat = st.checkbox("Google Satellite base", value=True)
        show_boundary = st.checkbox("Show boundary", value=True)

    with col1:
        if load_map or "map_loaded" in st.session_state:
            with st.spinner("Loading satellite tiles..."):
                try:
                    m = folium.Map(location=center, zoom_start=10, tiles=None)

                    if show_sat:
                        folium.TileLayer(
                            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                            attr="Google Satellite", name="Satellite", overlay=False
                        ).add_to(m)
                    else:
                        folium.TileLayer("CartoDB positron", name="Street").add_to(m)

                    # Add selected layers
                    for lname in selected_layers:
                        try:
                            tile_url = get_layer_image(bbox, lname, year)
                            folium.TileLayer(
                                tiles=tile_url,
                                attr=f"GEE · {LAYERS[lname]['source']}",
                                name=f"{LAYERS[lname]['icon']} {lname.split('—')[0]}",
                                overlay=True,
                                opacity=0.75
                            ).add_to(m)
                        except Exception as e:
                            st.warning(f"{lname}: {e}")

                    if show_boundary:
                        folium.Rectangle(
                            bounds=[[bbox[1],bbox[0]],[bbox[3],bbox[2]]],
                            color="#16a34a", fill=False, weight=2,
                            dash_array="8",
                            tooltip=f"{province} · {country}"
                        ).add_to(m)

                    # Add all provinces as markers
                    for pname, pdata in country_data["provinces"].items():
                        folium.Marker(
                            location=pdata["center"],
                            tooltip=pname,
                            icon=folium.Icon(
                                color="green" if pname==province else "gray",
                                icon="leaf" if pname==province else "info-sign",
                                prefix="glyphicon"
                            )
                        ).add_to(m)

                    folium.LayerControl(collapsed=False).add_to(m)
                    LocateControl(auto_start=False).add_to(m)
                    MeasureControl().add_to(m)

                    st.session_state["map_loaded"] = True
                    st_folium(m, width=None, height=580,
                              key="global_map", returned_objects=[])
                    st.success(f"✓ Showing {len(selected_layers)} layer(s) for {province}")
                except Exception as e:
                    st.error(f"Map error: {e}")
        else:
            st.info("Select your layers in the sidebar and click 'Load Map'")

# ════════════════════════════ TAB 2 — ANALYSIS ══════════════════════════════
with tab_analysis:
    if "analysis" not in st.session_state:
        st.info("Click 'Run Full Analysis' to see results for this region.")
    else:
        r = st.session_state["analysis"]
        prov_name = st.session_state.get("analysis_prov", province)
        yr = st.session_state.get("analysis_year", year)

        st.subheader(f"Analysis Results — {prov_name} · {yr}")

        # Key metrics
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        ndvi_color = "normal" if r["ndvi"] > 0.25 else "inverse"
        c1.metric("NDVI", f"{r['ndvi']}", "Vegetation health")
        c2.metric("MNDWI", f"{r['mndwi']}", "Water index")
        c3.metric("EVI", f"{r['evi']}", "Enhanced vegetation")
        c4.metric("Rainfall", f"{r['rain_mm']} mm", "Annual")
        c5.metric("Cropland", f"{r['cropland_km2']} km²", "NDVI > 0.35")
        c6.metric("Water surface", f"{r['water_km2']} km²", "MNDWI > 0.05")

        st.divider()

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            # NDVI gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=r["ndvi"],
                domain={"x":[0,1],"y":[0,1]},
                title={"text":"NDVI — Vegetation Health"},
                gauge={
                    "axis":{"range":[0,0.8]},
                    "bar":{"color":"#16a34a"},
                    "steps":[
                        {"range":[0,0.15],"color":"#fee2e2"},
                        {"range":[0.15,0.25],"color":"#fef3c7"},
                        {"range":[0.25,0.4],"color":"#d9f99d"},
                        {"range":[0.4,0.8],"color":"#bbf7d0"},
                    ],
                    "threshold":{"line":{"color":"#16a34a","width":3},"value":r["ndvi"]}
                }
            ))
            fig.update_layout(height=250, margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Metrics radar
            categories = ["NDVI×10","Water×5","EVI×10","Rain/100","Crops/50"]
            values = [
                r["ndvi"]*10,
                max(0, r["mndwi"]*5+2),
                r["evi"]*10,
                min(10, r["rain_mm"]/100),
                min(10, r["cropland_km2"]/50)
            ]
            fig2 = go.Figure(go.Scatterpolar(
                r=values+[values[0]],
                theta=categories+[categories[0]],
                fill="toself",
                fillcolor="rgba(22,163,74,0.15)",
                line_color="#16a34a"
            ))
            fig2.update_layout(
                polar=dict(radialaxis=dict(visible=True,range=[0,10])),
                showlegend=False,
                title="Field Health Radar",
                height=250,
                margin=dict(l=40,r=40,t=40,b=10)
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Insights
        st.subheader("Key Insights")
        col_a, col_b = st.columns(2)
        with col_a:
            ndvi_s = "healthy" if r["ndvi"]>0.35 else "moderate" if r["ndvi"]>0.2 else "stressed"
            st.markdown(f"""<div class="insight">
            <strong>🌿 Vegetation: {ndvi_s.upper()}</strong><br>
            NDVI of {r['ndvi']} indicates {ndvi_s} vegetation.
            {"Good growing conditions." if ndvi_s=="healthy" else
             "Some stress detected — check water and fertilizer." if ndvi_s=="moderate" else
             "Severe stress — irrigation or intervention needed urgently."}
            </div>""", unsafe_allow_html=True)

            water_s = "available" if r["mndwi"]>0.05 else "low" if r["mndwi"]>-0.05 else "critical"
            st.markdown(f"""<div class="insight water">
            <strong>💧 Water: {water_s.upper()}</strong><br>
            MNDWI of {r['mndwi']} shows water is {water_s}.
            Rainfall: {r['rain_mm']}mm annually.
            {"Adequate water for current crops." if water_s=="available" else
             "Monitor irrigation closely." if water_s=="low" else
             "Critical water shortage — switch to drought-tolerant crops."}
            </div>""", unsafe_allow_html=True)

        with col_b:
            st.markdown(f"""<div class="insight soil">
            <strong>🌾 Cropland: {r['cropland_km2']} km²</strong><br>
            Active cropland area detected by NDVI threshold (>0.35).
            Water surface area: {r['water_km2']} km².
            Correlation between water and cropland is key indicator of agricultural health.
            </div>""", unsafe_allow_html=True)

            # Crop recommendation based on water
            if r["rain_mm"] < 200 or r["mndwi"] < -0.05:
                rec_crops = "Saffron, Flax, Chickpeas"
                rec_reason = "drought-tolerant crops recommended"
            elif r["rain_mm"] < 400:
                rec_crops = "Wheat, Flax, Chickpeas, Vegetables"
                rec_reason = "moderate water crops"
            else:
                rec_crops = "Wheat, Rice, Cotton, Vegetables"
                rec_reason = "good water availability"

            st.markdown(f"""<div class="insight">
            <strong>🌱 Recommended Crops</strong><br>
            Based on water ({r['rain_mm']}mm) and NDVI data — {rec_reason}:<br>
            <strong>{rec_crops}</strong>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════ TAB 3 — ALL LAYERS ════════════════════════════
with tab_layers:
    st.subheader("All Analysis Layers — Scientific Description")

    col1, col2 = st.columns(2)
    for i, (lname, linfo) in enumerate(LAYERS.items()):
        col = col1 if i % 2 == 0 else col2
        with col:
            with st.expander(f"{linfo['icon']} {lname}"):
                st.markdown(f"**What it shows:** {linfo['desc']}")
                st.markdown(f"**Data source:** {linfo['source']}")
                st.markdown(f"**Scale:** {linfo['min']} → {linfo['max']}")
                st.markdown("**Interpretation:**")
                for level, desc in linfo["interpretation"].items():
                    color = "🔴" if level=="low" else "🟡" if level=="medium" else "🟢"
                    st.markdown(f"{color} {desc}")

                # Color scale visualization
                colors = linfo["palette"]
                cols = st.columns(len(colors))
                for j, (c, clr) in enumerate(zip(cols, colors)):
                    c.markdown(f'<div style="background:{clr};height:20px;border-radius:4px"></div>', unsafe_allow_html=True)

                if st.button(f"Load {lname.split('—')[0]} on map", key=f"load_{i}"):
                    try:
                        tile_url = get_layer_image(bbox, lname, year)
                        st.success("Layer loaded — check Map tab")
                        if "extra_layers" not in st.session_state:
                            st.session_state.extra_layers = {}
                        st.session_state.extra_layers[lname] = tile_url
                    except Exception as e:
                        st.error(f"Error: {e}")

# ════════════════════════════ TAB 4 — COMPARE ═══════════════════════════════
with tab_compare:
    st.subheader("Compare Two Regions Worldwide")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Region A**")
        country_a = st.selectbox("Country A", list(REGIONS.keys()), key="ca")
        prov_a = st.selectbox("Province A",
                               list(REGIONS[country_a]["provinces"].keys()), key="pa")
    with col2:
        st.markdown("**Region B**")
        country_b = st.selectbox("Country B", list(REGIONS.keys()),
                                  index=1, key="cb")
        prov_b = st.selectbox("Province B",
                               list(REGIONS[country_b]["provinces"].keys()), key="pb")

    cmp_year = st.selectbox("Comparison year", [2024,2023,2022,2021,2020,2019],
                             key="cmp_year")

    if st.button("🔄 Compare Regions", type="primary"):
        with st.spinner("Loading data for both regions..."):
            try:
                bbox_a = REGIONS[country_a]["provinces"][prov_a]["bbox"]
                bbox_b = REGIONS[country_b]["provinces"][prov_b]["bbox"]
                r_a = analyse_region(bbox_a, cmp_year)
                r_b = analyse_region(bbox_b, cmp_year)

                # Metrics comparison
                c1,c2,c3,c4 = st.columns(4)
                c1.metric(f"{prov_a} NDVI", r_a["ndvi"],
                           f"{'▲' if r_a['ndvi']>r_b['ndvi'] else '▼'} vs {prov_b}")
                c2.metric(f"{prov_b} NDVI", r_b["ndvi"])
                c3.metric(f"{prov_a} Water", f"{r_a['mndwi']}",
                           f"{'▲' if r_a['mndwi']>r_b['mndwi'] else '▼'} vs {prov_b}")
                c4.metric(f"{prov_b} Water", f"{r_b['mndwi']}")

                # Bar chart comparison
                metrics = ["NDVI","MNDWI+0.5","EVI","Rain/100"]
                vals_a = [r_a["ndvi"], r_a["mndwi"]+0.5, r_a["evi"], r_a["rain_mm"]/100]
                vals_b = [r_b["ndvi"], r_b["mndwi"]+0.5, r_b["evi"], r_b["rain_mm"]/100]

                fig = go.Figure()
                fig.add_trace(go.Bar(name=f"{prov_a}", x=metrics, y=vals_a,
                                     marker_color="#16a34a", opacity=0.85))
                fig.add_trace(go.Bar(name=f"{prov_b}", x=metrics, y=vals_b,
                                     marker_color="#0284c7", opacity=0.85))
                fig.update_layout(
                    barmode="group",
                    title=f"{prov_a} ({country_a}) vs {prov_b} ({country_b}) — {cmp_year}",
                    legend=dict(orientation="h"),
                    margin=dict(l=10,r=10,t=50,b=10)
                )
                st.plotly_chart(fig, use_container_width=True)

                # Summary
                winner_ndvi = prov_a if r_a["ndvi"] > r_b["ndvi"] else prov_b
                winner_water = prov_a if r_a["mndwi"] > r_b["mndwi"] else prov_b
                st.markdown(f"""
                <div class="insight">
                <strong>🏆 Comparison Summary</strong><br>
                Better vegetation: <strong>{winner_ndvi}</strong><br>
                Better water: <strong>{winner_water}</strong><br>
                Rain difference: {abs(r_a['rain_mm']-r_b['rain_mm']):.0f}mm
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Comparison error: {e}")

# ════════════════════════════ TAB 5 — TRENDS ════════════════════════════════
with tab_trend:
    st.subheader(f"Historical Trend — {province} 2019–2024")

    if "analysis" in st.session_state:
        r = st.session_state["analysis"]
        trend = r["ndvi_trend"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(trend.keys()),
            y=list(trend.values()),
            mode="lines+markers",
            line=dict(color="#16a34a", width=2.5),
            marker=dict(
                size=12,
                color=["#dc2626" if v==min(trend.values())
                       else "#16a34a" if v==max(trend.values())
                       else "#86efac" for v in trend.values()]
            ),
            fill="tozeroy",
            fillcolor="rgba(22,163,74,0.08)",
            name="NDVI"
        ))
        fig.add_hline(y=0.25, line_dash="dash", line_color="#d97706",
                      annotation_text="Good crop threshold (0.25)")
        fig.update_layout(
            title=f"NDVI Trend — {province} — Green = best year, Red = worst year",
            xaxis_title="Year",
            yaxis_title="Mean NDVI",
            margin=dict(l=10,r=10,t=50,b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Year-over-year change
        st.subheader("Year-over-year change")
        years = sorted(trend.keys())
        changes = [0] + [trend[years[i]]-trend[years[i-1]] for i in range(1,len(years))]
        fig2 = go.Figure(go.Bar(
            x=years, y=changes,
            marker_color=["#16a34a" if c>=0 else "#dc2626" for c in changes]
        ))
        fig2.add_hline(y=0, line_color="#6b7280", line_width=1)
        fig2.update_layout(
            title="Annual NDVI Change",
            yaxis_title="NDVI change vs previous year",
            margin=dict(l=10,r=10,t=50,b=10)
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Run the analysis first to see historical trends.")
        if st.button("🛰️ Run Analysis Now", type="primary"):
            with st.spinner("Loading..."):
                result = analyse_region(bbox, year)
                st.session_state["analysis"] = result
                st.rerun()

# ════════════════════════════ TAB 6 — DATA EXPORT ═══════════════════════════
with tab_data:
    st.subheader("Data Export — Download Analysis Results")

    if "analysis" in st.session_state:
        r = st.session_state["analysis"]
        prov_name = st.session_state.get("analysis_prov", province)
        yr = st.session_state.get("analysis_year", year)

        # Summary table
        summary_data = {
            "Province": [prov_name],
            "Country": [country],
            "Year": [yr],
            "NDVI": [r["ndvi"]],
            "MNDWI": [r["mndwi"]],
            "EVI": [r["evi"]],
            "Rainfall_mm": [r["rain_mm"]],
            "Cropland_km2": [r["cropland_km2"]],
            "Water_km2": [r["water_km2"]],
        }

        # Add trend data
        for tyr, val in r["ndvi_trend"].items():
            summary_data[f"NDVI_{tyr}"] = [val]

        df = pd.DataFrame(summary_data)
        st.dataframe(df, use_container_width=True)

        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"zaminai_{prov_name}_{yr}.csv",
            mime="text/csv"
        )

        # Download JSON
        json_data = json.dumps({
            "province": prov_name,
            "country": country,
            "year": yr,
            "analysis": r
        }, indent=2)
        st.download_button(
            label="⬇️ Download JSON",
            data=json_data,
            file_name=f"zaminai_{prov_name}_{yr}.json",
            mime="application/json"
        )

        # NDVI trend table
        st.subheader("NDVI Historical Data")
        trend_df = pd.DataFrame([
            {"Year": yr, "NDVI": val,
             "Status": "Best" if val==max(r["ndvi_trend"].values())
                       else "Worst" if val==min(r["ndvi_trend"].values())
                       else "Normal",
             "Change vs 2019": f"{round((val-r['ndvi_trend'].get(2019,val))/max(r['ndvi_trend'].get(2019,0.001),0.001)*100,1)}%"}
            for yr, val in r["ndvi_trend"].items()
        ])
        st.dataframe(trend_df, use_container_width=True, hide_index=True)
    else:
        st.info("Run the analysis first to export data.")

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center;color:#6b9e74;font-size:11px;line-height:2;font-family:monospace">
Afghanistan Development Initiative (ADI) · zaminai.org<br>
Sentinel-2 · CHIRPS · MODIS · ERA5 · Hansen · SoilGrids · JRC · Google Earth Engine<br>
Analyst: Maiwand Jan Alamzoi · m.alamzoi123@gmail.com
</div>
""", unsafe_allow_html=True)
