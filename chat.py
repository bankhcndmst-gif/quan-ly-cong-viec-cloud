import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from utils import remove_duplicate_and_empty_cols, parse_dates

def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(show_spinner=False, ttl=60)
def load_all_sheets() -> dict:
    all_data = {}
    conn = get_connection()
    for name in conn.list_worksheets():
        df = conn.read(worksheet=name, ttl=0)
        df = remove_duplicate_and_empty_cols(df)
        df = parse_dates(df)
        all_data[name] = df
    return all_data

def save_raw_sheet(sheet_name: str, df_new: pd.DataFrame):
    conn = get_connection()
    df_save = df_new.copy().fillna("")
    conn.update(worksheet=sheet_name, data=df_save)

def append_row(sheet_name: str, row: dict):
    conn = get_connection()
    df_new = pd.DataFrame([row])
    conn.append(worksheet=sheet_name, data=df_new)
