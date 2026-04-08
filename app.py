import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(page_title="Global Geosynthetics Database", layout="wide")

# --- Data Handling ---
def load_data():
    try:
        df = pd.read_csv("suppliers.csv")
    except FileNotFoundError:
        columns = ['name', 'country', 'est_year', 'address', 'lat', 'lon', 'products', 'hs_code', 'certificates', 'turnover', 'website', 'comments']
        df = pd.DataFrame(columns=columns)
        df.to_csv("suppliers.csv", index=False)
    return df

def save_data(df):
    df.to_csv("suppliers.csv", index=False)

df = load_data()

# --- Sidebar Navigation ---
st.sidebar.title("🌍 Global Sourcing Hub")
menu = st.sidebar.radio("Navigation", ["Dashboard & Map", "Supplier Management", "Market News & Trends"])

# --- Module 1: Dashboard & Map ---
if menu == "Dashboard & Map":
    st.title("📊 Supplier Intelligence Dashboard")
    
    # Quick Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Suppliers", len(df))
    c2.metric("Regions Covered", len(df['country'].unique()) if not df.empty else 0)
    c3.metric("Key Certification", "CE/BBA/ASQUAL")

    st.divider()

    # Search and Filter
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_query = st.text_input("🔍 Search by Supplier Name or Product")
    with col_f2:
        cert_filter = st.multiselect("Filter by Certification", ["CE", "BBA", "AASHTO", "ASQUAL", "GB", "BIS", "UKCA", "NA"])

    # Filtering Logic
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().values, axis=1)]
    if cert_filter:
        filtered_df = filtered_df[filtered_df['certificates'].apply(lambda x: any(c in str(x) for c in cert_filter))]

    # Main View: Table and Map
    tab_list, tab_map = st.tabs(["📋 Supplier List", "📍 Geographic View"])
    
    with tab_list:
        st.dataframe(filtered_df, use_container_width=True)

    with tab_map:
        if not filtered_df.empty:
            m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodbpositron")
            for idx, row in filtered_df.iterrows():
                if pd.notnull(row['lat']) and pd.notnull(row['lon']):
                    folium.Marker(
                        [row['lat'], row['lon']],
                        popup=f"<b>{row['name']}</b><br>{row['products']}",
                        tooltip=row['name']
                    ).add_to(m)
            st_folium(m, width=1200, height=500)
        else:
            st.warning("No location data available for the current selection.")

# --- Module 2: Supplier Management ---
elif menu == "Supplier Management":
    st.title("🛠 Database Administration")
    
    action = st.selectbox("Action", ["Add New Supplier", "Edit/Delete Existing"])
    
    if action == "Add New Supplier":
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Supplier Name*")
            website = col2.text_input("Official Website")
            
            products = st.text_area("Product Range (e.g., Geogrid, HDPE Geomembrane)")
            
            col3, col4, col5 = st.columns(3)
            country = col3.text_input("Country")
            hs_code = col4.text_input("HS Code")
            est_year = col5.text_input("Established Year")
            
            col6, col7 = st.columns(2)
            lat = col6.number_input("Latitude (for Map)", format="%.6f")
            lon = col7.number_input("Longitude (for Map)", format="%.6f")
            
            certs = st.multiselect("Certifications", ["CE", "BBA", "AASHTO", "ASQUAL", "GB", "BIS", "UKCA", "NA"])
            comments = st.text_area("Procurement Team Feedback")
            
            if st.form_submit_button("Save to Database"):
                if name:
                    new_entry = {
                        'name': name, 'country': country, 'est_year': est_year, 
                        'address': "", 'lat': lat, 'lon': lon,
                        'products': products, 'hs_code': hs_code, 
                        'certificates': ", ".join(certs), 
                        'turnover': "", 'website': website, 'comments': comments
                    }
                    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                    save_data(df)
                    st.success(f"Supplier '{name}' added successfully!")
                else:
                    st.error("Supplier Name is required.")

    else:
        st.write("### Remove a Supplier")
        to_delete = st.selectbox("Select Supplier to Remove", ["None"] + list(df['name'].unique()))
        if st.button("Confirm Deletion"):
            if to_delete != "None":
                df = df[df['name'] != to_delete]
                save_data(df)
                st.rerun()

# --- Module 3: Market News ---
elif menu == "Market News & Trends":
    st.title("📰 Industry News Feed")
    st.write("Source: Geosynthetic News Australia")
    
    # Using iframe to embed the actual website
    components.iframe("https://www.geosyntheticnews.com.au/", height=800, scrolling=True)
