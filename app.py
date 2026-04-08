import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# --- Configuration & Styling ---
st.set_page_config(page_title="Global Geosynthetics Intelligence Hub", layout="wide")

# Product Options
PRODUCT_OPTIONS = [
    "Fiberglass Geogrid", "Woven PET Geogrid", "Knitted PET Geogrid", 
    "Geocell", "Woven PET Geotextile", "Woven PP Geotextile", 
    "Silt Tape PP", "Geotextile PP NW", "Geomembrane", "Geomat", 
    "Drainage board", "GCL", "GCCM", "Geogrid composite", 
    "Silt Fence", "Concrete Mattress", "Geotube", 
    "Rockbag PET/HDPE", "Vertical drainage", "Other"
]

CERT_OPTIONS = ["CE", "BBA", "AASHTO", "ASQUAL", "GB", "BIS", "UKCA", "NA"]
BU_OPTIONS = ["EU/Turkey/Africa", "Asia", "USA", "LATAM"]

# --- Geocoding Function ---
def get_coords(city_name):
    geolocator = Nominatim(user_agent="geosynthetics_procurement_app_v3")
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
        df = pd.read_csv("suppliers.csv")
        # Check if columns exist (for migration if you had an old csv)
        if 'bu' not in df.columns:
            df['bu'] = ""
        return df
    except FileNotFoundError:
        cols = ['name', 'country', 'city', 'lat', 'lon', 'products', 'certs', 'bu', 'website', 'comments', 'est_year']
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
    
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 1, 1])
    with col_f1:
        search_name = st.text_input("🔍 Search Supplier Name or Comments")
    with col_f2:
        filter_prod = st.multiselect("Filter by Product Category", PRODUCT_OPTIONS)
    with col_f3:
        filter_cert = st.multiselect("Filter by Cert", CERT_OPTIONS)
    with col_f4:
        filter_bu = st.multiselect("Filter by BU", BU_OPTIONS)

    # Filter Logic
    mask = df.copy()
    if search_name:
        mask = mask[mask.apply(lambda r: search_name.lower() in str(r).lower(), axis=1)]
    if filter_prod:
        mask = mask[mask['products'].apply(lambda x: any(p in str(x) for p in filter_prod))]
    if filter_cert:
        mask = mask[mask['certs'].apply(lambda x: any(c in str(x) for c in filter_cert))]
    if filter_bu:
        mask = mask[mask['bu'].apply(lambda x: any(b in str(x) for b in filter_bu))]

    tab_map, tab_data = st.tabs(["📍 Interactive Map", "📊 Data Table"])
    
    with tab_map:
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodbpositron")
        for _, row in mask.iterrows():
            if not pd.isna(row['lat']):
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=f"<b>{row['name']}</b><br>BU: {row['bu']}<br>Products: {row['products']}",
                    tooltip=f"{row['name']} ({row['city']})"
                ).add_to(m)
        st_folium(m, width="100%", height=600)

    with tab_data:
        st.dataframe(mask, use_container_width=True)

