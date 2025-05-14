import yfinance as yf
import pandas as pd
import numpy as np
from ta import add_all_ta_features
from ta.utils import dropna
from scipy.signal import find_peaks
import re
from pandas.tseries.frequencies import to_offset
from groq import Groq
import json

# Set your Groq API key


def yf_tech_analysis_with_llm(ticker: str, ask_period: str = "30d"):
    fetch_period = "1y"
    stock = yf.Ticker(ticker)

    try:
        history = stock.history(period=fetch_period, auto_adjust=True)
    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}

    if history.empty:
        return {"error": f"No historical data found for {ticker} with period {fetch_period}"}

    # Determine frequency
    num_days = int(re.findall(r'\d+', ask_period)[0])
    frequency = "weekly" if num_days > 10 else "daily"

    if frequency == "weekly":
        history = history.resample("W").agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        }).dropna()
    history.fillna(method='ffill', inplace=True)
    # Add technical indicators
    df = add_all_ta_features(
        history, open="Open", high="High", low="Low", close="Close", volume="Volume"
    )
    # print(df.columns)
    # Add custom indicators
    df['volatility'] = df['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
    df['momentum'] = df['Close'] - df['Close'].shift(20)

    if df.empty:
        return {"error": "Insufficient data after feature engineering."}

    # Filter by ask_period
    ask_offset = to_offset(ask_period)
    end_date = df.index[-1]
    start_date = end_date - ask_offset.delta
    df = df[df.index >= start_date]

    if df.empty:
        return {"error": f"No data in the specified ask_period {ask_period}"}

    # Peak/trough detection
    close_prices = df['Close'].values
    peaks, _ = find_peaks(close_prices, distance=2)
    troughs, _ = find_peaks(-close_prices, distance=2)
    support_levels = close_prices[troughs][-3:].tolist() if len(troughs) >= 3 else close_prices[troughs].tolist()
    resistance_levels = close_prices[peaks][-3:].tolist() if len(peaks) >= 3 else close_prices[peaks].tolist()

    # Select last 5 entries
    output_df = df.tail(5)

    # Prepare data to send to LLM
    indicator_data = {
    "ticker": ticker,
    "data_frequency": frequency,
    "dates": output_df.index.strftime("%Y-%m-%d").tolist(),
    "close_price": output_df['Close'].tolist(),
    "volume_obv": output_df['volume_obv'].tolist(),
    "volume_cmf": output_df['volume_cmf'].tolist(),
    "volume_mfi": output_df['volume_mfi'].tolist(),
    "volatility_atr": output_df['volatility_atr'].tolist(),
    "macd_histogram": output_df['trend_macd_diff'].tolist(),
    "ema_fast": output_df['trend_ema_fast'].tolist(),
    "ema_slow": output_df['trend_ema_slow'].tolist(),
    "adx": output_df['trend_adx'].tolist(),
    "aroon_up": output_df['trend_aroon_up'].tolist(),
    "aroon_down": output_df['trend_aroon_down'].tolist(),
    "rsi": output_df['momentum_rsi'].tolist(),
    "ao": output_df['momentum_ao'].tolist(),
    "williams_r": output_df['momentum_wr'].tolist(),
    "roc": output_df['momentum_roc'].tolist(),
    "stochastic": output_df['momentum_stoch'].tolist(),
    "stochastic_signal": output_df['momentum_stoch_signal'].tolist(),
    "custom_volatility": output_df['volatility'].tolist(),
    "custom_momentum": output_df['momentum'].tolist(),
    "support_levels": support_levels,
    "resistance_levels": resistance_levels,
    }

    # Prompt for LLM
    prompt = f"""
You are an expert financial analyst with deep expertise in technical analysis and market behavior. I need you to provide a comprehensive, professional analysis of {ticker} based on the technical indicators provided below (sampled at {frequency} frequency).

Please structure your analysis as follows:

1. **PRICE ACTION SUMMARY**: Analyze the recent price movements, key levels, and overall trend direction.

2. **VOLUME ANALYSIS**: Interpret the On-Balance Volume (OBV), Chaikin Money Flow (CMF), and Money Flow Index (MFI) to determine buying/selling pressure and potential divergences.

3. **TREND INDICATORS**: Evaluate the EMA crossovers, MACD histogram, ADX strength, and Aroon indicators to determine trend strength, direction, and potential reversals.

4. **MOMENTUM ANALYSIS**: Assess RSI, Williams %R, Rate of Change (ROC), Awesome Oscillator (AO), and Stochastic oscillators to identify overbought/oversold conditions and momentum shifts.

5. **VOLATILITY ASSESSMENT**: Examine ATR, Bollinger Band indicators, and custom volatility metrics to gauge market volatility and potential breakouts.

6. **SUPPORT & RESISTANCE**: Analyze the identified support and resistance levels and their significance for future price action.

7. **TECHNICAL OUTLOOK**: Synthesize all indicators to provide a cohesive short-term (1-2 weeks) and medium-term (1-2 months) outlook.

8. **KEY SIGNALS TO WATCH**: Highlight 3-5 specific technical signals that traders should monitor in the coming days/weeks.

For each section, explain the significance of indicator interactions, any notable divergences, and how these patterns have historically performed for this asset class. Include specific price levels where appropriate.

Data:
{json.dumps(indicator_data, indent=2)}
"""


    try:
        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        # Make the API call using Groq client
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful financial market analyst."},
                {"role": "user", "content": prompt}
            ],
            model=GROQ_MODEL,
            temperature=0.7,
            max_completion_tokens=1000
        )
        
        llm_analysis = response.choices[0].message.content.strip()
    except Exception as e:
        llm_analysis = f"LLM analysis failed: {str(e)}"

    return {
        "frequency": frequency,
        "indicators": indicator_data,
        "analysis": llm_analysis
    }

# Example usage
GROQ_API_KEY = "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"
GROQ_MODEL = "llama3-70b-8192"