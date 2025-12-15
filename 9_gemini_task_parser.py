import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime


# =========================================================
# ✅ HÀM TẠO CONTEXT TỪ TẤT CẢ SHEET
# =========================================================
def build_context_from_sheets(all_sheets):
    """
    Tạo context mô tả toàn bộ dữ liệu:
    - Nhân sự
    - Đơn vị
    - Dự án
    - Gói thầu
    - Hợp đồng
    - Văn bản
    """
    ctx = []

    # -----------------------------
    # ✅ Nhân sự
    # -----------------------------
    df = all_sheets["1_NHAN_SU"]
    if not df.empty:
        ctx.append("DANH SÁCH NHÂN SỰ:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_NHAN_SU']}: {r['HO_TEN']} ({r['CHUC_VU']})")

    # -----------------------------
    # ✅ Đơn vị
    # -----------------------------
    df = all_sheets["2_DON_VI"]
    if not df.empty:
        ctx.append("\nDANH SÁCH ĐƠN VỊ:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_DON_VI']}: {r['TEN_DON_VI']}")

    # -----------------------------
    # ✅ Dự án
    # -----------------------------
    df = all_sheets["4_DU_AN"]
    if not df.empty:
        ctx.append("\nDANH SÁCH DỰ ÁN:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_DU_AN']}: {r['TEN_DU_AN']}")

    # -----------------------------
    # ✅ Gói thầu
    # -----------------------------
    df = all_sheets["5_GOI_THAU"]
    if not df.empty:
        ctx.append("\nDANH SÁCH GÓI THẦU:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_GOI_THAU']}: {r['TEN_GOI_THAU']}")

    # -----------------------------
    # ✅ Hợp đồng
    # -----------------------------
    df = all_sheets["6_HOP_DONG"]
    if not df.empty:
        ctx.append("\nDANH SÁCH HỢP ĐỒNG:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_HOP_DONG']}: {r['TEN_HD']}")

    # -----------------------------
    # ✅ Văn bản
    # -----------------------------
    df = all_sheets["3_VAN_BAN"]
    if not df.empty:
        ctx.append("\nDANH SÁCH VĂN BẢN:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_VB']}: {r['SO_VAN_BAN']} - {r['TRICH_YEU']}")

    return "\n".join(ctx)


# =========================================================
# ✅ HÀM GỌI GEMINI ĐỂ PHÂN TÍCH CÂU CHAT → JSON CÔNG VIỆC
# =========================================================
def parse_task_from_chat(api_key, user_message, all_sheets):
    """
    Gửi câu chat + context vào Gemini → nhận JSON danh sách công việc.
    """
    genai.configure(api_key=api_key)

    context = build_context_from_sheets(all_sheets)

    prompt = f"""
Bạn là trợ lý quản lý công việc. Hãy phân tích câu mô tả sau thành danh sách công việc.

YÊU CẦU:
- Trả về JSON dạng list các object.
- Mỗi công việc gồm các trường:
  - TEN_VIEC
  - NOI_DUNG
  - NGUOI_GIAO (ID_NHAN_SU)
  - NGUOI_NHAN (ID_NHAN_SU)
  - NGAY_GIAO (dd/mm/yyyy)
  - HAN_CHOT (dd/mm/yyyy)
  - IDDV_CV (ID_DON_VI)
  - IDDA_CV (ID_DU_AN)
  - IDGT_CV (ID_GOI_THAU)
  - IDHD_CV (ID_HOP_DONG)
  - IDVB_VAN_BAN (ID_VB)
  - GHI_CHU_GEMINI

DỮ LIỆU THAM CHIẾU:
{context}

CÂU MÔ TẢ CỦA NGƯỜI DÙNG:
\"\"\"{user_message}\"\"\"

HÃY TRẢ VỀ JSON DUY NHẤT, KHÔNG GIẢI THÍCH.
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        text = response.text.strip()

        # Tìm JSON trong câu trả lời
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        tasks = pd.read_json(text)

        # Chuẩn hóa cột
        required_cols = [
            "TEN_VIEC", "NOI_DUNG",
            "NGUOI_GIAO", "NGUOI_NHAN",
            "NGAY_GIAO", "HAN_CHOT",
            "IDDV_CV", "IDDA_CV", "IDGT_CV", "IDHD_CV", "IDVB_VAN_BAN",
            "GHI_CHU_GEMINI"
        ]

        for col in required_cols:
            if col not in tasks.columns:
                tasks[col] = ""

        return tasks

    except Exception as e:
        st.error(f"❌ Lỗi phân tích công việc từ Gemini: {e}")
        return pd.DataFrame()
