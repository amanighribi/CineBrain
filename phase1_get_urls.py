from playwright.sync_api import sync_playwright
import os
import time

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

URL = "https://www.rogerebert.com/reviews"
OUTPUT_FILE = "data/urls.txt"
CLICKS = 24          # 1 initial load + 24 clicks = 25 batches = ~500 reviews
WAIT_SECONDS = 2     # wait after each "Load more" click


def extract_urls(page):
    links = page.eval_on_selector_all(
        "a[href*='/reviews/']",
        "elements => elements.map(el => el.href)"
    )
    urls = [
        link for link in links
        if link.startswith("https://www.rogerebert.com/reviews/")
        and link != "https://www.rogerebert.com/reviews/"
    ]
    return list(dict.fromkeys(urls))


def main():
    # The data/ folder is not part of the repository, so create it if it is missing
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f"Opening {URL} ...")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)  # let ads and JS finish loading

        print("Page loaded.")

        all_urls = set()

        initial_urls = extract_urls(page)
        all_urls.update(initial_urls)
        print(f"Initial load: {len(initial_urls)} URLs found (total: {len(all_urls)})")

        for click_num in range(1, CLICKS + 1):
            print(f"Click {click_num}/{CLICKS}...", end=" ", flush=True)

            try:
                load_more = page.locator("button.facetwp-load-more")
                load_more.wait_for(state="visible", timeout=10000)
                load_more.click()

                time.sleep(WAIT_SECONDS)

                current_urls = extract_urls(page)
                new_count = len(set(current_urls) - all_urls)
                all_urls.update(current_urls)

                print(f"+{new_count} new URLs (total: {len(all_urls)})")

            except Exception as e:
                print(f"\n[STOP] Could not click 'Load more': {e}")
                break

        browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")

    print("-" * 50)
    print(f"Done. {len(all_urls)} URLs saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()