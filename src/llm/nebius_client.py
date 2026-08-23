"""
Thin wrapper for getting a LangChain-compatible chat model pointed at
Nebius Token Factory's OpenAI-compatible endpoint.
"""
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def get_llm(temperature: float = 0.0, max_tokens: int = 1024, reasoning_effort: str = "low", frequency_penalty: float = 0.4) -> ChatOpenAI:
    return ChatOpenAI(
        base_url=os.environ["NEBIUS_BASE_URL"],
        api_key=os.environ["NEBIUS_API_KEY"],
        model=os.environ["NEBIUS_MODEL"],
        temperature=temperature,
        max_tokens=max_tokens,
        frequency_penalty=frequency_penalty,
        extra_body={"reasoning_effort": reasoning_effort},
    )

