"""Sources for AI21 Labs (Jamba) model releases.

The blog runs on WordPress, so its REST API returns the posts as JSON with title,
date, link, excerpt and full HTML content.
"""

from models.common.items import item, newest_first, to_markdown
from models.common.runner import cli
from models.common.sources import api, hf
from models.common.validation import require_type

def extract_posts(content: list, source_url: str) -> list[dict]:
	"""Map WordPress REST posts to items, using the excerpt as summary and the content as body.

	Args:
		content (list): JSON list from ``/wp-json/wp/v2/posts``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item per post, newest first.
	"""

	require_type("content", content, list)

	items = []

	for post in content:
		link = post.get("link")
		excerpt = (post.get("excerpt") or {}).get("rendered")
		body = to_markdown((post.get("content") or {}).get("rendered"), link)
		items.append(item((post.get("title") or {}).get("rendered"), post.get("date"), link, excerpt, body))

	return newest_first(items)

LABEL = "AI21 Labs"

SOURCES = [
	api("https://www.ai21.com/wp-json/wp/v2/posts?per_page=10&_fields=date,title,link,excerpt,content", extract_posts),
	hf("ai21labs"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
