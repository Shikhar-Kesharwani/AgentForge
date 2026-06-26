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

def store_memory(task: str, outcome: str):
    """Store the outcome of a task as a long-term memory."""
    memory_id = str(uuid.uuid4())
    document = f"Task: {task}\nOutcome: {outcome}"
    
    collection.add(
        documents=[document],
        metadatas=[{"task": task}],
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
