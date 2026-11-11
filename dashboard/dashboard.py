
import streamlit as st
import pandas as pd
import plotly.express as px

from pathlib import Path

# Konfigurasi halaman
st.set_page_config(
    page_title="Olist E-Commerce Analytics",
    page_icon="🛒",
    layout="wide"
)

# Lokasi file
BASE_DIR = Path(__file__).parent

# Membaca dataset hasil analisis
monthly_sales = pd.read_csv(
    BASE_DIR / "monthly_sales.csv"
)

delivery_data = pd.read_csv(
    BASE_DIR / "delivery_by_state.csv"
)

rfm_data = pd.read_csv(
    BASE_DIR / "rfm_summary.csv"
)

# Judul dashboard
st.title("🛒 Olist E-Commerce Analytics Dashboard")

st.markdown("""
Dashboard ini menyajikan hasil analisis data E-Commerce Olist,
meliputi performa penjualan, pengiriman, dan segmentasi pelanggan
berdasarkan metode RFM.
""")

st.divider()

# Menghitung KPI
total_sales = monthly_sales["total_sales"].sum()

total_orders = monthly_sales["total_orders"].sum()

total_customers = rfm_data["Total_Customers"].sum()

total_late_orders = delivery_data["late_orders"].sum()

total_delivery_orders = delivery_data["total_orders"].sum()

late_percentage = (
    total_late_orders / total_delivery_orders * 100
    if total_delivery_orders > 0 else 0
)

# Menampilkan KPI
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

st.divider()

st.success("Seluruh data analisis berhasil dimuat!")


# ==========================================
# 1. MONTHLY SALES PERFORMANCE
# ==========================================

st.header("📈 Monthly Sales Performance")

st.markdown("""
Visualisasi perkembangan jumlah pesanan dan total nilai
penjualan produk secara bulanan pada E-Commerce Olist.
""")


# ==========================================
# FILTER PERIODE PENJUALAN
# ==========================================

# Mengurutkan daftar bulan
available_months = sorted(
    monthly_sales["order_month"].astype(str).unique()
)

# Membuat filter pada sidebar
selected_months = st.sidebar.select_slider(
    "Pilih Periode Penjualan",
    options=available_months,
    value=(available_months[0], available_months[-1])
)

# Memfilter dataset berdasarkan periode
filtered_sales = monthly_sales[
    (monthly_sales["order_month"].astype(str) >= selected_months[0]) &
    (monthly_sales["order_month"].astype(str) <= selected_months[1])
].copy()

# Menghitung KPI berdasarkan periode terpilih
filtered_total_sales = filtered_sales["total_sales"].sum()
filtered_total_orders = filtered_sales["total_orders"].sum()

col_sales, col_orders = st.columns(2)

col_sales.metric(
    "Sales in Selected Period",
    f"BRL {filtered_total_sales:,.2f}"
)

col_orders.metric(
    "Orders in Selected Period",
    f"{filtered_total_orders:,.0f}"
)

# Membuat grafik penjualan bulanan
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

# Grafik jumlah pesanan bulanan
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


# ==========================================
# 2. DELIVERY PERFORMANCE
# ==========================================

st.divider()

st.header("🚚 Delivery Performance by State")

st.markdown("""
Analisis performa pengiriman berdasarkan negara bagian
pelanggan di Brasil untuk mengidentifikasi wilayah
dengan tingkat keterlambatan pengiriman tertinggi.
""")

# Menggunakan wilayah dengan minimal 100 pesanan
delivery_visual = delivery_data[
    delivery_data["total_orders"] >= 100
].copy()


# ==========================================
# FILTER CUSTOMER STATE
# ==========================================

available_states = sorted(
    delivery_visual["customer_state"].unique()
)

selected_states = st.sidebar.multiselect(
    "Pilih Negara Bagian",
    options=available_states,
    default=available_states
)

# Memfilter data berdasarkan wilayah
filtered_delivery = delivery_visual[
    delivery_visual["customer_state"].isin(selected_states)
].copy()


# ------------------------------------------
# A. DELIVERY DELAY RATE
# ------------------------------------------

top_delay_rate = filtered_delivery.sort_values(
    by="late_percentage",
    ascending=False
).head(10)

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

# ------------------------------------------
# B. AVERAGE DELIVERY DELAY
# ------------------------------------------

top_avg_delay = (
    filtered_delivery
    .dropna(subset=["avg_delay_days"])
    .sort_values(
        by="avg_delay_days",
        ascending=False
    )
    .head(10)
)

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


# ==========================================
# 3. CUSTOMER SEGMENTATION (RFM ANALYSIS)
# ==========================================

st.divider()

st.header("👥 Customer Segmentation (RFM Analysis)")

st.markdown("""
Analisis segmentasi pelanggan menggunakan metode
Recency, Frequency, dan Monetary (RFM) untuk memahami
perilaku pembelian dan kontribusi nilai pelanggan.
""")

# Mengurutkan berdasarkan jumlah pelanggan
rfm_visual = rfm_data.sort_values(
    by="Total_Customers",
    ascending=False
)

# ------------------------------------------
# A. CUSTOMER DISTRIBUTION BY SEGMENT
# ------------------------------------------

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

# ------------------------------------------
# B. TOTAL MONETARY BY SEGMENT
# ------------------------------------------

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

# ------------------------------------------
# C. AVERAGE MONETARY BY SEGMENT
# ------------------------------------------

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

# ------------------------------------------
# D. RFM SUMMARY TABLE
# ------------------------------------------

st.subheader("RFM Segment Summary")

st.dataframe(
    rfm_visual.round(2),
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 4. KEY BUSINESS INSIGHTS
# ==========================================

st.divider()

st.header("💡 Key Business Insights")

st.markdown("""
Ringkasan temuan utama berdasarkan hasil analisis
penjualan, pengiriman, dan segmentasi pelanggan.
""")

# ------------------------------------------
# A. SALES INSIGHT
# ------------------------------------------

sales_with_transactions = monthly_sales[
    monthly_sales["total_orders"] > 0
]

highest_sales = sales_with_transactions.loc[
    sales_with_transactions["total_sales"].idxmax()
]

# ------------------------------------------
# B. DELIVERY INSIGHT
# ------------------------------------------

highest_delay = delivery_data.loc[
    delivery_data["late_percentage"].idxmax()
]

# ------------------------------------------
# C. CUSTOMER SEGMENT INSIGHT
# ------------------------------------------

largest_segment = rfm_data.loc[
    rfm_data["Total_Customers"].idxmax()
]

highest_avg_monetary = rfm_data.loc[
    rfm_data["Avg_Monetary"].idxmax()
]

# ------------------------------------------
# D. DISPLAY INSIGHTS
# ------------------------------------------

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

