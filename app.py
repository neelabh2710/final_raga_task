from utils import final_call
from utils import QueryProcessor

# # query = str(input("Enter your query app: "))
# # groq_api_key = str(input("Enter your Groq API key: "))
# # serpapi_key = str(input("Enter your SerpAPI key: "))
# # processor = QueryProcessor(groq_api_key= groq_api_key,serpapi_key= serpapi_key)
# # result = processor.process_query(query)
# # TICKERS = result['tickers']

# # results = final_call(query,groq_api_key,serpapi_key)
# # print("Tickers found in the query:", TICKERS)
# # print(f"Answer:\n{results['answer']}\n")
# # print(f"Sources: {results['sources']}")




# import streamlit as st
# import yfinance as yf
# import numpy as np
# import ta as TA
# import matplotlib.pyplot as plt
# from utils import QueryProcessor  # Make sure you have this module

# # Set page config
# st.set_page_config(
#     page_title="Financial Analysis App",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS for styling
# st.markdown("""
#     <style>
#     .main {
#         background-color: #1E1E1E;
#         color: #FFFFFF;
#     }
#     .stTextInput>div>div>input {
#         color: #1E1E1E;
#     }
#     .st-bw {
#         background-color: #2E2E2E;
#     }
#     .css-1d391kg {
#         padding-top: 3.5rem;
#     }
#     </style>
#     """, unsafe_allow_html=True)

# def get_stock_data(ticker, period='1y'):
#     stock = yf.Ticker(ticker)
#     hist = stock.history(period=period)
#     return hist

# def plot_technical_indicators(data, ticker):
#     # Calculate indicators using TA-Lib
#     close_prices = data['Close'].values

#     # Calculate indicators
#     sma_20 = ta.trend.SMAIndicator(close=close_prices, window=100)
#     data['SMA_20'] = sma_20.sma_indicator()
#     data['RSI'] = ta.trend.SMAIndicator(close=close_prices, window=150).sma_indicator()
#     macdd = ta.trend.MACD(close=data['Close'])
#     macd = macdd.macd()
#     macdsignal = macdd.macd_signal()
#     macdhist = macdd.macd_diff()
#     # macd, macdsignal, macdhist = TA.MACD(close_prices, 
#     #                                    fastperiod=12, 
#     #                                    slowperiod=26, 
#     #                                    signalperiod=9)
    
#     # Create plot
#     plt.style.use('dark_background')
#     fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
#     # Price and SMA
#     ax1.plot(data['Close'], label='Closing Price', color='#00FFAA')
#     ax1.plot(data['SMA_20'], label='20-day SMA', color='#FFAA00')
#     ax1.set_ylabel('Price')
#     ax1.set_title(f'{ticker} Technical Analysis')
#     ax1.legend()
    
#     # RSI
#     ax2.plot(data['RSI'], label='RSI', color='#00AAFF')
#     ax2.axhline(70, color='red', linestyle='--')
#     ax2.axhline(30, color='green', linestyle='--')
#     ax2.set_ylabel('RSI')
#     ax2.legend()
    
#     # MACD
#     ax3.plot(macd, label='MACD', color='#FF00AA')
#     ax3.plot(macdsignal, label='Signal Line', color='#00FFAA')
#     ax3.bar(data.index, macdhist, label='Histogram', color='#555555')
#     ax3.set_ylabel('MACD')
#     ax3.legend()
    
#     plt.tight_layout()
#     return fig

# def main():
#     st.title("Financial Analysis Dashboard")
    
#     # Inputs in sidebar
#     with st.sidebar:
#         st.header("API Configuration")
#         groq_api_key = st.text_input("Groq API Key", type="password")
#         serpapi_key = st.text_input("SerpAPI Key", type="password")
#         query = st.text_area("Enter your query")
#         process_button = st.button("Process Query")
    
#     if process_button and groq_api_key and serpapi_key and query:
#         try:
#             processor = QueryProcessor(groq_api_key=groq_api_key, serpapi_key=serpapi_key)
#             result = processor.process_query(query)
#             tickers = result['tickers']
#             results = final_call(query, groq_api_key, serpapi_key)
            
#             # Display results
#             st.subheader("Analysis Results")
            
