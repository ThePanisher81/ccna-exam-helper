import psycopg2                                     # PostgreSQL database adapter
from sentence_transformers import SentenceTransformer  # Library for generating sentence embeddings
import chromadb                                      # ChromaDB for vector storage and querying

# ----------------------------------------------------------------------------
# 1. Initialize the ChromaDB client:
#    - PersistentClient stores data on disk at the specified path ("./chroma_db").
#    - This allows embeddings to persist across script runs.
# ----------------------------------------------------------------------------
client = chromadb.PersistentClient(path="./chroma_db")

# ----------------------------------------------------------------------------
# 2. Get or create a collection in ChromaDB:
#    - The collection is named "ccna_embeddings".
#    - If the collection doesn't exist, it's created; otherwise the existing
#      collection is returned.
# ----------------------------------------------------------------------------
collection = client.get_or_create_collection(name="ccna_embeddings")

# ----------------------------------------------------------------------------
# 3. Initialize the SentenceTransformer model:
#    - 'all-MiniLM-L6-v2' is a popular lightweight model for embedding sentences.
# ----------------------------------------------------------------------------
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# ----------------------------------------------------------------------------
# 4. Connect to the PostgreSQL database:
#    - Update the credentials as needed (dbname, user, password, host).
# ----------------------------------------------------------------------------
conn = psycopg2.connect(
    dbname="ccna_db",
    user="postgres",
    password="23058113",
    host="localhost"
)

# ----------------------------------------------------------------------------
# Function: preprocess_questions
#   - Fetches questions from the PostgreSQL database.
#   - Creates embeddings for each question using the SentenceTransformer model.
#   - Inserts the question texts and their embeddings into the ChromaDB collection.
# ----------------------------------------------------------------------------
def preprocess_questions():
    # Open a cursor to perform database operations
    with conn.cursor() as cur:
        # Retrieve question IDs and text from the 'questions' table
        cur.execute("SELECT id, question FROM questions")
        questions = cur.fetchall()

    # Loop through each question record
    for qid, question in questions:
        # Encode the question text into a vector using the Transformer model
        embedding = model.encode([question])[0]
        
        # Add the question text and its embedding to the ChromaDB collection
        collection.add(
            documents=[question],
            embeddings=[embedding],
            ids=[str(qid)]
        )

# ----------------------------------------------------------------------------
# Main entry point:
#   - Calls the preprocess_questions function when the script is executed.
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    preprocess_questions()
