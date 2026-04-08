import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# --- Configuration & Styling ---
st.set_page_config(page_title="Global Geosynthetics Intelligence Hub", layout="wide")

# Updated Professional Product List based on your requirement
PRODUCT_OPTIONS = [
    "PP Geogrid", "HDPE Geogrid","Fiberglass Geogrid", "Woven PET Geogrid", "Knitted PET Geogrid", 
    "Geocell", "Woven PET Geotextile", "Woven PP Geotextile", 
    "Silt Tape PP", "Geotextile PP NW", "Geomembrane", "Geomat", 
    "Drainage board", "GCL", "GCCM", "Geogrid composite", 
    "Silt Fence", "Concrete Mattress", "Geotube", 
    "Rockbag PET/HDPE", "Vertical drainage", "Other"
]

CERT_OPTIONS = ["CE", "BBA", "AASHTO", "ASQUAL", "GB", "BIS", "UKCA", "NA"]

# --- Geocoding Function ---
def get_coords(city_name):
    # Added user_agent for compliance with Nominatim's usage policy
    geolocator = Nominatim(user_agent="geosynthetics_procurement_app_v2")
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

# --- Sidebar Navigation ---
st.sidebar.title("🏢 Geosynthetics Intelligence")
menu = st.sidebar.radio("Navigation", ["Global Map & Search", "Supplier Management", "Market Insights"])

# --- Module 1: Global Map & Search ---
if menu == "Global Map & Search":
    st.title("🌐 Global Sourcing Database")
    
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        search_name = st.text_input("🔍 Search Supplier Name or Comments")
    with col_f2:
        filter_prod = st.multiselect("Filter by Product Category", PRODUCT_OPTIONS)
    with col_f3:
        filter_cert = st.multiselect("Filter by Certification", CERT_OPTIONS)

    # Filter Logic
    mask = df.copy()
    if search_name:
        mask = mask[mask.apply(lambda r: search_name.lower() in str(r).lower(), axis=1)]
    if filter_prod:
        # Check if any selected product is in the 'products' string of the row
        mask = mask[mask['products'].apply(lambda x: any(p in str(x) for p in filter_prod))]
    if filter_cert:
        mask = mask[mask['certs'].apply(lambda x: any(c in str(x) for c in filter_cert))]

    tab_map, tab_data = st.tabs(["📍 Interactive Map", "📊 Data Table"])
    
    with tab_map:
        # Default center of the world
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
    st.title("🛠 Database Administration")
    
    with st.expander("➕ Add New Supplier", expanded=True):
        with st.form("supplier_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Supplier Name*")
            city = c2.text_input("City & Country* (e.g., Shanghai, China or Paris, France)")
            
            # This allows multi-selection for the product list you provided
            prods = st.multiselect("Product Range", PRODUCT_OPTIONS)
            certs = st.multiselect("Certifications", CERT_OPTIONS)
            
            c3, c4, c5 = st.columns(3)
            hs = c3.text_input("HS Code")
            web = c4.text_input("Official Website")
            est = c5.text_input("Est. Year")
            
            notes = st.text_area("Procurement Team Feedback & Internal Ratings")
            
            if st.form_submit_button("Geocode & Save to Cloud"):
                if name and city:
                    with st.spinner('Locating City on Map...'):
                        lat, lon = get_coords(city)
                    if lat:
                        # Split city to get country for the country column
                        country_val = city.split(',')[-1].strip()
                        new_row = {
                            'name': name, 'country': country_val, 'city': city,
                            'lat': lat, 'lon': lon, 'products': ", ".join(prods),
                            'hs_code': hs, 'certs': ", ".join(certs), 'website': web, 'comments': notes
                        }
                        # Using concat instead of append (future-proof)
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df)
                        st.success(f"Verified & Saved: {name} located at {city} ({lat}, {lon})")
                    else:
                        st.error("Error: Could not find the city location. Please check the spelling or format (City, Country).")
                else:
                    st.error("Supplier Name and City are mandatory fields.")

    with st.expander("🗑️ Remove Supplier"):
        target = st.selectbox("Select Supplier to Delete", ["None"] + list(df['name'].unique()))
        if st.button("Delete Permanently"):
            if target != "None":
                df = df[df['name'] != target]
                save_data(df)
                st.warning(f"Supplier '{target}' has been removed.")
                st.rerun()

# --- Module 3: Market Insights ---
elif menu == "Market Insights":
    st.title("📈 Market Intelligence & News")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Raw Material Tracking")
        st.write("Current polymer trends impact your FOB prices:")
        st.markdown("""
        - [PP Resin Prices](https://www.chemorbis.com/en/plastics-market/Polypropylene-PP)
        - [PE/HDPE Trends](https://www.platts.com)
        - [Shipping Freight Index (WCI)](https://www.drewry.co.uk/supply-chain-advisors/world-container-index-reporting)
        """)
        st.info("Tip: Share freight trends with logistics for better planning.")
    
    with col2:
        st.subheader("Industry News Feed")
        # Embedding the news site as requested
        components.iframe("https://www.geosyntheticnews.com.au/", height=800, scrolling=True)
