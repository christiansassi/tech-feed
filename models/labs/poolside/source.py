"""Sources for Poolside (Laguna) model releases.

The blog is a SvelteKit app; ``__data.json`` holds its post list in SvelteKit's
flattened "devalue" format, where objects store the indexes of their values in
one shared array. Posts live at https://poolside.ai/blog/<slug>.
"""

from typing import Any

from models.common.items import item, newest_first
from models.common.runner import cli
from models.common.sources import api, hf
from models.common.validation import require_type

POST_URL = "https://poolside.ai/blog/"

def unflatten(values: list) -> Any:
	"""Rebuild the value stored in a devalue array, whose first element is the root.

	Args:
		values (list): Flattened array from a SvelteKit node's ``data`` field.

	Returns:
		Any: The rebuilt nested value.
	"""

	require_type("values", values, list)

	def resolve(index: int) -> Any:
		"""Return the value at ``index``, resolving nested indexes.

		Args:
			index (int): Position in ``values``; negative numbers stand for special values.

		Returns:
			Any: Rebuilt value, or None for special values.
		"""

		if index < 0:
			return None

		value = values[index]

		if isinstance(value, dict):
			return {key: resolve(child) for key, child in value.items()}

		if isinstance(value, list):
			return [resolve(child) for child in value]

		return value

	return resolve(0)

def extract_posts(content: dict, source_url: str) -> list[dict]:
	"""Map the SvelteKit data of the blog page to items.

	Args:
		content (dict): JSON from ``/blog/__data.json``.
		source_url (str): API URL (unused).

	Returns:
		list[dict]: One item per post with its description as summary, newest first.
	"""

	require_type("content", content, dict)

	posts = []

	for node in content.get("nodes") or []:

		if node and node.get("type") == "data" and node.get("data"):
			groups = (unflatten(node["data"]) or {}).get("posts") or {}
			posts.extend(post for group in groups.values() if isinstance(group, list) for post in group)

	seen = set()
	items = []

	for post in posts:

		if not isinstance(post, dict) or post.get("slug") in seen:
			continue

		seen.add(post.get("slug"))
		items.append(item(post.get("title"), post.get("date"), POST_URL + post.get("slug", ""), post.get("description")))

	return newest_first(items)

SOURCES = [
	api("https://poolside.ai/blog/__data.json", extract_posts),
	hf("poolside"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
