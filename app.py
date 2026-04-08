import streamlit as st
import pandas as pd

# 设置网页标题和布局
st.set_page_config(page_title="全球土工材料供应商数据库", layout="wide")

st.title("🌍 全球土工材料供应商归档系统")
st.markdown("用于内部归档、筛选供应商生产能力及政策影响。")

# 1. 加载数据
@st.cache_data
def load_data():
    # 实际部署时，这里可以读取本地 csv 或 GitHub 上的链接
    df = pd.read_csv("suppliers.csv")
    return df

try:
    df = load_data()

    # 2. 侧边栏筛选器
    st.sidebar.header("筛选条件")
    
    # 按地区筛选
    region_list = ["全部"] + list(df['region'].unique())
    selected_region = st.sidebar.selectbox("选择地区", region_list)

    # 按产品筛选
    product_list = ["全部"] + list(df['product'].unique())
    selected_product = st.sidebar.selectbox("选择产品类型", product_list)

    # 关键字搜索
    search_query = st.sidebar.text_input("关键字搜索 (如证书、特点)")

    # 3. 数据过滤逻辑
    filtered_df = df.copy()
    if selected_region != "全部":
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    if selected_product != "全部":
        filtered_df = filtered_df[filtered_df['product'] == selected_product]
    if search_query:
        filtered_df = filtered_df[
            filtered_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().values, axis=1)
        ]

    # 4. 展示结果
    st.subheader(f"找到 {len(filtered_df)} 个匹配的供应商")
    
    # 增强版表格展示
    st.dataframe(filtered_df, use_container_width=True)

    # 5. 详细查看（点击选择某一行展示详情）
    if not filtered_df.empty:
        st.divider()
        selected_name = st.selectbox("选择一个供应商查看详细报告：", filtered_df['name'])
        detail = filtered_df[filtered_df['name'] == selected_name].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**产品能力:** {detail['product']}")
            st.warning(f"**关税影响:** {detail['tariff_impact']}")
        with col2:
            st.success(f"**证书资质:** {detail['certificate']}")
            st.write(f"**特殊点:** {detail['notable_features']}")

except FileNotFoundError:
    st.error("请确保 suppliers.csv 文件与 app.py 在同一目录下。")