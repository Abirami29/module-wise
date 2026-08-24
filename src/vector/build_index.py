"""
Story 5.1: builds the Qdrant vector store.

Chunking strategy: whole-document (one chunk per source). Module READMEs
are short (150-300 tokens) and self-contained by convention, so splitting
would fragment rather than improve retrieval - chunk size is matched to
actual document size rather than applying a default splitter.

Sources embedded, each tagged with a "source_type" in metadata for provenance:
  - module READMEs + their inline comments (source_type="module_doc")
  - internal docs, e.g. decision records (source_type="internal_doc")

Qdrant chosen over Pinecone/Chroma: open-source, self-hostable (no forced
vendor account for anyone running this project), free managed tier for
this POC. See project doc for full reasoning.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from src.parsing.terraform.comment_extractor import extract_comments_for_module
from src.vector.embeddings_client import get_embeddings

load_dotenv()

MODULES_DIR = Path("data/github-repos/infra-modules/modules")
INTERNAL_DOCS_DIR = Path("data/internal-docs")
COLLECTION_NAME = "module_wise_docs"
EMBEDDING_DIM = 4096  # Qwen3-Embedding-8B output dimension


def build_module_documents() -> list[Document]:
    """One Document per module: README text + inline comments appended."""
    docs = []
    for module_dir in sorted(p for p in MODULES_DIR.iterdir() if p.is_dir()):
        module_name = module_dir.name
        readme_path = module_dir / "README.md"
        readme_text = readme_path.read_text() if readme_path.exists() else ""

        comments = extract_comments_for_module(module_dir)
        comments_text = "\n".join(comments) if comments else ""

        full_text = readme_text
        if comments_text:
            full_text += f"\n\nInline notes:\n{comments_text}"

        if not full_text.strip():
            continue

        docs.append(Document(
            page_content=full_text,
            metadata={
                "module_name": module_name,
                "source_type": "module_doc",
                "source_path": str(readme_path),
            },
        ))
    return docs


def build_internal_doc_documents() -> list[Document]:
    """One Document per internal doc (decision records, etc.)."""
    docs = []
    if not INTERNAL_DOCS_DIR.exists():
        return docs

    for doc_path in sorted(INTERNAL_DOCS_DIR.glob("*.md")):
        text = doc_path.read_text()
        if not text.strip():
            continue
        docs.append(Document(
            page_content=text,
            metadata={
                "source_type": "internal_doc",
                "source_path": str(doc_path),
            },
        ))
    return docs


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
    )


def build_vector_store(clear_first: bool = True) -> QdrantVectorStore:
    client = get_qdrant_client()
    embeddings = get_embeddings()

    if clear_first and client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        print("Cleared existing Qdrant collection")

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )

    all_docs = build_module_documents() + build_internal_doc_documents()
    print(f"Embedding {len(all_docs)} documents...")

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )
    vector_store.add_documents(all_docs)
    print("Vector store built.")
    return vector_store


def load_vector_store() -> QdrantVectorStore:
    """Connect to an already-built collection without re-embedding."""
    client = get_qdrant_client()
    embeddings = get_embeddings()
    return QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )


if __name__ == "__main__":
    build_vector_store()
