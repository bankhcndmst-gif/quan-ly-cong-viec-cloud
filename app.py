import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta

# =====================================================
# CẤU HÌNH CHUNG
# =====================================================
st.set_page_config(
    page_title="Hệ thống Quản lý Công việc EVNGENCO1",
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
    "11_CHAT_GEMINI"
]

# =====================================================
# KẾT NỐI GOOGLE SHEET
# =====================================================
@st.cache_resource
def connect_gsheet():
    creds = dict(st.secrets["gdrive"])
    creds["private_key"] = creds["private_key"].replace("\\n", "\n")
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_key(creds["spreadsheet_id"])
    return sh

# =====================================================
# LOAD 1 SHEET – AN TOÀN TUYỆT ĐỐI
# =====================================================
@st.cache_data(ttl=300)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    sh = connect_gsheet()
    ws = sh.worksheet(sheet_name)

    values = ws.get_all_values()

    if not values or len(values) < 2:
        return pd.DataFrame()

    header = values[0]
    clean_header = []
    valid_idx = []

    for i, h in enumerate(header):
        h = h.strip()
        if h:
            clean_header.append(h)
            valid_idx.append(i)

    if not clean_header:
        return pd.DataFrame()

    rows = []
    for r in values[1:]:
        row = []
        for idx in valid_idx:
            row.append(r[idx] if idx < len(r) else "")
        rows.append(row)

    return pd.DataFrame(rows, columns=clean_header)

# =====================================================
# LOAD TOÀN BỘ SHEET
# =====================================================
@st.cache_data(ttl=300)
def load_all_sheets():
    data = {}
    errors = {}

    for name in SHEET_TABS:
        try:
            data[name] = load_sheet_df(name)
        except Exception as e:
            data[name] = pd.DataFrame()
            errors[name] = str(e)

    return data, errors

# =====================================================
# BÁO CÁO TỔNG HỢP
# =====================================================
def generate_report(df_cv, tu_ngay, den_ngay, id_du_an, id_goi_thau, id_hop_dong):
    df = df_cv.copy()

    for col in ["HAN_CHOT", "NGAY_THUC_TE_XONG", "NGAY_GIAO"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    df = df[
        (df["NGAY_GIAO"] <= den_ngay) &
        (
            df["NGAY_THUC_TE_XONG"].isna() |
            (df["NGAY_THUC_TE_XONG"] >= tu_ngay)
        )
    ]

    if id_du_an != "Tất cả" and "IDDA_DU_AN" in df.columns:
        df = df[df["IDDA_DU_AN"] == id_du_an]

    if id_goi_thau != "Tất cả" and "IDGT_GOI_THAU" in df.columns:
        df = df[df["IDGT_GOI_THAU"] == id_goi_thau]

    if id_hop_dong != "Tất cả" and "IDHD_HOP_DONG" in df.columns:
        df = df[df["IDHD_HOP_DONG"] == id_hop_dong]

    df["QUA_HAN"] = (
        (df["HAN_CHOT"] < den_ngay) &
        (df["TRANG_THAI_TONG"] != "Hoan_Thanh")
    )

    st.subheader("📊 KẾT QUẢ BÁO CÁO")

    for _, r in df.iterrows():
        han = r["HAN_CHOT"].strftime("%d/%m/%Y") if pd.notna(r["HAN_CHOT"]) else "—"
        flag = " ⚠️ QUÁ HẠN" if r["QUA_HAN"] else ""

        st.markdown(
            f"""
**- {r.get("TEN_VIEC","")}**  
• Trạng thái: `{r.get("TRANG_THAI_TONG","")}`{flag}  
• Hạn: **{han}**  
• Vướng mắc: {r.get("VUONG_MAC","")}  
• Đề xuất: {r.get("DE_XUAT","")}
---
"""
        )

# =====================================================
# GIAO DIỆN CHÍNH
# =====================================================
st.title("🗂️ Hệ thống Quản lý Công việc EVNGENCO1")

with st.spinner("Đang tải dữ liệu Google Sheet..."):
    all_sheets, sheet_errors = load_all_sheets()

if sheet_errors:
    st.warning("⚠️ Một số sheet có cấu trúc chưa chuẩn nhưng hệ thống đã tự bỏ qua:")
    for k in sheet_errors:
        st.write(f"- {k}")

tabs = st.tabs(SHEET_TABS + ["📊 BÁO CÁO"])

# =====================================================
# TAB DỮ LIỆU GỐC
# =====================================================
for idx, tab_name in enumerate(SHEET_TABS):
    with tabs[idx]:
        st.header(tab_name)
        df = all_sheets[tab_name]
        st.data_editor(df, num_rows="dynamic", use_container_width=True)

# =====================================================
# TAB BÁO CÁO
# =====================================================
with tabs[-1]:
    st.header("📊 BÁO CÁO CÔNG VIỆC")

    df_cv = all_sheets["7_CONG_VIEC"]

    col1, col2 = st.columns(2)
    with col1:
        tu_ngay = st.date_input("Từ ngày", datetime.now() - timedelta(days=7))
    with col2:
        den_ngay = st.date_input("Đến ngày", datetime.now())

    def pick(col):
        if col in df_cv.columns:
            return ["Tất cả"] + sorted(df_cv[col].dropna().unique().tolist())
        return ["Tất cả"]

    col3, col4, col5 = st.columns(3)
    with col3:
        id_du_an = st.selectbox("ID Dự án", pick("IDDA_DU_AN"))
    with col4:
        id_goi_thau = st.selectbox("ID Gói thầu", pick("IDGT_GOI_THAU"))
    with col5:
        id_hop_dong = st.selectbox("ID Hợp đồng", pick("IDHD_HOP_DONG"))

    if st.button("📊 TẠO BÁO CÁO"):
        generate_report(
            df_cv,
            pd.to_datetime(tu_ngay),
            pd.to_datetime(den_ngay),
            id_du_an,
            id_goi_thau,
            id_hop_dong
        )
