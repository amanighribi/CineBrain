from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import os
import time

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

INPUT_FILE  = "data/urls.txt"
OUTPUT_FILE = "data/reviews.jsonl"
SLEEP_SECONDS = 1.5


# ─────────────────────────────────────────────
# FUNCTION: extract review data from page HTML
# ─────────────────────────────────────────────

def parse_review(html, url):
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Unknown"

    # Reviewer
    reviewer = "Unknown"
    reviewer_tag = soup.find("a", {"rel": "author"})
    if reviewer_tag:
        reviewer = reviewer_tag.get_text(strip=True)

    # Rating (CSS class like "star35" = 3.5 stars)
    rating = None
    star_tag = soup.find("img", class_=lambda c: c and "filled" in c.split() if c else False)
    if star_tag:
        for cls in star_tag.get("class", []):
            if cls.startswith("star") and cls[4:].isdigit():
                rating = int(cls[4:]) / 10

    # Review body
    review_text = ""
    article = soup.find("div", class_=lambda c: "review-body" in c if c else False)
    if not article:
        article = soup.find("article")
    if article:
        paragraphs = article.find_all("p")
        review_text = "\n\n".join(
            p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
        )

    if len(review_text) < 100:
        return None

    return {
        "url": url,
        "title": title,
        "reviewer": reviewer,
        "rating": rating,
        "review_text": review_text,
    }


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    with open(INPUT_FILE) as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(urls)} URLs")

    # Resume support
    already_done = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            for line in f:
                try:
                    already_done.add(json.loads(line)["url"])
                except:
                    pass
        print(f"Resuming: {len(already_done)} done, {len(urls) - len(already_done)} remaining")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        scraped = 0
        skipped = 0

        with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
            for i, url in enumerate(urls, 1):
                if url in already_done:
                    continue

                slug = url.split("/")[-1][:50]
                print(f"[{i}/{len(urls)}] {slug}...", end=" ", flush=True)

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(1)
                    html = page.content()
                    review = parse_review(html, url)
                except Exception as e:
                    print(f"ERROR: {e}")
                    skipped += 1
                    continue

                if review:
                    out.write(json.dumps(review, ensure_ascii=False) + "\n")
                    scraped += 1
                    print(f"✓  ({len(review['review_text'])} chars)")
                else:
                    skipped += 1
                    print("skipped (no text)")

                time.sleep(SLEEP_SECONDS)

        browser.close()

    print("-" * 50)
    print(f"Done. {scraped} saved, {skipped} skipped → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()