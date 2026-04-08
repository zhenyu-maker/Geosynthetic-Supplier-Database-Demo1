import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# --- Configuration & Styling ---
st.set_page_config(page_title="Global Geosynthetics Intelligence", layout="wide")

# Standard Product List
PRODUCT_OPTIONS = [
    "Woven Geotextile", "Non-woven Geotextile", "HDPE Geomembrane", 
    "LLDPE Geomembrane", "Biaxial Geogrid", "Uniaxial Geogrid", 
    "Geocell", "GCL (Bentomite)", "Drainage Net", "Erosion Control Mat"
]

CERT_OPTIONS = ["CE", "BBA", "AASHTO", "ASQUAL", "GB", "BIS", "UKCA", "NA"]

# --- Geocoding Function ---
def get_coords(city_name):
    geolocator = Nominatim(user_agent="geo_app_procurement")
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        return None, None
    except (GeocoderTimedOut, Exception):
        return None, None

# --- Data Handling ---
def load_data():
    try:
        return pd.read_csv("suppliers.csv")
    except FileNotFoundError:
        cols = ['name', 'country', 'city', 'lat', 'lon', 'products', 'hs_code', 'certs', 'website', 'comments']
        return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv("suppliers.csv", index=False)

df = load_data()

# --- Sidebar ---
st.sidebar.title("🏢 Geosynthetics Hub")
menu = st.sidebar.radio("Navigation", ["Global Map & Search", "Supplier Management", "Market Insights"])

# --- Module 1: Global Map & Search ---
if menu == "Global Map & Search":
    st.title("🌐 Global Sourcing Database")
    
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        search_name = st.text_input("🔍 Search Supplier/Comment")
    with col_f2:
        filter_prod = st.multiselect("Filter by Product", PRODUCT_OPTIONS)
    with col_f3:
        filter_cert = st.multiselect("Filter by Cert", CERT_OPTIONS)

    # Filter Logic
    mask = df.copy()
    if search_name:
        mask = mask[mask.apply(lambda r: search_name.lower() in str(r).lower(), axis=1)]
    if filter_prod:
        mask = mask[mask['products'].apply(lambda x: any(p in str(x) for p in filter_prod))]
    if filter_cert:
        mask = mask[mask['certs'].apply(lambda x: any(c in str(x) for c in filter_cert))]

    tab_map, tab_data = st.tabs(["📍 Interactive Map", "📊 Detailed Data"])
    
    with tab_map:
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodbpositron")
        for _, row in mask.iterrows():
            if not pd.isna(row['lat']):
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=f"<b>{row['name']}</b><br>Products: {row['products']}",
                    tooltip=f"{row['name']} ({row['city']})"
                ).add_to(m)
        st_folium(m, width="100%", height=600)

    with tab_data:
        st.dataframe(mask, use_container_width=True)

# --- Module 2: Supplier Management ---
elif menu == "Supplier Management":
    st.title("🛠 Database Management")
    
    with st.expander("➕ Add New Supplier", expanded=True):
        with st.form("supplier_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Supplier Name*")
            city = c2.text_input("City & Country* (e.g. Lyon, France)")
            
            prods = st.multiselect("Products Produced", PRODUCT_OPTIONS)
            certs = st.multiselect("Certifications", CERT_OPTIONS)
            
            c3, c4, c5 = st.columns(3)
            hs = c3.text_input("HS Code")
            web = c4.text_input("Website")
            est = c5.text_input("Est. Year")
            
            notes = st.text_area("Internal Procurement Feedback")
            
            if st.form_submit_button("Geocode & Save Supplier"):
                if name and city:
                    lat, lon = get_coords(city)
                    if lat:
                        new_row = {
                            'name': name, 'country': city.split(',')[-1].strip(), 'city': city,
                            'lat': lat, 'lon': lon, 'products': ", ".join(prods),
                            'hs_code': hs, 'certs': ", ".join(certs), 'website': web, 'comments': notes
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df)
                        st.success(f"Successfully added {name} at {lat}, {lon}")
                    else:
                        st.error("Could not find that city. Please try 'City, Country' format.")
                else:
                    st.error("Name and City are required!")

    with st.expander("🗑️ Delete Supplier"):
        target = st.selectbox("Select Supplier", ["None"] + list(df['name'].unique()))
        if st.button("Delete Permanently"):
            df = df[df['name'] != target]
            save_data(df)
            st.rerun()

# --- Module 3: Market Insights ---
elif menu == "Market Insights":
    st.title("📈 Market Intelligence")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Raw Material Indices")
        st.info("💡 Keep an eye on Resin prices for negotiations.")
        st.markdown("""
        - [Platts Polypropylene Index](https://www.spglobal.com/platts/en/market-insights/symbols/polypropylene)
        - [LME Plastics History](https://www.lme.com/)
        - [Oil & Energy Feedstocks](https://www.reuters.com/markets/commodities/)
        """)
    
    with col2:
        st.subheader("Latest Industry News")
        components.iframe("https://www.geosyntheticnews.com.au/", height=700, scrolling=True)
