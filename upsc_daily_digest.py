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
Act as a professional equity research analyst specializing in event-driven trading for Indian stock markets. Your task is to autonomously scan the latest live web data and extract the Top 10 most important, high-impact news events that can affect NSE-listed stocks.

Strict Rules for the LLM (MANDATORY):
1> Do not include any pre or post commentary. Only follow OUTPUT FORMAT strictly.
2> Focus ONLY on news that can directly impact stock prices (ignore general news).
3> Prioritize these event types:

* Earnings surprises
* Large orders / contracts
* Mergers, acquisitions, stake sales
* Government policy / regulatory changes
* Capex announcements
* Sector-wide developments (banking, IT, defense, energy, etc.)
* Management changes
* Legal issues / bans / approvals
* Global macro impacting Indian markets (Fed, crude oil, geopolitics)

4> Source news from prominent and reliable financial sources:

* Economic Times
* Moneycontrol
* Business Standard
* LiveMint
* Bloomberg
* Reuters
* NSE / BSE filings

5> Only include news from last 24–48 hours.
6> Avoid duplicate or low-impact news.
7> Each news must be mapped to specific NSE-listed stocks or sectors.
8> Assign an impact rating: VERY HIGH / HIGH / MEDIUM / LOW
9> Keep explanations concise, analytical, and trading-focused.

Tone:
Use professional but simple language. No storytelling. No academic tone.

---

Output Format:

### TOP 10 MARKET-MOVING NEWS (NSE)

(Repeat structure for 10 items)

[Headline]

1> Stock/Sector Impacted: (Name NSE stocks or sector)
2> The News: What exactly happened (fact-based)
3> Why It Matters: Explain market impact clearly
4> Impact Level: VERY HIGH / HIGH / MEDIUM / LOW
5> Expected Direction: BULLISH / BEARISH / NEUTRAL
6> Trade Insight: (Optional short insight like breakout, watch levels, sentiment shift)

"""

# ==============================================================================
# 2. TELEGRAM SENDER (STRICT CHARACTER LIMIT)
# ==============================================================================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Split by lines to avoid breaking words or tags
    lines = text.split('\n')
    chunks = []
    current_chunk = ""

    for line in lines:
        # If adding this line exceeds 3500 chars, start a new chunk
        if len(current_chunk) + len(line) + 1 > 3500:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())

    print(f"📦 Message split into {len(chunks)} parts for Telegram.")

    for i, msg in enumerate(chunks):
        # Add a part indicator if there are multiple parts
        final_text = f"(Part {i+1}/{len(chunks)})\n\n{msg}" if len(chunks) > 1 else msg
        
        payload = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": final_text, 
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=20)
            if response.status_code == 200:
                print(f"✅ Part {i+1} sent successfully.")
            else:
                print(f"⚠️ Telegram API Warning (Part {i+1}): {response.text}")
            
            # Anti-flood delay
            time.sleep(1.5) 
        except Exception as e:
            print(f"❌ Telegram Error: {e}")

# ==============================================================================
# 3. MAIN LOGIC
# ==============================================================================
def generate_digest():
    print("🧠 Generating UPSC digest using Gemini 3.1 Flash Lite...")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    # Gemini 3.1 Flash Lite is optimized for fast, concise summaries
    model_id = "gemini-3.1-flash-lite-preview" 

    try:
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
