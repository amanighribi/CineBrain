# CineBrain

A retrieval-augmented (RAG) chatbot that answers questions about films using Roger Ebert's published reviews. Each answer comes with the review excerpts it was based on, including the title, Ebert's star rating and a link to the original review.

This is a personal learning project. It was built to practice the full RAG pipeline: scraping, chunking, embeddings, vector search and LLM generation.

## How it works

1. **Collect.** `phase1_get_urls.py` opens the reviews page of rogerebert.com in a Playwright-controlled Chromium window, clicks "Load more" up to 24 times (about 500 reviews) and saves the review URLs to `data/urls.txt`. `phase2_scrape_reviews.py` then loads each page with Playwright, parses it with BeautifulSoup (title, reviewer, star rating, URL, review text) and appends one JSON record per review to `data/reviews.jsonl`. It can be stopped and re-run: URLs that were already saved are skipped, and pages with almost no text are dropped.
2. **Index.** `01_ingest.py` splits every review into paragraphs (paragraphs under 100 characters are skipped), embeds them with `all-MiniLM-L6-v2` (384-dimensional vectors) and stores them in a persistent ChromaDB collection using cosine similarity. Title, reviewer, rating and URL are kept as metadata.
3. **Answer.** `query.py` embeds the question, retrieves the most relevant review chunks from ChromaDB, and sends them with the question to an LLM through the Groq API. It returns the answer and the sources used.
4. **Interface.** `app.py` is a Streamlit chat UI. A "Sources" panel lists each source review with its rating and link.

## Project structure

```
phase1_get_urls.py        # collect review URLs
phase2_scrape_reviews.py  # scrape review text into data/reviews.jsonl
01_ingest.py              # chunk, embed and store in ChromaDB
query.py                  # retrieval + LLM answer (ask())
app.py                    # Streamlit chat interface
check.py                  # prints basic statistics about the scraped dataset
.env.example              # environment variables to set
requirements.txt
```

## Setup

```bash
git clone https://github.com/amanighribi/CineBrain.git
cd CineBrain
python -m venv .venv
.venv\Scripts\activate        # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # browser used by the scraper
```

Copy `.env.example` to `.env` and fill in your values:

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

`GROQ_MODEL` can be any chat model your Groq account has access to. Groq retires models from time to time, so the name is read from the environment and not hard-coded.

## Running it

The review data and the vector store are **not** included in this repository (the review text belongs to its publisher). You build them locally:

```bash
python phase1_get_urls.py        # opens a visible browser window; change CLICKS in the file for more or fewer reviews
python phase2_scrape_reviews.py
python check.py          # optional: sanity-check the scraped data
python 01_ingest.py      # builds the ChromaDB index in data/chroma
streamlit run app.py
```

Check the terms of the source website before scraping, and keep the scraped data for personal use.

## Limitations

- Only one source (Roger Ebert's reviews), so answers reflect that critic's opinions and cover only the films he reviewed.
- The scraper depends on the current HTML structure of the website (CSS classes and tags), so it may stop working if the site changes.
- Chunking is by paragraph, with no overlap and no reranking of retrieved results.
- The model can still make statements the retrieved excerpts don't support. The Sources panel is there so answers can be checked against the original reviews.
- There is no systematic evaluation of answer quality yet.
- The embedding model and the LLM are fixed choices that I have not benchmarked against alternatives.
