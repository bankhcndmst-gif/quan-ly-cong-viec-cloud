import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread

# =========================================================
# === CẤU HÌNH GOOGLE SHEET
# =========================================================
SPREADSHEET_ID = st.secrets["gdrive"]["spreadsheet_id"]

def _make_creds():
    return {
        "type": "service_account",
        "client_email": st.secrets["gdrive"]["client_email"],
        "private_key": st.secrets["gdrive"]["private_key"].replace("\\n", "\n"),
        "token_uri": "https://oauth2.googleapis.com/token",
    }

@st.cache_resource
def get_gspread_client():
    return gspread.service_account_from_dict(_make_creds())

@st.cache_resource
def get_spreadsheet():
    gc = get_gspread_client()
    return gc.open_by_key(SPREADSHEET_ID)

@st.cache_data(ttl=300)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    sh = get_spreadsheet()
    ws = sh.worksheet(sheet_name)
    rows = ws.get_all_records()
    return pd.DataFrame(rows)

def save_sheet_df(sheet_name: str, df: pd.DataFrame):
    sh = get_spreadsheet()
    ws = sh.worksheet(sheet_name)
    ws.clear()
    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())

# =========================================================
# === LOAD DỮ LIỆU
# =========================================================
@st.cache_data(ttl=300)
def load_all_data():
    df_congviec = load_sheet_df("7_CONG_VIEC")
    df_nhansu = load_sheet_df("1_NHAN_SU")[["ID_NHANSU", "HOTEN", "EMAIL"]]

    df = pd.merge(
        df_congviec,
        df_nhansu,
        left_on="NGUOI_NHAN",
        right_on="ID_NHANSU",
        how="left",
    )

    # Chuẩn hóa
    df["HAN_CHOT"] = pd.to_datetime(df["HAN_CHOT"], errors="coerce").dt.date
    df["NGAY_THUC_TE_XONG"] = pd.to_datetime(df["NGAY_THUC_TE_XONG"], errors="coerce").dt.date
    df[["VUONG_MAC", "DE_XUAT", "TRANG_THAI_CHI_TIET"]] = df[
        ["VUONG_MAC", "DE_XUAT", "TRANG_THAI_CHI_TIET"]
    ].fillna("")

    # Danh sách trạng thái – cố định (đơn giản)
    list_trang_thai = ["Dang_Lam", "Hoan_Thanh", "Cho_Duyet", "Tam_Dung"]

    return df, list_trang_thai

# =========================================================
# === GIAO DIỆN
# =========================================================
st.set_page_config(layout="wide", page_title="Quản Lý Công Việc EVNGENCO1")
st.title("🗂️ Hệ thống Quản lý Công việc EVNGENCO1")
st.caption("Nguồn dữ liệu: Google Sheet – realtime")

df_tong_hop, list_trang_thai = load_all_data()

tab1, tab2 = st.tabs([
    "1. QUẢN LÝ CÔNG VIỆC",
    "2. BÁO CÁO TỔNG HỢP",
])

# =========================================================
# TAB 1 – QUẢN LÝ CÔNG VIỆC
# =========================================================
with tab1:
    st.header("Danh sách công việc")

    # Bộ lọc
    col1, col2 = st.columns(2)
    with col1:
        nguoi_list = ["Tất cả"] + sorted(df_tong_hop["HOTEN"].dropna().unique().tolist())
        loc_nguoi = st.selectbox("Lọc theo người nhận", nguoi_list)
    with col2:
        tt_list = ["Tất cả"] + list_trang_thai
        loc_tt = st.selectbox("Lọc theo trạng thái", tt_list)

    df_view = df_tong_hop.copy()
    if loc_nguoi != "Tất cả":
        df_view = df_view[df_view["HOTEN"] == loc_nguoi]
    if loc_tt != "Tất cả":
        df_view = df_view[df_view["TRANG_THAI_TONG"] == loc_tt]

    display_cols = [
        "ID_CONGVIEC", "TEN_VIEC", "HOTEN",
        "HAN_CHOT", "TRANG_THAI_TONG",
        "TRANG_THAI_CHI_TIET", "VUONG_MAC",
        "DE_XUAT", "NGAY_THUC_TE_XONG",
    ]

    edited_df = st.data_editor(
        df_view[display_cols],
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "ID_CONGVIEC": st.column_config.Column("ID", disabled=True),
            "HOTEN": st.column_config.Column("Người nhận", disabled=True),
            "HAN_CHOT": st.column_config.DateColumn("Hạn chót"),
            "NGAY_THUC_TE_XONG": st.column_config.DateColumn("Ngày hoàn thành"),
            "TRANG_THAI_TONG": st.column_config.SelectboxColumn(
                "Trạng thái", options=list_trang_thai, required=True
            ),
        },
    )

    if st.button("💾 LƯU THAY ĐỔI"):
        df_save = edited_df.drop(columns=["HOTEN"])
        save_sheet_df("7_CONG_VIEC", df_save)
        st.cache_data.clear()
        st.success("Đã lưu dữ liệu vào Google Sheet")
        st.rerun()

# =========================================================
# TAB 2 – BÁO CÁO
# =========================================================
with tab2:
    st.header("Báo cáo tổng hợp")

    hom_nay = datetime.now().date()
    df = df_tong_hop.copy()
    df["QUAHAN"] = (df["HAN_CHOT"] < hom_nay) & (df["TRANG_THAI_TONG"] != "Hoan_Thanh")

    st.dataframe(
        df[[
            "TEN_VIEC", "HOTEN", "HAN_CHOT",
            "TRANG_THAI_TONG", "QUAHAN",
            "VUONG_MAC", "DE_XUAT",
        ]],
        use_container_width=True,
    )
