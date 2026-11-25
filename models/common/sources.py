"""Source definitions used by every lab's ``source.py``.

A lab lists its sources in priority order with the constructors below. Each
constructor returns a ``Source`` that records the source kind, the URL and how
to fetch it; the runner turns that list into the published JSON.
"""

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode

from models.common.validation import require_callable, require_choice, require_http_url, require_text, require_type

KINDS = ("api", "rss", "html", "hf")

HF_API = "https://huggingface.co/api/models"

HF_LIMIT = 50

GITHUB_LIMIT = 30


@dataclass(frozen=True)
class Source:
	"""One place a lab publishes model news.

	Attributes:
		kind (str): ``"api"`` (JSON kept as is), ``"rss"`` (XML converted with xmltodict), ``"html"`` (page converted to markdown) or ``"hf"`` (Hugging Face models API).
		url (str): URL that is requested.
		method (str): HTTP method, ``"GET"`` or ``"POST"``.
		json_body (dict | None): JSON body for a POST request.
		headers (dict | None): Extra request headers.
		fetch (Callable | None): Custom fetch function ``fetch(client, source) -> content`` that replaces the default one for the kind.
	"""

	kind: str
	url: str
	method: str = "GET"
	json_body: dict | None = None
	headers: dict | None = None
	fetch: Callable[..., Any] | None = None


def _check_headers(headers: dict | None) -> None:
	"""Raise unless ``headers`` is None or a dict of strings.

	Args:
		headers (dict | None): Extra request headers.

	Returns:
		None
	"""

	if headers is None:
		return

	require_type("headers", headers, dict)

	for key, value in headers.items():
		require_text("header name", key)
		require_type(f"header {key}", value, str)


def api(url: str, method: str = "GET", json_body: dict | None = None, headers: dict | None = None) -> Source:
	"""Return a source whose JSON response is published unchanged.

	Args:
		url (str): Absolute URL of the JSON endpoint.
		method (str): ``"GET"`` or ``"POST"``.
		json_body (dict | None): JSON body for a POST request.
		headers (dict | None): Extra request headers.

	Returns:
		Source: Source of kind ``"api"``.
	"""

	require_http_url("url", url)
	require_choice("method", method, ("GET", "POST"))

	if json_body is not None:
		require_type("json_body", json_body, dict)

	_check_headers(headers)

	return Source("api", url, method, json_body, headers)


def rss(url: str) -> Source:
	"""Return a source whose RSS or Atom feed is converted to JSON with xmltodict.

	Args:
		url (str): Absolute URL of the feed.

	Returns:
		Source: Source of kind ``"rss"``.
	"""

	require_http_url("url", url)

	return Source("rss", url)


def html(url: str, headers: dict | None = None) -> Source:
	"""Return a source whose page is converted to markdown.

	Args:
		url (str): Absolute URL of the page.
		headers (dict | None): Extra request headers, for sites that reject requests without them.

	Returns:
		Source: Source of kind ``"html"``.
	"""

	require_http_url("url", url)
	_check_headers(headers)

	return Source("html", url, headers=headers)


def hf(org: str, search: str | None = None) -> Source:
	"""Return a source that lists the newest models of a Hugging Face organization.

	Args:
		org (str): Organization name on Hugging Face, e.g. ``"Qwen"``.
		search (str | None): Optional substring filter on model ids, for organizations that publish many unrelated models.

	Returns:
		Source: Source of kind ``"hf"``.
	"""

	require_text("org", org)

	if search is not None:
		require_text("search", search)

	params = {"author": org, "sort": "createdAt", "direction": "-1", "limit": str(HF_LIMIT)}

	if search:
		params["search"] = search

	return Source("hf", f"{HF_API}?{urlencode(params)}")


def github(org: str) -> Source:
	"""Return a source that lists the newest repositories of a GitHub organization.

	The request uses the ``GITHUB_TOKEN`` environment variable when it is set,
	since unauthenticated calls share a low rate limit per IP address.

	Args:
		org (str): Organization name on GitHub, e.g. ``"InternLM"``.

	Returns:
		Source: Source of kind ``"api"``.
	"""

	require_text("org", org)

	url = f"https://api.github.com/orgs/{quote(org)}/repos?sort=created&direction=desc&per_page={GITHUB_LIMIT}"
	headers = {"Accept": "application/vnd.github+json"}
	token = os.environ.get("GITHUB_TOKEN")

	if token:
		headers["Authorization"] = f"Bearer {token}"

	return Source("api", url, headers=headers)


def custom(kind: str, url: str, fetch: Callable[..., Any]) -> Source:
	"""Return a source with its own fetch function, for sites that need extra steps.

	Args:
		kind (str): One of ``KINDS``; describes the published content.
		url (str): Absolute URL of the entry point, shown in the output.
		fetch (Callable[..., Any]): Function ``fetch(client, source) -> content``.

	Returns:
		Source: Source that the runner fetches with ``fetch``.
	"""

	require_choice("kind", kind, KINDS)
	require_http_url("url", url)
	require_callable("fetch", fetch)

	return Source(kind, url, fetch=fetch)
