from sentence_transformers import SentenceTransformer  # Library for generating sentence embeddings
import chromadb                                         # ChromaDB for vector storage and querying

# -------------------------------------------------------------------------
# 1. Initialize the SentenceTransformer model:
#    - 'all-MiniLM-L6-v2' is a popular, lightweight sentence transformer
#    - This model will generate embedding vectors for queries/questions.
# -------------------------------------------------------------------------
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# -------------------------------------------------------------------------
# 2. Create a persistent ChromaDB client:
#    - 'PersistentClient' ensures that data is stored on disk at './chroma_db'
#    - This allows for data to persist across sessions.
# -------------------------------------------------------------------------
client_chroma = chromadb.PersistentClient(path="./chroma_db")

# -------------------------------------------------------------------------
# 3. Retrieve or create a collection in ChromaDB for CCNA embeddings:
#    - The collection is identified by the name "ccna_embeddings".
#    - If it doesn't exist, it will be created; otherwise, the existing one is returned.
# -------------------------------------------------------------------------
collection = client_chroma.get_or_create_collection(name="ccna_embeddings")

# -------------------------------------------------------------------------
# 4. Define a function to search questions based on a query:
#    - top_k determines how many results to retrieve from the database (default=5).
#    - The function encodes the user query into an embedding,
#      then asks ChromaDB to return the most similar documents.
# -------------------------------------------------------------------------
def search_questions(query, top_k=5):
    # Encode the user query into an embedding vector using the model
    query_embedding = model.encode([query])[0]

    # Query the ChromaDB collection for the top_k most similar documents
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents"]
    )

    # Return only the "documents" (i.e., the text data) from the query results
    return results["documents"]
