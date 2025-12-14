# --- Hàm Tải Dữ liệu từ Google Sheets (An toàn cho Streamlit Cloud) ---
@st.cache_data(ttl=600)  # Cache 10 phút
def load_data_from_gsheets():
    try:
        # 1. Tạo credentials TỐI THIỂU – CHUẨN GSPREAD
        credentials = {
            "type": "service_account",
            "private_key": st.secrets["gdrive"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["gdrive"]["client_email"],
            "token_uri": "https://oauth2.googleapis.com/token", # Cần cho gspread v6+
        }

        # 2. Kết nối Google Sheet
        gc = gspread.service_account_from_dict(credentials)
        sh = gc.open_by_key(st.secrets["gdrive"]["spreadsheet_id"])

        # 3. Load dữ liệu
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
