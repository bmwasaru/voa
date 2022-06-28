from utils import VoaSwahili


news_links = {
    'headlines': "https://www.voaswahili.com/",
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


for k, v in news_links.items():
    news = VoaSwahili(v, k)
    news.get_page_headlines()
    news.get_page_content(content_class="content-floated-wrap fb-quotable")


special_news = VoaSwahili("https://www.voaswahili.com/makala-maalum", "makala-maalum")
special_news.get_page_content(content_class="fa-container")
