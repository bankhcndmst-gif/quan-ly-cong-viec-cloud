# ============================================================
# APP: HỆ THỐNG QUẢN LÝ CÔNG VIỆC – STREAMLIT CLOUD
# ============================================================

import streamlit as st
import gspread
import pandas as pd

# ============================================================
# CẤU HÌNH CHUNG
# ============================================================

st.set_page_config(
    page_title="Hệ thống Quản lý Công việc",
    layout="wide"
)

# ============================================================
# HÀM KẾT NỐI GOOGLE SHEET
# ============================================================

@st.cache_data(ttl=600)
def connect_gsheet():
    """
    Kết nối Google Sheet an toàn, tự bổ sung token_uri nếu thiếu
    """
    creds = dict(st.secrets["gdrive"])
    spreadsheet_id = creds.pop("spreadsheet_id")

    # 🔴 BẮT BUỘC: đảm bảo token_uri tồn tại
    if "token_uri" not in creds:
        creds["token_uri"] = "https://oauth2.googleapis.com/token"

    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_key(spreadsheet_id)
    return sh


@st.cache_data(ttl=600)
def load_sheet(sh, sheet_name: str) -> pd.DataFrame:
    """
    Load 1 worksheet thành DataFrame an toàn
    """
    try:
        ws = sh.worksheet(sheet_name)
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        return df
    except gspread.WorksheetNotFound:
        st.warning(f"⚠️ Không tìm thấy tab: {sheet_name}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc tab {sheet_name}: {e}")
        return pd.DataFrame()


# ============================================================
# UI CHÍNH
# ============================================================

st.title("🗂️ Hệ thống Quản lý Công việc")

with st.spinner("🔌 Đang kết nối Google Sheet..."):
    try:
        sh = connect_gsheet()
    except Exception as e:
        st.exception(e)
        st.stop()

st.success("✅ Kết nối Google Sheet thành công")

# ============================================================
# LIỆT KÊ TAB (DEBUG & CHUẨN HÓA)
# ============================================================

with st.expander("📋 Danh sách tab trong Google Sheet", expanded=False):
    try:
        tab_names = [ws.title for ws in sh.worksheets()]
        st.write(tab_names)
    except Exception as e:
        st.exception(e)

# ============================================================
# LOAD DỮ LIỆU CÁC TAB CHÍNH
# ============================================================

TAB_CONFIG = {
    "DUAN": "DUAN",
    "NHANSU": "NHANSU",
    "DONVI": "DONVI",
    "VANBAN": "VANBAN",
    "CONGVIEC": "CONGVIEC",
    "GOITHAU": "GOITHAU",
    "HOPDONG": "HOPDONG",
    "CAUHINH": "CAUHINH",
}

data = {}

for key, sheet_name in TAB_CONFIG.items():
    data[key] = load_sheet(sh, sheet_name)

# ============================================================
# HIỂN THỊ THEO TAB UI
# ============================================================

tabs = st.tabs(list(TAB_CONFIG.keys()))

for tab, key in zip(tabs, TAB_CONFIG.keys()):
    with tab:
        df = data.get(key, pd.DataFrame())

        if df.empty:
            st.info("Chưa có dữ liệu")
        else:
            st.write(f"📊 Số dòng: {len(df)}")
            st.dataframe(df, use_container_width=True)

# ============================================================
# KIỂM TRA DỮ LIỆU CƠ BẢN (KHÔNG BẮT BUỘC)
# ============================================================

with st.expander("🧪 Kiểm tra dữ liệu cơ bản", expanded=False):
    if "DUAN" in data and not data["DUAN"].empty:
        df_duan = data["DUAN"]
        missing_id = df_duan["ID_DUAN"].isna().sum()
        st.write(f"- DUAN thiếu ID_DUAN: {missing_id}")

    if "NHANSU" in data and not data["NHANSU"].empty:
        df_ns = data["NHANSU"]
        missing_ns = df_ns["ID_NHANSU"].isna().sum()
        st.write(f"- NHANSU thiếu ID_NHANSU: {missing_ns}")

st.caption("© Hệ thống Quản lý Công việc – Streamlit Cloud")

