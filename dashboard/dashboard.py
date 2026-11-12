
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import timedelta

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

    monthly_sales = pd.read_csv(
        BASE_DIR / "monthly_sales.csv"
    )

    delivery_data = pd.read_csv(
        BASE_DIR / "delivery_by_state.csv"
    )

    rfm_data = pd.read_csv(
        BASE_DIR / "rfm_summary.csv"
    )

    orders = pd.read_csv(
        DATA_DIR / "orders_dataset.csv"
    )

    customers = pd.read_csv(
        DATA_DIR / "customers_dataset.csv"
    )

    order_items = pd.read_csv(
        DATA_DIR / "order_items_dataset.csv"
    )

    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"],
        errors="coerce"
    )

    # Hanya menggunakan pesanan delivered
    delivered_orders = orders[
        orders["order_status"] == "delivered"
    ].copy()

    # Menggabungkan pesanan dengan pelanggan
    customer_orders = delivered_orders.merge(
        customers[
            ["customer_id", "customer_unique_id", "customer_state"]
        ],
        on="customer_id",
        how="left"
    )

    # Menggabungkan pesanan dengan order items
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

    sales_detail["order_month"] = (
        sales_detail["order_purchase_timestamp"]
        .dt.strftime("%Y-%m")
    )

    return (
        monthly_sales,
        delivery_data,
        rfm_data,
        customer_orders,
        sales_detail
    )


(
    monthly_sales,
    delivery_data,
    rfm_data,
    customer_orders,
    sales_detail
) = load_data()


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

# FILTER TANGGAL

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


# FILTER CUSTOMER STATE

delivery_visual = delivery_data[
    delivery_data["total_orders"] >= 100
].copy()

available_states = sorted(
    delivery_visual["customer_state"].dropna().unique()
)

selected_states = st.sidebar.multiselect(
    "Pilih Negara Bagian",
    options=available_states,
    default=available_states
)


# FILTER DATA PENJUALAN BERDASARKAN TANGGAL

filtered_sales_detail = sales_detail[
    (
        sales_detail["order_purchase_timestamp"].dt.date >= start_date
    ) &
    (
        sales_detail["order_purchase_timestamp"].dt.date <= end_date
    )
].copy()


# FILTER DATA PELANGGAN BERDASARKAN TANGGAL DAN WILAYAH

filtered_customer_orders = customer_orders[
    (
        customer_orders["order_purchase_timestamp"].dt.date >= start_date
    ) &
    (
        customer_orders["order_purchase_timestamp"].dt.date <= end_date
    ) &
    (
        customer_orders["customer_state"].isin(selected_states)
    )
].copy()


# FILTER DATA PENGIRIMAN BERDASARKAN WILAYAH

filtered_delivery = delivery_visual[
    delivery_visual["customer_state"].isin(selected_states)
].copy()


# AGREGASI PENJUALAN BULANAN BERDASARKAN FILTER TANGGAL

filtered_sales = (
    filtered_sales_detail
    .groupby("order_month")
    .agg(
        total_orders=("order_id", "nunique"),
        total_sales=("price", "sum")
    )
    .reset_index()
)


# ==========================================
# 5. DYNAMIC KPI
# ==========================================

# KPI PENJUALAN

total_sales = filtered_sales_detail["price"].sum()

total_orders = filtered_sales_detail["order_id"].nunique()


# KPI PELANGGAN

total_customers = (
    filtered_customer_orders["customer_unique_id"].nunique()
)


# KPI PENGIRIMAN

total_late_orders = filtered_delivery["late_orders"].sum()

total_delivery_orders = filtered_delivery["total_orders"].sum()

late_percentage = (
    total_late_orders / total_delivery_orders * 100
    if total_delivery_orders > 0
    else 0
)


# ==========================================
# 6. DISPLAY KPI
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
# 7. MONTHLY SALES PERFORMANCE
# ==========================================

st.header("📈 Monthly Sales Performance")

st.markdown("""
Visualisasi perkembangan jumlah pesanan dan total nilai
penjualan produk secara bulanan pada E-Commerce Olist.
""")

if not filtered_sales.empty:

    fig_sales = px.bar(
        filtered_sales,
        x="order_month",
        y="total_sales",
        labels={
            "order_month": "Month",
            "total_sales": "Sales Value (BRL)"
        },
        title="Monthly Product Sales Value",
        text_auto=".2s"
    )

    fig_sales.update_layout(
        xaxis_title="Month",
        yaxis_title="Sales Value (BRL)",
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_sales,
        use_container_width=True
    )

    fig_orders = px.line(
        filtered_sales,
        x="order_month",
        y="total_orders",
        markers=True,
        labels={
            "order_month": "Month",
            "total_orders": "Number of Orders"
        },
        title="Monthly Delivered Orders"
    )

    fig_orders.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Orders",
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_orders,
        use_container_width=True
    )

else:
    st.warning(
        "Tidak terdapat data penjualan pada rentang tanggal yang dipilih."
    )


