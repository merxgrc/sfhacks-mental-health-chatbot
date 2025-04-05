from dotenv import load_dotenv
import google.generativeai as genai
import os
import time
import re

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("No API key found. Please set the GEMINI_API_KEY environment variable (e.g., in a .env file).")

MODEL="gemini-2.0-flash"
genai.configure(api_key=api_key)

NURSE_PROMPT = """
!!! VERY IMPORTANT INSTRUCTION !!!

Your *only* goal when the user mentions a specific mental health struggle
(like anxiety, depression, stress, trauma, OCD, grief, anger)
is to output the handover signal.

If you detect such an issue, you MUST respond with *only* the following format:
HANDOVER:<IssueName>

Replace <IssueName> with a single, lowercase keyword (e.g., anxiety, depression, stress).
DO NOT add any other words or punctuation before or after the signal.

Example:
User: "I feel so depressed."
Your ONLY response: HANDOVER:depression

If the user has *not* mentioned a specific mental health issue, act as Nurse Gemini:
- Friendly, calm, empathetic
- Short, simple sentences
- Make user feel safe
- Gently encourage them to share
- Start the *first* conversation by introducing yourself as Nurse Gemini and asking how they feel today
"""

SPECIALIST_PROMPTS = {
    "anxiety": """
    You are the Anxiety Specialist bot. You provide empathetic, knowledgeable support on anxiety.
    Offer clear, practical tips (breathing, mindfulness). Avoid medical diagnoses.
    Remind the user you are not a licensed professional.
    The user was just transferred for anxiety. Gently acknowledge the transfer and invite them to share more.
    """,
    "depression": """
    You are the Depression Support bot. You provide compassionate, non-judgmental support for depression.
    Encourage self-care, small steps, and seeking professional help if severe.
    The user was just transferred for depression. Acknowledge and invite them to share more.
    """,
    "stress": """
    You are the Stress Management bot. You provide calm, actionable support on stress.
    Suggest healthy coping mechanisms without diagnosing.
    The user was just transferred for stress. Acknowledge and invite them to share more.
    """,
    "default": """
    You are the Wellness Support bot, offering general mental health support.
    You greet the user warmly, encourage them, and remind them you are not a licensed therapist.
    The user was transferred for an unspecified issue. Acknowledge and invite them to share more.
    """
}

def create_chat(chat_id:str, system_prompt: str, model_name: str):

    if chat_id in active_chats:
        return active_chats[chat_id]

    print(f"\n<System: Creating new chat session: {chat_id} (Model: {model_name})>")
    model = genai.GenerativeModel(
        model_name,
        system_instruction=system_prompt
    )
    chat_session = model.start_chat(history=[])
    active_chats[chat_id] = chat_session
    return chat_session

def get_response(chat_session, prompt: str) -> str:
    response = ""
    try:
        response = chat_session.send_message(prompt, stream=True)
        for chunk in response:
            text_part = getattr(chunk, "text", "")
            print(text_part, end="", flush=True)
            full_response += text_part
            time.sleep(0.05)
        print()
    except Exception as e:
        print(f"\n<System: Error during API call: {e}>")
        full_response = "SYSTEM_ERROR"
    return full_response.strip()

active_chats = {}
CURRENT_USER_ID = "user_main"

print(f"Initializing Mental Health Support Chat (Model: {MODEL})...\n")
nurse_chat_id = f"{CURRENT_USER_ID}_nurse"
current_chat_session = create_chat(nurse_chat_id, NURSE_PROMPT, MODEL)
current_chat_id = nurse_chat_id

print("<System: Nurse Gemini starting conversation...>")
_ = get_response(current_chat_session, "Hello")

print("\nEnter text to chat. Type 'exit' to quit.")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        print("Assistant: Take care! Remember that professional help is available if you need it.")
        break
    response_text = get_response(current_chat_session, user_input)
    print(f"<Debug: Raw response from {current_chat_id}: '{response_text}'>")

    if response_text == "SYSTEM_ERROR":
        print("<System: Please try again.>")
        continue

    if current_chat_id == nurse_chat_id and response_text.startswith("HANDOVER:"):
        match = re.match(r"HANDOVER:(\w+)", response_text)
        if match:
            issue = match.group(1).lower()
            print(f"\n<System: Detected issue '{issue}'. Transferring to specialist...>")

            specialist_prompt = SPECIALIST_PROMPTS.get(issue, SPECIALIST_PROMPTS["default"])
            specialist_chat_id = f"{CURRENT_USER_ID}_{issue}"

            current_chat_session = create_chat(specialist_chat_id, specialist_prompt, MODEL_NAME)
            current_chat_id = specialist_chat_id

            print("<System: Now talking to the specialist>\n")

            _ = get_response(current_chat_session, f"I was transferred because I mentioned {issue}.")
        else:
            print(f"<System: Invalid handover format: '{response_text}'. Staying with Nurse.>")

print("\nChat session ended.")