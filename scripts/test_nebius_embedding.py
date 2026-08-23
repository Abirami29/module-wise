"""
Minimal embedding connectivity check + dimension confirmation.
Run: python -m scripts.test_nebius_embedding
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def main():
    client = OpenAI(
        base_url=os.environ["NEBIUS_BASE_URL"],
        api_key=os.environ["NEBIUS_API_KEY"],
    )
    response = client.embeddings.create(
        model=os.environ["NEBIUS_EMBEDDING_MODEL"],
        input="test embedding connectivity",
    )
    embedding = response.data[0].embedding
    print(f"[PASS] Got embedding of length {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print(f"\nUse this number as EMBEDDING_DIM in src/vector/build_index.py: {len(embedding)}")


if __name__ == "__main__":
    main()