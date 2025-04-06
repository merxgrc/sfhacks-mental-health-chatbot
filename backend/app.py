from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from rag_utils import (
    initialize_rag_database,
    retrieve_relevant_conversations,
    augment_prompt_with_rag
)

# --- Load Environment Variables ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("No API key found. Please set the GOOGLE_API_KEY in a .env file.")

# --- Configure Gemini ---
genai.configure(api_key=api_key)
MODEL = "gemini-2.0-flash"

# --- Flask Setup ---
app = Flask(__name__)
CORS(app)

# --- Prompts ---
NURSE_PROMPT = """
!!! IMPORTANT INSTRUCTION !!!
Begin by introducing yourself as Nurse Gemini and ask how they feel today.

If the user mentions a specific mental health struggle (e.g., anxiety, depression, stress, trauma, OCD, grief, anger), immediately respond with only:
HANDOVER:<issue>
Replace <issue> with a single, lowercase keyword (like anxiety). Do not add any extra text.
If the user's input is vague or simply affirmative (like "Yes"), do NOT output the handover signal.
Instead, provide empathetic support and ask them to share more about their feelings.

If no specific struggle is mentioned, act as Nurse Gemini:
- Be friendly, calm, and empathetic.
- Use very short responses (1-2 sentences).
- Make the user feel safe.
- Gently encourage them to share.
- You don't have to remind them you are not a licensed professional or your name after saying it once.
"""

SPECIALIST_PROMPTS = {
    "anxiety": """
    !!! IMPORTANT INSTRUCTION !!!
    You are the Anxiety Management bot. Provide empathetic, knowledgeable support on anxiety.
    Keep your responses short and simple (2-3 sentences), but be descriptive enough to be helpful.
    Offer clear, practical tips (like breathing exercises or mindfulness techniques).
    Try to encourage the user to share more about their issues and feelings.
    Avoid medical diagnoses or jargon.
    """,
    "depression": """
    !!! IMPORTANT INSTRUCTION !!!
    You are the Depression Management bot. Provide compassionate, non-judgmental support for depression.
    Keep your responses short and simple (2-3 sentences), but be descriptive enough to be helpful.
    Encourage self-care, small steps, and seeking professional help if symptoms are severe.
    Try to encourage the user to share more about their issues and feelings.
    Avoid medical diagnoses or jargon.
    """,
    "stress": """
    !!! IMPORTANT INSTRUCTION !!!
    You are the Stress Management bot. Provide calm, actionable support on stress.
    Keep your responses short and simple (2-3 sentences), but be descriptive enough to be helpful.
    Suggest healthy coping mechanisms (like exercise or mindfulness) without diagnosing.
    Try to encourage the user to share more about their issues and feelings.
    Avoid medical diagnoses or jargon.
    """,
    "default": """
    !!! IMPORTANT INSTRUCTION !!!
    You are the Wellness Support bot, offering general mental health support.
    Greet the user warmly, encourage them, and remind them you are not a licensed therapist.
    Keep your responses short and simple (2-3 sentences), but be descriptive enough to be helpful.
    Try to encourage the user to share more about their issues and feelings.
    If the user was transferred for an unspecified issue, acknowledge it and invite them to share more.
    """
}


# --- Active Session Storage ---
active_chats = {}
CURRENT_USER_ID = "web_user"
current_chat_id = None

def create_chat(chat_id: str, system_prompt: str, model_name: str):
    if chat_id in active_chats:
        return active_chats[chat_id]

    print(f"<System: Creating chat session {chat_id}>")
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt
    )
    chat = model.start_chat(history=[])
    active_chats[chat_id] = chat
    return chat

@app.route("/")
def index():
    return "✅ Mental Health Chatbot backend is running!"

@app.route("/api/init", methods=["GET"])
def init_chat():
    global active_chats, current_chat_id, last_introduction
    nurse_chat_id = f"{CURRENT_USER_ID}_nurse"
    try:
        # Remove any existing nurse session so a fresh introduction is generated.
        active_chats.pop(nurse_chat_id, None)
        current_chat_id = nurse_chat_id
        nurse_chat = create_chat(nurse_chat_id, NURSE_PROMPT, MODEL)

        intro_message = nurse_chat.send_message("Introduce yourself").text.strip()
        print(f"[NURSE INTRODUCTION] {intro_message}")
        last_introduction = intro_message  # Cache the new introduction
        return jsonify({"intro": intro_message})
    except Exception as e:
        print(f"Error initializing chat: {e}")
        # Always fallback to the last introduction if available
        fallback = last_introduction if last_introduction is not None else "Nurse Gemini is ready."
        return jsonify({"intro": fallback})


