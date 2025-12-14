import streamlit as st
import gspread
import pandas as pd

# =========================
# HÀM LOAD GOOGLE SHEETS
# =========================
@st.cache_data(ttl=600)
def load_data_from_gsheets():
    try:
        credentials = {
            "type": "service_account",
            "private_key": st.secrets["gdrive"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["gdrive"]["client_email"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }

        gc = gspread.service_account_from_dict(credentials)
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])

        sheets = {}
        for name in [
            "1_NHAN_SU",
            "7_CONG_VIEC",
            "2_NHIEM_VU",
            "4_TIEU_CHI"
        ]:
            try:
                ws = sh.worksheet(name)
                sheets[name] = pd.DataFrame(ws.get_all_records())
            except Exception as e:
                st.warning(f"⚠️ Sheet {name}: {e}")
                sheets[name] = pd.DataFrame()

        return sheets

    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
        return None


# =========================
# UI TỐI THIỂU (BẮT BUỘC)
# =========================
st.title("🗂️ Hệ thống Quản lý Công việc")

data = load_data_from_gsheets()

if data is None:
    st.stop()

st.success("✅ Load dữ liệu thành công")
st.write(list(data.keys()))
