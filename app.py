import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# =========================================================
# CẤU HÌNH GOOGLE SHEET
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
    return get_gspread_client().open_by_key(SPREADSHEET_ID)

@st.cache_data(ttl=300)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    ws = get_spreadsheet().worksheet(sheet_name)
    rows = ws.get_all_records()
    return pd.DataFrame(rows)

def save_sheet_df(sheet_name: str, df: pd.DataFrame):
    ws = get_spreadsheet().worksheet(sheet_name)
    ws.clear()
    ws.update([df.columns.tolist()] + df.astype(str).values.tolist())

# =========================================================
# LOAD TẤT CẢ CÁC SHEET
# =========================================================
@st.cache_data(ttl=300)
def load_all_sheets():
    sheets = {}
    sheet_names = [
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
    for name in sheet_names:
        sheets[name] = load_sheet_df(name)
    return sheets

# =========================================================
# GIAO DIỆN CHUNG
# =========================================================
st.set_page_config(layout="wide", page_title="Hệ thống Quản lý Công việc EVNGENCO1")
st.title("🗂️ Hệ thống Quản lý Công việc EVNGENCO1")
st.caption("Nguồn dữ liệu: Google Sheet (realtime)")

all_sheets = load_all_sheets()

# =========================================================
# TẠO TAB
# =========================================================
tabs = st.tabs([
    "1. NHÂN SỰ",
    "2. ĐƠN VỊ",
    "3. VĂN BẢN",
    "4. DỰ ÁN",
    "5. GÓI THẦU",
    "6. HỢP ĐỒNG",
    "7. CÔNG VIỆC",
    "9. CẤU HÌNH",
    "11. CHAT GEMINI",
])

# =========================================================
# TAB TEMPLATE – XEM & SỬA DỮ LIỆU GỐC
# =========================================================
def render_editable_tab(sheet_name: str):
    df = all_sheets[sheet_name].copy()
    st.subheader(f"Nội dung {sheet_name}")
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
    )
    if st.button(f"💾 LƯU {sheet_name}", key=f"save_{sheet_name}"):
        save_sheet_df(sheet_name, edited_df)
        st.cache_data.clear()
        st.success(f"Đã lưu {sheet_name}")
        st.rerun()

# =========================================================
# TAB 1 → 6 (DỮ LIỆU GỐC)
# =========================================================
with tabs[0]:
    render_editable_tab("1_NHAN_SU")

with tabs[1]:
    render_editable_tab("2_DON_VI")

with tabs[2]:
    render_editable_tab("3_VAN_BAN")

with tabs[3]:
    render_editable_tab("4_DU_AN")

with tabs[4]:
    render_editable_tab("5_GOI_THAU")

with tabs[5]:
    render_editable_tab("6_HOP_DONG")

# =========================================================
# TAB 7 – CÔNG VIỆC (LOGIC RIÊNG)
# =========================================================
with tabs[6]:
    st.subheader("Quản lý Công việc")

    df_cv = all_sheets["7_CONG_VIEC"].copy()
    df_ns = all_sheets["1_NHAN_SU"][["ID_NHANSU", "HOTEN"]]

    df = pd.merge(
        df_cv,
        df_ns,
        left_on="NGUOI_NHAN",
        right_on="ID_NHANSU",
        how="left",
    )

    df["HAN_CHOT"] = pd.to_datetime(df["HAN_CHOT"], errors="coerce").dt.date
    df["NGAY_THUC_TE_XONG"] = pd.to_datetime(df["NGAY_THUC_TE_XONG"], errors="coerce").dt.date
    df[["VUONG_MAC", "DE_XUAT", "TRANG_THAI_CHI_TIET"]] = df[
        ["VUONG_MAC", "DE_XUAT", "TRANG_THAI_CHI_TIET"]
    ].fillna("")

    list_trang_thai = ["Dang_Lam", "Hoan_Thanh", "Cho_Duyet", "Tam_Dung"]

    # Bộ lọc
    col1, col2 = st.columns(2)
    with col1:
        nguoi = st.selectbox(
            "Lọc theo người nhận",
            ["Tất cả"] + sorted(df["HOTEN"].dropna().unique().tolist())
        )
    with col2:
        tt = st.selectbox(
            "Lọc theo trạng thái",
            ["Tất cả"] + list_trang_thai
        )

    df_view = df.copy()
    if nguoi != "Tất cả":
        df_view = df_view[df_view["HOTEN"] == nguoi]
    if tt != "Tất cả":
        df_view = df_view[df_view["TRANG_THAI_TONG"] == tt]

    display_cols = [
        "ID_CONGVIEC", "TEN_VIEC", "HOTEN",
        "HAN_CHOT", "TRANG_THAI_TONG",
        "TRANG_THAI_CHI_TIET",
        "VUONG_MAC", "DE_XUAT",
        "NGAY_THUC_TE_XONG",
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

    if st.button("💾 LƯU CÔNG VIỆC"):
        df_save = edited_df.drop(columns=["HOTEN"])
        save_sheet_df("7_CONG_VIEC", df_save)
        st.cache_data.clear()
        st.success("Đã lưu công việc")
        st.rerun()

# =========================================================
# TAB 9 – CẤU HÌNH
# =========================================================
with tabs[7]:
    render_editable_tab("9_CAU_HINH")

# =========================================================
# TAB 11 – CHAT GEMINI (CHUẨN BỊ AI)
# =========================================================
with tabs[8]:
    st.subheader("Chat Gemini (dữ liệu cấu hình)")
    st.dataframe(all_sheets["11_CHAT_GEMINI"], use_container_width=True)
    st.info("Tab này dùng làm dữ liệu cho AI / Gemini về sau (chưa kích hoạt chat).")
