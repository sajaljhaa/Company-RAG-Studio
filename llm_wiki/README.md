# LLM Wiki - Company Intelligence AI Chatbot

Welcome to the central knowledge base for the Company Intelligence AI Chatbot project.

## Wiki Index
- [Architecture](architecture.md) - High-level system architecture and component interactions.
- [RAG Pipeline](rag_pipeline.md) - Deep dive into multi-tenant vector storage, crawling strategy, and hybrid retrieval.

## Project Overview
This project provides an intelligent AI research chatbot capable of creating separate, isolated Retrieval-Augmented Generation (RAG) knowledge bases for individual companies. By crawling official company websites, dedicated career portals, and supplementing with real-time web search, the chatbot delivers accurate, cited answers regarding company vision, products, engineering culture, and open career opportunities.

## Tech Stack
- **Environment & Package Manager**: `uv`
- **Core Language**: Python 3.11+
- **LLM / Embeddings**: Mistral AI (`langchain-mistralai`) / Google Gemini (`google-genai`) / OpenAI (`langchain-openai`)
- **Vector Database**: ChromaDB (Multi-collection per company)
- **Web Crawler & Scraper**: `httpx`, `BeautifulSoup4`, `trafilatura`
- **Live Web Search Engine**: `duckduckgo-search` / `tavily-python`
- **User Interface**: Streamlit
