# RAG Pipeline & Crawling Strategy

## Multi-Tenant RAG Strategy
To maintain precise, uncluttered contexts for each organization under research, vector storage is isolated by company identifiers.

### Data Flow
1. **Target Input**: User enters Company Name & Base URL (e.g., `https://openai.com`).
2. **Auto-Discovery**: Crawler fetches landing page, extracts navigation links, and discovers career/jobs pages.
3. **Extraction & Chunking**: `trafilatura` extracts clean main-text, stripping headers/footers. Text chunker splits content into ~1000 character overlapping windows.
4. **Embedding & Indexing**: Chunks are embedded and saved into `company_<sanitized_name>` collection in ChromaDB.
5. **Retrieval**: User queries are matched against the active company collection. If results are insufficient or external context is needed, live search is queried.
