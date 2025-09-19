# in src/test_retrieval.py
import os
import logging
from langchain_community.embeddings import OllamaEmbeddings
from db_manager import DatabaseManager

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def test_rag_retrieval():
    """
    Tests the core retrieval step of the RAG system.
    """
    try:
        # --- 1. Initialize dependencies ---
        logging.info("Initializing DatabaseManager and OllamaEmbeddings...")
        db_manager = DatabaseManager(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            user=os.getenv("DB_USER", "rag_user"),
            password=os.getenv("DB_PASSWORD", "password123"),
            dbname=os.getenv("DB_NAME", "rag_db"),
        )
        embeddings_model = OllamaEmbeddings(
            model="nomic-embed-text", base_url="http://ollama:11434"
        )
        logging.info("Initialization complete.")

        # --- 2. Define a user question ---
        user_question = "What are the key concerns for a patient with Hypertension?"  # the hypertension is editable
        logging.info(f"Test Question: {user_question}")

        # --- 3. Embed the user's question ---
        logging.info("Generating embedding for the question...")
        question_embedding = embeddings_model.embed_query(user_question)
        logging.info("Embedding generated successfully.")

        # --- 4. Retrieve similar documents from the database ---
        logging.info("Finding similar documents in the database...")
        # We'll retrieve the top 3 most similar records
        similar_records = db_manager.find_similar_chunks(question_embedding, k=3)
        logging.info(f"Found {len(similar_records)} similar records.")

        # --- 5. Print the results ---
        print("\n--- Top 3 Retrieved Documents ---")
        for i, record in enumerate(similar_records):
            print(f"\n--- Document {i+1} ---")
            print(record)
        print("\n---------------------------------")

    except Exception as e:
        logging.error(
            f"An error occurred during the retrieval test: {e}", exc_info=True
        )


if __name__ == "__main__":
    test_rag_retrieval()
