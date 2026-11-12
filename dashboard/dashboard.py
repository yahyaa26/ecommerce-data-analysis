
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Olist E-Commerce Analytics",
    page_icon="🛒",
    layout="wide"
)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data"


# ==========================================
# 2. LOAD DATA
# ==========================================

@st.cache_data
def load_data():

    orders = pd.read_csv(
        DATA_DIR / "orders_dataset.csv"
    )

    customers = pd.read_csv(
        DATA_DIR / "customers_dataset.csv"
    )

    order_items = pd.read_csv(
        DATA_DIR / "order_items_dataset.csv"
    )

    # Convert date columns
    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]

    for column in date_columns:
        if column in orders.columns:
            orders[column] = pd.to_datetime(
                orders[column],
                errors="coerce"
            )

    # Only delivered orders
    delivered_orders = orders[
        orders["order_status"] == "delivered"
    ].copy()

    # Merge customer information
    customer_orders = delivered_orders.merge(
        customers[
            ["customer_id", "customer_unique_id", "customer_state"]
        ],
        on="customer_id",
        how="left"
    )

    # Merge product prices
    sales_detail = delivered_orders.merge(
        order_items[["order_id", "price"]],
        on="order_id",
        how="inner"
    )

    sales_detail = sales_detail.merge(
        customers[
            ["customer_id", "customer_unique_id", "customer_state"]
        ],
        on="customer_id",
        how="left"
    )

    # Monthly column
    sales_detail["order_month"] = (
        sales_detail["order_purchase_timestamp"]
        .dt.strftime("%Y-%m")
    )

    return customer_orders, sales_detail


customer_orders, sales_detail = load_data()


# ==========================================
# 3. DASHBOARD HEADER
# ==========================================

st.title("🛒 Olist E-Commerce Analytics Dashboard")

st.markdown("""
Dashboard ini menyajikan hasil analisis data E-Commerce Olist,
meliputi performa penjualan, pengiriman, dan segmentasi pelanggan
berdasarkan metode RFM.
""")

st.divider()


# ==========================================
# 4. GLOBAL FILTER
# ==========================================

st.sidebar.header("Dashboard Filters")

# DATE FILTER

min_date = sales_detail[
    "order_purchase_timestamp"
].min().date()

max_date = sales_detail[
    "order_purchase_timestamp"
].max().date()

selected_dates = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(selected_dates) != 2:
    st.warning("Silakan pilih tanggal awal dan tanggal akhir.")
    st.stop()

start_date, end_date = selected_dates

if start_date > end_date:
    st.error("Tanggal awal tidak boleh melebihi tanggal akhir.")
    st.stop()


# STATE FILTER

available_states = sorted(
    customer_orders["customer_state"]
    .dropna()
    .unique()
)

selected_states = st.sidebar.multiselect(
    "Pilih Negara Bagian",
    options=available_states,
    default=available_states
)


# ==========================================
# 5. APPLY GLOBAL FILTER
# ==========================================

# SALES FILTER

filtered_sales_detail = sales_detail[
    (sales_detail["order_purchase_timestamp"].dt.date >= start_date) &
    (sales_detail["order_purchase_timestamp"].dt.date <= end_date) &
    (sales_detail["customer_state"].isin(selected_states))
].copy()


# CUSTOMER FILTER

filtered_customer_orders = customer_orders[
    (customer_orders["order_purchase_timestamp"].dt.date >= start_date) &
    (customer_orders["order_purchase_timestamp"].dt.date <= end_date) &
    (customer_orders["customer_state"].isin(selected_states))
].copy()


# DELIVERY FILTER

filtered_delivery = filtered_customer_orders.copy()

# Calculate delivery duration
filtered_delivery["delivery_duration"] = (
    filtered_delivery["order_delivered_customer_date"] -
    filtered_delivery["order_purchase_timestamp"]
).dt.total_seconds() / 86400

# Calculate delivery delay
filtered_delivery["delay_days"] = (
    filtered_delivery["order_delivered_customer_date"] -
    filtered_delivery["order_estimated_delivery_date"]
).dt.total_seconds() / 86400

filtered_delivery["is_late"] = (
    filtered_delivery["delay_days"] > 0
)


# ==========================================
# 6. DYNAMIC KPI
# ==========================================

total_sales = filtered_sales_detail["price"].sum()

total_orders = (
    filtered_sales_detail["order_id"].nunique()
)

total_customers = (
    filtered_customer_orders["customer_unique_id"].nunique()
)

total_late_orders = (
    filtered_delivery["is_late"].sum()
)

total_delivery_orders = (
    filtered_delivery["order_id"].nunique()
)

late_percentage = (
    total_late_orders / total_delivery_orders * 100
    if total_delivery_orders > 0
    else 0
)