# --- Module 2: Supplier Management ---
elif menu == "Supplier Management":
    st.title("🛠 Database Administration")
    
    action = st.radio("Choose Action", ["Add New Supplier", "Modify Supplier Profile", "Remove Supplier"], horizontal=True)
    
    # 1. ADD NEW
    if action == "Add New Supplier":
        with st.form("add_form", clear_on_submit=True):
            st.subheader("Create New Entry")
            c1, c2 = st.columns(2)
            name = c1.text_input("Supplier Name*")
            city = c2.text_input("City & Country* (e.g., Shanghai, China)")
            
            prods = st.multiselect("Product Range", PRODUCT_OPTIONS)
            certs = st.multiselect("Certifications", CERT_OPTIONS)
            bus = st.multiselect("Covered BU", BU_OPTIONS)
            
            c3, c4 = st.columns(2)
            web = c3.text_input("Official Website")
            est = c4.text_input("Est. Year")
            
            notes = st.text_area("Procurement Team Feedback")
            
            if st.form_submit_button("Save Supplier"):
                if name and city:
                    lat, lon = get_coords(city)
                    if lat:
                        new_row = {
                            'name': name, 'country': city.split(',')[-1].strip(), 'city': city,
                            'lat': lat, 'lon': lon, 'products': ", ".join(prods),
                            'certs': ", ".join(certs), 'bu': ", ".join(bus), 
                            'website': web, 'comments': notes, 'est_year': est
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df)
                        st.success(f"Added: {name}")
                        st.rerun()
                    else:
                        st.error("Location not found.")
                else:
                    st.error("Required fields missing.")

    # 2. MODIFY EXISTING
    elif action == "Modify Supplier Profile":
        st.subheader("Edit Existing Entry")
        target_name = st.selectbox("Select Supplier to Modify", ["None"] + list(df['name'].unique()))
        
        if target_name != "None":
            # Get current data
            s_data = df[df['name'] == target_name].iloc[0]
            
            with st.form("edit_form"):
                e_name = st.text_input("Supplier Name", value=s_data['name'])
                e_city = st.text_input("City & Country", value=s_data['city'])
                
                # Pre-select existing tags
                current_prods = [p.strip() for p in str(s_data['products']).split(',')] if pd.notna(s_data['products']) else []
                current_certs = [c.strip() for c in str(s_data['certs']).split(',')] if pd.notna(s_data['certs']) else []
                current_bus = [b.strip() for b in str(s_data['bu']).split(',')] if pd.notna(s_data['bu']) else []
                
                e_prods = st.multiselect("Product Range", PRODUCT_OPTIONS, default=[p for p in current_prods if p in PRODUCT_OPTIONS])
                e_certs = st.multiselect("Certifications", CERT_OPTIONS, default=[c for c in current_certs if c in CERT_OPTIONS])
                e_bus = st.multiselect("Covered BU", BU_OPTIONS, default=[b for b in current_bus if b in BU_OPTIONS])
                
                e_web = st.text_input("Website", value=s_data['website'])
                e_est = st.text_input("Est. Year", value=s_data['est_year'])
                e_notes = st.text_area("Procurement Feedback", value=s_data['comments'])
                
                if st.form_submit_button("Update Profile"):
                    # Update row
                    idx = df[df['name'] == target_name].index[0]
                    
                    # If city changed, re-geocode
                    new_lat, new_lon = s_data['lat'], s_data['lon']
                    if e_city != s_data['city']:
                        new_lat, new_lon = get_coords(e_city)
                    
                    df.at[idx, 'name'] = e_name
                    df.at[idx, 'city'] = e_city
                    df.at[idx, 'lat'] = new_lat
                    df.at[idx, 'lon'] = new_lon
                    df.at[idx, 'products'] = ", ".join(e_prods)
                    df.at[idx, 'certs'] = ", ".join(e_certs)
                    df.at[idx, 'bu'] = ", ".join(e_bus)
                    df.at[idx, 'website'] = e_web
                    df.at[idx, 'est_year'] = e_est
                    df.at[idx, 'comments'] = e_notes
                    
                    save_data(df)
                    st.success("Profile Updated!")
                    st.rerun()

    # 3. REMOVE
    elif action == "Remove Supplier":
        st.subheader("Delete Entry")
        target = st.selectbox("Select Supplier", ["None"] + list(df['name'].unique()))
        if st.button("Delete Permanently"):
            if target != "None":
                df = df[df['name'] != target]
                save_data(df)
                st.warning(f"Deleted {target}")
                st.rerun()

# --- Module 3: Market Insights ---
elif menu == "Market Insights":
    st.title("📈 Market Intelligence")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("Global Pricing Reference")
        st.markdown("""
        - [PP/PE Prices](https://www.chemorbis.com)
        - [Freight Cost (WCI)](https://www.drewry.co.uk)
        """)
    with col2:
        components.iframe("https://www.geosyntheticnews.com.au/", height=800, scrolling=True)
