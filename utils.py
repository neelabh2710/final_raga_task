import os
import json
import requests
from groq import Groq
from typing import Dict, List, Optional, Union
from main import process_tickers
from main import FinancialQueryProcessor


# from duckduckgo_search import DDGS

class QueryProcessor:
    def __init__(self, groq_api_key: str, serpapi_key: str):
        self.groq_client = Groq(api_key=groq_api_key)
        self.serpapi_key = serpapi_key
        self.model = "llama3-70b-8192"  # Using Llama 3 70B for best performance
        
    def process_query(self, query: str) -> Dict:
        """
        Process a financial query to extract tickers and enhance it with metadata
        """
        # Step 1: Initial analysis with Groq LLM
        enhanced_query = self._enhance_query(query)
        
        # Step 2: Check if tickers are explicitly mentioned
        tickers = self._extract_explicit_tickers(enhanced_query)
        
        # Step 3: If no tickers found, use Google Search to identify them
        if not tickers:
            tickers = self._search_for_tickers(enhanced_query)
            
        # Step 4: Create structured output with metadata
        result = {
            "original_query": query,
            "enhanced_query": enhanced_query,
            "tickers": tickers,
            "query_type": self._determine_query_type(enhanced_query),
            "time_frame": self._extract_time_frame(enhanced_query)
        }
        
        return result
    
    def _enhance_query(self, query: str) -> str:
        """Use Groq to make the query more specific and detailed"""
        system_prompt = """
        You are a financial query enhancement assistant. Your task is to:
        1. Make vague financial queries more specific and detailed
        2. Preserve all information from the original query
        3. Add specificity around timeframes if they're vague (e.g., "past weeks" -> "past 2 weeks")
        4. DO NOT invent information not implied in the original query
        5. Return ONLY the enhanced query text with no additional explanation

        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Enhance this financial query: {query}"}
        ]
        
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    
    def _extract_explicit_tickers(self, query: str) -> List[str]:
        """Extract explicitly mentioned stock tickers from the query"""
        # Use Groq to identify any explicit tickers in the query
        system_prompt = """
        Extract all stock ticker symbols mentioned in the text. 
        Return ONLY a JSON array of ticker symbols without any explanation.
        If no tickers are found, return an empty array.
        Example: ["AAPL", "MSFT", "GOOGL"]
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_tokens=100
        )
        
        try:
            tickers = json.loads(response.choices[0].message.content.strip())
            return tickers if isinstance(tickers, list) else []
        except:
            return []
    
    def _search_for_tickers(self, query: str) -> List[str]:
        """Use Google Search via SerpAPI to find relevant tickers when none are explicitly mentioned"""
        # First, use Groq to create a search query specifically for finding tickers
        system_prompt = """
        Convert this financial query into a search query specifically designed to find 
        stock ticker symbols for the companies or sector mentioned, if the sector is mentioned in the query then go for searching of that sector index.
        and also dont add any kind of new thing to the query.
        1. Do not add any new information to the query.
        Return ONLY the search query with no additional text.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.5,
            max_tokens=100
        )
        
        search_query = response.choices[0].message.content.strip()
        print(f"Search Query: {search_query}")
        # Now use SerpAPI to perform the search
        search_results = self._get_search_result(search_query)
        print(f"Search Results#################################: {search_results}##########################################")
        # Extract tickers from search results using Groq
        if search_results:
            system_prompt = """
            Extract all stock ticker symbols from this search result text.
            Return ONLY a JSON array of ticker symbols without any explanation.
            If no tickers are found, return an empty array.
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(search_results)}
            ]
            
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=100
            )
            
            try:
                tickers = json.loads(response.choices[0].message.content.strip())
                return tickers if isinstance(tickers, list) else []
            except:
                return []
        
        return []
    
    def _get_search_result(self, query: str) -> Optional[Dict]:
        """Perform a Google search using SerpAPI"""
        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.serpapi_key,
                "location": "United States"
            }
            
            response = requests.get("https://serpapi.com/search", params=params)
            json_response = response.json()
            
            # Return the answer box if available, otherwise organic results
            if "answer_box" in json_response:
                return json_response["answer_box"]
            elif "organic_results" in json_response:
                return json_response["organic_results"][:3]  # Return top 3 results
            else:
                return None
        except Exception as e:
            print(f"Error performing search: {e}")
            return None
        
    def _determine_query_type(self, query: str) -> str:
        """Determine the type of financial query (price check, performance analysis, etc.)"""
        system_prompt = """
        Categorize this financial query into exactly ONE of these types:
        - PRICE_CHECK: Queries about current or historical prices
        - PERFORMANCE_ANALYSIS: Queries about performance over time
        - COMPARISON: Queries comparing multiple stocks
        - NEWS: Queries about recent news or events
        - FUNDAMENTALS: Queries about financial fundamentals
        - PREDICTION: Queries about future performance
        - OTHER: Any other type of query
        
        Return ONLY the category name with no explanation.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_tokens=20
        )
        
        return response.choices[0].message.content.strip()
    
    def _extract_time_frame(self, query: str) -> Dict:
        """Extract time frame information from the query"""
        system_prompt = """
        just understand that how many days, weeks, months or years are there in the query.
        and return the the time frame in no of days only 
        Return ONLY the JSON with no additional text.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_tokens=150
        )
        
        try:
            time_frame = json.loads(response.choices[0].message.content.strip())
            return time_frame
        except:
            return {
                "period_type": "none",
                "start_date": None,
                "end_date": None,
                "relative_period": None
            }


def final_call(query: str,groq_api_key: str, serpapi_key: str) -> Dict:
    """
    Final function to process the query and return the result
    """
    # Initialize the processor
    processor = QueryProcessor(
        groq_api_key= groq_api_key,
        serpapi_key= serpapi_key
    )
    
    # Process a vague query
    result = processor.process_query(query)
    
    # Extract tickers and process them
    TICKERS = result['tickers']
    vector_db = process_tickers(
            tickers=TICKERS,
            years=1,
            ask_period="60d",
            groq_api_key=groq_api_key
        )
    
    PROCESSOR = FinancialQueryProcessor(
            index_path="financial_data.index",
            metadata_path="metadata.json",
            groq_api_key=groq_api_key
        )

    result = PROCESSOR.query(query)

    return result


# GROQ_API_KEY = "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"
# # Serp_API_KEY = "2c9f61a889ad98af47c7fdfc0e3b6b218346e52ea567c55a64874063917f8497"
# user_query = str(input("Enter your financial query: "))
# result = final_call(user_query, GROQ_API_KEY, Serp_API_KEY)
# print(f"Answer:\n{result['answer']}\n")
# print(f"Sources: {result['sources']}")

