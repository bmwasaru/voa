import logging

from utils import VoaSwahili


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# Main VOA Swahili category and sub-category pages.
# Output behavior:
# - Each daily run writes/appends to that day's dated file only:
#       sentences/dd-mm-yy.csv
# - All categories scraped on the same day go into that same dated file.
NEWS_LINKS = {
    "headlines": "https://www.voaswahili.com/",
    "kenya": "https://www.voaswahili.com/kenya",
    "tanzania": "https://www.voaswahili.com/tanzania",
    "kongo": "https://www.voaswahili.com/jamhuri-ya-kidemokrasia-ya-kongo",
    "rwanda": "https://www.voaswahili.com/rwanda",
    "uganda": "https://www.voaswahili.com/uganda",
    "burundi": "https://www.voaswahili.com/burundi",
    "afrika": "https://www.voaswahili.com/afrika",
    "marekani": "https://www.voaswahili.com/marekani",
    "dunia": "https://www.voaswahili.com/dunia",
}

DEFAULT_CONTENT_CLASS = "content-floated-wrap fb-quotable"
SPECIAL_CONTENT_CLASS = "container container--featured m-t-md"


def scrape_listing(name, url, content_class):
    logging.info("Scraping category: %s", name)
    news = VoaSwahili(url, name)

    # Keep write_headlines=False. This prevents category/listing headlines and
    # programme names from being saved directly into the sentence corpus.
    news.get_page_headlines(write_headlines=False)
    logging.info("Found %s article links for %s", len(news.page_links), name)

    news.get_page_content(content_class=content_class)
    logging.info("Finished category: %s", name)


def main():
    for name, url in NEWS_LINKS.items():
        scrape_listing(name, url, DEFAULT_CONTENT_CLASS)

    scrape_listing(
        "makala-maalum",
        "https://www.voaswahili.com/makala-maalum",
        SPECIAL_CONTENT_CLASS,
    )


if __name__ == "__main__":
    main()
