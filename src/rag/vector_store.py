import re
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import CHROMA_DB_DIR

class CompanyVectorStoreManager:
    def __init__(self, persist_directory: str = CHROMA_DB_DIR):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", " ", ""]
        )

    def _sanitize_collection_name(self, company_name: str) -> str:
        # ChromaDB collection names must be 3-63 chars, alphanumeric or underscores/hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', company_name.lower().strip())
        sanitized = f"company_{sanitized}"[:60]
        if len(sanitized) < 3:
            sanitized = f"{sanitized}_comp"
        return sanitized

    def get_indexed_companies(self) -> List[str]:
        """
        Return a list of user-friendly company names currently indexed.
        """
        collections = self.client.list_collections()
        companies = []
        for col in collections:
            if col.name.startswith("company_"):
                # retrieve metadata or reconstruct name
                clean_name = col.name[8:].replace("_", " ").title()
                companies.append(clean_name)
        return sorted(list(set(companies)))

    def add_company_documents(self, company_name: str, documents: List[Dict[str, Any]]) -> int:
        """
        Chunk and index scraped documents into the company's dedicated collection.
        """
        collection_name = self._sanitize_collection_name(company_name)
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"company": company_name}
        )

        texts = []
        metadatas = []
        ids = []

        chunk_counter = 0
        for doc in documents:
            content = doc.get("content", "")
            if not content.strip():
                continue

            chunks = self.text_splitter.split_text(content)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc['url']}_{i}_{chunk_counter}"
                chunk_counter += 1
                
                texts.append(chunk)
                metadatas.append({
                    "url": doc.get("url", ""),
                    "title": doc.get("title", ""),
                    "content_type": doc.get("content_type", "main_website"),
                    "company": company_name,
                    "domain": doc.get("domain", "")
                })
                ids.append(chunk_id)

        if texts:
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                collection.upsert(
                    documents=texts[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size],
                    ids=ids[i:i+batch_size]
                )

        return len(texts)

    def search_company_knowledge(self, company_name: str, query: str, top_k: int = 5, content_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a given company.
        """
        collection_name = self._sanitize_collection_name(company_name)
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            return []

        where_filter = None
        if content_type_filter:
            where_filter = {"content_type": content_type_filter}

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )

        formatted_results = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0]*len(docs)

            for doc, meta, dist in zip(docs, metas, distances):
                formatted_results.append({
                    "content": doc,
                    "metadata": meta,
                    "score": dist
                })

        return formatted_results
