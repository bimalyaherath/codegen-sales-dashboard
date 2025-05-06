import streamlit as st
import pandas as pd
import plotly.express as px

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
st.sidebar.header("Filters")
selected_company = st.sidebar.selectbox("Select Company", options=["All"] + sorted(df["Company"].dropna().unique().tolist()))
date_range = st.sidebar.date_input("Select Sale Month Range", [])

# Filter logic
if selected_company != "All":
    df = df[df["Company"] == selected_company]
if len(date_range) == 2:
    df = df[(df["Sale Month"] >= pd.to_datetime(date_range[0])) & (df["Sale Month"] <= pd.to_datetime(date_range[1]))]

# KPIs
st.title("Sales Dashboard")
st.markdown("### Summary Metrics")
total_reported_sales = df["Reported Sale Value"].sum()
total_actual_sales = df["Actual Sale Value"].sum()
total_collections = df[["Payment 1", "Payment 2", "Payment 3"]].sum().sum()
outstanding_amount = total_actual_sales - total_collections
collection_ratio = (total_collections / total_actual_sales) * 100 if total_actual_sales > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Reported Sales", f"Rs. {total_reported_sales:,.0f}")
col2.metric("Actual Sales", f"Rs. {total_actual_sales:,.0f}")
col3.metric("Cash Collected", f"Rs. {total_collections:,.0f}")

col4, col5 = st.columns(2)
col4.metric("Outstanding", f"Rs. {outstanding_amount:,.0f}")
col5.metric("Collection Ratio", f"{collection_ratio:.2f}%")

# Charts
st.markdown("### Reported vs Actual Sales")
sales_summary = df.groupby("Company")[["Reported Sale Value", "Actual Sale Value"]].sum().reset_index()
fig_sales = px.bar(sales_summary, x="Company", y=["Reported Sale Value", "Actual Sale Value"], barmode='group', title="Company-wise Sales")
st.plotly_chart(fig_sales, use_container_width=True)

st.markdown("### Collections Over Time")
df["Total Payments"] = df[["Payment 1", "Payment 2", "Payment 3"]].sum(axis=1)
payment_trend = df.groupby("Sale Month")["Total Payments"].sum().reset_index()
fig_collections = px.line(payment_trend, x="Sale Month", y="Total Payments", markers=True, title="Monthly Collections")
st.plotly_chart(fig_collections, use_container_width=True)
