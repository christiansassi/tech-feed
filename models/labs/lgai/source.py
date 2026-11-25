"""Sources for LG AI Research (EXAONE) model releases.

The blog is rendered with JavaScript; its post list comes from this API, which
also returns each post's full HTML. Posts in the News category (``BAAADD``)
open at https://www.lgresearch.ai/news/view?seq=<seq>, all other posts at
https://www.lgresearch.ai/blog/view?seq=<seq> (both checked with direct requests).
"""

from models.common.items import item, newest_first, to_markdown
from models.common.runner import cli
from models.common.sources import api, hf
from models.common.validation import require_type

BLOG_URL = "https://www.lgresearch.ai/blog/view?seq="

NEWS_URL = "https://www.lgresearch.ai/news/view?seq="

NEWS_CATEGORY = "BAAADD"

def extract_posts(content: dict, source_url: str) -> list[dict]:
	"""Map the blog list API response to items, using the post HTML for summary and body.

	Args:
		content (dict): JSON with the posts under ``data.list``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item per post, newest first.
	"""

	require_type("content", content, dict)

	items = []

	for post in (content.get("data") or {}).get("list") or []:
		base = NEWS_URL if post.get("catgCd") == NEWS_CATEGORY else BLOG_URL
		url = f"{base}{post.get('seq')}"
		date = post.get("expsYmd") or post.get("rgstYmd")
		items.append(item(post.get("ttl"), date, url, post.get("cont"), to_markdown(post.get("cont"), url)))

	return newest_first(items)

SOURCES = [
	api("https://www.lgresearch.ai/api/board/blog/list?pg=1&pgSz=10&schExpsYn=Y&schLangTp=en", extract_posts),
	hf("LGAI-EXAONE"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
