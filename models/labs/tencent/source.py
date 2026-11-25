"""Sources for Tencent Hunyuan model releases.

The research page is a JavaScript app; its post list comes from this API, which
also returns each post's body in Hunyuan's own block markup (``@@@block`` and ``[[name]]`` lines
followed by ``key = "value"`` settings and text). Posts live at
https://hunyuan.tencent.com/research/<customUrl>, or at /research/<id> when a post
has no custom URL (both checked in a browser).
"""

import re

from models.common.items import item, newest_first
from models.common.runner import cli
from models.common.sources import api, hf
from models.common.validation import require_type

POST_URL = "https://hunyuan.tencent.com/research/"

_SETTING = re.compile(r'^\s*(@@@\w*|\[\[\w+\]\]|[\w-]+\s*=\s*".*?"|[\w-]+\s*=\s*\S*)\s*$', re.MULTILINE)

def readable_text(markup: str | None) -> str | None:
	"""Remove the block markers and block settings from a Hunyuan post body.

	Args:
		markup (str | None): Post body in Hunyuan block markup.

	Returns:
		str | None: Remaining text with blank lines collapsed, or None.
	"""

	if not markup:
		return None

	require_type("markup", markup, str)

	text = re.sub(r"\n{3,}", "\n\n", _SETTING.sub("", markup)).strip()

	return text or None

def extract_posts(content: dict, source_url: str) -> list[dict]:
	"""Map the blog list API response to items.

	Args:
		content (dict): JSON with the posts under ``data.list``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item per post, newest first.
	"""

	require_type("content", content, dict)

	items = []

	for post in (content.get("data") or {}).get("list") or []:
		body = readable_text(post.get("content"))
		slug = post.get("customUrl") or post.get("id")
		url = f"{POST_URL}{slug}" if slug else None
		items.append(item(post.get("title"), post.get("displayPublishTime") or post.get("publishedAt"), url, body, body))

	return newest_first(items)

LABEL = "Tencent"

SOURCES = [
	api("https://api.hunyuan.tencent.com/api/blog/publicList", extract_posts, method="POST", json_body={"pageNum": 1, "pageSize": 20}),
	hf("tencent", search="Hunyuan"),
	hf("tencent", search="Hy"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