@app.route("/api/chat", methods=["POST"])
def chat():
    global active_chats, current_chat_id

    data = request.get_json()
    user_message = data.get("message", "").strip()
    print(f"<User Message> {user_message}")

    try:
        if not active_chats:
            # Step 1: Talk to Nurse Gemini first
            nurse_chat_id = f"{CURRENT_USER_ID}_nurse"
            current_chat_id = nurse_chat_id
            current_chat = create_chat(nurse_chat_id, NURSE_PROMPT, MODEL)

        current_chat = active_chats[current_chat_id]

        augmented_input = user_message

        # Step 2.1: RAG Enhancement - Get relevant conversations
        try:
            relevant_examples = retrieve_relevant_conversations(user_message)
            print("This happens")
            if relevant_examples:
                # Augment prompt with relevant examples
                augmented_prompt = augment_prompt_with_rag(
                    user_message,
                    relevant_examples
                )
                print(augmented_prompt) 
                # Use the augmented prompt instead
                augmented_input = augmented_prompt
            # else:
            #     print("Response without RAG")
            #     # Fall back to original prompt if no relevant examples
            #     response = current_chat.send_message(user_message).text.strip()
        except Exception as rag_error:
            print(f"RAG enhancement failed: {rag_error}. Using default prompt.")
            # response = current_chat.send_message(user_message).text.strip()

        response = current_chat.send_message(augmented_input).text.strip()
        print(f"[{current_chat_id.upper()} RESPONSE] {response}")

        # Step 2: Did Nurse Gemini say to hand over?
        if current_chat_id.endswith("_nurse") and response.startswith("HANDOVER:"):
            issue = re.sub(r"HANDOVER:", "", response).strip().lower()

            specialist_prompt = SPECIALIST_PROMPTS.get(issue, SPECIALIST_PROMPTS["default"])
            specialist_chat_id = f"{CURRENT_USER_ID}_{issue}"

            current_chat = create_chat(specialist_chat_id, specialist_prompt, MODEL)
            current_chat_id = specialist_chat_id

            # Send intro message to new specialist bot
            # handover_intro = f"The user was transferred for {issue}."
            # response = current_chat.send_message(handover_intro).text.strip()
            response = current_chat.send_message(augmented_input).text.strip()

        return jsonify({'response': response})

    except Exception as e:
        print(f"<Error> {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


if __name__ == '__main__':
    # Initialize RAG database before starting the app
    initialize_rag_database()
    app.run(debug=True)

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os
# import re
# from google import genai
# from google.genai import types
# import google.generativeai as genai
# from dotenv import load_dotenv

# load_dotenv()

# # --- Flask ---
# app = Flask(__name__)
# CORS(app)

# # Load the API key
# api_key = os.environ.get("GOOGLE_API_KEY")

# # Configure Gemini client
# # if api_key:
# #     # genai.configure(api_key=api_key)
# #     # model = genai.GenerativeModel('gemini-2.0-flash')
# #     client = genai.Client(api_key=api_key)
# #     model = client.chats.create(model="gemini-2.0-flash")
# # else:
# #     print("Error: GOOGLE_API_KEY environment variable not set.")
# #     model = None

# # if not api_key:
# #     raise ValueError("GOOGLE_API_KEY did not load correctly")
# # genai.configure(api_key=api_key)
# # model = genai.GenerativeModel('gemini-2.0-flash')

# api_key = os.getenv("GOOGLE_API_KEY")
# if not api_key:
#     raise ValueError("No API key found. Please set the GEMINI_API_KEY environment variable (e.g., in a .env file).")

# MODEL="gemini-2.0-flash"
# genai.configure(api_key=api_key)


# # --- Prompts ---
# NURSE_PROMPT = """
# !!! VERY IMPORTANT INSTRUCTION !!!

# Your *only* goal when the user mentions a specific mental health struggle
# (like anxiety, depression, stress, trauma, OCD, grief, anger)
# is to output the handover signal.

# If you detect such an issue, you MUST respond with *only* the following format:
# HANDOVER:<IssueName>

# Replace <IssueName> with a single, lowercase keyword (e.g., anxiety, depression, stress).
# DO NOT add any other words or punctuation before or after the signal.

# Example:
# User: "I feel so depressed."
# Your ONLY response: HANDOVER:depression

# If the user has *not* mentioned a specific mental health issue, act as Nurse Gemini:
# - Friendly, calm, empathetic
# - Short, simple sentences
# - Make user feel safe
# - Gently encourage them to share
# - Start the *first* conversation by introducing yourself as Nurse Gemini and asking how they feel today
# """

# SPECIALIST_PROMPTS = {
#     "anxiety": """
#     You are the Anxiety Specialist bot. You provide empathetic, knowledgeable support on anxiety.
#     Offer clear, practical tips (breathing, mindfulness). Avoid medical diagnoses.
#     Remind the user you are not a licensed professional.
#     The user was just transferred for anxiety. Gently acknowledge the transfer and invite them to share more.
#     """,
#     "depression": """
#     You are the Depression Support bot. You provide compassionate, non-judgmental support for depression.
#     Encourage self-care, small steps, and seeking professional help if severe.
#     The user was just transferred for depression. Acknowledge and invite them to share more.
#     """,
#     "stress": """
#     You are the Stress Management bot. You provide calm, actionable support on stress.
#     Suggest healthy coping mechanisms without diagnosing.
#     The user was just transferred for stress. Acknowledge and invite them to share more.
#     """,
#     "default": """
#     You are the Wellness Support bot, offering general mental health support.
#     You greet the user warmly, encourage them, and remind them you are not a licensed therapist.
#     The user was transferred for an unspecified issue. Acknowledge and invite them to share more.
#     """
# }

#  #--- Active Chats ---
# active_chats = {}
# CURRENT_USER_ID = "user_main"  # In production, you’d use auth/user ID

# # def get_chat_session(chat_id, prompt):
# #     if chat_id not in active_chats:
# #         print(f"<Creating session: {chat_id}>")
# #         chat = model.start_chat(history=[])
# #         chat.send_message(prompt)  # send the "system" instruction as first message
# #         active_chats[chat_id] = chat
# #     return active_chats[chat_id]
# def create_chat(chat_id:str, system_prompt: str, model_name: str):

#     if chat_id in active_chats:
#         return active_chats[chat_id]

#     print(f"\n<System: Creating new chat session: {chat_id} (Model: {model_name})>")
#     model = genai.GenerativeModel(
#         model_name,
#         system_instruction=system_prompt
#     )
#     chat_session = model.start_chat(history=[])
#     active_chats[chat_id] = chat_session
#     return chat_session

# @app.route('/')
# def index():
#     return "Mental Health Chatbot API is running!"

# # @app.route('/api/chat', methods=['POST'])
# # def chat():
# #     if model is None:
# #         return jsonify({'error': 'Gemini API key not configured.'}), 500

# #     data = request.get_json()
# #     user_message = data.get('message')

# #     if not user_message:
# #         return jsonify({'error': 'No message provided'}), 400

# #     try:
# #         # response = model.generate_content(user_message)
# #         # response = model.send_message_stream(user_message)
# #         #response = model.send_message(user_message)

# #         response = client.models.generate_content(
# #              model="gemini-2.0-flash",
# #              config=types.GenerateContentConfig(
# #                  system_instruction="You are a cat. Your name is Neko."),
# #              contents=user_message
# #          )

# #         return jsonify({'response': response.text})

# #     except Exception as e:
# #         return jsonify({'error': f'Error generating response: {str(e)}'}), 500

# # if __name__ == '__main__':
# #     app.run(debug=True)

# @app.route("/api/chat", methods=["POST"])
# def get_response():
#     data = request.get_json()
#     user_msg = data.get("message", "").strip()
#     if not user_msg:
#         return jsonify({'error': 'No message provided'}), 400


#     response= chat_session.send_message(prompt)
#     return jsonify({'response'})


#     # try:
#     #     # Step 1: Start with the nurse if this is the first message
#     #     nurse_chat_id = f"{CURRENT_USER_ID}_nurse"
#     #     current_chat = get_chat_session(nurse_chat_id, NURSE_PROMPT)

#     #     # Step 2: Get response from Nurse Gemini
#     #     nurse_response = current_chat.send_message(user_msg).text.strip()
#     #     print(f"[NURSE RESPONSE] {nurse_response}")

#     #     if nurse_response.startswith("HANDOVER:"):
#     #         issue = re.sub(r"HANDOVER:", "", nurse_response).strip().lower()
#     #         prompt = SPECIALIST_PROMPTS.get(issue, SPECIALIST_PROMPTS["default"])
#     #         specialist_chat_id = f"{CURRENT_USER_ID}_{issue}"

#     #         current_chat = get_chat_session(specialist_chat_id, prompt)
#     #         specialist_response = current_chat.send_message(
#     #             f"The user was transferred for {issue}."
#     #         ).text.strip()

#     #         return jsonify({'response': specialist_response})

#     #     return jsonify({'response': nurse_response})


# if __name__ == '__main__':
#     app.run(debug=True)