import os
import re
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import save_lead, save_message, get_history

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SYSTEM_PROMPT = """You are a friendly, professional customer support assistant for TedRed — an innovative business solutions company.

Your TWO goals:
1. Help visitors by answering questions about TedRed's services warmly and professionally.
2. Naturally collect the visitor's: NAME, EMAIL, and what they are INTERESTED IN.

Rules for lead collection:
- Do NOT ask for all info at once. Collect naturally in conversation.
- First, greet and ask how you can help.
- After understanding their interest, ask for their name.
- After getting their name, ask for their email so the team can follow up.
- Always be helpful — never make them feel interrogated.

When you detect name/email/phone in user messages, respond normally AND include a special JSON tag at the very END of your response like this:
[LEAD_DATA:{"name": "...", "email": "...", "phone": "...", "interest": "..."}]

Only include fields you actually detected. Leave out fields you don't know yet.

About TedRed:
- Innovative Business Solutions company
- Helps businesses grow with technology and smart strategies
- Services include consulting, digital solutions, and business development

Keep responses SHORT (2-4 sentences). Be warm and conversational."""


def extract_lead_data(text: str) -> dict:
    match = re.search(r'\[LEAD_DATA:({.*?})\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            return {}
    return {}


def clean_response(text: str) -> str:
    return re.sub(r'\[LEAD_DATA:.*?\]', '', text, flags=re.DOTALL).strip()


async def chat(session_id: str, user_message: str) -> str:
    await save_message(session_id, "user", user_message)

    history = await get_history(session_id)

    contents = []
    for msg in history[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append(types.Content(
            role=role,
            parts=[types.Part(text=msg["content"])]
        ))

    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=user_message)]
    ))

    print(f"DEBUG: Calling Gemini with {len(contents)} messages...")

    try:
        import asyncio
        loop = asyncio.get_event_loop()

        # Run the blocking Gemini call in a thread with a 15s timeout
        def call_gemini():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=1000,
                    temperature=0.7,
                )
            )

        response = await asyncio.wait_for(
            loop.run_in_executor(None, call_gemini),
            timeout=15.0
        )

        raw_reply = response.text
        print(f"DEBUG: Got reply: {raw_reply[:80]}")

    except asyncio.TimeoutError:
        print("DEBUG: Gemini timed out after 15s")
        error_msg = "I'm taking too long to respond. Please try again."
        await save_message(session_id, "assistant", error_msg)
        return error_msg

    except Exception as e:
        print(f"DEBUG: Gemini error: {type(e).__name__}: {e}")
        error_msg = "Sorry, I'm temporarily unavailable. Please try again."
        await save_message(session_id, "assistant", error_msg)
        return error_msg

    lead_data = extract_lead_data(raw_reply)
    if lead_data:
        await save_lead(
            session_id=session_id,
            name=lead_data.get("name"),
            email=lead_data.get("email"),
            phone=lead_data.get("phone"),
            interest=lead_data.get("interest")
        )

    clean_reply = clean_response(raw_reply)
    await save_message(session_id, "assistant", clean_reply)

    print(f"DEBUG: Sending clean reply: {clean_reply[:80]}")
    return clean_reply