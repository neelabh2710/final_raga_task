import yfinance as yf
import pandas as pd
from groq import Groq
from edgar import set_identity
from edgar import Company
set_identity("neelabhv3@gmail.com") 

def generate_financial_analysis(client, ticker, cash_flow_text, income_statement_text, balance_sheet_text):
    """Generate a detailed analysis of financial statements using Groq LLM"""
    
    prompt = f"""
You are an expert financial analyst specializing in corporate financial statement analysis. 
I need you to analyze the following financial data for {ticker} and provide a comprehensive analysis.

The data includes the Cash Flow Statement, Income Statement, and Balance Sheet for the past few years.

Please provide:

1. **CASH FLOW ANALYSIS**: 
   - Analyze operating, investing, and financing cash flows
   - Identify trends in free cash flow generation
   - Evaluate capital allocation decisions (dividends, buybacks, capex)
   - Assess cash conversion efficiency

2. **PROFITABILITY ANALYSIS**:
   - Analyze revenue growth, margins (gross, operating, net)
   - Identify trends in key profitability metrics
   - Compare performance against previous years

3. **BALANCE SHEET STRENGTH**:
   - Evaluate liquidity and solvency metrics
   - Analyze debt levels and leverage
   - Assess working capital management

4. **FINANCIAL HEALTH INDICATORS**:
   - Calculate and interpret key financial ratios
   - Identify any red flags or areas of concern
   - Highlight financial strengths

5. **FORWARD OUTLOOK**:
   - Based on the financial trends, provide insights on future performance
   - Identify potential risks and opportunities

Financial Data:

**Cash Flow Statement:**
{cash_flow_text}

**Income Statement:**
{income_statement_text}

**Balance Sheet:**
{balance_sheet_text}

Provide a detailed, professional analysis that would be valuable for investors.
"""
    
    try:
        # Make the API call using Groq client
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert financial analyst."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
            temperature=0.5,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Analysis generation failed: {str(e)}"

def analyze_financial_statements(ticker: str, groq_api_key: str):
    """
    Extract financial data for a given ticker and generate a detailed analysis using Groq LLM.
    
    Args:
        ticker (str): The stock ticker symbol
        groq_api_key (str): API key for Groq
        
    Returns:
        dict: Contains the formatted financial data and the analysis
    """
    try:
        # Initialize Groq client
        client = Groq(api_key=groq_api_key)
        
        # Get the financial data
        company = Company(ticker)
        financials = company.get_financials()
        cashflow_df = financials.cashflow_statement()
        income_df = financials.income_statement()
        balance_df = financials.balance_sheet()
        
        # # Convert DataFrames to structured text
        # cash_flow_text = cashflow_df.to_string()
        # income_statement_text = income_df.to_string()
        # balance_sheet_text = balance_df.to_string()
        
        # Generate analysis using LLM
        analysis = generate_financial_analysis(client, ticker, cashflow_df, income_df, balance_df)
        
        return {
            "ticker": ticker,
            "cash_flow_data": cashflow_df,
            "income_statement": income_df,
            "balance_sheet": balance_df,
            "analysis": analysis
        }
        
    except Exception as e:
        return {"error": f"Error analyzing {ticker}: {str(e)}"}