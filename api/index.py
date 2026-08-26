import os
import requests
from fastapi import FastAPI, Request, Response
from google import genai

app = FastAPI()

VERIFY_TOKEN = "mywhatsappbot123"

def get_gemini_client():
    key = os.getenv("GEMINI_API_KEY")
    if key:
        try:
            return genai.Client(api_key=key)
        except Exception as e:
            print(f"Gemini Init Error: {e}")
    return None

@app.get("/")
def home():
    return {"status": "WhatsApp Bot is Live on Vercel!"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, status_code=200)
    return Response(content="Verification failed", status_code=403)

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            from_number = msg.get("from")
            text_body = msg.get("text", {}).get("body", "")

            if text_body:
                client = get_gemini_client()
                if client:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=text_body,
                    )
                    reply_text = response.text
                else:
                    reply_text = "Server Error: GEMINI_API_KEY missing hai."

                send_whatsapp_message(from_number, reply_text)

    except Exception as e:
        print(f"Error processing message: {e}")

    return {"status": "success"}

def send_whatsapp_message(to_number, text):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("PHONE_NUMBER_ID")

    if not token or not phone_id:
        return

    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload, headers=headers)