# ==========================================
# 7. DISPLAY KPI
# ==========================================

st.header("📊 Business Performance Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Sales",
    f"BRL {total_sales:,.2f}"
)

col2.metric(
    "Total Orders",
    f"{total_orders:,.0f}"
)

col3.metric(
    "Total Customers",
    f"{total_customers:,.0f}"
)

col4.metric(
    "Delivery Delay Rate",
    f"{late_percentage:.2f}%"
)

st.caption(
    f"Sales Period: {start_date} to {end_date} "
    f"| Selected States: {len(selected_states)}"
)

st.divider()


# ==========================================
# 8. MONTHLY SALES PERFORMANCE
# ==========================================

st.header("📈 Monthly Sales Performance")

st.markdown("""
Visualisasi perkembangan jumlah pesanan dan total nilai
penjualan produk secara bulanan pada E-Commerce Olist.
""")

filtered_sales = (
    filtered_sales_detail
    .groupby("order_month")
    .agg(
        total_orders=("order_id", "nunique"),
        total_sales=("price", "sum")
    )
    .reset_index()
    .sort_values("order_month")
)

if not filtered_sales.empty:

    fig_sales = px.bar(
        filtered_sales,
        x="order_month",
        y="total_sales",
        text="total_sales",
        title="Monthly Product Sales Value",
        labels={
            "order_month": "Month",
            "total_sales": "Sales Value (BRL)"
        }
    )

    fig_sales.update_traces(
        texttemplate="BRL %{text:,.0f}",
        textposition="outside"
    )

    fig_sales.update_layout(
        template="plotly_white",
        xaxis_title="Month",
        yaxis_title="Sales Value (BRL)",
        xaxis_type="category"
    )

    st.plotly_chart(
        fig_sales,
        width="stretch"
    )

    fig_orders = px.line(
        filtered_sales,
        x="order_month",
        y="total_orders",
        markers=True,
        title="Monthly Delivered Orders",
        labels={
            "order_month": "Month",
            "total_orders": "Number of Orders"
        }
    )

    fig_orders.update_layout(
        template="plotly_white",
        xaxis_title="Month",
        yaxis_title="Number of Orders",
        xaxis_type="category"
    )

    st.plotly_chart(
        fig_orders,
        width="stretch"
    )

else:
    st.info("Tidak terdapat data penjualan pada filter yang dipilih.")


# ==========================================
# 9. DELIVERY PERFORMANCE
# ==========================================

st.divider()

st.header("🚚 Delivery Performance by State")

st.markdown("""
Analisis performa pengiriman berdasarkan negara bagian
pelanggan di Brasil.
""")

if not filtered_delivery.empty:

    delivery_summary = (
        filtered_delivery
        .groupby("customer_state")
        .agg(
            total_orders=("order_id", "nunique"),
            late_orders=("is_late", "sum"),
            avg_delivery_duration=("delivery_duration", "mean"),
            avg_delay_days=(
                "delay_days",
                lambda x: x[x > 0].mean()
            )
        )
        .reset_index()
    )

    delivery_summary["late_percentage"] = (
        delivery_summary["late_orders"] /
        delivery_summary["total_orders"] * 100
    )

    delivery_summary["avg_delay_days"] = (
        delivery_summary["avg_delay_days"].fillna(0)
    )

    # Delivery delay rate
    top_delay_rate = (
        delivery_summary
        .sort_values(
            "late_percentage",
            ascending=False
        )
        .head(10)
        .sort_values("late_percentage")
    )

    fig_delay_rate = px.bar(
        top_delay_rate,
        x="late_percentage",
        y="customer_state",
        orientation="h",
        text="late_percentage",
        title="Top 10 States with Highest Delivery Delay Rate",
        labels={
            "late_percentage": "Delivery Delay Rate (%)",
            "customer_state": "Customer State"
        }
    )

    fig_delay_rate.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside"
    )

    fig_delay_rate.update_layout(
        template="plotly_white",
        xaxis_title="Delivery Delay Rate (%)",
        yaxis_title="Customer State"
    )

    st.plotly_chart(
        fig_delay_rate,
        width="stretch"
    )

    # Average delivery delay
    top_avg_delay = (
        delivery_summary
        .sort_values(
            "avg_delay_days",
            ascending=False
        )
        .head(10)
        .sort_values("avg_delay_days")
    )

    fig_avg_delay = px.bar(
        top_avg_delay,
        x="avg_delay_days",
        y="customer_state",
        orientation="h",
        text="avg_delay_days",
        title="Top 10 States with Highest Average Delivery Delay",
        labels={
            "avg_delay_days": "Average Delay (Days)",
            "customer_state": "Customer State"
        }
    )

    fig_avg_delay.update_traces(
        texttemplate="%{text:.2f} days",
        textposition="outside"
    )

    fig_avg_delay.update_layout(
        template="plotly_white",
        xaxis_title="Average Delay (Days)",
        yaxis_title="Customer State"
    )

    st.plotly_chart(
        fig_avg_delay,
        width="stretch"
    )

