import os
from functools import lru_cache
from langchain_groq import ChatGroq

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


@lru_cache(maxsize=None)
def get_llm(temperature: float = 0.2) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
            "and put it in your .env file."
        )
    return ChatGroq(model=DEFAULT_MODEL, api_key=api_key, temperature=temperature)
