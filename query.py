import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
import os
from dotenv import load_dotenv
from groq import Groq
load_dotenv()
print([m.id for m in Groq().models.list().data])
# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

CHROMA_DIR  = "data/chroma"
COLLECTION  = "ebert_reviews"
MODEL_NAME  = "all-MiniLM-L6-v2"
TOP_K       = 5      # number of chunks to retrieve per query
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
# Load once — these are reused across queries
model      = SentenceTransformer(MODEL_NAME)
client     = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_collection(COLLECTION)
import os
groq = Groq()

# ─────────────────────────────────────────────
# CORE FUNCTION
# ─────────────────────────────────────────────

def ask(question: str) -> dict:
    """
    Full RAG pipeline:
    1. Embed the question
    2. Retrieve top-K similar chunks from ChromaDB
    3. Build a prompt with the retrieved context
    4. Call Groq LLM and return the answer

    Returns a dict with 'answer' and 'sources'.
    """

    # STEP 1 — embed the question
    query_vector = model.encode(question).tolist()

    # STEP 2 — retrieve similar chunks
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"]
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # STEP 3 — build context string
    context_parts = []
    for doc, meta in zip(documents, metadatas):
        context_parts.append(
            f"Movie: {meta['title']} (Rating: {meta['rating']}/4.0)\n"
            f"Reviewer: {meta['reviewer']}\n"
            f"Excerpt: {doc}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # STEP 4 — build prompt and call Groq
    prompt = f"""You are CineBrain, an expert film analyst with deep knowledge of cinema.
You answer questions about movies using review excerpts as your source material.
Be insightful, specific, and conversational. Reference the reviews naturally.
If the context doesn't contain enough information, say so honestly.

REVIEW EXCERPTS:
{context}

USER QUESTION:
{question}

Answer based on the review excerpts above:"""

    response = groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content

    # Build sources list for display
    sources = [
        {
            "title":    m["title"],
            "reviewer": m["reviewer"],
            "rating":   m["rating"],
            "url":      m["url"],
        }
        for m in metadatas
    ]
    # deduplicate by title
    seen = set()
    unique_sources = []
    for s in sources:
        if s["title"] not in seen:
            seen.add(s["title"])
            unique_sources.append(s)

    return {"answer": answer, "sources": unique_sources}


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    test_question = "What makes a great psychological thriller?"
    print(f"Question: {test_question}\n")
    print("Thinking...\n")

    result = ask(test_question)

    print("ANSWER:")
    print(result["answer"])
    print("\nSOURCES:")
    for s in result["sources"]:
        print(f"  - {s['title']} ({s['rating']}/4.0) — {s['reviewer']}")