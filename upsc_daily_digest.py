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

PROMPT = """
Role & Objective:
Act as a professional equity research analyst specializing in event-driven trading for Indian stock markets. Extract Top 10 high-impact news affecting NSE stocks.

Strict Rules:
1. No commentary, only output.
2. Focus only on market-moving news.
3. You MUST use Telegram HTML formatting ONLY. 
   - Use <b>text</b> for bold text and headings.
   - Use <i>text</i> for italics.
   - DO NOT use markdown like **bold** or *italic*.
   - DO NOT use unsupported HTML tags like <br> or <h1>. Use standard newline characters for line breaks.

Output Format (STRICT HTML):
<b>TOP MARKET-MOVING NEWS (NSE)</b>

(Repeat for 10 items)
<b>[Headline]</b>
• <b>Stock/Sector:</b> Name
• <b>The News:</b> Explanation
• <b>Why It Matters:</b> Impact
• <b>Impact:</b> VERY HIGH / HIGH / MEDIUM / LOW
• <b>Direction:</b> BULLISH / BEARISH / NEUTRAL
• <i>Trade Insight:</i> Optional
"""

# ==============================================================================
# 2. TELEGRAM SENDER (SAFE SPLIT + HTML MODE)
# ==============================================================================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    MAX_LEN = 3800  # safe margin under 4096 to account for HTML tags
    lines = text.split("\n")

    chunks = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > MAX_LEN:
            chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"

    if current:
        chunks.append(current.strip())

    print(f"📦 Sending {len(chunks)} message part(s)...")

    for i, msg in enumerate(chunks):
        # Adding bold formatting to the chunk indicator
        final_text = (
            f"<b>Part {i+1}/{len(chunks)}</b>\n\n{msg}"
            if len(chunks) > 1 else msg
        )

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": final_text,
            "parse_mode": "HTML" # Telling Telegram to read the <b> and <i> tags
        }

        try:
            res = requests.post(url, json=payload, timeout=20)
            if res.status_code == 200:
                print(f"✅ Part {i+1} sent")
            else:
                print(f"⚠️ Telegram Error: {res.text}")
            time.sleep(1.2)
        except Exception as e:
            print(f"❌ Telegram Exception: {e}")

# ==============================================================================
# 3. MAIN LOGIC
# ==============================================================================
def generate_digest():
    print("🧠 Generating market news...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Using Gemini 2.5 Flash for the optimal balance of speed and instruction following
    model_id = "gemini-2.5-flash"

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=PROMPT,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )

        if response.text:
            print("✅ Generated successfully")
            send_telegram_message(response.text)
        else:
            print("⚠️ Empty response")

    except Exception as e:
        print(f"❌ AI Error: {e}")

# ==============================================================================
# 4. ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("❌ Missing environment variables!")
    else:
        generate_digest()
