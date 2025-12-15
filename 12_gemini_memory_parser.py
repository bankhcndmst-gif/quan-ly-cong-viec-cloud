import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime


# =========================================================
# ✅ TẠO CONTEXT TỪ DỮ LIỆU HỆ THỐNG
# =========================================================
def build_memory_context(all_sheets):
    """
    Tạo context để Gemini hiểu:
    - Nhân sự
    - Dự án
    - Hợp đồng
    - Gói thầu
    - Văn bản
    """
    ctx = []

    # Nhân sự
    df = all_sheets["1_NHAN_SU"]
    if not df.empty:
        ctx.append("DANH SÁCH NHÂN SỰ:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_NHAN_SU']}: {r['HO_TEN']} ({r['CHUC_VU']})")

    # Dự án
    df = all_sheets["4_DU_AN"]
    if not df.empty:
        ctx.append("\nDANH SÁCH DỰ ÁN:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_DU_AN']}: {r['TEN_DU_AN']}")

    # Hợp đồng
    df = all_sheets["6_HOP_DONG"]
    if not df.empty:
        ctx.append("\nDANH SÁCH HỢP ĐỒNG:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_HOP_DONG']}: {r['TEN_HD']}")

    # Gói thầu
    df = all_sheets["5_GOI_THAU"]
    if not df.empty:
        ctx.append("\nDANH SÁCH GÓI THẦU:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_GOI_THAU']}: {r['TEN_GOI_THAU']}")

    # Văn bản
    df = all_sheets["3_VAN_BAN"]
    if not df.empty:
        ctx.append("\nDANH SÁCH VĂN BẢN:")
        for _, r in df.iterrows():
            ctx.append(f"- {r['ID_VB']}: {r['SO_VAN_BAN']} - {r['TRICH_YEU']}")

    return "\n".join(ctx)


# =========================================================
# ✅ GỌI GEMINI ĐỂ PHÂN TÍCH TRÍ NHỚ AI
# =========================================================
def parse_memory_from_chat(api_key, user_message, all_sheets):
    """
    Phân tích câu chat thành trí nhớ AI:
    - NHAC_VIEC
    - HOP
    - VIEC_DA_LAM
    """
    genai.configure(api_key=api_key)

    context = build_memory_context(all_sheets)

    prompt = f"""
Bạn là trợ lý trí nhớ AI. Hãy phân tích câu mô tả sau thành TRÍ NHỚ AI.

CÁC LOẠI TRÍ NHỚ:
1. NHAC_VIEC
   - Lặp lại: none / daily / weekly / monthly
   - Chu kỳ: mô tả thêm (nếu có)
   - Thời gian: dd/mm/yyyy HH:MM hoặc dd/mm/yyyy

2. HOP
   - Tóm tắt nội dung họp
   - Nội dung đầy đủ

3. VIEC_DA_LAM
   - Mô tả việc đã hoàn thành
   - Thời gian hoàn thành

YÊU CẦU TRẢ VỀ JSON DẠNG LIST:
[
  {{
    "LOAI": "",
    "THOI_GIAN": "",
    "NOI_DUNG": "",
    "LAP_LAI": "",
    "CHU_KY": "",
    "NGAY_TAO": "",
    "LIEN_QUAN": "",
    "TOM_TAT": "",
    "NOI_DUNG_DAY_DU": "",
    "TRANG_THAI": ""
  }}
]

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

        # Loại bỏ markdown nếu có
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        df = pd.read_json(text)

        # -----------------------------------------------------
        # ✅ Chuẩn hóa cột
        # -----------------------------------------------------
        required_cols = [
            "LOAI", "THOI_GIAN", "NOI_DUNG",
            "LAP_LAI", "CHU_KY",
            "NGAY_TAO", "LIEN_QUAN",
            "TOM_TAT", "NOI_DUNG_DAY_DU",
            "TRANG_THAI"
        ]

        for col in required_cols:
            if col not in df.columns:
                df[col] = ""

        # Tự động thêm ngày tạo
        df["NGAY_TAO"] = datetime.now().strftime("%d/%m/%Y")

        return df

    except Exception as e:
        st.error(f"❌ Lỗi phân tích trí nhớ AI từ Gemini: {e}")
        return pd.DataFrame()
