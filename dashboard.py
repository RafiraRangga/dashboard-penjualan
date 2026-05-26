import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os

# ─── PAGE CONFIG ──────────────────────────────
st.set_page_config(
    page_title="Dashboard Penjualan",
    page_icon="📊",
    layout="wide"
)

# ─── HELPER: Generate / Load Data ─────────────
DATA_FILE = "sales_data.csv"

def generate_sample_data():
    """Generate 90 hari data penjualan dummy"""
    products = ["Voucher 3 Jam", "Voucher 5 Jam", "Voucher 8 Jam", "Voucher 24 Jam"]
    payment = ["Cash", "QRIS"]
    data = []
    start = datetime.now() - timedelta(days=90)
    for i in range(200):
        date = start + timedelta(days=random.randint(0, 90))
        prod = random.choice(products)
        qty = random.randint(1, 5)
        price_map = {"Voucher 3 Jam": 5000, "Voucher 5 Jam": 8000, "Voucher 8 Jam": 12000, "Voucher 24 Jam": 20000}
        harga = price_map[prod]
        data.append({
            "tanggal": date.strftime("%Y-%m-%d"),
            "produk": prod,
            "qty": qty,
            "harga_satuan": harga,
            "total": harga * qty,
            "pembayaran": random.choice(payment)
        })
    df = pd.DataFrame(data)
    df.to_csv(DATA_FILE, index=False)
    return df

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df["tanggal"] = pd.to_datetime(df["tanggal"])
        return df
    return generate_sample_data()

# ─── SIDEBAR ──────────────────────────────────
st.sidebar.title("📊 Dashboard Penjualan AFGANET")
st.sidebar.caption("AFGANET")

# Filter
df = load_data()
min_date = df["tanggal"].min().date()
max_date = df["tanggal"].max().date()

date_range = st.sidebar.date_input(
    "📅 Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df["tanggal"].dt.date >= start_date) & (df["tanggal"].dt.date <= end_date)
    df_filtered = df[mask]
else:
    df_filtered = df

produk_list = st.sidebar.multiselect(
    "🏷️ Filter Produk",
    options=df["produk"].unique(),
    default=df["produk"].unique()
)
df_filtered = df_filtered[df_filtered["produk"].isin(produk_list)]

st.sidebar.markdown("---")
st.sidebar.caption("🔄 Data dummy — ganti CSV asli nanti")

# ─── MAIN CONTENT ─────────────────────────────
st.title("📊 Dashboard Penjualan")
st.caption(f"Periode: {start_date} — {end_date} | {len(df_filtered)} transaksi")

# ─── METRIC CARDS ─────────────────────────────
col1, col2, col3, col4 = st.columns(4)
total_penjualan = df_filtered["total"].sum()
total_transaksi = len(df_filtered)
rata_rata = df_filtered["total"].mean() if total_transaksi > 0 else 0
produk_terlaris = df_filtered.groupby("produk")["qty"].sum().idxmax() if total_transaksi > 0 else "-"

col1.metric("💰 Total Penjualan", f"Rp {total_penjualan:,.0f}")
col2.metric("🧾 Total Transaksi", total_transaksi)
col3.metric("📈 Rata-rata / Transaksi", f"Rp {rata_rata:,.0f}")
col4.metric("🏆 Produk Terlaris", produk_terlaris)

st.markdown("---")

# ─── CHARTS ───────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Trend Penjualan Harian")
    daily = df_filtered.groupby("tanggal")["total"].sum().reset_index()
    fig_line = px.line(
        daily, x="tanggal", y="total",
markers=True,
        labels={"tanggal": "Tanggal", "total": "Total (Rp)"},
    )
    fig_line.update_traces(line_color="#ff6b6b")
    fig_line.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.subheader("🏷️ Penjualan per Produk")
    by_product = df_filtered.groupby("produk")["total"].sum().reset_index().sort_values("total", ascending=True)
    fig_bar = px.bar(
        by_product, x="total", y="produk", orientation="h",
        color="produk", text_auto=".0f",
        labels={"total": "Total (Rp)", "produk": ""}
    )
    fig_bar.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

# ─── PIE CHART + PAYMENT ──────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("💳 Metode Pembayaran")
    pay_counts = df_filtered["pembayaran"].value_counts().reset_index()
    pay_counts.columns = ["Metode", "Jumlah"]
    fig_pie = px.pie(pay_counts, values="Jumlah", names="Metode", hole=0.4)
    fig_pie.update_traces(marker=dict(colors=["#ff6b6b", "#4ecdc4"]))
    fig_pie.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    st.subheader("📦 Volume per Produk")
    by_qty = df_filtered.groupby("produk")["qty"].sum().reset_index().sort_values("qty", ascending=True)
    fig_qty = px.bar(
        by_qty, x="qty", y="produk", orientation="h",
        color="produk", text_auto=True,
        labels={"qty": "Qty Terjual", "produk": ""}
    )
    fig_qty.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
    st.plotly_chart(fig_qty, use_container_width=True)

st.markdown("---")

# ─── DATA TABLE ───────────────────────────────
st.subheader("📋 Detail Transaksi")
search = st.text_input("🔍 Cari produk / tanggal / pembayaran...")

df_display = df_filtered.copy()
df_display["tanggal"] = df_display["tanggal"].dt.strftime("%d %b %Y")
df_display["total"] = df_display["total"].apply(lambda x: f"Rp {x:,.0f}")
df_display["harga_satuan"] = df_display["harga_satuan"].apply(lambda x: f"Rp {x:,.0f}")

if search:
    df_display = df_display[df_display.astype(str).apply(lambda row: row.str.contains(search, case=False).any(), axis=1)]

st.dataframe(
    df_display.sort_values("tanggal", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "tanggal": "Tanggal",
        "produk": "Produk",
        "qty": st.column_config.NumberColumn("Qty"),
        "harga_satuan": "Harga Satuan",
        "total": "Total",
        "pembayaran": "Bayar"
    }
)

# ─── EXPORT ───────────────────────────────────
st.markdown("---")
c1, c2 = st.columns([1, 5])
with c1:
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Export CSV",
        csv,
        "penjualan_export.csv",
        "text/csv"
    )
with c2:
    st.caption("💡 Ganti `sales_data.csv` dengan data asli lo nanti (format kolom sama: tanggal, produk, qty, harga_satuan, total, pembayaran)")
