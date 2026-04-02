import streamlit as st
import pandas as pd
import struct
import pyodbc
from sqlalchemy import create_engine, text
from azure.identity import DefaultAzureCredential
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
from sqlalchemy.exc import OperationalError

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Sector Rotation", page_icon="🤖", layout="wide")
st.title("🤖 AI Quant Portfolio Dashboard")
st.markdown("Live Agentic Sector Rotation based on K-Means Macro Clustering")


# --- SECURE SQL CONNECTION ---
@st.cache_data(ttl=3600)  # Caches data for 1 hour
def load_data():
    server = 'quant-server-123.database.windows.net'  # UPDATE THIS
    database = 'trading-db'  # UPDATE THIS
    driver = '{ODBC Driver 17 for SQL Server}'

    # 1. Grab the token securely
    credential = DefaultAzureCredential()
    token_object = credential.get_token("https://database.windows.net/.default")
    token_as_bytes = bytes(token_object.token, "UTF-8")
    encoded_token = token_as_bytes.decode("UTF-8").encode("UTF-16-LE")
    token_struct = struct.pack(f"<I{len(encoded_token)}s", len(encoded_token), encoded_token)

    # 2. Add 'Connection Timeout=30;' to give the initial knock a bit more time
    conn_str = f"DRIVER={driver};SERVER=tcp:{server},1433;DATABASE={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    SQL_COPT_SS_ACCESS_TOKEN = 1256

    def get_conn():
        return pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})

    engine = create_engine("mssql+pyodbc://", creator=get_conn)

    # 3. ROBUST RETRY LOGIC FOR COLD STARTS
    max_retries = 3
    retry_delay = 15  # seconds to wait while the database wakes up

    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                # If we get inside this block, the database is awake!
                df = pd.read_sql(text("SELECT * FROM ProcessedMarketData ORDER BY Date ASC"), conn)

                try:
                    df_thesis = pd.read_sql(text("SELECT * FROM AIThesis ORDER BY Date ASC"), conn)
                except:
                    # Fallback if the table doesn't exist yet
                    df_thesis = pd.DataFrame({'Date': [pd.Timestamp.today()], 'Thesis': ["Thesis not found."]})

                return df, df_thesis

        except OperationalError as e:
            # Catch the timeout error specifically
            if attempt < max_retries - 1:
                print(
                    f"Database sleeping or unavailable. Retrying in {retry_delay} seconds... (Attempt {attempt + 1} of {max_retries})")
                time.sleep(retry_delay)
            else:
                # If we fail 3 times, it's a real error (like a bad IP or password), so we let it crash and show the user
                raise Exception(f"Database failed to respond after {max_retries} attempts. Original Error: {e}")

