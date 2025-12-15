import streamlit as st
import pandas as pd
from datetime import datetime
from gsheet import load_all_sheets, append_row
from utils import get_display_list_multi, lookup_display

# =========================================================
# 💬 TAB TRAO ĐỔI CÔNG VIỆC – CHUẨN CLOUD
# =========================================================
def render_chat_tab():
    st.header("💬 Trao đổi công việc")

    # -----------------------------------------------------
    # 1. KIỂM TRA ĐĂNG NHẬP
    # -----------------------------------------------------
    if "user_role" not in st.session_state:
        st.warning("⚠️ Vui lòng đăng nhập để sử dụng chức năng này.")
        st.stop()

    # -----------------------------------------------------
    # 2. TẢI DỮ LIỆU
    # -----------------------------------------------------
    all_sheets = load_all_sheets()

    df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame())
    df_chat = all_sheets.get("10_TRAO_DOI", pd.DataFrame())
    df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame())

    if df_cv.empty:
        st.warning("Chưa có công việc nào.")
        return

    # -----------------------------------------------------
    # 3. ĐẢM BẢO ĐỦ CỘT CHAT
    # -----------------------------------------------------
    required_cols = ["ID_CONG_VIEC", "NGUOI_GUI", "NOI_DUNG", "THOI_GIAN", "FILE_DINH_KEM"]
    for col in required_cols:
        if col not in df_chat.columns:
            df_chat[col] = ""

    # -----------------------------------------------------
    # 4. CHỌN CÔNG VIỆC
    # -----------------------------------------------------
    cv_display, cv_map = get_display_list_multi(
        df_cv,
        id_col="ID_CONG_VIEC",
        cols=["TEN_VIEC", "HAN_CHOT"],
        prefix="Chọn công việc..."
    )

    selected_cv_display = st.selectbox("Chọn công việc", cv_display)
    selected_cv_id = cv_map.get(selected_cv_display)

    if not selected_cv_id:
        return

    st.subheader(f"📄 Lịch sử trao đổi – Công việc **{selected_cv_id}**")

    # -----------------------------------------------------
    # 5. HIỂN THỊ LỊCH SỬ CHAT
    # -----------------------------------------------------
    df_chat["ID_CONG_VIEC"] = df_chat["ID_CONG_VIEC"].astype(str)
    df_chat_filtered = df_chat[df_chat["ID_CONG_VIEC"] == str(selected_cv_id)]

    if df_chat_filtered.empty:
        st.info("Chưa có trao đổi nào.")
    else:
        for _, row in df_chat_filtered.iterrows():
            nguoi_gui = lookup_display(
                row["NGUOI_GUI"],
                df_ns,
                "ID_NHAN_SU",
                ["HO_TEN", "CHUC_VU"]
            )

            with st.container():
                st.markdown(
                    f"**👤 {nguoi_gui}** — *{row['THOI_GIAN']}*"
                )
                st.write(row["NOI_DUNG"])
                if row.get("FILE_DINH_KEM"):
                    st.markdown(f"[📎 File đính kèm]({row['FILE_DINH_KEM']})")
                st.markdown("---")

    # -----------------------------------------------------
    # 6. FORM GỬI TRAO ĐỔI MỚI
    # -----------------------------------------------------
    st.subheader("✏️ Gửi trao đổi mới")

    ns_display, ns_map = get_display_list_multi(
        df_ns,
        id_col="ID_NHAN_SU",
        cols=["HO_TEN", "CHUC_VU"],
        prefix="Chọn người gửi..."
    )

    nguoi_gui_display = st.selectbox("Người gửi", ns_display)
    nguoi_gui = ns_map.get(nguoi_gui_display)

    noi_dung = st.text_area("Nội dung trao đổi")
    file_dinh_kem = st.text_input("Link file đính kèm (nếu có)")

    # -----------------------------------------------------
    # 7. NÚT GỬI (APPEND – KHÔNG GHI ĐÈ)
    # -----------------------------------------------------
    if st.button("📨 Gửi trao đổi", type="primary"):
        if not nguoi_gui:
            st.error("❌ Vui lòng chọn người gửi.")
            return

        if not noi_dung.strip():
            st.error("❌ Vui lòng nhập nội dung trao đổi.")
            return

        new_row = {
            "ID_CONG_VIEC": str(selected_cv_id),
            "NGUOI_GUI": nguoi_gui,
            "NOI_DUNG": noi_dung.strip(),
            "THOI_GIAN": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "FILE_DINH_KEM": file_dinh_kem.strip(),
        }

        try:
            append_row("10_TRAO_DOI", new_row)
            st.success("✅ Đã gửi trao đổi!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi khi gửi trao đổi: {e}")
