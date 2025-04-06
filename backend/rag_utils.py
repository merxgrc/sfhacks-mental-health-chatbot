import os
import uuid
import math
import time
import chromadb
import google.generativeai as genai
from datasets import load_dataset
from dotenv import load_dotenv
import tiktoken  # Added for token counting

# Load environment variables
load_dotenv()
# Set up the Google Generative AI API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

EMBEDDING_MODEL_ID = "models/embedding-001"  # or "models/text-embedding-001" for lower quota limits
MAX_INPUT_TOKENS = 2048
EMBEDDING_BATCH_SIZE = 100 
CHROMADB_ADD_BATCH_SIZE = EMBEDDING_BATCH_SIZE
COLLECTION_NAME = ""

# --- Helper: Token counting using tiktoken ---
def count_tokens(text, model_name):
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    class CountResult:
        def __init__(self, total_tokens):
            self.total_tokens = total_tokens
    return CountResult(len(tokens))

def truncate_text_by_tokens(text, model_name, max_tokens):
    """
    Counts tokens using the provided model name and truncates text if it exceeds max_tokens.
    Returns a tuple: (processed_text, original_token_count, final_token_count)
    Returns (None, original_token_count, -1) on token counting error.
    """
    if not text:
        return "", 0, 0

    original_token_count = -1
    final_token_count = -1

    try:
        # 1. Count initial tokens
        count_result = count_tokens(text, model_name)
        original_token_count = count_result.total_tokens
        final_token_count = original_token_count  # Assume no truncation initially

        # 2. Check if truncation is needed
        if original_token_count <= max_tokens:
            return text, original_token_count, final_token_count  # No truncation needed

        print(f"  - Truncation needed: Original tokens {original_token_count} > {max_tokens}")

        # 3. Estimate character cutoff
        proportion = (max_tokens * 0.95) / original_token_count
        estimated_char_cutoff = int(len(text) * proportion)
        processed_text = text[:estimated_char_cutoff]

        # 4. Iteratively refine truncation
        attempts = 0
        max_attempts = 10  # Prevent infinite loops

        while attempts < max_attempts:
            attempts += 1
            current_token_count = count_tokens(processed_text, model_name).total_tokens
            final_token_count = current_token_count  # Update final count

            if current_token_count <= max_tokens:
                print(f"  - Truncation successful: Final tokens {current_token_count} (Attempt {attempts})")
                return processed_text, original_token_count, final_token_count  # Success

            print(f"  - Truncation refinement needed: Current tokens {current_token_count} (Attempt {attempts})")

            # Trim by a percentage of remaining characters
            chars_to_remove = max(10, int(len(processed_text) * 0.05))  # Remove at least 10 chars or 5%
            if len(processed_text) <= chars_to_remove:
                print(f"  - Warning: Text too short to truncate further ({len(processed_text)} chars).")
                return processed_text, original_token_count, final_token_count

            processed_text = processed_text[:-chars_to_remove]

        print(f"Error: Failed to truncate text below {max_tokens} tokens after {max_attempts} attempts.")
        print(f"Original tokens: {original_token_count}, Last attempt tokens: {final_token_count}")
        return None, original_token_count, final_token_count  # Indicate failure
    except Exception as e:
        print(f" Error during token counting/truncation: {e}")
        return None, original_token_count, -1  # Indicate error state

def get_chroma_client():
    """Create and return a ChromaDB client with persistent storage"""
    client = chromadb.PersistentClient("./chroma_db")
    return client

def get_or_create_collection(client):
    global COLLECTION_NAME
    """Get or create the collection for mental health conversations"""
    try:
        collection = client.get_collection("mental_health_conversations")
        print(f"Using existing collection {collection.name}")
    except Exception:
        print("Creating new collection")
        collection = client.create_collection(
            name="mental_health_conversations",
            metadata={
                "hnsw:space": "cosine",
                "embedding_model": EMBEDDING_MODEL_ID,
            }
        )
        COLLECTION_NAME = collection.name
        print(f"Created collection: {collection.name} with metadata {collection.metadata}")
    return collection

def create_embeddings_batch(texts):
    """Create embedding vector for a text using the Gemini embedding model"""
    if not texts:
        return None
    try:
        result = genai.embed_content(EMBEDDING_MODEL_ID, texts)
        embeddings = result["embedding"]
        return embeddings
    except Exception as e:
        print(f"Error generating embeddings batch: {e}")
        if "token limit" in str(e).lower():
            print("Potential token limit error detected in embedding request despite pre-truncation attempts.")
        print(f"Failed to embed batch of size {len(texts)}. Returning empty embeddings for this batch.")
        return [None] * len(texts)


def load_and_process_dataset():
    """Load the mental health counseling dataset from Hugging Face"""
    dataset = load_dataset("Amod/mental_health_counseling_conversations")
    print(f"Dataset loaded. Number of conversations: {len(dataset['train'])}")
    return dataset

