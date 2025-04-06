"""
ChromaDB implementation of the database provider
"""
import os
import chromadb
from db_provider import DatabaseProvider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
CHROMADB_PATH = os.getenv("CHROMADB_PATH", "./chroma_db")


class ChromaDBProvider(DatabaseProvider):
    """ChromaDB implementation of DatabaseProvider"""

    def __init__(self):
        self.client = None
        self.collection = None

    def initialize(self):
        """Initialize the ChromaDB client"""
        self.client = chromadb.PersistentClient(CHROMADB_PATH)
        return self.client

    def get_collection(self):
        """Get or create the ChromaDB collection"""
        if not self.client:
            self.initialize()

        try:
            # Try to get the collection first
            self.collection = self.client.get_collection("mental_health_conversations")
            print("Using existing ChromaDB collection")
        except:
            print("Creating new ChromaDB collection")
            self.collection = self.client.create_collection(
                name="mental_health_conversations",
                metadata={"hnsw:space": "cosine"}
            )
        return self.collection

    def collection_count(self):
        """Return the number of documents in the collection"""
        if not self.collection:
            self.get_collection()
        return self.collection.count()

    def add_embeddings(self, ids, embeddings, metadatas):
        """Add embeddings to the ChromaDB collection"""
        if not self.collection:
            self.get_collection()

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def search_similar(self, query_embedding, top_k=3):
        """Search for similar documents using vector similarity"""
        if not self.collection:
            self.get_collection()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas"]
        )

        # Format the results to match the expected structure
        formatted_results = []
        if results and 'metadatas' in results and results['metadatas']:
            for metadata in results['metadatas'][0]:  # First (and only) query results
                formatted_results.append({
                    "user_input": metadata["user_input"],
                    "expert_response": metadata["expert_response"]
                })

        return formatted_results