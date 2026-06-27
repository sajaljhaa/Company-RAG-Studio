import streamlit as st
import os
from pathlib import Path
from src.config import GEMINI_API_KEY, OPENAI_API_KEY, MISTRAL_API_KEY, LLM_PROVIDER
from src.crawler.company_crawler import CompanyCrawler
from src.search.web_search import WebSearchEngine
from src.rag.vector_store import CompanyVectorStoreManager
from src.rag.rag_chain import CompanyRAGChain

# Page Setup
st.set_page_config(
    page_title="Company Intelligence AI Chatbot",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .stCard {
        border-radius: 10px;
        padding: 1.5rem;
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
    }
    .source-tag {
        display: inline-block;
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Objects
@st.cache_resource
def get_managers():
    vector_mgr = CompanyVectorStoreManager()
    search_eng = WebSearchEngine()
    rag_chain = CompanyRAGChain(vector_store=vector_mgr, search_engine=search_eng)
    crawler = CompanyCrawler()
    return vector_mgr, search_eng, rag_chain, crawler

vector_mgr, search_eng, rag_chain, crawler = get_managers()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_company" not in st.session_state:
    st.session_state.active_company = None

# Sidebar Setup
with st.sidebar:
    st.title("🏢 Company RAG Studio")
    st.caption("Powered by Python `uv` & Multi-Tenant RAG")
    
    st.divider()
    
    # Provider status check
    st.subheader("⚙️ System Status")
    if LLM_PROVIDER == "mistral" and MISTRAL_API_KEY:
        st.success("Mistral AI API: Active 🚀")
    elif LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        st.success("Google Gemini API: Active")
    elif LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        st.success("OpenAI API: Active")
    else:
        st.warning("⚠️ LLM Key Missing in `.env` (Fallback mode active)")

    st.divider()

    # Company Selection
    st.subheader("🎯 Select Active Company")
    indexed_companies = vector_mgr.get_indexed_companies()
    
    if indexed_companies:
        selected_company = st.selectbox(
            "Target Company Portfolio",
            options=indexed_companies,
            index=0 if st.session_state.active_company is None or st.session_state.active_company not in indexed_companies else indexed_companies.index(st.session_state.active_company)
        )
        if selected_company != st.session_state.active_company:
            st.session_state.active_company = selected_company
            st.session_state.messages = [] # reset chat context on company change
            st.rerun()
    else:
        st.info("No companies indexed yet. Crawl a company below to start!")
        st.session_state.active_company = None

    st.divider()

    # Fast Crawl Quick Action
    st.subheader("🔍 Discovery Assistant")
    quick_search_term = st.text_input("Find Company Web & Career Links", placeholder="e.g. Stripe, OpenAI")
    if st.button("Search Links"):
        if quick_search_term:
            with st.spinner("Searching live web for company portals..."):
                found = search_eng.find_company_links(quick_search_term)
                st.write("**Main Website Links:**")
                for l in found["main_links"]:
                    st.markdown(f"- [{l}]({l})")
                st.write("**Career Portal Links:**")
                for l in found["career_links"]:
                    st.markdown(f"- [{l}]({l})")

# Header
st.markdown('<div class="main-header">Multi-Company Intelligence & RAG AI Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Crawl target company websites, analyze career portals, and query deep company insights with source attributions.</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💬 AI Company Chat", "🕸️ Crawl & Index Company", "📊 Knowledge Inspector"])

# TAB 1: AI CHAT
with tab1:
    if not st.session_state.active_company:
        st.info("👈 Please select or crawl a company profile from the sidebar to begin research.")
    else:
        st.markdown(f"### Researching: **{st.session_state.active_company}**")
        
        # Enable Web Search Toggle
        enable_web = st.checkbox("🌐 Enable Dynamic Live Web Search Fallback", value=True, help="Complements local vector storage with real-time web queries if needed.")

        # Display Chat History
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander("📌 View Referenced Sources"):
                        for src in message["sources"]:
                            st.markdown(f"- [{src['title']}]({src['url']}) `({src['type']})`")

        # Chat Input
        if user_input := st.chat_input(f"Ask anything about {st.session_state.active_company} (e.g. tech stack, open roles, culture)..."):
            # Render user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Generate Assistant Answer
            with st.chat_message("assistant"):
                with st.spinner("Searching knowledge vector store & analyzing context..."):
                    result = rag_chain.query_company(
                        company_name=st.session_state.active_company,
                        user_query=user_input,
                        enable_web_search=enable_web
                    )
                    
                    st.markdown(result["answer"])
                    
                    if result["sources"]:
                        with st.expander("📌 View Referenced Sources"):
                            for src in result["sources"]:
                                st.markdown(f"- [{src['title']}]({src['url']}) `({src['type']})`")

            # Store assistant response in history
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"]
            })

# TAB 2: CRAWL & INDEX
with tab2:
    st.markdown("### Crawl New Company Portals")
    st.write("Enter the target company details below. The crawler will automatically explore the main website, career portals, and job listings.")

    col1, col2 = st.columns(2)
    with col1:
        comp_name_input = st.text_input("Company Name *", placeholder="e.g. OpenAI, Stripe, Google")
    with col2:
        comp_url_input = st.text_input("Main Website or Career URL *", placeholder="e.g. https://openai.com")

    with st.expander("⚙️ Advanced Crawler Settings"):
        max_pages = st.slider("Maximum Pages to Crawl", min_value=3, max_value=30, value=12)
        extra_urls_text = st.text_area("Additional Specific URLs to Crawl (One per line)", placeholder="https://openai.com/careers\nhttps://openai.com/about")

    if st.button("🚀 Start Company Crawling & Indexing", type="primary"):
        if not comp_name_input or not comp_url_input:
            st.error("Please enter both Company Name and Main URL.")
        else:
            extra_urls = [line.strip() for line in extra_urls_text.split("\n") if line.strip()]
            crawler.max_pages = max_pages
            
            progress_bar = st.progress(0, text="Starting web crawler...")
            
            with st.spinner(f"Crawling {comp_name_input} pages and career portal..."):
                crawled_docs = crawler.crawl_company(comp_url_input, extra_urls=extra_urls)
                progress_bar.progress(60, text=f"Crawled {len(crawled_docs)} pages. Chunking & vectorizing into ChromaDB...")
                
                if crawled_docs:
                    total_chunks = vector_mgr.add_company_documents(comp_name_input, crawled_docs)
                    progress_bar.progress(100, text="Indexing complete!")
                    
                    st.success(f"Successfully indexed **{comp_name_input}**! Added {len(crawled_docs)} pages and {total_chunks} vector chunks.")
                    
                    # Set as active company
                    st.session_state.active_company = comp_name_input.strip().title()
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error("Failed to extract content from the provided URLs. Please check the domain or try adding direct links.")

# TAB 3: INSPECTOR
with tab3:
    st.markdown("### Company Knowledge Base Explorer")
    if not indexed_companies:
        st.info("No companies indexed in ChromaDB yet.")
    else:
        inspect_comp = st.selectbox("Inspect Portfolio", options=indexed_companies, key="inspect_select")
        if inspect_comp:
            # Query sample documents
            sample_chunks = vector_mgr.search_company_knowledge(inspect_comp, query="company product career jobs technology", top_k=10)
            
            st.markdown(f"#### Total Chunks Preview for **{inspect_comp}**")
            st.metric("Retrieved Sample Chunks", len(sample_chunks))

            for i, chunk in enumerate(sample_chunks, 1):
                meta = chunk["metadata"]
                with st.expander(f"Chunk #{i} - {meta.get('title', 'Untitled')} ({meta.get('content_type', 'website')})"):
                    st.write(f"**URL:** [{meta.get('url')}]({meta.get('url')})")
                    st.write(f"**Domain:** `{meta.get('domain')}`")
                    st.markdown("**Content Snippet:**")
                    st.info(chunk["content"])
