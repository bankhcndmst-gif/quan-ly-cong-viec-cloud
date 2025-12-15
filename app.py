import streamlit as st
import pandas as pd
from datetime import datetime
import time
from streamlit_gsheets import GSheetsConnection

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Nội bộ EVNGENCO1", layout="wide", page_icon="🏢")

# --- HÀM KẾT NỐI GOOGLE SHEETS ---
def get_data_from_google_sheet(sheet_name):
    """
    Hàm này kết nối với Google Sheet thông qua st.connection
    ttl=0: Không lưu Cache, luôn lấy dữ liệu mới nhất.
    """
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=sheet_name, ttl=0)
        return df
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối Google Sheet: {e}")
        return pd.DataFrame()

# --- HÀM LƯU TIN NHẮN (Tạm thời lưu vào phiên làm việc) ---
def save_message_local(user, message):
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

# --- KHỞI TẠO SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

# --- LOGIC ĐĂNG NHẬP (PHIÊN BẢN ROBUST - CHỐNG LỖI) ---
def login_logic(username, password):
    # 1. Tải dữ liệu từ Sheet 1_NHAN_SU
    df_users = get_data_from_google_sheet("1_NHAN_SU")
    
    if df_users.empty:
        st.error("Không tải được dữ liệu nhân sự. Vui lòng kiểm tra lại kết nối!")
        return

    # 2. Chuẩn hóa tên cột (Viết hoa hết & xóa khoảng trắng)
    # Giúp máy hiểu: "Gmail" == "GMAIL" == "GMAIL "
    df_users.columns = df_users.columns.str.strip().str.upper()

    # [DEBUG] In ra để kiểm tra nếu cần (Xóa dòng này sau khi chạy ổn)
    # st.write("Các cột máy đọc được:", df_users.columns.tolist())

    # 3. Kiểm tra cột bắt buộc
    if 'GMAIL' not in df_users.columns:
        st.error("❌ Lỗi: Không tìm thấy cột 'GMAIL' trong file Google Sheet.")
        st.info(f"Các cột máy đọc được là: {df_users.columns.tolist()}")
        return
    
    # Tìm cột mật khẩu (Có thể là PASSWORD hoặc MAT_KHAU tùy file)
    # Ưu tiên tìm 'PASSWORD', nếu không thấy thì tìm 'MAT_KHAU'
    pass_col = 'PASSWORD'
    if 'PASSWORD' not in df_users.columns:
        if 'MAT_KHAU' in df_users.columns:
            pass_col = 'MAT_KHAU'
        else:
            st.error("❌ Lỗi: Không tìm thấy cột 'PASSWORD' hoặc 'MAT_KHAU'.")
            return

    # 4. Xử lý Logic So sánh
    # Làm sạch dữ liệu nhập vào
    input_email = str(username).strip().lower()
    input_pass = str(password).strip()

    # Tạo cột phụ chứa Email sạch để so sánh
    df_users['GMAIL_CLEAN'] = df_users['GMAIL'].astype(str).str.strip().str.lower()
    
    # Tìm dòng có Email trùng
    user_row = df_users[df_users['GMAIL_CLEAN'] == input_email]
    
    if not user_row.empty:
        # Lấy mật khẩu từ Sheet
        stored_pass = str(user_row.iloc[0][pass_col]).strip()
        
        # So sánh mật khẩu
        if stored_pass == input_pass:
            st.session_state.logged_in = True
            
            # Lấy tên hiển thị
            if 'HO_TEN' in df_users.columns:
                st.session_state.current_user = user_row.iloc[0]['HO_TEN']
            else:
                st.session_state.current_user = "User"
            
            # Lấy vai trò (Admin/NhanVien)
            if 'VAI_TRO' in df_users.columns:
                st.session_state.user_role = str(user_row.iloc[0]['VAI_TRO']).strip().upper()
            else:
                st.session_state.user_role = "NHAN_VIEN"

            st.success("✅ Đăng nhập thành công!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ Sai mật khẩu!")
    else:
        st.error(f"❌ Email không tồn tại: {input_email}")

# --- HÀM ĐĂNG XUẤT ---
def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.session_state.user_role = ""
    st.rerun()

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================

