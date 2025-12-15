import streamlit as st
import pandas as pd
from datetime import datetime
from gsheet import load_all_sheets, save_raw_sheet
from utils import get_display_list_multi, lookup_display

# =========================================================
# ✅ TAB TRAO ĐỔI CÔNG VIỆC (ĐÃ FIX LỖI THIẾU CỘT)
# =========================================================
def render_chat_tab():
    st.header("💬 Trao đổi công việc")

    # -----------------------------------------------------
    # ✅ Tải dữ liệu
    # -----------------------------------------------------
    all_sheets = load_all_sheets()
    df_cv = all_sheets.get("7_CONG_VIEC", pd.DataFrame()).copy()
    df_chat = all_sheets.get("10_TRAO_DOI", pd.DataFrame()).copy()
    df_ns = all_sheets.get("1_NHAN_SU", pd.DataFrame()).copy()

    # 🛠️ FIX LỖI KEY ERROR: Tự động thêm cột nếu thiếu
    required_cols = ["ID_CONG_VIEC", "NGUOI_GUI", "NOI_DUNG", "THOI_GIAN", "FILE_DINH_KEM"]
    for col in required_cols:
        if col not in df_chat.columns:
            df_chat[col] = "" # Tạo cột trống nếu chưa có

    if df_cv.empty:
        st.warning("Chưa có công việc nào.")
        return

    # -----------------------------------------------------
    # ✅ Dropdown chọn công việc
    # -----------------------------------------------------
    cv_display, cv_map = get_display_list_multi(
        df_cv,
        id_col="ID_CONG_VIEC",
        cols=["TEN_VIEC", "HAN_CHOT"],
        prefix="Chọn công việc..."
    )

    selected_cv_display = st.selectbox("Chọn công việc", cv_display)
    selected_cv_id = cv_map.get(selected_cv_display, "")

    if not selected_cv_id:
        return

    st.subheader(f"📄 Lịch sử trao đổi của công việc **{selected_cv_id}**")

    # -----------------------------------------------------
    # ✅ Lọc lịch sử chat theo ID công việc
    # -----------------------------------------------------
    # Chuyển về string để so sánh an toàn
    df_chat["ID_CONG_VIEC"] = df_chat["ID_CONG_VIEC"].astype(str)
    df_chat_filtered = df_chat[df_chat["ID_CONG_VIEC"] == str(selected_cv_id)]

    if df_chat_filtered.empty:
        st.info("Chưa có trao đổi nào.")
    else:
        # -----------------------------------------------------
        # ✅ Hiển thị dạng timeline
        # -----------------------------------------------------
        for _, row in df_chat_filtered.iterrows():
            nguoi_gui = lookup_display(
                row["NGUOI_GUI"],
                df_ns,
                "ID_NHAN_SU",
                ["HO_TEN", "CHUC_VU"]
            )

            thoi_gian = row["THOI_GIAN"]
            noi_dung = row["NOI_DUNG"]
            file_dinh_kem = row.get("FILE_DINH_KEM", "")

            with st.container():
                st.markdown(f"**👤 {nguoi_gui}** — *{thoi_gian}*")
                st.write(noi_dung)
                if file_dinh_kem:
                    st.markdown(f"[📎 File đính kèm]({file_dinh_kem})")
                st.markdown("---")

    st.subheader("✏️ Gửi trao đổi mới")

    # -----------------------------------------------------
    # ✅ Form gửi tin nhắn mới
    # -----------------------------------------------------
    ns_display, ns_map = get_display_list_multi(
        df_ns,
        id_col="ID_NHAN_SU",
        cols=["HO_TEN", "CHUC_VU"],
        prefix="Chọn người gửi..."
    )

    nguoi_gui_display = st.selectbox("Người gửi", ns_display)
    nguoi_gui = ns_map.get(nguoi_gui_display, "")

    noi_dung = st.text_area("Nội dung trao đổi")
    file_dinh_kem = st.text_input("Link file đính kèm (nếu có)")

    # -----------------------------------------------------
    # ✅ Nút gửi tin nhắn
    # -----------------------------------------------------
    if st.button("📨 Gửi trao đổi", type="primary"):
        if not nguoi_gui:
            st.error("❌ Vui lòng chọn người gửi.")
            return

        if not noi_dung.strip():
            st.error("❌ Vui lòng nhập nội dung trao đổi.")
            return

        new_row = {
            "ID_CONG_VIEC": selected_cv_id,
            "NGUOI_GUI": nguoi_gui,
            "NOI_DUNG": noi_dung,
            "THOI_GIAN": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "FILE_DINH_KEM": file_dinh_kem,
        }

        # Đảm bảo DataFrame chat có đủ cột trước khi thêm
        for col in required_cols:
             if col not in df_chat.columns:
                 df_chat[col] = ""

        df_new = df_chat.copy()
        df_new.loc[len(df_new)] = new_row

        save_raw_sheet("10_TRAO_DOI", df_new)
        st.success("✅ Đã gửi trao đổi!")
