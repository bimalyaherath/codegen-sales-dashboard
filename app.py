import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# KPIs
st.title("📊 Sales Performance Dashboard")
st.markdown("""
<style>
.metric-label > div {
    font-size: 20px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

total_reported_sales = df["Reported Sale Value"].sum()
total_actual_sales = df["Actual Sale Value"].sum()
total_collections = df[["Payment 1", "Payment 2", "Payment 3"]].sum().sum()
outstanding_amount = total_actual_sales - total_collections
collection_ratio = (total_collections / total_actual_sales) * 100 if total_actual_sales > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("💼 Reported Sales", f"Rs. {total_reported_sales:,.0f}")
col2.metric("✅ Actual Sales", f"Rs. {total_actual_sales:,.0f}")
col3.metric("💰 Cash Collected", f"Rs. {total_collections:,.0f}")

col4, col5 = st.columns(2)
col4.metric("📉 Outstanding", f"Rs. {outstanding_amount:,.0f}")
col5.metric("📈 Collection Ratio", f"{collection_ratio:.2f}%")

# Additional Metrics by Company
st.markdown("### 🏢 Company-wise Sales Overview")
sales_summary = df.groupby("Company")[["Reported Sale Value", "Actual Sale Value"]].sum().reset_index()
fig_sales = px.bar(sales_summary, x="Company", y=["Reported Sale Value", "Actual Sale Value"],
                   barmode='group', title="Reported vs Actual Sales", color_discrete_sequence=px.colors.qualitative.Set2)
st.plotly_chart(fig_sales, use_container_width=True)

# Collections Over Time
st.markdown("### 📆 Monthly Collection Trends")
df["Total Payments"] = df[["Payment 1", "Payment 2", "Payment 3"]].sum(axis=1)
payment_trend = df.groupby("Sale Month")["Total Payments"].sum().reset_index()
fig_collections = px.area(payment_trend, x="Sale Month", y="Total Payments",
                          title="Cash Collections Over Time", color_discrete_sequence=['teal'])
st.plotly_chart(fig_collections, use_container_width=True)

# Payment distribution
st.markdown("### 💸 Payment Distribution")
payment_dist = df[["Payment 1", "Payment 2", "Payment 3"]].sum().reset_index()
payment_dist.columns = ["Payment Stage", "Amount"]
fig_payment = px.pie(payment_dist, names="Payment Stage", values="Amount",
                     title="Payment Stage Distribution", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
st.plotly_chart(fig_payment, use_container_width=True)

# Heatmap of Outstanding
st.markdown("### 🔥 Outstanding Heatmap by Company")
df["Outstanding"] = df["Actual Sale Value"] - df["Total Payments"]
outstanding_summary = df.groupby("Company")["Outstanding"].sum().reset_index()
fig_heat = px.density_heatmap(outstanding_summary, x="Company", y="Outstanding",
                              title="Outstanding by Company", nbinsx=10, color_continuous_scale="Reds")
st.plotly_chart(fig_heat, use_container_width=True)

# Expandable dataset view
st.markdown("### 📋 Raw Dataset Viewer")
with st.expander("🔽 Click to view full dataset with filters"):
    st.dataframe(df, use_container_width=True)
