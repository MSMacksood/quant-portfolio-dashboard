import json
import os

import streamlit as st


def load_css():
    """Reads the CSS file safely and injects it into the Streamlit app."""
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>\n{f.read()}\n</style>", unsafe_allow_html=True)
    else:
        st.warning("style.css not found in the src/ directory.")


def format_regimes(text_str):
    if not isinstance(text_str, str): return text_str
    return text_str.replace("Regime 0", "Sideways Chop").replace("Regime 1", "Risk-On Bull").replace("Regime 2",
                                                                                                     "Risk-Off Shock")


def render_header():
    # Inject the CSS globally at the very top of the page
    load_css()

    st.markdown("""
    <div class="quant-banner">
        <h1 class="quant-title">
            <svg xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 14px;"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline></svg>
            AI Quant Portfolio Dashboard
        </h1>
        <p class="quant-subtitle">Live Agentic S&P 500 Sector Rotation Insights based on K-Means Macro Clustering</p>
    </div>
    """, unsafe_allow_html=True)


def render_status_badges(server_utc, market_cutoff, thesis_date):
    st.markdown(f"""
    <div class="status-container">
        <div class="status-card">
            <span class="status-icon">🕒</span>
            <span class="status-label">Server</span>
            <span class="status-value">{server_utc}</span>
        </div>
        <div class="status-card">
            <span class="status-icon">📊</span>
            <span class="status-label">Market Data</span>
            <span class="status-value">{market_cutoff}</span>
        </div>
        <div class="status-card">
            <span class="status-icon">🧠</span>
            <span class="status-label">AI Sync</span>
            <span class="status-value">{thesis_date}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_market_summary(latest, regime_labels):
    st.markdown("### 📊 Daily Market Summary")
    m1, m2, m3, m4 = st.columns(4)

    current_regime = int(latest['Regime'])

    regime_html = '<div><div class="regime-label">Current Market Regime</div>'
    for r_idx, r_name in regime_labels.items():
        if r_idx == current_regime:
            regime_html += f'<div class="regime-item active r-{r_idx}">{r_name}</div>'
        else:
            regime_html += f'<div class="regime-item inactive">{r_name}</div>'
    regime_html += "</div>"
    m1.markdown(regime_html, unsafe_allow_html=True)

    ret_val = latest['SPY_Daily_Return'] * 100
    ret_color = "#2ecc71" if ret_val >= 0 else "#e74c3c"
    ret_icon = "📈" if ret_val >= 0 else "📉"
    ret_sign = "+" if ret_val > 0 else ""

    with m2:
        st.markdown(
            f'<div><div class="metric-card"><div class="metric-label">S&P 500 Daily Return</div><div class="metric-value" style="color: {ret_color};">{ret_icon} {ret_sign}{ret_val:.2f}%</div><div class="metric-sub">Trailing 24h Performance</div></div></div>',
            unsafe_allow_html=True)
    with m3:
        st.markdown(
            f'<div><div class="metric-card"><div class="metric-label">20-Day Volatility</div><div class="metric-value" style="color: var(--text-color);">🌊 {latest["SPY_Volatility_20d"]:.4f}</div><div class="metric-sub">Rolling Annualized Volatility</div></div></div>',
            unsafe_allow_html=True)
    with m4:
        st.markdown(
            f'<div><div class="metric-card"><div class="metric-label">Macro CPI Level</div><div class="metric-value" style="color: var(--text-color);">🛒 {latest["CPI"]:.2f}</div><div class="metric-sub">US Consumer Price Index</div></div></div>',
            unsafe_allow_html=True)

    st.markdown("---")


def render_agentic_engine(df_thesis):
    st.markdown("### 🤖 Agentic Decision Engine")

    try:
        raw_text = None
        for i in range(len(df_thesis) - 1, -1, -1):
            text_candidate = str(df_thesis.iloc[i]['Thesis']).strip()
            if text_candidate.startswith("{") or text_candidate.startswith("```json"):
                raw_text = text_candidate
                break
        if not raw_text: raise ValueError("No JSON thesis found.")

        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        ai_data = json.loads(clean_text)

        sector_signals = ai_data.get("sector_signals", [])
        risk_protocol = ai_data.get("risk_protocol", [])
        macro_text = format_regimes(ai_data.get('macro_thesis', ''))

        st.markdown(
            f'<div><div class="macro-box"><div class="macro-header">🌍 Strategic Macro Outlook</div><div class="macro-content">{macro_text}</div></div></div>',
            unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Waiting for valid JSON thesis... \n\nError: {e}")
        sector_signals, risk_protocol = [], []

    signal_col, risk_col = st.columns([2, 1])

    with signal_col:
        st.markdown("#### Sector Rotation Protocol")
        sector_icons = {"XLK": "💻", "XLY": "🛍️", "XLF": "🏦", "XLV": "⚕️", "XLU": "⚡"}
        sector_html = "<div>"
        for s in sector_signals:
            ticker = s.get("ticker", "")
            signal = s.get("signal", "HOLD").upper()
            icon = s.get("icon", "") if s.get("icon", "") not in ["?", "??", ""] else sector_icons.get(ticker, "📊")
            badge_class = "badge-buy" if signal == "BUY" else "badge-sell" if signal == "SELL" else "badge-hold"
            sector_html += f'<div class="modern-card"><div class="card-header"><div class="card-title">{icon} {ticker} <span class="sub-text">{s.get("name", "")}</span></div><div class="badge {badge_class}">{signal}</div></div><div class="card-body">{format_regimes(s.get("rationale", ""))}</div></div>'
        sector_html += "</div>"
        st.markdown(sector_html, unsafe_allow_html=True)

    with risk_col:
        st.markdown("#### Risk Management Protocol")
        risk_icons = {"Max Sector Allocation": "🥧", "Strategy Stance": "🔄", "Cash Position": "💵", "Total Equity": "📊"}
        risk_html = "<div>"
        for r in risk_protocol:
            factor = r.get("factor", "")
            icon = r.get("icon", "") if r.get("icon", "") not in ["?", "??", ""] else risk_icons.get(factor, "🛡️")
            risk_html += f'<div class="modern-card"><div class="card-header"><div class="card-title">{icon} {factor}</div><div class="badge badge-risk">{r.get("signal", "")}</div></div><div class="card-body">{format_regimes(r.get("rationale", ""))}</div></div>'
        risk_html += "</div>"
        st.markdown(risk_html, unsafe_allow_html=True)


def render_footer():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("---")
    col_logo, col_tech = st.columns([1, 2.5])

    with col_logo:
        # Wrapped tightly in a root div to protect the image tag from the markdown parser
        st.markdown(
            '<div><div style="display: flex; height: 100%; align-items: center; justify-content: flex-start; padding-top: 15px;"><img src="https://upload.wikimedia.org/wikipedia/de/5/59/Logo_CoventryUniversity_.svg" width="320" style="opacity: 0.5;"></div></div>',
            unsafe_allow_html=True)

    with col_tech:
        st.markdown(
            "<div style='text-align: left; opacity: 0.4; font-size: 0.9em; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 25px;'>DEVELOPED USING...</div>",
            unsafe_allow_html=True)

        # Flatted to a single line inside a strict <div> container
        def tech_badge(name, url, icon_url):
            return f'<div><a href="{url}" target="_blank" style="display: flex; align-items: center; gap: 12px; text-decoration: none; color: inherit; margin-bottom: 12px; transition: opacity 0.2s;" onmouseover="this.style.opacity=\'0.8\'" onmouseout="this.style.opacity=\'0.5\'"><img src="{icon_url}" width="28" height="28" style="opacity: 0.5; object-fit: contain;"><span style="font-size: 0.95em; font-weight: 500; opacity: 0.4;">{name}</span></a></div>'

        f1, f2, f3, f4 = st.columns(4)
        header_style = "font-weight: 600; font-size: 1.05em; opacity: 0.4; margin-bottom: 15px;"

        with f1:
            st.markdown(f"<p style='{header_style}'>Frontend & Core</p>", unsafe_allow_html=True)
            st.markdown(tech_badge("Python 3.11", "https://www.python.org/",
                                   "https://icon.icepanel.io/Technology/svg/Python.svg"), unsafe_allow_html=True)
            st.markdown(tech_badge("Streamlit", "https://streamlit.io/",
                                   "https://icon.icepanel.io/Technology/svg/Streamlit.svg"), unsafe_allow_html=True)
            st.markdown(
                tech_badge("Plotly", "https://plotly.com/python/", "https://icon.icepanel.io/Technology/svg/Ploty.svg"),
                unsafe_allow_html=True)

        with f2:
            st.markdown(f"<p style='{header_style}'>AI & Analytics</p>", unsafe_allow_html=True)
            st.markdown(tech_badge("Google Gemini", "https://deepmind.google/technologies/gemini/",
                                   "https://upload.wikimedia.org/wikipedia/commons/1/1d/Google_Gemini_icon_2025.svg"),
                        unsafe_allow_html=True)
            st.markdown(tech_badge("Scikit-Learn", "https://scikit-learn.org/",
                                   "https://scikit-learn.org/stable/_static/scikit-learn-logo-without-subtitle.svg"),
                        unsafe_allow_html=True)
            st.markdown(tech_badge("Pandas", "https://pandas.pydata.org/",
                                   "https://icon.icepanel.io/Technology/svg/Pandas.svg"), unsafe_allow_html=True)

        with f3:
            st.markdown(f"<p style='{header_style}'>Cloud Infrastructure</p>", unsafe_allow_html=True)
            st.markdown(tech_badge("Azure App Service", "https://azure.microsoft.com/en-us/products/app-service",
                                   "https://symbols.getvecta.com/stencil_28/5_app-service-web-app.dbdab14e4a.svg"),
                        unsafe_allow_html=True)
            st.markdown(
                tech_badge("Azure SQL Database", "https://azure.microsoft.com/en-us/products/azure-sql/database",
                           "https://upload.wikimedia.org/wikipedia/commons/0/03/Azure_SQL_cloud_icon.svg"),
                unsafe_allow_html=True)
            st.markdown(tech_badge("GitHub Actions", "https://github.com/features/actions",
                                   "https://icon.icepanel.io/Technology/svg/GitHub-Actions.svg"),
                        unsafe_allow_html=True)

        with f4:
            st.markdown(f"<p style='{header_style}'>Data Pipelines & APIs</p>", unsafe_allow_html=True)
            st.markdown(tech_badge("Yahoo Finance", "https://finance.yahoo.com/",
                                   "https://companieslogo.com/img/orig/yahoo-finance-e577cb16.png?t=1720244494"),
                        unsafe_allow_html=True)
            st.markdown(tech_badge("FRED API", "https://fred.stlouisfed.org/docs/api/fred/",
                                   "https://img.icons8.com/color/48/000000/line-chart.png"), unsafe_allow_html=True)

        st.markdown("""
            <div style='text-align: center; margin-top: 50px;'>
                <p style='opacity: 0.5; font-size: 0.8em; margin-bottom: 8px;'>Developed by MSM Macksood | MSc in Data Science | Coventry University</p>
                <a href="https://github.com/MSMacksood/quant-portfolio-dashboard" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none; color: inherit; opacity: 0.5; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='0.5'">
                    <img src="https://cdn.simpleicons.org/github/gray" width="18" height="18" alt="GitHub">
                    <span style="font-size: 0.85em; font-weight: 500;">View Source Code on GitHub</span>
                </a>
            </div>
        """, unsafe_allow_html=True)
