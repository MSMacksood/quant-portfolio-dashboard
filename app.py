import streamlit as st
import pandas as pd
from src import data_handler, analytics, charts, components

# --- 1. PAGE CONFIG & HEADER ---
st.set_page_config(page_title="S&P 500 AI Rotation", page_icon="🤖", layout="wide")
components.render_header()

try:
    # --- 2. DATA LOADING & PREP ---
    with st.status("Initializing AI Quant Engine...", expanded=True) as status:
        st.write("🔐 Authenticating and Loading Data...")
        df_raw, df_thesis = data_handler.load_data()

        st.write("📊 Processing Market Data & Technicals...")
        df = data_handler.sanitize_data(df_raw)

        st.write("🧠 Syncing Agentic Sector Signals...")
        status.update(label="System Online. Dashboard Ready.", state="complete", expanded=False, )

    # DYNAMIC TIMESTAMPS
    now_est = pd.Timestamp.now('US/Eastern').strftime('%B %d, %Y | %I:%M %p EST')
    market_cutoff = df['Date'].iloc[-1].strftime('%B %d, %Y')
    try:
        thesis_date = pd.to_datetime(df_thesis.iloc[-1]['Date']).strftime('%B %d, %Y')
    except:
        thesis_date = market_cutoff
    components.render_status_badges(now_est, market_cutoff, thesis_date)

    # REGIME SETUP
    df['Regime'] = df['Regime'].astype(int)
    regime_labels = {0: "Sideways Chop ⚖️", 1: "Risk-On Bull 🐂", 2: "Risk-Off Shock 🐻"}
    df['Regime_Name'] = df['Regime'].map(regime_labels)

    # --- 3. DAILY MARKET SUMMARY ---
    components.render_market_summary(df.iloc[-1], regime_labels)

    # --- 4. STOCK PEER ANALYSIS ---
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

        fig_peer = charts.build_peer_analysis_chart(df_plot, selected_clean)
        st.plotly_chart(fig_peer, width='stretch')

    st.markdown("---")

    # --- 5. TECHNICAL INDICATORS ---
    with st.expander("🔍 View Technical Health Indicators (SPY Proxy)", expanded=False):
        df_tech = analytics.calculate_technical_indicators(df)
        fig_tech = charts.build_technical_chart(df_tech.tail(500), st.get_option("theme.base"))
        st.plotly_chart(fig_tech, width="stretch")
        st.markdown("---")

    # --- 6. AGENTIC DECISION ENGINE ---
    components.render_agentic_engine(df_thesis)

except Exception as e:
    st.error(f"Failed to load data or render UI. Error: {e}")

# --- 7. FOOTER ---
components.render_footer()