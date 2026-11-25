"""Sources for Qwen (Alibaba) model releases.

The qwen.ai research page is rendered with JavaScript; its article list comes
from the retrieval API below, which returns every article with its full markdown
body. Article pages live at https://qwen.ai/blog?id=<path> (checked in a browser).
Hugging Face lists the open-weight releases.
"""

from models.common.items import item, newest_first
from models.common.runner import cli
from models.common.sources import api, hf
from models.common.validation import require_type

ARTICLE_URL = "https://qwen.ai/blog?id="

def extract_articles(content: dict, source_url: str) -> list[dict]:
	"""Map the retrieval API response to items, using the introduction as summary and the markdown as body.

	Args:
		content (dict): JSON from the retrieval API, with articles under ``data.articles``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item per article, newest first.
	"""

	require_type("content", content, dict)

	items = []

	for article in content["data"]["articles"]:
		extra = article.get("extra") or {}
		items.append(item(article.get("title"), extra.get("date"), ARTICLE_URL + article["path"], extra.get("introduction"), article.get("content")))

	return newest_first(items)

LABEL = "Qwen"

SOURCES = [
	api("https://qwen.ai/api/v2/article/retrieval?type=qwen_ai&language=en-US", extract_articles),
	hf("Qwen"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
