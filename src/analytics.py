import pandas as pd

def calculate_technical_indicators(df):
    """Calculates SMA, MACD, and RSI using SPY as the proxy."""
    df_tech = df[['Date', 'Close_SPY']].copy()
    df_tech.set_index('Date', inplace=True)

    # Moving Averages
    df_tech['SMA_50'] = df_tech['Close_SPY'].rolling(window=50).mean()
    df_tech['SMA_200'] = df_tech['Close_SPY'].rolling(window=200).mean()

    # MACD
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
    return df_tech