if not st.session_state.logged_in:
    # --- MÀN HÌNH ĐĂNG NHẬP ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Cổng thông tin EVNGENCO1")
        st.info("Vui lòng đăng nhập bằng tài khoản được cấp.")
        
        username_input = st.text_input("Địa chỉ Gmail")
        password_input = st.text_input("Mật khẩu", type="password")
        
        if st.button("Đăng nhập", use_container_width=True):
            if not username_input or not password_input:
                st.warning("Vui lòng nhập đầy đủ thông tin!")
            else:
                login_logic(username_input, password_input)

else:
    # --- MÀN HÌNH SAU KHI ĐĂNG NHẬP ---
    
    # Sidebar thông tin
    with st.sidebar:
        st.write(f"👤 Xin chào: **{st.session_state.current_user}**")
        st.write(f"🛡️ Vai trò: `{st.session_state.user_role}`")
        if st.button("Đăng xuất"):
            logout()
    
    st.title("📂 Quản lý công việc nội bộ")

    # Phân quyền hiển thị Tab
    tab_titles = ["📋 Danh sách Công việc", "💬 Thảo luận Nhóm"]
    if st.session_state.user_role == "ADMIN":
        tab_titles.append("⚙️ Quản trị (Admin)")
    
    tabs = st.tabs(tab_titles)

    # --- TAB 1: CÔNG VIỆC ---
    with tabs[0]:
        st.subheader("Tiến độ công việc")
        df_tasks = get_data_from_google_sheet("7_CONG_VIEC")
        
        if not df_tasks.empty:
            # Nếu là NHAN_VIEN -> Chỉ thấy việc của mình
            if st.session_state.user_role == "NHAN_VIEN":
                # Giả sử cột người phụ trách tên là "Người thực hiện" hoặc "Phụ trách"
                # Code này tìm cột nào chứa tên "Người" hoặc "Phụ trách" để lọc
                col_name_task = next((c for c in df_tasks.columns if "Người" in c or "trách" in c), None)
                
                if col_name_task:
                    # Lọc theo tên người đang đăng nhập
                    df_display = df_tasks[df_tasks[col_name_task] == st.session_state.current_user]
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.warning("Không tìm thấy cột người phụ trách để lọc dữ liệu.")
                    st.dataframe(df_tasks, use_container_width=True)
            else:
                # Admin thấy hết
                st.dataframe(df_tasks, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu công việc.")

    # --- TAB 2: CHAT ---
    with tabs[1]:
        st.subheader("Kênh trao đổi")
        
        # Load dữ liệu chat ban đầu từ Sheet (chỉ đọc)
        if "chat_data" not in st.session_state:
            df_chat_sheet = get_data_from_google_sheet("10_TRAO_DOI")
            # Chuẩn hóa cột Chat cho đồng nhất
            if not df_chat_sheet.empty and len(df_chat_sheet.columns) >= 3:
                 # Đổi tên 3 cột đầu tiên thành Time, User, Message cho dễ xử lý
                 df_chat_sheet.columns.values[0] = "Time"
                 df_chat_sheet.columns.values[1] = "User"
                 df_chat_sheet.columns.values[2] = "Message"
                 st.session_state.chat_data = df_chat_sheet
            else:
                 st.session_state.chat_data = pd.DataFrame(columns=["Time", "User", "Message"])

        # Hiển thị khung chat
        chat_container = st.container(height=400)
        with chat_container:
            for idx, row in st.session_state.chat_data.iterrows():
                role = "user" if row['User'] == st.session_state.current_user else "assistant"
                st.chat_message(role).write(f"**{row['User']}**: {row['Message']}")

        # Nhập tin nhắn
        if prompt := st.chat_input("Nhập nội dung..."):
            save_message_local(st.session_state.current_user, prompt)
            st.rerun()

    # --- TAB 3: ADMIN (Chỉ hiện nếu là ADMIN) ---
    if st.session_state.user_role == "ADMIN" and len(tabs) > 2:
        with tabs[2]:
            st.warning("Khu vực quản trị hệ thống")
            st.write("Dữ liệu nhân sự (Đã ẩn mật khẩu):")
            df_admin_view = get_data_from_google_sheet("1_NHAN_SU")
            
            # Ẩn cột Password khi hiển thị
            safe_cols = [c for c in df_admin_view.columns if "PASS" not in c.upper() and "MAT_KHAU" not in c.upper()]
            st.dataframe(df_admin_view[safe_cols], use_container_width=True)

