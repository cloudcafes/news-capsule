import os
import requests
import time
from google import genai
from google.genai import types

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

UPSC_PROMPT = """
Role & Objective:
Act as a friendly, expert UPSC mentor for a 10th-grade CBSE student. 
Provide a "Daily Digest" of the Top 10 high-impact news stories from the last 24-48 hours.
Focus: Science, Environment, Economy, Governance, or International Relations.

Rules:
1> Stick ONLY to the format. No intro/outro.
2> Use 10th-grade vocabulary. Be encouraging.
3> Formatting: Use *bold* and _italics_ (WhatsApp style).

Output Format:
*TODAY'S TOP 10 UPSC STORIES*

*[Headline]*
*1> The Facts:* [What happened]
*2> Why it Matters:* [Importance for India/World/CBSE 10th student]
*3> Points for critical thinking:* [UPSC perspective]
*4> Explanation for Points:* [Brief detail]
*5> Points to carry:* [Future exam takeaway]
"""

# ==============================================================================
# 2. TELEGRAM SENDER
# ==============================================================================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # Split message if it's too long for Telegram (Limit is 4096)
    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    else:
        chunks = [text]

    for chunk in chunks:
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code != 200:
                print(f"⚠️ Telegram API Warning: {response.text}")
        except Exception as e:
            print(f"❌ Telegram Error: {e}")

# ==============================================================================
# 3. MAIN LOGIC
# ==============================================================================
def generate_digest():
    print("🧠 Generating UPSC digest using Gemini 2.0 Flash...")
    
    # Initialize Client
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Using the current stable model ID
    model_id = "gemini-3.1-flash-lite-preview" 

    try:
        # GOOGLE SEARCH TOOL REMOVED HERE
        response = client.models.generate_content(
            model=model_id,
            contents=UPSC_PROMPT,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )
        
        if response.text:
            print("✅ Digest Generated. Sending to Telegram...")
            send_telegram_message(response.text)
        else:
            print("⚠️ Empty response from AI.")

    except Exception as e:
        print(f"❌ Error during AI generation: {e}")

if __name__ == "__main__":
    if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("❌ Missing API Keys in Environment Variables!")
    else:
        generate_digest()
