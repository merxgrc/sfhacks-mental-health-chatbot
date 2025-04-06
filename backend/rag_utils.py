import os
import chromadb
import google.generativeai as genai
from datasets import load_dataset
from dotenv import load_dotenv
import uuid
import time

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
# Use embedding-001 model as it has higher quota limits
EMBEDDING_MODEL_ID = "models/embedding-001"

# ChromaDB setup
def get_chroma_client():
    """Create and return a ChromaDB client with persistent storage"""
    client = chromadb.PersistentClient("./chroma_db")
    return client

def get_or_create_collection(client):
    """Get or create the collection for mental health conversations"""
    # Check if collection exists, if not create it
    try:
        # Try to get the collection first
        collection = client.get_collection("mental_health_conversations")
        print("Using existing collection")
    except:
        print("Creating new collection")
        collection = client.create_collection(
            name="mental_health_conversations",
            metadata={"hnsw:space": "cosine"}
        )
    return collection

def create_embedding(text):
    """Create embedding vector for a text using Gemini embedding model"""
    result = genai.embed_content(
        model=EMBEDDING_MODEL_ID,
        content=text
    )
    return result['embedding']

def load_and_process_dataset():
    """Load the mental health counseling dataset from Hugging Face"""
    # This will download the dataset from HuggingFace
    dataset = load_dataset("Amod/mental_health_counseling_conversations")

    # Return the dataset
    return dataset

def populate_vector_database(dataset, chroma_collection):
    """Process dataset and store in ChromaDB with embeddings"""
    # Check if collection already has data
    if chroma_collection.count() > 0:
        print("Collection already populated, skipping...")
        return

    print("Populating vector database...")
    # Process each conversation pair
    ids = []
    texts = []
    embeddings = []
    metadatas = []

    for idx, item in enumerate(dataset['train']):
        user_input = item['Context']
        expert_response = item['Response']

        # Create combined text for embedding
        # combined_text = f"User: {user_input}\nExpert: {expert_response}"
        # probably don't need the response for comparing user prompt to user_input in dataset
        combined_text = user_input

        # Generate a unique ID
        doc_id = str(uuid.uuid4())

        # Generate embedding
        embedding = create_embedding(combined_text)

        # Store data for batch addition
        ids.append(doc_id)
        texts.append(combined_text)
        embeddings.append(embedding)
        metadatas.append({
            "user_input": user_input,
            "expert_response": expert_response
        })

        # Add in batches of 100 to avoid memory issues
        if len(ids) >= 100 or idx == len(dataset['train']) - 1:
            chroma_collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            # Clear the lists
            ids = []
            texts = []
            embeddings = []
            metadatas = []

            print(f"Processed {idx + 1} documents")

    print(f"Database populated with {chroma_collection.count()} documents")

def retrieve_relevant_conversations(query, chroma_collection, top_k=3):
    """Retrieve the most relevant conversations for a user query"""
    # Create embedding for the query
    query_embedding = create_embedding(query)

    # Perform vector search
    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas"]
    )

    # Format the results to match the structure expected by the rest of the app
    formatted_results = []
    if results and 'metadatas' in results and results['metadatas']:
        for metadata in results['metadatas'][0]:  # First (and only) query results
            formatted_results.append({
                "user_input": metadata["user_input"],
                "expert_response": metadata["expert_response"]
            })

    return formatted_results

def augment_prompt_with_rag(user_message, relevant_examples):
    """Augment the specialist prompt with RAG context"""

    # Format the retrieved examples
    examples_text = ""
    for example in relevant_examples:
        examples_text += f"User: {example['user_input']}\nExpert: {example['expert_response']}\n\n"

    # Create the augmented prompt
    augmented_prompt = f"""
Here are some examples of professional conversations to use as guidance:

{examples_text}

Remember to use these examples as guidance while maintaining your own conversational style.
The user's current message is: {user_message}
"""

    return augmented_prompt