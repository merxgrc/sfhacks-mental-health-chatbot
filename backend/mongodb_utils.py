"""
MongoDB implementation of the database provider
"""
import os
from pymongo import MongoClient
from db_provider import DatabaseProvider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")


class MongoDBProvider(DatabaseProvider):
    """MongoDB implementation of DatabaseProvider"""

    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None

    def initialize(self):
        """Initialize the MongoDB client"""
        if not MONGODB_URI:
            raise ValueError("No MongoDB URI found. Please set MONGODB_URI in .env file")

        self.client = MongoClient(MONGODB_URI)
        self.db = self.client.mental_health_rag
        return self.client

    def get_collection(self):
        """Get the MongoDB collection"""
        if self.client is None:
            self.initialize()

        self.collection = self.db.conversations
        print("Using MongoDB collection")
        return self.collection

    def collection_count(self):
        """Return the number of documents in the collection"""
        if self.collection is None:
            self.get_collection()
        return self.collection.count_documents({})

    def add_embeddings(self, ids, embeddings, metadatas):
        """Add embeddings to the MongoDB collection"""
        if self.collection is None:
            self.get_collection()

        # MongoDB needs documents to be added one by one
        documents = []
        for i in range(len(ids)):
            document = {
                "_id": ids[i],
                "embedding": embeddings[i],
                "user_input": metadatas[i]["user_input"],
                "expert_response": metadatas[i]["expert_response"]
            }
            documents.append(document)

        # Insert all documents
        if documents:
            self.collection.insert_many(documents)

    def search_similar(self, query_embedding, top_k=3):
        """Search for similar documents using vector similarity"""
        if self.collection is None:
            self.get_collection()

        # Perform vector search
        # Note: This requires a vector search index to be set up in MongoDB Atlas
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "conversation_vector_index",
                    "queryVector": query_embedding,
                    "path": "embedding",
                    "numCandidates": 100,
                    "limit": top_k
                }
            },
            {
                "$project": {
                    "user_input": 1,
                    "expert_response": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        try:
            results = list(self.collection.aggregate(pipeline))
            return results
        except Exception as e:
            print(f"MongoDB vector search error: {e}")
            return []