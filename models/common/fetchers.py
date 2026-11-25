"""Default fetch functions, one per source kind.

``api`` and ``hf`` sources return the decoded JSON unchanged, ``rss`` sources
return the feed converted to a dict by xmltodict, and ``html`` sources return the
page as markdown with every link made absolute.
"""

import re
from typing import Any
from urllib.parse import urljoin
from xml.parsers.expat import ExpatError

import primp
import xmltodict

from models.common.http import FetchError, send
from models.common.sources import Source
from models.common.validation import require_type

FEED_ROOTS = ("rss", "feed", "rdf:RDF")

_REFERENCE_LINK = re.compile(r"^(\[\d+\]:\s*)(\S+)(.*)$", re.MULTILINE)


def fetch_json(client: primp.Client, source: Source) -> Any:
	"""Fetch a JSON endpoint and return the decoded body.

	Args:
		client (primp.Client): Client from ``new_client``.
		source (Source): Source of kind ``"api"`` or ``"hf"``.

	Returns:
		Any: Decoded JSON exactly as the server sent it.
	"""

	require_type("source", source, Source)

	response = send(client, source.url, source.method, source.json_body, source.headers)

	try:
		return response.json()
	except (ValueError, primp.PrimpError) as exc:
		raise FetchError(f"response is not JSON: {exc}", response.status_code) from exc


def fetch_feed(client: primp.Client, source: Source) -> dict:
	"""Fetch an RSS or Atom feed and convert the XML to a dict with xmltodict.

	Args:
		client (primp.Client): Client from ``new_client``.
		source (Source): Source of kind ``"rss"``.

	Returns:
		dict: Literal xmltodict conversion of the feed.
	"""

	require_type("source", source, Source)

	response = send(client, source.url, source.method, source.json_body, source.headers)

	try:
		parsed = xmltodict.parse(response.text)
	except ExpatError as exc:
		raise FetchError(f"response is not XML: {exc}", response.status_code) from exc

	if not any(root in parsed for root in FEED_ROOTS):
		raise FetchError(f"XML root is not a feed: {list(parsed)}", response.status_code)

	return parsed


def absolute_links(markdown: str, base_url: str) -> str:
	"""Rewrite the reference links of a markdown document as absolute URLs.

	Args:
		markdown (str): Markdown produced by primp, with links such as ``[3]: /news/post``.
		base_url (str): URL of the page the markdown came from.

	Returns:
		str: Same markdown with every reference target resolved against ``base_url``.
	"""

	require_type("markdown", markdown, str)
	require_type("base_url", base_url, str)

	return _REFERENCE_LINK.sub(lambda m: m.group(1) + urljoin(base_url, m.group(2)) + m.group(3), markdown)


def fetch_markdown(client: primp.Client, source: Source) -> str:
	"""Fetch an HTML page and return it as markdown with absolute links.

	Args:
		client (primp.Client): Client from ``new_client``.
		source (Source): Source of kind ``"html"``.

	Returns:
		str: Page content as markdown.
	"""

	require_type("source", source, Source)

	response = send(client, source.url, source.method, source.json_body, source.headers)
	markdown = response.text_markdown

	if not markdown.strip():
		raise FetchError("page converted to empty markdown", response.status_code)

	return absolute_links(markdown, str(response.url))


DEFAULT_FETCHERS = {
	"api": fetch_json,
	"hf": fetch_json,
	"rss": fetch_feed,
	"html": fetch_markdown,
}
