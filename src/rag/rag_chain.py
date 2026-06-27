import os
from typing import List, Dict, Any
from src.config import LLM_PROVIDER, MISTRAL_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, MISTRAL_MODEL, GEMINI_MODEL, OPENAI_MODEL
from src.rag.vector_store import CompanyVectorStoreManager
from src.search.web_search import WebSearchEngine

class CompanyRAGChain:
    def __init__(self, vector_store: CompanyVectorStoreManager, search_engine: WebSearchEngine):
        self.vector_store = vector_store
        self.search_engine = search_engine
        self._init_llm()

    def _init_llm(self):
        self.llm_type = LLM_PROVIDER
        if self.llm_type == "mistral" and MISTRAL_API_KEY:
            try:
                from langchain_mistralai import ChatMistralAI
                self.llm = ChatMistralAI(
                    model=MISTRAL_MODEL,
                    api_key=MISTRAL_API_KEY,
                    temperature=0.3
                )
                return
            except Exception as e:
                print(f"Failed to initialize ChatMistralAI: {e}")

        if self.llm_type == "gemini" and GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.llm = ChatGoogleGenerativeAI(
                    model=GEMINI_MODEL,
                    google_api_key=GEMINI_API_KEY,
                    temperature=0.3
                )
                return
            except Exception as e:
                print(f"Failed to initialize ChatGoogleGenerativeAI: {e}")

        if self.llm_type == "openai" and OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model=OPENAI_MODEL,
                    api_key=OPENAI_API_KEY,
                    temperature=0.3
                )
                return
            except Exception as e:
                print(f"Failed to initialize ChatOpenAI: {e}")

        # Fallback if no keys set or provider init fails
        self.llm = None

    def query_company(self, company_name: str, user_query: str, enable_web_search: bool = True) -> Dict[str, Any]:
        """
        Execute full RAG + Web Search research pipeline.
        """
        # 1. Retrieve local RAG knowledge
        rag_results = self.vector_store.search_company_knowledge(company_name, user_query, top_k=5)
        
        # 2. Perform live web search if requested or context is sparse
        web_results = []
        if enable_web_search:
            search_query = f"{company_name} {user_query}"
            web_results = self.search_engine.search(search_query)

        # 3. Construct Context
        context_blocks = []
        sources = []

        if rag_results:
            context_blocks.append("--- RAG Knowledge Base Context ---")
            for i, res in enumerate(rag_results, 1):
                meta = res["metadata"]
                url = meta.get("url", "N/A")
                title = meta.get("title", "Document")
                ctype = meta.get("content_type", "website")
                context_blocks.append(f"[{i}] Title: {title} ({ctype})\nURL: {url}\nContent: {res['content']}\n")
                sources.append({"title": title, "url": url, "type": ctype})

        if web_results:
            context_blocks.append("--- Live Web Search Context ---")
            for j, web in enumerate(web_results, 1):
                url = web.get("url", "")
                title = web.get("title", "")
                context_blocks.append(f"[Web-{j}] Title: {title}\nURL: {url}\nSnippet: {web['snippet']}\n")
                sources.append({"title": title, "url": url, "type": "web_search"})

        full_context = "\n".join(context_blocks)

        # 4. Generate Response using LLM (or structured template if offline)
        if self.llm:
            prompt = f"""You are an expert Company Research AI assistant answering questions about '{company_name}'.
Answer the user query thoroughly based on the provided context.
Highlight key details about products, technology stack, company vision, engineering culture, or career opportunities whenever relevant.
Always include markdown inline source links (e.g., [Title](URL)) when referencing facts.

Context Information:
{full_context}

User Query: {user_query}

Detailed Answer:"""
            try:
                response = self.llm.invoke(prompt)
                answer_text = response.content
            except Exception as e:
                answer_text = f"Error calling LLM provider ({self.llm_type}): {e}\n\nHere is the raw retrieved context:\n{full_context}"
        else:
            # Smart fallback when API key is not yet configured
            answer_text = f"**[Note: LLM API Key not detected in .env. Showing structured retrieved context for '{company_name}']**\n\n"
            if rag_results:
                answer_text += "### Key Information from Company Knowledge Base:\n"
                for res in rag_results[:3]:
                    meta = res["metadata"]
                    answer_text += f"- **[{meta.get('title', 'Link')}]({meta.get('url', '#')})** ({meta.get('content_type')}):\n  {res['content'][:300]}...\n\n"
            if web_results:
                answer_text += "### Live Web Search Highlights:\n"
                for web in web_results[:3]:
                    answer_text += f"- **[{web.get('title', 'Web Link')}]({web.get('url', '#')})**:\n  {web.get('snippet', '')}\n\n"

        return {
            "answer": answer_text,
            "sources": sources,
            "rag_chunks_found": len(rag_results),
            "web_results_found": len(web_results)
        }
