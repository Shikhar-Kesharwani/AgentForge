import os
import uuid
import re

# Check for Pinecone Cloud Vector DB
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "agentforge")

USE_PINECONE = bool(PINECONE_API_KEY)

if USE_PINECONE:
    print("☁️  Using Managed Cloud Vector DB (Pinecone)")
    from pinecone import Pinecone, ServerlessSpec
    
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Ensure index exists
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=1536, # Standard text-embedding-ada-002 or gemini embedding dim
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Note: A real implementation requires generating an embedding vector using the Gemini API.
    # For this architecture demonstration, we assume store_memory/retrieve_memories will 
    # generate vectors prior to calling index.upsert() / index.query().
    
else:
    print("🏠 Using Local Standalone Vector DB (ChromaDB)")
    import chromadb
    
    # Create DB directory in workspace
    DB_DIR = os.path.abspath(os.path.join(os.getcwd(), "memory_db"))
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Initialize ChromaDB persistent client
    chroma_client = chromadb.PersistentClient(path=DB_DIR)
    collection = chroma_client.get_or_create_collection(name="agent_memory")

def sanitize_text(text: str) -> str:
    """Basic sanitization to prevent indirect prompt injections in memory."""
    malicious_patterns = [
        r"(?i)ignore previous instructions",
        r"(?i)forget everything",
        r"(?i)system instruction",
        r"(?i)you are now",
        r"(?i)bypass restrictions"
    ]
    sanitized = text
    for pattern in malicious_patterns:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized)
    return sanitized

def store_memory(task: str, outcome: str):
    """Store the outcome of a task as a long-term memory."""
    memory_id = str(uuid.uuid4())
    
    safe_task = sanitize_text(task)
    safe_outcome = sanitize_text(outcome)
    document = f"Task: {safe_task}\nOutcome: {safe_outcome}"
    
    if USE_PINECONE:
        # Pseudo-code for Pinecone implementation (needs actual vector generation)
        # vector = generate_gemini_embedding(document)
        # index.upsert(vectors=[(memory_id, vector, {"task": safe_task, "text": document})])
        pass
    else:
        collection.add(
            documents=[document],
            metadatas=[{"task": safe_task}],
            ids=[memory_id]
        )
    return memory_id

def retrieve_memories(query: str, n_results: int = 3) -> list[str]:
    """Retrieve relevant past memories based on a query."""
    if USE_PINECONE:
        # Pseudo-code for Pinecone implementation
        # query_vector = generate_gemini_embedding(query)
        # results = index.query(vector=query_vector, top_k=n_results, include_metadata=True)
        # return [match['metadata']['text'] for match in results['matches']]
        return []
    else:
        if collection.count() == 0:
            return []
        
        actual_n = min(n_results, collection.count())
        if actual_n == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=actual_n
        )
        return results.get("documents", [[]])[0]