#             # Answer sections
#             st.markdown("### Answer")
#             st.markdown(f"**Direct Answer:**  \n{results['answer'].split('Direct Answer:')[1].split('Reasoning:')[0]}")
#             st.markdown(f"**Reasoning:**  \n{results['answer'].split('Reasoning:')[1].split('Citations:')[0]}")
#             st.markdown(f"**Citations:**  \n{results['answer'].split('Citations:')[1].split('Confidence Level:')[0]}")
#             st.markdown(f"**Confidence Level:**  \n{results['answer'].split('Confidence Level:')[1]}")
            
#             # Sources
#             st.markdown("### Sources")
#             for source in results['sources']:
#                 st.write(f"- {source[0]} ({source[1]})" if source[0] else "- General Analysis")
            
#             # Ticker graphs
#             if tickers:
#                 st.subheader("Technical Analysis Charts")
#                 cols = st.columns(2)
                
#                 for idx, ticker in enumerate(tickers):
#                     with cols[idx % 2]:
#                         try:
#                             data = get_stock_data(ticker)
#                             if not data.empty:
#                                 fig = plot_technical_indicators(data, ticker)
#                                 st.pyplot(fig)
#                             else:
#                                 st.warning(f"No data found for {ticker}")
#                         except Exception as e:
#                             st.error(f"Error fetching data for {ticker}: {str(e)}")
#         except Exception as e:
#             st.error(f"Error processing query: {str(e)}")

# if __name__ == "__main__":
#     main()




from utils import final_call
from utils import QueryProcessor
import streamlit as st

# Set page config
st.set_page_config(
    page_title="Financial Analysis App",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #FFFFFF;
        color: #1E1E1E;
    }
    .result-box {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        background-color: #F8F9FA;
        border-left: 5px solid #2E5BFF;
    }
    .confidence-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #FFF4E5;
        margin: 15px 0;
    }
    .section-header {
        color: #2E5BFF;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("Financial Analysis Assistant")
    
    # Inputs in sidebar
    with st.sidebar:
        st.header("API Configuration")
        groq_api_key = st.text_input("Groq API Key", type="password")
        serpapi_key = st.text_input("SerpAPI Key", type="password")
    
    # Main query input
    query = st.text_area("Enter your financial query:", 
                       placeholder="e.g., What is the current market outlook for tech stocks?",
                       height=100)
    
    if st.button("Analyze", type="primary"):
        if not groq_api_key or not serpapi_key:
            st.warning("Please provide both API keys in the sidebar")
            return
        if not query:
            st.warning("Please enter a query")
            return
            
        try:
            processor = QueryProcessor(groq_api_key=groq_api_key, serpapi_key=serpapi_key)
            result = processor.process_query(query)
            results = final_call(query, groq_api_key, serpapi_key)
            
            # Split the answer into components
            answer_parts = results['answer'].split('**\n\n**')
            if len(answer_parts) >= 4:
                direct_answer = answer_parts[1].replace('**', '').strip()
                reasoning = answer_parts[3].replace('**', '').strip()
                citations = answer_parts[5].replace('**', '').strip()
                confidence = answer_parts[7].replace('**', '').strip()
            else:
                direct_answer = results['answer']
                reasoning = citations = confidence = "N/A"

            # Display results in structured format
            # Custom CSS for styling
            st.markdown("""
                <style>
                .main {
                    background-color: #FFFFFF;
                }
                .result-box {
                    padding: 1.5rem;
                    border-radius: 8px;
                    margin: 1rem 0;
                    background-color: #f0f2f6;
                    border-left: 4px solid #2e5bff;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .result-box h4 {
                    color: #2e5bff !important;
                    margin-bottom: 0.8rem;
                    font-size: 1.1rem;
                }
                .result-content {
                    color: #1e1e1e;
                    line-height: 1.6;
                    font-size: 1rem;
                }
                h3 {
                    color: #1e1e1e !important;
                    border-bottom: 2px solid #2e5bff;
                    padding-bottom: 0.5rem;
                }
                </style>
                """, unsafe_allow_html=True)

            # Modified container section
            with st.container():
                
                # Direct Answer
                st.markdown(
                    f"""
                    <div class='result-box'>
                        <h4>📌 Direct Answer</h4>
                        <div class='result-content'>{direct_answer}</div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
            # Error handling remains the same
                    
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")

if __name__ == "__main__":
    main()