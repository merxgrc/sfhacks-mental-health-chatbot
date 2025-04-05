from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

# Load the API key
api_key = os.environ.get("GOOGLE_API_KEY")

# Configure Gemini client
if api_key:
    # genai.configure(api_key=api_key)
    # model = genai.GenerativeModel('gemini-2.0-flash')
    client = genai.Client(api_key=api_key)
    model = client.chats.create(model="gemini-2.0-flash")
else:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    model = None

@app.route('/')
def index():
    return "Welcome to the Mental Health Chatbot Backend!"

@app.route('/api/chat', methods=['POST'])
def chat():
    if model is None:
        return jsonify({'error': 'Gemini API key not configured.'}), 500

    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # response = model.generate_content(user_message)
        # response = model.send_message_stream(user_message)
        response = model.send_message(user_message)

        # response = client.models.generate_content(
        #     model="gemini-2.0-flash",
        #     config=types.GenerateContentConfig(
        #         system_instruction="You are a cat. Your name is Neko."),
        #     contents=user_message
        # )

        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
