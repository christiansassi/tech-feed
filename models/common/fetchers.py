"""Default fetch functions, one per source kind.

``api`` and ``hf`` sources return the decoded JSON, ``rss`` sources return the
feed converted to a dict by xmltodict, and ``html`` sources return the page HTML.
Each source's extractor then maps that content to items in the common schema.
"""

from typing import Any
from xml.parsers.expat import ExpatError

import primp
import xmltodict

from models.common.http import FetchError, send
from models.common.sources import Source
from models.common.validation import require_type

FEED_ROOTS = ("rss", "feed", "rdf:RDF")

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

def fetch_html(client: primp.Client, source: Source) -> str:
	"""Fetch an HTML page and return its markup for the source's extractor.

	Args:
		client (primp.Client): Client from ``new_client``.
		source (Source): Source of kind ``"html"``.

	Returns:
		str: Page HTML.
	"""

	require_type("source", source, Source)

	response = send(client, source.url, source.method, source.json_body, source.headers)

	if not response.text.strip():
		raise FetchError("empty page", response.status_code)

	return response.text

DEFAULT_FETCHERS = {
	"api": fetch_json,
	"hf": fetch_json,
	"rss": fetch_feed,
	"html": fetch_html,
}