else:
    delivery_summary = pd.DataFrame()

    st.info("Tidak terdapat data pengiriman pada filter yang dipilih.")


# ==========================================
# 10. CUSTOMER SEGMENTATION (RFM ANALYSIS)
# ==========================================

st.divider()

st.header("👥 Customer Segmentation (RFM Analysis)")

st.markdown("""
Analisis segmentasi pelanggan menggunakan metode
Recency, Frequency, dan Monetary (RFM) berdasarkan
transaksi dalam periode dan wilayah yang dipilih.
""")

if not filtered_sales_detail.empty:

    # Aggregate customer metrics (same calculation as notebook Cell 62)
    customer_rfm = (
        filtered_sales_detail
        .groupby("customer_unique_id")
        .agg(
            last_purchase=("order_purchase_timestamp", "max"),
            Frequency=("order_id", "nunique"),
            Monetary=("price", "sum")
        )
        .reset_index()
    )

    # Reference date based on the latest transaction in the filtered data
    reference_date = (
        filtered_sales_detail["order_purchase_timestamp"].max()
        + pd.Timedelta(days=1)
    )

    customer_rfm["Recency"] = (
        reference_date - customer_rfm["last_purchase"]
    ).dt.days

    # RFM scoring: exactly follow notebook Cell 63
    # R Score: lower Recency receives a higher score
    customer_rfm["R_Score"] = np.ceil(
        (1 - customer_rfm["Recency"].rank(
            method="average",
            pct=True
        )) * 5
    ).clip(1, 5).astype(int)

    # F Score: customers with the same order frequency receive the same score
    customer_rfm["F_Score"] = pd.cut(
        customer_rfm["Frequency"],
        bins=[0, 1, 2, 3, 5, np.inf],
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    # M Score: higher Monetary receives a higher score
    customer_rfm["M_Score"] = np.ceil(
        customer_rfm["Monetary"].rank(
            method="average",
            pct=True
        ) * 5
    ).clip(1, 5).astype(int)

    # Combine R, F, and M scores
    customer_rfm["RFM_Score"] = (
        customer_rfm["R_Score"].astype(str) +
        customer_rfm["F_Score"].astype(str) +
        customer_rfm["M_Score"].astype(str)
    )

    # Customer segmentation: exactly follow notebook Cell 64
    conditions = [
        (
            (customer_rfm["R_Score"] >= 4) &
            (customer_rfm["F_Score"] >= 3) &
            (customer_rfm["M_Score"] >= 4)
        ),
        (
            (customer_rfm["R_Score"] >= 3) &
            (customer_rfm["F_Score"] >= 3) &
            (customer_rfm["M_Score"] >= 3)
        ),
        (
            (customer_rfm["R_Score"] <= 2) &
            (customer_rfm["F_Score"] >= 3)
        ),
        (
            (customer_rfm["R_Score"] >= 4) &
            (customer_rfm["F_Score"] <= 2) &
            (customer_rfm["M_Score"] >= 3)
        ),
        (
            (customer_rfm["R_Score"] >= 4) &
            (customer_rfm["F_Score"] == 1) &
            (customer_rfm["M_Score"] < 3)
        )
    ]

    segment_names = [
        "Champions",
        "Loyal Customers",
        "At Risk",
        "Potential Loyalists",
        "Recent Customers"
    ]

    customer_rfm["Customer_Segment"] = np.select(
        conditions,
        segment_names,
        default="Others"
    )

    # Segment summary
    rfm_summary = (
        customer_rfm
        .groupby("Customer_Segment", observed=False)
        .agg(
            Total_Customers=("customer_unique_id", "nunique"),
            Avg_Recency=("Recency", "mean"),
            Avg_Frequency=("Frequency", "mean"),
            Avg_Monetary=("Monetary", "mean"),
            Total_Monetary=("Monetary", "sum")
        )
        .reset_index()
    )

    rfm_summary["Customer_Percentage"] = (
        rfm_summary["Total_Customers"] /
        rfm_summary["Total_Customers"].sum() * 100
    )

    rfm_visual = rfm_summary.sort_values(
        "Total_Customers",
        ascending=False
    )

    # Customer distribution
    fig_segment = px.bar(
        rfm_visual.sort_values("Total_Customers"),
        x="Total_Customers",
        y="Customer_Segment",
        orientation="h",
        text="Total_Customers",
        title="Customer Distribution by Segment",
        labels={
            "Total_Customers": "Number of Customers",
            "Customer_Segment": "Customer Segment"
        }
    )

    fig_segment.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig_segment.update_layout(
        template="plotly_white"
    )

    st.plotly_chart(
        fig_segment,
        width="stretch"
    )

    # Total monetary
    fig_monetary = px.bar(
        rfm_visual.sort_values("Total_Monetary"),
        x="Total_Monetary",
        y="Customer_Segment",
        orientation="h",
        text="Total_Monetary",
        title="Total Purchase Value by Customer Segment",
        labels={
            "Total_Monetary": "Total Monetary (BRL)",
            "Customer_Segment": "Customer Segment"
        }
    )

    fig_monetary.update_traces(
        texttemplate="BRL %{text:,.0f}",
        textposition="outside"
    )

    fig_monetary.update_layout(
        template="plotly_white"
    )

    st.plotly_chart(
        fig_monetary,
        width="stretch"
    )

    # Average monetary
    fig_avg_monetary = px.bar(
        rfm_visual.sort_values("Avg_Monetary"),
        x="Avg_Monetary",
        y="Customer_Segment",
        orientation="h",
        text="Avg_Monetary",
        title="Average Purchase Value per Customer",
        labels={
            "Avg_Monetary": "Average Monetary (BRL)",
            "Customer_Segment": "Customer Segment"
        }
    )

    fig_avg_monetary.update_traces(
        texttemplate="BRL %{text:,.2f}",
        textposition="outside"
    )

    fig_avg_monetary.update_layout(
        template="plotly_white"
    )

    st.plotly_chart(
        fig_avg_monetary,
        width="stretch"
    )

    # RFM table
    st.subheader("RFM Segment Summary")

    st.dataframe(
        rfm_visual.round(2),
        width="stretch",
        hide_index=True
    )

else:
    customer_rfm = pd.DataFrame()
    rfm_summary = pd.DataFrame()

    st.info("Tidak terdapat data pelanggan pada filter yang dipilih.")


# ==========================================
# 11. KEY BUSINESS INSIGHTS
# ==========================================

st.divider()

st.header("💡 Key Business Insights")

st.markdown("""
Ringkasan temuan berdasarkan filter tanggal dan
negara bagian yang dipilih.
""")

# SALES INSIGHT

if not filtered_sales.empty:

    highest_sales = filtered_sales.loc[
        filtered_sales["total_sales"].idxmax()
    ]

    lowest_sales = filtered_sales.loc[
        filtered_sales["total_sales"].idxmin()
    ]

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📈 Highest Sales")

        st.metric(
            "Highest Sales Month",
            highest_sales["order_month"]
        )

        st.write(
            f"Total sales: **BRL {highest_sales['total_sales']:,.2f}** "
            f"with **{highest_sales['total_orders']:,.0f} orders**."
        )

    with col2:

        st.subheader("📉 Lowest Sales")

        st.metric(
            "Lowest Sales Month",
            lowest_sales["order_month"]
        )

        st.write(
            f"Total sales: **BRL {lowest_sales['total_sales']:,.2f}** "
            f"with **{lowest_sales['total_orders']:,.0f} orders**."
        )


# DELIVERY INSIGHT

if not delivery_summary.empty:

    highest_delay = delivery_summary.loc[
        delivery_summary["late_percentage"].idxmax()
    ]

    st.subheader("🚚 Delivery Performance")

    st.metric(
        "Highest Delivery Delay Rate",
        f"{highest_delay['late_percentage']:.2f}%"
    )

    st.write(
        f"The highest delay rate occurred in "
        f"**{highest_delay['customer_state']}**, "
        f"with {highest_delay['late_orders']:,.0f} delayed orders."
    )


# CUSTOMER INSIGHT

if not rfm_summary.empty:

    largest_segment = rfm_summary.loc[
        rfm_summary["Total_Customers"].idxmax()
    ]

    highest_avg_monetary = rfm_summary.loc[
        rfm_summary["Avg_Monetary"].idxmax()
    ]

    col3, col4 = st.columns(2)

    with col3:

        st.subheader("👥 Largest Customer Segment")

        st.metric(
            "Customer Segment",
            largest_segment["Customer_Segment"]
        )

        st.write(
            f"This segment contains "
            f"**{largest_segment['Total_Customers']:,.0f} customers**, "
            f"representing "
            f"**{largest_segment['Customer_Percentage']:.2f}%** "
            f"of filtered customers."
        )

    with col4:

        st.subheader("💰 Highest Average Monetary")

        st.metric(
            "Customer Segment",
            highest_avg_monetary["Customer_Segment"]
        )

        st.write(
            f"Average purchase value: "
            f"**BRL {highest_avg_monetary['Avg_Monetary']:,.2f}** "
            f"per customer."
        )


# ==========================================
# 12. FOOTER
# ==========================================

st.divider()

st.caption(
    "Olist E-Commerce Data Analysis Project | Dicoding"
)
