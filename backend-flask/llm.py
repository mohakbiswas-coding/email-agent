# llm.py - Correct Groq LLaMA 3.1 client integration (Dec 2025)

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
TEMPERATURE_DEFAULT = 0.2

client = None

if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("Groq initialized. Using model:", GROQ_MODEL)
    except Exception as e:
        print("ERROR initializing Groq client:", e)
else:
    print("WARNING: GROQ_API_KEY missing. Using stub mode.")


def call_llm(messages, max_tokens=800):
    """
    Wrapper that safely calls Groq ChatCompletion.
    ALWAYS returns a string (never raises exceptions).
    """

    if client is None:
        return (
            "[LLM disabled — missing GROQ_API_KEY]\n"
            "Set your Groq key in backend-flask/.env"
        )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=TEMPERATURE_DEFAULT,
        )

        # FIX: message is an object, not a dict
        return response.choices[0].message.content

    except Exception as e:
        print("Groq LLM ERROR:", repr(e))
        return f"[LLM error] {e}"
