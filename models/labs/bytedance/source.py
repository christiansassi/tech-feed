"""Sources for ByteDance Seed model releases.

The blog is rendered with JavaScript; its article list comes from this API
(article_type=2 is the blog). Some posts only have Chinese fields, so the English
title is used when present and the Chinese one otherwise. Article pages live at
https://seed.bytedance.com/<en|zh>/blog/<TitleKey> (checked in a browser).
"""

from models.common.items import item, newest_first
from models.common.runner import cli
from models.common.sources import api, hf
from models.common.validation import require_type

SITE = "https://seed.bytedance.com"

def extract_articles(content: dict, source_url: str) -> list[dict]:
	"""Map the article list API response to items, preferring the English version of each post.

	Args:
		content (dict): JSON with the posts under ``sub_article_list``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item per post, newest first.
	"""

	require_type("content", content, dict)

	items = []

	for article in content.get("sub_article_list") or []:
		english = article.get("ArticleSubContentEn") or {}
		chinese = article.get("ArticleSubContentZh") or {}
		lang, sub = ("en", english) if (english.get("Title") or "").strip() else ("zh", chinese)
		url = f"{SITE}/{lang}/blog/{sub.get('TitleKey')}" if sub.get("TitleKey") else None
		published = (article.get("ArticleMeta") or {}).get("PublishDate")
		items.append(item(sub.get("Title"), published, url, (sub.get("Abstract") or "").strip() or None, sub.get("Content")))

	return newest_first(items)

SOURCES = [
	api("https://seed.bytedance.com/api/get_article_list_v2?article_type=2&count=10&order_desc=true", extract_articles),
	hf("ByteDance-Seed"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
