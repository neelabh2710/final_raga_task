import json
import faiss
import numpy as np
from groq import Groq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from agents.tech import yf_tech_analysis_with_llm
from agents.fundamental import analyze_financial_statements
from agents.sec import get_filing_data_json


class FinancialVectorDB:
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        self.index = None
        self.metadata = []
        self._init_faiss_index()

    def _init_faiss_index(self):
        dim = self.embedder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(dim)

    def _chunk_data(self, data: Dict) -> List[Dict]:
        """Chunk JSON data into text chunks with metadata"""
        chunks = []
        
        # SEC Filing Data
        if 'form_type' in data:
            for key, value in data.items():
                if key in ['ticker', 'form_type', 'accession_number']:
                    continue
                text_chunks = self.text_splitter.split_text(str(value))
                for chunk in text_chunks:
                    chunks.append({
                        'text': chunk,
                        'source': 'sec_filing',
                        'section': key,
                        'ticker': data['ticker']
                    })

        # Technical Analysis
        if 'analysis' in data:
            text_chunks = self.text_splitter.split_text(data['analysis'])
            for chunk in text_chunks:
                chunks.append({
                    'text': chunk,
                    'source': 'technical_analysis',
                    'ticker': data.get('ticker', ''),
                    'frequency': data.get('frequency', '')
                })

        # Financial Analysis
        if 'cash_flow_data' in data:
            analysis_chunks = self.text_splitter.split_text(data['analysis'])
            for chunk in analysis_chunks:
                chunks.append({
                    'text': chunk,
                    'source': 'financial_analysis',
                    'ticker': data['ticker']
                })

        return chunks

    def add_documents(self, documents: List[Dict]):
        """Add processed documents to the FAISS index"""
        embeddings = []
        new_metadata = []

        for doc in documents:
            chunks = self._chunk_data(doc)
            for chunk in chunks:
                embedding = self.embedder.encode([chunk['text']])[0]
                embeddings.append(embedding)
                new_metadata.append(chunk)

        if embeddings:
            embeddings_np = np.array(embeddings).astype('float32')
            self.index.add(embeddings_np)
            self.metadata.extend(new_metadata)

    def save_index(self, index_path: str, metadata_path: str):
        """Save FAISS index and metadata"""
        faiss.write_index(self.index, index_path)
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f)

def process_tickers(tickers: List[str], years: int, ask_period: str, groq_api_key: str):
    db = FinancialVectorDB()

    for ticker in tickers:
        try:
            # Process SEC filings
            sec_data = json.loads(get_filing_data_json(ticker, years))
            
            # Process technical analysis
            tech_data = yf_tech_analysis_with_llm(ticker, ask_period)
            
            # Process financial statements
            financial_data = analyze_financial_statements(ticker, groq_api_key)

            # Add all data to vector DB
            db.add_documents([sec_data, tech_data, financial_data])

        except Exception as e:
            print(f"Failed to process {ticker}: {str(e)}")
            continue

    # Save the final index
    db.save_index("financial_data.index", "metadata.json")
    return db





class FinancialQueryProcessor:
    def __init__(self, index_path: str, metadata_path: str, groq_api_key: str):
        self.groq_client = Groq(api_key=groq_api_key)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load FAISS index and metadata
        self.index = faiss.read_index(index_path)
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
    def _enhance_query(self, original_query: str) -> str:

        """Use LLM to enhance the query with financial terminology and context"""
        enhancement_prompt = f"""
        Original query: {original_query}

        You are a financial research expert. Expand the query into a more comprehensive version suitable for deep financial analysis.

        Context:
        - We have full technical analysis data, including trend indicators (MACD, EMA, ADX, Aroon), momentum indicators (RSI, AO, Williams %R, ROC, Stochastic), volume-based indicators (OBV, CMF, MFI), and volatility measures (ATR, custom volatility).
        - We also have fundamental analysis data including full cash flow statements, income statements, and balance sheets.
        - Time series data is available by date and includes support/resistance levels.

        Your task is to rewrite the query to:
        1. Use relevant financial and technical terminology based on the available indicators
        2. Add analytical depth — mention metrics, trends, or relationships that might be relevant
        3. Specify date or numerical ranges if implied or useful
        4. Include alternative phrasings of the question
        5. Mention regulatory standards (SEC filings, GAAP, IFRS) if applicable

        Return ONLY the enhanced version of the query. Do not add commentary or explanation.
        """

        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a financial search query optimizer."},
                    {"role": "user", "content": enhancement_prompt}
                ],
                model="llama3-70b-8192",
                temperature=0.3,
                max_tokens=200
            )
            print(f"Enhanced query: {response.choices[0].message.content.strip()}")
            return response.choices[0].message.content.strip()
        except:
            return original_query
        
    def _retrieve_context(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant context chunks from the vector database"""
        enhanced_query = self._enhance_query(query)
        query_embedding = self.embedder.encode([enhanced_query], convert_to_tensor=False)
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = self.index.search(query_embedding, top_k)
        return [self.metadata[idx] for idx in indices[0]]

    def _format_context(self, context_chunks: List[Dict]) -> str:
        """Format retrieved chunks into a coherent context string"""
        context_by_source = {}
        
        for chunk in context_chunks:
            source = chunk['source']
            ticker = chunk.get('ticker', 'Unknown')
            content = chunk['text']
            
            if source not in context_by_source:
                context_by_source[source] = []
            
            context_entry = f"[{ticker} - {source.upper()}]: {content}"
            if 'section' in chunk:
                context_entry = f"[{ticker} - {chunk['section']}]: {content}"
                
            context_by_source[source].append(context_entry)
        
        formatted_context = []
        for source, entries in context_by_source.items():
            formatted_context.append(f"=== {source.upper()} CONTEXT ===")
            formatted_context.extend(entries[:3])  # Limit to top 3 per source
            
        return "\n\n".join(formatted_context)[:3000]  # Truncate to 3000 chars

    def query(self, question: str, model: str = "llama3-70b-8192") -> Dict:
        """Process a query and generate an answer with citations"""
        try:
            question_enh = enhanced_query = self._enhance_query(question)
            # Retrieve relevant context
            context_chunks = self._retrieve_context(question_enh)
            print(f"Retrieved context chunks=================================================================================\
                  : {context_chunks}")
            formatted_context = self._format_context(context_chunks)
            print(f"Formatted context: {formatted_context}")
            # Prepare LLM prompt
            prompt = f"""
You are a financial analysis assistant providing sharp, evidence-based insights.

Using the financial and technical data provided below, answer the question with clear reasoning. Prioritize direct, insightful responses over generic commentary.

Context:
{formatted_context}

Question:
{question}

Your response must include:
1. Answer – A concise, well-supported answer to the question.
2. Reasoning – Brief explanation specific trends or data (e.g., RSI, MACD, volume vs average volume, etc.).
3. Citations – Use [Ticker-Source] to reference data points (e.g., [AMZN-TECHNICAL]).
4. Confidence Level – High / Medium / Low.


"""





            # Generate response
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a meticulous financial analyst that cites sources."},
                    {"role": "user", "content": prompt}
                ],
                model=model,
                temperature=0.5,
                max_tokens=1024,
                stop=["<|eot_id|>"]
            )
            
            return {
                "question": question,
                "answer": response.choices[0].message.content,
                "context_chunks": context_chunks,
                "sources": list({(c['ticker'], c['source']) for c in context_chunks})
            }
            
        except Exception as e:
            return {"error": str(e), "question": question}








