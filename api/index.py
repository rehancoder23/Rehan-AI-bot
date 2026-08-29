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

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return Response(content=challenge, media_type="text/plain", status_code=200)
        else:
            return Response(content="Verification token mismatch", status_code=403)
    return Response(content="Missing parameters", status_code=400)

@app.post("/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        print("Incoming Webhook Data:", data)
        
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            from_number = msg.get("from")
            text_body = msg.get("text", {}).get("body", "")
            print(f"Received message from {from_number}: {text_body}")

            if text_body:
                client = get_gemini_client()
                if client:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=text_body,
                    )
                    reply_text = response.text
                    print(f"Gemini Reply: {reply_text}")
                else:
                    reply_text = "Server Error: GEMINI_API_KEY missing hai."
                    print("Gemini API Key missing!")

                send_whatsapp_message(from_number, reply_text)

    except Exception as e:
        print(f"CRITICAL ERROR processing message: {e}")

    return {"status": "success"}

def send_whatsapp_message(to_number, text):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("PHONE_NUMBER_ID")

    if not token or not phone_id:
        print("WhatsApp Token or Phone ID missing in environment variables!")
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
    res = requests.post(url, json=payload, headers=headers)
    print(f"WhatsApp Send Response: {res.status_code}, {res.text}")
