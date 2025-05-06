import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel("dummy_sales_data.xlsx", sheet_name="Dummy_Sales_Dashboard_Data", header=1)
    df.columns = [
        "Rep", "Company", "Customer", "Reported Sale Value", "Sale Month",
        "Sales Dept Status", "Actual Sale Value", "Payment 1", "Payment 2",
        "Payment 3", "Percentage Paid", "Invoice Number", "PI Number", "Actual Status"
    ]
    df["Sale Month"] = pd.to_datetime(df["Sale Month"], errors='coerce')
    numeric_cols = ["Reported Sale Value", "Actual Sale Value", "Payment 1", "Payment 2", "Payment 3", "Percentage Paid"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Filters")
selected_company = st.sidebar.selectbox("Select Company", options=["All"] + sorted(df["Company"].dropna().unique().tolist()))
date_range = st.sidebar.date_input("Select Sale Month Range", [])

# Filter logic
if selected_company != "All":
    df = df[df["Company"] == selected_company]
if len(date_range) == 2:
    df = df[(df["Sale Month"] >= pd.to_datetime(date_range[0])) & (df["Sale Month"] <= pd.to_datetime(date_range[1]))]

# KPI comparisons
df_monthly = df.copy()
df_monthly['Month'] = df_monthly['Sale Month'].dt.to_period('M')
monthly_summary = df_monthly.groupby('Month').agg({
    "Reported Sale Value": "sum",
    "Actual Sale Value": "sum",
    "Payment 1": "sum",
    "Payment 2": "sum",
    "Payment 3": "sum"
}).reset_index()
monthly_summary['Total Payments'] = monthly_summary['Payment 1'] + monthly_summary['Payment 2'] + monthly_summary['Payment 3']

if len(monthly_summary) >= 2:
    current = monthly_summary.iloc[-1]
    previous = monthly_summary.iloc[-2]
    def trend(val):
        return "📈" if val >= 0 else "📉"
    def delta(curr, prev):
        return f"{trend(curr-prev)} {curr - prev:,.0f}"
else:
    current = previous = {k: 0 for k in ['Reported Sale Value', 'Actual Sale Value', 'Total Payments']}
    def delta(curr, prev): return ""

# KPIs
st.title("📊 Sales Performance Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("💼 Reported Sales", f"Rs. {current['Reported Sale Value']:,.0f}", delta(current['Reported Sale Value'], previous['Reported Sale Value']))
col2.metric("✅ Actual Sales", f"Rs. {current['Actual Sale Value']:,.0f}", delta(current['Actual Sale Value'], previous['Actual Sale Value']))
col3.metric("💰 Cash Collected", f"Rs. {current['Total Payments']:,.0f}", delta(current['Total Payments'], previous['Total Payments']))

outstanding_amount = current['Actual Sale Value'] - current['Total Payments']
collection_ratio = (current['Total Payments'] / current['Actual Sale Value']) * 100 if current['Actual Sale Value'] > 0 else 0
col4, col5 = st.columns(2)
col4.metric("📉 Outstanding", f"Rs. {outstanding_amount:,.0f}")
col5.metric("📈 Collection Ratio", f"{collection_ratio:.2f}%")

# Chart Selector
st.markdown("### 📊 Chart Viewer")
chart_type = st.selectbox("Choose chart type:", ["Bar Chart", "Line Chart", "Pie Chart", "Heatmap"])

if chart_type == "Bar Chart":
    sales_summary = df.groupby("Company")[["Reported Sale Value", "Actual Sale Value"]].sum().reset_index()
    fig_sales = px.bar(sales_summary, x="Company", y=["Reported Sale Value", "Actual Sale Value"],
                       barmode='group', title="Reported vs Actual Sales", color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig_sales, use_container_width=True)

elif chart_type == "Line Chart":
    df["Total Payments"] = df[["Payment 1", "Payment 2", "Payment 3"]].sum(axis=1)
    payment_trend = df.groupby("Sale Month")["Total Payments"].sum().reset_index()
    fig_collections = px.line(payment_trend, x="Sale Month", y="Total Payments", markers=True,
                              title="Monthly Collections Trend", color_discrete_sequence=['green'])
    st.plotly_chart(fig_collections, use_container_width=True)

elif chart_type == "Pie Chart":
    payment_dist = df[["Payment 1", "Payment 2", "Payment 3"]].sum().reset_index()
    payment_dist.columns = ["Payment Stage", "Amount"]
    fig_payment = px.pie(payment_dist, names="Payment Stage", values="Amount",
                         title="Payment Stage Distribution", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_payment, use_container_width=True)

elif chart_type == "Heatmap":
    df["Total Payments"] = df[["Payment 1", "Payment 2", "Payment 3"]].sum(axis=1)
    df["Outstanding"] = df["Actual Sale Value"] - df["Total Payments"]
    outstanding_summary = df.groupby("Company")["Outstanding"].sum().reset_index()
    fig_heat = px.density_heatmap(outstanding_summary, x="Company", y="Outstanding",
                                  title="Outstanding by Company", nbinsx=10, color_continuous_scale="Reds")
    st.plotly_chart(fig_heat, use_container_width=True)

# Filterable Table Selector
st.markdown("### 🔎 Filterable Dataset Table")
table_view = st.selectbox("View data table:", ["None", "Raw Table", "Filtered Table"])

if table_view == "Raw Table":
    st.dataframe(df, use_container_width=True)
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    st.download_button(
        label="⬇️ Download data as Excel",
        data=buffer,
        file_name="filtered_sales_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download data as CSV",
        data=csv_data,
        file_name="filtered_sales_data.csv",
        mime="text/csv"
    )

elif table_view == "Filtered Table":
    col1, col2 = st.columns(2)
    with col1:
        filter_company = st.selectbox("Filter by Company", options=["All"] + sorted(df["Company"].unique()))
        if filter_company != "All":
            df = df[df["Company"] == filter_company]
    with col2:
        filter_rep = st.selectbox("Filter by Rep", options=["All"] + sorted(df["Rep"].unique()))
        if filter_rep != "All":
            df = df[df["Rep"] == filter_rep]

    min_sale = st.slider("Minimum Reported Sale Value", min_value=int(df["Reported Sale Value"].min()), max_value=int(df["Reported Sale Value"].max()), value=int(df["Reported Sale Value"].min()))
    df = df[df["Reported Sale Value"] >= min_sale]

    st.dataframe(df, use_container_width=True)

    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    st.download_button(
        label="⬇️ Download filtered data as Excel",
        data=buffer,
        file_name="filtered_table_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download filtered data as CSV",
        data=csv_data,
        file_name="filtered_table_data.csv",
        mime="text/csv"
    )
