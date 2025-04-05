from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

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
!!! VERY IMPORTANT INSTRUCTION !!!

Your *only* goal when the user mentions a specific mental health struggle
(like anxiety, depression, stress, trauma, OCD, grief, anger)
is to output the handover signal.

If you detect such an issue, you MUST respond with *only* the following format:
HANDOVER:<IssueName>

Replace <IssueName> with a single, lowercase keyword (e.g., anxiety, depression, stress).
DO NOT add any other words or punctuation before or after the signal.

If no issue is mentioned, act as Nurse Gemini:
- Friendly, calm, empathetic
- Short, simple sentences
- Make user feel safe
- Gently encourage them to share
- Start the conversation by introducing yourself and asking how they feel today
"""

SPECIALIST_PROMPTS = {
    "anxiety": """
    You are the Anxiety Specialist bot. Provide kind, calm support.
    Share breathing or grounding tips. Avoid diagnosis.
    Gently acknowledge the transfer and invite the user to talk more.
    """,
    "depression": """
    You are the Depression Specialist bot. Be gentle and encouraging.
    Recommend small self-care steps. Avoid any medical advice.
    """,
    "stress": """
    You are the Stress Support bot. Be calm and helpful.
    Offer ways to manage stress like rest, exercise, and breathing.
    """,
    "default": """
    You are the Wellness Support bot.
    Provide general, empathetic mental health support.
    Remind users you are not a therapist, but you're here to help.
    """
}

# --- Active Session Storage ---
active_chats = {}
CURRENT_USER_ID = "web_user"

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

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Step 1: Talk to Nurse Gemini first
        nurse_chat_id = f"{CURRENT_USER_ID}_nurse"
        current_chat = create_chat(nurse_chat_id, NURSE_PROMPT, MODEL)
        response = current_chat.send_message(user_message).text.strip()

        print(f"[NURSE RESPONSE] {response}")

        # Step 2: Did Nurse Gemini say to hand over?
        if response.startswith("HANDOVER:"):
            issue = re.sub(r"HANDOVER:", "", response).strip().lower()
            specialist_prompt = SPECIALIST_PROMPTS.get(issue, SPECIALIST_PROMPTS["default"])
            specialist_chat_id = f"{CURRENT_USER_ID}_{issue}"
            current_chat = create_chat(specialist_chat_id, specialist_prompt, MODEL)

            # Send intro message to new specialist bot
            handover_intro = f"The user was transferred for {issue}."
            response = current_chat.send_message(handover_intro).text.strip()

        return jsonify({'response': response})

    except Exception as e:
        print(f"<Error> {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
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