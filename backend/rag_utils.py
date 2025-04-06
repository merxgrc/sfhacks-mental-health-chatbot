"""
RAG utilities for mental health chatbot
"""
import os
import uuid
import time
import google.generativeai as genai
from datasets import load_dataset
from dotenv import load_dotenv
from db_provider import get_db_provider

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
# Use embedding-001 model as it has higher quota limits
EMBEDDING_MODEL_ID = "models/embedding-001"

# Initialize the database provider
db_provider = get_db_provider()

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

def populate_vector_database(dataset):
    """Process dataset and store with embeddings"""
    # Initialize the database
    db_provider.initialize()
    collection = db_provider.get_collection()

    # Check if collection already has data
    if db_provider.collection_count() > 0:
        print("Collection already populated, skipping...")
        return collection

    print("Populating vector database...")
    # Process each conversation pair
    ids = []
    embeddings = []
    metadatas = []

    # Only process a subset to start with (reduce quota usage)
    max_samples = 100  # Limit initial dataset size

    # Rate limiting counters
    request_count = 0
    batch_size = 7  # Number of requests before longer pause

    for idx, item in enumerate(dataset['train']):  # Process limited number of samples
        user_input = item['Context']
        expert_response = item['Response']

        # Create combined text for embedding (only user input for efficiency)
        combined_text = user_input

        # Generate a unique ID
        doc_id = str(uuid.uuid4())

        # print(f"Generating embedding {idx+1}/{max_samples}...")

        # Rate limiting - short pause between each request
        if request_count > 0:
            time.sleep(0.5)  # Half second pause between embeddings

        # Additional longer pause after each batch
        if request_count % batch_size == 0 and request_count > 0:
            print(f"Taking a longer pause after {batch_size} requests...")
            time.sleep(3)  # 3 second pause after each batch

        # Generate embedding with rate limiting
        embedding = create_embedding(combined_text)
        request_count += 1

        # Store data for batch addition
        ids.append(doc_id)
        embeddings.append(embedding)
        metadatas.append({
            "user_input": user_input,
            "expert_response": expert_response
        })

        # Add in smaller batches to reduce memory usage
        if len(ids) >= 100 or idx == min(len(dataset['train']) - 1, max_samples - 1):
            db_provider.add_embeddings(ids, embeddings, metadatas)

            # Clear the lists
            ids = []
            embeddings = []
            metadatas = []

            print(f"Processed {idx + 1} documents")

    print(f"Database populated with {db_provider.collection_count()} documents")
    return collection

def retrieve_relevant_conversations(query, top_k=3):
    """Retrieve the most relevant conversations for a user query"""
    # Initialize the database if not already initialized
    db_provider.initialize()
    collection = db_provider.get_collection()

    try:
        # Create embedding for the query (with retry logic)
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                query_embedding = create_embedding(query)
                break
            except Exception as e:
                retry_count += 1
                if "429" in str(e) and retry_count < max_retries:
                    # If rate limited, wait longer before retry
                    print(f"Rate limited, pausing for {retry_count * 5} seconds...")
                    time.sleep(retry_count * 5)
                else:
                    if retry_count >= max_retries:
                        print(f"Failed after {max_retries} retries: {e}")
                        return []
                    raise e

        # Perform vector search using the provider
        return db_provider.search_similar(query_embedding, top_k)

    except Exception as e:
        print(f"Error in retrieve_relevant_conversations: {e}")
        # Return empty results if there's an error
        return []

def augment_prompt_with_rag(user_message, relevant_examples):
    """Augment the prompt with RAG context"""

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

def initialize_rag_database():
    """Initialize the RAG database with the mental health dataset"""
    try:
        dataset = load_and_process_dataset()
        populate_vector_database(dataset)
        print("RAG database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing RAG database: {e}")
        print("Continuing without RAG support...")
        return False

# Legacy functions for compatibility
def get_chroma_client():
    """Compatibility function - now handled by db_provider"""
    # Initialize the DB provider
    db_provider.initialize()
    print("Using abstracted database provider instead of direct ChromaDB access")
    return None

def get_or_create_collection(client):
    """Compatibility function - now handled by db_provider"""
    # Get the collection via the provider
    collection = db_provider.get_collection()
    print("Using abstracted database provider instead of direct ChromaDB access")
    return collection