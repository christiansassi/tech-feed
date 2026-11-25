"""Sources for Z.ai (GLM, Zhipu) model releases.

The zhipuai.cn site runs on Payload CMS, whose public REST API returns the
research and news articles with English titles, dates, introductions and
bodies (Lexical rich text). An article either links to an external page, such
as https://z.ai/blog/glm-5.4, or is shown at https://www.zhipuai.cn/en/research/<id>.
The docs feed lags behind and Hugging Face lists the open models.
"""

from models.common.items import item, newest_first
from models.common.runner import cli
from models.common.sources import api, hf, rss
from models.common.validation import require_type

ARTICLES_API = "https://www.zhipuai.cn/api/articles?limit=20&sort=-createAt&depth=0&where[active][equals]=true&select[title_en]=true&select[createAt]=true&select[category]=true&select[resume_en]=true&select[externalUrl_en]=true&select[content_en]=true"

ARTICLE_URL = "https://www.zhipuai.cn/en/research/"

def _inline_text(node: dict) -> str:
	"""Return the text of a Lexical node and all its children, joined without separators.

	Args:
		node (dict): Lexical node, such as a paragraph, link or text node.

	Returns:
		str: Concatenated text.
	"""

	return node.get("text") or "".join(_inline_text(child) for child in node.get("children") or [])

def lexical_markdown(document: dict | None) -> str | None:
	"""Convert a Lexical rich text document to simple markdown.

	Headings become ``#`` lines, list items become ``- `` lines and every other
	block becomes a paragraph; inline formatting is dropped.

	Args:
		document (dict | None): Lexical document with a ``root`` node.

	Returns:
		str | None: Markdown text, or None when the document is empty.
	"""

	if not document:
		return None

	require_type("document", document, dict)

	blocks = []

	for block in (document.get("root") or {}).get("children") or []:
		kind = block.get("type")

		if kind == "heading":
			level = int(str(block.get("tag") or "h2")[1:] or 2)
			blocks.append("#" * level + " " + _inline_text(block))
		elif kind == "list":
			blocks.append("\n".join("- " + _inline_text(entry) for entry in block.get("children") or []))
		else:
			blocks.append(_inline_text(block))

	text = "\n\n".join(block.strip() for block in blocks if block.strip())

	return text or None

def extract_articles(content: dict, source_url: str) -> list[dict]:
	"""Map the Payload articles API response to items.

	Args:
		content (dict): JSON with the articles under ``docs``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item per article, newest first; the summary falls back to the start of the body.
	"""

	require_type("content", content, dict)

	items = []

	for article in content.get("docs") or []:
		body = lexical_markdown(article.get("content_en"))
		url = article.get("externalUrl_en") or f"{ARTICLE_URL}{article.get('id')}"
		items.append(item(article.get("title_en"), article.get("createAt"), url, article.get("resume_en") or body, body))

	return newest_first(items)

LABEL = "Z.ai"

SOURCES = [
	api(ARTICLES_API, extract_articles),
	rss("https://docs.z.ai/release-notes/new-released/rss.xml"),
	hf("zai-org"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
