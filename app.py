import streamlit as st
import pandas as pd
from datetime import datetime
import time
from streamlit_gsheets import GSheetsConnection

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Nội bộ EVNGENCO1", layout="wide", page_icon="🏢")

# --- HÀM KẾT NỐI GOOGLE SHEETS ---
def get_data_from_google_sheet(sheet_name):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # ttl=0 để luôn lấy dữ liệu mới nhất (không lưu cache)
        df = conn.read(worksheet=sheet_name, ttl=0)
        return df
    except Exception as e:
        # Nếu lỗi (ví dụ chưa có sheet), trả về DataFrame rỗng để không sập App
        return pd.DataFrame()

# --- HÀM LƯU TIN NHẮN (Tạm thời) ---
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

# --- KHỞI TẠO TRẠNG THÁI (SESSION STATE) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

# --- LOGIC ĐĂNG NHẬP (THÔNG MINH HƠN) ---
def login_logic(username, password):
    # 1. Đọc Sheet Nhân sự
    df_users = get_data_from_google_sheet("1_NHAN_SU")
    
    if df_users.empty:
        st.error("⚠️ Không đọc được dữ liệu từ Sheet '1_NHAN_SU'. Vui lòng kiểm tra tên Sheet.")
        return

    # 2. Chuẩn hóa tên cột (Viết hoa hết để tránh lỗi gõ nhầm)
    df_users.columns = df_users.columns.str.strip().str.upper()

    # Kiểm tra cột GMAIL
    if 'GMAIL' not in df_users.columns:
        st.error("❌ File thiếu cột 'GMAIL'.")
        return
    
    # Tìm cột mật khẩu
    pass_col = 'PASSWORD'
    if 'PASSWORD' not in df_users.columns:
        if 'MAT_KHAU' in df_users.columns:
            pass_col = 'MAT_KHAU'
        else:
            st.error("❌ File thiếu cột mật khẩu ('PASSWORD' hoặc 'MAT_KHAU').")
            return

    # 3. Xử lý đăng nhập
    input_email = str(username).strip().lower()
    input_pass = str(password).strip()

    # Tạo cột email sạch để so sánh
    df_users['GMAIL_CLEAN'] = df_users['GMAIL'].astype(str).str.strip().str.lower()
    
    # Tìm dòng user
    user_row = df_users[df_users['GMAIL_CLEAN'] == input_email]
    
    if not user_row.empty:
        stored_pass = str(user_row.iloc[0][pass_col]).strip()
        
        if stored_pass == input_pass:
            st.session_state.logged_in = True
            
            # Lấy tên hiển thị
            if 'HO_TEN' in df_users.columns:
                st.session_state.current_user = user_row.iloc[0]['HO_TEN']
            else:
                st.session_state.current_user = "User"
            
            # --- QUAN TRỌNG: XỬ LÝ VAI TRÒ (ROLE) ---
            raw_role = "NHAN_VIEN" # Mặc định là nhân viên
            if 'VAI_TRO' in df_users.columns:
                # Lấy dữ liệu thô từ Excel và viết hoa lên
                raw_role = str(user_row.iloc[0]['VAI_TRO']).strip().upper()
            
            # Chuẩn hóa các từ đồng nghĩa về "ADMIN"
            # Nếu trong file ghi là "Quản trị", "Admin", "QTV"... đều tính là ADMIN
            if raw_role in ["ADMIN", "QUẢN TRỊ", "QUAN TRI", "QUAN_TRI", "MANAGER", "SẾP"]:
                st.session_state.user_role = "ADMIN"
            else:
                st.session_state.user_role = "NHAN_VIEN"

            st.success(f"✅ Đăng nhập thành công! (Quyền: {st.session_state.user_role})")
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
    # --- MÀN HÌNH LOGIN ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Cổng thông tin EVNGENCO1")
        
        username_input = st.text_input("Địa chỉ Gmail")
        password_input = st.text_input("Mật khẩu", type="password")
        
        if st.button("Đăng nhập", use_container_width=True):
            login_logic(username_input, password_input)

