import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- GIẢ LẬP KẾT NỐI DỮ LIỆU ---
# (Trong thực tế, bạn thay phần này bằng code kết nối Google Sheets của bạn)
def get_data_from_google_sheet(sheet_name):
    # Giả lập dữ liệu trả về từ Google Sheet
    
    if sheet_name == "1_NHAN_SU":
        # QUAN TRỌNG: Tên cột ở đây phải khớp với tên cột trong file Google Sheet thật của bạn
        return pd.DataFrame({
            "GMAIL": ["admin@gmail.com", "nhanvien1@gmail.com"], # Cột GMAIL
            "Password": ["123456", "123"],                        # Cột Password
            "HO_TEN": ["Quản trị viên", "Nguyễn Văn A"]             # Cột HO_TEN
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
    # Nối tin nhắn mới vào dataframe
    if "chat_data" in st.session_state:
        st.session_state.chat_data = pd.concat(
            [st.session_state.chat_data, pd.DataFrame([new_msg])], 
            ignore_index=True
        )

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Quản lý Công việc", layout="wide")

# --- KHỞI TẠO SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# --- HÀM XỬ LÝ ĐĂNG NHẬP ---
def login_logic(username, password):
    # 1. Lấy dữ liệu mật
    df_users = get_data_from_google_sheet("1_NHAN_SU")
    
    # Chuẩn hóa tên cột (Xóa khoảng trắng thừa ở tiêu đề cột nếu có)
    df_users.columns = df_users.columns.str.strip()
    
    # Kiểm tra xem có cột GMAIL không
    if 'GMAIL' not in df_users.columns:
        st.error(f"Lỗi: Không tìm thấy cột 'GMAIL' trong file dữ liệu. Các cột hiện có: {df_users.columns.tolist()}")
        return

    # 2. Kiểm tra khớp GMAIL (Dùng .strip() để xóa khoảng trắng thừa khi nhập)
    # Chuyển cả 2 về string để so sánh an toàn
    username = str(username).strip()
    
    # Lọc ra dòng có GMAIL trùng
    user_row = df_users[df_users['GMAIL'].astype(str).str.strip() == username]
    
    if not user_row.empty:
        # Lấy mật khẩu từ dòng tìm được
        stored_password = user_row.iloc[0]['Password']
        
        # So sánh mật khẩu (chuyển về chuỗi để so sánh chính xác)
        if str(stored_password).strip() == str(password).strip():
            st.session_state.logged_in = True
            # Lấy tên hiển thị từ cột HO_TEN
            if 'HO_TEN' in df_users.columns:
                st.session_state.current_user = user_row.iloc[0]['HO_TEN']
            else:
                st.session_state.current_user = username # Nếu không có cột tên thì dùng mail tạm
                
            st.success("Đăng nhập thành công!")
            time.sleep(1)
            st.rerun() 
        else:
            st.error("Sai mật khẩu!")
    else:
        st.error("Tài khoản Gmail không tồn tại trong hệ thống!")

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
        st.info("Tài khoản thử nghiệm: admin@gmail.com / MK: 123456") # Gợi ý pass
        
        user_input = st.text_input("Địa chỉ Gmail")
        pass_input = st.text_input("Mật khẩu", type="password")
        
        if st.button("Đăng nhập", use_container_width=True):
            if not user_input or not pass_input:
                st.warning("Vui lòng nhập đầy đủ thông tin!")
            else:
                login_logic(user_input, pass_input)

else:
    # ----------------------------------
    # TRƯỜNG HỢP 2: ĐÃ ĐĂNG NHẬP
    # ----------------------------------
    
    with st.sidebar:
        st.write(f"Xin chào, **{st.session_state.current_user}**")
        if st.button("Đăng xuất"):
            logout()
    
    st.title("📂 Cổng thông tin nội bộ")

    tab1, tab2 = st.tabs(["📋 Danh sách Công việc", "💬 Chat Nhóm"])

    # --- TAB 1: CÔNG VIỆC ---
    with tab1:
        st.subheader("Tiến độ công việc")
        df_tasks = get_data_from_google_sheet("2_CONG_VIEC")
        st.dataframe(df_tasks, use_container_width=True)

    # --- TAB 2: CHAT ---
    with tab2:
        st.subheader("Thảo luận nhóm")
        chat_container = st.container(height=400)
        df_chat = get_data_from_google_sheet("3_CHAT")
        
        with chat_container:
            if not df_chat.empty and 'User' in df_chat.columns:
                for index, row in df_chat.iterrows():
                    role = "user" if row['User'] == st.session_state.current_user else "assistant"
                    st.chat_message(role).write(f"**{row['User']}** ({row['Time']}): {row['Message']}")
            else:
                st.write("Chưa có tin nhắn nào.")

        prompt = st.chat_input("Nhập tin nhắn...")
        if prompt:
            save_message_to_sheet(st.session_state.current_user, prompt)
            st.rerun()
