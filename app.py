import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Quản lý Công việc EVNGENCO1",
    layout="wide"
)

SHEET_TABS = [
    "1_NHAN_SU",
    "2_DON_VI",
    "3_VAN_BAN",
    "4_DU_AN",
    "5_GOI_THAU",
    "6_HOP_DONG",
    "7_CONG_VIEC",
    "9_CAU_HINH",
    "11_CHAT_GEMINI",
]

# =====================================================
# GOOGLE SHEET CONNECT
# =====================================================
@st.cache_resource
def connect_gsheet():
    creds = {
        "type": "service_account",
        "client_email": st.secrets["gdrive"]["client_email"],
        "private_key": st.secrets["gdrive"]["private_key"].replace("\\n", "\n"),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
    return sh

@st.cache_data(ttl=300)
def load_sheet_df(sheet_name):
    sh = connect_gsheet()
    ws = sh.worksheet(sheet_name)
    rows = ws.get_all_values()
    if len(rows) < 2:
        return pd.DataFrame(columns=rows[0] if rows else [])
    return pd.DataFrame(rows[1:], columns=rows[0])

@st.cache_data(ttl=300)
def load_all_sheets():
    data = {}
    for name in SHEET_TABS:
        data[name] = load_sheet_df(name)
    return data

# =====================================================
# LOAD DATA
# =====================================================
st.title("🗂️ HỆ THỐNG QUẢN LÝ CÔNG VIỆC – EVNGENCO1")

try:
    all_sheets = load_all_sheets()
except Exception as e:
    st.error("❌ Không thể tải Google Sheet")
    st.exception(e)
    st.stop()

df_congviec = all_sheets["7_CONG_VIEC"]
df_nhansu = all_sheets["1_NHAN_SU"]

# Merge để có tên người nhận
if "NGUOI_NHAN" in df_congviec.columns and "ID_NHANSU" in df_nhansu.columns:
    df_congviec = df_congviec.merge(
        df_nhansu[["ID_NHANSU", "HOTEN"]],
        left_on="NGUOI_NHAN",
        right_on="ID_NHANSU",
        how="left"
    )

# Chuẩn hóa ngày
for col in ["NGAY_GIAO", "HAN_CHOT", "NGAY_THUC_TE_XONG"]:
    if col in df_congviec.columns:
        df_congviec[col] = pd.to_datetime(df_congviec[col], errors="coerce")

# =====================================================
# TABS
# =====================================================
tabs = st.tabs(
    [
        "📋 Công việc",
        "📊 Báo cáo",
        "👥 Nhân sự",
        "🏢 Đơn vị",
        "📄 Văn bản",
        "🏗️ Dự án",
        "📦 Gói thầu",
        "📑 Hợp đồng",
        "⚙️ Cấu hình & Chat",
    ]
)

# =====================================================
# TAB 1 – CÔNG VIỆC
# =====================================================
with tabs[0]:
    st.subheader("📋 Danh sách công việc")
    st.dataframe(df_congviec, use_container_width=True)

# =====================================================
# TAB 2 – BÁO CÁO
# =====================================================
with tabs[1]:
    st.subheader("📊 BÁO CÁO TIẾN ĐỘ CÔNG VIỆC")

    col1, col2 = st.columns(2)
    with col1:
        ngay_a = st.date_input("📅 Từ ngày", datetime.now().date() - timedelta(days=7))
    with col2:
        ngay_b = st.date_input("📅 Đến ngày", datetime.now().date())

    col3, col4, col5 = st.columns(3)
    with col3:
        du_an_list = ["TẤT CẢ"] + sorted(df_congviec["ID_DU_AN"].dropna().unique().tolist())
        chon_du_an = st.selectbox("ID Dự án", du_an_list)
    with col4:
        goi_thau_list = ["TẤT CẢ"] + sorted(df_congviec["ID_GOI_THAU"].dropna().unique().tolist())
        chon_goi_thau = st.selectbox("ID Gói thầu", goi_thau_list)
    with col5:
        hop_dong_list = ["TẤT CẢ"] + sorted(df_congviec["ID_HOP_DONG"].dropna().unique().tolist())
        chon_hop_dong = st.selectbox("ID Hợp đồng", hop_dong_list)

    df_bc = df_congviec.copy()

    df_bc = df_bc[
        (df_bc["NGAY_GIAO"] <= pd.to_datetime(ngay_b)) &
        (
            df_bc["NGAY_THUC_TE_XONG"].isna() |
            (df_bc["NGAY_THUC_TE_XONG"] >= pd.to_datetime(ngay_a))
        )
    ]

    if chon_du_an != "TẤT CẢ":
        df_bc = df_bc[df_bc["ID_DU_AN"] == chon_du_an]
    if chon_goi_thau != "TẤT CẢ":
        df_bc = df_bc[df_bc["ID_GOI_THAU"] == chon_goi_thau]
    if chon_hop_dong != "TẤT CẢ":
        df_bc = df_bc[df_bc["ID_HOP_DONG"] == chon_hop_dong]

    df_xong = df_bc[df_bc["TRANG_THAI_TONG"] == "Hoan_Thanh"]
    df_dang = df_bc[df_bc["TRANG_THAI_TONG"] != "Hoan_Thanh"]

    st.markdown("### ✅ Công việc đã hoàn thành")
    st.dataframe(df_xong, use_container_width=True)

    st.markdown("### ⏳ Công việc đang thực hiện / tồn đọng")
    st.dataframe(df_dang, use_container_width=True)

# =====================================================
# TAB 3 → 8 – CÁC DỮ LIỆU GỐC
# =====================================================
with tabs[2]:
    st.dataframe(all_sheets["1_NHAN_SU"], use_container_width=True)

with tabs[3]:
    st.dataframe(all_sheets["2_DON_VI"], use_container_width=True)

with tabs[4]:
    st.dataframe(all_sheets["3_VAN_BAN"], use_container_width=True)

with tabs[5]:
    st.dataframe(all_sheets["4_DU_AN"], use_container_width=True)

with tabs[6]:
    st.dataframe(all_sheets["5_GOI_THAU"], use_container_width=True)

with tabs[7]:
    st.dataframe(all_sheets["6_HOP_DONG"], use_container_width=True)

with tabs[8]:
    st.dataframe(all_sheets["9_CAU_HINH"], use_container_width=True)
    st.markdown("---")
    st.dataframe(all_sheets["11_CHAT_GEMINI"], use_container_width=True)
