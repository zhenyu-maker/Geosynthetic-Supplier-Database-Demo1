import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="全球土工材料供应商数据库", layout="wide")

# --- 初始数据检查与加载 ---
def load_data():
    try:
        df = pd.read_csv("suppliers.csv")
    except FileNotFoundError:
        # 如果文件不存在，创建一个初始模板
        columns = ['name', 'country', 'est_year', 'address', 'lat', 'lon', 'products', 'hs_code', 'certificates', 'turnover', 'website', 'comments']
        df = pd.DataFrame(columns=columns)
        df.to_csv("suppliers.csv", index=False)
    return df

def save_data(df):
    df.to_csv("suppliers.csv", index=False)

# --- 抓取新闻函数 ---
def fetch_geo_news():
    try:
        url = "https://www.geosyntheticnews.com.au/"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 抓取最近的5个标题（根据该网站结构简单提取）
        news = []
        for item in soup.find_all('h3', limit=5):
            news.append(item.get_text().strip())
        return news
    except:
        return ["暂时无法获取实时新闻，请手动访问网站。"]

# --- 主程序开始 ---
df = load_data()

st.sidebar.title("🧭 导航栏")
menu = st.sidebar.radio("跳转至：", ["首页 & 供应商地图", "数据管理 (管理员)", "新闻动态"])

# --- 模块 1：首页 & 供应商地图 ---
if menu == "首页 & 供应商地图":
    st.title("🌍 全球土工材料供应商数据库")
    
    # 筛选器
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        search_name = st.text_input("搜索供应商名称")
    with col_s2:
        selected_cert = st.multiselect("按证书筛选", ["CE", "BBA", "AASHTO", "ASQUAL", "GB", "BIS", "UKCA", "NA"])

    # 过滤数据
    display_df = df.copy()
    if search_name:
        display_df = display_df[display_df['name'].str.contains(search_name, case=False)]
    if selected_cert:
        # 简单包含逻辑
        display_df = display_df[display_df['certificates'].apply(lambda x: any(c in str(x) for c in selected_cert))]

    # 列表展示
    st.dataframe(display_df, use_container_width=True)

    # 地图展示
    st.subheader("📍 供应商地理分布")
    if not display_df.empty:
        # 以第一行的坐标为中心，若无坐标则默认[0,0]
        m = folium.Map(location=[20, 0], zoom_start=2)
        for idx, row in display_df.iterrows():
            if pd.notnull(row['lat']) and pd.notnull(row['lon']):
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=f"<b>{row['name']}</b><br>{row['products']}",
                    tooltip=row['name']
                ).add_to(m)
        st_folium(m, width=1200, height=500)
    else:
        st.write("暂无包含坐标的数据。")

# --- 模块 2：数据管理 ---
elif menu == "数据管理 (管理员)":
    st.title("🛠 供应商数据维护")
    
    tab1, tab2 = st.tabs(["新增/修改供应商", "删除供应商"])
    
    with tab1:
        st.write("填写下方表格以增加新供应商或更新信息：")
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("供应商名称*")
            country = c2.text_input("国家")
            est_year = c3.text_input("创立年份")
            
            addr = st.text_input("详细地址")
            c4, c5 = st.columns(2)
            lat = c4.number_input("纬度 (Latitude)", format="%.6f")
            lon = c5.number_input("经度 (Longitude)", format="%.6f")
            
            prods = st.text_area("生产产品 (用逗号分隔)")
            hs = st.text_input("对应 HS Code")
            certs = st.multiselect("证书认证", ["CE", "BBA", "AASHTO", "ASQUAL", "GB", "BIS", "UKCA", "NA"])
            
            c6, c7 = st.columns(2)
            turnover = c6.text_input("年营业额")
            website = c7.text_input("公司网址")
            
            comments = st.text_area("采购部门评语")
            
            submitted = st.form_submit_button("保存到数据库")
            if submitted:
                if name:
                    new_data = {
                        'name': name, 'country': country, 'est_year': est_year, 
                        'address': addr, 'lat': lat, 'lon': lon,
                        'products': prods, 'hs_code': hs, 
                        'certificates': ", ".join(certs), 
                        'turnover': turnover, 'website': website, 'comments': comments
                    }
                    df = df.append(new_data, ignore_index=True)
                    save_data(df)
                    st.success(f"供应商 {name} 已成功保存！")
                else:
                    st.error("名称是必填项")

    with tab2:
        st.write("选择要删除的供应商：")
        delete_name = st.selectbox("选择名称", ["请选择"] + list(df['name'].unique()))
        if st.button("确认删除"):
            if delete_name != "请选择":
                df = df[df['name'] != delete_name]
                save_data(df)
                st.warning(f"{delete_name} 已从数据库移除")
                st.experimental_rerun()

# --- 模块 3：新闻动态 ---
elif menu == "新闻动态":
    st.title("📰 土工材料行业头条")
    st.write(f"数据源：[Geosynthetic News](https://www.geosyntheticnews.com.au/)")
    
    if st.button("刷新新闻"):
        news_list = fetch_geo_news()
        for idx, n in enumerate(news_list):
            st.info(f"**{idx+1}.** {n}")
