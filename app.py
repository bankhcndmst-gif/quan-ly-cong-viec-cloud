import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- GIẢ LẬP KẾT NỐI DỮ LIỆU (Bạn thay phần này bằng code kết nối Google Sheets thật) ---
# Ví dụ: Dùng gspread hoặc streamlit-google-sheets
def get_data_from_google_sheet(sheet_name):
    # Đây là hàm giả lập để code chạy được ngay.
    # Trong thực tế, bạn thay bằng lệnh: conn.read(worksheet=sheet_name)
    
    if sheet_name == "1_NHAN_SU":
        # Dữ liệu này chỉ Python đọc, KHÔNG hiển thị ra màn hình
        return pd.DataFrame({
            "Username": ["admin", "nhanvien1"],
            "Password": ["123456", "123"],
            "HoTen": ["Quản trị viên", "Nguyễn Văn A"]
        })
    elif sheet_name == "2_CONG_VIEC":
        return pd.DataFrame({
            "Mã CV": ["CV01", "CV02"],
            "Tên việc": ["Báo cáo tuần", "Kiểm tra server"],
            "Trạng thái": ["Đang làm", "Hoàn thành"],
            "Người phụ trách": ["Nguyễn Văn A", "Quản trị viên"]
        })
    elif sheet_name == "3_CHAT":
        # Nếu chưa có trong session, tạo dữ liệu mẫu
        if "chat_data" not in st.session_state:
            st.session_state.chat_data = pd.DataFrame([
                {"Time": "10:00", "User": "Quản trị viên", "Message": "Chào mọi người"}
            ])
        return st.session_state.chat_data
    return pd.DataFrame()

def save_message_to_sheet(user, message):
    # Hàm này sẽ ghi vào Google Sheet thật
    # Ở đây mình ghi vào biến tạm trong Session State
    new_msg = {
        "Time": datetime.now().strftime("%H:%M:%S"), 
        "User": user, 
        "Message": message
    }
    st.session_state.chat_data = pd.concat(
        [st.session_state.chat_data, pd.DataFrame([new_msg])], 
        ignore_index=True
    )

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Công việc", layout="wide")

# --- KHỞI TẠO SESSION STATE (Lưu trạng thái đăng nhập) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# --- HÀM XỬ LÝ ĐĂNG NHẬP ---
def login_logic(username, password):
    # 1. Lấy dữ liệu mật (Chỉ lấy về biến df_users, không in ra)
    df_users = get_data_from_google_sheet("1_NHAN_SU")
    
    # 2. Kiểm tra khớp User/Pass
    # Tìm dòng có Username trùng
    user_row = df_users[df_users['GMAIL'] == username]
    
    if not user_row.empty:
        # Nếu tìm thấy user, kiểm tra password
        stored_password = user_row.iloc[0]['Password']
        if str(stored_password) == str(password):
            st.session_state.logged_in = True
            st.session_state.current_user = user_row.iloc[0]['HO_TEN']
            st.success("Đăng nhập thành công!")
            time.sleep(1)
            st.rerun() # Tải lại trang để vào giao diện chính
        else:
            st.error("Sai mật khẩu!")
    else:
        st.error("Tài khoản không tồn tại!")

# --- HÀM XỬ LÝ ĐĂNG XUẤT ---
def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.rerun()

# ==========================================
# GIAO DIỆN CHÍNH (MAIN UI)
# ==========================================

if not st.session_state.logged_in:
    # ----------------------------------
    # TRƯỜNG HỢP 1: CHƯA ĐĂNG NHẬP
    # ----------------------------------
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.header("🔐 Đăng nhập hệ thống")
        user_input = st.text_input("Tài khoản")
        pass_input = st.text_input("Mật khẩu", type="password")
        
        if st.button("Đăng nhập", use_container_width=True):
            login_logic(user_input, pass_input)

else:
    # ----------------------------------
    # TRƯỜNG HỢP 2: ĐÃ ĐĂNG NHẬP
    # ----------------------------------
    
    # Sidebar: Thông tin user & Đăng xuất
    with st.sidebar:
        st.write(f"Xin chào, **{st.session_state.current_user}**")
        if st.button("Đăng xuất"):
            logout()
    
    st.title("📂 Cổng thông tin nội bộ")

    # Tạo các Tab chức năng
    tab1, tab2 = st.tabs(["📋 Danh sách Công việc", "💬 Chat Nhóm"])

    # --- TAB 1: CÔNG VIỆC ---
    with tab1:
        st.subheader("Tiến độ công việc")
        # Chỉ tải dữ liệu sheet 2_CONG_VIEC
        df_tasks = get_data_from_google_sheet("2_CONG_VIEC")
        
        # Hiển thị bảng công việc (có thể thêm bộ lọc nếu cần)
        st.dataframe(df_tasks, use_container_width=True)

    # --- TAB 2: CHAT ---
    with tab2:
        st.subheader("Thảo luận nhóm")
        
        # Container chứa lịch sử chat
        chat_container = st.container(height=400)
        
        # Tải dữ liệu sheet 3_CHAT
        df_chat = get_data_from_google_sheet("3_CHAT")
        
        # Hiển thị lịch sử
        with chat_container:
            for index, row in df_chat.iterrows():
                if row['User'] == st.session_state.current_user:
                    st.chat_message("user").write(f"**{row['User']}** ({row['Time']}): {row['Message']}")
                else:
                    st.chat_message("assistant").write(f"**{row['User']}** ({row['Time']}): {row['Message']}")

        # Ô nhập liệu chat
        prompt = st.chat_input("Nhập tin nhắn...")
        if prompt:
            save_message_to_sheet(st.session_state.current_user, prompt)
            st.rerun() # Refresh để hiện tin nhắn mới
