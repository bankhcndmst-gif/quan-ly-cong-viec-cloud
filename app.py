import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
REQUIRED_SHEETS = [
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

DATE_COLS = ["NGAY_GIAO", "HAN_CHOT", "NGAY_THUC_TE_XONG"]

# =========================
# GOOGLE SHEET CONNECT
# =========================
@st.cache_resource
def connect_gsheet():
    creds_dict = dict(st.secrets["gdrive"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# =========================
# UTILS
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\u00a0", "", regex=False)
    )
    return df

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for c in DATE_COLS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

# =========================
# LOAD ONE SHEET
# =========================
@st.cache_data
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    gc = connect_gsheet()
    sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])
    ws = sh.worksheet(sheet_name)

    values = ws.get_all_values()
    if len(values) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(values[1:], columns=values[0])
    df = normalize_columns(df)
    df = parse_dates(df)
    return df

# =========================
# LOAD ALL SHEETS
# =========================
@st.cache_data
def load_all_sheets():
    sheets = {}
    for name in REQUIRED_SHEETS:
        sheets[name] = load_sheet_df(name)
    return sheets

# =========================
# REPORT LOGIC
# =========================
def filter_report(df, start_date, end_date, id_duan, id_goithau, id_hopdong):
    df = df.copy()

    if "NGAY_GIAO" in df.columns:
        df = df[
            (df["NGAY_GIAO"] >= start_date) &
            (df["NGAY_GIAO"] <= end_date)
        ]

    if id_duan != "Tất cả" and "ID_DU_AN" in df.columns:
        df = df[df["ID_DU_AN"] == id_duan]

    if id_goithau != "Tất cả" and "ID_GOI_THAU" in df.columns:
        df = df[df["ID_GOI_THAU"] == id_goithau]

    if id_hopdong != "Tất cả" and "ID_HOP_DONG" in df.columns:
        df = df[df["ID_HOP_DONG"] == id_hopdong]

    return df

# =========================
# UI
# =========================
st.set_page_config(page_title="Quản lý công việc EVNGENCO1", layout="wide")
st.title("📋 QUẢN LÝ CÔNG VIỆC – GOOGLE SHEET")

try:
    all_sheets = load_all_sheets()
    df_cv = all_sheets["7_CONG_VIEC"]

    # ---------------------
    # FILTER BAR
    # ---------------------
    with st.sidebar:
        st.header("🎯 Bộ lọc báo cáo")

        start_date = st.date_input("Từ ngày", datetime.now() - timedelta(days=7))
        end_date = st.date_input("Đến ngày", datetime.now())

        id_duan = ["Tất cả"] + sorted(df_cv.get("ID_DU_AN", []).dropna().unique().tolist())
        id_goithau = ["Tất cả"] + sorted(df_cv.get("ID_GOI_THAU", []).dropna().unique().tolist())
        id_hopdong = ["Tất cả"] + sorted(df_cv.get("ID_HOP_DONG", []).dropna().unique().tolist())

        chon_duan = st.selectbox("ID Dự án", id_duan)
        chon_goithau = st.selectbox("ID Gói thầu", id_goithau)
        chon_hopdong = st.selectbox("ID Hợp đồng", id_hopdong)

    # ---------------------
    # REPORT
    # ---------------------
    df_report = filter_report(
        df_cv,
        pd.to_datetime(start_date),
        pd.to_datetime(end_date),
        chon_duan,
        chon_goithau,
        chon_hopdong,
    )

    st.subheader("📊 KẾT QUẢ BÁO CÁO")

    if df_report.empty:
        st.info("Không có công việc nào trong khoảng đã chọn.")
    else:
        for _, r in df_report.iterrows():
            han_val = r.get("HAN_CHOT")
            han = (
                han_val.strftime("%d/%m/%Y")
                if pd.notna(han_val) and hasattr(han_val, "strftime")
                else "—"
            )

            st.markdown(
                f"""
                **• {r.get("NOI_DUNG", "")}**  
                - Ngày giao: {r.get("NGAY_GIAO").strftime("%d/%m/%Y") if pd.notna(r.get("NGAY_GIAO")) else "—"}  
                - Hạn chót: **{han}**  
                - Trạng thái: {r.get("TRANG_THAI_TONG", "")}
                """
            )
            st.markdown("---")

    # ---------------------
    # DATA TABS
    # ---------------------
    st.subheader("📁 DỮ LIỆU GỐC")
    tabs = st.tabs(REQUIRED_SHEETS)
    for tab, name in zip(tabs, REQUIRED_SHEETS):
        with tab:
            st.dataframe(all_sheets[name], use_container_width=True)

except Exception as e:
    st.error("❌ Lỗi hệ thống")
    st.exception(e)
