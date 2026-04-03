import struct
import time

import pandas as pd
import pyodbc
import streamlit as st
from azure.identity import DefaultAzureCredential
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Import the mock generator from your new module
from src.mock_data import generate_mock_data

# --- TOGGLE FOR LOCAL UI TESTING ---
# Set to True to test UI without hitting Azure SQL
USE_MOCK_DATA = False


@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 Hour
def load_data():
    if USE_MOCK_DATA:
        return generate_mock_data()

    server = 'quant-server-123.database.windows.net'
    database = 'trading-db'
    driver = '{ODBC Driver 17 for SQL Server}'

    credential = DefaultAzureCredential()
    token_object = credential.get_token("https://database.windows.net/.default")
    token_as_bytes = bytes(token_object.token, "UTF-8")
    encoded_token = token_as_bytes.decode("UTF-8").encode("UTF-16-LE")
    token_struct = struct.pack(f"<I{len(encoded_token)}s", len(encoded_token), encoded_token)

    conn_str = f"DRIVER={driver};SERVER=tcp:{server},1433;DATABASE={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    SQL_COPT_SS_ACCESS_TOKEN = 1256

    def get_conn():
        return pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})

    engine = create_engine("mssql+pyodbc://", creator=get_conn)
    max_retries = 3
    retry_delay = 15

    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                df = pd.read_sql(text("SELECT * FROM ProcessedMarketData ORDER BY Date ASC"), conn)
                try:
                    df_thesis = pd.read_sql(text("SELECT * FROM AIThesis ORDER BY Date ASC"), conn)
                except:
                    df_thesis = pd.DataFrame({'Date': [pd.Timestamp.today()], 'Thesis': ["Thesis not found."]})
                return df, df_thesis
        except OperationalError as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise Exception(f"Database failed to respond. Error: {e}")


def sanitize_data(df):
    """Linux ODBC Data Type Sanitizer"""
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    if 'Ticker' in df.columns:
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
    for col in df.columns:
        if col not in ['Date', 'Ticker']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df
