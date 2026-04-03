import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build_peer_analysis_chart(df_plot, selected_clean):
    """Builds the normalized multi-ticker line chart."""
    fig = px.line(df_plot, x="Date", y=selected_clean)
    fig.update_layout(
        height=450, margin=dict(l=0, r=0, t=10, b=0),
        legend_title_text='Ticker', xaxis_title="",
        yaxis_title="Normalized Price", hovermode="x unified"
    )
    return fig


def build_technical_chart(df_plot_tech, theme_base):
    """Builds the 3-row stacked technical indicators chart."""
    fig_tech = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.5, 0.25, 0.25])
    theme_color = 'white' if theme_base == "dark" else 'black'

    # Top Chart: Price & MAs
    fig_tech.add_trace(go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['Close_SPY'], name='SPY Close',
                                  line=dict(color=theme_color, width=1.5)), row=1, col=1)
    fig_tech.add_trace(go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['SMA_50'], name='50-Day SMA',
                                  line=dict(color='#3498db', dash='dash')), row=1, col=1)
    fig_tech.add_trace(go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['SMA_200'], name='200-Day SMA',
                                  line=dict(color='#e74c3c', dash='dash')), row=1, col=1)

    # Middle Chart: MACD
    fig_tech.add_trace(
        go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['MACD'], name='MACD', line=dict(color='#9b59b6')), row=2,
        col=1)
    fig_tech.add_trace(
        go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['Signal'], name='Signal Line', line=dict(color='#f39c12')),
        row=2, col=1)
    fig_tech.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)

    # Bottom Chart: RSI
    fig_tech.add_trace(
        go.Scatter(x=df_plot_tech['Date'], y=df_plot_tech['RSI'], name='RSI (14)', line=dict(color='#2ecc71')), row=3,
        col=1)
    fig_tech.add_hline(y=70, line_dash="dash", line_color="#e74c3c", row=3, col=1, annotation_text="Over Bought (70)",
                       annotation_position="top left")
    fig_tech.add_hline(y=30, line_dash="dash", line_color="#3498db", row=3, col=1, annotation_text="Over Sold (30)",
                       annotation_position="bottom left")

    fig_tech.update_layout(height=650, margin=dict(l=0, r=75, t=10, b=0), hovermode="x unified", showlegend=True)
    fig_tech.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig_tech.update_yaxes(title_text="MACD", row=2, col=1)
    fig_tech.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)

    return fig_tech
