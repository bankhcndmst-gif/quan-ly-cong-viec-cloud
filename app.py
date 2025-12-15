import streamlit as st
import pandas as pd
from datetime import datetime
import time
import unicodedata
from streamlit_gsheets import GSheetsConnection

# =====================================================
# CẤU HÌNH TRANG
# =====================================================
st.set_page_config(
    page_title="Hệ thống Nội bộ EVNGENCO1",
    layout="wide",
    page_icon="🏢"
)

# =====================================================
# KHÓA TRUY CẬP CỨNG – GIỮ LINK NHƯNG PRIVATE BẰNG CODE
# =====================================================
ALLOWED_DOMAINS = ["@evngenco1.vn"]

if "email_checked" not in st.session_state:
    st.session_state.email_checked = False

if not st.session_state.email_checked:
    st.markdown("## 🔒 HỆ THỐNG NỘI BỘ EVNGENCO1")
    email = st.text_input("Nhập email nội bộ để tiếp tục")

    if st.button("Xác nhận"):
        email = str(email).strip().lower()
        if any(email.endswith(d) for d in ALLOWED_DOMAINS):
            st.session_state.email_checked = True
            st.session_state.precheck_email = email
            st.rerun()
        else:
            st.error("❌ Truy cập bị từ chối. Chỉ cho phép email EVNGENCO1.")
            st.stop()

    st.stop()

# =====================================================
# GOOGLE SHEET CONNECT
# =====================================================
def get_data_from_google_sheet(sheet_name):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(worksheet=sheet_name, ttl=0)
    except:
        return pd.DataFrame()

def save_df_to_google_sheet(sheet_name, df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet=sheet_name, data=df)

def append_chat_to_sheet(user, message):
    conn = st.connection("gsheets", type=GSheetsConnection)
    new_row = pd.DataFrame([{
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User": user,
        "Message": message
    }])
    conn.append(worksheet="10_TRAO_DOI", data=new_row)

# =====================================================
# SESSION STATE
# =====================================================
for k, v in {
    "logged_in": False,
    "current_user": "",
    "user_role": "",
}.items():
    st.session_state.setdefault(k, v)

# =====================================================
# HÀM HỖ TRỢ
# =====================================================
def normalize_text(s):
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

# =====================================================
# LOGIN LOGIC
# =====================================================
def login_logic(username, password):
    df_users = get_data_from_google_sheet("1_NHAN_SU")

    if df_users.empty:
        st.error("⚠️ Không đọc được Sheet 1_NHAN_SU")
        return

    df_users.columns = df_users.columns.str.strip().str.upper()

    if "GMAIL" not in df_users.columns:
        st.error("❌ Thiếu cột GMAIL")
        return

    pass_col = "PASSWORD" if "PASSWORD" in df_users.columns else "MAT_KHAU"
    if pass_col not in df_users.columns:
        st.error("❌ Thiếu cột mật khẩu")
        return

    df_users["GMAIL_CLEAN"] = df_users["GMAIL"].astype(str).str.strip().str.lower()

    input_email = username.strip().lower()
    input_pass = password.strip()

    # 🔒 KHÓA THEO DANH SÁCH NỘI BỘ
    if input_email not in df_users["GMAIL_CLEAN"].values:
        st.error("❌ Tài khoản không nằm trong danh sách nội bộ EVNGENCO1")
        return

    user_row = df_users[df_users["GMAIL_CLEAN"] == input_email]

    if user_row.empty:
        st.error("❌ Email không tồn tại")
        return

    stored_pass = str(user_row.iloc[0][pass_col]).strip()

    if stored_pass != input_pass:
        st.error("❌ Sai mật khẩu")
        return

    # LOGIN OK
    st.session_state.logged_in = True
    st.session_state.current_user = (
        user_row.iloc[0]["HO_TEN"]
        if "HO_TEN" in df_users.columns else "User"
    )

    raw_role = normalize_text(user_row.iloc[0].get("VAI_TRO", "NHAN_VIEN"))
    admin_alias = {"ADMIN", "QUAN TRI", "QTV", "MANAGER", "SEP"}

    st.session_state.user_role = "ADMIN" if raw_role in admin_alias else "NHAN_VIEN"

    st.success(f"✅ Đăng nhập thành công ({st.session_state.user_role})")
    time.sleep(0.3)
    st.rerun()

def logout():
    for k in ["logged_in", "current_user", "user_role", "email_checked"]:
        st.session_state[k] = False if k != "current_user" else ""
    st.rerun()

# =====================================================
# LOGIN UI
# =====================================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Đăng nhập hệ thống")
        username = st.text_input(
            "Email nội bộ",
            value=st.session_state.get("precheck_email", "")
        )
        password = st.text_input("Mật khẩu", type="password")

        if st.button("Đăng nhập", use_container_width=True):
            login_logic(username, password)

    st.stop()

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.write(f"👤 **{st.session_state.current_user}**")
    st.success("🛡️ ADMIN" if st.session_state.user_role == "ADMIN" else "🛡️ NHÂN VIÊN")
    if st.button("Đăng xuất"):
        logout()

# =====================================================
# MAIN UI
# =====================================================
st.title("📂 Quản lý công việc nội bộ")

tabs_name = ["📋 Công việc", "💬 Trao đổi"]
if st.session_state.user_role == "ADMIN":
    tabs_name.append("⚙️ Quản trị")

tabs = st.tabs(tabs_name)

# =====================================================
# TAB 1 – CÔNG VIỆC
# =====================================================
with tabs[0]:
    df_tasks = get_data_from_google_sheet("7_CONG_VIEC")

    if df_tasks.empty:
        st.info("Chưa có dữ liệu")
    elif st.session_state.user_role == "ADMIN":
        edited = st.data_editor(df_tasks, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Lưu công việc"):
            save_df_to_google_sheet("7_CONG_VIEC", edited)
            st.success("Đã lưu")
            st.rerun()
    else:
        col_name = next((c for c in df_tasks.columns if "NGUOI" in c.upper()), None)
        if col_name:
            df_tasks["_CLEAN"] = df_tasks[col_name].astype(str).str.lower()
            st.dataframe(df_tasks[df_tasks["_CLEAN"] == st.session_state.current_user.lower()])
        else:
            st.dataframe(df_tasks)

# =====================================================
# TAB 2 – CHAT
# =====================================================
with tabs[1]:
    df_chat = get_data_from_google_sheet("10_TRAO_DOI")
    if df_chat.empty:
        df_chat = pd.DataFrame(columns=["Time", "User", "Message"])

    for _, r in df_chat.iterrows():
        role = "user" if r["User"] == st.session_state.current_user else "assistant"
        st.chat_message(role).write(f"**{r['User']}**: {r['Message']}")

    if msg := st.chat_input("Nhập nội dung trao đổi"):
        append_chat_to_sheet(st.session_state.current_user, msg)
        st.rerun()

# =====================================================
# TAB 3 – ADMIN
# =====================================================
if st.session_state.user_role == "ADMIN":
    with tabs[2]:
        st.subheader("🔒 Quản trị dữ liệu gốc")

        df_users = get_data_from_google_sheet("1_NHAN_SU")
        hide_cols = [c for c in df_users.columns if "PASS" in c.upper()]
        df_safe = df_users.drop(columns=hide_cols, errors="ignore")

        edited_users = st.data_editor(df_safe, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Lưu nhân sự"):
            save_df_to_google_sheet("1_NHAN_SU", edited_users)
            st.success("Đã lưu")
            st.rerun()
