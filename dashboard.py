import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ─── PAGE CONFIG ──────────────────────────────
st.set_page_config(
    page_title="AFGANET Dashboard",
    page_icon="📡",
    layout="wide"
)

# ─── AUTH ─────────────────────────────────────
def check_password():
    def login_form():
        st.markdown("## 📡 AFGANET Dashboard")
        st.caption("WiFi Voucher Management")
        with st.form("login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if user == "admin" and pwd == "afganet2026":
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Username atau password salah")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        login_form()
        st.stop()

check_password()

# ─── DATA FILE ────────────────────────────────
DATA_FILE = "sales_data.csv"

PRODUK = {
    "Voucher 3 Jam": 2000,
    "Voucher 5 Jam": 3000,
    "Voucher 8 Jam": 5000,
    "Daftar Baru": 250000,
    "Per Bulan": 150000,
}

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df["tanggal"] = pd.to_datetime(df["tanggal"])
        return df
    return pd.DataFrame(columns=["tanggal", "produk", "qty", "harga_satuan", "total", "pembayaran"])

# ─── SIDEBAR ──────────────────────────────────
st.sidebar.title("📡 AFGANET")
st.sidebar.caption(f"Login: {st.session_state.get('user', '')}")

df = load_data()

if not df.empty:
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
        options=sorted(PRODUK.keys()),
        default=sorted(PRODUK.keys())
    )
    df_filtered = df_filtered[df_filtered["produk"].isin(produk_list)]
else:
    df_filtered = df

# ─── INPUT DATA ───────────────────────────────
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Tambah Transaksi")
with st.sidebar.form("add_sale", clear_on_submit=True):
    tgl = st.date_input("Tanggal", datetime.now())
    prod = st.selectbox("Produk", list(PRODUK.keys()))
    qty = st.number_input("Qty", 1, 100, 1)
    bayar = st.selectbox("Pembayaran", ["Cash", "QRIS"])
    if st.form_submit_button("Simpan"):
        harga = PRODUK[prod]
        new_row = pd.DataFrame([{
            "tanggal": tgl.strftime("%Y-%m-%d"),
            "produk": prod,
            "qty": qty,
            "harga_satuan": harga,
            "total": harga * qty,
            "pembayaran": bayar,
        }])
        if os.path.exists(DATA_FILE):
            existing = pd.read_csv(DATA_FILE)
            new_row = pd.concat([existing, new_row], ignore_index=True)
        new_row.to_csv(DATA_FILE, index=False)
        st.rerun()

if st.sidebar.button("🗑️ Hapus Semua Data"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("💾 Data tersimpan di sales_data.csv")

# ─── MAIN CONTENT ─────────────────────────────
st.title("📡 Dashboard Penjualan AFGANET")
st.caption("WiFi Voucher — 3 Jam / 5 Jam / 8 Jam / Daftar Baru / Per Bulan")

# ─── CHARTS & METRICS ─────────────────────────
if not df_filtered.empty:
    col1, col2, col3, col4 = st.columns(4)
    total_penjualan = df_filtered["total"].sum()
    total_transaksi = len(df_filtered)
    rata_rata = df_filtered["total"].mean()
    produk_terlaris = df_filtered.groupby("produk")["qty"].sum().idxmax()

    col1.metric("💰 Total Penjualan", f"Rp {total_penjualan:,.0f}")
    col2.metric("🧾 Total Transaksi", total_transaksi)
    col3.metric("📈 Rata-rata / Transaksi", f"Rp {rata_rata:,.0f}")
    col4.metric("🏆 Produk Terlaris", produk_terlaris)

    st.markdown("---")

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
    )

    st.markdown("---")
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Export CSV", csv, "penjualan_export.csv", "text/csv")

else:
    st.info("📭 Belum ada data. Tambahkan transaksi di sidebar kiri.")
    st.markdown("---")
    st.subheader("📋 Daftar Harga")
    harga_df = pd.DataFrame([
        {"Produk": k, "Harga": f"Rp {v:,.0f}"} for k, v in PRODUK.items()
    ])
    st.dataframe(harga_df, use_container_width=True, hide_index=True)
