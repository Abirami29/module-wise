"""
LangChain-compatible embeddings wrapper pointed at Nebius Token Factory.
"""
import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        base_url=os.environ["NEBIUS_BASE_URL"],
        api_key=os.environ["NEBIUS_API_KEY"],
        model=os.environ["NEBIUS_EMBEDDING_MODEL"],
        check_embedding_ctx_length=False,  # Nebius expects raw text, not pre-tokenized input
    )