else:
    # --- SIDEBAR (THANH BÊN TRÁI) ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state.current_user}**")
        
        # Hiển thị rõ quyền để bạn kiểm tra
        if st.session_state.user_role == "ADMIN":
            st.success(f"🛡️ Quyền: ADMIN")
        else:
            st.info(f"🛡️ Quyền: NHÂN VIÊN")
            
        if st.button("Đăng xuất"):
            logout()
    
    st.title("📂 Quản lý công việc nội bộ")

    # --- CẤU HÌNH CÁC TAB ---
    # Mặc định có 2 tab
    tab_titles = ["📋 Danh sách Công việc", "💬 Thảo luận (10_TRAO_DOI)"]
    
    # Nếu là ADMIN thì thêm Tab thứ 3
    if st.session_state.user_role == "ADMIN":
        tab_titles.append("⚙️ Quản trị & Dữ liệu gốc")
    
    tabs = st.tabs(tab_titles)

    # --- TAB 1: CÔNG VIỆC (7_CONG_VIEC) ---
    with tabs[0]:
        st.subheader("Tiến độ công việc (Sheet: 7_CONG_VIEC)")
        df_tasks = get_data_from_google_sheet("7_CONG_VIEC")
        
        if not df_tasks.empty:
            if st.session_state.user_role == "NHAN_VIEN":
                # Logic lọc cho nhân viên
                col_name_task = next((c for c in df_tasks.columns if "Người" in c or "trách" in c), None)
                if col_name_task:
                    # Chỉ hiện việc của mình
                    df_display = df_tasks[df_tasks[col_name_task] == st.session_state.current_user]
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.warning("Không tìm thấy cột 'Người phụ trách' để lọc. Hiển thị toàn bộ.")
                    st.dataframe(df_tasks, use_container_width=True)
            else:
                # ADMIN: Xem toàn bộ
                st.dataframe(df_tasks, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu công việc hoặc tên Sheet sai.")

    # --- TAB 2: TRAO ĐỔI (10_TRAO_DOI) ---
    with tabs[1]:
        st.subheader("Kênh trao đổi nội bộ")
        
        # Load dữ liệu từ sheet 10_TRAO_DOI
        if "chat_data" not in st.session_state:
            df_chat_sheet = get_data_from_google_sheet("10_TRAO_DOI") # <-- ĐÃ SỬA TÊN
            
            # Nếu sheet có dữ liệu, chuẩn hóa tên cột để hiển thị
            if not df_chat_sheet.empty and len(df_chat_sheet.columns) >= 3:
                 # Copy dữ liệu ra để không ảnh hưởng gốc
                 df_temp = df_chat_sheet.copy()
                 # Giả định 3 cột đầu là: Thời gian, Người gửi, Nội dung
                 df_temp.columns.values[0] = "Time"
                 df_temp.columns.values[1] = "User"
                 df_temp.columns.values[2] = "Message"
                 st.session_state.chat_data = df_temp
            else:
                 st.session_state.chat_data = pd.DataFrame(columns=["Time", "User", "Message"])

        # Khung chat cuộn
        chat_container = st.container(height=400)
        with chat_container:
            for idx, row in st.session_state.chat_data.iterrows():
                # Phân biệt tin nhắn của mình và người khác
                role = "user" if row['User'] == st.session_state.current_user else "assistant"
                st.chat_message(role).write(f"**{row['User']}**: {row['Message']}")

        # Ô nhập tin nhắn
        if prompt := st.chat_input("Nhập nội dung trao đổi..."):
            save_message_local(st.session_state.current_user, prompt)
            st.rerun()

    # --- TAB 3: ADMIN (Chỉ Admin mới thấy) ---
    if st.session_state.user_role == "ADMIN" and len(tabs) > 2:
        with tabs[2]:
            st.error("🔒 Khu vực Quản trị viên - Dữ liệu gốc")
            
            st.write("### 1. Dữ liệu Nhân sự (1_NHAN_SU)")
            df_users_view = get_data_from_google_sheet("1_NHAN_SU")
            # Ẩn cột mật khẩu cho an toàn, dù là Admin
            safe_cols = [c for c in df_users_view.columns if "PASS" not in c.upper() and "MAT_KHAU" not in c.upper()]
            st.dataframe(df_users_view[safe_cols], use_container_width=True)

            st.write("### 2. Dữ liệu Chat Gốc (10_TRAO_DOI)")
            st.dataframe(get_data_from_google_sheet("10_TRAO_DOI"), use_container_width=True)
