from google import genai
import os

# Get the API key from the environment variable
api_key = os.environ.get("GOOGLE_API_KEY")

# Initialize the client with the API key
if api_key:
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents="Explain what a cat is"
        )
        print(response.text)
    except Exception as e:
        print(f"An error occurred during content generation: {e}")
else:
    print("Error: GOOGLE_API_KEY environment variable not set.")