# --- BUILD THE UI ---
try:
    with st.spinner('Connecting to Azure SQL Data Warehouse...'):
        # Load data from Azure SQL
        df, df_thesis = load_data()

        # ==========================================
        # 🚨 START LINUX ODBC SANITIZER 🚨
        # Force Linux to parse data types exactly like Windows

        # 1. Force Dates to be actual Datetime objects
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])

        # 2. Strip hidden spaces from Tickers (fixes selection box issues)
        if 'Ticker' in df.columns:
            df['Ticker'] = df['Ticker'].astype(str).str.strip()

        # 3. Force all price/metric columns to be Floats, not strings
        for col in df.columns:
            if col not in ['Date', 'Ticker']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 🚨 END LINUX ODBC SANITIZER 🚨
        # ==========================================

    df['Regime'] = df['Regime'].astype(int)
    regime_labels = {
        0: "Sideways Chop ⚖️",
        1: "Risk-On Bull 🐂",
        2: "Risk-Off Shock 🐻"
    }
    df['Regime_Name'] = df['Regime'].map(regime_labels)
    latest = df.iloc[-1]

    # Grab the latest thesis text
    latest_thesis_text = df_thesis.iloc[-1]['Thesis']

    # --- PARSE THE THESIS ---
    # We slice the text using the section headers Gemini generates
    try:
        # Remove markdown asterisks just in case for cleaner splitting
        clean_text = latest_thesis_text.replace("**", "")
        sector_signals = clean_text.split("2. Decision Engine: Sector Signals")[1].split("3. Risk Management Protocol")[
            0].strip()
        risk_protocol = clean_text.split("3. Risk Management Protocol")[1].strip()
    except:
        sector_signals = "AI Sector Signals currently unavailable. Run the Agentic pipeline."
        risk_protocol = "AI Risk Protocol currently unavailable."

    # --- 1. HIGHLIGHTED TOP METRICS ---
    st.markdown("### 📊 Daily Market Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Market Regime", regime_labels[latest['Regime']])
    m2.metric("S&P 500 Daily Return", f"{round(latest['SPY_Daily_Return'] * 100, 2)}%")
    m3.metric("20-Day Volatility", round(latest['SPY_Volatility_20d'], 4))
    m4.metric("Macro CPI Level", round(latest['CPI'], 2))
    st.markdown("---")

    # --- 2. THE SPLIT DASHBOARD (Controls Left, Chart Right) ---
    st.markdown("### 📈 Stock Peer Analysis")
    control_col, chart_col = st.columns([1, 3])

    with control_col:
        st.markdown("#### Controls")
        sectors = [col for col in df.columns if col.startswith('Close_')]
        clean_sectors = [s.replace('Close_', '') for s in sectors]
        selected_clean = st.multiselect("Stock tickers", clean_sectors, default=['SPY', 'XLK', 'XLU'])

        st.write("")
        horizon = st.radio("Time horizon", ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years", "All Time"],
                           horizontal=False)

    with chart_col:
        horizon_map = {"1 Month": 21, "3 Months": 63, "6 Months": 126, "1 Year": 252, "5 Years": 1260,
                       "All Time": len(df)}
        df_filtered = df.tail(horizon_map[horizon]).copy()
        plot_cols = [f"Close_{s}" for s in selected_clean]

        df_plot = df_filtered[['Date'] + plot_cols].copy()
        for col in plot_cols:
            df_plot[col] = df_plot[col] / df_plot[col].iloc[0]

        df_plot.columns = ['Date'] + selected_clean
        fig2 = px.line(df_plot, x="Date", y=selected_clean)
        fig2.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0), legend_title_text='Ticker', xaxis_title="",
                           yaxis_title="Normalized Price", hovermode="x unified")
        st.plotly_chart(fig2)

    st.markdown("---")

    # --- 2.5 TECHNICAL HEALTH INDICATORS (EXPANDER) ---
    with st.expander("🔍 View Technical Health Indicators (SPY Proxy)", expanded=False):

        # 1. On-the-fly Quantitative Math
        df_tech = df[['Date', 'Close_SPY']].copy()
        df_tech.set_index('Date', inplace=True)

        # Moving Averages
        df_tech['SMA_50'] = df_tech['Close_SPY'].rolling(window=50).mean()
        df_tech['SMA_200'] = df_tech['Close_SPY'].rolling(window=200).mean()

        # MACD (12-day EMA - 26-day EMA)
        ema12 = df_tech['Close_SPY'].ewm(span=12, adjust=False).mean()
        ema26 = df_tech['Close_SPY'].ewm(span=26, adjust=False).mean()
        df_tech['MACD'] = ema12 - ema26
        df_tech['Signal'] = df_tech['MACD'].ewm(span=9, adjust=False).mean()

        # RSI (14-Day Wilder's Smoothing)
        delta = df_tech['Close_SPY'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
        rs = avg_gain / avg_loss
        df_tech['RSI'] = 100 - (100 / (1 + rs))

        df_tech.reset_index(inplace=True)

        # Filter for recent history to keep charts readable (last 2 years ~ 500 days)
        df_plot_tech = df_tech.tail(500)

        # 2. Build the Stacked Plotly Figure
        fig_tech = make_subplots(rows=3, cols=1, shared_xaxes=True,
                                 vertical_spacing=0.04,
                                 row_heights=[0.5, 0.25, 0.25])

        # Top Chart: Price & MAs
        fig_tech.add_trace(go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['Close_SPY'], name='SPY Close',
                                      line=dict(color='white' if st.get_option("theme.base") == "dark" else 'black',
                                                width=1.5)), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['SMA_50'], name='50-Day SMA',
                                      line=dict(color='#3498db', dash='dash')), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['SMA_200'], name='200-Day SMA',
                                      line=dict(color='#e74c3c', dash='dash')), row=1, col=1)

        # Middle Chart: MACD
        fig_tech.add_trace(
            go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['MACD'], name='MACD', line=dict(color='#9b59b6')), row=2,
            col=1)
        fig_tech.add_trace(go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['Signal'], name='Signal Line',
                                      line=dict(color='#f39c12')), row=2, col=1)
        fig_tech.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)

        # Bottom Chart: RSI
        fig_tech.add_trace(
            go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['RSI'], name='RSI (14)', line=dict(color='#2ecc71')),
            row=3, col=1)
        fig_tech.add_hline(y=70, line_dash="dash", line_color="#e74c3c", row=3, col=1, annotation_text="Overbought (70)", annotation_position="top left")
        fig_tech.add_hline(y=30, line_dash="dash", line_color="#3498db", row=3, col=1, annotation_text="Oversold (30)", annotation_position="bottom left")

        # Clean Layout
        fig_tech.update_layout(height=650, margin=dict(l=0, r=0, t=10, b=0),
                               hovermode="x unified", showlegend=True
                               )
        fig_tech.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig_tech.update_yaxes(title_text="MACD", row=2, col=1)
        fig_tech.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)

        st.plotly_chart(fig_tech, use_container_width=True)
        st.markdown("---")

    # --- 3. AI PORTFOLIO MANAGER SIGNALS ---
    st.markdown("### 🤖 Agentic Decision Engine")

    # UPGRADED CSS: Modern FinTech aesthetic with flexbox, hover states, and pill badges
    st.markdown("""
    <style>
    .macro-box {
        background-color: var(--secondary-background-color);
        border-left: 6px solid #636efa; /* Sleek quant indigo/blue accent */
        border-radius: 10px;
        padding: 24px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .macro-header {
        font-size: 1.25em;
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .macro-content {
        font-size: 1.05em;
        line-height: 1.6;
        opacity: 0.9;
    }
    .modern-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .modern-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        border-color: rgba(128, 128, 128, 0.4);
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .card-title {
        font-weight: 600;
        font-size: 1.15em;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sub-text {
        opacity: 0.6;
        font-size: 0.85em;
        font-weight: 400;
        margin-left: 6px;
    }
    .badge {
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 700;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Dynamic Badge Colors */
    .badge-buy { background-color: rgba(39, 174, 96, 0.15); color: #2ecc71; border: 1px solid rgba(46, 204, 113, 0.5); }
    .badge-hold { background-color: rgba(243, 156, 18, 0.15); color: #f1c40f; border: 1px solid rgba(241, 196, 15, 0.5); }
    .badge-sell { background-color: rgba(231, 76, 60, 0.15); color: #e74c3c; border: 1px solid rgba(231, 76, 60, 0.5); }
    .badge-risk { background-color: rgba(52, 152, 219, 0.15); color: #3498db; border: 1px solid rgba(52, 152, 219, 0.5); }

    .card-body {
        font-size: 0.95em;
        opacity: 0.85;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)

    # Safely load the JSON from the database
    try:
        raw_text = None
        for i in range(len(df_thesis) - 1, -1, -1):
            text_candidate = str(df_thesis.iloc[i]['Thesis']).strip()
            if text_candidate.startswith("{") or text_candidate.startswith("```json"):
                raw_text = text_candidate
                break

        if not raw_text:
            raise ValueError("No JSON thesis found.")

        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        ai_data = json.loads(clean_text)

        sector_signals = ai_data.get("sector_signals", [])
        risk_protocol = ai_data.get("risk_protocol", [])

        # Upgraded Executive Summary Panel
        macro_text = ai_data.get('macro_thesis', '')
        st.markdown(f'''
                <div class="macro-box">
                    <div class="macro-header">🌍 Strategic Macro Outlook</div>
                    <div class="macro-content">{macro_text}</div>
                </div>
                ''', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Waiting for valid JSON thesis... \n\nError: {e}")
        sector_signals, risk_protocol = [], []

    # Render the columns
    signal_col, risk_col = st.columns([2, 1])

    with signal_col:
        st.markdown("#### Sector Rotation Protocol")

        sector_icons = {"XLK": "💻", "XLY": "🛍️", "XLF": "🏦", "XLV": "⚕️", "XLU": "⚡"}
        sector_html = ""

        for s in sector_signals:
            ticker = s.get("ticker", "")
            name = s.get("name", "")
            signal = s.get("signal", "HOLD").upper()
            rationale = s.get("rationale", "")

            # Catch LLM hallucinated emojis
            icon = s.get("icon", "")
            if icon in ["?", "??", ""] or not icon:
                icon = sector_icons.get(ticker, "📊")

            badge_class = "badge-buy" if signal == "BUY" else "badge-sell" if signal == "SELL" else "badge-hold"

            # Build the Modern Flexbox Card
            sector_html += f'''
            <div class="modern-card">
                <div class="card-header">
                    <div class="card-title">{icon} {ticker} <span class="sub-text">{name}</span></div>
                    <div class="badge {badge_class}">{signal}</div>
                </div>
                <div class="card-body">{rationale}</div>
            </div>
            '''

        st.markdown(sector_html, unsafe_allow_html=True)

    with risk_col:
        st.markdown("#### Risk Management Protocol")

        risk_icons = {"Max Sector Allocation": "🥧", "Strategy Stance": "🔄", "Cash Position": "💵", "Total Equity": "📊"}
        risk_html = ""

        for r in risk_protocol:
            factor = r.get("factor", "")
            signal = r.get("signal", "")
            rationale = r.get("rationale", "")

            # Upgraded catch for "??"
            icon = r.get("icon", "")
            if icon in ["?", "??", ""] or not icon:
                icon = risk_icons.get(factor, "🛡️")

            risk_html += f'''
            <div class="modern-card">
                <div class="card-header">
                    <div class="card-title">{icon} {factor}</div>
                    <div class="badge badge-risk">{signal}</div>
                </div>
                <div class="card-body">{rationale}</div>
            </div>
            '''

        st.markdown(risk_html, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Failed to load data. Ensure your IP is whitelisted. Error: {e}")