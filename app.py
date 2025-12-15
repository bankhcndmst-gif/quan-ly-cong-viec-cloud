import streamlit as st
import pandas as pd
from datetime import datetime
import time
# Thêm dòng này lên đầu file app.py cùng các dòng import khác
from streamlit_gsheets import GSheetsConnection 

# --- HÀM KẾT NỐI DỮ LIỆU THẬT ---
def get_data_from_google_sheet(sheet_name):
    try:
        # Tạo kết nối
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Đọc dữ liệu (ttl=0 để luôn lấy mới nhất, không lưu cache cũ)
        df = conn.read(worksheet=sheet_name, ttl=0)
        
        # Nếu đọc được, trả về dataframe
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheet: {e}")
        return pd.DataFrame() # Trả về bảng rỗng nếu lỗi
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

# --- HÀM XỬ LÝ ĐĂNG NHẬP (PHIÊN BẢN FIX LỖI TỪ ẢNH) ---
def login_logic(username, password):
    # 1. Lấy dữ liệu
    df_users = get_data_from_google_sheet("1_NHAN_SU")
    
    # [DEBUG QUAN TRỌNG] In ra để xem Code có đọc đủ cột không
    # Nếu danh sách này không có 'GMAIL', nghĩa là code kết nối dữ liệu bị dừng ở cột trống
    st.write("📋 Các cột máy đọc được:", df_users.columns.tolist())
    
    # 2. CHUẨN HÓA TÊN CỘT (Để xử lý việc 'Password' vs 'PASSWORD')
    # Code này sẽ đổi toàn bộ tên cột thành CHỮ HOA và XÓA KHOẢNG TRẮNG
    df_users.columns = df_users.columns.str.strip().str.upper()
    
    # Kiểm tra lại sau khi chuẩn hóa
    if 'GMAIL' not in df_users.columns:
        st.error("❌ Lỗi: Code không đọc được cột 'GMAIL'. Có thể do cột này nằm quá xa hoặc bị ngắt bởi cột trống.")
        return
    
    if 'PASSWORD' not in df_users.columns: # Vì đã upper() nên tìm PASSWORD
        st.error("❌ Lỗi: Không tìm thấy cột 'Password' (Code đang tìm 'PASSWORD').")
        return

    # 3. LOGIC SO SÁNH (Loại bỏ mọi khả năng lỗi do dấu cách)
    
    # Làm sạch dữ liệu nhập vào (chữ thường + xóa cách)
    input_email_clean = str(username).strip().lower()
    input_pass_clean = str(password).strip()
    
    # Tạo cột phụ chứa Email đã làm sạch để so sánh
    df_users['GMAIL_CLEAN'] = df_users['GMAIL'].astype(str).str.strip().str.lower()
    
    # Tìm dòng dữ liệu khớp Email
    user_row = df_users[df_users['GMAIL_CLEAN'] == input_email_clean]
    
    if not user_row.empty:
        # Lấy mật khẩu từ file (Lưu ý: Cột giờ tên là PASSWORD do bước 2)
        stored_password = str(user_row.iloc[0]['PASSWORD']).strip()
        
        # So sánh mật khẩu
        if stored_password == input_pass_clean:
            # --- THÀNH CÔNG ---
            st.session_state.logged_in = True
            
            # Lấy tên hiển thị
            if 'HO_TEN' in df_users.columns:
                st.session_state.current_user = user_row.iloc[0]['HO_TEN']
            else:
                st.session_state.current_user = "User"
            
            # Lấy vai trò (VAI_TRO)
            if 'VAI_TRO' in df_users.columns:
                st.session_state.user_role = str(user_row.iloc[0]['VAI_TRO']).strip().upper()
            else:
                st.session_state.user_role = "NHAN_VIEN"
                
            st.success("✅ Đăng nhập thành công!")
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"❌ Sai mật khẩu! (Hệ thống nhận: {input_pass_clean})")
    else:
        st.error(f"❌ Email không tồn tại: '{input_email_clean}'")
        st.write("Danh sách Email hệ thống đang có:", df_users['GMAIL_CLEAN'].tolist())
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


