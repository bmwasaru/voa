import csv
import html
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException


class VoaSwahili:
    """
    Scrape VOA Swahili article pages and save clean sentences to a daily CSV file.

    Output saved using the date of running:
        sentences/dd-mm-yy.csv

    Key fixes:
    - get_page_headlines() now collects article links only by default. It does not
      write category/homepage headings into the sentence CSV unless explicitly asked.
    - Sentences already present in today's CSV are loaded and skipped, so rerunning
      the daily job does not keep appending duplicates.
    - Article extraction prefers paragraph tags inside the article body instead of
      dumping the whole page container.
    - VOA UI noise such as share buttons, player controls, related links, comments,
      and footer/navigation text is removed before sentence splitting.
    """

    BASE_URL = "https://www.voaswahili.com"

    NOISE_EXACT = {
        "",
        "shirikisha",
        "copy link",
        "facebook",
        "twitter",
        "whatsapp",
        "email",
        "ona maoni",
        "follow us",
        "x (twitter)",
        "youtube",
        "instagram",
        "print",
        "zinazohusiana",
        "forum",
        "funga",
        "tufuate",
        "habari",
        "afrika",
        "marekani",
        "dunia",
        "embed",
        "embed share",
        "share",
        "pleya",
        "kiungo cha moja kwa moja",
        "no media source currently available",
        "the code has been copied to your clipboard.",
        "the url has been copied to your clipboard",
        "please enable javascript to view the",
        "comments powered by disqus.",
        "this item is part of",
        "mubashara",
        "breaking news",
        "voa swahili",
        "voa swahili audio tube",
        "voa audio tube",
        "audio tube",
        "matangazo",
        "video",
        "voa africa",
        "idhaa yetu",
        "xs",
        "sm",
        "md",
        "lg",
        "zaidi",
        "iliyopita ijayo",
        "iliyopita",
        "ijayo",
        "jioni",
        "alfajiri",
        "kwa undani",
        "voa express",
        "duniani leo",
    }

    NOISE_PATTERNS = [
        re.compile(r"^by\s+VOA\s+Swahili", re.I),
        re.compile(r"^by\s+VOA\s+Swahili\s*[-–—]\s*Idhaa", re.I),
        re.compile(r"\bVOA\s+Swahili\s+Audio\s+Tube\b", re.I),
        re.compile(r"^\d{1,3}\s*kbps\s*\|\s*MP3$", re.I),
        re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$"),
        re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?\s+\d{1,2}:\d{2}(?::\d{2})?(\s+\d{1,2}:\d{2}(?::\d{2})?)?$"),
        re.compile(r"^width px height px$", re.I),
        re.compile(r".*\.(wav|mp3)$", re.I),
        re.compile(r"^local time:", re.I),
        re.compile(r"^[\*\-–—]+$"),
        re.compile(r"^\d+$"),
    ]

    REMOVE_SELECTORS = [
        "script",
        "style",
        "noscript",
        "nav",
        "footer",
        "header",
        "form",
        "iframe",
        "button",
        "aside",
        "svg",
        "picture",
        ".comments",
        "#comments",
        ".comment",
        ".disqus",
        ".share",
        ".social",
        ".article__links",
        ".content-offset",
        ".related-content",
        ".media-download",
        ".c-mmp",
        ".c-mmp__player",
        ".player",
        ".audio-player",
        ".embed",
        ".print",
        ".follow-us",
        ".footer",
        ".site-footer",
    ]

    LINK_SELECTORS = [
        "a.img-wrap[href]",
        "a.media-block__link[href]",
        "h4.media-block__title a[href]",
        "h3.media-block__title a[href]",
        "a[href*='/a/'][href]",
    ]

    def __init__(self, url, sub_folder=None, output_dir="sentences"):
        self.url = url
        self.sub_folder = sub_folder
        self.current_date = datetime.now().strftime("%d-%m-%y")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.page_links = []
        self.seen_sentences = set()
        self.seen_links = set()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                )
            }
        )

        self.load_existing_sentences()

    @property
    def output_path(self):
        return self.output_dir / f"{self.current_date}.csv"

    def load_existing_sentences(self):
        """Avoid duplicate appends when the daily cron/job is rerun."""
        if not self.output_path.exists():
            return

        try:
            with self.output_path.open("r", newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if not row:
                        continue
                    sentence = self.normalize_text(row[0])
                    if sentence:
                        self.seen_sentences.add(sentence.casefold())
        except Exception as exc:
            logging.warning("Could not read existing CSV %s: %s", self.output_path, exc)

    def fetch_soup(self, url):
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def normalize_text(self, text):
        text = html.unescape(text or "")
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\u00a0", " ").replace("\ufeff", " ")
        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([,.;:?!%])", r"\1", text)
        text = re.sub(r"([(“])\s+", r"\1", text)
        text = re.sub(r"\s+([)”])", r"\1", text)
        return text.strip()

    def is_noise(self, text):
        text = self.normalize_text(text)
        lower = text.casefold()

        if lower in self.NOISE_EXACT:
            return True

        if len(lower) < 2:
            return True

        for pattern in self.NOISE_PATTERNS:
            if pattern.search(text):
                return True

        # Remove short menu/program labels, but keep real sentences/questions.
        if len(text.split()) <= 2 and not re.search(r"[.!?]", text) and text.istitle():
            return True

        return False

    def split_sentences(self, text):
        text = self.normalize_text(text)
        if not text:
            return []

        # Split after punctuation. Keep abbreviations reasonably intact by only
        # splitting where the next sentence starts with uppercase/number/quote.
        pieces = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ0-9\"“])", text)
        return [self.normalize_text(piece) for piece in pieces if self.normalize_text(piece)]

    def clean_sentences(self, texts):
        cleaned = []
        for text in texts:
            for sentence in self.split_sentences(text):
                if self.is_noise(sentence):
                    continue

                key = sentence.casefold()
                if key in self.seen_sentences:
                    continue

                self.seen_sentences.add(key)
                cleaned.append(sentence)

        return cleaned

    def remove_page_noise(self, soup):
        for selector in self.REMOVE_SELECTORS:
            for tag in soup.select(selector):
                tag.decompose()

        noisy_class_words = re.compile(
            r"(share|social|comment|related|footer|player|audio|embed|print|cookie)",
            re.I,
        )
        for tag in soup.find_all(class_=noisy_class_words):
            tag.decompose()

        # Some VOA pages expose audio-widget labels as plain text nodes or
        # headings rather than inside a reliably named `.audio` / `.player`
        # container. Remove those blocks before paragraph extraction so strings
        # such as "VOA Swahili Audio Tube" are not saved as corpus rows.
        audio_label = re.compile(r"VOA\s+Swahili\s+Audio\s+Tube", re.I)
        for tag in soup.find_all(string=audio_label):
            parent = tag.parent
            if parent and parent.name not in {"html", "body"}:
                parent.decompose()
            else:
                tag.extract()

        return soup

    def is_article_url(self, url):
        parsed = urlparse(url)
        if parsed.netloc and parsed.netloc != urlparse(self.BASE_URL).netloc:
            return False

        path = parsed.path or ""
        # VOA article URLs normally contain /a/. This avoids adding category,
        # live radio, video channel, and footer/navigation URLs.
        return "/a/" in path

    def get_page_headlines(self, write_headlines=False):
        """
        Collect article links from the listing/category page.

        The method name is kept for compatibility with your existing get_news.py.
        By default it does NOT write headlines into the CSV, because those caused
        category titles like Alfajiri, VOA Express, and duplicate headings to be
        saved as corpus sentences.
        """
        try:
            soup = self.fetch_soup(self.url)
        except RequestException as exc:
            logging.error("Failed to fetch listing page %s: %s", self.url, exc)
            return

        for selector in self.LINK_SELECTORS:
            for tag in soup.select(selector):
                href = tag.get("href")
                if not href:
                    continue

                full_url = urljoin(self.BASE_URL, href)
                full_url = full_url.split("#", 1)[0]

                if not self.is_article_url(full_url):
                    continue

                if full_url not in self.seen_links:
                    self.seen_links.add(full_url)
                    self.page_links.append(full_url)

        if write_headlines:
            headline_texts = [
                tag.get_text(" ", strip=True)
                for tag in soup.select("h4.media-block__title, h3.media-block__title")
            ]
            self.write_sentences(self.clean_sentences(headline_texts))

    def find_container_by_class_string(self, soup, class_string):
        if not class_string:
            return None

        classes = [cls for cls in class_string.split() if cls]
        if not classes:
            return None

        selector = "." + ".".join(classes)
        return soup.select_one(selector)

    def extract_article_texts(self, soup, content_class=None):
        soup = self.remove_page_noise(soup)

        root = self.find_container_by_class_string(soup, content_class) if content_class else None

        if root:
            # Important for get_news.py: normal categories pass
            # "content-floated-wrap fb-quotable" and makala-maalum passes
            # "container container--featured m-t-md". Extract paragraphs inside
            # those containers rather than using get_text() on the whole block.
            texts = [tag.get_text(" ", strip=True) for tag in root.select("p")]
            texts = [text for text in texts if text]
            if texts:
                return texts

        article_selectors = [
            "article p",
            "div.article__body p",
            "div.wsw p",
            "div.content-floated-wrap.fb-quotable p",
            "div.content-floated-wrap p",
            "div.container.container--featured.m-t-md p",
        ]

        for selector in article_selectors:
            texts = [tag.get_text(" ", strip=True) for tag in soup.select(selector)]
            texts = [text for text in texts if text]
            if texts:
                return texts

        # Last-resort fallback for unusual pages.
        fallback_root = root or soup
        return fallback_root.get_text("\n", strip=True).splitlines()

    def write_sentences(self, sentences):
        """
        Append cleaned sentences to today's CSV file.

        Important: this method intentionally uses append mode (`a`), not write
        mode (`w`). Therefore each article/category adds rows to the existing
        daily CSV instead of recreating/replacing it.
        """
        if not sentences:
            return

        # `a` means append. Do not change this to `w`, because `w` would
        # rewrite the CSV every time the scraper processes another article.
        with self.output_path.open("a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            for sentence in sentences:
                sentence = self.normalize_text(sentence)
                if sentence and not self.is_noise(sentence):
                    writer.writerow([sentence])

    def get_page_content(self, content_class=None):
        """
        Scrape all article URLs collected from one category/listing page.

        Sentences are collected first, then appended once at the end of this
        category run. This avoids opening/recreating the file inside every
        article loop while still appending to the same daily CSV.
        """
        category_sentences = []

        for link in self.page_links:
            try:
                soup = self.fetch_soup(link)
                raw_texts = self.extract_article_texts(soup, content_class=content_class)
                category_sentences.extend(self.clean_sentences(raw_texts))
            except RequestException as exc:
                logging.error("CONNECTION ERROR: %s - %s", link, exc)
            except Exception as exc:
                logging.exception("FAILED TO PROCESS: %s - %s", link, exc)

        # Append this category's cleaned sentences to today's CSV.
        self.write_sentences(category_sentences)
