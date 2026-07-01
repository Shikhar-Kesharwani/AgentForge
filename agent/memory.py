import chromadb
import uuid
import os

# Create DB directory in workspace
DB_DIR = os.path.abspath(os.path.join(os.getcwd(), "memory_db"))
os.makedirs(DB_DIR, exist_ok=True)

# Initialize ChromaDB persistent client
client = chromadb.PersistentClient(path=DB_DIR)

# Get or create a collection for agent memories
collection = client.get_or_create_collection(name="agent_memory")

import re

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
    
    # Sanitize inputs before saving to DB
    safe_task = sanitize_text(task)
    safe_outcome = sanitize_text(outcome)
    
    document = f"Task: {safe_task}\nOutcome: {safe_outcome}"
    
    collection.add(
        documents=[document],
        metadatas=[{"task": safe_task}],
        ids=[memory_id]
    )
    return memory_id

def retrieve_memories(query: str, n_results: int = 3) -> list[str]:
    """Retrieve relevant past memories based on a query."""
    # If the collection is empty, return empty list to avoid errors
    if collection.count() == 0:
        return []
    
    # Bound n_results by the total number of documents
    num_docs = collection.count()
    actual_n = min(n_results, num_docs)
    
    if actual_n == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=actual_n
    )
    
    documents = results.get("documents", [[]])[0]
    return documents
