import os
import glob
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Document

load_dotenv(find_dotenv())

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "leukemia_knowledge_base")
DATA_DIR = Path(__file__).parent / "data"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 50

# Connect to Qdrant Cloud
client = QdrantClient(
    url=os.getenv("QDRANT_API_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    cloud_inference=True,
)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Split text into chunks by paragraphs, then by size if needed."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 1 <= chunk_size:
            current_chunk = f"{current_chunk}\n{para}".strip() if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If a single paragraph exceeds chunk_size, split by sentences
            if len(para) > chunk_size:
                words = para.split()
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= chunk_size:
                        current_chunk = f"{current_chunk} {word}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = word
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def load_txt_files(data_dir: Path) -> list[dict]:
    """Read all .txt files from data directory and chunk them."""
    all_chunks = []
    txt_files = sorted(glob.glob(str(data_dir / "*.txt")))

    if not txt_files:
        print(f"No .txt files found in {data_dir}")
        return all_chunks

    for filepath in txt_files:
        filename = os.path.basename(filepath)
        print(f"Reading: {filename}")
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source_file": filename,
                "chunk_index": i,
            })
        print(f"  -> {len(chunks)} chunks")

    return all_chunks


def ingestion():
    """Create collection and ingest all txt files from data/ into Qdrant."""
    # Recreate collection
    if client.collection_exists(collection_name=COLLECTION_NAME):
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(collection_name=COLLECTION_NAME)

    print(f"Creating collection: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    # Load and chunk documents
    all_chunks = load_txt_files(DATA_DIR)
    if not all_chunks:
        print("No data to ingest.")
        return

    # Build points
    points = []
    for i, chunk in enumerate(all_chunks):
        point = PointStruct(
            id=i,
            vector=Document(
                text=chunk["text"],
                model=EMBEDDING_MODEL,
            ),
            payload={
                "text": chunk["text"],
                "source_file": chunk["source_file"],
                "chunk_index": chunk["chunk_index"],
            },
        )
        points.append(point)

    # Upsert in batches of 100
    batch_size = 100
    for start in range(0, len(points), batch_size):
        batch = points[start : start + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(f"  Upserted points {start} - {start + len(batch) - 1}")

    print(f"\nIngestion complete: {len(points)} chunks into '{COLLECTION_NAME}'")


def search(query_text: str, limit: int = 5):
    """Search the collection for similar chunks."""
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=Document(text=query_text, model=EMBEDDING_MODEL),
        with_payload=True,
        limit=limit,
    )

    print(f"\nSearch results for: '{query_text}'\n")
    for result in results.points:
        print(f"Score: {result.score:.4f}")
        print(f"Source: {result.payload.get('source_file', 'N/A')}")
        print(f"Text: {result.payload['text'][:200]}...")
        print("---")


if __name__ == "__main__":
    ingestion()
    print("\n" + "=" * 60)
    search("How does the blast percentage differ between acute and chronic leukemia?")
    print("\n" + "=" * 60)
    search("What chromosomal translocation defines CML, and what genes are involved?")
