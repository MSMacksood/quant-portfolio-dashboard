import numpy as np
import pandas as pd


def generate_mock_data():
    """Generates fake data for offline UI testing."""
    dates = pd.date_range(end=pd.Timestamp.today(), periods=1300)

    df = pd.DataFrame({'Date': dates})
    tickers = ['SPY', 'XLK', 'XLU', 'XLF', 'XLV', 'XLY']
    for t in tickers:
        df[f'Close_{t}'] = np.linspace(100, 200, 1300) + np.random.normal(0, 5, 1300).cumsum()

    df['Regime'] = np.random.choice([0, 1, 2], 1300)
    df['SPY_Daily_Return'] = np.random.normal(0.001, 0.01, 1300)
    df['SPY_Volatility_20d'] = np.random.uniform(-0.01, 0.03, 1300)
    df['CPI'] = np.linspace(310, 326, 1300)

    mock_thesis = """
    {
      "macro_thesis": "Regime 0 simulated data. Sideways Chop dynamics favor defensive posturing.",
      "sector_signals": [
        {"ticker": "XLU", "name": "Utilities", "signal": "SELL", "rationale": "Crashing."},
        {"ticker": "XLK", "name": "Technology", "signal": "HOLD", "rationale": "High valuations limit upside."},
        {"ticker": "XLV", "name": "Healthcare", "signal": "BUY", "rationale": "Strong safe haven."}
      ],
      "risk_protocol": [
        {"factor": "Cash Position", "signal": "15-20% TARGET", "rationale": "Maintain liquidity for mean-reversion."}
      ]
    }
    """
    df_thesis = pd.DataFrame({'Date': [dates[-1]], 'Thesis': [mock_thesis]})
    return df, df_thesis
