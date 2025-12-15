import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def get_data_from_google_sheet(sheet_name):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(worksheet=sheet_name, ttl=0)
    except Exception:
        return pd.DataFrame()

def save_df_to_google_sheet(sheet_name, df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet=sheet_name, data=df)
