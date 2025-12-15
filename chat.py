import streamlit as st
import pandas as pd
from datetime import datetime

from gsheet import load_all_sheets, save_raw_sheet
from utils import get_display_list_multi, lookup_display

# =========================================================
# 💬 TAB TRAO ĐỔI CÔNG VIỆC
# =========================================================
def render_chat_tab():
    st.header("💬 Trao đổi công việc")

    # -----------------------------------------------------
    # 1️⃣ Load dữ liệu
    # -----------------------------------------------------
    all_sheets = load_all_sheets()

    df_cv   = all_sheets.get("7_CONG_VIEC", pd.DataFrame()).copy()
    df_chat = all_sheets.get("10_TRAO_DOI", pd.DataFrame()).copy()
    df_ns   = all_sheets.get("1_NHAN_SU", pd.DataFrame()).copy()

    if df_cv.empty:
        st.warning("⚠️ Chưa có công việc nào.")
        return

    # -----------------------------------------------------
    # 2️⃣ Chuẩn hóa cấu trúc Sheet CHAT
    # -----------------------------------------------------
    REQUIRED_COLS = [
        "ID_CONG_VIEC",
        "NGUOI_GUI",
        "NOI_DUNG",
        "THOI_GIAN",
        "FILE_DINH_KEM"
    ]

    for col in REQUIRED_COLS:
        if col not in df_chat.columns:
            df_chat[col] = ""

    # -----------------------------------------------------
    # 3️⃣ Chọn công việc
    # -----------------------------------------------------
    cv_display, cv_map = get_display_list_multi(
        df_cv,
        id_col="ID_CONG_VIEC",
        cols=["TEN_VIEC", "HAN_CHOT"],
        prefix="🔽 Chọn công việc..."
    )

    selected_display = st.selectbox("Công việc", cv_display)
    selected_cv_id = cv_map.get(selected_display)

    if not selected_cv_id:
        st.info("ℹ️ Vui lòng chọn công việc để xem trao đổi.")
        return

    st.subheader(f"📄 Lịch sử trao đổi – **{selected_cv_id}**")

    # -----------------------------------------------------
    # 4️⃣ Lọc & hiển thị lịch sử chat
    # -----------------------------------------------------
    df_chat["ID_CONG_VIEC"] = df_chat["ID_CONG_VIEC"].astype(str)
    df_view = df_chat[df_chat["ID_CONG_VIEC"] == str(selected_cv_id)]

    if df_view.empty:
        st.info("💬 Chưa có trao đổi nào.")
    else:
        for _, row in df_view.iterrows():
            nguoi_gui = lookup_display(
                row["NGUOI_GUI"],
                df_ns,
                "ID_NHAN_SU",
                ["HO_TEN", "CHUC_VU"]
            )

            with st.container():
                st.markdown(
                    f"""
                    **👤 {nguoi_gui}**  
                    ⏱️ *{row['THOI_GIAN']}*
                    """
                )
                st.write(row["NOI_DUNG"])

                if row.get("FILE_DINH_KEM"):
                    st.markdown(f"📎 [File đính kèm]({row['FILE_DINH_KEM']})")

                st.markdown("---")

    # -----------------------------------------------------
    # 5️⃣ Form gửi trao đổi mới
    # -----------------------------------------------------
    st.subheader("✏️ Gửi trao đổi mới")

    ns_display, ns_map = get_display_list_multi(
        df_ns,
        id_col="ID_NHAN_SU",
        cols=["HO_TEN", "CHUC_VU"],
        prefix="👤 Chọn người gửi..."
    )

    nguoi_gui_display = st.selectbox("Người gửi", ns_display)
    nguoi_gui_id = ns_map.get(nguoi_gui_display)

    noi_dung = st.text_area("Nội dung trao đổi", height=120)
    file_dinh_kem = st.text_input("Link file đính kèm (nếu có)")

    # -----------------------------------------------------
    # 6️⃣ Gửi & lưu
    # -----------------------------------------------------
    if st.button("📨 Gửi trao đổi", type="primary"):
        if not nguoi_gui_id:
            st.error("❌ Vui lòng chọn người gửi.")
            return

        if not noi_dung.strip():
            st.error("❌ Nội dung trao đổi không được để trống.")
            return

        new_row = {
            "ID_CONG_VIEC": selected_cv_id,
            "NGUOI_GUI": nguoi_gui_id,
            "NOI_DUNG": noi_dung.strip(),
            "THOI_GIAN": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "FILE_DINH_KEM": file_dinh_kem.strip(),
        }

        df_new = df_chat.copy()
        df_new.loc[len(df_new)] = new_row

        save_raw_sheet("10_TRAO_DOI", df_new)

        st.success("✅ Đã gửi trao đổi thành công!")
        st.cache_data.clear()
        st.rerun()
