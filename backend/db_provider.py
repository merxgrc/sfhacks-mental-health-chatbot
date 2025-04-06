"""
Database provider abstraction layer allowing switching between MongoDB and ChromaDB
"""
import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_PROVIDER = os.getenv("DB_PROVIDER", "chromadb").lower()  # Default to ChromaDB if not specified


class DatabaseProvider(ABC):
    """Abstract base class for database providers"""
    
    @abstractmethod
    def initialize(self):
        """Initialize the database connection"""
        pass
    
    @abstractmethod
    def get_collection(self):
        """Get or create the collection/table for storing embeddings"""
        pass
    
    @abstractmethod
    def collection_count(self):
        """Return the number of documents in the collection"""
        pass
    
    @abstractmethod
    def add_embeddings(self, ids, texts, embeddings, metadatas):
        """Add embeddings to the collection"""
        pass
    
    @abstractmethod
    def search_similar(self, query_embedding, top_k=3):
        """Search for similar documents using vector similarity"""
        pass


def get_db_provider():
    """Factory function to get the appropriate database provider based on configuration"""
    if DB_PROVIDER == "mongodb":
        from mongodb_utils import MongoDBProvider
        return MongoDBProvider()
    else:
        from chromadb_utils import ChromaDBProvider
        return ChromaDBProvider()