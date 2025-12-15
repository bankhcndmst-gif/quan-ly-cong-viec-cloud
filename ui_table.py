import streamlit as st
from gsheet_service import get_data_from_google_sheet, save_df_to_google_sheet

def render_table(
    sheet_name: str,
    editor_key: str,
    title: str = "",
    hide_cols: list | None = None
):
    """
    Chuẩn hệ thống:
    - ADMIN: sửa / thêm / xoá
    - USER: chỉ xem
    """

    if title:
        st.subheader(title)

    df = get_data_from_google_sheet(sheet_name)

    if df.empty:
        st.info("Chưa có dữ liệu.")
        return

    if hide_cols:
        df_view = df.drop(
            columns=[c for c in hide_cols if c in df.columns],
            errors="ignore"
        )
    else:
        df_view = df.copy()

    if st.session_state.get("user_role") == "ADMIN":
        edited_df = st.data_editor(
            df_view,
            num_rows="dynamic",      # 🔥 BẮT BUỘC
            use_container_width=True,
            key=editor_key
        )

        if st.button("💾 Lưu dữ liệu", key=f"save_{editor_key}"):
            save_df_to_google_sheet(sheet_name, edited_df)
            st.success("Đã lưu về Google Sheet")
            st.rerun()

    else:
        st.dataframe(df_view, use_container_width=True)
