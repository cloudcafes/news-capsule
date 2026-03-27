import os
import requests
from google import genai
from google.genai import types

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS
# ==============================================================================
# Best practice: Set these as environment variables in your OS
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==============================================================================
# 2. AI SYSTEM PROMPT
# ==============================================================================
UPSC_PROMPT = """
Role & Objective:
Act as a friendly, expert UPSC mentor dedicated to a 10th-grade CBSE student. Your task is to autonomously search the live web for the Top 10 most important, high-impact news, science & tech events from the last 24-48 hours and transform them into a quick, easy-to-read "Daily Digest" study note.

Strict Rules for the LLM (MANDATORY):
1> Do not include any pre or post commentary but just stick to core answers and OUTPUT FORMAT.
2> Fetch news relevant for future Indian UPSC exam related to subject History (Indian & World), Geography, Polity & Governance, Economy & Agriculture, Environment & Ecology, Science & Technology, International Relations (PSIR), Society & Sociology, Internal Security, Disaster Management, Current Affairs.
3> Zero-Touch: Do not ask for input. Fetch the top news stories yourself. Focus on Science, Environment, Economy, Governance, or International Relations.
4> Keep it Brief & interesting: Because you are covering news topics, keep the notes content for each topic interesting & relevant for a CBSE 10th grade student.
5> Tone: Use 9th/10th-grade vocabulary. Be encouraging and clear.
6> Formatting: Strictly use WhatsApp formatting (*asterisks for bold* and _underscores for italics_).

Output Format:
*TODAY'S TOP 10 UPSC STORIES*

(Repeat this structure for Topic 1, Topic 2 till Topic 10)

*[Insert Headline 1 Here]*
*1> The Facts:* Explain exactly what happened.
*2> Why it Matters:* why this is good, bad, or important for India/the world in terms of Class 10th CBSE student preparing for Civil Services exam in future.
*3> Points for critical thinking:* for Class 10th CBSE student preparing for Civil Services exam in future.
*4> Explanation for Points:* for critical thinking.
*5> Points to carry:* for future civil services exams.
"""

# ==============================================================================
# 3. TELEGRAM SENDER (With Markdown Support)
# ==============================================================================
def send_telegram_message(text: str) -> bool:
    """Sends a formatted message to Telegram, handling the 4096 char limit."""
    if not TELEGRAM_BOT_TOKEN or "YOUR_" in TELEGRAM_BOT_TOKEN:
        print("⚠️ Telegram skipped: Bot token not configured.")
        return False

    max_length = 4000  # Safe buffer below Telegram's 4096 limit
    
    # If the text is short enough, send it all at once
    if len(text) <= max_length:
        return _send_chunk(text)
    
    # If too long, split by double newlines to avoid breaking formatting blocks
    print(f"📤 Message too long ({len(text)} chars), splitting into chunks...")
    chunks = text.split('\n\n')
    current_message = ""
    success = True
    part = 1
    
    for chunk in chunks:
        if len(current_message) + len(chunk) + 2 > max_length:
            if current_message:
                if not _send_chunk(f"*📊 Part {part}:*\n\n{current_message}"):
                    success = False
                part += 1
                current_message = chunk
        else:
            current_message += "\n\n" + chunk if current_message else chunk
            
    # Send the final remaining chunk
    if current_message:
        if not _send_chunk(f"*📊 Part {part}:*\n\n{current_message}"):
            success = False
            
    return success

def _send_chunk(text: str) -> bool:
    """Internal helper to send a single payload to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown" # Enables rendering of *bold* and _italics_
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print("📱 Successfully sent message to Telegram!")
            return True
        else:
            print(f"⚠️ Telegram API error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False

# ==============================================================================
# 4. AI GENERATOR (With Search Grounding)
# ==============================================================================
def generate_digest():
    """Fetches live news via Gemini and formats the digest."""
    if not GEMINI_API_KEY or "YOUR_" in GEMINI_API_KEY:
        print("❌ Gemini API Key is missing.")
        return

    print("🧠 Initiating live web search and generating UPSC digest...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    try:
        # We enable the Google Search tool so the AI can fetch the last 24-48 hours of news
        response = client.models.generate_content(
            model="gemini-2.5-pro", # You can use gemini-3.1-pro-preview if you have access
            contents=UPSC_PROMPT,
            config=types.GenerateContentConfig(
                temperature=0.3, # Low temperature to keep formatting strict and factual
                tools=[{"google_search": {}}] 
            )
        )
        
        digest_content = response.text
        print("✅ Successfully generated the digest!")
        
        print("📲 Forwarding to Telegram...")
        send_telegram_message(digest_content)
        
    except Exception as e:
        print(f"❌ Error during AI generation: {e}")

# ==============================================================================
# 5. MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    generate_digest()