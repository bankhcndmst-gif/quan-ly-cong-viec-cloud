import streamlit as st
import gspread
import pandas as pd

# --- Hàm Tải Dữ liệu từ Google Sheets (An toàn cho Streamlit Cloud) ---
@st.cache_data(ttl=600)  # Cache 10 phút (có thể comment khi debug)
def load_data_from_gsheets():
    try:
        # ===== CHECKPOINT 0: Kiểm tra secrets =====
        if "gdrive" not in st.secrets:
            st.error("❌ Thiếu cấu hình [gdrive] trong Streamlit Secrets")
            st.stop()

        for key in ["private_key", "client_email", "spreadsheet_id"]:
            if key not in st.secrets["gdrive"]:
                st.error(f"❌ Thiếu gdrive.{key} trong Streamlit Secrets")
                st.stop()

        # ===== CHECKPOINT 1: Tạo credentials đầy đủ cho gspread =====
        credentials = {
            "type": "service_account",
            "project_id": "streamlit-gdrive-connector",     # giả, không bắt buộc
            "private_key_id": "key_id_placeholder",         # giả, không bắt buộc
            "private_key": st.secrets["gdrive"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["gdrive"]["client_email"],
            "client_id": "client_id_placeholder",           # giả, không bắt buộc
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": (
                "https://www.googleapis.com/robot/v1/metadata/x509/"
                "client_email_placeholder"
            ),
        }

        # ===== CHECKPOINT 2: Kết nối Google Sheets =====
        gc = gspread.service_account_from_dict(credentials)
        spreadsheet_id = st.secrets["gdrive"]["spreadsheet_id"]
        sh = gc.open_by_key(spreadsheet_id)

        # ===== CHECKPOINT 3: Tải dữ liệu các sheet =====
        sheets = {}
        sheet_titles = [
            "1_NHAN_SU",
            "7_CONG_VIEC",
            "2_NHIEM_VU",
            "4_TIEU_CHI"
        ]

        for title in sheet_titles:
            try:
                worksheet = sh.worksheet(title)
                records = worksheet.get_all_records()
                sheets[title] = pd.DataFrame(records)
            except gspread.WorksheetNotFound:
                st.warning(f"⚠️ Không tìm thấy sheet '{title}'")
                sheets[title] = pd.DataFrame()
            except Exception as e:
                st.error(f"❌ Lỗi khi tải sheet '{title}': {e}")
                sheets[title] = pd.DataFrame()

        # ===== CHECKPOINT 4: Hoàn tất =====
        return sheets

    except Exception as e:
        st.error(
            "❌ Lỗi nghiêm trọng khi kết nối Google Sheets.\n"
            f"Chi tiết: {e}"
        )
        return None
