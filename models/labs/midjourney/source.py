"""Sources for Midjourney model releases.

The updates site is private and midjourney.com is behind a bot challenge, so the
help center API is used: the Version article lists every model version, and the
newest articles show new features. Both lag behind launches.
"""

from models.common.items import item, newest_first, to_markdown
from models.common.runner import cli
from models.common.sources import api
from models.common.validation import require_type

def article_item(article: dict) -> dict:
	"""Map one help center article to an item, using its HTML body for summary and body.

	Args:
		article (dict): Article object from the Zendesk help center API.

	Returns:
		dict: Item with the article's last edit date, so a new model version shows as a fresh date.
	"""

	require_type("article", article, dict)

	url = article.get("html_url")
	date = article.get("edited_at") or article.get("updated_at") or article.get("created_at")

	return item(article.get("title"), date, url, article.get("body"), to_markdown(article.get("body"), url))

def extract_article(content: dict, source_url: str) -> list[dict]:
	"""Map a single-article response to a one-item list.

	Args:
		content (dict): JSON with the article under ``article``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item.
	"""

	require_type("content", content, dict)

	return [article_item(content["article"])]

def extract_articles(content: dict, source_url: str) -> list[dict]:
	"""Map an article list response to items.

	Args:
		content (dict): JSON with the articles under ``articles``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item per article, newest first.
	"""

	require_type("content", content, dict)

	return newest_first([article_item(article) for article in content.get("articles") or []])

LABEL = "Midjourney"

SOURCES = [
	api("https://docs.midjourney.com/api/v2/help_center/en-us/articles/32199405667853.json", extract_article),
	api("https://docs.midjourney.com/api/v2/help_center/en-us/articles.json?sort_by=created_at&sort_order=desc&per_page=30", extract_articles),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
