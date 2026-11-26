"""Sources for MiniMax and Hailuo model releases.

Hailuo launches appear in the news section, whose list comes from the news API
(posts live at https://www.minimax.io/news/<slug>). The blog is server-rendered
HTML read with the generic link list extractor.
"""

from models.common.items import item, newest_first
from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import api, hf, html, query_page
from models.common.validation import require_type

NEWS_URL = "https://www.minimax.io/news/"

def extract_news(content: dict, source_url: str) -> list[dict]:
	"""Map the news API response to items.

	Args:
		content (dict): JSON with the posts under ``data``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item per news post, newest first.
	"""

	require_type("content", content, dict)

	items = []

	for post in content.get("data") or []:
		url = NEWS_URL + post["slug"] if post.get("slug") else None
		items.append(item(post.get("title"), post.get("publishDate"), url, post.get("summary"), post.get("content") or None))

	return newest_first(items)

NEWS_API = "https://www.minimax.io/api/news?page=1&locale=en"

LABEL = "MiniMax"

SOURCES = [
	html("https://www.minimax.io/blog", link_list(r"^/(?:blog|news)/[^/]+$")),
	hf("MiniMaxAI"),
	api(NEWS_API, extract_news, next_page=query_page(NEWS_API, "page")),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
