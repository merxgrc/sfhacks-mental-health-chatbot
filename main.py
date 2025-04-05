from google import genai

client = genai.Client(api_key="AIzaSyDX47ZTx5qRx2X7D1X3erKup9tzLS0NLGw")

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain what a cat is"
)
print(response.text)
