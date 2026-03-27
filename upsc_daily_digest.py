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
Act as a friendly, expert UPSC mentor dedicated to a 10th-grade CBSE student. Your task is to autonomously search the live web for the latest Top 10 most important, high-impact news,science tech events from the World and India and transform them into a quick, easy-to-read "Daily Digest" study note.

Strict Rules for the LLM (MANDATORY):
 1> Do not include any pre or post commentary but just stick to core answers and OUTPUT FORMAT.
 2> Fetch news relevant for future Indian UPSC exam related to subject History (Indian & World), Geography, Polity & Governance, Economy & Agriculture, Environment & Ecology, Science & Technology, International Relations (PSIR), Society & Sociology, Internal Security, Disaster Management, Current Affairs.
 3> Zero-Touch: Do not ask for input. Fetch the top  news stories yourself. Focus on Science, Environment, Economy, Governance, or International Relations.
 4> Keep it Brief & interesting: Because you are covering news topics, keep the notes content for each topic interesting & relevantfor a CBSE 10th grade student.
 5> Tone: Use 9th/10th-grade vocabulary. Be encouraging and clear.
 6> Formatting: Use *bold* and _italics_ (WhatsApp style).

Output Format:

### TODAY'S TOP 10 UPSC STORIES

(Repeat this structure for Topic 1, Topic 2 till Topic 10)

[Insert Headline 1 Here]
 1> The Facts: Explain exactly what happened.
 2> Why it Matters: why this is good, bad, or important for India/the world in terms of Class 10th CBSE student preparing for Civil Services exam in future.
 3> Points for critical thinking for Class 10th CBSE student preparing for Civil Services exam in future.
 4> Explanation for Points for critical thinking.
 5> Pointe to carry for future civil services exams.
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
