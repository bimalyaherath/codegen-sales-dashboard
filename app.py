import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
df = pd.read_excel("dummy_sales_data.xlsx", skiprows=2)

# Strip spaces from column headers
df.columns = df.columns.str.strip()

# Debug: Show column names to verify formatting
st.write("Columns in Data:", df.columns.tolist())

# Parse date and add formatted month
df["Sale Month"] = pd.to_datetime(df["Sale Month"], format="%b-%Y")
df["YearMonth"] = df["Sale Month"].dt.strftime('%Y-%m')

# Sidebar filters
companies = df["Company"].unique()
selected_company = st.sidebar.selectbox("Select Company", ["All"] + list(companies))

if selected_company != "All":
    df = df[df["Company"] == selected_company]

# Title
st.title("Group Sales Dashboard")

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"{df['Sale Value'].sum():,.0f}")
col2.metric("Contracted Sales", f"{df[df['Status (Sales Dept)']=='Contract Signed']['Sale Value'].sum():,.0f}")
col3.metric("Cash Collected", f"{(df['1st payment'] + df['2nd payment'] + df['3rd payment']).sum():,.0f}")

col4, col5 = st.columns(2)
col4.metric("Outstanding", f"{(df['Sale Value'] - (df['1st payment'] + df['2nd payment'] + df['3rd payment'])).sum():,.0f}")
col5.metric("Closing Stock (dummy)", f"{df['Sale value (Actual)'].sum() / 10:,.0f}")

# Charts
st.plotly_chart(
    px.bar(df.groupby("Company")["Sale Value"].sum().reset_index(), 
           x="Company", y="Sale Value", title="Total Sales by Company"),
    use_container_width=True
)

st.plotly_chart(
    px.pie(df, values="Percentage paid from sales value", names="Company", 
           title="Payment Progress Distribution"),
    use_container_width=True
)

# Data Table
st.subheader("Detailed Sales Data")
st.dataframe(df)
