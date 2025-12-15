import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- GIẢ LẬP KẾT NỐI DỮ LIỆU ---
def get_data_from_google_sheet(sheet_name):
    # Thay code này bằng code kết nối thực tế của bạn
    
    if sheet_name == "1_NHAN_SU":
        # Thêm cột VAI_TRO vào dữ liệu
        return pd.DataFrame({
            "GMAIL": ["admin@gmail.com", "nhanvien@gmail.com"], 
            "Password": ["123456", "123"],
            "HO_TEN": ["Sếp Tổng", "Nhân viên A"],
            "VAI_TRO": ["ADMIN", "NHAN_VIEN"] # <-- Cột mới quan trọng
        })
        
    elif sheet_name == "2_CONG_VIEC":
        return pd.DataFrame({
            "Mã CV": ["CV01", "CV02", "CV03"],
            "Tên việc": ["Duyệt lương", "Viết báo cáo", "Sửa máy in"],
            "Trạng thái": ["Chờ duyệt", "Đang làm", "Mới"],
            "Người phụ trách": ["Sếp Tổng", "Nhân viên A", "Nhân viên A"]
        })
        
    elif sheet_name == "3_CHAT":
        if "chat_data" not in st.session_state:
            st.session_state.chat_data = pd.DataFrame([
                {"Time": "08:00", "User": "Sếp Tổng", "Message": "Hôm nay họp lúc 9h nhé"}
            ])
        return st.session_state.chat_data
        
    return pd.DataFrame()

def save_message_to_sheet(user, message):
    new_msg = {
        "Time": datetime.now().strftime("%H:%M:%S"), 
        "User": user, 
        "Message": message
    }
    if "chat_data" in st.session_state:
        st.session_state.chat_data = pd.concat(
            [st.session_state.chat_data, pd.DataFrame([new_msg])], 
            ignore_index=True
        )

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Nội bộ", layout="wide")

# --- KHỞI TẠO SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "user_role" not in st.session_state:  # <-- Biến lưu vai trò
    st.session_state.user_role = ""

# --- HÀM XỬ LÝ ĐĂNG NHẬP ---
def login_logic(username, password):
    df_users = get_data_from_google_sheet("1_NHAN_SU")
    df_users.columns = df_users.columns.str.strip() # Xóa khoảng trắng thừa ở tên cột
    
    # Kiểm tra đủ cột chưa
    required_cols = ['GMAIL', 'Password', 'HO_TEN', 'VAI_TRO']
    for col in required_cols:
        if col not in df_users.columns:
            st.error(f"Thiếu cột '{col}' trong Google Sheet!")
            return

    # Kiểm tra User/Pass
    username = str(username).strip()
    user_row = df_users[df_users['GMAIL'].astype(str).str.strip() == username]
    
    if not user_row.empty:
        stored_password = user_row.iloc[0]['Password']
        if str(stored_password).strip() == str(password).strip():
            
            # --- ĐĂNG NHẬP THÀNH CÔNG ---
            st.session_state.logged_in = True
            st.session_state.current_user = user_row.iloc[0]['HO_TEN']
            
            # Lấy vai trò và chuẩn hóa về chữ in hoa (để tránh lỗi Admin/admin)
            role = str(user_row.iloc[0]['VAI_TRO']).strip().upper()
            st.session_state.user_role = role
            
            st.success(f"Xin chào {role}: {st.session_state.current_user}")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Sai mật khẩu!")
    else:
        st.error("Email không tồn tại!")

def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.session_state.user_role = ""
    st.rerun()

# ==========================================
# GIAO DIỆN CHÍNH (MAIN UI)
# ==========================================

if not st.session_state.logged_in:
    # --- GIAO DIỆN ĐĂNG NHẬP ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.header("🔐 Đăng nhập")
        st.info("Test Admin: admin@gmail.com (123456) | Test NV: nhanvien@gmail.com (123)")
        
        u = st.text_input("Gmail")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Vào hệ thống", use_container_width=True):
            login_logic(u, p)

else:
    # --- GIAO DIỆN SAU KHI LOGIN ---
    
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        st.write(f"Người dùng: **{st.session_state.current_user}**")
        st.write(f"Vai trò: **{st.session_state.user_role}**") # Hiển thị vai trò
        st.divider()
        if st.button("Đăng xuất"):
            logout()
    
    st.title("📂 Cổng thông tin nội bộ")

    # --- LOGIC PHÂN QUYỀN HIỂN THỊ TAB ---
    
    # Mặc định ai cũng thấy 2 tab này
    tabs_list = ["📋 Công việc chung", "💬 Chat Nhóm"]
    
    # Nếu là ADMIN thì thêm tab quản trị
    if st.session_state.user_role == "ADMIN":
        tabs_list.append("⚙️ Quản trị (Admin Only)")
        
    # Tạo Tabs
    tabs = st.tabs(tabs_list)

    # --- TAB 1: CÔNG VIỆC ---
    with tabs[0]:
        st.subheader("Danh sách công việc")
        df_tasks = get_data_from_google_sheet("2_CONG_VIEC")
        
        # Ví dụ phân quyền dữ liệu: 
        # Nếu là NHAN_VIEN -> Chỉ thấy việc của mình
        # Nếu là ADMIN -> Thấy hết
        if st.session_state.user_role == "NHAN_VIEN":
            st.warning("Bạn đang xem ở chế độ Nhân viên (Chỉ thấy việc được giao)")
            df_display = df_tasks[df_tasks['Người phụ trách'] == st.session_state.current_user]
        else:
            st.success("Bạn đang xem ở chế độ Admin (Thấy tất cả)")
            df_display = df_tasks
            
        st.dataframe(df_display, use_container_width=True)

    # --- TAB 2: CHAT ---
    with tabs[1]:
        st.subheader("Thảo luận")
        chat_cont = st.container(height=400)
        df_chat = get_data_from_google_sheet("3_CHAT")
        with chat_cont:
            if not df_chat.empty and 'User' in df_chat.columns:
                for idx, row in df_chat.iterrows():
                    role = "user" if row['User'] == st.session_state.current_user else "assistant"
                    st.chat_message(role).write(f"**{row['User']}**: {row['Message']}")
        
        txt = st.chat_input("Nhập tin...")
        if txt:
            save_message_to_sheet(st.session_state.current_user, txt)
            st.rerun()

    # --- TAB 3: QUẢN TRỊ (CHỈ ADMIN MỚI THẤY) ---
    if st.session_state.user_role == "ADMIN":
        with tabs[2]:
            st.error("Khu vực này chỉ dành cho Admin!")
            st.write("Tại đây Admin có thể xem danh sách nhân sự (nhưng code này đang ẩn pass).")
            
            # Admin được phép xem danh sách nhân viên (nhưng giấu pass đi)
            df_users_view = get_data_from_google_sheet("1_NHAN_SU")
            if 'Password' in df_users_view.columns:
                df_users_view = df_users_view.drop(columns=['Password']) # Bảo mật: Xóa cột pass trước khi hiện
            st.dataframe(df_users_view)
