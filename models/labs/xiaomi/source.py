"""Sources for Xiaomi MiMo model releases.

Hugging Face is the main signal. The MiMo site is built with Rspress: the
homepage loads several script bundles, and one of them holds the metadata of
every page (route, language and front matter). The bundle names change on every
deploy, so they are read from the homepage first. Blog posts and model launch
pages (``/mimo-v2-6/``) are taken from that metadata. Posts usually carry their
title, description and date in the front matter; the model launch posts carry
none, so only those pages are fetched (following their iframe to the static
article) to read the title and the date (the first full date in the text,
else the month of a ``time`` element).
"""

import re
from urllib.parse import urljoin

import primp
from selectolax.lexbor import LexborHTMLParser

from models.common.http import FetchError, send
from models.common.items import item, newest_first
from models.common.pages import find_date, node_text
from models.common.runner import cli
from models.common.sources import Source, custom, hf
from models.common.validation import require_type

HOMEPAGE = "https://mimo.xiaomi.com/"

SCRIPT = re.compile(r'<script[^>]+src="([^"]+\.js)"')

PAGE = re.compile(r'routePath:"(/blog/[^"/]+|/mimo-v[\w-]+/?)",lang:"en",toc:\[.*?\],frontmatter:(\{.*?\}),version:')

FIELD = r'{}:"((?:[^"\\]|\\.)*)"'

TITLE_SUFFIX = re.compile(r"\s*\|\s*Xiaomi\s*$")

# Placeholder route that repeats the MiMo-V2-Flash post.
SKIPPED_ROUTES = {"/blog/blog1"}

def _field(frontmatter: str, name: str) -> str | None:
	"""Return one string field of a front matter object written as JavaScript.

	Args:
		frontmatter (str): Source text of the front matter object.
		name (str): Field name, such as ``"title"``.

	Returns:
		str | None: Field value, or None when missing or empty.
	"""

	match = re.search(FIELD.format(name), frontmatter)

	return match.group(1) if match and match.group(1) else None

def _page_details(client: primp.Client, url: str) -> dict:
	"""Read the title, description and first date of a MiMo page, following one iframe.

	Args:
		client (primp.Client): Client from ``new_client``.
		url (str): Absolute page URL.

	Returns:
		dict: ``title``, ``summary`` and ``date``, each possibly None.
	"""

	tree = LexborHTMLParser(send(client, url).text)
	frame = tree.css_first("iframe[src]")

	if frame is not None:
		tree = LexborHTMLParser(send(client, urljoin(url, frame.attributes["src"])).text)

	title = tree.css_first("title")
	description = tree.css_first('meta[name="description"]')
	time = tree.css_first("time[datetime]")

	return {
		"title": TITLE_SUFFIX.sub("", node_text(title)) if title is not None else None,
		"summary": description.attributes.get("content") if description is not None else None,
		"date": find_date(node_text(tree.body)) or (time.attributes.get("datetime") if time is not None else None),
	}

def bundle_posts(client: primp.Client, source: Source) -> list[dict]:
	"""Return the English blog posts and model launch pages listed in the MiMo page metadata bundle.

	Args:
		client (primp.Client): Client from ``new_client``.
		source (Source): Source whose URL is the homepage.

	Returns:
		list[dict]: Posts with ``title``, ``date``, ``url`` and ``summary``.
	"""

	page = send(client, source.url).text
	pages = []

	for script_url in SCRIPT.findall(page):
		script = send(client, script_url).text

		if 'routePath:"/blog/' in script:
			pages = PAGE.findall(script)
			break

	if not pages:
		raise FetchError("no blog pages found in the site bundles")

	posts = []

	for route, frontmatter in pages:

		if route in SKIPPED_ROUTES:
			continue

		url = urljoin(HOMEPAGE, route)
		post = {"title": _field(frontmatter, "title"), "date": _field(frontmatter, "date"), "url": url, "summary": _field(frontmatter, "description")}

		if not post["title"] or not post["date"]:

			try:
				details = _page_details(client, url)
			except FetchError:
				continue

			post = {key: post[key] or details.get(key) for key in post}

		if post["title"]:
			post["title"] = TITLE_SUFFIX.sub("", post["title"])
			posts.append(post)

	return posts

def extract_posts(posts: list[dict], source_url: str) -> list[dict]:
	"""Map the posts read from the bundle to items.

	Args:
		posts (list[dict]): Posts from ``bundle_posts``.
		source_url (str): Homepage URL (unused).

	Returns:
		list[dict]: One item per post, newest first.
	"""

	require_type("posts", posts, list)

	return newest_first([item(p["title"], p["date"], p["url"], p["summary"]) for p in posts])

SOURCES = [
	hf("XiaomiMiMo"),
	custom("api", HOMEPAGE, bundle_posts, extract_posts),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