def populate_vector_database(dataset, chroma_collection):
    """Process dataset and store in ChromaDB with embeddings"""
    if chroma_collection.count() > 0:
        print(f"Collection already contains {chroma_collection.count()} documents (>= dataset size {len(dataset['train'])}). Skipping population.")
        return

    print(f"\nPopulating vector database with model '{EMBEDDING_MODEL_ID}'...")
    ids_batch = []
    texts_to_embed_batch = []
    metadatas_batch = []

    processed_count = 0
    added_count = 0
    skipped_count = 0
    truncated_count = 0
    start_time = time.time()

    target_count = len(dataset['train'])
    num_batches = math.ceil(target_count / EMBEDDING_BATCH_SIZE)

    for idx, item in enumerate(dataset['train']):
        user_input = item['Context']
        expert_response = item['Response']
        doc_id = str(uuid.uuid4())

        processed_text, original_tokens, final_tokens = truncate_text_by_tokens(
            user_input, EMBEDDING_MODEL_ID, MAX_INPUT_TOKENS
        )

        if processed_text is None:
            print(f"Skipping document index {idx} due to tokenization/truncation error.")
            skipped_count += 1
            continue

        was_truncated = original_tokens > MAX_INPUT_TOKENS
        if was_truncated:
            truncated_count += 1

        ids_batch.append(doc_id)
        texts_to_embed_batch.append(processed_text)
        metadatas_batch.append({
            "user_input_original": user_input,
            "expert_response": expert_response,
            "original_index": idx,
            "tokens_original": original_tokens,
            "tokens_final": final_tokens,
            "was_truncated": was_truncated
        })

        if len(ids_batch) >= EMBEDDING_BATCH_SIZE or idx == target_count - 1:
            current_batch_num = (processed_count // EMBEDDING_BATCH_SIZE) + 1
            print(f"\nProcessing Embedding Batch {current_batch_num}/{num_batches} (size {len(ids_batch)})...")

            embeddings_batch = create_embeddings_batch(texts_to_embed_batch)
            valid_items = []
            for i, emb in enumerate(embeddings_batch):
                if emb is not None:
                    valid_items.append((ids_batch[i], emb, texts_to_embed_batch[i], metadatas_batch[i]))
                else:
                    print(f"Warning: Failed to generate embedding for item with original index {metadatas_batch[i]['original_index']} (ID: {ids_batch[i]}) in this batch.")
                    skipped_count += 1

            processed_count += len(ids_batch)

            if not valid_items:
                print("Skipping ChromaDB add for this batch as no valid embeddings were generated.")
            else:
                final_ids = [item[0] for item in valid_items]
                final_embeddings = [item[1] for item in valid_items]
                final_documents = [item[2] for item in valid_items]
                final_metadatas = [item[3] for item in valid_items]

                print(f"  Adding {len(final_ids)} valid items to ChromaDB...")
                add_start_time = time.time()
                try:
                    chroma_collection.add(
                        ids=final_ids,
                        embeddings=final_embeddings,
                        documents=final_documents,
                        metadatas=final_metadatas
                    )
                    added_count += len(final_ids)
                    add_end_time = time.time()
                    print(f"  Batch added in {add_end_time - add_start_time:.2f} seconds.")
                except Exception as e:
                    print(f"  ERROR adding batch to ChromaDB: {e}")
                    skipped_count += len(final_ids)
            # Clear lists for next batch
            ids_batch = []
            texts_to_embed_batch = []
            metadatas_batch = []

            # Print progress
            elapsed_time = time.time() - start_time
            if added_count > 0:
                time_per_doc = elapsed_time / added_count
                estimated_total_time = time_per_doc * (target_count - skipped_count)
                estimated_remaining = estimated_total_time - elapsed_time
                print(f"  Progress: {processed_count}/{target_count} attempted | {added_count} added | {skipped_count} skipped | {truncated_count} truncated")
                print(f"  Elapsed: {elapsed_time:.2f}s | Est. Remaining: {max(0, estimated_remaining):.2f}s")

    # --- Final Summary ---
    end_time = time.time()
    final_db_count = chroma_collection.count()
    print("-" * 30)
    print(f"Database population complete.")
    print(f"Attempted processing {processed_count} items from dataset.")
    print(f"Successfully added {added_count} documents to ChromaDB.")
    print(f"Skipped {skipped_count} documents (due to errors or failed embeddings).")
    print(f"Truncated {truncated_count} documents due to token limits.")
    print(f"Total time: {end_time - start_time:.2f} seconds.")
    if added_count > 0:
        print(f"Average time per successfully added document: {(end_time - start_time) / added_count:.4f} seconds.")
    print(f"Final documents in collection '{chroma_collection.name}': {final_db_count}")

def retrieve_relevant_conversations(query, chroma_collection, top_k=3):
    """Retrieve the most relevant conversations for a user query"""
    # Create embedding for the query (wrap query in a list)
    query_embeddings = create_embeddings_batch([query])
    if not query_embeddings or query_embeddings[0] is None:
        print("Failed to generate embedding for the query.")
        return []

    query_embedding = query_embeddings[0]

    # Perform vector search
    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas"]
    )

    formatted_results = []
    if results and 'metadatas' in results and results['metadatas']:
        for metadata in results['metadatas'][0]:
            formatted_results.append({
                "user_input": metadata.get("user_input_original", ""),
                "expert_response": metadata.get("expert_response", "")
            })

    return formatted_results

def augment_prompt_with_rag(user_message, relevant_examples):
    """Augment the specialist prompt with RAG context"""
    examples_text = ""
    for example in relevant_examples:
        examples_text += f"User: {example['user_input']}\nExpert: {example['expert_response']}\n\n"

    augmented_prompt = f"""
Here are some examples of professional conversations to use as guidance:

{examples_text}

Remember to use these examples as guidance while maintaining your own conversational style.
Talk to them as they were in the same room with you, and make sure to keep the conversation flowing naturally.
The user's current message is: {user_message}
"""
    return augmented_prompt