# ==========================================
# 8. DELIVERY PERFORMANCE
# ==========================================

st.divider()

st.header("🚚 Delivery Performance by State")

st.markdown("""
Analisis performa pengiriman berdasarkan negara bagian
pelanggan di Brasil untuk mengidentifikasi wilayah
dengan tingkat keterlambatan pengiriman tertinggi.
""")

if not filtered_delivery.empty:

    top_delay_rate = (
        filtered_delivery
        .sort_values(
            by="late_percentage",
            ascending=False
        )
        .head(10)
    )

    fig_delay_rate = px.bar(
        top_delay_rate.sort_values("late_percentage"),
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
        use_container_width=True
    )

    top_avg_delay = (
        filtered_delivery
        .dropna(subset=["avg_delay_days"])
        .sort_values(
            by="avg_delay_days",
            ascending=False
        )
        .head(10)
    )

    if not top_avg_delay.empty:

        fig_avg_delay = px.bar(
            top_avg_delay.sort_values("avg_delay_days"),
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
            xaxis_title="Average Delivery Delay (Days)",
            yaxis_title="Customer State"
        )

        st.plotly_chart(
            fig_avg_delay,
            use_container_width=True
        )

else:
    st.warning(
        "Tidak terdapat data pengiriman pada wilayah yang dipilih."
    )


# ==========================================
# 9. CUSTOMER SEGMENTATION (RFM ANALYSIS)
# ==========================================

st.divider()

st.header("👥 Customer Segmentation (RFM Analysis)")

st.markdown("""
Analisis segmentasi pelanggan menggunakan metode
Recency, Frequency, dan Monetary (RFM) untuk memahami
perilaku pembelian dan kontribusi nilai pelanggan.
""")

rfm_visual = rfm_data.sort_values(
    by="Total_Customers",
    ascending=False
)


# CUSTOMER DISTRIBUTION

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
    template="plotly_white",
    yaxis_title="Customer Segment",
    xaxis_title="Number of Customers"
)

st.plotly_chart(
    fig_segment,
    use_container_width=True
)


# TOTAL MONETARY

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
    template="plotly_white",
    yaxis_title="Customer Segment",
    xaxis_title="Total Monetary (BRL)"
)

st.plotly_chart(
    fig_monetary,
    use_container_width=True
)


# AVERAGE MONETARY

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
    template="plotly_white",
    yaxis_title="Customer Segment",
    xaxis_title="Average Monetary (BRL)"
)

st.plotly_chart(
    fig_avg_monetary,
    use_container_width=True
)


# RFM SUMMARY TABLE

st.subheader("RFM Segment Summary")

st.dataframe(
    rfm_visual.round(2),
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 10. KEY BUSINESS INSIGHTS
# ==========================================

st.divider()

st.header("💡 Key Business Insights")

st.markdown("""
Ringkasan temuan utama berdasarkan hasil analisis
penjualan, pengiriman, dan segmentasi pelanggan.
""")

# SALES INSIGHT

sales_with_transactions = monthly_sales[
    monthly_sales["total_orders"] > 0
]

if not sales_with_transactions.empty:

    highest_sales = sales_with_transactions.loc[
        sales_with_transactions["total_sales"].idxmax()
    ]

    lowest_sales = sales_with_transactions.loc[
        sales_with_transactions["total_sales"].idxmin()
    ]

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📈 Sales Performance")

        st.metric(
            "Highest Sales Month",
            str(highest_sales["order_month"])
        )

        st.write(
            f"Total sales reached "
            f"**BRL {highest_sales['total_sales']:,.2f}** "
            f"with **{highest_sales['total_orders']:,.0f} orders**."
        )

    with col2:

        st.subheader("📉 Lowest Sales Month")

        st.metric(
            "Lowest Sales Month",
            str(lowest_sales["order_month"])
        )

        st.write(
            f"Total sales were "
            f"**BRL {lowest_sales['total_sales']:,.2f}** "
            f"with **{lowest_sales['total_orders']:,.0f} orders**."
        )


# DELIVERY INSIGHT

if not delivery_data.empty:

    highest_delay = delivery_data.loc[
        delivery_data["late_percentage"].idxmax()
    ]

    st.subheader("🚚 Delivery Performance")

    st.metric(
        "Highest Delay Rate",
        f"{highest_delay['late_percentage']:.2f}%"
    )

    st.write(
        f"The highest delay rate occurred in "
        f"**{highest_delay['customer_state']}**, "
        f"with {highest_delay['late_orders']:,.0f} delayed orders."
    )


# CUSTOMER INSIGHT

if not rfm_data.empty:

    largest_segment = rfm_data.loc[
        rfm_data["Total_Customers"].idxmax()
    ]

    highest_avg_monetary = rfm_data.loc[
        rfm_data["Avg_Monetary"].idxmax()
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
            f"of all analyzed customers."
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
# END OF DASHBOARD
# ==========================================

st.divider()

st.caption(
    "Olist E-Commerce Data Analysis Project | Dicoding"
)
