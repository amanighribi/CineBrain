import json
import chromadb
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

REVIEWS_FILE = "data/reviews.jsonl"
CHROMA_DIR   = "data/chroma"
COLLECTION   = "ebert_reviews"
MODEL_NAME   = "all-MiniLM-L6-v2"   # fast, good quality, 384-dim vectors

MIN_CHUNK_LEN = 100   # skip very short paragraphs


# ─────────────────────────────────────────────
# LOAD MODEL + DB
# ─────────────────────────────────────────────

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("Connecting to ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION,
    metadata={"hnsw:space": "cosine"}   # use cosine similarity for search
)


# ─────────────────────────────────────────────
# PROCESS REVIEWS
# ─────────────────────────────────────────────

print("Reading reviews...")
reviews = [json.loads(l) for l in open(REVIEWS_FILE, encoding="utf-8")]
print(f"Loaded {len(reviews)} reviews")

chunks_text = []
chunks_meta = []
chunks_ids  = []

for review in reviews:
    # Split review into paragraphs
    paragraphs = [p.strip() for p in review["review_text"].split("\n\n") if p.strip()]

    for i, para in enumerate(paragraphs):
        if len(para) < MIN_CHUNK_LEN:
            continue   # skip very short paragraphs (captions, headers, etc.)

        chunk_id = f"{review['url']}__chunk{i}"

        chunks_text.append(para)
        chunks_ids.append(chunk_id)
        chunks_meta.append({
            "title":    review["title"],
            "reviewer": review["reviewer"],
            "rating":   float(review["rating"]) if review["rating"] else -1.0,
            "url":      review["url"],
        })

print(f"Total chunks to embed: {len(chunks_text)}")


# ─────────────────────────────────────────────
# EMBED + STORE IN CHROMADB
# ─────────────────────────────────────────────

print("Embedding chunks (this takes a minute)...")
embeddings = model.encode(chunks_text, show_progress_bar=True)

print("Storing in ChromaDB...")
# ChromaDB has a batch limit, so we insert in batches of 500
BATCH = 500
for i in range(0, len(chunks_text), BATCH):
    collection.add(
        ids        = chunks_ids[i:i+BATCH],
        documents  = chunks_text[i:i+BATCH],
        embeddings = [e.tolist() for e in embeddings[i:i+BATCH]],
        metadatas  = chunks_meta[i:i+BATCH],
    )
    print(f"  Stored {min(i+BATCH, len(chunks_text))}/{len(chunks_text)} chunks")

print("-" * 50)
print(f"Done. {len(chunks_text)} chunks stored in ChromaDB at {CHROMA_DIR}")